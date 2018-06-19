# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow import _
from collective.flow import browser
from collective.flow import content
from collective.flow import fields
from collective.flow import schema
from collective.flow import transforms
from plone import api
from Products.CMFPlone.interfaces import INonInstallable
from venusianconfiguration import configure
from venusianconfiguration import i18n_domain
from venusianconfiguration import scan
from zope.interface import implementer

import plone.supermodel.exportimport


# We implement good enough write support for defaultFactory
del plone.supermodel.exportimport.BaseHandler.filteredAttributes[
    'defaultFactory'
]  # noqa

i18n_domain('collective.flow')
configure.i18n.registerTranslations(directory='locales')

scan(content)
scan(schema)
scan(fields)
scan(transforms)

configure.include(package=browser, file='__init__.py')


@configure.gs.registerProfile.post_handler(
    name=u'default',
    title=_(u'Forms, workflows and everything'),
    description=_(u'Activates collective.flow'),
    directory=u'profiles/default',
    provides=u'Products.GenericSetup.interfaces.EXTENSION',
)
def setup(context):
    portal = api.portal.get()
    if 'schemata' in portal.objectIds():
        return
    portal.portal_types.FlowSchemaRepository.global_allow = True
    api.content.create(
        portal,
        'FlowSchemaRepository',
        'schemata',
        _(u'Flow schemata'),
    )
    portal.portal_types.FlowSchemaRepository.global_allow = False


configure.gs.upgradeDepends(
    source='1000',
    destination='1001',
    sortkey='1000',
    title=u'Upgrade collective.flow from 1000 to 1001',
    description=u'Update portal types',
    profile='collective.flow:default',
    import_steps='typeinfo plone.app.registry',
)

configure.gs.upgradeDepends(
    source='1001',
    destination='1002',
    sortkey='1001',
    title=u'Upgrade collective.flow from 1001 to 1002',
    description=u'Update resource bundles',
    profile='collective.flow:default',
    import_steps='typeinfo plone.app.registry',
)

configure.gs.upgradeDepends(
    source='1002',
    destination='1003',
    sortkey='1002',
    title=u'Upgrade collective.flow from 1002 to 1003',
    description=u'Update resource bundles and content types',
    profile='collective.flow:default',
    import_steps='typeinfo plone.app.registry',
)


@configure.gs.upgradeStep.handler(
    source='1003',
    destination='1004',
    sortkey='1003',
    title=u'Migrate FlowFolder content objects',
    description=u'',
    profile='collective.flow:default',
)
def addMissingAttributes(context):
    pc = api.portal.get_tool('portal_catalog')
    for brain in pc.unrestrictedSearchResults(portal_type='FlowFolder'):
        ob = brain._unrestrictedGetObject()
        try:
            assert aq_base(ob).submission_title_template is not None
        except (AttributeError, AssertionError):
            ob.submission_title_template = u'${parent_title} ${modified}'
        try:
            assert aq_base(ob).submission_path_template is not None
        except (AttributeError, AssertionError):
            ob.submission_path_template = ''


configure.gs.upgradeDepends(
    source='1004',
    destination='1005',
    sortkey='1004',
    title=u'Upgrade collective.flow from 1004 to 1005',
    description=u'Update resource bundles and content types',
    profile='collective.flow:default',
    import_steps='typeinfo plone.app.registry',
)

configure.gs.registerProfile(
    name=u'uninstall',
    title=_(u'Forms, workflows and everything'),
    description=_(u'Deactivates collective.flow'),
    directory=u'profiles/uninstall',
    provides=u'Products.GenericSetup.interfaces.EXTENSION',
)


@configure.utility.factory(name='collective.flow.HiddenProfiles')
@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        return [
            'collective.flow:uninstall',
        ]
