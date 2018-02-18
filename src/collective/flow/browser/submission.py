# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.browser.folder import save_form
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import load_schema
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.edit import DefaultEditForm
from venusianconfiguration import configure
from zope.cachedescriptors import property
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer


_ = MessageFactory('collective.flow')


@configure.browser.page.class_(
    name='view',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template='submission_templates/view.pt',
)
@implementer(IFlowSchemaForm)
class SubmissionView(WidgetsView):

    @property.Lazy
    def schema(self):
        return load_schema(aq_base(self.context).schema, context=self.context)


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
        return load_schema(aq_base(self.context).schema, context=self.context)

    additionalSchemata = ()

    def applyChanges(self, data):
        save_form(self, data, self.context)
