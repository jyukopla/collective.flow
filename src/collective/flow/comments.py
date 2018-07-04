# -*- coding: utf-8 -*-
from collective.flow import _
from venusianconfiguration import configure
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
