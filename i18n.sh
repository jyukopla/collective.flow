#!/nix/store/nkq0n2m4shlbdvdq0qijib5zyzgmn0vq-bash-4.4-p12/bin/bash
bin/i18ndude rebuild-pot --pot src/collective/flow/locales/collective.flow.pot --merge src/collective/flow/locales/manual.pot --create collective.flow src/collective/flow
bin/i18ndude sync --pot src/collective/flow/locales/collective.flow.pot src/collective/flow/locales/*/LC_MESSAGES/collective.flow.po
bin/pocompile src
