# -*- coding: utf-8 -*-
from collective.flow.browser import comments
from collective.flow.browser import folder
from collective.flow.browser import history
from collective.flow.browser import menu
from collective.flow.browser import schema
from collective.flow.browser import subfolder
from collective.flow.browser import submission
from collective.flow.browser import viewlets
from collective.flow.browser import widgets
from venusianconfiguration import configure
from venusianconfiguration import scan


# BBB: Plone < 5.1
try:
    # noinspection PyUnresolvedReferences
    from collective.flow.browser import submission_subform
    scan(submission_subform)
except ImportError:
    pass

scan(comments)
scan(folder)
scan(subfolder)
scan(schema)
scan(submission)
scan(widgets)
scan(viewlets)
scan(menu)
scan(history)

configure.plone.static(
    directory='static',
    type='plone',
    name='collective.flow',
)
