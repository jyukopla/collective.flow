# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.browser.folder import FlowSubmitForm
from collective.flow.interfaces import ATTACHMENT_WORKFLOW_FIELD
from collective.flow.interfaces import DEFAULT_ATTACHMENT_WORKFLOW
from collective.flow.interfaces import DEFAULT_FIELDSET_LABEL_FIELD
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import DEFAULT_SUBMISSION_WORKFLOW
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubFolder
from collective.flow.interfaces import SUBMISSION_BEHAVIORS_FIELD
from collective.flow.interfaces import SUBMISSION_PATH_TEMPLATE_FIELD
from collective.flow.interfaces import SUBMISSION_TITLE_TEMPLATE_FIELD
from collective.flow.interfaces import SUBMISSION_WORKFLOW_FIELD
from collective.flow.schema import customized_schema
from collective.flow.schema import load_schema
from collective.flow.schema import save_schema
from OFS.interfaces import IItem
from plone import api
from plone.memoize import view
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from venusianconfiguration import configure
from zope.i18n import negotiate
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.lifecycleevent import IObjectModifiedEvent


_ = MessageFactory('collective.flow')


@configure.subscriber.handler(
    for_=(IFlowFolder, IObjectModifiedEvent),
)
def on_flow_change_customize_schemata(context, event):
    catalog = api.portal.get_tool('portal_catalog')
    for brain in catalog(object_provides=IFlowSubFolder.__identifier__,
                         path='/'.join(context.getPhysicalPath())):
        ob = brain.getObject()
        try:
            assert aq_base(ob).schema
        except AttributeError:
            # called when uninitialized flow folder is added onto flow
            continue
        save_schema(
            ob,
            xml=customized_schema(
                aq_base(context).schema,
                aq_base(ob).schema,
            ),
        )


@configure.browser.page.class_(
    name='design',
    for_=IFlowSubFolder,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
    allowed_interface=IItem,
)
@implementer(IFlowSchemaContext)
class SubFlowSchemaContext(SchemaContext):
    def __init__(self, context, request):
        language = negotiate(context=request)
        try:
            schema = load_schema(
                aq_base(context).schema,
                language=language,
                cache_key=None,
            )
        except AttributeError:
            schema = load_schema(
                context.aq_explicit.aq_acquire('schema'),
                cache_key=None,
            )
        super(SubFlowSchemaContext, self).__init__(
            schema,
            request,
            name='@@{0:s}'.format(self.__name__),
            title=_(u'design'),
        )
        self.content = context


@configure.browser.page.class_(
    name='view',
    for_=IFlowSubFolder,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
)
@implementer(IFlowSchemaForm)
class SubFlowSubmitForm(FlowSubmitForm):
    def label(self):
        try:
            return self.context.aq_explicit.aq_acquire('title')
        except AttributeError:
            return self.context.title

    @property
    def default_fieldset_label(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                DEFAULT_FIELDSET_LABEL_FIELD,
            )
        except AttributeError:
            return _(u'Default')

    @property
    def submission_title_template(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                SUBMISSION_TITLE_TEMPLATE_FIELD,
            )
        except AttributeError:
            return u''

    @property
    def submission_path_template(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                SUBMISSION_PATH_TEMPLATE_FIELD,
            )
        except AttributeError:
            return u''

    @property
    def submission_behaviors(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                SUBMISSION_BEHAVIORS_FIELD,
            )
        except AttributeError:
            return []

    @property
    def submission_workflow(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                SUBMISSION_WORKFLOW_FIELD,
            )
        except AttributeError:
            return DEFAULT_SUBMISSION_WORKFLOW

    @property
    def attachment_workflow(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                ATTACHMENT_WORKFLOW_FIELD,
            )
        except AttributeError:
            return DEFAULT_ATTACHMENT_WORKFLOW

    @property
    @view.memoize
    def schema(self):
        language = negotiate(context=self.request)
        try:
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
