#!/usr/bin/env python3
"""
HTML <img> optimizer for bmwhotel.com.

For every <img> in every *.html:
  - adds loading="lazy"          (except first <img> on each page = hero)
  - adds decoding="async"
  - adds width/height            (read from actual file via `sips`)
  - adds fetchpriority="high"    on the hero image
"""
import os, re, subprocess, sys, html

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "images")

_dim_cache = {}
def dims(rel_src):
    """Return (w, h) for an image path relative to repo root, or None."""
    if rel_src in _dim_cache:
        return _dim_cache[rel_src]
    path = os.path.join(ROOT, rel_src)
    if not os.path.isfile(path):
        _dim_cache[rel_src] = None
        return None
    try:
        out = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
            text=True, stderr=subprocess.DEVNULL,
        )
        w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
        h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
        _dim_cache[rel_src] = (w, h)
        return (w, h)
    except Exception:
        _dim_cache[rel_src] = None
        return None

IMG_TAG_RE = re.compile(r"<img\b([^>]*?)/?>", re.IGNORECASE)
ATTR_RE = re.compile(r'(\w[\w:-]*)\s*=\s*"([^"]*)"|(\w[\w:-]*)\s*=\s*\'([^\']*)\'|(\w[\w:-]*)')

def parse_attrs(s):
    """Parse attribute string into list of (name, value, raw) preserving order."""
    attrs = []
    for m in ATTR_RE.finditer(s):
        if m.group(1):
            attrs.append((m.group(1).lower(), m.group(2)))
        elif m.group(3):
            attrs.append((m.group(3).lower(), m.group(4)))
        elif m.group(5):
            attrs.append((m.group(5).lower(), None))
    return attrs

def render_attrs(attrs):
    parts = []
    for k, v in attrs:
        if v is None:
            parts.append(k)
        else:
            parts.append(f'{k}="{html.escape(v, quote=True)}"')
    return " ".join(parts)

def upset(attrs, name, value):
    """Set or insert attr; return new list."""
    name = name.lower()
    for i, (k, _) in enumerate(attrs):
        if k == name:
            attrs[i] = (name, value)
            return attrs
    attrs.append((name, value))
    return attrs

def has(attrs, name):
    name = name.lower()
    return any(k == name for k, _ in attrs)

def process_html(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    img_index = [0]
    changes = [0]

    def replace(m):
        inside = m.group(1)
        attrs = parse_attrs(inside)
        is_hero = img_index[0] == 0
        img_index[0] += 1

        src_attr = next((v for k, v in attrs if k == "src"), None)
        if not src_attr:
            return m.group(0)

        original = render_attrs(attrs)

        # width/height from file
        if not has(attrs, "width") and not has(attrs, "height"):
            d = dims(src_attr.lstrip("/"))
            if d:
                w, h = d
                attrs = upset(attrs, "width", str(w))
                attrs = upset(attrs, "height", str(h))

        # decoding
        if not has(attrs, "decoding"):
            attrs = upset(attrs, "decoding", "async")

        # loading / fetchpriority
        if is_hero:
            if not has(attrs, "fetchpriority"):
                attrs = upset(attrs, "fetchpriority", "high")
            # explicitly do NOT lazy-load the hero
        else:
            if not has(attrs, "loading"):
                attrs = upset(attrs, "loading", "lazy")

        new = render_attrs(attrs)
        if new != original:
            changes[0] += 1
        return f"<img {new}>"

    new_src = IMG_TAG_RE.sub(replace, src)
    if new_src != src:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_src)
    return changes[0], img_index[0]

def main():
    total_files = 0
    total_imgs = 0
    total_changes = 0
    for fname in sorted(os.listdir(ROOT)):
        if not fname.endswith(".html"):
            continue
        path = os.path.join(ROOT, fname)
        ch, n = process_html(path)
        if n:
            total_files += 1
            total_imgs += n
            total_changes += ch
            print(f"  {fname:<24} {n:>3} imgs, {ch:>3} changed")
    print(f"\n{total_files} files, {total_imgs} <img> tags total, {total_changes} updated")

if __name__ == "__main__":
    main()
