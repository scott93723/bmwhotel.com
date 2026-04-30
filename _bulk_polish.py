#!/usr/bin/env python3
"""
Per-page polish:
  1. Hamburger menu a11y:
       - <button class="hamburger">  -> add aria-label, aria-expanded, aria-controls; drop inline onclick
       - <button class="nav-close">  -> add aria-label; drop inline onclick
       - Inject a tiny IIFE near </body> that wires up: click toggle + ESC + backdrop close
         (idempotent: guarded by data-nav-wired flag)
  2. Per-page SEO meta:
       - <link rel="canonical">
       - Open Graph (title, description, url, image, locale, site_name, type)
       - Twitter card
     Skips files that already have og:title (so the rich index.html block stays put).

Line endings of the original file are preserved.
"""
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://bmwhotel.com"
SITE_NAME = "香林田莊 BMW M Power 民宿"
DEFAULT_DESC = "日月潭香林田莊，BMW M3 Power 風格民宿，主打 M 三色視覺、特色房型、咖啡空間與日月潭旅遊。"
DEFAULT_OG_IMG = f"{BASE_URL}/images/home10.jpg"

# Per-page description override (keep tone consistent, add unique angle for SEO)
PAGE_DESC = {
    "index.html":      None,  # already has rich meta
    "about_us.html":   "認識日月潭香林田莊：BMW M Power 風格民宿的故事、空間與經營理念。",
    "house.html":      "日月潭香林田莊房型介紹，包含 M1、M3、M5、M6 等主題房型，可查看設備、床型與住宿亮點。",
    "mpower.html":     "M Power 主題咖啡館，主打 BMW 三色視覺空間、輕食咖啡與住客專屬下午茶。",
    "share.html":      "日月潭周邊景點推薦：九族文化村、清境農場、妖怪村，香林田莊出發路線一次看。",
    "nature.html":     "日月潭夏夜限定行程：賞螢火蟲、生態導覽，住宿即可參加的療癒夜遊。",
    "shop.html":       "BMW M 風格禮品店：M 三色周邊、模型、紀念商品，住客可現場選購或預訂。",
    "fish.html":       "日月潭釣魚船屋體驗：帶你登船下竿、認識湖上漁夫文化的獨家行程。",
    "news.html":       "日月潭香林田莊最新消息、優惠活動與住宿資訊更新。",
    "buy.html":        "線上訂房與付款說明：日月潭香林田莊的房型價格、入住須知、交通指引。",
    "rich.html":       "日月潭香林田莊主視覺集錦：BMW M Power 風格民宿的房型與空間實景。",
    "album.html":      "日月潭香林田莊相簿：民宿空間、房型、咖啡館、夜景實拍。",
    "privacy.html":    "香林田莊網站隱私權與個資使用政策。",
    "Adtechinno.html": "Adtechinno 廣告技術合作說明頁。",
    "home_cal.html":   "香林田莊訂房月曆：查詢空房日期與訂房洽詢。",
}

PAGE_TITLE_OVERRIDE = {
    "privacy.html": "隱私權政策｜香林田莊",
}

OG_IMAGE_HINT = re.compile(r'<img[^>]*\bsrc="(images/[^"]+)"', re.I)

