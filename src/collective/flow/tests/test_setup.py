# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.flow.testing import FLOW_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.flow is properly installed."""

    layer = FLOW_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.flow is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'collective.flow'))

    def test_browserlayer(self):
        """Test that IFLOWLayer is registered."""
        from collective.flow.interfaces import (
            ICollectiveFlowLayer)
        from plone.browserlayer import utils
        self.assertIn(ICollectiveFlowLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = FLOW_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

        # Uninstall as Manager
        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        login(self.portal, TEST_USER_NAME)
        self.installer.uninstallProducts(['collective.flow'])

    def test_product_uninstalled(self):
        """Test if collective.flow is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'collective.flow'))
