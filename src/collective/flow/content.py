# -*- coding: utf-8 -*-
from collective.flow.interfaces import IFlowSchema
from collective.flow.interfaces import IFlowSubmission
from collective.flow.utils import load_schema
from plone.app.content.interfaces import INameFromTitle
from plone.dexterity.content import Container
from Products.CMFPlone.interfaces import IPloneBaseTool
from Products.CMFPlone.interfaces import IWorkflowChain
from venusianconfiguration import configure
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import implementedBy
from zope.interface.declarations import implementer
from zope.interface.declarations import Implements
from zope.interface.declarations import ObjectSpecificationDescriptor


try:
    from Products.CMFPlacefulWorkflow.interfaces import IPlacefulMarker
    HAS_PLACEFUL_WORKFLOW = True
except ImportError:
    HAS_PLACEFUL_WORKFLOW = False


class FlowSchemaSpecificationDescriptor(ObjectSpecificationDescriptor):
    """Assign an instance of this to an object's __providedBy__ to make it
    dynamically declare that it provides the schema referenced in its
    ``schema_xml`` attribute.
    """

    def __get__(self, inst, cls=None):

        if inst is None:
            return getObjectSpecification(cls)

        spec = getattr(inst, '__provides__', None)
        if spec is None:
            spec = implementedBy(cls)

        schema = load_schema(inst.schema_xml)
        spec = Implements(schema, spec)
        return spec


@implementer(IFlowSchema)
class FlowSchema(Container):
    __providedBy__ = FlowSchemaSpecificationDescriptor()


@implementer(IFlowSubmission)
class FlowSubmission(Container):
    __providedBy__ = FlowSchemaSpecificationDescriptor()


@configure.adapter.factory(for_=IFlowSchema)
@implementer(INameFromTitle)
class NameFromTitle(object):
    def __init__(self, context):
        self.context = context

    @property
    def title(self):
        return self.context.title


@configure.adapter.factory(for_=(IFlowSubmission, IPloneBaseTool))
@implementer(IWorkflowChain)
def getFlowSubmissionWorkflowChain(ob, tool):
    return ob.workflow,


if HAS_PLACEFUL_WORKFLOW:
    @configure.adapter.factory(for_=(IFlowSubmission, IPlacefulMarker))
    def getFlowSubmissionPlacefulWorkflowChain(ob, tool):
        return ob.workflow,
