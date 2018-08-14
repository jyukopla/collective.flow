# -*- coding: utf-8 -*-
from collective.flow import _
from plone.app.contentmenu.interfaces import IContentMenuItem
from plone.app.contentmenu.menu import ActionsSubMenuItem
from plone.memoize.instance import memoize
from plone.protect.utils import addTokenToUrl
from venusianconfiguration import configure
from zope.browsermenu.interfaces import IBrowserMenu
from zope.browsermenu.interfaces import IBrowserSubMenuItem
from zope.browsermenu.menu import BrowserMenu
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface

import plone.api as api


class IFlowSubMenuItem(IBrowserSubMenuItem):
    """The menu item linking to the actions menu.
    """


class IFlowMenu(IBrowserMenu):
    """The actions menu.
    This gets its menu items from portal_actions.
    """


@configure.adapter.factory(
    for_=(Interface, Interface),
    provides=IContentMenuItem,
)
@implementer(IFlowSubMenuItem)
class FlowSubMenuItem(ActionsSubMenuItem):
    title = _(
        u'label_flow_menu',
        default=u'Flow',
    )
    description = _(
        u'title_flow_menu',
        default=u'Flow form management actions',
    )
    submenuId = 'plone_contentmenu_flow'
    order = 35
    extra = {
        'id': 'plone-contentmenu-flow',
        'li_class': 'plonetoolbar-content-action',
    }

    @memoize
    def available(self):
        actions_tool = api.portal.get_tool('portal_actions')
        actions = actions_tool.listActionInfos(
            object=self.context,
            categories=('object_flow', ),
            max=1,
        )
        return len(actions) > 0


@configure.browser.menu.class_(
    id=u'plone_contentmenu_flow',
    title=u'Flow form management actions',
)
@implementer(IFlowMenu)
class FlowMenu(BrowserMenu):
    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []

        context_state = getMultiAdapter((context, request),
                                        name='plone_context_state')
        context_state = getMultiAdapter(
            (context_state.canonical_object(), request),
            name='plone_context_state',
        )
        actions = context_state.actions('object_flow')
        if not actions:
            return results

        for action in actions:
            if not action['allowed']:
                continue
            aid = action['id']
            css_class = 'actionicon-object_flow-{0}'.format(aid)
            icon = action.get('icon', None)
            modal = action.get('modal', None)
            if modal:
                css_class += ' pat-plone-modal'

            results.append({
                'title': action['title'],
                'description': '',
                'action': addTokenToUrl(action['url'], request),
                'selected': False,
                'icon': icon,
                'extra': {
                    'id': 'plone-contentmenu-flow-' + aid,
                    'separator': None,
                    'class': css_class,
                    'modal': modal,
                },
                'submenu': None,
            })
        return results
