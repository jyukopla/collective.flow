# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.browser.folder import FlowImpersonationForm
from collective.flow.browser.folder import FlowSubmitForm
from collective.flow.browser.folder import FolderListing
from collective.flow.browser.localization import LanguageFieldsProxy
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubFolder
from collective.flow.schema import customized_schema
from collective.flow.schema import load_schema
from collective.flow.schema import save_schema
from collective.flow.subfolder import ICustomizableField
from collective.flow.utils import get_navigation_root_language
from OFS.interfaces import IItem
from plone import api
from plone.dexterity.browser.edit import DefaultEditForm
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.interfaces import IFieldEditorExtender
from plone.schemaeditor.interfaces import ISchemaContext
from venusianconfiguration import configure
from zope import schema
from zope.component import adapter
from zope.i18n import negotiate
from zope.i18nmessageid import MessageFactory
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import noLongerProvides
from zope.lifecycleevent import IObjectModifiedEvent
from zope.publisher.interfaces import IPublishTraverse
from zope.schema.interfaces import IField


_ = MessageFactory('collective.flow')


class IFieldCustomizableForm(Interface):
    comments = schema.Bool(
        title=_(u'Allow customizations in form flow sub-folders'),
        description=_(
            u'Allows customization of default and choice values '
            u'in form flow sub-folders (form specializations)',
        ),
        required=False,
    )


@configure.adapter.factory(
    name='collective.flow.customizable',
    provides=IFieldEditorExtender,
)
@adapter(ISchemaContext, IField)
def get_customization_schema(schema_context, field):
    return IFieldCustomizableForm


@configure.adapter.factory(provides=IFieldCustomizableForm)
@implementer(IFieldCustomizableForm)
@adapter(IField)
class FieldCustomizableAdapter(object):
    def __init__(self, field):
        self.field = field

    def _read_comments(self):
        return ICustomizableField.providedBy(self.field)

    def _write_comments(self, value):
        if value:
            alsoProvides(self.field, ICustomizableField)
        else:
            noLongerProvides(self.field, ICustomizableField)

    comments = property(_read_comments, _write_comments)


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
    name=u'contentlisting',
    for_=IFlowSubFolder,
    permission=u'zope2.View',
)
class SubFolderListing(FolderListing):
    pass


@configure.browser.page.class_(
    name='view',
    for_=IFlowSubFolder,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
)
@implementer(IFlowSchemaForm)
class SubFlowSubmitForm(FlowSubmitForm):

    def __init__(self, context, request):
        super(SubFlowSubmitForm, self).__init__(context, request)
        language = negotiate(context=request)
        context_language = get_navigation_root_language(self.context)
        if context_language.startswith(language):
            self.localized_context = context
        else:
            proxy = LanguageFieldsProxy(self.context)
            proxy._language = language
            self.localized_context = proxy


@configure.browser.page.class_(
    name='impersonate',
    for_=IFlowSubFolder,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IPublishTraverse)
@implementer(IFlowSchemaForm)
class ImpersonatedSubFlowSubmitForm(SubFlowSubmitForm):
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
                return super(ImpersonatedSubFlowSubmitForm, self).__call__()


@configure.browser.page.class_(
    name='edit',
    for_=IFlowSubFolder,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IFlowSchemaForm)
class FlowSubFolderEditForm(DefaultEditForm):
    def getContent(self):
        language = negotiate(context=self.request)
        context_language = get_navigation_root_language(self.context)
        if context_language.startswith(language):
            return self.context
        else:
            proxy = LanguageFieldsProxy(self.context)
            proxy._language = language
            return proxy
