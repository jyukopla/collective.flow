# -*- coding: utf-8 -*-
from collective.flow.content import FlowSubmissionData
from collective.flow.schema import SCHEMA_MODULE
from plone.app.z3cform.converters import AjaxSelectWidgetConverter
from plone.app.z3cform.interfaces import IAjaxSelectWidget
from plone.supermodel.interfaces import IToUnicode
from venusianconfiguration import configure
from z3c.form.interfaces import IDataConverter
from zope.component import adapter
from zope.dottedname.resolve import resolve
from zope.interface import implementer
from zope.schema._bootstrapinterfaces import IFromUnicode
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IInterfaceField
from zope.schema.interfaces import IObject

import inspect
import json
import os
import plone.supermodel


configure.include(package=plone.supermodel)

configure.browser.resource(
    name='schemaeditor.js',
    file=os.path.join('browser/schemaeditor.js'),
)


@configure.adapter.factory()
@adapter(ICollection, IAjaxSelectWidget)
@implementer(IDataConverter)
class SafeAjaxSelectWidgetConverter(AjaxSelectWidgetConverter):
    def toFieldValue(self, value):
        if value is None:
            value = ''
        return super(SafeAjaxSelectWidgetConverter, self).toFieldValue(value)


@configure.adapter.factory()
@implementer(IToUnicode)
@adapter(IInterfaceField)
class InterfaceFieldToUnicode(object):
    def __init__(self, context):
        self.context = context

    def toUnicode(self, value):
        ret = unicode(value.__identifier__)

        # Dynamic sub-schemas in collective flow are named after their
        # field. We can only get the field by going back in stack in the
        # parser:
        if ret.startswith(SCHEMA_MODULE):
            frame = inspect.currentframe()
            while frame is not None:
                if frame.f_locals.get('elementName') == 'field':
                    name = frame.f_locals.get('name')
                    if name:
                        ret = u'{0:s}.{1:s}'.format(SCHEMA_MODULE, name)
                    break
                frame = frame.f_back

        return ret


@configure.adapter.factory()
@implementer(IFromUnicode)
@adapter(IObject)
class ObjectFromUnicode(object):
    def __init__(self, context):
        self.context = context

    def fromUnicode(self, value):
        try:
            data = json.loads(value)
            obj = FlowSubmissionData()
            obj._v_initial_schema = self.context.schema
            obj.update(data)
        except ValueError:
            try:
                obj = resolve(value)
            except ImportError:
                obj = value
        self.context.validate(obj)
        return obj
