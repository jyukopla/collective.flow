# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from collective.flow.browser.widgets import IRichTextLabel
from collective.flow.content import FlowSubmissionData
from collective.flow.interfaces import IFlowSchemaDynamic
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import iterFlowSchemata
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.interfaces import IJsonCompatible
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from plone.supermodel.utils import mergedTaggedValueDict
from venusianconfiguration import configure
from zope.component import adapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import noLongerProvides
from zope.schema import getFields
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IVocabularyFactory
from zope.security.interfaces import IPermission

import logging
import uuid


logger = logging.getLogger('collective.flow')


class IFullVocabularyValuesExpansion(Interface):
    """Marker interface for expanding vocabulary values"""


def get_term_title(context, request, field, value):
    if not value:
        return value
    elif field.source:
        return field.source.getTerm(value).title
    elif field.vocabularyName:
        factory = getUtility(IVocabularyFactory, name=field.vocabularyName)
        try:
            vocab = factory(context)
            return translate(vocab.getTerm(value).title, context=request)
        except LookupError:
            return value
    return value


@configure.adapter.factory()
@adapter(IChoice, IDexterityContent, IFullVocabularyValuesExpansion)
@implementer(IFieldSerializer)
class ChoiceFieldSerializer(object):
    def __init__(self, field, context, request):
        self.context = context
        self.request = request
        self.field = field

    def __call__(self):
        return json_compatible(self.get_value())

    def get_value(self, default=None):
        value = getattr(
            self.field.interface(self.context),
            self.field.__name__,
            default,
        )
        return dict(
            title=get_term_title(
                self.context,
                self.request,
                self.field,
                value,
            ),
            value=value,
        )


@configure.adapter.factory()
@adapter(ICollection, IDexterityContent, IFullVocabularyValuesExpansion)
@implementer(IFieldSerializer)
class CollectionFieldSerializer(ChoiceFieldSerializer):
    def get_value(self, default=None):
        values = getattr(
            self.field.interface(self.context),
            self.field.__name__,
            default,
        )
        if not values:
            return values
        elif not IChoice.providedBy(self.field.value_type):
            return values
        return [
            dict(
                title=get_term_title(
                    self.context,
                    self.request,
                    self.field.value_type,
                    value,
                ),
                value=value,
            ) for value in values
        ]


def check_permission(permission_name, obj, permission_cache):
    if permission_name is None:
        return True

    if permission_name not in permission_cache:
        permission = queryUtility(IPermission, name=permission_name)
        if permission is None:
            permission_cache[permission_name] = True
        else:
            sm = getSecurityManager()  # noqa: P001
            permission_cache[permission_name] = bool(
                sm.checkPermission(permission.title, obj),  # noqa: P001
            )
    return permission_cache[permission_name]


removable = str(uuid.uuid4())


def serializeToJSON(context, request):
    result = {}
    permission_cache = {}
    for schema in iterFlowSchemata(context):
        if not schema.providedBy(context):
            continue
        read_permissions = mergedTaggedValueDict(schema, READ_PERMISSIONS_KEY)
        for name, field in getFields(schema).items():
            if IRichTextLabel.providedBy(field):
                continue
            if not check_permission(
                    read_permissions.get(name),
                    context,
                    permission_cache,
            ):
                continue

            serializer = queryMultiAdapter((field, context, request),
                                           IFieldSerializer)
            value = serializer()

            # Clean FlowSubmissionData values
            if value == removable:
                value = None
            elif isinstance(value, list):
                value = [v for v in value if v != removable]
            elif isinstance(value, tuple):
                value = tuple([v for v in value if v != removable])
            elif isinstance(value, set):
                value = set([v for v in value if v != removable])

            result[json_compatible(name)] = value
    return result


@configure.adapter.factory()
@adapter(FlowSubmissionData)
@implementer(IJsonCompatible)
def flow_data_converter(value):
    if value and value.values().count(None) != len(value):
        result = dict(value)
        for schema in value.__providedBy__.interfaces():
            if not issubclass(schema, IFlowSchemaDynamic):
                continue
            for name, field in getFields(schema).items():
                if IRichTextLabel.providedBy(field):
                    continue
                serializer = queryMultiAdapter(
                    (field, value.__parent__, getRequest()),
                    IFieldSerializer,
                )
                serializer.context = value
                try:
                    result[name] = serializer()
                except TypeError:
                    logger.exception(u'Unexpected exception:')
                    pass
            break
        return result
    return removable


@configure.adapter.factory(name='flow-values')
@implementer(IExpandableElement)
@adapter(IFlowSubmission, Interface)
class FlowSubmissionValues(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        result = {
            'flow-values': {
                '@id': '{0:s}/@flow-values'.format(
                    self.context.absolute_url(),
                ),
            },
        }
        if expand:
            try:
                alsoProvides(self.request, IFullVocabularyValuesExpansion)
                result['flow-values'].update(
                    serializeToJSON(self.context, self.request),
                )
            finally:
                noLongerProvides(self.request, IFullVocabularyValuesExpansion)
            return result
        return result


# noinspection PyAbstractClass
@configure.plone.service.factory(
    for_=IFlowSubmission,
    method='GET',
    name='@flow-values',
    permission='zope2.View',
)
class FlowSubmissionValuesGet(Service):
    def reply(self):
        factory = FlowSubmissionValues(self.context, self.request)
        return factory(expand=True)['flow-values']
