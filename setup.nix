{ pkgs ? import (fetchTarball {
    # branches nixos-20.03
    url = "https://github.com/NixOS/nixpkgs-channels/archive/99a3d7a86fce9e9c9f23b3e304d7d2b1270a12b8.tar.gz";
    sha256 = "0i40cl3n6600z2lkwrpiy28dcnv2r63fcgfswj91aaf1xfn2chql";
  }) {}
, plone ? "plone50"
, python ? "python27"
, pythonPackages ? builtins.getAttr (python + "Packages") pkgs
, requirements ?  ./. + "/requirements-${plone}-${python}.nix"
, image_app ? ""
, image_version ? ""
, image_revision ? ""
, image_hash ? ""
, image_build_ref_name ? ""
, image_url ? ""
, image_name ? null
, image_tag ? "latest"
}:

with builtins;
with pkgs;
with pkgs.lib;

let

  # Requirements for generating requirements.nix
  requirementsBuildInputs = [ cacert nix nix-prefetch-git
                              cyrus_sasl libffi libxml2 libxslt openldap ];
  buildoutPythonPackages = [ "cython" "pillow" "setuptools" ];

  # Load generated requirements
  requirementsFunc = import requirements {
    inherit pkgs;
    inherit (builtins) fetchurl;
    inherit (pkgs) fetchgit fetchhg;
  };

  # List package names in requirements
  requirementsNames = attrNames (requirementsFunc {} {});

  # Return base name from python drv name or name when not python drv
  pythonNameOrName = drv:
    if hasAttr "overridePythonAttrs" drv then drv.pname else drv.name;

  # Merge named input list from nixpkgs drv with input list from requirements drv
  mergedInputs = old: new: inputsName: self: super:
    (attrByPath [ inputsName ] [] new) ++ map
    (x: attrByPath [ (pythonNameOrName x) ] x self)
    (filter (x: !isNull x) (attrByPath [ inputsName ] [] old));

  # Merge package drv from nixpkgs drv with requirements drv
  mergedPackage = old: new: self: super:
    if isString new.src
       && !isNull (match ".*\.whl" new.src)  # do not merge build inputs for wheels
       && new.pname != "wheel"               # ...
    then new.overridePythonAttrs(old: rec {
      propagatedBuildInputs =
        mergedInputs old new "propagatedBuildInputs" self super;
    })
    else old.overridePythonAttrs(old: rec {
      inherit (new) pname version src;
      name = "${pname}-${version}";
      checkInputs =
        mergedInputs old new "checkInputs" self super;
      buildInputs =
        mergedInputs old new "buildInputs" self super;
      nativeBuildInputs =
        mergedInputs old new "nativeBuildInputs" self super;
      propagatedBuildInputs =
        mergedInputs old new "propagatedBuildInputs" self super;
      doCheck = false;
    });

  # Build python with manual aliases for naming differences between world and nix
  buildPython = (pythonPackages.python.override {
    packageOverrides = self: super:
      listToAttrs (map (name: {
        name = name; value = getAttr (getAttr name aliases) super;
      }) (filter (x: hasAttr (getAttr x aliases) super) (attrNames aliases)));
  });

  # Build target python with all generated & customized requirements
  targetPython = (buildPython.override {
    packageOverrides = self: super:
      # 1) Merge packages already in pythonPackages
      let super_ = (requirementsFunc self buildPython.pkgs);  # from requirements
          results = (listToAttrs (map (name: let new = getAttr name super_; in {
        inherit name;
        value = mergedPackage (getAttr name buildPython.pkgs) new self super_;
      })
      (filter (name: hasAttr "overridePythonAttrs"
                     (if (tryEval (attrByPath [ name ] {} buildPython.pkgs)).success
                      then (attrByPath [ name ] {} buildPython.pkgs) else {}))
       requirementsNames)))
      // # 2) with packages only in requirements or disabled in nixpkgs
      (listToAttrs (map (name: { inherit name; value = (getAttr name super_); })
      (filter (name: (! ((hasAttr name buildPython.pkgs) &&
                         (tryEval (getAttr name buildPython.pkgs)).success)))
       requirementsNames)));
      in # 3) finally, apply overrides (with aliased drvs mapped back)
      (let final = (super // (results //
        (listToAttrs (map (name: {
          name = getAttr name aliases; value = getAttr name results;
        }) (filter (x: hasAttr x results) (attrNames aliases))))
      )); in (final // (overrides self final)));
    self = buildPython;
  });

  # Alias packages with different names in requirements and in nixpkgs
  aliases = {
    "Pillow" = "pillow";
    "Pygments" = "pygments";
    "python-ldap" = "ldap";
  };

  # Final overrides to fix issues all the magic above cannot fix automatically
  overrides = self: super:

    # short circuit circulare dependency issues in Plone by ignoring dependencies
    super // (listToAttrs (map (name: {
      name = name;
      value = (getAttr name super).overridePythonAttrs(old: {
        buildInputs = old.buildInputs
          ++ optional (plone == "plone50") self."eggtestinfo";
        pipInstallFlags = [ "--no-dependencies" ];
        propagatedBuildInputs = [];
        doCheck = false;
      });
    }) (filter (name: (! hasAttr name buildPython.pkgs)) requirementsNames)))
    // {

      "eggtestinfo" = super.buildPythonPackage {
        name = "eggtestinfo-0.3";
        doCheck = false;
        src = fetchurl {
          url = "https://files.pythonhosted.org/packages/e0/8e/77c064957ea14137407e29abd812160eafc41b73a377c30d9e22d76f14fd/eggtestinfo-0.3.tar.gz";
          sha256 = "0s77knsv8aglns4s98ib5fvharljcsya5clf02ciqzy5s794jjsg";
        };
      };

      # fix issues where the shortcut above breaks build
      "Automat" = super."Automat".overridePythonAttrs(old: {});
      "SecretStorage" = super."SecretStorage".overridePythonAttrs(old: {});
      "Twisted" = super."Twisted".overridePythonAttrs(old: {});
      "docutils" = super."docutils".overridePythonAttrs(old: {});
      "keyring" = super."keyring".overridePythonAttrs(old: {});
      "readme-renderer" = super."readme-renderer".overridePythonAttrs(old: {});
      "twine" = super."twine".overridePythonAttrs(old: {});
      "nose-progressive" = if (plone != "plone50") then self."nose-progressive" else null;
      "funcsigs" = super."funcsigs".overridePythonAttrs(old: { doCheck = (plone != "plone50"); });
      "contextlib2" = super."contextlib2".overridePythonAttrs(old: { doCheck = (plone != "plone50"); });
      "robotframework-python3" = self."robotframework";

      # fix issues with overlapping paths
      "zope.testing" = super."zope.testing".overridePythonAttrs(old: {
        postInstall = optional (plone == "plone50") ''
          rm $out/bin/zope-testrunner
        '';
      });

      # fix issues with overlapping paths
      "createcoverage" = super."createcoverage".overridePythonAttrs(old: {
        postInstall = ''
          rm $out/bin/coverage
        '';
      });

      # let plone.app.robotframework override a script
      "Babel" = super."Babel".overridePythonAttrs(old: {
        patches = [];
        postInstall = ''
          rm $out/bin/pybabel
        '';
      });

      # let plone.app.robotframework override a script
      "robotframework" = super."robotframework".overridePythonAttrs(old: {
        postInstall = ''
          rm $out/bin/robot
        '';
      });

      # fix issue where nixpkgs drv is missing a dependency
      "sphinx" = super."sphinx".overridePythonAttrs(old: {
        propagatedBuildInputs = old.propagatedBuildInputs ++ [ self."packaging" ];
      });

    };

