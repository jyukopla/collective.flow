# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.flow import _
from collective.flow.comments import IComments
from collective.flow.comments import IDiscussableField
from collective.flow.interfaces import ICollectiveFlowLayer
from collective.flow.interfaces import IFlowSubmission
from collective.flow.interfaces import IFlowSubmissionComment
from plone.app.discussion.browser.comments import CommentForm
from plone.app.discussion.browser.conversation import ConversationView
from plone.app.discussion.interfaces import IConversation
from plone.app.layout.globals.interfaces import IViewView
from plone.app.layout.viewlets.interfaces import IBelowContent
from plone.schemaeditor.interfaces import IFieldEditorExtender
from plone.schemaeditor.interfaces import ISchemaContext
from plone.z3cform.interfaces import IWrappedForm
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


try:
    from plone.tiles import Tile
except ImportError:
    Tile = BrowserView

logger = logging.getLogger('collective.flow')


class IFieldCommentsForm(Interface):
    comments = schema.Bool(
        title=_(u'Enable comments'),
        required=False,
    )


@configure.adapter.factory(provides=IFieldCommentsForm)
@implementer(IFieldCommentsForm)
@adapter(IField)
class FieldCommentsAdapter(object):
    def __init__(self, field):
        self.field = field

    def _read_comments(self):
        return IDiscussableField.providedBy(self.field)

    def _write_comments(self, value):
        if value:
            alsoProvides(self.field, IDiscussableField)
        else:
            noLongerProvides(self.field, IDiscussableField)

    comments = property(_read_comments, _write_comments)


# The adapter could be registered directly as a named adapter providing
# IFieldEditorExtender for ISchemaContext and IField. But we can also register
# a separate callable which returns the schema only if extra conditions pass:
@configure.adapter.factory(
    provides=IFieldEditorExtender,
    name='collective.flow.comments',
)
@adapter(ISchemaContext, IField)
def get_comments_schema(schema_context, field):
    try:
        if IComments.providedBy(schema_context.content):
            return IFieldCommentsForm
        elif (u'submission_comments' in (aq_base(
                schema_context.content).submission_behaviors or [])):
            return IFieldCommentsForm
    except AttributeError:
        pass


class FieldCommentForm(CommentForm):
    prefix = 'form'
    action = ''
    enable_unload_protection = False

    def __init__(self, context, request, comment_title=None):
        super(FieldCommentForm, self).__init__(context, request)
        self.comment_title = comment_title
        self.action = self.request.getURL().rstrip('@@edit')

    def create_comment(self, data):
        comment = super(FieldCommentForm, self).create_comment(data)
        comment.title = self.comment_title
        alsoProvides(comment, IFlowSubmissionComment)
        return comment

    def render(self):
        # Optimize adding new comments and replying to comments when posting
        # with ajax_load=1:
        # - when calling the view directly, don't redirect and render twice
        # - when calling the dicussion tile, pass ajax_load=1 for redirect
        # TODO: Optimize more with views and forms that allow rendering
        #       of comments without evaluation main views or flow schemata
        output = super(FieldCommentForm, self).render()
        if ('@@plone.app.standardtiles' in self.request.getURL() and
                'location' in self.request.response.headers):
            if self.request.get('ajax_load'):
                params = '?ajax_load=1'
            else:
                params = ''
            location = self.request.response.getHeader('location')
            self.request.response.redirect(
                ''.join([
                    self.context.absolute_url(),
                    params,
                    '#',
                    location.split('#')[-1],
                ]),
            )
        elif self.request.get('ajax_load'):
            self.request.response.headers.pop('location', None)
            self.request.response.status = 200
        return output


@configure.browser.viewlet.class_(
    name=u'plone.comments',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    manager=IBelowContent,
    view=IViewView,
    permission='zope2.View',
    template=os.path.join(
        os.path.dirname(__file__),
        'comments_templates',
        'reply_form_viewlet.pt',
    ),
)
@configure.browser.viewlet.class_(
    name=u'plone.comments',
    for_=IComments,
    layer=ICollectiveFlowLayer,
    manager=IBelowContent,
    view=IViewView,
    permission='zope2.View',
    template=os.path.join(
        os.path.dirname(__file__),
        'comments_templates',
        'reply_form_viewlet.pt',
    ),
)
class EmptyDiscussionViewlet(BrowserView):
    form = None

    def __init__(self, context, request, view=None, manager=None):
        super(EmptyDiscussionViewlet, self).__init__(context, request)
        self.__parent__ = view
        self.context = context
        self.request = request
        self.view = view
        self.manager = manager

    def update(self):
        self.form = FieldCommentForm(self.context, self.request)
        self.form.enable_unload_protection = False
        alsoProvides(self.form, IWrappedForm)
        self.form.update()

    def __call__(self):
        if not IComments.providedBy(self.context):
            return u''
        elif self.form is None:
            self.update()
        return self.index()


