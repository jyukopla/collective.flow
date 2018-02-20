# -*- coding: utf-8 -*-
from collective.flow.schema import load_schema
from collective.flow.testing import FLOW_INTEGRATION_TESTING

import unittest


class TestSupermodel(unittest.TestCase):

    layer = FLOW_INTEGRATION_TESTING

    def test_schema_loads(self):
        ob = self.layer['portal'].order
        load_schema(ob.schema, cache_key=ob.schema_digest)
