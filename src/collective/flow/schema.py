# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.interfaces import IFlowSchemaDynamic
from lxml import etree
from lxml.etree import tostring
from plone.alterego import dynamic
from plone.alterego.interfaces import IDynamicObjectFactory
from plone.app.dexterity.permissions import DXFieldPermissionChecker
from plone.app.widgets.interfaces import IFieldPermissionChecker
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.utils import iterSchemata
from plone.memoize.volatile import CleanupDict
from plone.schemaeditor.interfaces import ISchemaModifiedEvent
from plone.stringinterp.interfaces import IStringInterpolator
from plone.supermodel import loadString
from plone.supermodel import serializeSchema
from plone.supermodel.interfaces import ISchemaPolicy
from plone.supermodel.interfaces import XML_NAMESPACE
from plone.supermodel.utils import ns
from venusianconfiguration import configure
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.event import notify
from zope.globalrequest import getRequest
from zope.i18n import interpolate as i18n_interpolate
from zope.i18n import negotiate
from zope.i18n import translate
from zope.interface import implementedBy
from zope.interface import implementer
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import Implements
from zope.interface.declarations import ObjectSpecificationDescriptor
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import Object

import hashlib
import logging
import plone.api as api
import threading


logger = logging.getLogger('collective.flow')

# Recursive schema support by resolving additional schemata from thread local
SCHEMA_MODULE = 'collective.flow.schema.dynamic'
SCHEMA_CACHE = CleanupDict()
SCHEMA_CACHE.cleanup_period = 60 * 60 * 12  # 12 hours
dynamic = dynamic.create(SCHEMA_MODULE)
current = threading.local()

CUSTOMIZABLE_TAGS = [
    ns('default'),
    ns('defaultFactory'),
    ns('values'),
]


# noinspection PyProtectedMember
def load_schema(xml, name=u'', language=u'', cache_key=None):
    """Load named (or default) supermodel schema from XML source with optional
    cache key (ZCA lookups require exact schema instance to match lookups)
    """
    if name:
        name = name.strip()
    if language:
        language = u'/' + language.strip() + u'/'
    try:
        try:
            return SCHEMA_CACHE[cache_key].schemata[language + name]
        except KeyError:
            return SCHEMA_CACHE[cache_key].schemata[name]
    except KeyError:
        schema, additional_schemata = split_schema(xml)
        additional = loadString(additional_schemata, policy='collective.flow')
        try:
            current.model = additional
            model = loadString(schema, policy='collective.flow')
            model.schemata.update(additional.schemata)
        finally:
            current.model = None
        if cache_key is not None:
            SCHEMA_CACHE[cache_key] = model
            logger.info('Cache MISS. Size {0:d}'.format(len(SCHEMA_CACHE)))
        try:
            return model.schemata[language + name]
        except KeyError:
            return model.schemata[name]


def split_schema(xml):
    """Split XML supermodel schema into main schema and additional schemata"""
    root = etree.fromstring(xml)

    stack = []
    for el in root.findall(ns('schema')):
        if el.attrib.get('name'):
            stack.append(el)
            root.remove(el)

    schema = etree.tostring(root)

    for el in root.findall(ns('schema')):
        root.remove(el)
    while stack:
        root.append(stack.pop())

    additional_schemata = etree.tostring(root)

    return schema, additional_schemata


def update_schema(xml, schema, name=u'', language=u''):
    root = etree.fromstring(xml)

    if name:
        name = name.strip()
    if language:
        language = u'/' + language.strip() + u'/'
    if isinstance(schema, str):
        schema_root = etree.fromstring(schema)
    else:
        schema_root = etree.fromstring(serializeSchema(schema, name))

    for el in root.findall(ns('schema')):
        name_ = el.attrib.get('name', u'')
        if name_ == name + language:
            root.remove(el)
            break
        elif name_ == name and not language:
            root.remove(el)
            break

    for el in schema_root.findall(ns('schema')):
        name_ = el.attrib.get('name', u'')
        if name_ == name + language:
            root.append(el)
            break
        elif name_ == name and language:
            el.attrib['name'] = language
            root.append(el)
            break
        elif name_ == name and not language:
            root.append(el)
            break

    return etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf8',
    )


def customized_schema(original, custom):
    root = etree.fromstring(custom)
    fields = {}

    # copy customizable data from customized schema
    for schema in root.findall(ns('schema')):
        if schema.attrib.get('name', u'') != u'':
            continue
        for field in schema.xpath(
                'supermodel:field',
                namespaces=dict(supermodel=XML_NAMESPACE),
        ):
            name = field.attrib['name']
            for node in [child for child in field.getchildren()
                         if child.tag in CUSTOMIZABLE_TAGS]:
                fields.setdefault(name, {})
                fields[name][node.tag] = node

    # apply customizations for copy of original schema
    root = etree.fromstring(original)
    for schema in root.findall(ns('schema')):
        if schema.attrib.get('name', u'') != u'':
            continue
        for name in fields:
            for field in schema.xpath(
                    'supermodel:field[@name="{0:s}"]'.format(name),
                    namespaces=dict(supermodel=XML_NAMESPACE),
            ):
                for node in [child for child in field.getchildren()
                             if child.tag in fields[name]]:
                    if (node.text or u'').strip() or node.getchildren():
                        # if master has value, drop the customization
                        del fields[name][node.tag]
                    else:
                        # if master is empty, apply the customization
                        field.replace(node, fields[name].pop(node.tag))
                for node in fields[name].values():
                    field.append(node)

    # serialize
    customized = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf8',
    )

    return customized


