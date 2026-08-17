# Homepage restyle — CAH layout principles, CCL colors

Date: 2026-08-17  
Scope: Homepage only (`/`), plus shared header/CSS changes needed to support it.

## Goal

Restyle the Cards Christians Like homepage using Cards Against Humanity’s **layout and UX principles** (huge type, white space, direct buy, how-to-play, FAQ) while keeping **our color scheme and voice**. Do not copy CAH branding, jokes, or black/white palette.

## Non-goals

- No restyle of product, collection, blog, or policy page templates beyond what shared CSS/header forces
- No email signup
- No blog section on the homepage
- No URL, redirect, or Amazon ASIN changes
- No print-at-home offer on the homepage (that SKU is retired)

## Header

- Links: **Games**, **Expansions**, **Shop on Amazon**
- Remove **Blog** from the header (this is the shared `page()` header, so Blog disappears from every page’s nav)
- Blog remains in the footer
- Amazon button stays, but less “pill shop”: slightly squarer corners, same ink background and Amazon-orange wordmark

## Homepage sections (top to bottom)

### 1. Hero

- Cream background (`--cream`), ink type — **no teal gradient**
- Headline: *It’s a party game, but with convictions.*
- One short subline (current meaning: original Christian party game, church/Bible humor)
- One primary CTA: Buy on Amazon → `https://www.amazon.com/dp/B0BBSGRR5X`
- Optional one-line note that the store moved to Amazon for price and shipping
- Yellow used as a small accent (underline, label, or button hover), not a full-width banner

### 2. How you play

- One paragraph: one player reads a prompt card; everyone else plays the funniest answer
- Two graphic card faces (the only fully graphic moment):
  - Prompt: teal background, cream type
  - Answer: cream/white background, ink type, thin ink or teal border
- Copy on the fake cards must be original CCL-style lines, not CAH lines
- No rules PDF, no extra steps, no numbered list beyond that one idea

### 3. Buy the game

- Hero product: **Cards Christians Like** (`/products/cards-christians-like`)
- Show existing image, title, blurb, price `$39.99`, Amazon button (same ASIN as now)
- Do **not** add a print-at-home CTA here

### 4. The other games

Large tiles (not small rounded shop cards), each linking to the existing product URL:

- Expansion Box Vol. 1
- Cast the First Stone
- Holy Guacamole
- Discernment

Each tile: image, name, one-line blurb from `data/products.json`, “View game”

### 5. FAQ accordion

Native `<details>` / `<summary>` so it works without JavaScript. All items start closed.

| Question | Answer intent |
|---|---|
| Where do I buy it? | Amazon. Link the main game ASIN. |
| How do you play? | Same explanation as the how-you-play section, shorter. |
| Do you sell expansions? | Yes — Expansion Box Vol. 1 and the other games. Link `/collections/expansions-1` and `/collections/games`. |
| Does it work for church / family night? | Yes — written for church groups, families, youth groups. Still punchy; not a kids’ Bible trivia game. |
| What happened to the old store? | Moved to Amazon for better prices, Prime shipping, and returns. Same games. |

Voice: CCL — dry and direct, not CAH crude.

### 6. Footer

Unchanged content. May pick up slightly sharper shared type/buttons.

## Visual system

Keep CSS variables:

- `--teal: #108474`
- `--teal-d: #0b6154`
- `--yellow: #fbcd0a`
- `--ink: #131b22`
- `--cream: #faf7f2`
- `--muted`, `--line`, `--amz` unchanged

Type: keep **Montserrat** headlines and **Open Sans** body. Headlines get larger size, line-height near 1, slight negative letter-spacing.

Chrome: fewer 999px pills; buttons and tiles use modest radius (about 4–8px). Product tiles: thin border, little or no drop shadow.

Shared CSS will shift type and buttons site-wide just enough that inner pages still look like the same brand. New homepage blocks use scoped classes (e.g. `.home-hero`, `.play-cards`, `.buy-block`, `.faq`) so product/blog cards are not forced into the large homepage tile layout.

## Implementation

- Edit `build.py` only (CSS string, `page()` nav, homepage `body`)
- Rebuild `dist/` with `python3 build.py`
- Do not change `vercel.json` redirects or product handles

## Success

- Homepage feels closer to CAH’s editorial shop (scale, spacing, buy path, FAQ) while clearly still CCL in color and copy
- Header has no Blog link
- Existing product URLs and Amazon CTAs still work
- Inner pages still usable after the shared CSS/header tweak
