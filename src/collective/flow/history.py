# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow import _
from collective.flow.interfaces import FLOW_NAMESPACE
from collective.flow.interfaces import FLOW_PREFIX
from plone.app.versioningbehavior.behaviors import IVersionable
from plone.app.versioningbehavior.behaviors import IVersioningSupport
from plone.app.versioningbehavior.behaviors import Versionable
from plone.supermodel.interfaces import IFieldMetadataHandler
from plone.supermodel.utils import ns
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.CMFEditions.interfaces.IArchivist import ArchivistError
from venusianconfiguration import configure
from zope.container.interfaces import IContainerModifiedEvent
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface


@configure.plone.behavior.provides(
    name=u'submission_versioning',
    title=_(u'Submission versioning'),
    description=_(
        u'Provides Form flow submission versioning support with CMFEditions',
    ),
    marker=IVersioningSupport,
    factory=Versionable,
)
class IVersionableSubmission(IVersionable):
    pass


class IVersionableField(Interface):
    """Marker interface for a field with changelog with versioning behavior"""


@configure.utility.factory(name='collective.flow.versioning')
@implementer(IFieldMetadataHandler)
class DiscussableFieldMetadataHandler(object):

    namespace = FLOW_NAMESPACE
    prefix = FLOW_PREFIX

    def read(self, node, schema, field):
        discussable = node.get(ns('changelog', self.namespace)) or ''
        if discussable.lower() in ('true', 'on', 'yes', 'y', '1'):
            alsoProvides(field, IVersionableField)

    def write(self, node, schema, field):
        if IVersionableField.providedBy(field):
            node.set(ns('changelog', self.namespace), 'true')


# noinspection PyPep8Naming
@configure.subscriber.handler(for_=(IVersioningSupport, IActionSucceededEvent))
def version(context, event):
    # only version the modified object, not its container on modification
    if IContainerModifiedEvent.providedBy(event):
        return

    # Hack for stagingbehavior, which triggers a event with a aq_based context
    # when deleting the working copy
    try:
        pr = context.portal_repository
    except AttributeError:
        return

    if not pr.isVersionable(context):
        return

    try:
        create_version = not pr.isUpToDate(
            context,
            aq_base(context).version_id,
        )
    except (AttributeError, ArchivistError):
        # The object is not actually registered, but a version is
        # set, perhaps it was imported, or versioning info was
        # inappropriately destroyed
        create_version = True

    # create new version if needed
    if create_version:
        pr.save(obj=context, comment=event.action)
