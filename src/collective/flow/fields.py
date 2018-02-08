# -*- coding: utf-8 -*-
from collective.flow.interfaces import IRichTextLabel
from plone.schemaeditor.fields import FieldFactory
from plone.supermodel.exportimport import BaseHandler
from venusianconfiguration import configure
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.schema import Field
from zope.schema._bootstrapinterfaces import IFromUnicode


_ = MessageFactory('collective.flow')


@implementer(IFromUnicode, IRichTextLabel)
class RichTextLabel(Field):
    """A rich text field
    """

    text = u''

    def __init__(self, text=u'', **kw):
        self.text = text
        super(RichTextLabel, self).__init__(**kw)

    def validate(self, value):
        pass

    def fromUnicode(self, s):
        pass


RichTextLabelFactory = FieldFactory(RichTextLabel, _(u'Instruction'))
RichTextLabelHandler = BaseHandler(RichTextLabel)

configure.utility(
    name=u'collective.flow.fields.RichTextLabel',
    component=u'collective.flow.fields.RichTextLabelFactory',
)

configure.utility(
    name=u'collective.flow.fields.RichTextLabel',
    component=u'collective.flow.fields.RichTextLabelHandler',
)
