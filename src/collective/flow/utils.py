# -*- coding: utf-8 -*-
from hashlib import md5
from plone.memoize import ram
from plone.supermodel import loadString


# noinspection PyCallingNonCallable
@ram.cache(lambda m, xml: md5(xml).hexdigest())
def load_schema(xml):
    return loadString(xml).schema
