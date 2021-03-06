%{?nodejs_find_provides_and_requires}
%global __provides_exclude_from %{_libdir}/%{name}/node_modules
%global __requires_exclude_from %{_libdir}/%{name}/node_modules
%global __requires_exclude (npm|libnode)

%global debug_package %{nil}
%global electron_ver  3.0.10

Name:    atom
Version: 1.33.1
Release: 1%{?dist}
Summary: A hack-able text editor for the 21st century
License: MIT
URL:     https://github.com/atom/atom
Source0: %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
Source1: symbols-view-use-system-ctags.patch
Source2: %{name}.js

Patch0:  fix-atom-sh.patch
Patch1:  fix-license-path.patch
Patch2:  fix-restart.patch
Patch3:  use-system-apm.patch
Patch4:  use-system-electron.patch
Patch5:  electron-3.patch

BuildRequires: git
BuildRequires: libtool
BuildRequires: /usr/bin/npm
BuildRequires: node-gyp
BuildRequires: nodejs-packaging
BuildRequires: npm(atom-package-manager)
BuildRequires: pkgconfig(xkbfile)
BuildRequires: pkgconfig(libsecret-1)
Requires:      desktop-file-utils
Requires:      electron >= %{electron_ver}
Requires:      npm(atom-package-manager)
Requires:      gvfs
Requires:      ctags

%description
Atom is a text editor that's modern, approachable, yet hack-able to the core
- a tool you can customize to do anything but also use productively without
ever touching a config file.

Visit https://atom.io to learn more.

%prep
%setup -q
sed -i 's|<lib>|%{_lib}|' %{P:0} %{P:2} %{P:4}
%patch0 -p1 -b .fix-atom-sh
%patch1 -p1 -b .fix-license-path
%patch2 -p1 -b .fix-restart
%patch3 -p1 -b .use-system-apm
%patch4 -p1 -b .use-system-electron
%patch5 -p1 -b .electron-3

# dugite use system git
sed -i '3aexport LOCAL_GIT_DIRECTORY=%{_prefix}' %{name}.sh

%build
node-gyp -v; node -v; npm -v; apm -v

# If unset, ~/.atom/.node-gyp/.atom/.npm is used
## https://github.com/atom/electron/blob/master/docs/tutorial/using-native-node-modules.md
npm_config_cache="${HOME}/.atom/.npm"
npm_config_disturl="https://atom.io/download/atom-shell"
npm_config_target="%{electron_ver}"
#npm_config_target_arch="x64|ia32"
npm_config_runtime="electron"

# The npm_config_target is no effect, set ATOM_NODE_VERSION
## https://github.com/atom/apm/blob/master/src/command.coffee
export ATOM_ELECTRON_VERSION="%{electron_ver}"
export ATOM_ELECTRON_URL="$npm_config_disturl"
export ATOM_RESOURCE_PATH="$PWD"
export ATOM_HOME="$npm_config_cache"

# Fix for Electron 3
npm install --package-lock-only @atom/nsfw@1.0.20 node-abi

# Installing atom dependencies
apm install --verbose

# Use system ctags for symbols-view
# https://github.com/FZUG/repo/issues/211
patch -p1 -i %{S:1}
rm -r node_modules/symbols-view/vendor

# Installing build tools
pushd script/
npm install --loglevel info
node build

%install
install -d %{buildroot}%{_libdir}
cp -r out/app %{buildroot}%{_libdir}/%{name}
install -m644 out/startup.js %{buildroot}%{_libdir}/%{name}/
install -m755 %{S:2} %{buildroot}%{_libdir}/%{name}/%{name}
rm -rf %{buildroot}%{_libdir}/%{name}/node_modules/

install -d %{buildroot}%{_datadir}/applications/
sed -e \
   's|<%= appName %>|Atom|
    s|<%= description %>|%{summary}|
    s|<%= installDir %>/bin/<%= appFileName %>/|%{name}|
    s|<%= iconPath %>|%{name}|' \
    resources/linux/atom.desktop.in > \
    %{buildroot}%{_datadir}/applications/%{name}.desktop

install -Dm0755 atom.sh %{buildroot}%{_bindir}/%{name}

