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


@configure.plone.behavior.provides(
    name=u'submission_comments',
    title=_(u'Submission commenting'),
    description=_(
        u'Provides field level comments for Flow Submissions',
    ),
)
class IComments(Interface):
    """Marker interface for submission comments behavior"""


class IDiscussableField(Interface):
    """Marker interface for a discussable field with comments behavior"""


@configure.utility.factory(name='collective.flow.comments')
@implementer(IFieldMetadataHandler)
class DiscussableFieldMetadataHandler(object):

    namespace = FLOW_NAMESPACE
    prefix = FLOW_PREFIX

    def read(self, node, schema, field):
        discussable = node.get(ns('comments', self.namespace)) or ''
        if discussable.lower() in ('true', 'on', 'yes', 'y', '1'):
            alsoProvides(field, IDiscussableField)

    def write(self, node, schema, field):
        if IDiscussableField.providedBy(field):
            node.set(ns('comments', self.namespace), 'true')
