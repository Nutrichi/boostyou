# Boostyou.ai – WoW Classic / TBC / WotLK Guides (2026)

Source for **https://boostyou.ai**, a fast static site with:
- Leveling guides (1-60, 60-70, 70-80) and comparisons
- Class/spec guides (all Classic classes + DK)
- Profession guides (Classic → WotLK)
- Addon comparisons (RestedXP vs Zygor, RestedXP vs Joana)
- Content hub with Shorts/YouTube/Twitch embeds

## What’s live
- `https://boostyou.ai/` – main landing
- `https://boostyou.ai/fast-leveling` – leveling overview with route links
- `https://boostyou.ai/class-guides` – all class/spec entry points
- `https://boostyou.ai/professions` – profession overview + detail pages
- `https://boostyou.ai/newcontent` – content hub (YouTube/Twitch + CurseForge links)
- Comparisons: `https://boostyou.ai/restedxp-vs-zygor`, `https://boostyou.ai/restedxp-vs-joana`
- Route pages: `https://boostyou.ai/fastest-1-60`, `https://boostyou.ai/fastest-60-70`, `https://boostyou.ai/fastest-70-80`
- Plus per-class and per-profession pages (see `content/`)

## SEO / discoverability
- Every active page now includes: `<title>`, `meta description`, `rel="canonical"`, `og:title`, `og:description`, `og:url`, `og:image`, `og:type`.
- Canonicals use the clean slug version (e.g., `https://boostyou.ai/fast-leveling`).
- Updated `sitemap.xml` covers all active HTML pages; `robots.txt` allows full crawl.
- Lightweight, mobile-friendly HTML/CSS; no blocking scripts beyond analytics where present.

## Maintenance
- Add new pages under `content/` and set title + description; canonicals/OG tags should follow the slug pattern.
- Update `sitemap.xml` when adding/removing pages (keep canonicals consistent).
- Keep `robots.txt` pointing at the current sitemap URL.

Contributions and fixes welcome—open an issue or PR.
