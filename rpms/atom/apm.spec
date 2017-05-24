# build Atom and Electron packages: https://github.com/tensor5/arch-atom
# RPM spec: http://pkgs.fedoraproject.org/cgit/rpms/?q=nodejs
# https://fedoraproject.org/wiki/Packaging:Node.js
%{?nodejs_find_provides_and_requires}
%global _cpln %(test $(rpm -E%?fedora) -gt 24 && echo "ln -s" || echo "cp -p")
%global debug_package %{nil}
%global _hardened_build 1
%global __provides_exclude_from %{nodejs_sitelib}/.*/node_modules
%global __requires_exclude_from %{nodejs_sitelib}/.*/node_modules
%global __requires_exclude (npm)

%global project apm
%global repo %{project}
%global node_ver v4

# commit
%global _commit cf5474e91f4b604c62665a207eade6dc9c27a8a6
%global _shortcommit %(c=%{_commit}; echo ${c:0:7})

Name:    nodejs-atom-package-manager
Version: 1.18.2
Release: 1.git%{_shortcommit}%{?dist}
Summary: Atom package manager

Group:   Applications/System
License: MIT
URL:     https://github.com/atom/apm/
Source0: %{url}/archive/%{_commit}/%{repo}-%{_shortcommit}.tar.gz
Source1: apm.js

Patch0:  use-system-npm.patch
Patch1:  use-local-node-devel.patch
Patch2:  no-scripts.patch
# GYP needs python2
Patch3:  python2.patch

BuildRequires: /usr/bin/npm, git
BuildRequires: nodejs-packaging
BuildRequires: libsecret-devel
BuildRequires: coffee-script
Requires: /usr/bin/npm, git, python2
# In fc25, the nodejs contains /bin/npm, and it do not depend node-gyp
Requires: node-gyp

%description
apm - Atom Package Manager
Discover and install Atom packages powered by https://atom.io

%prep
%setup -q -n %repo-%{_commit}
sed -i 's|<lib>|%{_lib}|' %{S:1} %{P:1}
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1

# Use custom launcher
rm bin/apm{,.cmd} bin/npm{,.cmd}
rm src/cli.coffee
install -m755 %{S:1} bin/apm

