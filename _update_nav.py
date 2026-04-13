#!/usr/bin/env python3
import re, os

NAV_NEW = '''<nav class="nav-links">
        <button class="hamburger" onclick="document.getElementById('navMenu').classList.toggle('open');">☰</button>
        <a class="btn btn-primary" href="tel:0905595617">立即訂房</a>
      </nav>'''

OVERLAY = '''
<div class="nav-overlay" id="navMenu">
  <button class="nav-close" onclick="document.getElementById('navMenu').classList.remove('open');">✕</button>
  <a href="index.html">首頁</a>
  <a href="about_us.html">關於我們</a>
  <a href="news.html">最新消息</a>
  <a href="house.html">房型介紹</a>
  <a href="mpower.html">咖啡館</a>
  <a href="share.html">民宿景點</a>
  <a href="nature.html">賞螢火蟲</a>
  <a href="shop.html">M禮品店</a>
  <a href="fish.html">釣魚船屋</a>
  <a href="https://www.facebook.com/%E6%97%A5%E6%9C%88%E6%BD%AD%E9%A6%99%E6%9E%97%E7%94%B0%E8%8E%8A-2072650812978160/">FB訂房</a>
  <hr>
  <a href="https://www.sunmoonlake.gov.tw/index.aspx#1">日月潭</a>
  <a href="http://www.nine.com.tw/">九族文化村</a>
  <a href="https://kumar.tw/b/">南投妖怪村</a>
  <a href="https://www.cingjing.gov.tw/">清境農場</a>
  <hr>
  <a href="https://www.google.com/maps/place/%E9%A6%99%E6%9E%97%E7%94%B0%E8%8E%8A%E6%B0%91%E5%AE%BF/@23.8354373,120.8998759,18.16z/data=!4m5!3m4!1s0x0:0x8d3e4e169d31cfa7!8m2!3d23.8352299!4d120.8998589">馬上導航</a>
</div>'''

HAMBURGER_CSS = '''
    .hamburger {
      background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #fff;
      font-size: 1.5rem; width: 48px; height: 48px; border-radius: 14px; cursor: pointer;
      display: grid; place-items: center; backdrop-filter: blur(8px);
    }
    .nav-overlay {
      display: none; position: fixed; inset: 0; z-index: 200;
      background: rgba(7,9,14,0.96); backdrop-filter: blur(20px);
      flex-direction: column; align-items: center; justify-content: center; gap: 16px;
      padding: 40px;
    }
    .nav-overlay.open { display: flex; }
    .nav-overlay a {
      color: #d8e4ef; font-size: 1.2rem; font-weight: 500; padding: 10px 20px;
      border-radius: 14px; transition: background 0.2s; text-decoration: none;
    }
    .nav-overlay a:hover { background: rgba(255,255,255,0.08); color: #fff; }
    .nav-overlay hr { width: 60px; border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 8px 0; }
    .nav-close {
      position: absolute; top: 24px; right: 24px; background: none; border: none;
      color: #fff; font-size: 1.8rem; cursor: pointer;
    }'''

# For the 4 already-styled files
for fname in ['index.html', 'house.html', 'about_us.html', 'shop.html']:
    path = os.path.join(os.path.dirname(__file__), fname)
    with open(path, 'r') as f:
        html = f.read()
    
    # Replace nav-links section (multiline or single line)
    html = re.sub(r'<nav class="nav-links">.*?</nav>', NAV_NEW, html, flags=re.DOTALL)
    
    # Add overlay after </header>
    if 'nav-overlay' not in html:
        html = html.replace('</header>', '</header>' + OVERLAY)
    
    # Add hamburger CSS before </style> (first occurrence)
    if '.hamburger' not in html:
        html = html.replace('</style>', HAMBURGER_CSS + '\n  </style>', 1)
    
    # Remove old dropdown CSS if present
    # (keep it, it won't hurt)
    
    with open(path, 'w') as f:
        f.write(html)
    print(f"Updated {fname}")

print("Done with styled files")
