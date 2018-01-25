collective.flow
==========================================

..  include:: _robot.rst

..  figure:: _screenshots/hello-plone.png
..  code:: robotframework

    Show Plone
        Go to  ${PLONE_URL}
        Capture and crop page screenshot
        ...  _screenshots/hello-plone.png
        ...  css=#content

..  toctree::

    example
