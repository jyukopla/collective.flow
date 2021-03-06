# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.interfaces import DEFAULT_SCHEMA
from collective.flow.interfaces import FLOW_NAMESPACE
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowImpersonation
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.interfaces import IFlowSchemaDynamic
from collective.flow.utils import get_navigation_root_language
from contextlib import contextmanager
from copy import deepcopy
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
from plone.supermodel import serializeSchema as _serializeSchema
from plone.supermodel.interfaces import ISchemaPolicy
from plone.supermodel.interfaces import XML_NAMESPACE
from plone.supermodel.utils import ns
from venusianconfiguration import configure
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.event import notify
from zope.globalrequest import getRequest
from zope.i18n import INegotiator
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
from zope.schema._bootstrapinterfaces import IContextAwareDefaultFactory

import hashlib
import logging
import re
import threading


logger = logging.getLogger('collective.flow')

# Recursive schema support by resolving additional schemata from thread local
SCHEMA_MODULE = 'collective.flow.schema.dynamic'
SCHEMA_CACHE = CleanupDict()
SCHEMA_CACHE.cleanup_period = 60 * 60 * 12  # 12 hours
dynamic = dynamic.create(SCHEMA_MODULE)
current = threading.local()

IS_TRANSLATION = re.compile(r'^/[a-z\-]+/$')

CUSTOMIZABLE_TAGS = [
    ns('default'),
    ns('defaultFactory'),
    ns('values'),
]

SYNCHRONIZED_TAGS = [
    ns('default'),
    ns('values'),
]


def serializeSchema(schema, name):
    """Patched serializeSchema"""
    xml = _serializeSchema(schema, name)
    # Something in plone.autoform integration for supermodel is
    # duplicating form:mode="display -values leading huge XML and
    # performance issues in parsing.
    while 'form:mode="display display' in xml:
        xml = xml.replace(
            'form:mode="display display',
            'form:mode="display',
        )
    return xml


# noinspection PyProtectedMember
def load_model(xml, cache_key=None):
    """Load supermodel instance from XML source with optional
    cache key (ZCA lookups require exact schema instance to match lookups)
    """
    try:
        return SCHEMA_CACHE[cache_key]
    except KeyError:
        schemata, additional_schemata = split_schema(xml)
        additional = loadString(additional_schemata, policy='collective.flow')
        try:
            current.model = additional
            model = loadString(schemata, policy='collective.flow')
            model.schemata.update(additional.schemata)
        finally:
            current.model = None
        if cache_key is not None:
            SCHEMA_CACHE[cache_key] = model
        return model


# noinspection PyProtectedMember
def load_schema(xml, name=u'', language=u'', cache_key=None):
    """Load named (or default) supermodel schema from XML source with optional
    cache key (ZCA lookups require exact schema instance to match lookups)
    """
    if name:
        name = name.strip()
    if language:
        language = u'/' + language.strip() + u'/'
    else:
        language = u''
    model = load_model(xml, cache_key=cache_key)
    try:
        return model.schemata[language + name]
    except KeyError:
        return model.schemata[name]


def split_schema(xml):
    """Split XML supermodel schema into main schemata and additional
    schemata """
    root = etree.fromstring(xml)

    stack = []
    for el in root.findall(ns('schema')):
        if el.attrib.get('name') and not IS_TRANSLATION.match(
                el.attrib.get('name')):
            stack.append(el)
            root.remove(el)

    schemata = etree.tostring(root)

    for el in root.findall(ns('schema')):
        root.remove(el)
    while stack:
        root.append(stack.pop())

    additional_schemata = etree.tostring(root)

    return schemata, additional_schemata


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

    # Drop default values from fields with defaultFactories
    for factory in root.xpath(
            '//supermodel:defaultFactory',
            namespaces=dict(supermodel=XML_NAMESPACE),
    ):
        for default in factory.itersiblings(ns('default'), preceding=False):
            default.getparent().remove(default)
        for default in factory.itersiblings(ns('default'), preceding=True):
            default.getparent().remove(default)

    return synchronized_schema(
        etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf8',
        ),
        master=language,
    )


