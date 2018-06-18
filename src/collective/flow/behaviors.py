# -*- coding: utf-8 -*-
"""WIP"""
from Acquisition import aq_base
from collective.flow.interfaces import IFlowSchemaDynamic
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import load_schema
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.behavior import DexterityBehaviorAssignable
# from venusianconfiguration import configure
from zope.component import adapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface


class IFlowSchemaDynamicFields(Interface):
    """Dynamic marker interface for providing dynamic fields"""


alsoProvides(IFlowSchemaDynamic, IFlowSchemaDynamicFields)


@implementer(IBehavior)
class FlowSchemaBehaviorRegistration(object):
    title = None
    description = None
    interface = None
    marker = None
    factory = None

    def __init__(self, iface):
        self.interface = iface


# @configure.adapter.factory()
@adapter(IFlowSubmission)
@implementer(IBehaviorAssignable)
class FlowSubmissionBehaviorAssignable(DexterityBehaviorAssignable):
    def enumerateBehaviors(self):
        for behavior in super(FlowSubmissionBehaviorAssignable,
                              self).enumerateBehaviors():
            yield behavior
        schema = load_schema(
            aq_base(self.context).schema,
            cache_key=aq_base(self.context).schema_digest,
        )
        alsoProvides(schema, IFlowSchemaDynamicFields)
        yield FlowSchemaBehaviorRegistration(schema)


# @configure.adapter.factory()
@implementer(IFormFieldProvider)
@adapter(IFlowSchemaDynamicFields)
def dynamic_form_fields(context):
    return context
