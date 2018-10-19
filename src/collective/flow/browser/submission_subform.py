# -*- coding: utf-8 -*-
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSchemaDynamic
from plone.app.z3cform.object import ObjectSubForm
from plone.app.z3cform.object import SubformAdapter
from plone.autoform.form import AutoObjectSubForm
from plone.autoform.interfaces import IAutoObjectSubForm
from venusianconfiguration import configure
from z3c.form.interfaces import IObjectWidget
from z3c.form.interfaces import ISubformFactory
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
@adapter(
    Interface, ICollectiveFlowLayer, Interface, Interface, IObjectWidget,
    Interface, IFlowSchemaDynamic,
)
class SubmissionSubFormAdapter(SubformAdapter):
    factory = SubmissionObjectSubForm
