# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.browser.folder import save_form
from collective.flow.browser.folder import validate
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSchemaForm
from collective.flow.interfaces import IFlowSubmission
from collective.flow.schema import load_schema
from plone.autoform.view import WidgetsView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.z3cform.fieldsets.extensible import ExtensibleForm
from venusianconfiguration import configure
from zope.cachedescriptors.property import Lazy
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer


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
        return load_schema(aq_base(self.context).schema,
                           cache_key=aq_base(self.context).schema_digest)

    def updateFieldsFromSchemata(self):
        super(SubmissionView, self).updateFieldsFromSchemata()
        self.updateFields()

        # disable default values
        for group in ([self] + self.groups):
            for name in group.fields:
                # noinspection PyPep8Naming
                group.fields[name].showDefault = False


@configure.browser.page.class_(
    name='edit',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='cmf.ModifyPortalContent',
)
@implementer(IFlowSchemaForm)
class SubmissionEditForm(DefaultEditForm):

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
        return load_schema(aq_base(self.context).schema,
                           cache_key=aq_base(self.context).schema_digest)

    additionalSchemata = ()

    # noinspection PyPep8Naming
    def extractData(self, setErrors=True):
        data, errors = super(
            SubmissionEditForm, self).extractData(setErrors=setErrors)
        if not errors:
            validator = self.validator()
            if validator:
                errors = validate(self, validator, data)
        return data, errors

    def applyChanges(self, data):
        save_form(self, data, self.context)