in rec {

  # shell with 'buildout' for resolving requirements.txt with buildout
  buildout = mkShell {
    buildInputs = requirementsBuildInputs ++ [
      (pythonPackages.python.withPackages(ps: with ps; [
        (zc_buildout_nix.overridePythonAttrs(old: { postInstall = ""; }))
      ] ++ map (name: getAttr name ps) buildoutPythonPackages))
    ];
  };

  # shell with 'pip2nix' for resolving requirements.txt into requirements.nix
  pip2nix = mkShell {
    buildInputs = requirementsBuildInputs ++ [
      (pythonPackages.python.withPackages(ps: with ps; [
        (zc_buildout_nix.overridePythonAttrs(old: { postInstall = ""; }))
        (getAttr
          ("python" + replaceStrings ["."] [""] pythonPackages.python.pythonVersion)
          ( import (fetchTarball {
              url = "https://github.com/datakurre/pip2nix/archive/7557e61808bfb5724ccae035d38d385a3c8d4dba.tar.gz";
              sha256 = "0rwxkbih5ml2mgz6lx23p3jgb6v0wvslyvscki1vv4hl3pd6jcld";
          } + "/release.nix") { inherit pkgs; }).pip2nix)
      ] ++ map (name: getAttr name ps) buildoutPythonPackages))
    ];
  };

  inherit buildPython targetPython toZConfig;

  # final env with packages in requirements.txt
  env = buildEnv {
    name = "plone-env";
    paths = [
      (targetPython.withPackages(ps: map (name: getAttr name ps) requirementsNames))
    ];
  };

  # final shell with packages in requirements.txt
  shell = mkShell {
    buildInputs = requirementsBuildInputs ++ [
      (targetPython.withPackages(ps: with ps; [
        (zc_buildout_nix.overridePythonAttrs(old: { postInstall = ""; }))
      ] ++ map (name: getAttr name ps)
        (filter (x: x != "zc.buildout") (buildoutPythonPackages ++ requirementsNames))))
      pkgs.firefox
      pkgs.geckodriver
    ];
  };
}
