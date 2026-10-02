#!/usr/bin/env python3
"""Cut the R7 icon to the Sailfish launcher silhouette.

The silhouette is a superellipse, |x|^n + |y|^n = 1. Fitting it against a real
stock icon's alpha channel gives n = 2.8 at 0.98 of the full radius, which
matches to within 0.34 % of the pixels -- close enough that nothing of the
stock artwork needs to be carried around.

The mask is built at four times the final size and only then scaled down,
otherwise the curve frays. The artwork is enlarged slightly so R7's own,
squarer corners fall outside the squircle edge.
"""
import sys

try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed - skipping the icon.", file=sys.stderr)
    raise SystemExit(0)

SOURCE = "/usr/share/icons/hicolor/172x172/apps/ru.r7office.documents.png"
SIZES = (86, 108, 128, 172)
EXPONENT = 2.8
RADIUS = 0.98
BLEED = 1.06          # artwork slightly larger than the mask
SUPERSAMPLE = 4


def squircle(size):
    """The launcher silhouette as an alpha mask."""
    mask = Image.new("L", (size, size), 0)
    pixels = mask.load()
    centre = (size - 1) / 2.0
    radius = centre * RADIUS
    for y in range(size):
        dy = (abs(y - centre) / radius) ** EXPONENT
        for x in range(size):
            dx = (abs(x - centre) / radius) ** EXPONENT
            if dx + dy <= 1.0:
                pixels[x, y] = 255
    return mask


def main(outdir):
    source = Image.open(SOURCE).convert("RGBA")
    for size in SIZES:
        big = size * SUPERSAMPLE
        mask = squircle(big)
        inner = int(big * BLEED)
        image = source.resize((inner, inner), Image.LANCZOS)
        edge = (inner - big) // 2
        image = image.crop((edge, edge, edge + big, edge + big))
        # The mask defines the shape; the artwork is opaque inside, so it is
        # enough on its own as the alpha channel.
        image.putalpha(mask)
        image = image.resize((size, size), Image.LANCZOS)
        target = "%s/ru.r7office.documents-%d.png" % (outdir, size)
        image.save(target)
        print("written:", target)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