def detect_eol(data: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in data else b"\n"

def find_first_image(html: str) -> str:
    m = OG_IMAGE_HINT.search(html)
    return f"{BASE_URL}/{m.group(1)}" if m else DEFAULT_OG_IMG

def get_title(html: str, fallback: str) -> str:
    m = re.search(r"<title>([^<]*)</title>", html, re.I)
    return m.group(1).strip() if m else fallback

# ----- Hamburger transforms ----------------------------------------------------

def patch_hamburger(html: str) -> tuple[str, int]:
    changes = 0

    # 1. <button class="hamburger" ... onclick="..." ...>☰</button>
    def hamb_repl(m):
        nonlocal changes
        attrs = m.group(1)
        # strip onclick
        attrs = re.sub(r'\s+onclick\s*=\s*"[^"]*"', "", attrs)
        attrs = re.sub(r"\s+onclick\s*=\s*'[^']*'", "", attrs)
        # ensure required attrs
        if "aria-label" not in attrs:
            attrs += ' aria-label="開啟主選單"'
        if "aria-expanded" not in attrs:
            attrs += ' aria-expanded="false"'
        if "aria-controls" not in attrs:
            attrs += ' aria-controls="navMenu"'
        if "type=" not in attrs:
            attrs += ' type="button"'
        changes += 1
        return f"<button{attrs}>☰</button>"

    html = re.sub(
        r'<button((?=[^>]*class="hamburger")[^>]*)>\s*☰\s*</button>',
        hamb_repl,
        html,
    )

    # 2. <button class="nav-close" ... onclick="...">✕</button>
    def close_repl(m):
        nonlocal changes
        attrs = m.group(1)
        attrs = re.sub(r'\s+onclick\s*=\s*"[^"]*"', "", attrs)
        attrs = re.sub(r"\s+onclick\s*=\s*'[^']*'", "", attrs)
        if "aria-label" not in attrs:
            attrs += ' aria-label="關閉主選單"'
        if "type=" not in attrs:
            attrs += ' type="button"'
        changes += 1
        return f"<button{attrs}>✕</button>"

    html = re.sub(
        r'<button((?=[^>]*class="nav-close")[^>]*)>\s*✕\s*</button>',
        close_repl,
        html,
    )

    # 3. Inject wiring script before </body> (idempotent)
    if "data-nav-wired" not in html and "class=\"hamburger\"" in html:
        script = (
            '\n<script data-nav-wired="1">\n'
            '(function(){\n'
            '  var btn = document.querySelector(".hamburger");\n'
            '  var menu = document.getElementById("navMenu");\n'
            '  if (!btn || !menu) return;\n'
            '  var closeBtn = menu.querySelector(".nav-close");\n'
            '  function setOpen(open){\n'
            '    menu.classList.toggle("open", open);\n'
            '    btn.setAttribute("aria-expanded", open ? "true" : "false");\n'
            '    if (open && closeBtn) closeBtn.focus();\n'
            '    else btn.focus();\n'
            '  }\n'
            '  btn.addEventListener("click", function(){ setOpen(!menu.classList.contains("open")); });\n'
            '  if (closeBtn) closeBtn.addEventListener("click", function(){ setOpen(false); });\n'
            '  document.addEventListener("keydown", function(e){\n'
            '    if (e.key === "Escape" && menu.classList.contains("open")) setOpen(false);\n'
            '  });\n'
            '  menu.addEventListener("click", function(e){\n'
            '    if (e.target === menu) setOpen(false);\n'
            '  });\n'
            '})();\n'
            '</script>\n'
        )
        if "</body>" in html:
            html = html.replace("</body>", script + "</body>", 1)
            changes += 1

    return html, changes

# ----- SEO meta block ---------------------------------------------------------

def build_meta_block(fname: str, title: str, desc: str, canonical: str, og_img: str) -> str:
    # Use spaces for indentation; the raw block is intentionally LF-only;
    # caller normalises EOL before writing.
    lines = [
        f'  <link rel="canonical" href="{canonical}">',
        f'  <meta property="og:type" content="website">',
        f'  <meta property="og:locale" content="zh_TW">',
        f'  <meta property="og:site_name" content="{SITE_NAME}">',
        f'  <meta property="og:title" content="{html_escape(title)}">',
        f'  <meta property="og:description" content="{html_escape(desc)}">',
        f'  <meta property="og:url" content="{canonical}">',
        f'  <meta property="og:image" content="{og_img}">',
        f'  <meta name="twitter:card" content="summary_large_image">',
    ]
    return "\n".join(lines) + "\n"

def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace('"', "&quot;")
             .replace("<", "&lt;").replace(">", "&gt;"))

def patch_meta(html: str, fname: str) -> tuple[str, bool]:
    if "og:title" in html:
        return html, False  # already done (e.g. index.html)

    title = PAGE_TITLE_OVERRIDE.get(fname) or get_title(html, SITE_NAME)
    desc = PAGE_DESC.get(fname) or DEFAULT_DESC
    canonical = f"{BASE_URL}/{fname}" if fname != "index.html" else f"{BASE_URL}/"
    og_img = find_first_image(html)

    block = build_meta_block(fname, title, desc, canonical, og_img)

    # Try to insert after <title>...</title>; otherwise before </head>
    if re.search(r"</title>", html, re.I):
        html = re.sub(r"(</title>)", lambda m: m.group(1) + "\n" + block, html, count=1, flags=re.I)
    elif "</head>" in html:
        html = html.replace("</head>", block + "</head>", 1)
    else:
        return html, False

    # Ensure description meta exists
    if 'name="description"' not in html and 'name=\'description\'' not in html:
        desc_tag = f'  <meta name="description" content="{html_escape(desc)}">\n'
        html = re.sub(r"(</title>)", lambda m: m.group(1) + "\n" + desc_tag, html, count=1, flags=re.I)

    return html, True

# ----- Driver -----------------------------------------------------------------

def normalise_eol(text: str, eol: bytes) -> bytes:
    raw = text.encode("utf-8")
    raw = raw.replace(b"\r\n", b"\n")  # canonical
    if eol == b"\r\n":
        raw = raw.replace(b"\n", b"\r\n")
    return raw

def main():
    total_files = 0
    hamb_changes = 0
    meta_changes = 0
    for fname in sorted(os.listdir(ROOT)):
        if not fname.endswith(".html"):
            continue
        path = os.path.join(ROOT, fname)
        with open(path, "rb") as f:
            data = f.read()
        eol = detect_eol(data)
        text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")

        new_text, ham = patch_hamburger(text)
        new_text, meta_added = patch_meta(new_text, fname)

        if new_text != text:
            with open(path, "wb") as f:
                f.write(normalise_eol(new_text, eol))
            total_files += 1
            hamb_changes += ham
            meta_changes += int(meta_added)
            print(f"  {fname:<22}  hamb-changes={ham}  meta={'+' if meta_added else '-'}")

    print(f"\n{total_files} files updated")
    print(f"  hamburger transforms: {hamb_changes}")
    print(f"  pages with new SEO meta: {meta_changes}")

if __name__ == "__main__":
    main()
