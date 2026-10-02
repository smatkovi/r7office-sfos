# Self-fetching installer package

Builds an aarch64 RPM that, when installed, downloads R7 Documents from the
vendor with `aria2c`, verifies its checksum, unpacks it and applies the
adaptations — in one `rpm -Uvh`, no reboot.

## Why it unpacks instead of installing

The obvious approach — have `%post` run `rpm -i` on the downloaded package —
cannot work: the RPM database is locked for the duration of a transaction, so a
second rpm inside a scriptlet always fails. Sailfish's `oneshot` mechanism would
defer the work to the next boot, which is clumsy.

So the script extracts the payload itself and records the file list in
`/var/lib/r7office-sfos/files.list`, which `%postun` uses to remove the files
again. A side benefit: the vendor package's header carries a wrong payload
checksum, which `rpm2cpio` does not care about.

**Do not pipe `rpm2cpio` into `cpio`.** On Sailfish it truncates unpredictably
when writing into a pipe — three identical calls here returned 319 MB, 319 MB
and then 5 MB, and `cpio` reports only `premature end of file`. Redirected to a
file it is reliable. The script therefore writes the payload out, deletes the
downloaded package to save room, extracts from the file, and finally counts how
many of the listed files really arrived — a short payload would otherwise pass
unnoticed.

Because that needs room for the package plus the payload (~400 MB), the spool
directory is picked by free space: `/home` when it has room, otherwise
`/var/tmp`. On Sailfish the root filesystem is often too tight for this.

If R7 is already installed through rpm, the script skips the download and only
applies the adaptations.

## Building

The package ships the patched QML, which is derived from R7's own files, so it
is not kept in this repository. Generate it from your own installed copy:

```sh
# with R7 installed and the patches applied (see the top-level README)
mkdir -p build/qml/pages build/icons
cp /usr/share/ru.r7office.documents/qml/pages/EditorPage.qml build/qml/pages/
cp /usr/share/ru.r7office.documents/qml/pages/FilesPage.qml  build/qml/pages/
python3 ../patches/squircle-icon.py build/icons

# then, in the SDK container, with r7office-install, the two .qml files and
# icons/ copied into ~/rpmbuild/SOURCES
sb2 -t SailfishOS-5.2.0.15-aarch64 -m sdk-build \
    rpmbuild --target aarch64 -bb r7office-sfos-installer.spec
```

## Removal

```sh
sudo rpm -e r7office-sfos-installer
```

Restores the original QML, icons and desktop file, and deletes the unpacked
vendor files listed in `files.list`.
