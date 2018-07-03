# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.browser.folder import save_form
from collective.flow.browser.folder import validate
from collective.flow.browser.widgets import RichTextLabelWidget
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import load_schema
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.z3cform.fieldsets.extensible import ExtensibleForm
from venusianconfiguration import configure
from z3c.form import button
from zope.browsermenu.interfaces import IBrowserMenu
from zope.cachedescriptors.property import Lazy
from zope.component import getUtility
from zope.event import notify
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import ObjectModifiedEvent

import functools
import re


_ = MessageFactory('collective.flow')


@configure.browser.page.class_(
    name='view',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template='submission_templates/view.pt',
)
@implementer(IFlowSchemaForm)
class SubmissionView(WidgetsView, ExtensibleForm):
    @Lazy
    def schema(self):
        return load_schema(
            aq_base(self.context).schema,
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

    def label(self):
        return self.context.aq_explicit.aq_acquire('title')

    def description(self):
        return self.context.aq_explicit.aq_acquire('description')

    def validator(self):
        return self.context.aq_explicit.aq_acquire('validator')

    @property
    def default_fieldset_label(self):
        try:
            return self.context.aq_explicit.aq_acquire(
                'default_fieldset_label',
            )
        except AttributeError:
            return _(u'Form')

    @Lazy
    def schema(self):
        return load_schema(
            aq_base(self.context).schema,
            cache_key=aq_base(self.context).schema_digest,
        )

    additionalSchemata = ()

    def updateActions(self):
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

        for action_id, action in actions.iteritems():
            new_button = button.Button(
                name=re.sub('^workflow-transition-(.*)', '\\1', action_id),
                title=u' '.join([
                    translate(
                        _(u'Save and'),
                        context=self.request,
                    ),
                    translate(
                        action['title'],
                        domain='plone',
                        context=self.request,
                    ).lower(),
                ]),
            )
            self.buttons += button.Buttons(new_button)
            self.handlers.addHandler(
                new_button,
                button.Handler(
                    new_button,
                    functools.partial(self.redirect, action['action']),
                ),
            )
        super(SubmissionEditForm, self).updateActions()

    def redirect(self, url, form, button_action):
        save = self.handlers.getHandler(self.buttons['save'])
        save(form, button_action)
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
