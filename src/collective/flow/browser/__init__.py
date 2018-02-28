# -*- coding: utf-8 -*-
from collective.flow.browser import folder
from collective.flow.browser import schema
from collective.flow.browser import subfolder
from collective.flow.browser import submission
from collective.flow.browser import widgets
from venusianconfiguration import configure
from venusianconfiguration import scan


scan(folder)
scan(subfolder)
scan(schema)
scan(submission)
scan(widgets)

configure.plone.static(
    directory='static',
    type='plone',
    name='collective.flow',
)
