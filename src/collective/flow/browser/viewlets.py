# -*- coding: utf-8 -*-
from collective.flow.interfaces import IFlowSubmission
from plone import api
from plone.app.layout.globals.interfaces import IViewView
from plone.app.layout.viewlets.interfaces import IBelowContentTitle
from plone.memoize import view
from Products.CMFCore.Expression import getExprContext
from Products.Five import BrowserView
from venusianconfiguration import configure
from zope.browsermenu.interfaces import IBrowserMenu
from zope.component import getUtility
from zope.interface import implementer
from zope.viewlet.interfaces import IViewlet

import os.path
import re


@configure.browser.viewlet.class_(
    name='jyu.ytolapp.metromap',
    for_=IFlowSubmission,
    view=IViewView,
    manager=IBelowContentTitle,
    permission='cmf.RequestReview',
    template=os.path.join('viewlets_templates', 'metromap_viewlet.pt'),
)
@implementer(IViewlet)
class MetroMapViewlet(BrowserView):
    def __init__(self, context, request, view, manager=None):
        super(MetroMapViewlet, self).__init__(context, request)
        self.__parent__ = view
        self.context = context
        self.request = request
        self.view = view
        self.manager = manager
        self.steps = []

    @view.memoize
    def update(self):
        tool = api.portal.get_tool('portal_workflow')

        # Get the default workflow id
        chain = tool.getChainFor(self.context)
        if not chain:
            return

        # Get the current workflow state and workflow definition
        status = tool.getStatusOf(chain[0], self.context)
        wf = tool.getWorkflowById(chain[0])

        # Get currently available workflow actions (re-use from menu)
        actions = {}
        menu = getUtility(IBrowserMenu, name='plone_contentmenu_workflow')
        for action in menu.getMenuItems(self.context, self.request):
            item_id = action.get('extra', {}).get('id', u'') or u''
            action_id = re.sub('^workflow-transition-(.*)', '\\1', item_id)
            actions[action_id] = action

        # Evaluate "ploneintranet"-style "happy path metro map" from wf
        metro_expression = wf.variables.get('metromap_transitions')
        try:
            metro = metro_expression.default_expr(getExprContext(self.context))
        except AttributeError:
            return

        # Build data for our metro map
        forward = None
        backward = None
        future = False
        for step in metro:
            state = wf.states[step.get('state', wf.initial_state)]

            # Define CSS class
            classes = []  # [u'state-{0:s}'.format(state.id)]

            if future:
                classes.append('in-future')

            if state.id == status.get('review_state'):
                classes.append('active')
                future = True

            for action_id in step.get('reopen_transition', '').split(','):
                backward = backward or actions.get(action_id)

            self.steps.append({
                'title': state.title,
                'className': ' '.join(classes),
                'forward': forward,
                'backward': backward,
            })

            forward = None
            backward = None

            for action_id in step.get('next_transition', '').split(','):
                forward = forward or actions.get(action_id)

    def render(self):
        return self.index()
