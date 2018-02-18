# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowAttachment
from collective.flow.interfaces import IFlowSchema
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import FlowSchemaSpecificationDescriptor
from collective.flow.schema import load_schema
from collective.flow.schema import SCHEMA_MODULE
from collective.flow.utils import parents
from persistent.mapping import PersistentMapping
from plone.app.content.interfaces import INameFromTitle
from plone.dexterity.content import Container
from Products.CMFPlone.interfaces import IPloneBaseTool
from Products.CMFPlone.interfaces import IWorkflowChain
from venusianconfiguration import configure
from z3c.form.interfaces import IObjectFactory
from zope.component import adapter
from zope.interface import Interface
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import implementedBy
from zope.interface.declarations import implementer
from zope.interface.declarations import Implements
from zope.interface.declarations import ObjectSpecificationDescriptor
from zope.location.interfaces import IContained


try:
    from Products.CMFPlacefulWorkflow.interfaces import IPlacefulMarker
    HAS_PLACEFUL_WORKFLOW = True
except ImportError:
    HAS_PLACEFUL_WORKFLOW = False


@implementer(IFlowSchema)
class FlowSchema(Container):
    __providedBy__ = FlowSchemaSpecificationDescriptor()


@implementer(IFlowSubmission)
class FlowSubmission(Container):
    __providedBy__ = FlowSchemaSpecificationDescriptor()


class FlowDataSpecificationDescriptor(ObjectSpecificationDescriptor):
    """Assign an instance of this to an object's __providedBy__ to make it
    dynamically declare that it provides the schema referenced in its schema.
    """

    # noinspection PyProtectedMember
    def __get__(self, inst, cls=None):

        if inst is None:
            return getObjectSpecification(cls)

        spec = getattr(inst, '__provides__', None)
        if spec is None:
            spec = implementedBy(cls)

        if inst.__parent__ is not None and inst.__name__ is not None:
            field = load_schema(aq_base(inst.__parent__).schema,
                                context=inst.__parent__)[inst.__name__]
            try:
                schema = field.schema
            except AttributeError:
                schema = field.value_type.schema
        else:
            # Set by FlowObjectFactory
            schema = inst._v_initial_schema

        spec = Implements(schema, spec)

        return spec


@implementer(IFlowSchema, IContained)
class FlowSubmissionData(PersistentMapping):
    __providedBy__ = FlowDataSpecificationDescriptor()

    __parent__ = None
    __name__ = None

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError


@configure.adapter.factory(name='{0:s}.any'.format(SCHEMA_MODULE))
@adapter(Interface, ICollectiveFlowLayer, IFlowSchemaForm, Interface)
@implementer(IObjectFactory)
class FlowObjectFactory(object):
    def __init__(self, context, request, form, widget):
        self.context = context
        self.request = request
        self.form = form
        self.widget = widget

    def __call__(self, value):
        assert isinstance(value, dict), \
            u'Unsupported value: "{0:s}"'.format(str(value))
        ob = FlowSubmissionData()
        ob.update(value)
        ob._v_initial_schema = self.widget.field.schema
        return ob


@configure.adapter.factory(for_=IFlowSchema)
@configure.adapter.factory(for_=IFlowSubmission)
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
    return ob.submission_workflow,


@configure.adapter.factory(for_=(IFlowAttachment, IPloneBaseTool))
@implementer(IWorkflowChain)
def getFlowAttachmentWorkflowChain(ob, tool):
    for parent in parents(ob, iface=IFlowSubmission):
        return parent.attachment_workflow,
    assert False, u'FlowFolder not found for "{0:s}"'.format(
        '/'.join(ob.getPhysicalPath()),
    )


if HAS_PLACEFUL_WORKFLOW:
    configure.adapter(
        for_=(IFlowSubmission, IPlacefulMarker),
        factory=getFlowSubmissionWorkflowChain,
    )
    configure.adapter(
        for_=(IFlowAttachment, IPlacefulMarker),
        factory=getFlowAttachmentWorkflowChain,
    )
