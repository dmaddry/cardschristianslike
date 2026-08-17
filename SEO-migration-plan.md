# cardschristianslike.com — Rebuild & SEO Migration Plan

**Prepared:** August 17, 2026
**Goal:** Replace the password-locked Shopify store with a fast static site that preserves the domain's SEO authority and routes all purchase intent to Amazon.

## 1. Why this is urgent

The Shopify store has been password-locked, which redirects every URL on the domain to the password page. Semrush shows the cost:

| Month | Organic keywords | Organic traffic/mo |
|---|---|---|
| Dec 2025 | 563 | 3,184 |
| Feb 2026 | 684 | 2,923 |
| Apr 2026 | 412 | 1,849 |
| Jun 2026 | 317 | 417 |
| Jul 2026 | 238 | 294 |

Traffic is down ~90% from peak. What's still intact: **Authority Score 19, 675 backlinks from 374 referring domains**, and top rankings on branded + non-branded terms ("cards christians like" #2, "christian cards against humanity" #2, "christian party games" #3, "christian card games" #7). The faster the real site returns, the more of this recovers.

## 2. What carries the authority

- **Homepage** — ~90% of all backlinks (330+ referring domains across http/https/www variants). Rebuilt as the Amazon-pointing landing page.
- **Product URLs** — `/products/cards-christians-like` (8 ref. domains), `/products/discernment` (6), plus the other games. All rebuilt at identical URLs with Amazon CTAs.
- **Blog posts** — 12 posts under `/blogs/news/`, several with backlinks; they target the non-branded keywords that drove discovery. All rebuilt at identical URLs.
- **Deleted product URLs with backlinks** — trash-theology, gen-z, jesus-loves-you, pop-culture, worship, cards-christians-hide expansion packs. 301 → `/products/expansion-box-vol-1`.
- **Collections** — games, expansions-1, print-at-home, holy-guacamole-bundle rebuilt; retired ones 301 to `/collections/games`.
- **Influencer shortlinks** (`/stickemup`, `/ksenia`, etc.) — 302 → the Amazon base-game listing (the Shopify discount codes behind them no longer exist).

## 3. What was built

Static site, exact same URL structure as Shopify (`cleanUrls`, no trailing slashes):

- `/` — landing page: hero, "Now available on Amazon," 5-game grid, blog teasers
- `/products/<handle>` — 10 product pages with original descriptions, prices, images, Product JSON-LD (offer URL = Amazon listing), per-product Amazon buttons
- `/collections/{games, expansions-1, print-at-home, holy-guacamole-bundle}`
- `/blogs/news` + all 12 articles with original content, BlogPosting JSON-LD, Amazon CTA footer
- `/pages/{privacy-policy, terms-of-service, return-and-refund-policy}`
- `sitemap.xml`, `robots.txt`, custom 404, 31 redirects in `vercel.json`
- All 70+ images downloaded from Shopify CDN / Bannerbear / Pexels, compressed (66 MB → ~9 MB), and self-hosted so nothing breaks when Shopify is cancelled

**Amazon listing map:**

| Page | ASIN |
|---|---|
| Cards Christians Like (+ print-at-home) | B0BBSGRR5X |
| Expansion Box Vol. 1 (+ bundle, print expansions, deleted packs) | B0BSB4NP3D |
| Cast The First Stone (+ print-at-home) | B0BDC1YVQ2 |
| Holy Guacamole | B0CS4VRN3N |
| Discernment | B0D5C874R9 |

## 4. Cutover checklist (after Vercel deploy)

1. **Add the domain in Vercel**: Project → Settings → Domains → add `cardschristianslike.com` and `www.cardschristianslike.com` (www → apex redirect).
2. **Update DNS** where the domain is registered (currently pointing at Shopify): apex A record → `76.76.21.21`, `www` CNAME → `cname.vercel-dns.com`. Remove the Shopify A/CNAME records. Vercel will show the exact records it wants.
3. **Verify redirects** after DNS propagates: spot-check `/password`, `/products/trash-theology-expansion-pack`, `/collections/special`, an old discount shortlink.
4. **Google Search Console**: verify the domain property (DNS TXT record), submit `https://cardschristianslike.com/sitemap.xml`, and use URL Inspection → Request Indexing on the homepage and top product pages.
5. **Bing Webmaster Tools**: import from Search Console, submit the sitemap.

## 5. Winding down Shopify — cautions

- **Do not let the domain lapse or transfer it carelessly** — the domain itself is the asset. If it's registered *through* Shopify, transfer it to a registrar (Cloudflare, Namecheap) **before** cancelling the plan.
- Keep the Shopify plan active until DNS has fully cut over and you've confirmed the Vercel site serves on the domain.
- Export orders/customers from Shopify admin before cancelling if you want the records.
- The site bundle currently deploys from a tarball hosted on your Shopify CDN; once deployed, the deployment is permanent, but keep the local `ccl-site-bundle.zip` as the source of truth for future edits/redeploys.

## 6. Expected outcome

Rankings that survived (mostly branded + top non-branded) should stabilize within days of the 200-status pages returning, and lost non-branded rankings ("christian party games," "christian card games," blog long-tails) have a good chance of recovering over 4–12 weeks since the backlink profile never degraded. The biggest single factor is simply time-to-launch — every week password-locked costs more of the remaining 238 keywords.

## 7. Maintenance notes

- Amazon links are plain `/dp/ASIN` URLs in the HTML — search for the ASIN to change a link.
- To edit content: unzip the bundle, edit `build.py` / `data/products.json` / `content/`, re-run `python3 build.py`, redeploy.
- If you later join Amazon Associates or Brand Referral Bonus, append your tag to the Amazon URLs for attribution revenue on the traffic you're sending.
