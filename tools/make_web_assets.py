# -*- coding: utf-8 -*-
"""
Convert the pipeline's master files into the smaller files the page loads.

Run after make_texture.py / make_condensation.py, or whenever a master changes:

    python tools/make_web_assets.py

The masters stay as they are (JPG/PNG, full quality) - they are the inputs.
The page only ever loads the .webp files written here.

Measured 23 Sep 2026:
  can_coke.jpg   588 KB -> can_coke.webp   131 KB  (2048 px kept: 1024 px went soft
  can_pepsi.jpg  612 KB -> can_pepsi.webp  133 KB   on a 2x display, the can wrap is
                                                    ~1200 texels tall on screen)
  can_normal.png 618 KB -> can_normal.webp 564 KB  LOSSLESS on purpose: lossy WebP
      subsamples chroma, and R/G of a normal map ARE the direction. Even q100 lossy
      tilted the droplet normals by 6.5 deg on average (p99 27 deg) and put up to
      21 deg bumps into the flat metal.
"""
import io
import os
import sys

from PIL import Image

HERE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
A = os.path.join(HERE, "assets")

JOBS = [
    # (master, output, save kwargs)
    ("can_coke.jpg",    "can_coke.webp",    dict(quality=85, method=6)),
    ("can_pepsi.jpg",   "can_pepsi.webp",   dict(quality=85, method=6)),
    ("can_normal.png",  "can_normal.webp",  dict(lossless=True, method=6)),
    ("bottle_coke.png", "bottle_coke.webp", dict(quality=88, method=6, alpha_quality=100)),
    ("globe_pepsi.png", "globe_pepsi.webp", dict(quality=88, method=6, alpha_quality=100)),
]

for src, dst, kw in JOBS:
    sp, dp = os.path.join(A, src), os.path.join(A, dst)
    if not os.path.exists(sp):
        sys.exit("ABORT: missing master %s" % sp)
    im = Image.open(sp)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", **kw)
    with open(dp, "wb") as f:
        f.write(buf.getvalue())
    print("%-16s %5d KB -> %-17s %5d KB  %s" % (src, os.path.getsize(sp) // 1024, dst,
                                               os.path.getsize(dp) // 1024, "x".join(map(str, im.size))))
