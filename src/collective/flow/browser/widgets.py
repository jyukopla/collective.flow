# -*- coding: utf-8 -*-
from plone.app.textfield import RichText
from Products.Five.browser.metaconfigure import ViewMixinForTemplates
from venusianconfiguration import configure
from z3c.form.browser.widget import addFieldClass
from z3c.form.browser.widget import HTMLFormElement
from z3c.form.interfaces import IField
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IWidget
from z3c.form.widget import FieldWidget
from z3c.form.widget import Widget
from zope.component import adapter
from zope.i18nmessageid import MessageFactory
from zope.interface import Attribute
from zope.interface import implementer
from zope.interface import implementer_only
from zope.interface import Interface

import os


_ = MessageFactory('collective.flow')


class IRichTextLabel(Interface, IField):
    """Rich text label field"""
    text = RichText(
        title=_(u'Text'),
        default=u'',
        missing_value=u'',
    )
    description = Attribute(u'Labels don\'t need to be described.')
    required = Attribute(u'Labels don\'t require any input value.')


class IRichTextLabelWidget(IWidget):
    """Rich text label widget"""


@implementer_only(IRichTextLabelWidget)
class RichTextLabelWidget(HTMLFormElement, Widget):
    klass = u'rich-text-label-widget'
    css = u'richtextlabel'
    value = u''

    def update(self):
        super(RichTextLabelWidget, self).update()
        addFieldClass(self)


# noinspection PyPep8Naming
@configure.adapter.factory()
@adapter(IRichTextLabel, IFormLayer)
@implementer(IFieldWidget)
def RichTextLabelFieldWidget(field, request):
    return FieldWidget(field, RichTextLabelWidget(request))


@configure.browser.page.class_(
    name=u'ploneform-render-widget',
    layer=IFormLayer,
    for_=IRichTextLabelWidget,
    permission='zope.Public',
    allowed_interface=IRichTextLabelWidget,
    template=os.path.join('widgets_templates', 'richtextlabel.pt'),
)
class RichLabelRenderWidget(ViewMixinForTemplates):
    pass


configure.z3c.widgetTemplate(
    mode=u'input',
    widget=IRichTextLabelWidget,
    layer=IFormLayer,
    template=os.path.join('widgets_templates', 'empty.pt'),
)

configure.z3c.widgetTemplate(
    mode=u'hidden',
    widget=IRichTextLabelWidget,
    layer=IFormLayer,
    template=os.path.join('widgets_templates', 'empty.pt'),
)

configure.z3c.widgetTemplate(
    mode=u'display',
    widget=IRichTextLabelWidget,
    layer=IFormLayer,
    template=os.path.join('widgets_templates', 'empty.pt'),
)