# Don't download binary Node
rm BUNDLED_NODE_VERSION script/*

%build
export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags}"

# Update node
%if 0%{?fedora} < 24 || 0%{?rhel}
git clone https://github.com/creationix/nvm.git .nvm
source .nvm/nvm.sh
nvm install %{node_ver}
nvm use %{node_ver}

# Install coffee-script
npm install coffee-script --loglevel info
Coffee="node_modules/.bin/coffee"
%endif

# Build apm
${Coffee:-coffee} -c --no-header -o lib src/*.coffee
npm install --loglevel info -g --prefix build/usr

# Copy system node binary
%{_cpln} "`which node`" build%{nodejs_sitelib}/atom-package-manager/bin

%install
cp -pr build/. %{buildroot}
rm -rf %{buildroot}%{nodejs_sitelib}/atom-package-manager/{node_modules,script,src}

pushd build%{nodejs_sitelib}/atom-package-manager
for ext in js json node gypi; do
    find node_modules -regextype posix-extended \
      -iname "*.${ext}" \
    ! -name '.*' \
    ! -name 'config.gypi' \
    ! -path '*deps' \
    ! -path '*test*' \
    ! -path '*obj.target*' \
    ! -path '*html*' \
    ! -path '*example*' \
    ! -path '*sample*' \
    ! -path '*benchmark*' \
    ! -regex '.*(oniguruma|git-utils|keytar)/node.*' \
      -exec install -Dm644 '{}' '%{buildroot}%{nodejs_sitelib}/atom-package-manager/{}' \;
done

# Remove some files
find %{buildroot} -regextype posix-extended -type f \
    -regex '.*js$' -exec sh -c "sed -i '/^#\!\/usr\/bin\/env/d' '{}'" \; -or \
    -regex '.*node' -exec strip '{}' \; -or \
    -name '.*' -exec rm -rf '{}' \; -or \
    -name '*.md' -delete -or \
    -name 'appveyor.yml' -delete

%files
%defattr(-,root,root,-)
%doc README.md
%license LICENSE.md
%{_bindir}/apm
%{nodejs_sitelib}/atom-package-manager/

%changelog
* Tue May 23 2017 mosquito <sensor.wen@gmail.com> - 1.18.2-1.gitcf5474e
- Release 1.18.2
* Fri Oct 21 2016 mosquito <sensor.wen@gmail.com> - 1.13.0-2.git33e67dd
- Fix coffee script error for fc23
* Fri Oct 21 2016 mosquito <sensor.wen@gmail.com> - 1.13.0-1.git33e67dd
- Release 1.13.0
* Fri Jun 17 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-6.git87b4bcb
- Fix launcher
* Fri May 27 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-5.git87b4bcb
- Use custom launcher. Thanks @tensor5
* Fri May 27 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-4.git87b4bcb
- Use environment variables to set electron version and resource path
- Use better patch (truncated-json-output.patch). Thanks @tensor5
- Refactor patch for using system Node.js
* Mon May 23 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-3.git87b4bcb
- Use node 4.x to build native modules
- Fix #106 by update node 4.x
  https://github.com/FZUG/repo/issues/106
* Wed May 18 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-2.git87b4bcb
- Fix #105 by rebuild apm
  https://github.com/FZUG/repo/issues/105
* Mon May  2 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-1.git87b4bcb
- Release 1.10.0
* Fri Apr 29 2016 mosquito <sensor.wen@gmail.com> - 1.9.3-2.git38ff5b5
- Fix arguments to path.join must be strings
* Fri Apr 29 2016 mosquito <sensor.wen@gmail.com> - 1.9.3-1.git38ff5b5
- Release 1.9.3
* Sun Apr 24 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-10.gitdef66c9
- Use npm path instead of package name
  https://github.com/FZUG/repo/issues/91
* Thu Apr 21 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-9.gitdef66c9
- Use local node devel files
* Sat Apr 16 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-8.gitdef66c9
- Fix system arch of dedupe for fc24+
* Sat Apr 16 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-7.gitdef66c9
- Fix fetch local packages failed for fc25
  https://github.com/FZUG/repo/issues/88
* Fri Apr 15 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-6.gitdef66c9
- Fix only be one child in node_modules
  https://github.com/FZUG/repo/issues/88
* Tue Apr 12 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-5.gitdef66c9
- Use system node for electron 0.37.5
- Link system node for fc24+
* Wed Apr  6 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-4.gitdef66c9
- Use node 4.x to build native modules for electron 0.37.4
* Tue Apr  5 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-3.gitdef66c9
- Add Req npm
- Use system npm
* Tue Apr  5 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-2.gitdef66c9
- Add Req node-gyp
* Wed Mar 30 2016 mosquito <sensor.wen@gmail.com> - 1.9.2-1.gitdef66c9
- Release 1.9.2
- Remove BReq node-gyp, Req libgnome-keyring
- Replace BReq git-core to git
* Tue Mar 29 2016 mosquito <sensor.wen@gmail.com> - 1.9.1-2.git24807ff
- Fixed fc24 running error: undefined symbol node_module_register
  https://github.com/atom/atom/issues/3385
- Copy system node binary
* Tue Mar 29 2016 mosquito <sensor.wen@gmail.com> - 1.9.1-1.git24807ff
- Release 1.9.1
* Mon Mar 21 2016 mosquito <sensor.wen@gmail.com> - 1.7.1-3.git955326e
- Fixed fc24 build error
- Rewrite install script
* Sat Mar 12 2016 mosquito <sensor.wen@gmail.com> - 1.7.1-2.git955326e
- Add requires python2, git-core, libgnome-keyring
* Sat Mar  5 2016 mosquito <sensor.wen@gmail.com> - 1.7.1-1.git955326e
- Release 1.7.1
* Sun Feb 14 2016 mosquito <sensor.wen@gmail.com> - 1.7.0-1.git829b81a
- Initial package
