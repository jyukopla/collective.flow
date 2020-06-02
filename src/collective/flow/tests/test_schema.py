# -*- coding: utf-8 -*-
from collective.flow.schema import synchronized_schema
from collective.flow.testing import FLOW_INTEGRATION_TESTING
from lxml import etree

import unittest


def canonical_xml(xml):
    return etree.tostring(
        etree.fromstring(xml),
        pretty_print=True,
        xml_declaration=True,
        encoding='utf8',
    )


class TestSynchronizedSchema(unittest.TestCase):

    layer = FLOW_INTEGRATION_TESTING

    def test_no_effect(self):
        a = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
        <element>Minor</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
  </schema>
</model>
""",
        )
        b = synchronized_schema(a)
        self.assertEqual(a, b)

    def test_add_values(self):
        a = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
        <element>Minor</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
      </values>
    </field>
  </schema>
</model>
""",
        )
        b = synchronized_schema(a)
        c = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
        <element>Minor</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
        <element>Minor</element>
      </values>
    </field>
  </schema>
</model>
""",
        )
        self.assertEqual(b, c)

    def test_merge_values(self):
        a = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
        <element>Minor</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
      </values>
    </field>
  </schema>
</model>
""",
        )
        b = synchronized_schema(a)
        c = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
        <element>Minor</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element>Major</element>
        <element>Minor</element>
      </values>
    </field>
  </schema>
</model>
""",
        )
        self.assertEqual(b, c)

    def test_keep_localized_labels(self):
        a = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Major</element>
        <element key="minor">Minor</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Suuri</element>
      </values>
    </field>
  </schema>
</model>
""",
        )
        b = synchronized_schema(a)
        c = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Major</element>
        <element key="minor">Minor</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Suuri</element>
        <element key="minor">Minor</element>
      </values>
    </field>
  </schema>
</model>
""",
        )
        self.assertEqual(b, c)

    def test_copy_default(self):
        a = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Major</element>
        <element key="minor">Minor</element>
      </values>
      <default>minor</default>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Suuri</element>
      </values>
    </field>
  </schema>
</model>
""",
        )
        b = synchronized_schema(a)
        c = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Major</element>
        <element key="minor">Minor</element>
      </values>
      <default>minor</default>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Suuri</element>
        <element key="minor">Minor</element>
      </values>
      <default>minor</default>
    </field>
  </schema>
</model>
""",
        )
        self.assertEqual(b, c)

    def test_syncronize_to_master(self):
        a = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Major</element>
      </values>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Suuri</element>
        <element key="minor">Pieni</element>
      </values>
      <default>minor</default>
    </field>
  </schema>
</model>
""",
        )
        b = synchronized_schema(a, '/fi/')
        c = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
    </field>
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Major</element>
        <element key="minor">Pieni</element>
      </values>
      <default>minor</default>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="position" type="zope.schema.Choice">
      <values>
        <element key="major">Suuri</element>
        <element key="minor">Pieni</element>
      </values>
      <default>minor</default>
    </field>
  </schema>
</model>
""",
        )
        self.assertEqual(b, c)

    def test_skip_text_default(self):
        a = canonical_xml(
            """\
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="name" type="zope.schema.TextLine">
      <title>Full name</title>
      <default>Example</default>
    </field>
  </schema>
  <schema name="/fi/">
    <field name="name" type="zope.schema.TextLine">
      <title>Etunimi</title>
      <default>Esimerkki</default>
    </field>
  </schema>
</model>
""",
        )
        b = synchronized_schema(a)
        self.assertEqual(a, b)
