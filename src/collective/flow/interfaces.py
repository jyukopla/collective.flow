# -*- coding: utf-8 -*-
from plone.namedfile.field import NamedBlobFile
from plone.namedfile.field import NamedBlobImage
from plone.schemaeditor.interfaces import ISchemaContext
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from plone.supermodel.directives import primary
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

    submission_workflow = schema.Choice(
        title=_(u'Submission workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default='intranet_workflow',
    )

    submission_transition = schema.Choice(
        title=_(u'Submit transition'),
        vocabulary='plone.app.vocabularies.WorkflowTransitions',
        required=False,
    )

    attachment_workflow = schema.Choice(
        title=_(u'Attachment workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default='intranet_workflow',
    )

    attachment_transition = schema.Choice(
        title=_(u'Attachment transition'),
        vocabulary='plone.app.vocabularies.WorkflowTransitions',
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
        default='intranet_workflow',
    )

    attachment_workflow = schema.Choice(
        title=_(u'Attachment workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default='intranet_workflow',
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