# copy over icons in sizes that most desktop environments like
for i in 1024 512 256 128 64 48 32 24 16; do
    install -Dm0644 resources/app-icons/stable/png/${i}.png \
      %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/%{name}.png
done

# find all *.js files and generate node.file-list
pushd out/app/
for ext in js jsm json coffee css map node types less png svg aff dic; do
    find node_modules -regextype posix-extended \
      -iname \*.${ext} -print \
    ! -name '.*' \
    ! -path '*test*' \
    ! -path '*example*' \
    ! -path '*sample*' \
    ! -path '*benchmark*', \
      -regex '.*shortest_path.*' -print | \
      xargs -i -n1 install -Dm644 '{}' '%{buildroot}%{_libdir}/%{name}/{}' ||:
done
popd

find %{buildroot} -type f -regextype posix-extended \
    -regex '.*js$' -exec sh -c "sed -i '/^#\!\/usr\/bin\/env/d' '{}'" \; -or \
    -regex '.*node$' -type f -exec strip '{}' \; -or \
    -name '.*?' -print -or \
    -size 0 -print | xargs rm -rf

install -m644 out/app/node_modules/symbols-view/lib/ctags-config \
  %{buildroot}%{_libdir}/%{name}/node_modules/symbols-view/lib/

%files
%doc README.md CONTRIBUTING.md docs/
%license LICENSE.md
%{_bindir}/%{name}
%{_libdir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png

%changelog
* Thu Dec 20 2018 mosquito <sensor.wen@gmail.com> - 1.33.1-1
- Release 1.33.1

* Sun Dec  9 2018 mosquito <sensor.wen@gmail.com> - 1.33.0-2
- Fix broken Exec line in .desktop file (#335)

* Thu Dec  6 2018 mosquito <sensor.wen@gmail.com> - 1.33.0-1
- Release 1.33.0

* Sat Sep 23 2017 mosquito <sensor.wen@gmail.com> - 1.20.1-1.git966dfcc
- Release 1.20.1

* Tue May 23 2017 mosquito <sensor.wen@gmail.com> - 1.17.0-1.git2791572
- Release 1.17.0

* Sat Mar 11 2017 mosquito <sensor.wen@gmail.com> - 1.15.0-1.git3e457f3
- Release 1.15.0

* Sat Feb 11 2017 mosquito <sensor.wen@gmail.com> - 1.14.1-2.gita49cd59
- Fix restart
- Use system ctags for symbols-view

* Sat Feb 11 2017 mosquito <sensor.wen@gmail.com> - 1.14.1-1.gita49cd59
- Release 1.14.1
- Move script to script-old, https://github.com/atom/atom/commit/6856534

* Tue Jan 17 2017 mosquito <sensor.wen@gmail.com> - 1.13.0-1.gita357b4d
- Release 1.13.0

* Fri Jan 13 2017 mosquito <sensor.wen@gmail.com> - 1.12.7-3.git4573089
- Add ctags-config file for symbols-view

* Sun Jan  8 2017 mosquito <sensor.wen@gmail.com> - 1.12.7-2.git4573089
- Fix jump to method causes error

* Tue Jan  3 2017 mosquito <sensor.wen@gmail.com> - 1.12.7-1.git4573089
- Release 1.12.7

* Thu Dec  1 2016 mosquito <sensor.wen@gmail.com> - 1.12.6-1.git5a3d615
- Release 1.12.6

* Thu Oct 20 2016 mosquito <sensor.wen@gmail.com> - 1.11.2-1.git0ecc150
- Release 1.11.2

* Thu Oct 20 2016 mosquito <sensor.wen@gmail.com> - 1.11.1-2.git099ffef
- Fix cannot find shortest_path_tree module

* Sat Oct 15 2016 mosquito <sensor.wen@gmail.com> - 1.11.1-1.git099ffef
- Release 1.11.1
- Replace Grunt-based build system. See https://github.com/atom/atom/pull/12410

* Mon Sep 26 2016 mosquito <sensor.wen@gmail.com> - 1.10.2-1.git3ae8b29
- Release 1.10.2

* Fri Sep  2 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-1.git4f3b013
- Release 1.10.0

* Sun Aug  7 2016 mosquito <sensor.wen@gmail.com> - 1.9.6-1.gite0801e7
- Release 1.9.6

* Sat Aug  6 2016 mosquito <sensor.wen@gmail.com> - 1.9.5-1.git4c1a1e3
- Release 1.9.5

* Fri Aug  5 2016 mosquito <sensor.wen@gmail.com> - 1.9.4-1.gita222879
- Release 1.9.4

* Tue Aug  2 2016 mosquito <sensor.wen@gmail.com> - 1.9.0-1.git59b62a2
- Release 1.9.0

* Fri Jun 17 2016 mosquito <sensor.wen@gmail.com> - 1.8.0-2.gitf89b273
- Build for electron 0.37.8

* Thu Jun  9 2016 mosquito <sensor.wen@gmail.com> - 1.8.0-1.gitf89b273
- Release 1.8.0
- Build for electron 1.2.2
- Fix tree-view does not work
  https://github.com/FZUG/repo/issues/120

* Tue May 31 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-4.git6bed3e5
- Use node-gyp@3.0.3 for el7, system node-gyp doesn't support
  the if-else conditions syntax
  See https://github.com/JCMais/node-libcurl/issues/56

* Tue May 31 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-3.git6bed3e5
- Remove --build-dir option
- Update to settings-view@0.238.0
- Fix height error on install page
  https://github.com/FZUG/repo/issues/116

* Mon May 30 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-2.git6bed3e5
- Fix settings-view dont work
  https://github.com/FZUG/repo/issues/114

* Thu May 26 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-1.git6bed3e5
- Release 1.7.4
- Build for electron 1.2.0
- Build nodegit 0.12.2 from source code
- Add BReq libtool and git
- Update node 0.12 for fedora 23

* Thu May 26 2016 mosquito <sensor.wen@gmail.com> - 1.7.3-2.git1b3da6b
- Fix spell-check dont work
  https://github.com/FZUG/repo/issues/110

* Fri Apr 29 2016 mosquito <sensor.wen@gmail.com> - 1.7.3-1.git1b3da6b
- Release 1.7.3
- Build for electron 0.37.7
- Remove reduplicate CSP header

* Tue Apr 19 2016 mosquito <sensor.wen@gmail.com> - 1.7.2-1.git1969903
- Release 1.7.2

* Sat Apr 16 2016 mosquito <sensor.wen@gmail.com> - 1.7.1-1.git5dda304
- Release 1.7.1

* Wed Apr 13 2016 mosquito <sensor.wen@gmail.com> - 1.7.0-1.git1e7dc02
- Release 1.7.0
- Update nodegit 0.12.2 for electron 0.37.5
- Fix nodegit build error for node 0.10

* Tue Apr 12 2016 mosquito <sensor.wen@gmail.com> - 1.6.2-3.git42d7c40
- Rebuild for electron 0.37.5

* Wed Apr  6 2016 mosquito <sensor.wen@gmail.com> - 1.6.2-2.git42d7c40
- Rebuild for electron 0.37.4
- Set CSP header to allow load images
- Use ATOM_ELECTRON_URL instead of npm_config_disturl

* Sun Apr  3 2016 mosquito <sensor.wen@gmail.com> - 1.6.2-1.git42d7c40
- Release 1.6.2

* Wed Mar 30 2016 mosquito <sensor.wen@gmail.com> - 1.6.1-1.gitcd9b7d3
- Release 1.6.1
- Remove BReq nodejs, libgnome-keyring-devel, git-core
- Replace Req http-parser to desktop-file-utils

* Tue Mar 29 2016 mosquito <sensor.wen@gmail.com> - 1.6.0-3.git01c7777
- Fixes not found mime.types file

* Mon Mar 21 2016 mosquito <sensor.wen@gmail.com> - 1.6.0-2.git01c7777
- Fixes not found nodegit.node module
- Rewrite install script

* Mon Mar 21 2016 mosquito <sensor.wen@gmail.com> - 1.6.0-1.git01c7777
- Release 1.6.0

* Sun Mar 13 2016 mosquito <sensor.wen@gmail.com> - 1.5.4-3.gitb8cc0b4
- Fixes renderer path

* Sat Mar 12 2016 mosquito <sensor.wen@gmail.com> - 1.5.4-2.gitb8cc0b4
- rebuild for electron 0.36.11

* Sat Mar  5 2016 mosquito <sensor.wen@gmail.com> - 1.5.4-1.gitb8cc0b4
- Release 1.5.4

* Sun Feb 14 2016 mosquito <sensor.wen@gmail.com> - 1.5.3-2.git3e71894
- The package is split into atom, nodejs-atom-package-manager and electron
- Use system apm and electron
- Not generated asar file
- Remove exception-reporting and metrics dependencies from package.json
- Remove unnecessary files

* Sat Feb 13 2016 mosquito <sensor.wen@gmail.com> - 1.5.3-1.git3e71894
- Release 1.5.3

* Sat Feb 13 2016 mosquito <sensor.wen@gmail.com> - 1.5.2-1.git05731e3
- Release 1.5.2

* Fri Feb 12 2016 mosquito <sensor.wen@gmail.com> - 1.5.1-1.git88524b1
- Release 1.5.1

* Fri Feb  5 2016 mosquito <sensor.wen@gmail.com> - 1.4.3-1.git164201e
- Release 1.4.3

* Wed Jan 27 2016 mosquito <sensor.wen@gmail.com> - 1.4.1-2.git2cf2ccb
- Fix https://github.com/FZUG/repo/issues/64

* Tue Jan 26 2016 mosquito <sensor.wen@gmail.com> - 1.4.1-1.git2cf2ccb
- Release 1.4.1

* Sun Jan 17 2016 mosquito <sensor.wen@gmail.com> - 1.4.0-1.gite0dbf94
- Release 1.4.0

* Sun Dec 20 2015 mosquito <sensor.wen@gmail.com> - 1.3.2-1.git473e885
- Release 1.3.2

* Sat Dec 12 2015 mosquito <sensor.wen@gmail.com> - 1.3.1-1.git3937312
- Release 1.3.1

* Thu Nov 26 2015 mosquito <sensor.wen@gmail.com> - 1.2.4-1.git05ef4c0
- Release 1.2.4

* Sat Nov 21 2015 mosquito <sensor.wen@gmail.com> - 1.2.3-1.gitfb5b1ba
- Release 1.2.3

* Sat Nov 14 2015 mosquito <sensor.wen@gmail.com> - 1.2.1-1.git7e902bc
- Release 1.2.1

* Wed Nov 04 2015 mosquito <sensor.wen@gmail.com> - 1.1.0-1.git402f605
- Release 1.1.0

* Thu Sep 17 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.13-1
- Change lib to libnode

* Tue Sep 01 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.10-1
- Release 1.0.10

* Thu Aug 27 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.8-1
- Clean and test spec for epel, centos and fedora
- Release 1.0.8

* Tue Aug 11 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.6-1
- Release 1.0.6

* Thu Aug 06 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.5-1
- Release 1.0.5

* Wed Jul 08 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.1-1
- Release 1.0.1

* Thu Jun 25 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.0-1
- Release 1.0.0

* Wed Jun 10 2015 Helber Maciel Guerra <helbermg@gmail.com> - 0.208.0-1
- Fix atom.desktop

* Tue Jun 09 2015 Helber Maciel Guerra <helbermg@gmail.com> - 0.207.0-1
- Fix desktop icons and some rpmlint.

* Fri Oct 31 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.141.0-1
- release 0.141.0

* Thu Oct 23 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.139.0-1
- release 0.139.0

* Wed Oct 15 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.137.0-2
- release 0.137.0

* Tue Oct 07 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.136.0-1
- release 0.136.0

* Tue Sep 30 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.133.0-2
- Build OK

* Fri Aug 22 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.123.0-2
- Change package name to atom.

* Thu Aug 21 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.123.0-1
- RPM package is just working.

* Sat Jul 26 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.119.0-1
- Try without nodejs.

* Tue Jul 01 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.106.0-1
- Try new version

* Sun May 25 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.99.0
- Initial package
