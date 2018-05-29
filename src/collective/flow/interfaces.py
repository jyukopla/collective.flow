# -*- coding: utf-8 -*-
from plone.app.z3cform.interfaces import IPloneFormLayer
from plone.autoform.directives import widget
from plone.namedfile.field import NamedBlobFile
from plone.namedfile.field import NamedBlobImage
from plone.schemaeditor.interfaces import ISchemaContext
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from plone.supermodel.directives import primary
from z3c.form.browser.textarea import TextAreaWidget
from zope import schema
from zope.i18nmessageid import MessageFactory
from zope.interface import Attribute
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


_ = MessageFactory('collective.flow')

DEFAULT_SCHEMA = u"""
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
  </schema>
</model>
"""


class ICollectiveFlowLayer(IDefaultBrowserLayer, IPloneFormLayer):
    """Marker interface that defines a browser layer."""


class IFlowSchemaDynamic(model.Schema):
    """Marker interface for dynamic flow schemas."""


class IAddFlowSchemaDynamic(IFlowSchemaDynamic):
    """Marker interface for dynamic flow schemas."""


class IFlowSchema(model.Schema):
    """Editable schema"""

    schema = Attribute(u'XML serialized flow schema')
    schema_digest = Attribute(u'MD5 hash of the current schema')

    # These should have been a protected attributes, but in the end that could
    # have caused more issues than it would have solved.


class IFlowSchemaForm(model.Schema):
    """Marker interface for flow schema aware forms"""


class IFlowSchemaRepository(model.Schema):
    """Container for editable schemas"""


class IFlowSchemaContext(ISchemaContext):

    object = Attribute(u'Object whose schema is being edited')


class IFlowFolder(IFlowSchema):
    """Container representing a form or workflow"""

    default_fieldset_label = schema.TextLine(
        title=_(u'Default fieldset label'),
        default=_(u'Form'),
    )

    submit_label = schema.TextLine(
        title=_(u'Submit button label'),
        default=_(u'Submit'),
    )

    #   fieldset(    klass = u'textarea-widget pat-foobar'
    #       'instructions',
    #       label=_(u'Instructions'),
    #       fields=[u'form_prologue',
    #               u'form_epilogue',
    #               u'form_thanks'],
    #   )

    #   form_prologue = RichText(
    #       title=_(u'Form prologue'),
    #       required=False,
    #   )

    #   form_epilogue = RichText(
    #       title=_(u'Form epilogue'),
    #       required=False,
    #   )

    #   form_thanks = RichText(
    #       title=_(u'Thank you message'),
    #       required=False,
    #   )

    fieldset(
        'workflow',
        label=_(u'Workflows'),
        fields=[
            u'submission_workflow',
            u'submission_transition',
            u'attachment_workflow',
            u'attachment_transition',
        ],
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

    widget('css', TextAreaWidget, klass='pat-style-editor')
    css = schema.Text(
        title=_(u'Custom CSS'),
        required=False,
    )

    fieldset(
        'css',
        label=_(u'Styles'),
        fields=[u'css'],
    )

    widget('javascript', TextAreaWidget, klass='pat-script-editor')
    javascript = schema.Text(
        title=_(u'Custom JavaScript'),
        required=False,
    )

    fieldset(
        'javascript',
        label=_(u'Scripts'),
        fields=[u'javascript'],
    )

    widget('validator', TextAreaWidget, klass='pat-python-editor')
    validator = schema.Text(
        title=_(u'Custom validator'),
        description=u"errors['fieldname'] = 'error' if not data['fieldname']",
        required=False,
    )

    fieldset(
        'validation',
        label=_(u'Validation'),
        fields=[u'validator'],
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
