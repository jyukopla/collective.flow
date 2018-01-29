# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.schema import load_schema
from collective.flow.schema import remove_attachments
from datetime import datetime
from persistent.mapping import PersistentMapping
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.events import AddBegunEvent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.namedfile import NamedBlobFile
from plone.namedfile import NamedBlobImage
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from venusianconfiguration import configure
from z3c.form.interfaces import NOT_CHANGED
from zope.cachedescriptors import property
from zope.component import createObject
from zope.component import getUtility
from zope.event import notify
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.location.interfaces import IContained

import os


_ = MessageFactory('collective.flow')


def save_form(form, data, submission):
    for name, field in form.fields.items():
        if name == 'schema':
            continue
        elif name not in data:
            continue

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


def extract_attachments(data, context, prefix=u''):
    if isinstance(data, list) or isinstance(data, tuple):
        for i in range(len(data)):
            for attachment in extract_attachments(
                    data[i], context,
                    prefix=u'{0:s}{1:02d}-'.format(prefix, i + 1)):
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
                    prefix, name, attachment.file.filename)
                del data[name]
                yield aq_base(attachment)
            elif isinstance(value, NamedBlobImage):
                attachment = createObject(fti.factory).__of__(context)
                attachment.file = None
                attachment.image = value
                attachment.image.filename = u'{0:s}{1:s}-{2:s}'.format(
                    prefix, name, attachment.image.filename)
                del data[name]
                yield aq_base(attachment)
            elif value:
                for attachment in extract_attachments(
                        value, context,
                        prefix=u'{0:s}{1:s}-'.format(prefix, name)):
                    yield attachment


@configure.browser.page.class_(
    name='view',
    for_=IFlowFolder,
    layer=ICollectiveFlowLayer,
    permission='zope2.View')
@implementer(IFlowSchemaForm)
class FlowSubmitForm(DefaultAddForm):
    portal_type = 'FlowSubmission'
    description = u''
    content = None

    def label(self):
        return self.context.Title()

    @property.Lazy
    def schema(self):
        try:
            return load_schema(self.context.schema)
        except AttributeError:
            self.request.response.redirect(
                u'{0}/@@design'.format(self.context.absolute_url()))
            return load_schema(DEFAULT_SCHEMA)

    additionalSchemata = ()

    def update(self):
        if 'disable_border' in self.request.form:
            del self.request.form['disable_border']
        super(DefaultAddForm, self).update()
        # fire the edit begun only if no action was executed
        if len(self.actions.executedActions) == 0:
            notify(AddBegunEvent(self.context))

    def create(self, data):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        context = aq_inner(self.context)
        submission = createObject(fti.factory).__of__(context)

        # extract attachments to be saved into separate objects
        attachments = tuple(extract_attachments(data, context))

        # save form data (bypass data manager for speed
        # and to avoid needing to reload the form schema)
        save_form(self, data, submission)

        submission.schema = remove_attachments(self.context.schema)
        submission.title = u'{0:s} {1:s}'.format(
            context.title, datetime.utcnow().strftime('%Y-%#m-%#d'),
        )

        return aq_base(submission), attachments

    def add(self, submission_with_attachments):
        submission, attachments = submission_with_attachments
        form = aq_inner(self.context)
        submission = addContentToContainer(
            form, submission, checkConstraints=False)
        for attachment in attachments:
            addContentToContainer(
                submission, attachment, checkConstraints=False)
        self.content = submission.__of__(self.context)

    def render(self):
        if self._finishedAdd:
            return SubmissionView(
                self.context, self.request, self.content)()
        return super(FlowSubmitForm, self).render()

    def updateActions(self):
        # override to re-title save button and remove the cancel button
        super(FlowSubmitForm, self).updateActions()
        self.buttons['save'].title = self.context.submit_label
        if 'cancel' in self.buttons:
            del self.buttons['cancel']


class SubmissionView(WidgetsView):
    ignoreRequest = True

    index = ViewPageTemplateFile(
        os.path.join('submission_templates', 'view.pt'))

    def __init__(self, context, request, content):
        self.content = content
        self.schema = load_schema(content.schema)
        super(SubmissionView, self).__init__(context, request)

    def getContent(self):
        return self.content
