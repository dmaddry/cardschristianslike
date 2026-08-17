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
:root{--teal:#108474;--teal-d:#0b6154;--blue:#347DEC;--yellow:#fbcd0a;--ink:#131b22;--muted:#5a6672;--cream:#faf7f2;--line:#e8e2d8;--amz:#ff9900}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:'Open Sans',system-ui,sans-serif;color:var(--ink);background:var(--cream);line-height:1.65}
h1,h2,h3,h4{font-family:'Montserrat',sans-serif;font-weight:800;line-height:1.2;margin:0 0 .5em}
a{color:var(--teal)}img{max-width:100%;height:auto;border-radius:12px}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.site{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:50}
header.site .wrap{display:flex;align-items:center;gap:24px;height:64px}
.logo{font-family:'Montserrat',sans-serif;font-weight:800;font-size:1.05rem;color:var(--ink);text-decoration:none;display:flex;align-items:center;gap:10px}
.logo img{width:32px;height:32px;border-radius:6px}
nav.main{margin-left:auto;display:flex;gap:20px;flex-wrap:wrap}
nav.main a{color:var(--ink);text-decoration:none;font-weight:600;font-size:.92rem}
nav.main a:hover{color:var(--teal)}
.btn{display:inline-block;background:var(--teal);color:#fff!important;font-family:'Montserrat',sans-serif;font-weight:700;text-decoration:none;padding:13px 26px;border-radius:999px;transition:.15s}
.btn:hover{background:var(--teal-d)}
.btn.amazon{background:var(--ink)}
.btn.amazon:hover{background:#000}
.btn.amazon .a{color:var(--amz)}
.hero{background:linear-gradient(135deg,var(--teal) 0%,#0d6e61 60%,#0b5d52 100%);color:#fff;text-align:center;padding:84px 20px 92px}
.hero h1{font-size:clamp(2rem,5vw,3.3rem);max-width:820px;margin:0 auto .35em}
.hero p.tag{font-size:clamp(1.05rem,2.2vw,1.35rem);opacity:.92;margin:0 auto 1.6em;max-width:640px}
.hero .note{margin-top:18px;font-size:.9rem;opacity:.85}
.pill{display:inline-block;background:var(--yellow);color:var(--ink);font-family:'Montserrat',sans-serif;font-weight:700;font-size:.8rem;letter-spacing:.06em;text-transform:uppercase;padding:6px 14px;border-radius:999px;margin-bottom:22px}
section{padding:64px 0}
.grid{display:grid;gap:28px;grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;transition:.15s;text-decoration:none;color:var(--ink)}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 24px rgba(16,132,116,.13)}
.card img{border-radius:0;aspect-ratio:1/1;object-fit:cover;width:100%}
.card .pad{padding:18px 18px 22px;display:flex;flex-direction:column;gap:8px;flex:1}
.card h3{font-size:1.05rem;margin:0}
.card p{margin:0;font-size:.88rem;color:var(--muted);flex:1}
.card .cta{font-weight:700;color:var(--teal);font-size:.9rem}
.split{display:grid;gap:48px;grid-template-columns:1fr 1fr;align-items:center}
@media(max-width:760px){.split{grid-template-columns:1fr}}
.product-hero{padding:56px 0}
.price{font-family:'Montserrat',sans-serif;font-weight:700;color:var(--muted);margin:6px 0 18px}
.retired-note{background:#fff8e1;border:1px solid #f0dd9a;border-radius:12px;padding:14px 18px;font-size:.92rem;margin:18px 0}
.prose{max-width:760px}
.prose img{margin:18px 0}
.prose h2{margin-top:1.6em;font-size:1.5rem}.prose h3{margin-top:1.4em;font-size:1.2rem}
.prose table{border-collapse:collapse;width:100%;font-size:.92rem}.prose td,.prose th{border:1px solid var(--line);padding:8px 10px;text-align:left}
.meta{color:var(--muted);font-size:.9rem;margin-bottom:26px}
.band{background:var(--ink);color:#fff;text-align:center;padding:70px 20px}
.band h2{color:#fff}
footer.site{background:#fff;border-top:1px solid var(--line);padding:44px 0;font-size:.9rem;color:var(--muted)}
footer.site .cols{display:flex;flex-wrap:wrap;gap:40px;justify-content:space-between}
footer.site a{color:var(--muted);text-decoration:none;display:block;margin-bottom:8px}
footer.site a:hover{color:var(--teal)}
footer.site h4{font-size:.85rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink)}
.crumbs{font-size:.85rem;color:var(--muted);padding-top:26px}
.crumbs a{color:var(--muted)}
.blog-list .card img{aspect-ratio:16/9}
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
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800&family=Open+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>{CSS}</style>
{ld}
</head>
<body>
<header class="site"><div class="wrap">
<a class="logo" href="/"><img src="/assets/img/favicon.png" alt="Cards Christians Like logo">Cards Christians Like</a>
<nav class="main">
<a href="/collections/games">Games</a>
<a href="/collections/expansions-1">Expansions</a>
<a href="/blogs/news">Blog</a>
<a class="btn amazon" style="padding:9px 18px;font-size:.85rem" href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Shop on <span class="a">Amazon</span></a>
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
<a href="/products/expansion-box-vol-1">Expansion Box Vol. 1</a>
<a href="/products/cast-the-first-stone">Cast The First Stone</a>
<a href="/products/holy-guacamole">Holy Guacamole</a>
<a href="/products/discernment">Discernment</a>
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

sitemap_urls = []

# ---------------- product pages ----------------
by_handle = {p["handle"]: p for p in products}
for p in products:
    img = localize_image(p["image"])
    label = p.get("amazonLabel", "Buy on Amazon")
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
<p style="font-size:.85rem;color:var(--muted)">Fast shipping &middot; Easy returns &middot; Sold by Christians Like, LLC on Amazon</p>
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
        cards += f"""<a class="card" href="/products/{h}"><img src="{img}" alt="{html.escape(p['title'])}" loading="lazy"><div class="pad"><h3>{html.escape(p['title'])}</h3><p>{html.escape(p['blurb'])}</p><span class="cta">View game &rarr;</span></div></a>"""
    body = f"""
<div class="wrap crumbs"><a href="/">Home</a> / {title}</div>
<section class="wrap" style="padding-top:28px"><h1>{title}</h1><p style="max-width:640px;color:var(--muted)">{desc}</p>
<div class="grid" style="margin-top:34px">{cards}</div>
<p style="margin-top:40px"><a class="btn amazon" href="https://www.amazon.com/s?k=cards+christians+like" target="_blank" rel="noopener">See everything on Amazon &rarr;</a></p>
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
    cards += f"""<a class="card" href="/blogs/news/{a['handle']}">{imgtag}<div class="pad"><h3>{html.escape(a['title'])}</h3><p>{html.escape(summary[:140])}</p><span class="cta">Read more &rarr;</span></div></a>"""
body = f"""
<div class="wrap crumbs"><a href="/">Home</a> / Blog</div>
<section class="wrap blog-list" style="padding-top:28px"><h1>News &amp; Ideas</h1>
<p style="max-width:640px;color:var(--muted)">Game night ideas, Christian party game guides, and updates from the Cards Christians Like team.</p>
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
<div style="margin-top:50px;padding:30px;background:#fff;border:1px solid var(--line);border-radius:16px;max-width:760px">
<h3>Ready for game night?</h3>
<p>Cards Christians Like, Holy Guacamole, Discernment, and Cast The First Stone are all available on Amazon with fast shipping.</p>
<a class="btn amazon" href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Shop our games on Amazon &rarr;</a>
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
featured = ["cards-christians-like", "expansion-box-vol-1", "cast-the-first-stone", "holy-guacamole", "discernment"]
cards = ""
for h in featured:
    p = by_handle[h]
    img = localize_image(p["image"])
    cards += f"""<a class="card" href="/products/{h}"><img src="{img}" alt="{html.escape(p['title'])} Christian party game" loading="lazy"><div class="pad"><h3>{html.escape(p['title'])}</h3><p>{html.escape(p['blurb'])}</p><span class="cta">View game &rarr;</span></div></a>"""
recent = ""
for a in articles[:3]:
    img = localize_image(a["image"]["url"]) if a.get("image") else None
    imgtag = f'<img src="{img}" alt="{html.escape(a["title"])}" loading="lazy">' if img else ""
    recent += f"""<a class="card" href="/blogs/news/{a['handle']}">{imgtag}<div class="pad"><h3>{html.escape(a['title'])}</h3><span class="cta">Read more &rarr;</span></div></a>"""
ld = [{"@context": "https://schema.org", "@type": "Organization", "name": "Cards Christians Like",
       "legalName": "Christians Like, LLC", "url": BASE, "logo": BASE + "/assets/img/favicon.png",
       "email": "hello@cardschristianslike.com",
       "sameAs": ["https://www.instagram.com/cardschristianslike", "https://www.tiktok.com/@cardschristianslike",
                   "https://www.facebook.com/cardschristianslike", "https://www.amazon.com/dp/B0BBSGRR5X"]},
      {"@context": "https://schema.org", "@type": "WebSite", "name": "Cards Christians Like", "url": BASE}]
body = f"""
<div class="hero">
<span class="pill">Now available on Amazon</span>
<h1>It's a party game, but with convictions.</h1>
<p class="tag">Cards Christians Like is the original Christian party game — hundreds of hilarious combinations that capitalize on Christian culture and the Bible.</p>
<a class="btn amazon" href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Buy on <span class="a">Amazon</span> &rarr;</a>
<p class="note">We've moved our store to Amazon for the best prices and the fastest shipping.</p>
</div>
<section class="wrap" id="games">
<h2>Our Games</h2>
<p style="max-width:620px;color:var(--muted)">Five hilarious, faith-filled games for church groups, families, youth groups, and game nights. Every game ships fast from Amazon.</p>
<div class="grid" style="margin-top:34px">{cards}</div>
</section>
<div class="band">
<h2>Why Amazon?</h2>
<p style="max-width:560px;margin:0 auto 26px;opacity:.85">Better prices, Prime shipping, and easy returns. Same games, same humor, same convictions — just faster to your door.</p>
<a class="btn" style="background:var(--yellow);color:var(--ink)!important" href="https://www.amazon.com/s?k=cards+christians+like" target="_blank" rel="noopener">See all our games on Amazon &rarr;</a>
</div>
<section class="wrap">
<h2>Game Night Ideas</h2>
<div class="grid" style="margin-top:30px">{recent}</div>
<p style="margin-top:26px"><a href="/blogs/news" style="font-weight:700">Read the blog &rarr;</a></p>
</section>
"""
write("/index.html", page("Cards Christians Like – It's a party game but with convictions.",
      "The original Christian party game. Hundreds of hilarious combinations that capitalize on Christian culture and the Bible. Now available on Amazon.", "/index", body, ld))
sitemap_urls.insert(0, "/")

# ---------------- 404 ----------------
body = """<section class="wrap" style="text-align:center;padding:110px 20px">
<h1>Well, this page hath passed away.</h1>
<p style="color:var(--muted)">The page you're looking for isn't here — but the games definitely are.</p>
<p style="margin-top:24px"><a class="btn" href="/">Back to home</a>&nbsp;&nbsp;<a class="btn amazon" href="https://www.amazon.com/dp/B0BBSGRR5X" target="_blank" rel="noopener">Shop on Amazon</a></p></section>"""
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
