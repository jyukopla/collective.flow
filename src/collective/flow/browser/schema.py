# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from Acquisition import aq_base
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSchema
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.schema import load_schema
from collective.flow.schema import save_schema
from lxml import etree
from OFS.interfaces import IItem
from plone.dexterity.browser.edit import DefaultEditForm
from plone.memoize import view
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from Products.Five import BrowserView
from venusianconfiguration import configure
from z3c.form import button
from zope.component import queryMultiAdapter
from zope.i18n import negotiate
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

import json
import plone.app.dexterity.browser


_ = MessageFactory('collective.flow')


@configure.browser.page.class_(
    name='view',
    for_=IFlowSchema,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template='schema_templates/view.pt',
)
class SchemaView(DefaultEditForm):
    buttons = button.Buttons()

    def label(self):
        return self.context.title

    def description(self):
        return self.context.description

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
                '{0:s}/@@design'.format(self.context.absolute_url()),
            )
            return load_schema(DEFAULT_SCHEMA, cache_key=None)

    additionalSchemata = ()


@configure.browser.page.class_(
    name='design',
    for_=IFlowSchema,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
    allowed_interface=IItem,
)
@implementer(IFlowSchemaContext)
class FlowSchemaContext(SchemaContext):
    def __init__(self, context, request):
        language = negotiate(context=request)
        try:
            schema = load_schema(
                aq_base(context).schema,
                language=language,
                cache_key=None,
            )
        except AttributeError:
            schema = load_schema(DEFAULT_SCHEMA, cache_key=None)
        super(FlowSchemaContext, self).__init__(
            schema,
            request,
            name='@@{0:s}'.format(self.__name__),
            title=_(u'design'),
        )
        self.content = context


@configure.browser.page.class_(
    name='fields',
    for_=IFlowSchemaContext,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
class RedirectSchemaEditor(BrowserView):
    def __call__(self):
        self.request.response.redirect(
            self.context.content.absolute_url() + u'/@@design',
        )


class ModelEditorView(BrowserView):
    def modelSource(self):
        try:
            return aq_base(self.context.content).schema
        except AttributeError:
            return DEFAULT_SCHEMA


def authorized(context, request):
    authenticator = queryMultiAdapter((context, request),
                                      name=u'authenticator')
    return authenticator and authenticator.verify()


@configure.browser.page.class_(
    name='model-edit-save',
    for_=IFlowSchemaContext,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
class AjaxSaveHandler(BrowserView):
    def __call__(self):
        if not authorized(self.context, self.request):
            raise Unauthorized()

        source = self.request.form.get('source')

        try:
            source = etree.tostring(
                etree.fromstring(source),
                pretty_print=True,
                xml_declaration=True,
                encoding='utf8',
            )
            load_schema(source, cache_key=None)
        except Exception as e:
            message = e.args[0].replace('\n  File "<unknown>"', '')
            return json.dumps({
                'success': False,
                'message': u'ParseError: {0}'.format(message),
            })

        save_schema(self.context.content, xml=source)

        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps({'success': True, 'message': _(u'Saved')})


with configure(package=plone.app.dexterity.browser) as subconfigure:
    subconfigure.browser.page(
        name='modeleditor',
        for_=IFlowSchemaContext,
        layer=ICollectiveFlowLayer,
        class_=ModelEditorView,
        permission='cmf.ModifyPortalContent',
        template='modeleditor.pt',
    )
