# cardschristianslike.com

Static landing site for Cards Christians Like. Replaces the old Shopify store, preserves every Shopify URL for SEO, and points all purchase CTAs to Amazon.

## Project layout

```
build.py            # static site generator (Python 3, no dependencies)
data/products.json  # product content: titles, descriptions, prices, Amazon ASINs
content/            # blog article JSON (from Shopify), policy page HTML, image cache
content/img-cache/  # all images, downloaded once — never re-fetched if present
dist/               # GENERATED site — what Vercel serves. Commit this folder.
vercel.json         # redirects (SEO-critical), clean URLs, cache headers
```

## Two ways to edit

**A. Edit content, then regenerate (recommended for products/posts):**

1. Edit `data/products.json` (descriptions, prices, Amazon links) or `build.py` (layout, CSS — see the `CSS` string and `page()` template).
2. Run `python3 build.py` — rebuilds `dist/` in a few seconds. Images come from `content/img-cache/`, so no network needed.
3. Preview locally: `python3 -m http.server 8000 --directory dist` → http://localhost:8000
4. Commit and push — Vercel deploys automatically once the repo is connected.

**B. Edit `dist/` HTML directly (fine for quick tweaks):**
Works, but changes are overwritten the next time `build.py` runs. If you start doing heavy design work in Cursor, either do it in `build.py`'s template/CSS, or abandon the generator and treat `dist/` as the source of truth.

## SEO rules — do not break these

- **Never change or delete URLs** in `dist/` (products/, collections/, blogs/news/, pages/). They match the old Shopify paths and carry the domain's backlinks and rankings.
- **Never remove redirects from `vercel.json`** — they route link equity from deleted Shopify URLs.
- Keep `sitemap.xml` in sync if you add pages (build.py handles this automatically).

## Amazon listing map

| Product | ASIN |
|---|---|
| Cards Christians Like | B0BBSGRR5X |
| Expansion Box Vol. 1 | B0BSB4NP3D |
| Cast The First Stone | B0BDC1YVQ2 |
| Holy Guacamole | B0CS4VRN3N |
| Discernment | B0D5C874R9 |

## Vercel

Project: `cardschristianslike` (team dmaddrys-projects).
Once connected to git, set in Project → Settings → Build & Development:
- Framework preset: **Other**
- Build command: **(empty / off)** — `dist/` is committed, nothing to build
- Output directory: **dist**

(Until git is connected, the project uses a legacy tarball build command — clear it when connecting.)
