Name:       r7office-sfos-installer
Version:    1.2.0
Release:    1
Summary:    Fetches R7 Documents from the vendor and sets it up for Sailfish
License:    MIT
URL:        https://github.com/smatkovi/r7office-sfos
ExclusiveArch: aarch64

# squircle-icon.py imports Pillow inside a try block and bows out politely when
# it is missing, so the automatic dependency generator must not turn that into a
# hard requirement -- Pillow is not on a stock device.
%global __requires_exclude ^python3dist\\(pillow\\)$

# For fetching and unpacking. aria2 is preferred but lives in Chum, so it is
# only recommended -- the script falls back to curl, which is always present.
Recommends: aria2
Requires:   rpm
Requires:   cpio
Requires:   python3-base
# The Aurora stand-ins are built into this package, so that a single RPM is
# enough on a stock device.
Provides:   libauroraapp-shim = 1.0.0
Conflicts:  libauroraapp-shim
# What R7 itself needs. These are not checked otherwise, because the vendor
# package is unpacked rather than installed through rpm.
Requires:   sailfishsilica-qt5 >= 0.10.9
Requires:   sailfish-components-webview-qt5
Requires:   sailfish-components-webview-qt5-pickers
Requires:   sailfish-components-webview-qt5-popups
Requires:   qtmozembed-qt5
Conflicts:  r7office-sfos-patch

%description
Downloads Р7-Документы (R7 Documents, Aurora OS) from the vendor, verifies its
checksum, unpacks the payload and applies the Sailfish adaptations -- all while
this package is being installed.

Nothing belonging to R7 is shipped here. The adaptations are patch scripts that
are applied to the freshly unpacked files on the device.

The vendor package is unpacked rather than installed through rpm: the RPM
database is locked for the duration of a transaction, so a second rpm always
fails inside a scriptlet. The file list is recorded so that removal stays clean.

Р7-Документы belongs to АО «Р7» and is not bundled here.

BuildRequires: pkgconfig(Qt5Core) pkgconfig(Qt5Gui) pkgconfig(Qt5Quick) libsailfishapp-devel

%prep
%setup -c -T

%build
g++ -std=c++11 -fPIC -shared -O2 -I/usr/include/sailfishapp \
  $(pkg-config --cflags Qt5Core Qt5Gui Qt5Quick) \
  -Wl,-soname,libauroraapp.so.2 -o libauroraapp.so.2 %{_sourcedir}/auroraapp.cpp \
  -lsailfishapp $(pkg-config --libs Qt5Core Qt5Gui Qt5Quick)
g++ -std=c++11 -fPIC -shared -O2 \
  $(pkg-config --cflags Qt5Core) \
  -Wl,-soname,libQt5SystemInfo.so.5 \
  -Wl,--version-script,%{_sourcedir}/qt5systeminfo.map \
  -o libQt5SystemInfo.so.5 %{_sourcedir}/qt5systeminfo.cpp \
  $(pkg-config --libs Qt5Core)

%install
mkdir -p %{buildroot}%{_bindir} %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_datadir}/%{name}/patches
install -m 0644 libauroraapp.so.2 %{buildroot}%{_libdir}/libauroraapp.so.2
install -m 0644 libQt5SystemInfo.so.5 %{buildroot}%{_libdir}/libQt5SystemInfo.so.5
install -m 0755 %{_sourcedir}/r7office-install %{buildroot}%{_bindir}/r7office-install
install -m 0755 %{_sourcedir}/patch_editorpage.py %{buildroot}%{_datadir}/%{name}/patches/
install -m 0755 %{_sourcedir}/patch_filespage.py  %{buildroot}%{_datadir}/%{name}/patches/
install -m 0755 %{_sourcedir}/patch_perms.py      %{buildroot}%{_datadir}/%{name}/patches/
install -m 0755 %{_sourcedir}/squircle-icon.py    %{buildroot}%{_datadir}/%{name}/patches/

%post
if %{_bindir}/r7office-install; then
    :
else
    echo "" >&2
    echo "Setup failed (no network?). Finish it later with:" >&2
    echo "    sudo r7office-install" >&2
fi
exit 0

%postun
if [ $1 -eq 0 ]; then
    TARGET=/usr/share/ru.r7office.documents
    # Undo the adaptations
    for f in pages/EditorPage.qml pages/FilesPage.qml; do
        [ -f "$TARGET/qml/$f.r7orig" ] && mv -f "$TARGET/qml/$f.r7orig" "$TARGET/qml/$f"
    done
    for g in 86 108 128 172; do
        I=/usr/share/icons/hicolor/${g}x${g}/apps/ru.r7office.documents.png
        [ -f "$I.r7orig" ] && mv -f "$I.r7orig" "$I"
    done
    D=/usr/share/applications/ru.r7office.documents.desktop
    [ -f "$D.r7orig" ] && mv -f "$D.r7orig" "$D"
    # Remove the unpacked vendor payload again -- but only when it is not
    # actually installed through rpm.
    if ! rpm -q ru.r7office.documents >/dev/null 2>&1; then
        if [ -f /var/lib/r7office-sfos/files.list ]; then
            while read -r f; do
                [ -f "$f" ] && rm -f "$f"
            done < /var/lib/r7office-sfos/files.list
            sort -r /var/lib/r7office-sfos/files.list | while read -r f; do
                rmdir "$(dirname "$f")" 2>/dev/null || true
            done
        fi
    fi
    rm -rf /var/lib/r7office-sfos /var/tmp/r7office-sfos
fi
exit 0

%files
%{_libdir}/libauroraapp.so.2
%{_libdir}/libQt5SystemInfo.so.5
%{_bindir}/r7office-install
%{_datadir}/%{name}
