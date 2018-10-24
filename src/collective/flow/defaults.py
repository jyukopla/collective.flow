# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow import _
from collective.flow.schema import load_schema
from copy import deepcopy
from plone.supermodel.interfaces import IDefaultFactory
from venusianconfiguration import configure
from zope.interface import Interface
from zope.interface import provider
from zope.lifecycleevent import IObjectAddedEvent
from zope.location.interfaces import IContained
from zope.schema._bootstrapinterfaces import IContextAwareDefaultFactory

import datetime
import plone.api as api


@configure.plone.behavior.provides(
    name=u'submission_default_values',
    title=_(u'Submission default values burner'),
    description=_(
        u'Provides support evaluating default values on creation',
    ),
)
class IDefaultValues(Interface):
    """Marker interface for submission comments behavior"""


def set_contained(value, name, parent):
    # Set contained information of schema.Object
    if IContained.providedBy(value):
        value.__name__ = name
        value.__parent__ = aq_base(parent)
    # Set contained information of schema.List|Tuple(value_type=Object)
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            if IContained.providedBy(item):
                item.__name__ = name
                item.__parent__ = aq_base(parent)


@configure.subscriber.handler(
    for_=(IDefaultValues, IObjectAddedEvent),
)
def burnDefaultValues(ob, event):
    schema = load_schema(
        aq_base(ob).schema,
        cache_key=aq_base(ob).schema_digest,
    )
    for name in schema.names():
        field = schema[name]
        try:
            factory = field.defaultFactory
        except AttributeError:
            factory = None
        try:
            default = field.default
        except AttributeError:
            default = None
        if not (factory or default):
            continue
        bound = field.bind(ob)
        try:
            value = bound.get(ob)
        except AttributeError:
            value = None
        if value:
            continue
        if factory:
            if IContextAwareDefaultFactory.providedBy(factory):
                value = factory(ob)
            else:
                value = factory()
        else:
            value = deepcopy(default)
        if value:
            bound.set(ob, value)
            set_contained(value, name, ob)


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
