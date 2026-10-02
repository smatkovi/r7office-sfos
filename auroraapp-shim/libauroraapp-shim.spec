Name:       libauroraapp-shim
Version:    1.0.0
Release:    1
Summary:    Stand-ins for Aurora OS libraries on Sailfish OS
License:    MIT
URL:        https://github.com/smatkovi/r7office-sfos
BuildRequires: pkgconfig(Qt5Core) pkgconfig(Qt5Gui) pkgconfig(Qt5Quick) libsailfishapp-devel
%description
Maps the five Aurora::Application symbols that Aurora OS applications import
onto libsailfishapp, and provides a stand-in for libQt5SystemInfo.so.5 covering
the four IMEI symbols R7 Documents needs.

Note: Aurora::Application::getPath() and cacheDir() return QDir, not QString.

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
mkdir -p %{buildroot}%{_libdir}
install -m 0644 libauroraapp.so.2 %{buildroot}%{_libdir}/libauroraapp.so.2
install -m 0644 libQt5SystemInfo.so.5 %{buildroot}%{_libdir}/libQt5SystemInfo.so.5

%files
%{_libdir}/libauroraapp.so.2
%{_libdir}/libQt5SystemInfo.so.5
