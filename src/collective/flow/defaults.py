# -*- coding: utf-8 -*-
from plone import api
from plone.supermodel.interfaces import IDefaultFactory
from zope.interface import provider

import datetime


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
    return fullname().split(u' ', 1)[-0]


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
