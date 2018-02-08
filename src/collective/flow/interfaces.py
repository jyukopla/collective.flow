# -*- coding: utf-8 -*-
from plone.app.textfield import RichText
from plone.namedfile.field import NamedBlobFile
from plone.namedfile.field import NamedBlobImage
from plone.schemaeditor.interfaces import ISchemaContext
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from plone.supermodel.directives import primary
from z3c.form.interfaces import IWidget
from zope import schema
from zope.i18nmessageid import MessageFactory
from zope.interface import Attribute
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema.interfaces import IField


_ = MessageFactory('collective.flow')

DEFAULT_SCHEMA = u"""
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
  </schema>
</model>
"""


class ICollectiveFlowLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IFlowSchema(model.Schema):
    """Editable schema"""

    schema = Attribute(u'XML serialized flow schema')
    schema_digest = Attribute(u'MD5 hash of the current schema')

    # These should have been a protected attribute, but in the end that could
    # have caused more issues than it would have solved.


class IFlowSchemaForm(model.Schema):
    """Marker interface for flow schema aware forms"""


class IFlowSchemaRepository(model.Schema):
    """Container for editable schemas"""


class IFlowSchemaContext(ISchemaContext):

    object = Attribute(u'Object whose schema is being edited')


class IFlowFolder(IFlowSchema):
    """Container representing a form or workflow"""

    submit_label = schema.TextLine(
        title=_(u'Submit button label'),
        default=_(u'Submit'),
    )

    form_prologue = RichText(
        title=_(u'Form prologue'),
        required=False,
    )

    form_epilogue = RichText(
        title=_(u'Form epilogue'),
        required=False,
    )

    form_thanks = RichText(
        title=_(u'Thank you message'),
        required=False,
    )

    fieldset(
        'workflow',
        label=_(u'Workflows'),
        fields=[u'submission_workflow',
                u'submission_transition',
                u'attachment_workflow',
                u'attachment_transition'],
    )

    submission_workflow = schema.Choice(
        title=_(u'Submission workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default='always_private_workflow',
    )

    submission_transition = schema.Choice(
        title=_(u'Submit transition'),
        vocabulary='plone.app.vocabularies.WorkflowTransitions',
        default=None,
        required=False,
    )

    attachment_workflow = schema.Choice(
        title=_(u'Attachment workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default='always_private_workflow',
    )

    attachment_transition = schema.Choice(
        title=_(u'Attachment transition'),
        vocabulary='plone.app.vocabularies.WorkflowTransitions',
        default=None,
        required=False,
    )

    css = schema.Text(
        title=_(u'Custom CSS'),
        required=False,
    )

    fieldset(
        'css',
        label=_(u'Styles'),
        fields=[u'css'],
    )

    javascript = schema.Text(
        title=_(u'Custom JavaScript'),
        required=False,
    )

    fieldset(
        'javascript',
        label=_(u'Scripts'),
        fields=[u'javascript'],
    )


class IFlowSubFolder(model.Schema):
    """Flow folder"""


class IFlowSubmission(IFlowSchema):
    """Flow submission"""

    submission_workflow = schema.Choice(
        title=_(u'Submission workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default='always_private_workflow',
    )

    attachment_workflow = schema.Choice(
        title=_(u'Attachment workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default='always_private_workflow',
    )


class IFlowAttachment(model.Schema):
    """Flow submission attachment"""

    primary('file')
    file = NamedBlobFile(
        title=_(u'File'),
        required=False,
    )

    primary('image')
    image = NamedBlobImage(
        title=_(u'Image'),
        required=False,
    )


class IRichTextLabel(model.Schema, IField):
    """Rich text label field"""
    text = RichText(
        title=_(u'Text'),
        default=u'',
        missing_value=u'',
    )
    description = Attribute(u'Labels don\'t need to be described.')
    required = Attribute(u'Labels don\'t require any input value.')


class IRichTextLabelWidget(IWidget):
    """Rich text label widget"""
