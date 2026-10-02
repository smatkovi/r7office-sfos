#!/usr/bin/env python3
"""Cut the R7 icon to Sailfish's squircle silhouette.

The edges are masked at four times the final size and only then scaled down,
otherwise the curve frays. The artwork is enlarged slightly so R7's own,
squarer corners fall outside the squircle edge.

The mask is the alpha channel of a real stock icon -- approximating the shape
reads as foreign between the stock icons at a glance.
"""
import sys
from PIL import Image

MASK = "/home/defaultuser/ps/meego-icon-tool/mask-icon-l.png"
SOURCE = "/usr/share/icons/hicolor/172x172/apps/ru.r7office.documents.png"
SIZES = (86, 108, 128, 172)
BLEED = 1.06          # artwork slightly larger than the mask


def main(outdir):
    mask = Image.open(MASK).convert("RGBA").split()[3]
    source = Image.open(SOURCE).convert("RGBA")
    for size in SIZES:
        big = size * 4
        m = mask.resize((big, big), Image.LANCZOS)
        inner = int(big * BLEED)
        image = source.resize((inner, inner), Image.LANCZOS)
        edge = (inner - big) // 2
        image = image.crop((edge, edge, edge + big, edge + big))
        # The mask defines the shape; the artwork is opaque inside, so it is
        # enough on its own as the alpha channel.
        image.putalpha(m)
        image = image.resize((size, size), Image.LANCZOS)
        target = "%s/ru.r7office.documents-%d.png" % (outdir, size)
        image.save(target)
        print("written:", target)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
