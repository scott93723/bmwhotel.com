#!/usr/bin/env python3
"""
Compress JPGs in images/ smartly using macOS `sips`:
  - Resize so max dimension <= 1920 (most screens never need more)
  - Try quality 70; only keep result if it's actually smaller than original
  - Skip files already <= 100KB (not worth touching)
  - Always resize huge files (>2MB or >2400px) regardless

Reports per-file before/after and totals.
"""
import os, subprocess, re, shutil, tempfile

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
MAX_DIM = 1920
QUALITY = 70
SKIP_BELOW = 100 * 1024     # don't bother re-encoding tiny files
ALWAYS_RESIZE_PX = 2400      # absurdly oversized -> always resize

def get_dims(path):
    out = subprocess.check_output(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
        text=True, stderr=subprocess.DEVNULL,
    )
    w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
    h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
    return w, h

def compress(path):
    before = os.path.getsize(path)
    if before < SKIP_BELOW:
        return before, before, "skip-small"
    w, h = get_dims(path)
    oversized = max(w, h) > ALWAYS_RESIZE_PX

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        args = ["sips"]
        if max(w, h) > MAX_DIM:
            args += ["-Z", str(MAX_DIM)]
        args += ["-s", "format", "jpeg",
                 "-s", "formatOptions", str(QUALITY),
                 path, "--out", tmp_path]
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        after = os.path.getsize(tmp_path)
        # Only swap in the new file if it's smaller, OR if the original was absurdly oversized
        if after < before or oversized:
            shutil.move(tmp_path, path)
            return before, after, "compressed" if after < before else "downsized"
        else:
            return before, before, "kept-original"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def fmt(n):
    if n >= 1024 * 1024:
        return f"{n/1024/1024:.1f}MB"
    return f"{n//1024}KB"

def main():
    total_before = 0
    total_after = 0
    files = sorted(f for f in os.listdir(IMG_DIR)
                   if f.lower().endswith((".jpg", ".jpeg")))
    for f in files:
        path = os.path.join(IMG_DIR, f)
        before, after, status = compress(path)
        total_before += before
        total_after += after
        saved_pct = (1 - after / before) * 100 if before else 0
        if status == "skip-small":
            continue
        if status == "kept-original":
            marker = "= "
        elif saved_pct >= 50:
            marker = "**"
        elif saved_pct >= 30:
            marker = " *"
        else:
            marker = "  "
        print(f"{marker} {f:<22} {fmt(before):>7} -> {fmt(after):>7}  (-{saved_pct:4.1f}%)  {status}")
    saved = total_before - total_after
    pct = (1 - total_after / total_before) * 100 if total_before else 0
    print(f"\nTotal: {fmt(total_before)} -> {fmt(total_after)}  saved {fmt(saved)} ({pct:.1f}%)")

if __name__ == "__main__":
    main()
