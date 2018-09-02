# -*- coding: utf-8 -*-
from collective.flow import _
from venusianconfiguration import configure
from zope.interface import Interface


@configure.plone.behavior.provides(
    name=u'submission_buttons_top',
    title=_(u'Submission top buttons'),
    description=_(
        u'Provides action and workflow buttons above content',
    ),
)
class ITopButtons(Interface):
    """Marker interface for top buttons behavior"""


@configure.plone.behavior.provides(
    name=u'submission_buttons_bottom',
    title=_(u'Submission bottom buttons'),
    description=_(
        u'Provides action and workflow buttons above content',
    ),
)
class IBottomButtons(Interface):
    """Marker interface for bottom buttons behavior"""
