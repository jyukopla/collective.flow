# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow import _
from collective.flow import behaviors
from collective.flow import browser
from collective.flow import buttons
from collective.flow import comments
from collective.flow import content
from collective.flow import defaults
from collective.flow import fields
from collective.flow import history
from collective.flow import schema
from collective.flow import transforms
from Products.CMFPlone.interfaces import INonInstallable
from venusianconfiguration import configure
from venusianconfiguration import has_package
from venusianconfiguration import i18n_domain
from venusianconfiguration import scan
from zope.interface import implementer

import plone.api as api
import plone.supermodel.exportimport


# We implement good enough write support for defaultFactory
plone.supermodel.exportimport.BaseHandler.filteredAttributes.pop(
    'defaultFactory',
    None,
)  # noqa
plone.supermodel.exportimport.ChoiceHandler.filteredAttributes.pop(
    'defaultFactory',
    None,
)  # noqa

i18n_domain('collective.flow')
configure.i18n.registerTranslations(directory='locales')

scan(behaviors)
scan(buttons)
scan(comments)
scan(content)
scan(defaults)
scan(fields)
scan(history)
scan(schema)
scan(transforms)

configure.include(package=browser, file='__init__.py')

if has_package('plone.restapi'):
    from collective.flow import restapi
    import plone.rest
    configure.include(package=plone.rest, file='meta.zcml')
    scan(restapi)


@configure.gs.registerProfile.post_handler(
    name=u'default',
    title=_(u'Forms, workflows and everything'),
    description=_(u'Activates collective.flow'),
    directory=u'profiles/default',
    provides=u'Products.GenericSetup.interfaces.EXTENSION',
)
def setup(context):
    # Creation of schema repository is disabled until there is a real use-case
    # and user interfaces for it:
    pass
    # portal = api.portal.get()
    # if 'schemata' in portal.objectIds():
    #     return
    # portal.portal_types.FlowSchemaRepository.global_allow = True
    # api.content.create(
    #     portal,
    #     'FlowSchemaRepository',
    #     'schemata',
    #     _(u'Flow schemata'),
    # )
    # portal.portal_types.FlowSchemaRepository.global_allow = False


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
@configure.gs.upgradeStep.handler(
    source='1008',
    destination='1009',
    sortkey='1008',
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
        try:
            assert aq_base(ob).submission_behaviors is not None
        except (AttributeError, AssertionError):
            ob.submission_behaviors = []
        try:
            assert aq_base(ob).submission_impersonation is not None
        except (AttributeError, AssertionError):
            ob.submission_impersonation = False


configure.gs.upgradeDepends(
    source='1004',
    destination='1005',
    sortkey='1004',
    title=u'Upgrade collective.flow from 1004 to 1005',
    description=u'Update resource bundles and content types',
    profile='collective.flow:default',
    import_steps='typeinfo plone.app.registry',
)

configure.gs.upgradeDepends(
    source='1005',
    destination='1006',
    sortkey='1005',
    title=u'Upgrade collective.flow from 1005 to 1006',
    description=u'Update workflow and viewlet order',
    profile='collective.flow:default',
    import_steps='repositorytool workflow viewlets',
)

configure.gs.upgradeDepends(
    source='1006',
    destination='1007',
    sortkey='1006',
    title=u'Upgrade collective.flow from 1006 to 1007',
    description=u'Update workflow and actions',
    profile='collective.flow:default',
    import_steps='typeinfo actions',
)

configure.gs.upgradeDepends(
    source='1007',
    destination='1008',
    sortkey='1007',
    title=u'Upgrade collective.flow from 1007 to 1008',
    description=u'Update workflow, viewlet order and typeinfo',
    profile='collective.flow:default',
    import_steps='typeinfo viewlets workflow',
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
