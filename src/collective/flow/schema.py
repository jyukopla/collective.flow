# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.interfaces import IFlowSchemaContext
from collective.flow.interfaces import IFlowSchemaDynamic
from lxml import etree
from plone.alterego import dynamic
from plone.alterego.interfaces import IDynamicObjectFactory
from plone.schemaeditor.interfaces import ISchemaModifiedEvent
from plone.supermodel import loadString
from plone.supermodel import serializeSchema
from plone.supermodel.interfaces import ISchemaPolicy
from plone.supermodel.interfaces import XML_NAMESPACE
from plone.supermodel.utils import ns
from venusianconfiguration import configure
from zope.component import adapter
from zope.interface import implementedBy
from zope.interface import implementer
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import Implements
from zope.interface.declarations import ObjectSpecificationDescriptor

import hashlib
import logging
import threading


logger = logging.getLogger('collective.flow')

# Recursive schema support by resolving additional schemata from thread local
SCHEMA_MODULE = 'collective.flow.schema.dynamic'
dynamic = dynamic.create(SCHEMA_MODULE)
current = threading.local()


# noinspection PyProtectedMember
def load_schema(xml, name=u'', context=None):
    """Load named (or default) supermodel schema from XML source with optional
    cache context (ZCA lookups requires exact schema instance to match lookups)
    """
    try:
        return aq_base(context).__getattribute__('_v_model').schemata[name]
    except AttributeError:
        schema, additional_schemata = split_schema(xml)
        additional = loadString(additional_schemata, policy='collective.flow')
        try:
            current.model = additional
            model = loadString(schema, policy='collective.flow')
            model.schemata.update(additional.schemata)
        finally:
            current.model = None
        if context is not None:
            context._v_model = model
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


def update_schema(xml, schema):
    root = etree.fromstring(xml)
    schema_root = etree.fromstring(serializeSchema(schema))

    for el in root.findall(ns('schema')):
        if not el.attrib.get('name'):
            root.remove(el)

    for el in schema_root.findall(ns('schema')):
        if not el.attrib.get('name'):
            root.append(el)

    return etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf8',
    )


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
        try:
            return current.model.schemata[name]
        except (AttributeError, KeyError):
            if name not in ['V', '__file__']:
                logger.exception(
                    u'Schema "{0:s}" did not resolve:'.format(name))
            return None


class FlowSchemaSpecificationDescriptor(ObjectSpecificationDescriptor):
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

        schema = load_schema(inst.schema, context=inst)
        spec = Implements(schema, spec)

        return spec


@configure.subscriber.handler()
@adapter(IFlowSchemaContext, ISchemaModifiedEvent)
def save_schema(schema_context, event):
    # Update XML schema
    try:
        schema_context.content.schema = update_schema(
            aq_base(schema_context.content).schema,
            schema_context.schema,
        )
    except AttributeError:
        schema_context.content.schema = serializeSchema(schema_context.schema)

    # Update schema digest
    schema_context.content.schema_digest = \
        hashlib.md5(schema_context.content.schema).hexdigest()

    # Purge cache
    try:
        delattr(schema_context.content, '_v_model')
    except AttributeError:
        pass


@configure.utility.factory(name=u'collective.flow')
@implementer(ISchemaPolicy)
class FlowSchemaPolicy(object):
    def module(self, schemaName, tree):
        return SCHEMA_MODULE

    def bases(self, schemaName, tree):
        return IFlowSchemaDynamic,

    def name(self, schemaName, tree):
        # every schema should have the same name to allow generic object
        # factory adapter in ./content.py
        return 'any'
