# -*- coding: utf-8 -*-
from collective.flow import _
from collective.flow.content import FlowSubmissionData
from collective.flow.schema import SCHEMA_MODULE
from plone.app.z3cform.converters import AjaxSelectWidgetConverter
from plone.app.z3cform.converters import DatetimeWidgetConverter
from plone.app.z3cform.converters import DateWidgetConverter
from plone.app.z3cform.interfaces import IAjaxSelectWidget
from plone.app.z3cform.interfaces import IDatetimeWidget
from plone.app.z3cform.interfaces import IDateWidget
from plone.supermodel.interfaces import IToUnicode
from venusianconfiguration import configure
from z3c.form.converter import FieldDataConverter
from z3c.form.interfaces import IDataConverter
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.component import getUtility
from zope.dottedname.resolve import resolve
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import Invalid
from zope.schema._bootstrapinterfaces import ConstraintNotSatisfied
from zope.schema._bootstrapinterfaces import IFromUnicode
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IDate
from zope.schema.interfaces import IDatetime
from zope.schema.interfaces import IInterfaceField
from zope.schema.interfaces import IObject
from zope.schema.interfaces import IVocabularyFactory

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
@adapter(IDate, IDateWidget)
@implementer(IDataConverter)
class AccessibleDateWidgetConverter(DateWidgetConverter):
    def toFieldValue(self, value):
        try:
            return super(AccessibleDateWidgetConverter, self).toFieldValue(
                value,
            )
        except (TypeError, ValueError):
            raise Invalid(
                _(
                    u'Date must be in international '
                    u'numerical format (YYYY-MM-DD).',
                ),
            )


@configure.adapter.factory()
@adapter(IDatetime, IDatetimeWidget)
@implementer(IDataConverter)
class AccessibleDatetimeWidgetConverter(DatetimeWidgetConverter):
    def toFieldValue(self, value):
        try:
            return super(AccessibleDatetimeWidgetConverter, self).toFieldValue(
                value,
            )
        except (TypeError, ValueError):
            raise Invalid(
                _(
                    u'Date with time must be in international '
                    u'numerical format (YYYY-MM-DD HH:MM).',
                ),
            )


@configure.adapter.factory()
@adapter(IChoice, IAjaxSelectWidget)
@implementer(IDataConverter)
class AccessibleAjaxSelectWidgetConverter(FieldDataConverter):
    def toFieldValue(self, value):
        try:
            return super(AccessibleAjaxSelectWidgetConverter,
                         self).toFieldValue(value)
        except ConstraintNotSatisfied as e:
            request = getRequest()
            if not request:
                raise
            if IAnnotations(request).get('collective.promises'):
                # skip rendering when unsolved promises exist
                raise
            if not self.widget.vocabulary:
                raise
            # Somewhat enable AjaxSelectWidget to work without javascript by
            # providing valid suggestions on the base of the entered value.
            factory = getUtility(
                IVocabularyFactory,
                name=self.widget.vocabulary,
            )
            try:
                results = factory(query=e.args[0])
            except (IndexError, TypeError):
                raise e
            candidates = []
            for term in results:
                candidates.append(
                    u'"{0:s}" ({1:s})'.format(
                        term.token,
                        translate(term.title, context=request),
                    ),
                )
                if len(candidates) >= 10:
                    break
            if not candidates:
                raise
            if len(candidates) == 1:
                raise Invalid(
                    _(
                        u'Did you mean ${candidate}? '
                        u'Separate multiple values with ";".',
                        mapping={'candidate': candidates[0]},
                    ),
                )
            else:
                raise Invalid(
                    _(
                        u'Did you mean ${candidates} '
                        u'or ${last_candidate}? '
                        u'Separate multiple values with ";".',
                        mapping={
                            'candidates': u', '.join(candidates[:-1]),
                            'last_candidate': candidates[-1],
                        },
                    ),
                )


@configure.adapter.factory()
@adapter(ICollection, IAjaxSelectWidget)
@implementer(IDataConverter)
class SafeAjaxSelectWidgetConverter(AjaxSelectWidgetConverter):
    """Data converter for ICollection fields using the AjaxSelectWidget.
    """

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
