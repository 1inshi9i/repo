%global debug_package %{nil}
%global __provides_exclude (npm)
%global __requires_exclude (npm|0.7)

%global project LightTable
%global repo %{project}

%global _commit b83f440115726199563c232364e9b3168456b701
%global _shortcommit %(c=%{_commit}; echo ${c:0:7})

Name:    lighttable
Version: 0.8.1
Release: 5%{?dist}
Summary: LightTable - An open source code editor

Group:   Development/Tools
License: MIT
URL:     https://github.com/LightTable/LightTable
Source0: %{url}/archive/%{_commit}/%{repo}-%{_shortcommit}.tar.gz
Patch0:  fix-lt-exception.patch
Patch1:  fix-electron-1.2.0.patch

BuildArch: noarch
BuildRequires: /usr/bin/npm, git
BuildRequires: leiningen
BuildRequires: desktop-file-utils
Requires: electron

%description
Light Table is a next generation code editor that
connects you to your creation with instant feedback.
Light Table is very customization and can display
anything a Chromium browser can.

%prep
%setup -q -n %{repo}-%{_commit}
%patch0 -p1
%patch1 -p1

%build
# Build the core cljs
rm -f deploy/core/node_modules/lighttable/bootstrap.js
lein cljsbuild once app

# Fixes Invalid match arg /\./ for electron 0.37.x
#https://github.com/lazerwalker/clojurescript-koans/issues/13#issuecomment-184464285
sed -i '/b.hasOwnProperty/s@))@))||true@' \
    deploy/core/node_modules/lighttable/bootstrap.js

# Fetch plugins
#https://github.com/LightTable/LightTable/blob/master/script/build.sh
PLUGINS=(
    'Clojure,0.3.3'
    'CSS,0.0.6'
    'Emmet,0.0.2'
    'HTML,0.1.0'
    'Javascript,0.2.0'
    'Paredit,0.0.4'
    'Python,0.0.7'
    'Rainbow,0.0.8'
    'Vim,0.2.1'
    'Whitespace,0.0.1'
)

# Plugins cache
mkdir -p deploy/plugins
pushd deploy/plugins
    for plugin in "${PLUGINS[@]}"; do
        NAME="${plugin%%,*}"
        VERSION="${plugin##*,}"
        echo "Cloning plugin $NAME $VERSION..."
        git clone "https://github.com/LightTable/$NAME"
        cd $NAME
        git checkout --quiet $VERSION
        cd -
    done
popd

%install
# Data files
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -R deploy/core %{buildroot}%{_datadir}/%{name}
cp deploy/core/package.json %{buildroot}%{_datadir}/%{name}
sed -i 's|main.js|core\/main.js|' %{buildroot}%{_datadir}/%{name}/package.json
cp -R deploy/settings %{buildroot}%{_datadir}/%{name}
cp -R deploy/plugins %{buildroot}%{_datadir}/%{name}
rm -rf %{buildroot}%{_datadir}/%{name}/core/node_modules

# Bin file
mkdir -p %{buildroot}%{_bindir}
cat <<EOT >> %{buildroot}%{_bindir}/%{name}
#!/bin/bash
NAME="%{name}"
LIGHT_PATH="%{_datadir}/\$NAME"
ELECTRON="%{_bindir}/electron"
"\$ELECTRON" "\$LIGHT_PATH" "\$@"
exit \$?
EOT

# Icon files
install -Dm 0644 deploy/core/img/lticon.png \
    %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{name}.png

# Desktop file
mkdir -p %{buildroot}%{_datadir}/applications
cat <<EOT >> %{buildroot}%{_datadir}/applications/%{name}.desktop
[Desktop Entry]
Type=Application
Name=Light Table
GenericName=Light Table
Comment=Code Editing.
Exec=%{name}
Icon=%{name}
Terminal=false
Categories=GTK;Development;IDE;
MimeType=text/plain;text/x-chdr;text/x-csrc;text/x-c++hdr;text/x-c++src;text/x-java;text/x-dsrc;text/x-pascal;text/x-perl;text/x-python;application/x-php;application/x-httpd-php3;application/x-httpd-php4;application/x-httpd-php5;application/xml;text/html;text/css;text/x-sql;text/x-diff;
StartupNotify=true
EOT

desktop-file-install -m 644 %{buildroot}%{_datadir}/applications/%{name}.desktop

# find all *.js files and generate node.file-list
pushd deploy/core
for ext in js json node types css html; do
    find node_modules -iname "*.${ext}" \
    ! -path '*doc*' \
    ! -path '*test*' \
    ! -path '*sample*' \
    ! -path '*example*' \
    ! -path '*benchmark*' \
    ! -path '*obj.target*' \
    -exec install -Dm644 '{}' '%{buildroot}%{_datadir}/%{name}/core/{}' \;
done

find %{buildroot} -name '.*' | xargs rm -rf

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
%doc README.md
%license LICENSE.md
%attr(755,-,-) %{_bindir}/%{name}
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/applications/%{name}.desktop
%defattr(-,root,root,757)
%{_datadir}/%{name}/

%changelog
* Mon Jan 16 2017 mosquito <sensor.wen@gmail.com> - 0.8.1-5
- Update to latest (b83f440)
* Mon Jun 20 2016 mosquito <sensor.wen@gmail.com> - 0.8.1-4
- Fixes path must be a string for electron 1.2.3
* Sat Jun  4 2016 mosquito <sensor.wen@gmail.com> - 0.8.1-3
- Fixes running error for electron 1.2.0
- Update some plugins
* Wed Apr 13 2016 mosquito <sensor.wen@gmail.com> - 0.8.1-2
- Fixes Invalid match arg /\./ for electron 0.37.x
* Mon Mar 28 2016 mosquito <sensor.wen@gmail.com> - 0.8.1-1
- Initial build
