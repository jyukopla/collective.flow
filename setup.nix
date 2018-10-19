{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/81f5c2698a87c65b4970c69d472960c574ea0db4.tar.gz";
    sha256 = "0p4x9532d3qlbykyyq8zk62k8py9mxd1s7zgbv54zmv597rs5y35";
  }) {}
, setup ? import (fetchTarball {
    url = "https://github.com/datakurre/setup.nix/archive/d3025ac35cc348d7bb233ee171629630bb4d6864.tar.gz";
    sha256 = "09czivsv81y1qydl7jnqa634bili8z9zvzsj0h3snbr8pk5dzwkj";
 })
, pythonPackages ? pkgs.python2Packages
}:

let overrides = self: super:  {

  "eggtestinfo" = super.buildPythonPackage {
    name = "eggtestinfo-0.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e0/8e/77c064957ea14137407e29abd812160eafc41b73a377c30d9e22d76f14fd/eggtestinfo-0.3.tar.gz";
      sha256 = "0s77knsv8aglns4s98ib5fvharljcsya5clf02ciqzy5s794jjsg";
    };
    doCheck = false;
  };

  "plonecli" = super."plonecli".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."pytestrunner" ];
    propagatedBuildInputs = old.propagatedBuildInputs ++ [
      self.tkinter
    ];
    src = pkgs.fetchFromGitHub {
      owner = "plone";
      repo = "plonecli";
      rev = "2070a22cb01c411fcff4e1354ccfc5bb68b4ef89";
      sha256 = "10izl11cz70lnn6ycq8rv32gqkgfnp5yvs300rgql5dlg3pz58w0";
    };
  });

  "z3c.autoinclude" = super."z3c.autoinclude".overridePythonAttrs (old: {
    src = pkgs.fetchFromGitHub {
      owner = "zopefoundation";
      repo = "z3c.autoinclude";
      rev = "8f8c603024979a44b95a3fd104fff02cdb208da1";
      sha256 = "1mf11ivnyjdfmc2vdd01akqwqiss0q8ax624glxrzk8qx46spqqi";
    };
    installFlags = [ "--no-deps" ];
    propagatedBuildInputs = [];
  });

  "flake8-print" = super."flake8-print".overridePythonAttrs (old: {
    propagatedBuildInputs = old.propagatedBuildInputs ++ [
      self."enum34"
      self."mccabe"
      self."configparser"
    ];
    installFlags = [ "--no-deps" ];
  });

  "BTrees" = super."BTrees".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."persistent" self."zope.interface" ];
    propagatedBuildInputs = [];
  });

  "Products.Archetypes" = super."Products.Archetypes".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."eggtestinfo" ];
    propagatedBuildInputs = [];
  });

  "Products.CMFCore" = super."Products.CMFCore".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."eggtestinfo" ];
    propagatedBuildInputs = [];
  });

  "Products.CMFUid" = super."Products.CMFUid".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."eggtestinfo" ];
    propagatedBuildInputs = [];
  });

  "Products.DCWorkflow" = super."Products.DCWorkflow".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."eggtestinfo" ];
    propagatedBuildInputs = [];
  });

  "Products.GenericSetup" = super."Products.GenericSetup".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."eggtestinfo" ];
    propagatedBuildInputs = [];
  });

  "zope.security" = super."zope.security".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    buildInputs = [ self."zope.interface" self."zope.proxy" ];
    propagatedBuildInputs = [];
  });

  "sauna.reload" = super."sauna.reload".overridePythonAttrs (old: {
    installFlags = [ "--no-deps" ];
    src = fetchTarball {
      url = "https://github.com/collective/sauna.reload/archive/e12a0a9e01204de324ab934aec5754773ac30bd6.tar.gz";
      sha256 = "1hshs9b4693hwlm2n0jx6miq6q18wc7qq2a5l7nqmxxgs21x9a3c";
    };
  });
};

in

setup {
  inherit pkgs pythonPackages overrides;
  src = ./.;
  buildInputs = with pkgs; [
    geckodriver
  ];
  force = true;
  ignoreCollisions = true;
}
