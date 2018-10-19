# -*- coding: utf-8 -*-
from collective.flow import _
from collective.flow.interfaces import FLOW_NAMESPACE
from collective.flow.interfaces import FLOW_PREFIX
from plone.supermodel.parser import IFieldMetadataHandler
from plone.supermodel.utils import ns
from venusianconfiguration import configure
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface


class ICustomizableField(Interface):
    """Marker interface for a customizable field in sub-folders"""


@configure.utility.factory(name='collective.flow.customizable')
@implementer(IFieldMetadataHandler)
class CustomizableFieldMetadataHandler(object):

    namespace = FLOW_NAMESPACE
    prefix = FLOW_PREFIX

    def read(self, node, schema, field):
        discussable = node.get(ns('customizable', self.namespace)) or ''
        if discussable.lower() in ('true', 'on', 'yes', 'y', '1'):
            alsoProvides(field, ICustomizableField)

    def write(self, node, schema, field):
        if ICustomizableField.providedBy(field):
            node.set(ns('customizable', self.namespace), 'true')
