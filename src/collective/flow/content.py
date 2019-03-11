# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.browser.folder import FlowSubmitForm
from collective.flow.browser.folder import FlowSubmitFormGroup
from collective.flow.interfaces import ATTACHMENT_WORKFLOW_FIELD
from collective.flow.interfaces import DEFAULT_ATTACHMENT_WORKFLOW
from collective.flow.interfaces import DEFAULT_SUBMISSION_WORKFLOW
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowAttachment
from collective.flow.interfaces import IFlowSchema
from collective.flow.interfaces import IFlowSubmission
from collective.flow.interfaces import IFlowSubmissionComment
from collective.flow.interfaces import SUBMISSION_WORKFLOW_FIELD
from collective.flow.schema import FlowSchemaSpecificationDescriptor
from collective.flow.schema import IS_TRANSLATION
from collective.flow.schema import load_model
from collective.flow.schema import SCHEMA_MODULE
from persistent.mapping import PersistentMapping
from plone.app.content.interfaces import INameFromTitle
from plone.dexterity.content import Container
from plone.supermodel.interfaces import IDefaultFactory
from plone.supermodel.interfaces import IToUnicode
from Products.CMFPlone.interfaces import IPloneBaseTool
from Products.CMFPlone.interfaces import IWorkflowChain
from venusianconfiguration import configure
from z3c.form.interfaces import IMultiWidget
from z3c.form.interfaces import IObjectFactory
from z3c.form.interfaces import IValue
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.dottedname.resolve import resolve
from zope.globalrequest import getRequest
from zope.interface import Interface
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import implementedBy
from zope.interface.declarations import implementer
from zope.interface.declarations import Implements
from zope.interface.declarations import ObjectSpecificationDescriptor
from zope.location.interfaces import IContained
from zope.schema.interfaces import IContextAwareDefaultFactory
from zope.schema.interfaces import IObject

import json


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
    submission_behaviors = None


class FlowDataSpecificationDescriptor(ObjectSpecificationDescriptor):
    """Assign an instance of this to an object's __providedBy__ to make it
    dynamically declare that it provides the schema referenced in its schema.
    """

    # noinspection PyProtectedMember
    def __get__(self, inst, cls=None):
        if inst is None:
            return getObjectSpecification(cls)

        request = getRequest()
        annotations = IAnnotations(request)

        # Return cached spec from request
        if inst.__parent__ is not None and inst.__name__ is not None:
            digest = inst.__parent__.schema_digest
            key = '.'.join([self.__class__.__name__, digest, inst.__name__])
            spec = annotations.get(key)
            if spec is not None:
                return spec

            spec = getattr(inst, '__provides__', None)
            if spec is None:
                spec = implementedBy(cls)

            model = load_model(
                aq_base(inst.__parent__).schema,
                cache_key=inst.__parent__.schema_digest,
            )
            schemata = []
            for schema in [model.schemata[name]
                           for name in model.schemata
                           if name == u'' or IS_TRANSLATION.match(name)]:
                try:
                    field = schema[inst.__name__]
                except AttributeError:
                    continue
                try:
                    schemata.append(field.schema)
                except AttributeError:
                    schemata.append(field.value_type.schema)
            schemata.append(spec)

            spec = Implements(*schemata)

            # Cache spec into request
            annotations[key] = spec

        else:

            spec = getattr(inst, '__provides__', None)
            if spec is None:
                spec = implementedBy(cls)

            # Set by FlowSubmissionDataFactory
            schemata = [inst._v_initial_schema, spec]

            spec = Implements(*schemata)

        return spec


@implementer(IFlowSchema, IContained)
class FlowSubmissionData(PersistentMapping):
    __providedBy__ = FlowDataSpecificationDescriptor()
    __allow_access_to_unprotected_subobjects__ = 1

    __parent__ = None
    __name__ = None

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError


