# -*- coding: utf-8 -*-
from collective.flow.buttons import IBottomButtons
from collective.flow.buttons import ITopButtons
from collective.flow.interfaces import IFlowSubmission
from plone import api
from plone.app.layout.globals.interfaces import IViewView
from plone.app.layout.viewlets.interfaces import IAboveContentBody
from plone.app.layout.viewlets.interfaces import IAboveContentTitle
from plone.app.layout.viewlets.interfaces import IBelowContentBody
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


def get_default_metromap(wf):
    states = {}
    transitions = {}
    for state_id in wf.states:
        transition_ids = wf.states[state_id].transitions
        states[state_id] = {
            'state': state_id,
            'next_transition': list(transition_ids),
            'reopen_transition': [],
        }
        for transition_id in transition_ids:
            transitions.setdefault(transition_id, 0)
            transitions[transition_id] += 1

    for transition_id in wf.transitions:
        states[wf.transitions[transition_id].new_state_id
               ]['reopen_transition'].append(transition_id)

    metro = []
    stack = [states.pop(wf.initial_state)]
    while stack:
        state = stack.pop()
        state['reopen_transition'] = sorted(
            set(transitions).intersection(set(state['reopen_transition'])),
            key=lambda x: transitions[x],
        )[:1]
        for transition_id in state['reopen_transition']:
            transitions.pop(transition_id)
        state['next_transition'] = sorted(
            set(transitions).intersection(set(state['next_transition'])),
            key=lambda x: transitions[x],
        )[:1]
        for transition_id in state['next_transition']:
            transitions.pop(transition_id)
            if transition_id in wf.transitions:
                state_id = wf.transitions[transition_id].new_state_id
                if state_id in states:
                    stack.append(states.pop(state_id))
        metro.append(state)

    for state in metro:
        state['next_transition'] = ','.join(state['next_transition'])
        state['reopen_transition'] = ','.join(state['reopen_transition'])

    return metro


configure.browser.viewlet(
    name='collective.flow.submission.edit',
    for_=ITopButtons,
    view=IViewView,
    manager=IAboveContentBody,
    permission='cmf.ModifyPortalContent',
    template=os.path.join('viewlets_templates', 'submission_edit_viewlet.pt'),
)

configure.browser.viewlet(
    name='collective.flow.submission.edit',
    for_=IBottomButtons,
    view=IViewView,
    manager=IBelowContentBody,
    permission='cmf.ModifyPortalContent',
    template=os.path.join('viewlets_templates', 'submission_edit_viewlet.pt'),
)


@configure.browser.viewlet.class_(
    name='collective.flow.metromap.requester',
    for_=IFlowSubmission,
    view=IViewView,
    manager=IAboveContentTitle,
    permission='cmf.RequestReview',
    template=os.path.join('viewlets_templates', 'metromap_viewlet.pt'),
)
@configure.browser.viewlet.class_(
    name='collective.flow.metromap.reviewer',
    for_=IFlowSubmission,
    view=IViewView,
    manager=IAboveContentTitle,
    permission='cmf.ReviewPortalContent',
    template=os.path.join('viewlets_templates', 'metromap_viewlet.pt'),
)
@configure.browser.viewlet.class_(
    name='collective.flow.submission.actions',
    for_=ITopButtons,
    view=IViewView,
    manager=IAboveContentBody,
    permission='zope2.View',
    template=os.path.join(
        'viewlets_templates',
        'submission_actions_viewlet.pt',
    ),
)
@configure.browser.viewlet.class_(
    name='collective.flow.submission.actions',
    for_=IBottomButtons,
    view=IViewView,
    manager=IBelowContentBody,
    permission='zope2.View',
    template=os.path.join(
        'viewlets_templates',
        'submission_actions_viewlet.pt',
    ),
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
    def actions(self):
        tool = api.portal.get_tool('portal_workflow')

        # Get the default workflow id
        chain = tool.getChainFor(self.context)
        if not chain:
            return

        # Get currently available workflow actions (re-use from menu)
        actions = {}
        menu = getUtility(IBrowserMenu, name='plone_contentmenu_workflow')
        for action in menu.getMenuItems(self.context, self.request):
            item_id = action.get('extra', {}).get('id', u'') or u''
            action_id = re.sub('^workflow-transition-(.*)', '\\1', item_id)
            actions[action_id] = action

        for action in ['advanced', 'policy']:  # blacklisted menuitems
            if action in actions:
                del actions[action]

        return actions

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
        actions = self.actions()

        # Evaluate "ploneintranet"-style "happy path metro map" from wf
        metro_expression = wf.variables.get('metromap_transitions')
        try:
            metro = metro_expression.default_expr(getExprContext(self.context))
        except AttributeError:
            metro = get_default_metromap(wf)

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

            if status and state.id == status.get('review_state'):
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

        if len(self.steps) < 2:
            self.steps = []

    def render(self):
        return self.index()
