# -*- coding: utf-8 -*-
from plone.memoize import request
from plone.uuid.interfaces import IUUID
from Products.CMFEditions.interfaces.IArchivist import ArchivistError
from Products.Five import BrowserView
from venusianconfiguration import configure
from z3c.form.interfaces import IWidget

import logging
import os
import plone.api as api
import re


logger = logging.getLogger('collective.flow')


# noinspection PyUnusedLocal,PyShadowingNames
def cache_key(self, context, portal_repository, request=request):
    return 'collective.flow.history.' + IUUID(context)  # noqa: P001


# noinspection PyUnusedLocal,PyShadowingNames
@request.cache(cache_key)
def get_history(context, portal_repository, request=request):
    """Return renderable widgets for available version history of given
    context
    """
    metadata = portal_repository.getHistoryMetadata(context)

    if not metadata:
        return []

    # Iterate available history
    history = []
    for event in range(metadata.getLength(countPurged=False)):
        info = metadata.retrieve(event, countPurged=False)['vc_info']
        try:
            version = portal_repository.retrieve(
                context,
                int(info.version_id),
                countPurged=False,
            )
        except ArchivistError:
            continue
        # Lookup view for the version, expect it to be widgets view
        view = version.object.restrictedTraverse('@@view')
        view.update()
        widgets = dict(view.widgets)
        for group in getattr(view, 'groups', None) or []:
            widgets.update(group.widgets)
        history.append((version.object.modified(), widgets))
    return history


@configure.browser.page.class_(
    name=u'field-history',
    for_=IWidget,
    permission='zope2.View',
    template=os.path.join(
        os.path.dirname(__file__),
        'history_templates',
        'field_history_view.pt',
    ),
)
class FieldHistoryView(BrowserView):
    """Render available value history for a widget"""

    def __init__(self, widget, request):
        self.widget = widget
        self.field = widget.field
        self.form = widget.form
        self.name = self.field.__name__
        self._pr = api.portal.get_tool('portal_repository')
        super(FieldHistoryView, self).__init__(widget.context, request)

    def enabled(self):
        return self._pr.isVersionable(self.context)

    def history(self):
        seen = []
        result = []

        versions = get_history(self.context, self._pr, request=self.request)
        for version in versions:
            try:
                modified, widgets = version
                widget = widgets[self.field.__name__]
            except KeyError:
                continue
            if all([widget.value, widget.value != self.widget.value,
                    widget.value not in seen]):
                seen.append(widget.value)
                # Drop duplicate IDs
                widget.render = re.sub('\sid="[^"]+"', '', widget.render())
                result.append({
                    'modified': modified,
                    'widget': widget,
                })

        return result

    def __call__(self):
        if self.enabled():
            # noinspection PyBroadException
            try:
                return self.index()
            except Exception:
                logger.exception(u'Unexpected exception:')
                return u''
        else:
            return u''
