# -*- coding: utf-8 -*-
from collective.flow.browser.folder import FlowSubmitForm
from collective.flow.browser.submission import SubmissionEditForm
from collective.flow.browser.submission import SubmissionView
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.utils import parents
from lxml.etree import CDATA
from lxml.html import builder
from plone.transformchain.interfaces import ITransform
from repoze.xmliter.serializer import XMLSerializer
from scss import Scss
from venusianconfiguration import configure
from zope.interface import implementer
from zope.lifecycleevent import IObjectModifiedEvent


@configure.adapter.factory(
    name='collective.flow.inlineinject',
    for_=(FlowSubmitForm, ICollectiveFlowLayer),
)
@configure.adapter.factory(
    name='collective.flow.inlineinject',
    for_=(SubmissionView, ICollectiveFlowLayer),
)
@configure.adapter.factory(
    name='collective.flow.inlineinject',
    for_=(SubmissionEditForm, ICollectiveFlowLayer),
)
@implementer(ITransform)
class InjectInlineStylesAndScripts(object):

    order = 8900  # after plone.app.theming / diazo

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def transform(self, result, encoding):
        css = u''
        javascript = u''
        for parent in parents(self.published.context, iface=IFlowFolder):
            css = parent._v_css = getattr(  # noqa: P001
                parent,
                '_v_css',
                Scss().compile(parent.css or u''),
            )
            javascript =\
                (parent.javascript or u'').strip().replace(u'\r\n', u'\n')
            break

        root = result.tree.getroot()
        if css:
            head = root.find('head')
            head.append(builder.STYLE(
                css,
                type='text/css',
            ))

        if javascript:
            body = root.find('body')
            # trick LXML to render script with //<!CDATA[[
            script = builder.SCRIPT(u'\n//', type='application/javascript')
            script.append(builder.S(CDATA(u'\n' + javascript + u'\n//')))
            script.getchildren()[0].tail = u'\n'
            body.append(script)

        return result

    def transformBytes(self, result, encoding):
        return None

    def transformUnicode(self, result, encoding):
        return None

    def transformIterable(self, result, encoding):
        if not isinstance(result, XMLSerializer):
            return None

        return self.transform(result, encoding)


# noinspection PyPep8Naming
@configure.subscriber.handler(
    for_=(IFlowFolder, IObjectModifiedEvent),
)
def purgeTransformCache(ob, event):
    try:
        delattr(ob, '_v_css')
    except AttributeError:
        pass
