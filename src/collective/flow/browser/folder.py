# -*- coding: utf-8 -*-
from AccessControl.interfaces import IOwned
from AccessControl.security import checkPermission
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.flow.browser.widgets import RichTextLabelWidget
from collective.flow.interfaces import DEFAULT_FIELDSET_LABEL_FIELD
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import IAddFlowSchemaDynamic
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowImpersonation
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IImpersonateFlowSchemaDynamic
from collective.flow.interfaces import SUBMISSION_TITLE_TEMPLATE_FIELD
from collective.flow.interfaces import SUBMIT_LABEL_FIELD
from collective.flow.schema import FlowSchemaFieldPermissionChecker
from collective.flow.schema import interpolate
from collective.flow.schema import load_schema
from collective.flow.schema import remove_attachments
from collective.flow.utils import parents
from collective.flow.utils import prepare_restricted_function
from collective.flow.utils import unrestricted
from datetime import datetime
from persistent.mapping import PersistentMapping
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.widgets.interfaces import IFieldPermissionChecker
from plone.autoform.form import AutoExtensibleForm
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.events import AddBegunEvent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.dexterity.utils import createContent
from plone.i18n.normalizer import IIDNormalizer
from plone.memoize import view
from plone.namedfile import NamedBlobFile
from plone.namedfile import NamedBlobImage
from plone.namedfile.interfaces import INamedFileField
from plone.uuid.interfaces import IMutableUUID
from plone.uuid.interfaces import IUUID
from plone.z3cform.fieldsets.group import Group
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from uuid import uuid4
from venusianconfiguration import configure
from z3c.form import button
from z3c.form.form import Form
from z3c.form.interfaces import IDataManager
from z3c.form.interfaces import IErrorViewSnippet
from z3c.form.interfaces import IMultiWidget
from z3c.form.interfaces import IObjectWidget
from z3c.form.interfaces import IValue
from z3c.form.interfaces import IWidget
from z3c.form.interfaces import NOT_CHANGED
from z3c.form.util import changedField
from zope.component import adapter
from zope.component import createObject
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.globalrequest import getRequest
from zope.i18n import negotiate
from zope.i18nmessageid import MessageFactory
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Invalid
from zope.location.interfaces import IContained
from zope.proxy import ProxyBase
from zope.publisher.interfaces import IPublishTraverse
from ZPublisher.HTTPRequest import FileUpload

import hashlib
import new
import os
import plone.api as api


_ = MessageFactory('collective.flow')


def save_form(  # noqa: C901 (this has gotten quite complex)
        form,
        data,
        submission,
        default_values=False,
        force=False,
):
    changes = {}
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
            value.__parent__ = aq_base(submission)

        # Set contained information of schema.List|Tuple(value_type=Object)
        if isinstance(value, list) or isinstance(value, tuple):
            for item in value:
                if IContained.providedBy(item):
                    item.__name__ = name
                    item.__parent__ = aq_base(submission)

        if force:
            setattr(submission, name, value)
        elif changedField(field.field, value, context=submission):
            # Only update the data, if it is different
            dm = getMultiAdapter((submission, field.field), IDataManager)
            dm.set(value)
            # Record the change using information required later
            changes.setdefault(dm.field.interface, []).append(name)
    try:
        for group in form.groups:
            changes.update(
                save_form(group, data, submission, default_values, force),
            )
    except AttributeError:
        pass

    return changes


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
    return errors.values()


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


def get_submission_container(root, container, submission):
    try:
        template = submission.aq_explicit.aq_acquire(
            'submission_path_template',
        )
    except AttributeError:
        template = None
    if not template:
        return container
    container = root
    language = api.portal.get_default_language().split('-')[0]
    path = datetime.utcnow().strftime(
        interpolate(template, submission, language=language),
    )
    normalizer = getUtility(IIDNormalizer)
    for title in filter(bool, path.split('/')):
        id_ = normalizer.normalize(title)
        try:
            container = container[id_]
        except KeyError:
            container = create_sub_folder(container, id_, title)
    return container


@unrestricted
def create_sub_folder(container, id_, title):
    content = createContent('FlowSubFolder', title=title)
    IOwned(content).changeOwnership(IOwned(container).getOwner())
    content.id = id_
    content.schema = container.schema
    content.schema_digest = container.schema_digest
    addContentToContainer(container, content, checkConstraints=False)
    return container[id_]


