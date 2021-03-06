# -*- coding: utf-8 -*-
from plone.app.discussion.interfaces import IDiscussionLayer
from plone.app.z3cform.interfaces import IPloneFormLayer
from plone.app.z3cform.widget import AjaxSelectFieldWidget
from plone.app.z3cform.widget import SelectFieldWidget
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
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


_ = MessageFactory('collective.flow')

FLOW_NAMESPACE = 'http://namespaces.plone.org/supermodel/flow'
FLOW_PREFIX = 'flow'

COMMENTS_KEY = u'collective.flow.comments'
CHANGELOG_KEY = u'collective.flow.changelog'

DEFAULT_SCHEMA = u"""
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
  </schema>
</model>
"""

DEFAULT_SUBMISSION_WORKFLOW = 'always_private_workflow'
DEFAULT_ATTACHMENT_WORKFLOW = 'always_private_workflow'

DEFAULT_FIELDSET_LABEL_FIELD = u'default_fieldset_label'
SUBMISSION_BEHAVIORS_FIELD = u'submission_behaviors'
SUBMISSION_IMPERSONATION_FIELD = u'submission_impersonation'
SUBMISSION_PATH_TEMPLATE_FIELD = u'submission_path_template'
SUBMISSION_TITLE_TEMPLATE_FIELD = u'submission_title_template'
SUBMIT_LABEL_FIELD = u'submit_label'
SUBMISSION_WORKFLOW_FIELD = u'submission_workflow'
SUBMISSION_TRANSITION_FIELD = u'submission_transition'
ATTACHMENT_WORKFLOW_FIELD = u'attachment_workflow'
ATTACHMENT_TRANSITION_FIELD = u'attachment_transition'


class ICollectiveFlowLayer(
        IDefaultBrowserLayer,
        IPloneFormLayer,
        IDiscussionLayer,
):
    """Marker interface that defines a browser layer."""


class IFlowSchemaDynamic(model.Schema):
    """Marker interface for dynamic flow schemas."""


class IAddFlowSchemaDynamic(IFlowSchemaDynamic):
    """Marker interface for dynamic flow schemas."""


class IImpersonateFlowSchemaDynamic(IFlowSchemaDynamic):
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
        'advanced',
        label=_(u'Advanced'),
        fields=[
            SUBMISSION_TITLE_TEMPLATE_FIELD,
            SUBMISSION_PATH_TEMPLATE_FIELD,
            SUBMISSION_BEHAVIORS_FIELD,
            SUBMISSION_IMPERSONATION_FIELD,
            SUBMISSION_WORKFLOW_FIELD,
            SUBMISSION_TRANSITION_FIELD,
            ATTACHMENT_WORKFLOW_FIELD,
            ATTACHMENT_TRANSITION_FIELD,
        ],
    )

    submission_title_template = schema.TextLine(
        title=_(u'Submission title template'),
        description=_(
            u'submission_title_help',
            default=u''
            u'Customize submission titles to enhance their '
            u'discoverability in listings.',
        ),
        default=u'${parent_title} ${created}',
    )

    submission_path_template = schema.BytesLine(
        title=_(u'Submission filing template'),
        description=_(
            u'submission_path_help',
            default=u''
            u'Customize submission filing sub-paths to '
            u'allow delegation submission reviewer roles.',
        ),
        required=False,
    )

    widget(SUBMISSION_BEHAVIORS_FIELD, SelectFieldWidget)
    submission_behaviors = schema.List(
        title=_(u'Submission behaviors'),
        value_type=schema.Choice(
            vocabulary='collective.flow.submission.behaviors',
        ),
        required=False,
    )

    submission_impersonation = schema.Bool(
        title=_(u'Impersonated submissions'),
        description=_(
            u'Allow editors to submit forms impersonating '
            u'as someone else',
        ),
    )

    submission_workflow = schema.Choice(
        title=_(u'Submission workflow'),
        vocabulary='plone.app.vocabularies.Workflows',
        default=DEFAULT_SUBMISSION_WORKFLOW,
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
        default=DEFAULT_ATTACHMENT_WORKFLOW,
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


class IFlowSubFolder(IFlowSchema):
    """Flow folder"""


class IFlowSubmission(IFlowSchema):
    """Flow submission"""


class IFlowSubmissionComment(Interface):
    """Flow submission comment marker interface"""


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


class IFlowImpersonation(model.Schema):
    """Default flow impersonation schema"""

    widget('username', AjaxSelectFieldWidget)
    username = schema.Choice(
        title=_(u'Select user to impersonate'),
        vocabulary='plone.app.vocabularies.Users',
    )