@configure.browser.page.class_(
    name=u'plone.app.standardtiles.discussion',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template=os.path.join(
        os.path.dirname(__file__),
        'comments_templates',
        'reply_form_viewlet.pt',
    ),
)
@configure.browser.page.class_(
    name=u'plone.app.standardtiles.discussion',
    for_=IComments,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
    template=os.path.join(
        os.path.dirname(__file__),
        'comments_templates',
        'reply_form_viewlet.pt',
    ),
)
class ReplyFormTile(Tile):
    """This tile replaces discussion tile with only re-usable reply form"""

    form = None

    def __call__(self):
        if not IComments.providedBy(self.context):
            return u''
        # Call form
        self.form = FieldCommentForm(self.context, self.request)
        alsoProvides(self.form, IWrappedForm)
        self.form.update()
        # Fix form action to target tile
        self.form.action = self.url
        # Fix submit redirect from tile to context
        return u'<html><body>{0:s}</body></html>'.format(self.index())


@configure.browser.page.class_(
    name=u'conversation_view',
    for_=IFlowSubmission,
    layer=ICollectiveFlowLayer,
    permission='zope2.View',
)
class FlowSubmissionConversationView(ConversationView):
    def enabled(self):
        return (
            IComments.providedBy(self.context) or
            super(FlowSubmissionConversationView, self).enabled()
        )


@configure.browser.page.class_(
    name=u'field-comments',
    for_=IWidget,
    permission='zope2.View',
    template=os.path.join(
        os.path.dirname(__file__),
        'comments_templates',
        'field_comments_form.pt',
    ),
)
@configure.browser.page.class_(
    name=u'field-comments-readonly',
    for_=IWidget,
    permission='zope2.View',
    template=os.path.join(
        os.path.dirname(__file__),
        'comments_templates',
        'field_comments_view.pt',
    ),
)
class FieldCommentsView(BrowserView):
    """Render available value history for a widget"""

    form_klass = FieldCommentForm
    form_instance = None

    def __init__(self, widget, request):
        self.widget = widget
        self.field = widget.field
        self.form = widget.form
        self.name = self.field.__name__
        super(FieldCommentsView, self).__init__(widget.context, request)

    def enabled(self):
        return all([
            IComments.providedBy(self.context),
            IDiscussableField.providedBy(self.field),
            self.widget.value in [[], None],
        ])

    def update(self):
        self.form_instance = self.form_klass(
            aq_inner(self.context),
            self.request,
            self.name,
        )
        self.form_instance.prefix = self.widget.name
        alsoProvides(self.form_instance, IWrappedForm)
        self.form_instance.update()

    def __call__(self):
        if IAnnotations(self.request).get('collective.promises'):
            # skip rendering when unsolved promises exist
            return u''

        if self.enabled():
            try:
                self.update()
                return self.index()
            except Exception:
                logger.exception('Unexpected exception:')
                raise
        else:
            return u''

    def has_replies(self):
        """Returns true if there are replies.
        """
        if self.get_replies() is not None:
            try:
                self.get_replies().next()
                return True
            except StopIteration:
                pass
        return False

    def get_replies(self):
        """Returns all replies to a content object.
        """
        context = aq_inner(self.context)
        conversation = IConversation(context, None)
        wf = api.portal.get_tool('portal_workflow')
        if len(conversation.objectIds()):
            replies = False
            for r in conversation.getThreads():
                r = r.copy()
                # Yield comments for the field
                if any([
                        r['comment'].title == self.name,
                        replies and r['comment'].in_reply_to,
                ]):
                    # List all possible workflow actions
                    r['actions'] = [
                        a for a in wf.listActionInfos(object=r['comment'])
                        if a['category'] == 'workflow' and a['allowed']
                    ]
                    r['review_state'] = wf.getInfoFor(  # noqa: P001
                        r['comment'],
                        'review_state',
                        'acknowledged',
                    )
                    # Yield
                    yield r
                    replies = True
                else:
                    replies = False
