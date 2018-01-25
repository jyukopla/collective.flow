# -*- coding: utf-8 -*-
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSchema
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.utils import load_schema
from OFS.interfaces import IItem
from plone.dexterity.browser.edit import DefaultEditForm
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.interfaces import ISchemaModifiedEvent
from plone.supermodel import serializeSchema
from venusianconfiguration import configure
from z3c.form import button
from zope.cachedescriptors import property
from zope.component import adapter
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer


_ = MessageFactory('collective.flow')


@configure.browser.page.class_(
    name='view',
    for_=IFlowSchema,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template='submission_templates/view.pt',
)
class SchemaView(DefaultEditForm):
    buttons = button.Buttons()

    def label(self):
        return self.context.title

    def description(self):
        return self.context.description

    @property.Lazy
    def schema(self):
        try:
            return load_schema(self.context.schema_xml)
        except AttributeError:
            self.request.response.redirect(
                '{0:s}/@@schema'.format(self.context.absolute_url()))
            return load_schema(DEFAULT_SCHEMA)

    additionalSchemata = ()


@configure.browser.page.class_(
    name='schema',
    for_=IFlowSchema,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
    allowed_interface=IItem,
)
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
            title=_(u'flow input'))
        self.object = context


@configure.subscriber.handler()
@adapter(IFlowSchemaContext, ISchemaModifiedEvent)
def save_schema(schema_context, event):
    schema_context.object.schema_xml = serializeSchema(schema_context.schema)
