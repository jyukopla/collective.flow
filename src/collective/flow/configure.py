# -*- coding: utf-8 -*-
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
    provides=u'Products.GenericSetup.interfaces.EXTENSION')
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
    source='1000', destination='1001', sortkey='1000',
    title=u'Upgrade collective.flow from 1000 to 1001',
    description=u'Update portal types',
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


@configure.utility.factory(
    name='collective.flow.HiddenProfiles')
@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        return [
            'collective.flow:uninstall',
        ]