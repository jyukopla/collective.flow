# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.browser.folder import save_form
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSchemaDynamic
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import load_schema
from plone.app.z3cform.object import ObjectSubForm
from plone.app.z3cform.object import SubformAdapter
from plone.autoform.form import AutoObjectSubForm
from plone.autoform.interfaces import IAutoObjectSubForm
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.z3cform.fieldsets.extensible import ExtensibleForm
from venusianconfiguration import configure
from z3c.form.interfaces import IObjectWidget
from z3c.form.interfaces import ISubformFactory
from zope.cachedescriptors import property
from zope.component import adapter
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.interface import Interface


_ = MessageFactory('collective.flow')


@implementer(IAutoObjectSubForm)
class SubmissionObjectSubForm(ObjectSubForm, AutoObjectSubForm):

    def setupFields(self):
        self.updateFieldsFromSchemata()

    def __call__(self):
        return u''  # never called directly


@configure.adapter.factory()
@implementer(ISubformFactory)
@adapter(Interface, ICollectiveFlowLayer, Interface, Interface,
         IObjectWidget, Interface, IFlowSchemaDynamic)
class SubmissionSubFormAdapter(SubformAdapter):
    factory = SubmissionObjectSubForm


@configure.browser.page.class_(
    name='view',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template='submission_templates/view.pt',
)
@implementer(IFlowSchemaForm)
class SubmissionView(WidgetsView, ExtensibleForm):

    @property.Lazy
    def schema(self):
        return load_schema(aq_base(self.context).schema,
                           cache_key=aq_base(self.context).schema_digest)

    def updateFieldsFromSchemata(self):
        super(SubmissionView, self).updateFieldsFromSchemata()
        self.updateFields()


@configure.browser.page.class_(
    name='edit',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IFlowSchemaForm)
class SubmissionEditForm(DefaultEditForm):

    @property.Lazy
    def schema(self):
        return load_schema(aq_base(self.context).schema,
                           cache_key=aq_base(self.context).schema_digest)

    additionalSchemata = ()

    def applyChanges(self, data):
        save_form(self, data, self.context)
