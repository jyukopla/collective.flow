# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.utils import load_schema
from OFS.interfaces import IItem
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.events import AddBegunEvent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.interfaces import ISchemaModifiedEvent
from plone.supermodel import serializeSchema
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from venusianconfiguration import configure
from z3c.form.interfaces import NOT_CHANGED
from zope.cachedescriptors import property
from zope.component import adapter
from zope.component import createObject
from zope.component import getUtility
from zope.event import notify
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

import os


_ = MessageFactory('collective.flow')


@configure.browser.page.class_(
    name='schema',
    for_=IFlowFolder,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
    allowed_interface=IItem)
@implementer(IFlowSchemaContext)
class FlowSchemaContext(SchemaContext):
    def __init__(self, context, request):
        try:
            schema = load_schema(context.schema_xml)
        except AttributeError:
            schema = load_schema(DEFAULT_SCHEMA)
        super(FlowSchemaContext, self).__init__(
            schema, request,
            name=self.__name__,
            title=_(u'flow input schema'))
        self.object = context


@configure.subscriber.handler()
@adapter(IFlowSchemaContext, ISchemaModifiedEvent)
def save_schema(schema_context, event):
    schema_context.object.schema_xml = serializeSchema(schema_context.schema)


@configure.browser.page.class_(
    name='view',
    for_=IFlowFolder,
    layer=ICollectiveFlowLayer,
    permission='zope2.View')
class FlowSubmitForm(DefaultAddForm):
    portal_type = 'FlowSubmission'
    description = u''

    _submission = None

    def label(self):
        return self.context.Title()

    @property.Lazy
    def schema(self):
        try:
            return load_schema(self.context.schema_xml)
        except AttributeError:
            self.request.response.redirect(
                u'{0}/@@edit-schema'.format(self.context.absolute_url()))
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

        form = aq_inner(self.context)
        submission = createObject(fti.factory).__of__(form)
        submission.schema_xml = serializeSchema(self.schema)

        # save form data (bypass data manager for speed
        # and to avoid needing to reload the form schema)
        for name, field in self.fields.items():
            if name not in data:
                continue
            if data[name] is NOT_CHANGED:
                continue
            setattr(submission, name, data[name])
        submission.title = self.context.title
        submission.workflow = self.context.workflow

        return aq_base(submission)

    def add(self, submission):
        form = aq_inner(self.context)
        addContentToContainer(form, submission, checkConstraints=False)
        self._submission = submission.__of__(self.context)

    def render(self):
        if self._finishedAdd:
            return SubmissionView(self.context, self.request, self.schema)()
        return super(FlowSubmitForm, self).render()

    def updateActions(self):
        # override to re-title save button and remove the cancel button
        super(FlowSubmitForm, self).updateActions()
        self.buttons['save'].title = self.context.submit_label
        if 'cancel' in self.buttons:
            del self.buttons['cancel']


class SubmissionView(WidgetsView):
    ignoreContext = True
    ignoreRequest = False
    index = ViewPageTemplateFile(
        os.path.join('submission_templates', 'view.pt'))

    def __init__(self, context, request, schema):
        self.schema = schema
        super(SubmissionView, self).__init__(context, request)
