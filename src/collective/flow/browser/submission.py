# -*- coding: utf-8 -*-
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSubmission
from collective.flow.utils import load_schema
from plone.autoform.view import WidgetsView
from venusianconfiguration import configure
from zope.cachedescriptors import property
from zope.i18nmessageid import MessageFactory


_ = MessageFactory('collective.flow')


@configure.browser.page.class_(
    name='view',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template='submission_templates/view.pt',
)
class SubmissionView(WidgetsView):

    @property.Lazy
    def schema(self):
        return load_schema(self.context.schema_xml)
