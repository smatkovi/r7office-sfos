# Self-fetching installer package

Builds an aarch64 RPM that, when installed, downloads R7 Documents from the
vendor, verifies its checksum, unpacks it and applies the adaptations — in one
`rpm -Uvh`, no reboot.

**One package is enough, and it ships nothing belonging to R7.** The
adaptations travel as the patch scripts from `patches/`, which are applied to
the freshly unpacked files on the device — so the package is MIT throughout and
can be published.

It carries the Aurora stand-ins itself (hence `Provides: libauroraapp-shim` and
`Conflicts:` with the separate shim package), and everything else it needs —
`rpm`, `cpio`, `python3-base`, Silica, the WebView components — is stock
Sailfish. `aria2c` is only *recommended*: it is quicker, but it lives in Chum,
so the script falls back to `curl` when it is missing.

The icon step needs Pillow, which is not on a stock device and may be installed
only for your user rather than system-wide. The installer runs as root, so it
skips the icon with a note when it cannot import it. To apply it afterwards:

```sh
T=$(mktemp -d)
python3 /usr/share/r7office-sfos-installer/patches/squircle-icon.py "$T"
for g in 86 108 128 172; do
  sudo cp "$T/ru.r7office.documents-$g.png" \
          /usr/share/icons/hicolor/${g}x${g}/apps/ru.r7office.documents.png
done
```

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

Everything the package needs is in this repository. Copy `r7office-install`,
the four scripts from `../patches/`, and the shim sources from
`../auroraapp-shim/` into `~/rpmbuild/SOURCES`, then:

```sh
sb2 -t SailfishOS-5.2.0.15-aarch64 -m sdk-build \
    rpmbuild --target aarch64 -bb r7office-sfos-installer.spec
```

## Removal

```sh
sudo rpm -e r7office-sfos-installer
```

Restores the original QML, icons and desktop file, and deletes the unpacked
vendor files listed in `files.list`.
