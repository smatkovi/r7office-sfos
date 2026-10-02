#!/bin/bash
# Builds libauroraapp.so.2 against a Sailfish target. Run inside the SDK.
set -e
TARGET=${1:-SailfishOS-5.2.0.15-aarch64}
cd "$(dirname "$0")"
sb2 -t "$TARGET" g++ -std=c++11 -fPIC -shared -O2 \
  -I/usr/include/sailfishapp \
  $(sb2 -t "$TARGET" pkg-config --cflags Qt5Core Qt5Gui Qt5Quick) \
  -Wl,-soname,libauroraapp.so.2 \
  -o libauroraapp.so.2 auroraapp.cpp \
  -lsailfishapp $(sb2 -t "$TARGET" pkg-config --libs Qt5Core Qt5Gui Qt5Quick)
echo "== symbols =="
nm -D --defined-only libauroraapp.so.2 | grep Aurora