def customized_schema(original, custom):
    root = etree.fromstring(custom)
    fields = {}
    # fields_schemata = {}

    # copy customizable data from customized schema
    for schema in root.findall(ns('schema')):
        schema_name = schema.attrib.get('name') or u''
        fields.setdefault(schema_name, {})
        # fields_schemata.setdefault(schema_name, {})
        for field in schema.xpath(
                'supermodel:field',
                namespaces=dict(supermodel=XML_NAMESPACE),
        ):
            name = field.attrib['name']
            for node in [child for child in field.getchildren()
                         if child.tag in CUSTOMIZABLE_TAGS]:
                fields[schema_name].setdefault(name, {})
                fields[schema_name][name][node.tag] = node

            # NOTE: This code was written to copy sub schema customizations
            # from the default language for new translated languages, but
            # it is not currently possible to customize sub schemas TTW.
            #
            # field_schemata = field.xpath(
            #     'supermodel:schema',
            #     namespaces=dict(supermodel=XML_NAMESPACE),
            # ) + field.xpath(
            #     '*/supermodel:schema',
            #     namespaces=dict(supermodel=XML_NAMESPACE),
            # )
            # for schema_ in field_schemata:
            #     name_ = schema_.text or ''
            #     if not name_.startswith(SCHEMA_MODULE + '.'):
            #         continue
            #     fields_schemata[schema_name][name] = name_[
            #         len(SCHEMA_MODULE + '.'):]

    # copy original schema
    root = etree.fromstring(original)

    # copy default language customizations for missing languages
    for schema in root.findall(ns('schema')):
        schema_name = schema.attrib.get('name') or u''

        if schema_name in fields:
            continue

        if not IS_TRANSLATION.match(schema_name):
            continue

        canonical_name = schema_name[4:]
        if canonical_name not in fields:
            continue

        fields.setdefault(
            schema_name,
            deepcopy(fields[canonical_name]),
        )

        # NOTE: This code was written to copy sub schema customizations
        # from the default language for new translated languages, but
        # it is not currently possible to customize sub schemas TTW.

        # if canonical_name not in fields_schemata:
        #     continue
        #
        # for field in schema.xpath(
        #         'supermodel:field',
        #         namespaces=dict(supermodel=XML_NAMESPACE),
        # ):
        #     name = field.attrib['name']
        #     if name not in fields_schemata[canonical_name]:
        #         continue
        #
        #     field_schemata = field.xpath(
        #         'supermodel:schema',
        #         namespaces=dict(supermodel=XML_NAMESPACE),
        #     ) + field.xpath(
        #         '*/supermodel:schema',
        #         namespaces=dict(supermodel=XML_NAMESPACE),
        #     )
        #     for schema_ in field_schemata:
        #         name_ = schema_.text or ''
        #         if not name_.startswith(SCHEMA_MODULE + '.'):
        #             continue
        #         name_ = name_[len(SCHEMA_MODULE + '.'):]
        #         fields.setdefault(
        #             name_,
        #             deepcopy(fields[fields_schemata[canonical_name][name]]),
        #         )

    # apply customizations for copy of original schema
    for schema in root.findall(ns('schema')):
        schema_name = schema.attrib.get('name') or u''
        fields.setdefault(schema_name, {})
        for name in fields[schema_name]:
            fields[schema_name].setdefault(name, {})
            for field in schema.xpath(
                ('supermodel:field[@name="{0:s}" and '
                 '@flow:customizable="true"]').format(name),
                    namespaces=dict(supermodel=XML_NAMESPACE,
                                    flow=FLOW_NAMESPACE),
            ):
                for node in [child for child in field.getchildren()
                             if child.tag in fields[schema_name][name]]:
                    field.replace(
                        node,
                        fields[schema_name][name].pop(node.tag),
                    )
                for node in fields[schema_name][name].values():
                    field.append(node)

    # serialize
    customized = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf8',
    )

    return customized


def merge_vocabularies(from_node, to_node):
    if from_node.tag == ns('values'):
        vocabulary = {}
        for term in from_node.iterchildren():
            vocabulary[term.attrib.get('key') or term.text] = term.text
        for term in to_node.iterchildren():
            key = term.attrib.get('key') or term.text
            term.text = vocabulary.get(key) or term.text
    return to_node


