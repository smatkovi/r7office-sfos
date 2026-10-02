# R7 Documents on Sailfish OS

A kit for running the **Aurora OS build of Р7-Документы** (R7 Documents, an
ONLYOFFICE derivative) unchanged on Sailfish OS — with a working editor and a
working file list.

Tested on a **Jolla Phone (2026), Sailfish OS 5.2.0.18, aarch64**.

## The vendor package

This kit contains **nothing** belonging to R7. The application itself is a free
download from the vendor and has to be fetched there:

```
https://download.r7-office.ru/aurora/ru.r7office.documents-1.5.5.2126-1.aarch64.rpm
```

85 MB, no login required, linked from the
[R7 download catalogue](https://support.r7-office.ru/download/desktop-editors/)
under „Р7-Документы для ОС Аврора (офлайн приложение)".

Two things to know about it:

* The package header carries a **wrong payload checksum** (`rpm -K` fails) while
  the payload itself is complete (1031 files). Install it with `--nodigest`.
* It exists for **aarch64 only**. There is nothing to run on armv7hl devices,
  even though the shim is built for that architecture too.

## Installation

**The short way — one package, nothing else:**

```sh
sudo rpm -Uvh r7office-sfos-installer-1.2.0-1.aarch64.rpm
```

It fetches R7 from the vendor, verifies it, unpacks it and applies everything
below. `sudo rpm -e r7office-sfos-installer` undoes all of it. Details in
[installer/README.md](installer/README.md).

**Or by hand:**

```sh
# 1. The shim (from this repository's releases)
sudo rpm -Uvh libauroraapp-shim-1.0.0-1.aarch64.rpm

# 2. The application, from the vendor
curl -LO https://download.r7-office.ru/aurora/ru.r7office.documents-1.5.5.2126-1.aarch64.rpm
sudo rpm -Uvh --nodigest ru.r7office.documents-1.5.5.2126-1.aarch64.rpm

# 3. The adaptations
sudo python3 patches/patch_editorpage.py
sudo python3 patches/patch_filespage.py
sudo python3 patches/patch_perms.py
python3 patches/squircle-icon.py /tmp/icons && \
  for g in 86 108 128 172; do
    sudo cp /tmp/icons/ru.r7office.documents-$g.png \
            /usr/share/icons/hicolor/${g}x${g}/apps/ru.r7office.documents.png
  done
```

The patch scripts abort when they cannot find their anchors — they are written
against version **1.5.5.2126**.

## What needs adapting, and why

### 1. `libauroraapp.so.2` — the shim

The application is an ordinary **Sailfish Silica app**; apart from one entry its
dependencies are pure Sailfish (`sailfishsilica-qt5`,
`sailfish-components-webview-qt5`, `qtmozembed-qt5`, …). The only Aurora-specific
library is `libauroraapp.so.2`, and exactly five of its symbols are used:

```
Aurora::Application::application(int&, char**)
Aurora::Application::createView()
Aurora::Application::pathTo(QString const&)
Aurora::Application::getPath(PathType)
Aurora::Application::cacheDir(bool)
```

`auroraapp-shim` maps them onto `libsailfishapp`. **The trap:** `getPath()` and
`cacheDir()` return **`QDir`**, not `QString` — returning a QString segfaults
inside `QDir::path()` straight out of `main()`.

Alongside it comes a stand-in for `libQt5SystemInfo.so.5`, which Sailfish does
not ship. Only four symbols are needed from it, all about the IMEI
(`QDeviceInfo::imei`/`imeiCount`); they report "no IMEI". The `Qt_5` version node
has to be set with `--version-script`, otherwise the package does not provide
`libQt5SystemInfo.so.5(Qt_5)(64bit)` and rpm refuses to install R7.

### 2. `EditorPage.qml` — without this the editor stays blank

Aurora's `Sailfish.WebView` has a `urlLoadingOverride` property; Sailfish 5.2
does not. Assigning it makes the entire WebView component fail to instantiate,
so the editor never appears and all you see is Silica's loader error. Replaced
with the `linkClicked(url)` signal.

This single property was the **only** reason documents would not open. With it
fixed the whole chain runs: `x2t` converts, the built-in HTTP server listens on
`127.0.0.1:10042`, and the mobile sdkjs frontend loads.

### 3. `FilesPage.qml` — our own file list

R7's `FilesModel` sends its Tracker queries correctly — one per extension, with
a working output file descriptor, and no error reply — but **never reads the
results back**. The list therefore always stays empty ("Documents not found")
even though Tracker happily returns the documents.

Measured from inside the sandbox: the very same query delivers both test
documents there. Neither Tracker nor Sailjail is at fault, and
`Sandboxing=Disabled` is **not** needed.

The patch points the list view at our own model, which scans
`StandardPaths.documents` and `.download` with a `FolderListModel` for the known
extensions. The roles (`path`, `fileName`, `extension`, `size`, `lastChanges`)
are the ones the delegate already uses, so search, delete, rename and share keep
working untouched.

### 4. Odds and ends

* Sailjail permissions widened by `RemovableMedia;UDisks;Sharing;Thumbnails`
  (purely additive — the sandbox stays on).
* Icons cut to the Sailfish silhouette.

## One-step installer

`installer/` builds that single package. It ships nothing belonging to R7 — the
adaptations travel as the patch scripts above and are applied on the device —
so it is MIT throughout and published here.
See [installer/README.md](installer/README.md).

## Building

```sh
# inside the Sailfish SDK container
cd auroraapp-shim
sb2 -t SailfishOS-5.2.0.15-aarch64 -m sdk-build rpmbuild --target aarch64 -bb libauroraapp-shim.spec
```

`build.sh` builds just the library, without the RPM wrapper.

## Debugging

The shim can keep a log. Started with `R7_LOG=1` in the environment, the Aurora
calls **and every Qt message from the application** end up in:

```
~/.cache/ru.r7office/documents/shim.log
```

The application's messages only show up because the shim reinstalls the Qt
message handler inside `createView()` — that is, *after* R7 has installed its
own and displaced the one from the library constructor — and turns the logging
categories on. That is how the `urlLoadingOverride` error was found; before
that, the application appeared completely silent.

More background in [ANALYSIS.md](ANALYSIS.md).

## Licence

The code in this repository (shim, patch scripts) is MIT.
Р7-Документы itself is proprietary and belongs to АО «Р7» — it is neither
bundled here nor redistributed in modified form. The patches change only the
copy installed on your own device.