def remove_attachments(xml):
    """Strip schema schema from binary fields"""
    root = etree.fromstring(xml)
    for el in root.xpath('//supermodel:field',
                         namespaces=dict(supermodel=XML_NAMESPACE)):
        if el.attrib.get('type') in [
                'plone.namedfile.field.NamedBlobFile',
                'plone.namedfile.field.NamedBlobImage',
        ]:
            el.getparent().remove(el)
    return etree.tostring(root)


@configure.utility.factory(name=SCHEMA_MODULE)
@implementer(IDynamicObjectFactory)
class FlowSchemaModuleFactory(object):
    def __call__(self, name, module):
        if name:
            name = name.strip()
        try:
            return current.model.schemata[name]
        except (AttributeError, KeyError):
            if name not in ['V', '__file__']:
                logger.exception(
                    u'Schema "{0:s}" did not resolve:'.format(name),
                )
                return loadString(
                    DEFAULT_SCHEMA,
                    policy='collective.flow',
                ).schemata['']
            return None


class FlowSchemaSpecificationDescriptor(ObjectSpecificationDescriptor):
    """Assign an instance of this to an object's __providedBy__ to make it
    dynamically declare that it provides the schema referenced in its schema.
    """

    # noinspection PyProtectedMember
    def __get__(self, inst, cls=None):
        if inst is None:
            return getObjectSpecification(cls)

        request = getRequest()
        annotations = IAnnotations(request)
        digest = inst.schema_digest

        # Return cached spec from request
        if not getattr(self, '__recursion__', False):
            spec = annotations.get(self.__class__.__name__ + '.' + digest)
            if spec is not None:
                return spec

        spec = getattr(inst, '__provides__', None)
        if spec is None:
            spec = implementedBy(cls)

        schema = load_schema(inst.schema, cache_key=inst.schema_digest)

        if getattr(self, '__recursion__', False):
            return Implements(schema, spec)

        self.__recursion__ = True
        dynamically_provided = []
        try:
            assignable = IBehaviorAssignable(inst, None)
            if assignable is not None:
                for behavior_registration in assignable.enumerateBehaviors():
                    if behavior_registration.marker:
                        dynamically_provided.append(
                            behavior_registration.marker,
                        )
        finally:
            del self.__recursion__

        spec = Implements(schema, spec, *dynamically_provided)

        # Cache spec into request
        annotations[self.__class__.__name__ + '.' + digest] = spec
        return spec


@configure.adapter.factory()
@implementer(IFieldPermissionChecker)
@adapter(IFlowSchemaDynamic)
class FlowSchemaFieldPermissionChecker(DXFieldPermissionChecker):
    DEFAULT_PERMISSION = 'Modify portal content'

    def _get_schemata(self):
        schemata = tuple(iterSchemata(self.context))
        try:
            schema = load_schema(
                aq_base(self.context).schema,
                cache_key=aq_base(self.context).schema_digest,
            )
            schemata = schemata + tuple((schema, ))
        except AttributeError:
            pass
        return schemata


def save_schema(context, schema=None, xml=None, language=u''):
    if schema:
        # Update XML schema (got update from model designer)
        try:
            context.schema = update_schema(
                aq_base(context).schema,
                schema,
                language=language,
            )
            # TODO: synchronize languages
        except AttributeError:
            context.schema = serializeSchema(schema)
        for name in schema:
            value_type = getattr(schema[name], 'value_type', None)
            if isinstance(value_type, Object):
                context.schema = update_schema(
                    aq_base(context).schema,
                    value_type.schema,
                    name=name,
                )
    else:
        # Override with new XML (got update from modelxml editor)
        context.schema = xml

    # Update schema digest
    context.schema_digest = hashlib.md5(context.schema).hexdigest()

    # Notify that object has been modified
    notify(
        ObjectModifiedEvent(
            context,
            Attributes(IFlowFolder, 'schema', 'schema_digest'),
        ),
    )


@configure.subscriber.handler()
@adapter(IFlowSchemaContext, ISchemaModifiedEvent)
def save_schema_from_schema_context(schema_context, event=None):
    assert event
    language = negotiate(context=getRequest())
    default_language = api.portal.get_default_language()
    save_schema(
        schema_context.content,
        schema=schema_context.schema,
        language=language != default_language and language or u'',
    )


@configure.utility.factory(name=u'collective.flow')
@implementer(ISchemaPolicy)
class FlowSchemaPolicy(object):
    def module(self, schemaName, tree):
        return SCHEMA_MODULE

    def bases(self, schemaName, tree):
        if 'IFlowSchemaDynamic' not in tostring(tree):
            return tuple((IFlowSchemaDynamic, ))
        else:
            return ()

    def name(self, schemaName, tree):
        # every schema should have the same name to allow generic object
        # factory adapter in ./content.py
        return 'any'


def interpolate(template, ob, request=None):
    if request is None:
        request = getRequest()
    # Currently interpolation uses always the default language by purpose,
    # because multilingual support would result e.g. in language specific
    # folder structure (because of the current use cases of interpolation).
    schema = load_schema(
        aq_base(ob).schema,
        cache_key=aq_base(ob).schema_digest,
    )
    mapping = {}
    for name in schema.names():
        field = schema[name]
        bound = field.bind(ob)
        try:
            value = bound.get(ob)
        except AttributeError:
            mapping[name] = ''
            continue
        try:
            mapping[name] = translate(
                bound.vocabulary.getTerm(value).title,
                context=request,
            )
        except (AttributeError, LookupError):
            mapping[name] = value
    interpolator = IStringInterpolator(ob)
    value = interpolator(i18n_interpolate(template or u'', mapping))
    return value
