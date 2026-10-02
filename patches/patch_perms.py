#!/usr/bin/env python3
"""Widen the Sailjail permissions.

Purely additive -- the sandbox stays on. RemovableMedia and UDisks cover USB
and SD storage, Sharing covers the share menu, Thumbnails the previews.
"""
PATH = "/usr/share/applications/ru.r7office.documents.desktop"
OLD = "Permissions=Internet;MediaIndexing;UserDirs;WebView"
NEW = OLD + ";RemovableMedia;UDisks;Sharing;Thumbnails"

def main():
    text = open(PATH).read()
    if OLD + "\n" not in text:
        raise SystemExit("permission line not found -- already patched?")
    open(PATH, "w").write(text.replace(OLD + "\n", NEW + "\n", 1))
    print("permissions set:", NEW)

if __name__ == "__main__":
    main()
