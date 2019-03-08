# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.interfaces import DEFAULT_FIELDSET_LABEL_FIELD
from collective.flow.interfaces import SUBMISSION_TITLE_TEMPLATE_FIELD
from collective.flow.interfaces import SUBMIT_LABEL_FIELD
from zope.proxy import ProxyBase


class LanguageFieldsProxy(ProxyBase):
    __slots__ = ['_context', '_language']

    def __init__(self, context):
        super(LanguageFieldsProxy, self).__init__(context)
        self._context = context
        self._language = None

    def get_title(self):
        try:
            return getattr(
                aq_base(self._context),
                'title' + '_' + self._language,
            )
        except AttributeError:
            return self._context.title

    def set_title(self, value):
        setattr(self._context, 'title' + '_' + self._language, value)

    title = property(get_title, set_title)

    def get_description(self):
        try:
            return getattr(
                aq_base(self._context),
                'description' + '_' + self._language,
            )
        except AttributeError:
            return self._context.description

    def set_description(self, value):
        setattr(self._context, 'description' + '_' + self._language, value)

    description = property(get_description, set_description)

    def get_default_fieldset_label(self):
        try:
            return getattr(
                self._context,
                DEFAULT_FIELDSET_LABEL_FIELD + '_' + self._language,
            )
        except AttributeError:
            return self._context.default_fieldset_label

    def set_default_fieldset_label(self, value):
        setattr(
            self._context,
            DEFAULT_FIELDSET_LABEL_FIELD + '_' + self._language,
            value,
        )

    default_fieldset_label = property(
        get_default_fieldset_label,
        set_default_fieldset_label,
    )

    def get_submit_label(self):
        try:
            return getattr(
                self._context,
                SUBMIT_LABEL_FIELD + '_' + self._language,
            )
        except AttributeError:
            return self._context.submit_label

    def set_submit_label(self, value):
        setattr(
            self._context,
            SUBMIT_LABEL_FIELD + '_' + self._language,
            value,
        )

    submit_label = property(
        get_submit_label,
        set_submit_label,
    )

    def get_submission_title_template(self):
        try:
            return getattr(
                self._context,
                SUBMISSION_TITLE_TEMPLATE_FIELD + '_' + self._language,
            )
        except AttributeError:
            return self._context.submission_title_template

    def set_submission_title_template(self, value):
        setattr(
            self._context,
            SUBMISSION_TITLE_TEMPLATE_FIELD + '_' + self._language,
            value,
        )

    submission_title_template = property(
        get_submission_title_template,
        set_submission_title_template,
    )
