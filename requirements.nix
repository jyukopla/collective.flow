# Generated by pip2nix 0.8.0.dev1
# See https://github.com/johbo/pip2nix

{ pkgs, fetchurl, fetchgit, fetchhg }:

self: super: {
  "dataflake.fakeldap" = super.buildPythonPackage {
    name = "dataflake.fakeldap-1.0";
    doCheck = false;
    propagatedBuildInputs = [
      self."python-ldap"
      self."setuptools"
    ];
    src = fetchurl {
      url = "https://files.pythonhosted.org/packages/20/f4/adb8dcb2646fc559c6a78bdd01dd5f7809efee2695871d3c78168f8c328d/dataflake.fakeldap-1.0.tar.gz";
      sha256 = "1ll53h4hdnvac2az0vyh483c8333r6g44sz077ddisrc5wq1y7jj";
    };
  };
  "pyasn1" = super.buildPythonPackage {
    name = "pyasn1-0.4.4";
    doCheck = false;
    src = fetchurl {
      url = "https://files.pythonhosted.org/packages/10/46/059775dc8e50f722d205452bced4b3cc965d27e8c3389156acd3b1123ae3/pyasn1-0.4.4.tar.gz";
      sha256 = "0drilmx5j25aplfr5wrml0030cs5fgxp9yp94fhllxgx28yjm3zm";
    };
  };
  "pyasn1-modules" = super.buildPythonPackage {
    name = "pyasn1-modules-0.2.2";
    doCheck = false;
    propagatedBuildInputs = [
      self."pyasn1"
    ];
    src = fetchurl {
      url = "https://files.pythonhosted.org/packages/37/33/74ebdc52be534e683dc91faf263931bc00ae05c6073909fde53999088541/pyasn1-modules-0.2.2.tar.gz";
      sha256 = "0ivm850yi7ajjbi8j115qpsj95bgxdsx48nbjzg0zip788c3xkx0";
    };
  };
  "python-ldap" = super.buildPythonPackage {
    name = "python-ldap-3.1.0";
    doCheck = false;
    propagatedBuildInputs = [
      self."pyasn1"
      self."pyasn1-modules"
    ];
    src = fetchurl {
      url = "https://files.pythonhosted.org/packages/7f/1c/28d721dff2fcd2fef9d55b40df63a00be26ec8a11e8c6fc612ae642f9cfd/python-ldap-3.1.0.tar.gz";
      sha256 = "1i97nwfnraylyn0myxlf3vciicrf5h6fymrcff9c00k581wmx5s1";
    };
  };
  "setuptools" = super.buildPythonPackage {
    name = "setuptools-40.5.0";
    doCheck = false;
    src = fetchurl {
      url = "https://files.pythonhosted.org/packages/26/e5/9897eee1100b166a61f91b68528cb692e8887300d9cbdaa1a349f6304b79/setuptools-40.5.0.zip";
      sha256 = "1aqykblgfxd21q9ccrgdxwl4xjifpq01l29ssbgdn2kn987j0aia";
    };
  };
  "zc.buildout" = super.buildPythonPackage {
    name = "zc.buildout-2.12.2";
    doCheck = false;
    propagatedBuildInputs = [
      self."setuptools"
    ];
    src = fetchurl {
      url = "https://files.pythonhosted.org/packages/d7/02/ad9b098ba8f77715ca2beb66fda9c1b674c8bcbc26e94b56ba392349fe69/zc.buildout-2.12.2.tar.gz";
      sha256 = "0hx0a24r8b6gl48silhqhpfjksamrvv5xlr523z8vnk12f57wpgz";
    };
  };
}
