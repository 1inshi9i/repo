%global arch %(test $(rpm -E%?_arch) = x86_64 && echo "x64" || echo "ia32")
%global debug_package %{nil}
%global _hardened_build 1
%global __provides_exclude (npm)
%global __requires_exclude (npm|0.12|nodejs.abi)

%global project vscode
%global repo %{project}
%global electron_ver 1.3.13
%global node_ver 6

# commit
%global _commit ee428b0eead68bf0fb99ab5fdc4439be227b6281
%global _shortcommit %(c=%{_commit}; echo ${c:0:7})

# compute checksum for file
# https://github.com/Microsoft/vscode/blob/master/build/gulpfile.vscode.js#L165
%global hash MD5() { openssl md5 -binary $1 |openssl base64 |cut -d= -f1; }
%global line_num LN() { wc -l $1 |cut -d" " -f1; }
%global _files files=(\
  "vs/workbench/workbench.main.js"\
  "vs/workbench/workbench.main.css"\
  "vs/workbench/electron-browser/bootstrap/index.html"\
  "vs/workbench/electron-browser/bootstrap/index.js"\
)
%{nil}

Name:    vscode
Version: 1.8.1
Release: 1%{?dist}
Summary: Visual Studio Code - An open source code editor

Group:   Development/Tools
License: MIT
URL:     https://github.com/Microsoft/vscode
Source0: %{url}/archive/%{_commit}/%{repo}-%{_shortcommit}.tar.gz
# https://github.com/Microsoft/vscode/blob/master/src/vs/workbench/electron-main/env.ts
Source1: about.json
Patch0:  improve-i18n.patch

BuildRequires: openssl
BuildRequires: /usr/bin/npm
BuildRequires: node-gyp, git
BuildRequires: python, libX11-devel
BuildRequires: desktop-file-utils
Requires: electron = %{electron_ver}

%description
 VS Code is a new type of tool that combines the simplicity of a code editor
 with what developers need for their core edit-build-debug cycle. Code provides
 comprehensive editing and debugging support, an extensibility model, and
 lightweight integration with existing tools.

%prep
%setup -q -n %{repo}-%{_commit}
%patch0 -p1

git clone https://github.com/creationix/nvm.git .nvm
source .nvm/nvm.sh
nvm install %{node_ver}
npm config set python=`which python2`

# https://github.com/Microsoft/vscode/pull/2559
sed -i '/electronVer/s|:.*,$|: "%{electron_ver}",|' package.json

# Do not download electron
sed -i '/pipe.electron/s|^|//|' build/gulpfile.vscode.js

%build
export CFLAGS="%{optflags} -fPIC -pie"
export CXXFLAGS="%{optflags} -fPIC -pie"
source .nvm/nvm.sh
nvm use %{node_ver}
scripts/npm.sh install --loglevel info
node_modules/.bin/gulp vscode-linux-%{arch}
npm dedupe

%install
# Data files
mkdir --parents %{buildroot}%{_libdir}/%{name}
cp -a ../VSCode-linux-*/. %{buildroot}%{_libdir}/%{name}
rm -rf %{buildroot}%{_libdir}/%{name}/{node_modules,bin}

# Bin file
mkdir --parents %{buildroot}%{_bindir}
cat <<EOT >> %{buildroot}%{_bindir}/%{name}
#!/usr/bin/env bash
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root
# for license information.

NAME="%{name}"
VSCODE_PATH="%{_libdir}/\$NAME"
ELECTRON="%{_bindir}/electron-%{electron_ver}"
CLI="\$VSCODE_PATH/out/cli.js"
ELECTRON_RUN_AS_NODE=1 "\$ELECTRON" "\$CLI" --app="\$VSCODE_PATH" "\$@"
exit \$?
EOT

# Icon files
install -Dm 0644 resources/linux/code.png \
    %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/%{name}.png

# Desktop file
mkdir --parents %{buildroot}%{_datadir}/applications
cat <<EOT >> %{buildroot}%{_datadir}/applications/%{name}.desktop
[Desktop Entry]
Type=Application
Name=Visual Studio Code
GenericName=Text Editor
Comment=Code Editing. Redefined.
Exec=%{name} %U
Icon=%{name}
Terminal=false
StartupNotify=true
StartupWMClass=VSCode
Categories=Utility;TextEditor;Development;IDE;
MimeType=text/plain;
Actions=new-window;
Keywords=Text;Editor;vscode;
Keywords[zh_CN]=文本;编辑器;Text;Editor;vscode;

[Desktop Action new-window]
Name=New Window
Name[de]=Neues Fenster
Name[es]=Nueva ventana
Name[fr]=Nouvelle fenêtre
Name[it]=Nuova finestra
Name[ja]=新規ウインドウ
Name[ko]=새 창
Name[ru]=Новое окно
Name[zh_CN]=新建窗口
Name[zh_TW]=開新視窗
Exec=%{name} --new-window %U
Icon=%{name}
EOT

desktop-file-install --mode 0644 %{buildroot}%{_datadir}/applications/%{name}.desktop

# Change appName
install -m 0644 %{S:1} %{buildroot}%{_libdir}/%{name}/product.json
sed -i -e \
   '/Short/s|:.*,$|: "VSCode",|
    /Long/s|:.*,$|: "Visual Studio Code",|' \
    %{buildroot}%{_libdir}/%{name}/product.json

# About.json
sed -i '$a\\t"commit": "%{_commit}",\n\t"date": "'`date -u +%FT%T.%3NZ`'",\n\t"checksums": {' \
    %{buildroot}%{_libdir}/%{name}/product.json
sed -i '2s|:.*,$|: "VSCode",|' \
    %{buildroot}%{_libdir}/%{name}/package.json

