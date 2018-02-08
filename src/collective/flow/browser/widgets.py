# -*- coding: utf-8 -*-
from collective.flow.interfaces import IRichTextLabel
from collective.flow.interfaces import IRichTextLabelWidget
from Products.Five.browser.metaconfigure import ViewMixinForTemplates
from venusianconfiguration import configure
from z3c.form.browser import widget
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from z3c.form.widget import FieldWidget
from z3c.form.widget import Widget
from zope.component import adapter
from zope.interface import implementer
from zope.interface import implementer_only

import os


@implementer_only(IRichTextLabelWidget)
class RichTextLabelWidget(widget.HTMLFormElement, Widget):
    klass = u'rich-text-label-widget'
    css = u'richtextlabel'
    value = u''

    def update(self):
        super(RichTextLabelWidget, self).update()
        widget.addFieldClass(self)


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
