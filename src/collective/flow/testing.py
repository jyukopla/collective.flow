# -*- coding:utf-8 -*-
from Acquisition import aq_base
from collective.flow.schema import SCHEMA_MODULE
from plone import api
from plone.app.robotframework import AutoLogin
from plone.app.robotframework import I18N
from plone.app.robotframework import MockMailHost
from plone.app.robotframework import RemoteLibraryLayer
from plone.app.robotframework import Users
from plone.app.robotframework import Zope2ServerRemote
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import ploneSite
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.testing import z2
from Products.MailHost.interfaces import IMailHost
from zope.component import getSiteManager
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory

import collective.flow
import hashlib
import os
import pkg_resources
import venusianconfiguration


_ = MessageFactory('collective.flow')

try:
    HAVE_PLONE_5 = False
    if pkg_resources.get_distribution('Products.CMFPlone>=5.0'):
        HAVE_PLONE_5 = True
        import plone.app.contenttypes
except pkg_resources.VersionConflict:
    pass

venusianconfiguration.configure.includePluginsOverrides(
    package=u'plone', file='overrides.py'
)

ORDER_SCHEMA = """\
<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="order" type="zope.schema.List">
      <title>Order</title>
      <value_type type="zope.schema.Object">
        <schema>{0:s}.order</schema>
      </value_type>
    </field>
  </schema>
  <schema name="order">
    <field name="name" type="zope.schema.TextLine">
      <title>Name</title>
    </field>
    <field name="amount" type="zope.schema.Int">
      <title>Amount</title>
    </field>
  </schema>
</model>
""".format(SCHEMA_MODULE)


def populate(portal, target_language):
    setRoles(portal, TEST_USER_ID, ('Manager', ))
    login(portal, TEST_USER_NAME)
    ob = api.content.create(
        portal,
        'FlowFolder',
        'order',
        title=translate(_(u'Order'), target_language=target_language),
    )
    ob.schema = ORDER_SCHEMA
    ob.schema_digest = hashlib.md5(ORDER_SCHEMA).hexdigest()
    ob.submission_workflow = 'intranet_workflow'
    ob.attachment_workflow = 'intranet_workflow'
    logout()


class MockMailHostLayer(z2.Layer):
    defaultBases = (PLONE_FIXTURE, )

    def setUp(self):
        # zope.testing-set environment variable is in place.
        from Products.CMFPlone.tests import utils
        with ploneSite() as portal:
            portal.email_from_address = 'noreply@example.com'
            portal.email_from_name = 'Plone Site'
            portal._original_MailHost = portal.MailHost
            portal.MailHost = mailhost = utils.MockMailHost('MailHost')
            portal.MailHost.smtp_host = 'localhost'
            sm = getSiteManager(context=portal)
            sm.unregisterUtility(provided=IMailHost)
            sm.registerUtility(mailhost, provided=IMailHost)

    def tearDown(self):
        with ploneSite() as portal:
            mailhost = getattr(portal, '_original_MailHost', None)
            if mailhost:
                portal.MailHost = portal._original_MailHost
                sm = getSiteManager(context=portal)
                sm.unregisterUtility(provided=IMailHost)
                sm.registerUtility(
                    aq_base(portal._original_MailHost), provided=IMailHost
                )


MOCK_MAILHOST_FIXTURE = MockMailHostLayer()


class FlowLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        if HAVE_PLONE_5:
            self.loadZCML(package=plone.app.contenttypes)
        venusianconfiguration.enable()
        self.loadZCML(package=collective.flow, name='configure.py')
        self.loadZCML(package=collective.flow, name='testing.py')

    def setUpPloneSite(self, portal):
        if HAVE_PLONE_5:
            self.applyProfile(portal, 'plone.app.contenttypes:default')
        portal.portal_workflow.setDefaultChain('simple_publication_workflow')
        self.applyProfile(portal, 'collective.flow:default')

        language_tool = api.portal.get_tool('portal_languages')
        try:
            language_tool.settings.available_languages = [
                os.environ.get('LANGUAGE', 'en')
            ]
        except AttributeError:
            pass
        language_tool.setDefaultLanguage(os.environ.get('LANGUAGE', 'en'))
        populate(portal, language_tool.getDefaultLanguage())


FLOW_FIXTURE = FlowLayer()


class Flow(object):
    """Remote keyword library"""


FLOW_REMOTE_LIBRARY_BUNDLE_FIXTURE = RemoteLibraryLayer(
    bases=(PLONE_FIXTURE, ),
    libraries=(AutoLogin, Users, I18N, MockMailHost, Zope2ServerRemote, Flow),
    name='RemoteLibraryBundle:RobotRemote',
)

FLOW_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FLOW_FIXTURE, ),
    name='FlowLayer:IntegrationTesting',
)

FLOW_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FLOW_FIXTURE, ),
    name='FlowLayer:FunctionalTesting',
)

FLOW_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        FLOW_REMOTE_LIBRARY_BUNDLE_FIXTURE,
        FLOW_FIXTURE,
        MOCK_MAILHOST_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='FlowLayer:AcceptanceTesting',
)
