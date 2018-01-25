# -*- coding: utf-8 -*-
from collective.flow.browser import folder
from collective.flow.browser import schema
from collective.flow.browser import submission
from venusianconfiguration import scan


scan(schema)
scan(folder)
scan(submission)
