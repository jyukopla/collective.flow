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
  "dataflake.fakeldap" = super."dataflake.fakeldap".overridePythonAttrs(old: {
    buildInputs = [ self."setuptools-git" ];
  });
  "zc.buildout" = pythonPackages."zc_buildout_nix".overridePythonAttrs(old:
    with super."zc.buildout"; {
      inherit name src;
      postInstall = ''
        sed -i "s|import sys|import sys\nimport os\nsys.executable = os.path.join(sys.prefix, 'bin', os.path.basename(sys.executable))|" $out/bin/buildout
        cat $out/bin/buildout
      '';
      propagatedBuildInputs = with self; [
        cryptography
        self."dataflake.fakeldap"
        ipdb
        kerberos
        lxml
        pillow
        pycrypto
        pycryptodome
        pyscss
        python-ldap
        python_magic
      ];
    }
  );
}; in

setup {
  inherit pkgs pythonPackages overrides;
  src = ./requirements.nix;
  buildInputs = with pkgs; [
    geckodriver
    firefox
  ];
}
