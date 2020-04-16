# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.behaviors import ICancelButton
from collective.flow.behaviors import ISaveAndActionButtons
from collective.flow.browser.folder import save_form
from collective.flow.browser.folder import validate
from collective.flow.browser.widgets import RichTextLabelWidget
from collective.flow.interfaces import DEFAULT_FIELDSET_LABEL_FIELD
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowFolder
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import load_schema
from collective.flow.utils import get_navigation_root_language
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.locking.interfaces import ILockable
from plone.z3cform.fieldsets.extensible import ExtensibleForm
from Products.CMFCore.interfaces import IActionWillBeInvokedEvent
from Products.Five import BrowserView
from venusianconfiguration import configure
from z3c.form import button
from zope.browsermenu.interfaces import IBrowserMenu
from zope.cachedescriptors.property import Lazy
from zope.component import getUtility
from zope.event import notify
from zope.i18n import negotiate
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import IObjectModifiedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import getSchemaValidationErrors
from zope.schema._bootstrapinterfaces import RequiredMissing

import functools
import plone.api as api
import re


_ = MessageFactory('collective.flow')


@configure.subscriber.handler(
    for_=(IFlowFolder, IObjectModifiedEvent),
)
def on_flow_change_update_behaviors(context, event):
    catalog = api.portal.get_tool('portal_catalog')
    try:
        submission_behaviors = aq_base(context).submission_behaviors or []
    except AttributeError:
        submission_behaviors = []
    submission_behaviors = sorted(submission_behaviors)
    for brain in catalog(object_provides=IFlowSubmission.__identifier__,
                         path='/'.join(context.getPhysicalPath())):
        ob = aq_base(brain.getObject())
        try:
            if (submission_behaviors != sorted(ob.submission_behaviors or [])):
                ob.submission_behaviors = submission_behaviors[:]
        except AttributeError:
            ob.submission_behaviors = submission_behaviors[:]


@configure.browser.page.class_(
    name='view',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template='submission_templates/view.pt',
)
@implementer(IFlowSchemaForm)
class SubmissionView(WidgetsView, ExtensibleForm):
    @property
    def default_fieldset_label(self):
        language = negotiate(context=self.request) or u''
        try:
            try:
                return self.context.aq_explicit.aq_acquire(
                    DEFAULT_FIELDSET_LABEL_FIELD + '_' + language,
                )
            except AttributeError:
                return self.context.aq_explicit.aq_acquire(
                    DEFAULT_FIELDSET_LABEL_FIELD,
                )
        except AttributeError:
            return _(u'Form')

    @Lazy
    def schema(self):
        language = negotiate(context=self.request) or u''
        return load_schema(
            aq_base(self.context).schema,
            language=language,
            cache_key=aq_base(self.context).schema_digest,
        )

    def updateFieldsFromSchemata(self):
        super(SubmissionView, self).updateFieldsFromSchemata()
        self.updateFields()

        # disable default values
        for group in ([self] + list(self.groups)):
            for name in group.fields:
                # noinspection PyPep8Naming
                group.fields[name].showDefault = False

    def update(self):
        super(SubmissionView, self).update()
        for group in ([self] + list(self.groups)):
            for widget in group.widgets.values():
                if isinstance(widget, RichTextLabelWidget):
                    widget.label = u''


@configure.browser.page.class_(
    name='metadata',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IFlowSchemaForm)
class SubmissionMetadataForm(DefaultEditForm):
    pass


@configure.browser.page.class_(
    name='edit',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IFlowSchemaForm)
