#!/usr/bin/env bash
bin/i18ndude rebuild-pot --pot src/collective/flow/locales/collective.flow.pot --merge src/collective/flow/locales/manual.pot --create collective.flow src/collective/flow
bin/i18ndude sync --pot src/collective/flow/locales/collective.flow.pot src/collective/flow/locales/*/LC_MESSAGES/collective.flow.po
bin/i18ndude sync --pot src/collective/flow/locales/plone.pot src/collective/flow/locales/*/LC_MESSAGES/plone.po
bin/pocompile src