def get_submission_title(form, submission):
    language = negotiate(context=getRequest())
    try:
        try:
            template = submission.aq_explicit.aq_acquire(
                SUBMISSION_TITLE_TEMPLATE_FIELD + '_' + language,
            )
        except AttributeError:
            template = submission.aq_explicit.aq_acquire(
                SUBMISSION_TITLE_TEMPLATE_FIELD,
            )
        return datetime.utcnow().strftime(
            interpolate(template, submission).encode('utf-8', 'ignore'),
        ).decode('utf-8', 'ignore')
    except AttributeError:
        return u'{0:s} {1:s}'.format(
            form.title,
            datetime.utcnow().strftime('%Y-%#m-%#d'),
        )


# noinspection PyAbstractClass
class FlowSubmitFormGroup(Group):
    pass


@configure.browser.page.class_(
    name=u'contentlisting',
    for_=IFlowFolder,
    permission=u'zope2.View',
)
class FolderListing(BrowserView):
    def __call__(self, batch=False, b_size=20, b_start=0, orphan=0, **kw):
        query = {}
        query.update(kw)

        query['path'] = '/'.join(self.context.getPhysicalPath())
        query['portal_type'] = ['FlowSubmission']

        user = api.user.get_current()
        if 'Creator' not in query and user:
            query['Creator'] = user.getId()
        if 'sort_on' not in query:
            query['sort_on'] = 'modified'
        if 'sort_order' not in query:
            query['sort_order'] = 'descending'

        # Provide batching hints to the catalog
        if batch:
            query['b_start'] = b_start
            query['b_size'] = b_size + orphan

        catalog = api.portal.get_tool('portal_catalog')
        results = catalog(query)
        return IContentListing(results)


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
    template = ViewPageTemplateFile(
        os.path.join('folder_templates', 'folder_form.pt'),
    )
    view_template = ViewPageTemplateFile(
        os.path.join('folder_templates', 'folder_listing.pt'),
    )
    enable_form_tabbing = False
    css_class = 'pat-folding-fieldsets'
    impersonate_url = None

    def __init__(self, context, request):
        super(FlowSubmitForm, self).__init__(context, request)
        language = negotiate(context=self.request)
        if api.portal.get_default_language().startswith(language):
            self.localized_context = context
        else:
            proxy = LanguageFieldsProxy(self.context)
            proxy._language = language
            self.localized_context = proxy
        self.buttons = button.Buttons()
        self.handlers = button.Handlers()

    def __call__(self):
        if 'disable_border' in self.request.form:
            del self.request.form['disable_border']

        pc = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        if (not self.submission_path_template and
                len(pc.unrestrictedSearchResults(  # noqa: W503
                    path=path,
                    portal_type=['FlowFolder', 'FlowSubFolder'],
                )) > 1):
            return self.view_template(self)
        else:
            return super(FlowSubmitForm, self).__call__()

    def label(self):
        return self.localized_context.title

    # noinspection PyRedeclaration
    @property
    def description(self):
        return self.localized_context.description

    @property
    def default_fieldset_label(self):
        return self.localized_context.default_fieldset_label

    @property
    def submit_label(self):
        return self.localized_context.submit_label

    @property
    def submission_title_template(self):
        return self.localized_context.submission_title_template

    @property
    def submission_path_template(self):
        return self.context.submission_path_template

    @property
    def submission_behaviors(self):
        return self.context.submission_behaviors

    @property
    def submission_impersonation(self):
        return self.context.submission_impersonation

    @property
    def submission_workflow(self):
        return self.context.submission_workflow

    @property
    def attachment_workflow(self):
        return self.context.attachment_workflow

    @property
    @view.memoize
    def schema(self):
        language = negotiate(context=self.request)
        try:
            try:
                schema = load_schema(
                    aq_base(self.context).schema,
                    name='++add++',
                    language=language,
                    cache_key=aq_base(self.context).schema_digest,
                )
                alsoProvides(schema, IAddFlowSchemaDynamic)
                return schema
            except KeyError:
                return load_schema(
                    aq_base(self.context).schema,
                    language=language,
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
        submission.title = IUUID(submission)  # noqa: P001

        # extract attachments to be saved into separate objects
        submission._v_attachments = tuple(extract_attachments(data, context))

        # save form data (bypass data manager for speed
        # and to avoid needing to reload the form schema)
        save_form(self, data, submission, default_values=True, force=True)

        # save schema to allow submission to adapt its schema interface
        submission.schema = remove_attachments(self.context.schema)
        submission.schema_digest = hashlib.md5(submission.schema).hexdigest()

        # we cannot acquire from parent FlowFolder, because behaviors
        # are resolved (this method called) without acquisition chain
        submission.submission_behaviors = self.submission_behaviors

        return aq_base(submission)

    def add(self, submission):
        try:
            # noinspection PyProtectedMember
            attachments = submission._v_attachments
            delattr(submission, '_v_attachments')
        except AttributeError:
            attachments = []

        folder = self.context
        for folder in parents(folder, IFlowFolder):
            # Traverse from IFlowSubFolders to IFlowFolder
            break
        container = get_submission_container(
            folder,
            self.context,
            submission.__of__(self.context),
        )
        submission = addContentToContainer(
            container,
            submission,
            checkConstraints=False,
        )
        for attachment in attachments:
            addContentToContainer(
                submission,
                attachment,
                checkConstraints=False,
            )
        content = submission.__of__(self.context)
        submission.title = get_submission_title(folder, content)
        submission.reindexObject(idxs=['title'])
        self.content = content

    def render(self):
        if self._finishedAdd:
            can_view = checkPermission(  # noqa: P001
                'zope2.View',
                self.content,
            )
            can_edit = checkPermission(  # noqa: P001
                'cmf.ModifyPortalContent',
                self.content,
            )
            if IAddFlowSchemaDynamic.providedBy(self.schema) and can_edit:
                self.request.response.redirect(
                    self.content.absolute_url() + u'/@@edit',
                )
                return u''
            elif can_view:
                self.request.response.redirect(self.content.absolute_url())
                return u''
            else:
                return SubmissionView(
                    self.context,
                    self.request,
                    self.content,
                )()
        else:
            can_edit = checkPermission(  # noqa: P001
                'cmf.ModifyPortalContent',
                self.context,
            )
            if can_edit and self.submission_impersonation:
                self.impersonate_url = (
                    self.context.absolute_url() + u'/@@impersonate'
                )
        return super(FlowSubmitForm, self).render()

    def updateActions(self):
        # override to re-title save button and remove the cancel button
        btn = button.Button(name='submit', title=self.submit_label)
        self.buttons += button.Buttons(btn)
        self.handlers.addHandler(btn, self.handleAdd)
        super(FlowSubmitForm, self).updateActions()


class FlowImpersonationForm(AutoExtensibleForm, Form):
    label = _(u'Fill the form for other person')

    ignoreContext = True

    @property
    @view.memoize
    def schema(self):
        try:
            language = negotiate(context=self.request)
            schema = load_schema(
                aq_base(self.context).schema,
                name='@@impersonate',
                language=language,
                cache_key=aq_base(self.context).schema_digest,
            )
            alsoProvides(schema, IImpersonateFlowSchemaDynamic)
            return schema
        except (AttributeError, KeyError):
            return IFlowImpersonation

    @button.buttonAndHandler(_(u'Continue'))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.request.response.redirect(
            self.request.getURL() + '/' + data['username'],
        )


@configure.browser.page.class_(
    name='impersonate',
    for_=IFlowFolder,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IPublishTraverse)
@implementer(IFlowSchemaForm)
class ImpersonatedFlowSubmitForm(FlowSubmitForm):
    username = None

    def publishTraverse(self, request, name):
        self.username = name
        return self

    def __call__(self):
        if self.username is None:
            if 'disable_border' in self.request.form:
                del self.request.form['disable_border']
            form = FlowImpersonationForm(self.context, self.request)
            form.update()
            return form()
        else:
            with api.env.adopt_user(username=self.username):
                return super(ImpersonatedFlowSubmitForm, self).__call__()


@configure.adapter.factory()
@adapter(IFlowSchemaForm)
@implementer(IFieldPermissionChecker)
class FlowSubmitFormPermissionChecker(FlowSchemaFieldPermissionChecker):
    DEFAULT_PERMISSION = 'Add portal content'

    def __init__(self, form):
        super(FlowSubmitFormPermissionChecker, self).__init__(form.context)


class SubmissionView(WidgetsView):
    ignoreRequest = True

    index = ViewPageTemplateFile(
        os.path.join('folder_templates', 'submission_view.pt'),
    )

    def __init__(self, context, request, content):
        language = negotiate(context=request)
        self.content = content
        self.schema = load_schema(
            aq_base(content).schema,
            language=language,
            cache_key=aq_base(content).schema_digest,
        )
        super(SubmissionView, self).__init__(context, request)

    @property
    def default_fieldset_label(self):
        language = negotiate(context=self.request)
        try:
            try:
                return getattr(
                    self.context,
                    DEFAULT_FIELDSET_LABEL_FIELD + '_' + language,
                )
            except AttributeError:
                return getattr(self.context, DEFAULT_FIELDSET_LABEL_FIELD)
        except AttributeError:
            return _(u'Form')

    def getContent(self):
        return self.content

    def updateFieldsFromSchemata(self):
        super(SubmissionView, self).updateFieldsFromSchemata()

        # disable default values
        for group in ([self] + self.groups):
            for name in group.fields:
                # noinspection PyPep8Naming
                group.fields[name].showDefault = False

    def update(self):
        super(SubmissionView, self).update()
        for group in ([self] + list(self.groups)):
            for widget in group.widgets.values():
                if isinstance(widget, RichTextLabelWidget):
                    widget.label = u''


class LanguageFieldsProxy(ProxyBase):
    __slots__ = ['_context', '_language']

    def __init__(self, context):
        super(LanguageFieldsProxy, self).__init__(context)
        self._context = context
        self._language = None

    def get_title(self):
        try:
            return getattr(self._context, 'title' + '_' + self._language)
        except AttributeError:
            return self._context.title

    def set_title(self, value):
        setattr(self._context, 'title' + '_' + self._language, value)

    title = property(get_title, set_title)

    def get_description(self):
        try:
            return getattr(self._context, 'description' + '_' + self._language)
        except AttributeError:
            return self._context.description

    def set_description(self, value):
        setattr(self._context, 'description' + '_' + self._language, value)

    description = property(get_description, set_description)

    def get_default_fieldset_label(self):
        try:
            return getattr(
                self._context,
                DEFAULT_FIELDSET_LABEL_FIELD + '_' + self._language,
            )
        except AttributeError:
            return self._context.default_fieldset_label

    def set_default_fieldset_label(self, value):
        setattr(
            self._context,
            DEFAULT_FIELDSET_LABEL_FIELD + '_' + self._language,
            value,
        )

    default_fieldset_label = property(
        get_default_fieldset_label,
        set_default_fieldset_label,
    )

    def get_submit_label(self):
        try:
            return getattr(
                self._context,
                SUBMIT_LABEL_FIELD + '_' + self._language,
            )
        except AttributeError:
            return self._context.submit_label

    def set_submit_label(self, value):
        setattr(
            self._context,
            SUBMIT_LABEL_FIELD + '_' + self._language,
            value,
        )

    submit_label = property(
        get_submit_label,
        set_submit_label,
    )

    def get_submission_title_template(self):
        try:
            return getattr(
                self._context,
                SUBMISSION_TITLE_TEMPLATE_FIELD + '_' + self._language,
            )
        except AttributeError:
            return self._context.submission_title_template

    def set_submission_title_template(self, value):
        setattr(
            self._context,
            SUBMISSION_TITLE_TEMPLATE_FIELD + '_' + self._language,
            value,
        )

    submission_title_template = property(
        get_submission_title_template,
        set_submission_title_template,
    )


@configure.browser.page.class_(
    name='edit',
    for_=IFlowFolder,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IFlowSchemaForm)
class FlowFolderEditForm(DefaultEditForm):
    def getContent(self):
        language = negotiate(context=self.request)
        if api.portal.get_default_language().startswith(language):
            return self.context
        else:
            proxy = LanguageFieldsProxy(self.context)
            proxy._language = language
            return proxy
