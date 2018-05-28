# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.schema import load_schema
from collective.flow.schema import remove_attachments
from collective.flow.utils import prepare_restricted_function
from datetime import datetime
from persistent.mapping import PersistentMapping
from plone import api
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.events import AddBegunEvent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.memoize import view
from plone.namedfile import NamedBlobFile
from plone.namedfile import NamedBlobImage
from plone.namedfile.interfaces import INamedFileField
from plone.uuid.interfaces import IMutableUUID
from plone.z3cform.fieldsets.group import Group
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from uuid import uuid4
from venusianconfiguration import configure
from z3c.form.interfaces import IErrorViewSnippet
from z3c.form.interfaces import IMultiWidget
from z3c.form.interfaces import IObjectWidget
from z3c.form.interfaces import IValue
from z3c.form.interfaces import IWidget
from z3c.form.interfaces import NOT_CHANGED
from zope.component import createObject
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.interface import Invalid
from zope.location.interfaces import IContained
from ZPublisher.HTTPRequest import FileUpload

import hashlib
import new
import os


_ = MessageFactory('collective.flow')


def save_form(form, data, submission, default_values=False):
    for name, field in form.fields.items():
        if name == 'schema':
            continue
        elif name not in data and default_values:
            value = field.field.default
            adapter = queryMultiAdapter(
                (
                    form.context,
                    form.request,
                    form,
                    field.field,
                    form.widgets[name],
                ),
                IValue,
                name='default',
            )
            if adapter:
                value = adapter.get()
        elif name not in data:
            continue
        else:
            value = data[name]
        if value is NOT_CHANGED:
            continue

        # Set contained information of schema.Object
        if IContained.providedBy(value):
            value.__name__ = name
            value.__parent__ = submission

        # Set contained information of schema.List|Tuple(value_type=Object)
        if isinstance(value, list) or isinstance(value, tuple):
            for item in value:
                if IContained.providedBy(item):
                    item.__name__ = name
                    item.__parent__ = submission

        setattr(submission, name, value)
    try:
        for group in form.groups:
            save_form(group, data, submission, default_values)
    except AttributeError:
        pass


def validate(form, code, data):
    # errors
    errors = {}

    # build re-usable restricted function components like in PythonScript
    path = 'undefined.py'
    code, g, defaults = prepare_restricted_function(
        'context, data, errors',
        code,
        'validate',
        path,
        [],
    )

    # update globals
    g = g.copy()
    g['__file__'] = path

    # validate
    new.function(code, g, None, defaults)(form.context, data, errors)

    # set errors
    for name, message in errors.items():

        # resolve field
        widget = None
        try:
            widget = form.widgets[name]
        except KeyError:
            for group in (form.groups or ()):
                try:
                    widget = group.widgets[name]
                    break
                except KeyError:
                    pass
        if widget is None:
            continue

        # set error
        error = Invalid(message)
        snippet = getMultiAdapter(
            (error, form.request, widget, widget.field, form, form.context),
            IErrorViewSnippet,
        )
        snippet.update()
        widget.error = snippet
        errors[name] = snippet

    # return errors
    return errors


def extract_attachments(data, context, prefix=u''):
    if isinstance(data, list) or isinstance(data, tuple):
        for i in range(len(data)):
            for attachment in extract_attachments(
                    data[i], context, prefix=u'{0:s}{1:02d}-'.format(prefix,
                                                                     i + 1)):
                yield attachment
        return
    elif isinstance(data, dict) or isinstance(data, PersistentMapping):
        fti = getUtility(IDexterityFTI, name='FlowAttachment')
        for name, value in data.items():
            if isinstance(value, NamedBlobFile):
                attachment = createObject(fti.factory).__of__(context)
                attachment.image = None
                attachment.file = value
                attachment.file.filename = u'{0:s}{1:s}-{2:s}'.format(
                    prefix,
                    name,
                    attachment.file.filename,
                )
                del data[name]
                yield aq_base(attachment)
            elif isinstance(value, NamedBlobImage):
                attachment = createObject(fti.factory).__of__(context)
                attachment.file = None
                attachment.image = value
                attachment.image.filename = u'{0:s}{1:s}-{2:s}'.format(
                    prefix,
                    name,
                    attachment.image.filename,
                )
                del data[name]
                yield aq_base(attachment)
            elif value:
                for attachment in extract_attachments(
                        value, context, prefix=u'{0:s}{1:s}-'.format(prefix,
                                                                     name)):
                    yield attachment


def reset_fileupload_widgets(form):
    for widget in form.widgets:
        if not IWidget.providedBy(widget):
            widget = form.widgets[widget]
        if INamedFileField.providedBy(widget.field):
            widget.value = None
        elif IMultiWidget.providedBy(widget):
            reset_fileupload_widgets(widget)
        elif IObjectWidget.providedBy(widget):
            reset_fileupload_widgets(widget.subform)
    try:
        for group in form.groups:
            reset_fileupload_widgets(group)
    except AttributeError:
        pass