class SubmissionEditForm(DefaultEditForm):
    enable_form_tabbing = False
    css_class = 'pat-folding-fieldsets'

    def __init__(self, context, request):
        super(SubmissionEditForm, self).__init__(context, request)
        language = negotiate(context=request) or u''
        context_language = get_navigation_root_language(self.context)
        if context_language.startswith(language or context_language):
            self._locale_postfix = ''
        else:
            self._locale_postfix = '_' + language
        self.buttons = button.Buttons()
        self.handlers = button.Handlers()

    def label(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                'title' + self._locale_postfix,
            )
        except AttributeError:
            return self.context.aq_explicit.aq_acquire('title')

    def description(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                'description' + self._locale_postfix,
            )
        except AttributeError:
            return self.context.aq_explicit.aq_acquire('description')

    def validator(self):
        return self.context.aq_explicit.aq_acquire('validator')

    @property
    def default_fieldset_label(self):
        try:
            try:
                return self.context.aq_explicit.aq_acquire(
                    DEFAULT_FIELDSET_LABEL_FIELD + self._locale_postfix,
                )
            except AttributeError:
                return self.context.aq_explicit.aq_acquire(
                    DEFAULT_FIELDSET_LABEL_FIELD,
                )
        except AttributeError:
            return _(u'Form')

    @Lazy
    def schema(self):
        language = negotiate(context=self.request) or u''
        return load_schema(
            aq_base(self.context).schema,
            language=language,
            cache_key=aq_base(self.context).schema_digest,
        )

    additionalSchemata = ()

    def updateActions(self):
        btn = button.Button(name='save', title=_(u'Save'))
        self.buttons += button.Buttons(btn)
        self.handlers.addHandler(btn, self.handleApply)

        if ISaveAndActionButtons.providedBy(self.context):
            append_action_buttons(self)

        if ICancelButton.providedBy(self.context):
            btn = button.Button(name='cancel', title=_(u'Cancel'))
            self.buttons += button.Buttons(btn)
            self.handlers.addHandler(btn, self.handleCancel)

        super(SubmissionEditForm, self).updateActions()

    def redirect(self, url, form, button_action):
        save = self.handlers.getHandler(self.buttons['save'])
        save(form, button_action)
        if not self.status:
            self.request.response.redirect(url)

    # noinspection PyPep8Naming
    def extractData(self, setErrors=True):
        data, errors = super(SubmissionEditForm,
                             self).extractData(setErrors=setErrors)
        if not errors:
            validator = self.validator()
            if validator:
                errors = validate(self, validator, data)
        return data, errors

    def applyChanges(self, data):
        changes = save_form(self, data, self.context)
        descriptions = []
        if changes:
            for interface, names in changes.items():
                descriptions.append(Attributes(interface, *names))
            notify(ObjectModifiedEvent(self.context, *descriptions))
        return changes


@configure.browser.page.class_(
    name='guard-no-required-missing',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='cmf.RequestReview',
)
@implementer(IFlowSchemaForm)
class SubmissionValidationGuard(BrowserView):
    def __call__(self):
        for name, value in getSchemaValidationErrors(
            self.schema,
            self.context,
        ):
            if isinstance(value, RequiredMissing):
                return False
        return True

    @Lazy
    def schema(self):
        language = negotiate(context=self.request) or u''
        return load_schema(
            aq_base(self.context).schema,
            language=language,
            cache_key=aq_base(self.context).schema_digest,
        )


def append_action_buttons(form):
    # Get currently available workflow actions (re-use from menu)
    actions = {}
    menu = getUtility(IBrowserMenu, name='plone_contentmenu_workflow')

    def lower_first(s):
        if s and isinstance(s, unicode) and len(s) > 1:
            return s[0].lower() + s[1:]
        elif s and isinstance(s, unicode):
            return s.lower()
        return s

    for action in menu.getMenuItems(form.context, form.request):
        item_id = action.get('extra', {}).get('id', u'') or u''
        action_id = re.sub('^workflow-transition-(.*)', '\\1', item_id)
        actions[action_id] = action

    for action in ['advanced', 'policy']:  # blacklisted menuitems
        if action in actions:
            del actions[action]

    form.buttons = form.buttons.copy()
    for action_id, action in actions.iteritems():
        new_button = button.Button(
            name=re.sub('^workflow-transition-(.*)', '\\1', action_id),
            title=u' '.join([
                translate(
                    _(u'Save and'),
                    context=form.request,
                ),
                lower_first(
                    translate(
                        action['title'],
                        domain='plone',
                        context=form.request,
                    ),
                ),
            ]),
        )
        form.buttons += button.Buttons(new_button)
        form.handlers.addHandler(
            new_button,
            button.Handler(
                new_button,
                functools.partial(form.redirect, action['action']),
            ),
        )


@configure.subscriber.handler(
    for_=(IFlowSubmission, IActionWillBeInvokedEvent),
)
def unlock_before_transition(ob, event):
    # Force unlock to always allow workflow transitions
    lockable = ILockable(ob, None)
    if lockable is not None:
        lockable.clear_locks()
