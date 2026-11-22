#!/usr/bin/env python3
"""Generate small, consistently encoded posters for the movie popup."""
from pathlib import Path
from PIL import Image, ImageOps

directory = Path("posters")
for name in ("shchedryk", "pamfir", "pekelna-khoruhva"):
    source = directory / f"{name}.jpeg"
    target = directory / f"{name}.webp"
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        image.thumbnail((900, 1350), Image.Resampling.LANCZOS)
        image = image.convert("RGB")
        image.save(target, "WEBP", quality=78, method=6)
    print(f"{source}: {source.stat().st_size:,} bytes => {target}: {target.stat().st_size:,} bytes")
