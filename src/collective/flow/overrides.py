# -*- coding: utf-8 -*-
from collective.flow.schema import SCHEMA_MODULE
from plone.supermodel.interfaces import IToUnicode
from venusianconfiguration import configure
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IInterfaceField

import inspect
import os
import plone.supermodel


configure.include(package=plone.supermodel)


configure.browser.resource(
    name='schemaeditor.js',
    file=os.path.join('browser/schemaeditor.js'),
)


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