# Compute checksum
%{hash}
%{line_num}
%{_files}
pushd ../VSCode-linux-*/out/
for i in `seq ${#files[@]}`; do
  _md5=`MD5 ${files[$((i-1))]}`
  sed -i '$a\\t\t"'${files[$((i-1))]}'": "'${_md5}'"' %{buildroot}%{_libdir}/%{name}/product.json
  if [ ${#files[@]} -ne $i ]; then
    _ln=`LN %{buildroot}%{_libdir}/%{name}/product.json`
    sed -i ''${_ln}'s|$|,|' %{buildroot}%{_libdir}/%{name}/product.json
  else
    sed -i '$a\\t}\n}' %{buildroot}%{_libdir}/%{name}/product.json
  fi
done

# find all *.js files and generate node.file-list
pushd ..
for ext in js json node; do
    find node_modules -iname "*.${ext}" \
    ! -path '*doc*' \
    ! -path '*test*' \
    ! -path '*tools*' \
    ! -path '*example*' \
    ! -path '*obj.target*' \
    -exec sh -c "strip '{}' &>/dev/null ||:" \; \
    -exec install -Dm644 '{}' '%{buildroot}%{_libdir}/%{name}/{}' \;
done
popd

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null ||:
/usr/bin/update-desktop-database &>/dev/null ||:

%postun
if [ $1 -eq 0 ]; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null ||:
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null ||:
fi
/usr/bin/update-desktop-database &>/dev/null ||:

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null ||:

%files
%defattr(-,root,root,-)
%doc README.md ThirdPartyNotices.txt
%license LICENSE.txt
%attr(755,-,-) %{_bindir}/%{name}
%{_libdir}/%{name}/
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/applications/%{name}.desktop

%changelog
* Tue Jan  3 2017 mosquito <sensor.wen@gmail.com> - 1.8.1-1
- Release 1.8.1
* Sat Dec  3 2016 mosquito <sensor.wen@gmail.com> - 1.7.2-2
- Fix reopen /usr/lib64/vscode/ directory every time
* Thu Dec  1 2016 mosquito <sensor.wen@gmail.com> - 1.7.2-1
- Release 1.7.2
* Sun Oct 16 2016 mosquito <sensor.wen@gmail.com> - 1.6.1-2
- Compute checksum
* Sat Oct 15 2016 mosquito <sensor.wen@gmail.com> - 1.6.1-1
- Release 1.6.1
* Thu Oct  6 2016 mosquito <sensor.wen@gmail.com> - 1.5.3-1
- Release 1.5.3
* Wed Jul 13 2016 mosquito <sensor.wen@gmail.com> - 1.3.1-1
- Release 1.3.1
- Build for electron 1.2.7
* Fri Jun 17 2016 mosquito <sensor.wen@gmail.com> - 1.2.1-1
- Release 1.2.1
- Build for electron 1.2.3
* Tue May 31 2016 mosquito <sensor.wen@gmail.com> - 1.2.0-2
- Use ELECTRON_RUN_AS_NODE for Electron 1.2.0
* Mon May 30 2016 mosquito <sensor.wen@gmail.com> - 1.2.0-1
- Release 1.2.0
- Build for electron 1.2.0
- Use ELECTRON_RUN_AS_NODE environment variable
* Fri May  6 2016 mosquito <sensor.wen@gmail.com> - 1.1.0-1
- Release 1.1.0 (insiders)
- Build for electron 0.37.8
- fsevents dont support linux
- Fix postinstall.js script
* Thu Apr 14 2016 mosquito <sensor.wen@gmail.com> - 1.0.0-1
- Release 1.0.0
- Improve i18n
* Wed Apr 13 2016 mosquito <sensor.wen@gmail.com> - 0.10.15-1
- Release 0.10.15 (insiders)
- Use gulp-tsb 1.10.3 for node 0.12
* Tue Apr 12 2016 mosquito <sensor.wen@gmail.com> - 0.10.14-2
- Build test for electron 0.37.5
- Use node 0.12 to build native module
* Wed Apr  6 2016 mosquito <sensor.wen@gmail.com> - 0.10.14-1
- Release 0.10.14 (insiders)
- Build test for electron 0.37.4, but running crash
- Use node 4.x to build native module
- Update nan 2.2.0, fixes oniguruma native module build error
- Fix crash by remove value of aiConfig
  https://github.com/electron/electron/issues/4299
* Sat Mar 12 2016 mosquito <sensor.wen@gmail.com> - 0.10.10-3
- Rebuild for electron 0.36.11
* Tue Mar  8 2016 mosquito <sensor.wen@gmail.com> - 0.10.10-2
- Fixed extensionsGallery url
* Tue Mar  8 2016 mosquito <sensor.wen@gmail.com> - 0.10.10-1
- Release 0.10.10
- Spilt package
- Update electron to 0.36.10
* Thu Feb 11 2016 mosquito <sensor.wen@gmail.com> - 0.10.8-1
- Release 0.10.8
- Remove welcome.md
* Thu Dec 24 2015 mosquito <sensor.wen@gmail.com> - 0.10.6-1
- Release 0.10.6
* Sun Dec 20 2015 mosquito <sensor.wen@gmail.com> - 0.10.5-1
- Release 0.10.5
* Fri Dec 04 2015 mosquito <sensor.wen@gmail.com> - 0.10.3-1
- Release 0.10.3
* Thu Nov 26 2015 mosquito <sensor.wen@gmail.com> - 0.10.2-1
- Release 0.10.2
- Add about information
* Wed Nov 25 2015 mosquito <sensor.wen@gmail.com> - 0.10.1-1
- Initial build