def synchronized_schema(xml, master=u''):
    """Synchronize defaults and values between schemas"""
    root = etree.fromstring(xml)
    fields = {}

    # copy values from master schema
    for schema in root.findall(ns('schema')):
        schema_name = schema.attrib.get('name') or u''
        if schema_name != master:
            continue

        # fields_schemata.setdefault(schema_name, {})
        for field in schema.xpath(
                'supermodel:field',
                namespaces=dict(supermodel=XML_NAMESPACE),
        ):
            name = field.attrib['name']
            type_ = field.attrib['type']
            if type_ in [
                    'zope.schema.Text',
                    'zope.schema.TextLine',
                    'plone.app.textfield.RichText',
            ]:
                # Skip synchronizing text fields, because they are
                # expected to contain localization specific data
                continue
            for node in [child for child in field.getchildren()
                         if child.tag in SYNCHRONIZED_TAGS]:
                fields.setdefault(name, {})
                fields[name][node.tag] = node

    # Re-parse schema to avoid "moving instead of cloning" mistakes later
    root = etree.fromstring(xml)

    # apply values for other languages
    for schema in root.findall(ns('schema')):
        schema_name = schema.attrib.get('name') or u''

        # skip master schema
        if schema_name == master:
            continue

        # skip object field schemas
        if not IS_TRANSLATION.match(schema_name) and schema_name != '':
            continue

        for name in fields:
            fields.setdefault(name, {})
            for field in schema.xpath(
                    'supermodel:field[@name="{0:s}"]'.format(name),
                    namespaces=dict(supermodel=XML_NAMESPACE,
                                    flow=FLOW_NAMESPACE),
            ):
                for node in [child for child in field.getchildren()
                             if child.tag in fields[name]]:
                    field.replace(
                        node,
                        merge_vocabularies(node, fields[name].pop(node.tag)),
                    )
                for node in fields[name].values():
                    field.append(node)

    # serialize
    synchronized = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf8',
    )

    return synchronized


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

        try:
            digest = inst.schema_digest
        except AttributeError:
            spec = getattr(inst, '__provides__', None)
            if spec is None:
                return implementedBy(cls)
            else:
                return spec

        # Return cached spec from request
        if not getattr(self, '__recursion__', False):
            spec = annotations.get(self.__class__.__name__ + '.' + digest)
            if spec is not None:
                return spec

        spec = getattr(inst, '__provides__', None)
        if spec is None:
            spec = implementedBy(cls)

        model = load_model(inst.schema, cache_key=inst.schema_digest)
        schemata = [
            model.schemata[name]
            for name in model.schemata
            if name in [u'', u'++add++'] or
            IS_TRANSLATION.match(name.split(u'++add++')[0])
        ]
        schemata.append(spec)

        if getattr(self, '__recursion__', False):
            return Implements(*schemata)

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

        schemata.extend(dynamically_provided)
        spec = Implements(*schemata)

        # Cache spec into request
        annotations[self.__class__.__name__ + '.' + digest] = spec
        return spec


def iterFlowSchemata(context, with_impersonation=False):
    try:
        schema = load_schema(
            aq_base(context).schema,
            cache_key=aq_base(context).schema_digest,
        )
        yield schema
        for name in schema:
            value_type = getattr(schema[name], 'value_type', None)
            schema_ = getattr(value_type, 'schema', None)
            if schema_:
                yield schema_
    except AttributeError:
        pass
    try:
        schema = load_schema(
            aq_base(context).schema,
            name='++add++',
            cache_key=aq_base(context).schema_digest,
        )
        yield schema
    except (AttributeError, KeyError):
        pass
    if with_impersonation:
        try:
            schema = load_schema(
                aq_base(context).schema,
                name='@@impersonate',
                cache_key=aq_base(context).schema_digest,
            )
            yield schema
        except (AttributeError, KeyError):
            pass
        yield IFlowImpersonation


@configure.adapter.factory()
@implementer(IFieldPermissionChecker)
@adapter(IFlowSchemaDynamic)
class FlowSchemaFieldPermissionChecker(DXFieldPermissionChecker):
    DEFAULT_PERMISSION = 'Modify portal content'

    def _get_schemata(self):
        return list(iterSchemata(self.context)) + list(
            iterFlowSchemata(self.context, with_impersonation=True),
        )


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
            context.schema = serializeSchema(schema, name=u'')
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
    language = negotiate(context=getRequest()) or u''
    context_language = get_navigation_root_language(schema_context.content)
    save_schema(
        schema_context.content,
        schema=schema_context.schema,
        language=not context_language.startswith(language or context_language) and language or u'',
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


@implementer(INegotiator)
class FixedNegotiator(object):
    def __init__(self, language):
        self.language = language

    # noinspection PyUnusedLocal
    def getLanguage(self, *args, **kwargs):
        return self.language


@contextmanager
def fixed_language(language, request=None):
    """Context manager for forcing the current language by temporarily
    replacing the global language negotiator with a fixed language negotiator
    """
    if request is None:
        request = getRequest()
    current_language = negotiate(context=request) or u''
    if current_language != language:
        original = queryUtility(INegotiator)
        if original is not None:
            gsm = getGlobalSiteManager()
            replacement = FixedNegotiator(language)
            gsm.registerUtility(replacement, provided=INegotiator)
            try:
                yield
            finally:
                gsm.unregisterUtility(replacement, provided=INegotiator)
                gsm.registerUtility(original, provided=INegotiator)
        else:
            yield
    else:
        yield


# Currently interpolation uses always the default language by purpose,
# because multilingual support would result e.g. in language specific
# folder structure (because of the current use cases of interpolation).
def interpolate(template, ob, request=None, language=None):
    if language:
        with fixed_language(language):
            return _interpolate(template, ob, request)
    else:
        return _interpolate(template, ob, request)


def _interpolate(template, ob, request=None):
    if request is None:
        request = getRequest()
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
            value = ''
        if not value:
            try:
                factory = field.defaultFactory
            except AttributeError:
                factory = None
            if not factory:
                continue
            if IContextAwareDefaultFactory.providedBy(factory):
                value = factory(ob)
            else:
                value = factory()
        if not value:
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
