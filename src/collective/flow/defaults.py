# -*- coding: utf-8 -*-
from plone import api
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory


def safe_unicode(st):
    if isinstance(st, str):
        st = st.decode('utf8')
    return st


class date(object):
    @staticmethod
    @provider(IContextAwareDefaultFactory)
    def now(context):
        import datetime
        return datetime.datetime.now().date()


class datetime(object):
    @staticmethod
    @provider(IContextAwareDefaultFactory)
    def now(context):
        import datetime
        return datetime.datetime.now()


# noinspection PyPep8Naming
class user(object):
    @staticmethod
    @provider(IContextAwareDefaultFactory)
    def username(context):
        member = api.user.get_current()
        if member is None:
            return None
        return safe_unicode(member.getId())

    @staticmethod
    @provider(IContextAwareDefaultFactory)
    def firstname(context):
        member = api.user.get_current()
        if member is None:
            return None
        value = (member.getProperty('fullname') or u'').strip()
        return safe_unicode(value or member.getId())

    @staticmethod
    @provider(IContextAwareDefaultFactory)
    def lastname(context):
        member = api.user.get_current()
        if member is None:
            return None
        value = (member.getProperty('fullname') or u'').strip()
        return safe_unicode(value.split(u' ', 1)[0] or member.getId())

    @staticmethod
    @provider(IContextAwareDefaultFactory)
    def fullname(context):
        member = api.user.get_current()
        if member is None:
            return None
        value = (member.getProperty('fullname') or u'').strip()
        return safe_unicode(value.split(u' ', 1)[-1] or member.getId())

    @staticmethod
    @provider(IContextAwareDefaultFactory)
    def email(context):
        member = api.user.get_current()
        if member is None:
            return None
        email = (member.getProperty('email') or u'').strip()
        return email or None
