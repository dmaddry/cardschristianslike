#!/usr/bin/env python3
"""Static site generator for cardschristianslike.com — preserves Shopify URL structure."""
import json, os, re, hashlib, html, pathlib, urllib.request, urllib.parse, shutil, datetime

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"
ASSETS = DIST / "assets" / "img"
BASE = "https://cardschristianslike.com"

shutil.rmtree(DIST, ignore_errors=True)
ASSETS.mkdir(parents=True)

products = json.loads((ROOT / "data/products.json").read_text())
articles = []
for b in ["articles_batch1.json", "articles_batch2.json"]:
    d = json.loads((ROOT / "content" / b).read_text())
    for e in d["data"]["blogs"]["edges"][0]["node"]["articles"]["edges"]:
        articles.append(e["node"])
articles.sort(key=lambda a: a["publishedAt"], reverse=True)

# ---------------- image pipeline ----------------
_img_cache = {}
def localize_image(url):
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if url in _img_cache:
        return _img_cache[url]
    if not url.startswith("http"):
        # bare filename -> pre-placed file in content/img-cache
        src = ROOT / "content" / "img-cache" / url
        shutil.copy(src, ASSETS / url)
        local = f"/assets/img/{url}"
        _img_cache[url] = local
        return local
    clean = url.split("?")[0]
    ext = os.path.splitext(clean)[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"):
        ext = ".jpg"
    name = re.sub(r"[^a-z0-9-]", "-", os.path.splitext(os.path.basename(clean))[0].lower())[:60]
    h = hashlib.md5(url.encode()).hexdigest()[:8]
    fname = f"{name}-{h}{ext}"
    cache_dir = ROOT / "content" / "img-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / fname
    dest = ASSETS / fname
    if not cached.exists():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r, open(cached, "wb") as f:
                f.write(r.read())
        except Exception as ex:
            print(f"  !! image failed {url[:90]} -> {ex}")
            _img_cache[url] = url  # keep remote as fallback
            return url
    shutil.copy(cached, dest)
    local = f"/assets/img/{fname}"
    _img_cache[url] = local
    return local

def rewrite_body(body):
    """Rewrite article/page HTML: localize images, fix internal links, drop tracking links."""
    body = re.sub(r"<meta charset=\"utf-8\">", "", body)
    # kill inline <style> blocks (privacy policy junk)
    body = re.sub(r"<style>.*?</style>", "", body, flags=re.S)
    # localize every img src
    def img_sub(m):
        return f'src="{localize_image(m.group(1))}"'
    body = re.sub(r'src="(https?://[^"]+)"', img_sub, body)
    body = re.sub(r'\s+srcset="[^"]*"', "", body)
    # attentive email tracking links -> expansions collection
    body = re.sub(r'href="https://cards-christians-like\.attentivemail\.com/[^"]*"',
                  'href="/collections/expansions-1"', body)
    # absolute internal links -> relative
    body = re.sub(r'href="https?://(?:www\.)?cardschristianslike\.com/?([^"]*)"',
                  lambda m: f'href="/{m.group(1)}"' if m.group(1) else 'href="/"', body)
    # external links: open new tab
    body = re.sub(r'<a href="(http[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    return body

# ---------------- layout ----------------
CSS = """
@font-face{font-family:'Gotham';src:url(/assets/fonts/gotham-book.woff2) format('woff2');font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'Gotham';src:url(/assets/fonts/gotham-book-italic.woff2) format('woff2');font-weight:400;font-style:italic;font-display:swap}
@font-face{font-family:'Gotham';src:url(/assets/fonts/gotham-medium.woff2) format('woff2');font-weight:500 600;font-style:normal;font-display:swap}
@font-face{font-family:'Gotham';src:url(/assets/fonts/gotham-bold.woff2) format('woff2');font-weight:700;font-style:normal;font-display:swap}
@font-face{font-family:'Gotham';src:url(/assets/fonts/gotham-ultra.woff2) format('woff2');font-weight:800 900;font-style:normal;font-display:swap}
:root{--teal:#108474;--teal-d:#0b6154;--blue:#347DEC;--yellow:#fbcd0a;--ink:#131b22;--muted:#5a6672;--cream:#faf7f2;--line:#e8e2d8;--amz:#ff9900}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:'Gotham',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,sans-serif;color:var(--ink);background:#fff;line-height:1.65}
h1,h2,h3,h4{font-family:inherit;font-weight:800;line-height:1.08;letter-spacing:-.02em;margin:0 0 .5em}
h1{font-size:clamp(2.2rem,5vw,3.4rem)}
a{color:var(--teal)}img{max-width:100%;height:auto;border-radius:8px}
.wrap{max-width:1200px;margin:0 auto;padding:0 24px}
header.site{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:50}
header.site .wrap{display:flex;align-items:center;gap:24px;height:84px}
.logo{display:flex;align-items:center;text-decoration:none}
.logo img{height:52px;width:auto;border-radius:0;display:block}
nav.main{margin-left:auto;display:flex;gap:22px;flex-wrap:wrap;align-items:center}
nav.main a{color:var(--ink);text-decoration:none;font-weight:600;font-size:.92rem}
nav.main a:hover{color:var(--teal)}
.btn{display:inline-block;background:#000;color:#fff!important;font-weight:500;font-size:.9rem;text-decoration:none;padding:12px 26px;border-radius:999px;transition:.15s}
.btn:hover{background:#222;transform:scale(1.03)}
.btn .a,.btn.amazon .a{color:var(--amz)}
.hero .btn,.band .btn{background:var(--yellow);color:var(--ink)!important}
.hero .btn:hover,.band .btn:hover{background:#e9be00}
.hero .btn .a,.band .btn .a{color:var(--ink)}
.hero{background:#000;color:#fff;text-align:center;padding:84px 20px 92px}
.hero h1{font-size:clamp(2rem,5vw,3.3rem);max-width:820px;margin:0 auto .35em}
.hero p.tag{font-size:clamp(1.05rem,2.2vw,1.35rem);opacity:.92;margin:0 auto 1.6em;max-width:640px}
.hero .note{margin-top:18px;font-size:.9rem;opacity:.85}
.pill{display:inline-block;background:var(--yellow);color:var(--ink);font-weight:700;font-size:.8rem;letter-spacing:.06em;text-transform:uppercase;padding:6px 14px;border-radius:6px;margin-bottom:22px}
section{padding:64px 0}
.grid{display:grid;gap:36px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.grid .tile img{aspect-ratio:1/1}
.split{display:grid;gap:48px;grid-template-columns:1fr 1fr;align-items:center}
@media(max-width:760px){.split{grid-template-columns:1fr}}
.product-hero{padding:72px 0}
.price{font-weight:700;color:var(--ink);font-size:1.15rem;margin:6px 0 18px}
.retired-note{background:var(--yellow);border-radius:6px;padding:14px 18px;font-size:.92rem;margin:18px 0}
.prose{max-width:760px}
.prose img{margin:18px 0}
.prose h2{margin-top:1.6em;font-size:1.8rem}.prose h3{margin-top:1.4em;font-size:1.3rem}
.prose table{border-collapse:collapse;width:100%;font-size:.92rem}.prose td,.prose th{border:1px solid var(--line);padding:8px 10px;text-align:left}
.meta{color:var(--ink);font-size:.9rem;margin-bottom:26px}
.page-lead{max-width:640px;font-size:1.1rem}
.post-cta{margin-top:50px;padding:36px;background:var(--yellow);border-radius:6px;max-width:760px}
.post-cta h3{font-size:1.5rem}
.band{background:var(--ink);color:#fff;text-align:center;padding:70px 20px}
.band h2{color:#fff}
footer.site{background:#000;border-top:1px solid rgba(255,255,255,.2);padding:64px 0;font-size:.9rem;color:rgba(255,255,255,.65)}
footer.site .cols{display:flex;flex-wrap:wrap;gap:40px;justify-content:space-between}
footer.site a{color:rgba(255,255,255,.65);text-decoration:none;display:block;margin-bottom:8px}
footer.site a:hover{color:var(--yellow)}
footer.site h4{font-size:.85rem;text-transform:uppercase;letter-spacing:.08em;color:#fff}
.crumbs{font-size:.85rem;color:var(--ink);padding-top:26px}
.crumbs a{color:var(--ink)}
.blog-list .tile img{aspect-ratio:16/9}
.blog-list .tile h3{font-size:1.25rem}
/* ---- homepage (CAH-style layout, CCL colors) ---- */
.home-hero{background:#fff;color:var(--ink);padding:84px 0 150px}
.home-hero h1{font-size:clamp(2.8rem,8vw,5.6rem);max-width:1000px;margin:0 0 .3em}
.home-hero h1 em{font-style:normal;box-shadow:inset 0 -0.28em var(--yellow)}
.home-hero p.tag{font-size:clamp(1.15rem,2.4vw,1.55rem);color:var(--ink);margin:0 0 2em;max-width:680px}
.home-hero .note{margin-top:22px;font-size:.95rem;color:var(--ink)}
.home-h2{font-size:clamp(2.3rem,5vw,3.6rem)}
.play{background:#000;color:#fff;height:340vh;position:relative}
.play-sticky{position:sticky;top:0;min-height:100vh;display:flex;align-items:center;overflow:hidden}
.play-sticky>.wrap{width:100%}
.play .split{align-items:center}
.play p.big{font-size:clamp(1.15rem,2vw,1.4rem);max-width:520px}
.play-cards{display:flex;gap:26px;justify-content:center;align-items:flex-start;flex-wrap:wrap}
.pcard{width:225px;aspect-ratio:5/7;border-radius:16px;padding:22px 20px;font-weight:700;font-size:1.02rem;line-height:1.35;display:flex;flex-direction:column;justify-content:space-between}
.pcard .brand{font-size:.62rem;font-weight:800;letter-spacing:.02em;text-align:center}
.pcard.prompt{background:var(--blue);color:#fff;transform:rotate(-6deg)}
.pcard.answer{background:#fff;color:var(--blue)}
.answer-stack{position:relative;width:225px;aspect-ratio:5/7;transform:rotate(3deg) translateY(16px)}
.answer-stack .pcard{position:absolute;inset:0;opacity:0;transform:rotate(75deg);transform-origin:50% 90%;will-change:transform,opacity}
.answer-stack .pcard:first-child{transform:none;opacity:1}
.buy-block{padding:110px 0}
.buy-block .split{align-items:center}
.buy-block img{border:1px solid var(--line);border-radius:8px}
.buy-block .price{font-size:1.3rem;color:var(--ink)}
.buy-block p{font-size:1.1rem}
.games-block{background:var(--yellow);padding:110px 0}
.games-block p.lead{max-width:640px;font-size:1.15rem}
.tiles{display:grid;gap:36px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin-top:48px}
.tile{display:block;text-decoration:none;color:var(--ink)}
.tile img{border-radius:14px;aspect-ratio:1/1;object-fit:cover;width:100%;transition:transform .15s}
.tile:hover img{transform:scale(1.03)}
.tile h3{font-size:clamp(1.3rem,2vw,1.7rem);margin:18px 0 6px}
.tile p{margin:0;font-size:.95rem}
.faq{background:#000;color:#fff;padding:110px 0}
.faq .inner{max-width:none}
.faq .home-h2{font-size:clamp(2.4rem,5.5vw,3.6rem);margin-bottom:.7em}
.faq details{border-bottom:1px solid rgba(255,255,255,.5)}
.faq details:first-of-type{border-top:1px solid rgba(255,255,255,.5)}
.faq summary{cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:16px;padding:19px 0;font-weight:700;font-size:clamp(1.1rem,2vw,1.45rem)}
.faq summary::-webkit-details-marker{display:none}
.faq summary:after{content:"+";font-size:1.8rem;font-weight:400;color:#fff;flex-shrink:0;line-height:1}
.faq details[open] summary:after{content:"\\2212"}
.faq .a-body{padding:0 0 26px;color:rgba(255,255,255,.75);max-width:680px}
.faq .a-body a{font-weight:600;color:var(--yellow)}
@media(max-width:760px){header.site .wrap{height:64px}.logo img{height:38px}.home-hero{padding:70px 0 64px}.play-cards{gap:18px}.pcard{width:150px;border-radius:12px;padding:14px;font-size:.74rem;line-height:1.3}.pcard .brand{font-size:.46rem}.answer-stack{width:150px}}
"""

def page(title, desc, path, body, jsonld=None, ogimg=None):
    canonical = BASE + (path if path != "/index" else "/")
    canonical = canonical.replace(".html", "")
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    og = f'<meta property="og:image" content="{ogimg}">' if ogimg else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">{og}
<link rel="icon" href="/assets/img/favicon.png">
<link rel="preload" href="/assets/fonts/gotham-book.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/gotham-ultra.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
{ld}
</head>
<body>
<header class="site"><div class="wrap">
<a class="logo" href="/"><img src="/assets/img/christians-like-logo.png" alt="Christians Like – home"></a>
<nav class="main">
<a href="/collections/games">Shop</a>
<a class="btn amazon" href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Buy on <span class="a">Amazon</span> &rarr;</a>
</nav>
</div></header>
{body}
<footer class="site"><div class="wrap">
<div class="cols">
<div style="max-width:300px">
<h4>Cards Christians Like</h4>
<p>It's a party game but with convictions. Made by Christians Like, LLC.</p>
<p><a href="mailto:hello@cardschristianslike.com">hello@cardschristianslike.com</a></p>
</div>
<div><h4>Shop</h4>
<a href="/products/cards-christians-like">Cards Christians Like</a>
<a href="/products/discernment">Discernment</a>
<a href="/products/holy-guacamole">Holy Guacamole</a>
<a href="/products/cast-the-first-stone">Cast The First Stone</a>
</div>
<div><h4>Company</h4>
<a href="/blogs/news">Blog</a>
<a href="/pages/privacy-policy">Privacy Policy</a>
<a href="/pages/terms-of-service">Terms of Service</a>
<a href="/pages/return-and-refund-policy">Returns &amp; Refunds</a>
</div>
<div><h4>Follow</h4>
<a href="https://www.instagram.com/cardschristianslike" target="_blank" rel="noopener">Instagram</a>
<a href="https://www.tiktok.com/@cardschristianslike" target="_blank" rel="noopener">TikTok</a>
<a href="https://www.facebook.com/cardschristianslike" target="_blank" rel="noopener">Facebook</a>
</div>
</div>
<p style="margin-top:34px">&copy; {datetime.date.today().year} Christians Like, LLC. All rights reserved. All games ship fast via <a href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Amazon</a>.</p>
</div></footer>
</body></html>"""

def write(path, content):
    p = DIST / path.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    print("  +", path)

# favicon
fav = localize_image("https://cardschristianslike.com/cdn/shop/files/Icon-Color-Transparent.png?height=180&v=1614315978&width=180")
if fav.startswith("/assets"):
    shutil.copy(DIST / fav.lstrip("/"), ASSETS / "favicon.png")
else:
    print("  !! favicon fallback")

# header brand logo (local asset, not from Shopify)
shutil.copy(ROOT / "content/img-cache/christians-like-logo.png", ASSETS / "christians-like-logo.png")

# self-hosted brand fonts
FONTS = DIST / "assets" / "fonts"
FONTS.mkdir(parents=True, exist_ok=True)
for f in (ROOT / "content/fonts").glob("*.woff2"):
    shutil.copy(f, FONTS / f.name)

sitemap_urls = []

# ---------------- product pages ----------------
by_handle = {p["handle"]: p for p in products}
for p in products:
    img = localize_image(p["image"])
    label = p.get("amazonLabel", "Buy on Amazon").replace("Amazon", '<span class="a">Amazon</span>')
    retired = f'<div class="retired-note"><strong>Heads up:</strong> the print-at-home edition has been retired. The full boxed game is available on Amazon with fast Prime shipping.</div>' if p.get("retired") else ""
    ld = {
        "@context": "https://schema.org", "@type": "Product",
        "name": p["title"], "image": BASE + img if img.startswith("/") else img,
        "description": re.sub("<[^>]+>", " ", p["descriptionHtml"]).strip()[:300],
        "brand": {"@type": "Brand", "name": "Cards Christians Like"},
        "offers": {"@type": "Offer", "url": p["amazon"], "priceCurrency": "USD",
                   "price": p["price"], "availability": "https://schema.org/InStock"}
    }
    body = f"""
<div class="wrap crumbs"><a href="/">Home</a> / <a href="/collections/games">Games</a> / {html.escape(p['title'])}</div>
<div class="wrap product-hero"><div class="split">
<div><img src="{img}" alt="{html.escape(p['title'])} – Christian party game"></div>
<div>
<h1>{html.escape(p['title'])}</h1>
<p class="price">${p['price']} &middot; Sold on Amazon</p>
{retired}
<div class="prose">{p['descriptionHtml']}</div>
<p style="margin-top:26px"><a class="btn amazon" href="{p['amazon']}" target="_blank" rel="noopener">{label} &rarr;</a></p>
<p style="font-size:.85rem">Fast shipping &middot; Easy returns &middot; Sold by Christians Like, LLC on Amazon</p>
</div>
</div></div>
"""
    path = f"/products/{p['handle']}"
    desc = p.get("seoDescription") or p["blurb"]
    write(path + ".html", page(p.get("seoTitle") or p["title"], desc, path, body, ld, ogimg=BASE + img if img.startswith("/") else img))
    sitemap_urls.append(path)

# ---------------- collections ----------------
collections = [
    ("games", "Games", "Christian Card Games For Family Fun",
     "Every game we make — hilarious, faith-filled card games for families, youth groups, and game nights.", ["cards-christians-like", "expansion-box-vol-1", "cast-the-first-stone", "holy-guacamole", "discernment"]),
    ("expansions-1", "Expansions", "Christian Card Game Expansions For Family Fun",
     "Expansions for Cards Christians Like — hundreds of new cards to keep game night fresh.", ["expansion-box-vol-1", "ccl-expansion-bundle", "all-expansions-print-at-home", "print-at-home-new-expansions"]),
    ("print-at-home", "Print at Home", "Printable Christian Card Games For Church Groups",
     "Our retired print-at-home editions — every game is now available as a full boxed set on Amazon.", ["cards-christians-like-print-at-home", "copy-of-print-at-home-cards-christians-like", "all-expansions-print-at-home", "print-at-home-new-expansions"]),
    ("holy-guacamole-bundle", "Holy Guacamole Expansions", "Holy Guacamole Expansions",
     "Holy Guacamole and its expansions — the hilarious guessing game for Christian families.", ["holy-guacamole"]),
]
for handle, title, seo, desc, members in collections:
    cards = ""
    for h in members:
        p = by_handle[h]
        img = localize_image(p["image"])
        cards += f"""<a class="tile" href="/products/{h}"><img src="{img}" alt="{html.escape(p['title'])}" loading="lazy"><h3>{html.escape(p['title'])}</h3><p>{html.escape(p['blurb'])}</p></a>"""
    body = f"""
<div class="wrap crumbs"><a href="/">Home</a> / {title}</div>
<section class="wrap" style="padding-top:28px"><h1>{title}</h1><p class="page-lead">{desc}</p>
<div class="grid" style="margin-top:34px">{cards}</div>
<p style="margin-top:40px"><a class="btn amazon" href="https://www.amazon.com/s?k=cards+christians+like" target="_blank" rel="noopener">See everything on <span class="a">Amazon</span> &rarr;</a></p>
</section>"""
    path = f"/collections/{handle}"
    write(path + ".html", page(seo, desc, path, body))
    sitemap_urls.append(path)

# ---------------- blog ----------------
cards = ""
for a in articles:
    img = localize_image(a["image"]["url"]) if a.get("image") else None
    imgtag = f'<img src="{img}" alt="{html.escape(a["title"])}" loading="lazy">' if img else ""
    d = a["publishedAt"][:10]
    summary = a.get("summary") or ""
    cards += f"""<a class="tile" href="/blogs/news/{a['handle']}">{imgtag}<h3>{html.escape(a['title'])}</h3><p>{html.escape(summary[:140])}</p></a>"""
body = f"""
<div class="wrap crumbs"><a href="/">Home</a> / Blog</div>
<section class="wrap blog-list" style="padding-top:28px"><h1>News &amp; Ideas</h1>
<p class="page-lead">Game night ideas, Christian party game guides, and updates from the Cards Christians Like team.</p>
<div class="grid" style="margin-top:34px">{cards}</div></section>"""
write("/blogs/news.html", page("News & Game Night Ideas – Cards Christians Like",
      "Christian party game guides, game night ideas, and company updates from Cards Christians Like.", "/blogs/news", body))
sitemap_urls.append("/blogs/news")

for a in articles:
    bodyhtml = rewrite_body(a["body"])
    img = localize_image(a["image"]["url"]) if a.get("image") else None
    imgtag = f'<img src="{img}" alt="{html.escape(a["title"])}" style="margin-bottom:28px">' if img else ""
    d = a["publishedAt"][:10]
    desc = (a.get("summary") or re.sub("<[^>]+>", " ", a["body"])[:155].strip())
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": a["title"],
          "datePublished": a["publishedAt"], "author": {"@type": "Organization", "name": "Cards Christians Like"},
          "publisher": {"@type": "Organization", "name": "Christians Like, LLC"},
          "mainEntityOfPage": f"{BASE}/blogs/news/{a['handle']}"}
    if img:
        ld["image"] = BASE + img
    body = f"""
<div class="wrap crumbs"><a href="/">Home</a> / <a href="/blogs/news">Blog</a> / {html.escape(a['title'][:60])}</div>
<article class="wrap" style="padding:28px 20px 70px">
<h1 style="max-width:820px">{html.escape(a['title'])}</h1>
<p class="meta">Published {d} &middot; Cards Christians Like</p>
{imgtag}
<div class="prose">{bodyhtml}</div>
<div class="post-cta">
<h3>Ready for game night?</h3>
<p>Cards Christians Like, Holy Guacamole, Discernment, and Cast The First Stone are all available on Amazon with fast shipping.</p>
<a class="btn amazon" href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Shop our games on <span class="a">Amazon</span> &rarr;</a>
</div>
</article>"""
    path = f"/blogs/news/{a['handle']}"
    write(path + ".html", page(a["title"] + " – Cards Christians Like", desc[:160], path, body, ld, ogimg=(BASE + img) if img else None))
    sitemap_urls.append(path)

# ---------------- policy pages ----------------
for fname in ["privacy-policy", "terms-of-service", "return-and-refund-policy"]:
    raw = (ROOT / f"content/pages/{fname}.html").read_text()
    bodyhtml = rewrite_body(raw)
    title = {"privacy-policy": "Privacy Policy", "terms-of-service": "Terms of Service",
             "return-and-refund-policy": "Return and Refund Policy"}[fname]
    body = f"""<div class="wrap crumbs"><a href="/">Home</a> / {title}</div>
<article class="wrap" style="padding:28px 20px 70px"><h1>{title}</h1><div class="prose">{bodyhtml}</div></article>"""
    path = f"/pages/{fname}"
    write(path + ".html", page(f"{title} – Cards Christians Like", f"{title} for Christians Like, LLC.", path, body))
    sitemap_urls.append(path)

# ---------------- homepage ----------------
other_games = ["discernment", "holy-guacamole", "cast-the-first-stone"]
tiles = ""
for h in other_games:
    p = by_handle[h]
    img = localize_image(p["image"])
    tiles += f"""<a class="tile" href="/products/{h}"><img src="{img}" alt="{html.escape(p['title'])} Christian party game" loading="lazy"><h3>{html.escape(p['title'])}</h3><p>{html.escape(p['blurb'])}</p></a>"""
main_game = by_handle["cards-christians-like"]
main_img = localize_image(main_game["image"])
ld = [{"@context": "https://schema.org", "@type": "Organization", "name": "Cards Christians Like",
       "legalName": "Christians Like, LLC", "url": BASE, "logo": BASE + "/assets/img/favicon.png",
       "email": "hello@cardschristianslike.com",
       "sameAs": ["https://www.instagram.com/cardschristianslike", "https://www.tiktok.com/@cardschristianslike",
                   "https://www.facebook.com/cardschristianslike", "https://www.amazon.com/dp/B0BBSGRR5X"]},
      {"@context": "https://schema.org", "@type": "WebSite", "name": "Cards Christians Like", "url": BASE}]
body = f"""
<div class="home-hero"><div class="wrap">
<h1>It's a party game, but with <em>convictions</em>.</h1>
<p class="tag">The original Christian party game — hundreds of hilarious combinations about church, culture, and the Bible.</p>
<a class="btn amazon" href="{main_game['amazon']}" target="_blank" rel="noopener">Buy on <span class="a">Amazon</span> &rarr;</a>
<p class="note">Our store moved to Amazon for better prices and faster shipping.</p>
</div></div>
<section class="play" id="play-scroll"><div class="play-sticky"><div class="wrap"><div class="split">
<div>
<h2 class="home-h2">The game is simple.</h2>
<p class="big">Each round, one player reads a prompt card. Everyone else plays the funniest response card they've got. Best answer wins the round — and probably derails the Bible study.</p>
</div>
<div class="play-cards" aria-label="Example cards from the game">
<div class="pcard prompt"><span>If ____________ is wrong then I don't want to be right.</span><span class="brand">Cards Christians Like</span></div>
<div class="answer-stack">
<div class="pcard answer"><span>Sending memes during church.</span><span class="brand">Cards Christians Like</span></div>
<div class="pcard answer"><span>Jesus's temple whip.</span><span class="brand">Cards Christians Like</span></div>
<div class="pcard answer"><span>Live animals on stage during Christmas.</span><span class="brand">Cards Christians Like</span></div>
</div>
</div>
</div></div></div></section>
<script>
(function(){{
var sec=document.getElementById('play-scroll');
if(!sec)return;
var cards=[].slice.call(sec.querySelectorAll('.answer-stack .pcard'));
if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
function ease(t){{return t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2}}
var ticking=false;
function update(){{
ticking=false;
var r=sec.getBoundingClientRect();
var total=r.height-innerHeight;
var p=Math.min(1,Math.max(0,-r.top/(total||1)));
var n=cards.length;
cards.forEach(function(c,i){{
var t=Math.min(1,Math.max(0,p*n-i));
var rot=75,o=0;
if(t<=0){{rot=75;o=0}}
else if(t<.4){{var e=ease(t/.4);rot=(1-e)*75;o=e}}
else if(t<.6||i===n-1){{rot=0;o=1}}
else{{var e2=ease((t-.6)/.4);rot=-e2*75;o=1-e2}}
c.style.transform='rotate('+rot+'deg)';
c.style.opacity=o;
}});
}}
function onScroll(){{if(!ticking){{ticking=true;requestAnimationFrame(update)}}}}
addEventListener('scroll',onScroll,{{passive:true}});
addEventListener('resize',onScroll);
update();
}})();
</script>
<section class="buy-block"><div class="wrap">
<div class="split">
<div><img src="{main_img}" alt="Cards Christians Like – the original Christian party game" loading="lazy"></div>
<div>
<h2 class="home-h2">Buy the game.</h2>
<p style="max-width:500px">{html.escape(main_game['blurb'])} Perfect for church groups, families, youth groups, and game nights.</p>
<p class="price">${main_game['price']} on Amazon</p>
<a class="btn amazon" href="{main_game['amazon']}" target="_blank" rel="noopener">Buy on <span class="a">Amazon</span> &rarr;</a>
</div>
</div>
</div></section>
<section class="games-block" id="games"><div class="wrap">
<h2 class="home-h2">More games. More laughs.</h2>
<p class="lead">Three more hilarious, faith-filled games — every one ships fast from Amazon.</p>
<div class="tiles">{tiles}</div>
</div></section>
<section class="faq"><div class="wrap"><div class="inner">
<h2 class="home-h2">Your holy questions.</h2>
<details><summary>Where do I buy Cards Christians Like?</summary><div class="a-body"><p>On <a href="{main_game['amazon']}" target="_blank" rel="noopener">Amazon</a>. Every game we make is there, with Prime shipping and easy returns.</p></div></details>
<details><summary>How do you play?</summary><div class="a-body"><p>One player reads a prompt card, everyone else answers with their funniest response card. Funniest answer wins the round. That's the whole rulebook, more or less.</p></div></details>
<details><summary>Do you sell expansions?</summary><div class="a-body"><p>We have — though availability on Amazon comes and goes. The reliable move is one of our <a href="/collections/games">three other standalone games</a>, or check <a href="https://www.amazon.com/s?k=cards+christians+like" target="_blank" rel="noopener">everything currently shipping on Amazon</a>.</p></div></details>
<details><summary>Does it work for church groups and family night?</summary><div class="a-body"><p>That's exactly who it's for. It's written for church groups, families, and youth groups — punchy enough to be funny, clean enough that your grandma stays in the room.</p></div></details>
<details><summary>What happened to the old store?</summary><div class="a-body"><p>We moved everything to Amazon for better prices, faster shipping, and easier returns. Same games, same humor, same convictions.</p></div></details>
</div></div></section>
"""
write("/index.html", page("Cards Christians Like – It's a party game but with convictions.",
      "The original Christian party game. Hundreds of hilarious combinations that capitalize on Christian culture and the Bible. Now available on Amazon.", "/index", body, ld))
sitemap_urls.insert(0, "/")

# ---------------- 404 ----------------
body = """<section class="wrap" style="text-align:center;padding:110px 20px">
<h1>Well, this page hath passed away.</h1>
<p>The page you're looking for isn't here — but the games definitely are.</p>
<p style="margin-top:24px"><a class="btn" href="/">Back to home</a>&nbsp;&nbsp;<a class="btn amazon" href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Buy on <span class="a">Amazon</span> &rarr;</a></p></section>"""
write("/404.html", page("Page not found – Cards Christians Like", "Page not found.", "/404", body))

# ---------------- sitemap + robots ----------------
today = datetime.date.today().isoformat()
urls = "\n".join(f"<url><loc>{BASE}{u if u != '/' else ''}{'/' if u == '/' else ''}</loc><lastmod>{today}</lastmod></url>" for u in sitemap_urls)
write("/sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>')
write("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")

# ---------------- vercel.json ----------------
redirects = [
    # deleted products that still have backlinks -> closest live page
    {"source": "/products/trash-theology-expansion-pack", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/gen-z-expansion-pack", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/jesus-loves-you-expansion-pack", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/pop-culture-expansion-pack", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/worship-expansion-pack", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/cards-christians-hide-expansion-pack", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/dating-expansion-pack", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/your-other-cards-storage-box-1", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/ccl-expansion-box-vol-1", "destination": "/products/expansion-box-vol-1", "permanent": True},
    {"source": "/products/shipping-protection", "destination": "/", "permanent": True},
    # retired collections
    {"source": "/collections/special", "destination": "/collections/games", "permanent": True},
    {"source": "/collections/holiday-bundles-:rest*", "destination": "/collections/games", "permanent": True},
    {"source": "/collections/all", "destination": "/collections/games", "permanent": True},
    # shopify system paths
    {"source": "/password", "destination": "/", "permanent": True},
    {"source": "/cart", "destination": "/", "permanent": True},
    {"source": "/account/:rest*", "destination": "/", "permanent": True},
    {"source": "/search", "destination": "/", "permanent": True},
    {"source": "/collections", "destination": "/collections/games", "permanent": True},
    {"source": "/blogs", "destination": "/blogs/news", "permanent": True},
    {"source": "/pages/collabs", "destination": "/", "permanent": True},
    {"source": "/collabs", "destination": "/", "permanent": True},
    # influencer discount shortlinks -> amazon base listing (discount codes no longer exist)
    {"source": "/discount/:code*", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/blakealexiss", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/stickemup", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/ng0charlie", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/heavenlyminded", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/setupedia", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/ksenia", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/pauldal", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
    {"source": "/teresitaroses", "destination": "https://www.amazon.com/dp/B0BBSGRR5X", "permanent": False},
]
vercel = {"cleanUrls": True, "trailingSlash": False, "redirects": redirects,
          "headers": [{"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]}]}
(DIST / "vercel.json").write_text(json.dumps(vercel, indent=2))
print("  + /vercel.json")
print(f"\nDone. {len(sitemap_urls)} pages, {len(list(ASSETS.iterdir()))} images.")