def dottedname(value):
    prefix = value.__module__
    name = value.__name__
    try:
        candidate = prefix + '.' + name
        if resolve(candidate) is value:
            return candidate
    except ImportError:
        pass

    module = resolve(prefix)
    for key in dir(module):
        if key.startswith('_'):
            continue
        try:
            candidate = prefix + '.' + key + '.' + name
            if resolve(candidate) is value:
                return candidate
        except ImportError:
            pass
    return value


@configure.adapter.factory()
@implementer(IToUnicode)
@adapter(IObject)
class ObjectToUnicode(object):
    def __init__(self, context):
        self.context = context

    def toUnicode(self, value):
        if isinstance(value, FlowSubmissionData):
            return json.dumps(dict(value))
        elif IContextAwareDefaultFactory.providedBy(value):
            return dottedname(value)
        elif IDefaultFactory.providedBy(value):
            return dottedname(value)
        raise NotImplementedError()


@configure.adapter.factory(name='{0:s}.any'.format(SCHEMA_MODULE))
@adapter(Interface, ICollectiveFlowLayer, Interface, Interface)
@implementer(IObjectFactory)
class FlowSubmissionDataFactory(object):
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


@configure.adapter.factory(
    name='default',
    for_=(Interface, Interface, FlowSubmitForm, Interface, IMultiWidget),
)
@configure.adapter.factory(
    name='default',
    for_=(Interface, Interface, FlowSubmitFormGroup, Interface, IMultiWidget),
)
@implementer(IValue)
class DefaultRoot(object):
    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget

    def get(self):
        value = self.field.default or []
        for i in range((self.field.min_length or 0) - len(value)):
            ob = FlowSubmissionData()
            ob._v_initial_schema = self.field.value_type.schema
            for name in ob._v_initial_schema.names():
                ob[name] = None
            value.append(ob)
        return value


@configure.adapter.factory(for_=IFlowSchema)
@configure.adapter.factory(for_=IFlowSubmission)
@implementer(INameFromTitle)
class NameFromTitle(object):
    def __init__(self, context):
        self.context = context

    @property
    def title(self):
        return self.context.title


# noinspection PyPep8Naming
@configure.adapter.factory(for_=(IFlowSubmission, IPloneBaseTool))
@implementer(IWorkflowChain)
def getFlowSubmissionWorkflowChain(ob, tool):
    try:
        wf_id = ob.aq_explicit.aq_acquire(SUBMISSION_WORKFLOW_FIELD)
    except AttributeError:
        wf_id = DEFAULT_SUBMISSION_WORKFLOW
    if wf_id:
        return tuple((wf_id, ))
    else:
        return ()


# noinspection PyPep8Naming
@configure.adapter.factory(for_=(IFlowAttachment, IPloneBaseTool))
@implementer(IWorkflowChain)
def getFlowAttachmentWorkflowChain(ob, tool):
    try:
        wf_id = ob.aq_explicit.aq_acquire(ATTACHMENT_WORKFLOW_FIELD)
    except AttributeError:
        wf_id = DEFAULT_ATTACHMENT_WORKFLOW
    if wf_id:
        return tuple((wf_id, ))
    else:
        return ()


# noinspection PyPep8Naming
@configure.adapter.factory(for_=(IFlowSubmissionComment, IPloneBaseTool))
@implementer(IWorkflowChain)
def getFlowSubmissionCommentWorkflowChain(ob, tool):
    return tuple(('acknowledgement_workflow', ))


if HAS_PLACEFUL_WORKFLOW:
    configure.adapter(
        for_=(IFlowSubmission, IPlacefulMarker),
        factory=getFlowSubmissionWorkflowChain,
    )
    configure.adapter(
        for_=(IFlowAttachment, IPlacefulMarker),
        factory=getFlowAttachmentWorkflowChain,
    )
    configure.adapter(
        for_=(IFlowSubmissionComment, IPlacefulMarker),
        factory=getFlowSubmissionCommentWorkflowChain,
    )