def reset_fileupload(form):
    for key, value in list(form.request.form.items()):
        if not key.startswith(form.prefix):
            continue
        if isinstance(value, FileUpload):
            del form.request.form[key]
            form.request.form[key + '.action'] = 'remove'
    try:
        for group in form.groups:
            reset_fileupload(group)
    except AttributeError:
        pass
    reset_fileupload_widgets(form)


# noinspection PyAbstractClass
class FlowSubmitFormGroup(Group):
    pass


@configure.browser.page.class_(
    name='view',
    for_=IFlowFolder,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
)
@implementer(IFlowSchemaForm)
class FlowSubmitForm(DefaultAddForm):
    portal_type = 'FlowSubmission'
    description = u''
    content = None
    group_class = FlowSubmitFormGroup
    view_template = ViewPageTemplateFile(
        os.path.join('folder_templates', 'folder_listing.pt'),
    )

    def __call__(self):
        if 'disable_border' in self.request.form:
            del self.request.form['disable_border']

        pc = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        if (len(pc.unrestrictedSearchResults(
                path=path,
                portal_type=['FlowFolder', 'FlowSubFolder'],
        )) > 1):
            return self.view_template(self)
        else:
            return super(FlowSubmitForm, self).__call__()

    def label(self):
        return self.context.Title()

    # noinspection PyRedeclaration
    @property
    def description(self):
        return self.context.Description()

    @property
    def default_fieldset_label(self):
        return self.context.default_fieldset_label

    @property
    def submit_label(self):
        return self.context.submit_label

    @property
    def submission_workflow(self):
        return self.context.submission_workflow

    @property
    def attachment_workflow(self):
        return self.context.attachment_workflow

    @property
    @view.memoize
    def schema(self):
        try:
            return load_schema(
                aq_base(self.context).schema,
                cache_key=aq_base(self.context).schema_digest,
            )
        except AttributeError:
            self.request.response.redirect(
                u'{0}/@@design'.format(self.context.absolute_url()),
            )
            return load_schema(DEFAULT_SCHEMA, cache_key=None)

    additionalSchemata = ()

    def update(self):
        super(DefaultAddForm, self).update()
        # fire the edit begun only if no action was executed
        if len(self.actions.executedActions) == 0:
            notify(AddBegunEvent(self.context))

    # noinspection PyPep8Naming
    def extractData(self, setErrors=True):
        data, errors = super(FlowSubmitForm,
                             self).extractData(setErrors=setErrors)
        if errors:
            reset_fileupload(self)  # Required until we have drafting support
            data, errors = super(FlowSubmitForm,
                                 self).extractData(setErrors=setErrors)
        if not errors:
            validator = (self.context.validator or u'').strip()
            if validator:
                errors = validate(self, validator, data)
        return data, errors

    def create(self, data):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        context = aq_inner(self.context)
        submission = createObject(fti.factory).__of__(context)
        IMutableUUID(submission).set(uuid4())

        # extract attachments to be saved into separate objects
        attachments = tuple(extract_attachments(data, context))

        # save form data (bypass data manager for speed
        # and to avoid needing to reload the form schema)
        save_form(self, data, submission, default_values=True)

        # save required submission fields
        submission.schema = remove_attachments(self.context.schema)
        submission.schema_digest = hashlib.md5(submission.schema).hexdigest()
        submission.submission_workflow = self.submission_workflow
        submission.attachment_workflow = self.attachment_workflow

        submission.title = u'{0:s} {1:s}'.format(
            context.title,
            datetime.utcnow().strftime('%Y-%#m-%#d'),
        )

        return aq_base(submission), attachments

    def add(self, submission_with_attachments):
        submission, attachments = submission_with_attachments
        form = aq_inner(self.context)
        submission = addContentToContainer(
            form,
            submission,
            checkConstraints=False,
        )
        for attachment in attachments:
            addContentToContainer(
                submission,
                attachment,
                checkConstraints=False,
            )
        self.content = submission.__of__(self.context)

    def render(self):
        if self._finishedAdd:
            return SubmissionView(self.context, self.request, self.content)()
        return super(FlowSubmitForm, self).render()

    def updateActions(self):
        # override to re-title save button and remove the cancel button
        super(FlowSubmitForm, self).updateActions()
        self.buttons['save'].title = self.submit_label
        if 'cancel' in self.buttons:
            del self.buttons['cancel']


class SubmissionView(WidgetsView):
    ignoreRequest = True

    index = ViewPageTemplateFile(
        os.path.join('folder_templates', 'submission_view.pt'),
    )

    def __init__(self, context, request, content):
        self.content = content
        self.schema = load_schema(
            aq_base(content).schema,
            cache_key=aq_base(content).schema_digest,
        )
        super(SubmissionView, self).__init__(context, request)

    def getContent(self):
        return self.content

    def updateFieldsFromSchemata(self):
        super(SubmissionView, self).updateFieldsFromSchemata()

        # disable default values
        for group in ([self] + self.groups):
            for name in group.fields:
                # noinspection PyPep8Naming
                group.fields[name].showDefault = False
