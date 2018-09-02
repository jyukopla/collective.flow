# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow import _
from collective.flow.history import IVersionableField
from collective.flow.history import IVersionableSubmission
from plone.app.versioningbehavior.behaviors import IVersioningSupport
from plone.memoize import request
from plone.schemaeditor.interfaces import IFieldEditorExtender
from plone.schemaeditor.interfaces import ISchemaContext
from plone.uuid.interfaces import IUUID
from Products.Five import BrowserView
from venusianconfiguration import configure
from z3c.form.interfaces import IWidget
from zope import schema
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import noLongerProvides
from zope.schema.interfaces import IField

import logging
import os
import plone.api as api
import re


logger = logging.getLogger('collective.flow')


class IFieldChangelogForm(Interface):
    changelog = schema.Bool(
        title=_(u'Enable changelog'),
        required=False,
    )


@configure.adapter.factory(provides=IFieldChangelogForm)
@implementer(IFieldChangelogForm)
@adapter(IField)
class FieldCommentsAdapter(object):
    def __init__(self, field):
        self.field = field

    def _read_changelog(self):
        return IVersionableField.providedBy(self.field)

    def _write_changelog(self, value):
        if value:
            alsoProvides(self.field, IVersionableField)
        else:
            noLongerProvides(self.field, IVersionableField)

    changelog = property(_read_changelog, _write_changelog)


# The adapter could be registered directly as a named adapter providing
# IFieldEditorExtender for ISchemaContext and IField. But we can also register
# a separate callable which returns the schema only if extra conditions pass:
@configure.adapter.factory(
    provides=IFieldEditorExtender,
    name='collective.flow.changelog',
)
@adapter(ISchemaContext, IField)
def get_changelog_schema(schema_context, field):
    try:
        if IVersionableSubmission.providedBy(schema_context.content):
            return IFieldChangelogForm
        elif (u'submission_versioning' in (aq_base(
                schema_context.content).submission_behaviors or [])):
            return IFieldChangelogForm
    except AttributeError:
        pass


# noinspection PyUnusedLocal,PyShadowingNames
def cache_key(self, context, portal_repository, request=request):
    return 'collective.flow.history.' + IUUID(context)  # noqa: P001


# noinspection PyUnusedLocal,PyShadowingNames
@request.cache(cache_key)
def get_history(context, portal_repository, request=request):
    """Return renderable widgets for available version history of given
    context
    """
    history = []
    for version in portal_repository.getHistory(
            context,
            oldestFirst=True,
            countPurged=False,
    ):
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
        return IVersioningSupport.providedBy(
            self.context,
        ) and self._pr.isVersionable(
            self.context,
        ) and IVersionableField.providedBy(self.field)

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
        if IAnnotations(self.request).get('collective.promises'):
            # skip rendering when unsolved promises exist
            return u''

        # Only render when enabled; Also, assume not required or ajax loads
        if self.enabled() and 'ajax_load' not in self.request.form:
            # noinspection PyBroadException
            try:
                return self.index()
            except Exception:
                logger.exception(u'Unexpected exception:')
                return u''
        else:
            return u''
