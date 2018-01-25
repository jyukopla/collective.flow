# -*- coding: utf-8 -*-
from plone.namedfile.field import NamedBlobFile
from plone.schemaeditor.interfaces import ISchemaContext
from plone.supermodel import model
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

    schema_xml = Attribute(u'The XML serialization of the schema')


class IFlowSchemaRepository(model.Schema):
    """Container for editable schemas"""


class IFlowSchemaContext(ISchemaContext):

    object = Attribute(u'Object whose schema is being edited')


class IFlowFolder(IFlowSchema):
    """Container representing a form or workflow"""

    css = schema.Text(
        title=_(u'Custom CSS'),
        required=False,
    )

    javascript = schema.Text(
        title=_(u'Custom JavaScript'),
        required=False,
    )

    submit_label = schema.TextLine(
        title=_(u'Submit button label'),
        default=_(u'Submit'),
    )

    workflow = schema.Choice(
        title=_(u'Submission workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
    )

    transition = schema.Choice(
        title=_(u'Submit transition'),
        vocabulary='plone.app.vocabularies.WorkflowTransitions',
    )


class IFlowSubFolder(model.Schema):
    """Flow folder"""


class IFlowSubmission(IFlowSchema):
    """Flow submission"""

    workflow = schema.Choice(
        title=_(u'Submission workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
    )


class IFlowAttachment(model.Schema):
    """Flow submission attachment"""

    file = NamedBlobFile(title=_(u'File'))
