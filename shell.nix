{ plone ? "plone50"
, python ? "python27"
}:

(import ./setup.nix { inherit plone python; }).buildout
