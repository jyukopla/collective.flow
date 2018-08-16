# -*- coding: utf-8 -*-
from collective.flow import _
from collective.flow.schema import load_schema
from plone.supermodel.interfaces import IDefaultFactory
from venusianconfiguration import configure
from zope.interface import Interface
from zope.interface import provider
from zope.lifecycleevent import IObjectAddedEvent

import datetime
import plone.api as api


@configure.plone.behavior.provides(
    name=u'submission_default_values',
    title=_(u'Submission (calculated) default values'),
    description=_(
        u'Provides support evaluating default values on creation',
    ),
)
class IDefaultValues(Interface):
    """Marker interface for submission comments behavior"""


@configure.subscriber.handler(
    for_=(IDefaultValues, IObjectAddedEvent),
)
def burnDefaultValues(submission, event):
    print submission


@provider(IDefaultFactory)
def username():
    return api.user.get_current().getId()


@provider(IDefaultFactory)
def email():
    return api.user.get_current().getProperty('email', None) or None


@provider(IDefaultFactory)
def fullname():
    name = api.user.get_current().getProperty('fullname', u'')
    if isinstance(name, bytes):
        return unicode(name, 'utf-8', 'ignore')
    else:
        return name


@provider(IDefaultFactory)
def firstname():
    return fullname().split(u' ', 1)[0]


@provider(IDefaultFactory)
def lastname():
    return fullname().split(u' ', 1)[-1]


@provider(IDefaultFactory)
def today():
    return datetime.datetime.now().date()


@provider(IDefaultFactory)
def tomorrow():
    return datetime.datetime.now().date() + datetime.timedelta(1)


@provider(IDefaultFactory)
def week():
    return datetime.datetime.now().date() + datetime.timedelta(7)


@provider(IDefaultFactory)
def twoWeeks():
    return datetime.datetime.now().date() + datetime.timedelta(14)


@provider(IDefaultFactory)
def month():
    return datetime.datetime.now().date() + datetime.timedelta(30)


@provider(IDefaultFactory)
def twoMonths():
    return datetime.datetime.now().date() + datetime.timedelta(60)
