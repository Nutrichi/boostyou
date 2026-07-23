#!/usr/bin/env python3
"""post_pages.py — static SEO pages for the news posts.

The NEWS feed (content/newcontent.html) renders posts/*.txt client-side via
the GitHub API, which crawlers cannot index. This tool gives every post a
crawlable static twin and keeps discovery surfaces in sync:

  content/news-<YYYY-MM-DD-slug>.html   one article page per posts/*.txt
  content/newcontent.html               static "All posts" links block
                                        (between news-pages markers)
  sitemap.xml                           block between news-pages markers
  llms.txt                              block between news-pages markers

Post format (same as assets/blog.js): filename YYYY-MM-DD-slug.txt,
first line = title, blank line = new paragraph, URLs auto-link.

Run after adding/editing a post (see CLAUDE.md "News blog"); idempotent,
re-runs stamp_nav.py automatically. Never hand-edit content/news-*.html.
"""

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://boostyou.ai"
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

GA = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-V8NDLSEBGZ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag('js', new Date());
    gtag('config', 'G-V8NDLSEBGZ');
  </script>"""

STYLE = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: rgb(15, 23, 42); color: #e2e8f0; font-family: 'Inter', -apple-system, sans-serif; line-height: 1.7; }
    .page { max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
    .crumbs { font-size: 0.85rem; color: #94a3b8; margin: 1rem 0 1.5rem; }
    .crumbs a { color: #60a5fa; text-decoration: none; }
    .post-date { color: #fbbf24; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    h1 { font-size: 1.9rem; font-weight: 900; color: #f1f5f9; line-height: 1.25; margin: 0.4rem 0 1.5rem; }
    article p { margin-bottom: 1.1rem; color: #cbd5e1; }
    article a { color: #60a5fa; word-break: break-all; }
    .more { margin-top: 2.5rem; padding-top: 1.25rem; border-top: 1px solid rgba(148, 163, 184, 0.2); }
    .more h2 { font-size: 1.05rem; font-weight: 800; color: #f1f5f9; margin-bottom: 0.6rem; }
    .more ul { list-style: none; }
    .more li { margin: 0.35rem 0; }
    .more a { color: #60a5fa; text-decoration: none; }
    .more a:hover { text-decoration: underline; }
    .more .d { color: #94a3b8; font-size: 0.85rem; margin-left: 0.4rem; }
    .cta-wrap { margin-top: 2.5rem; }
    @media (max-width: 640px) { h1 { font-size: 1.45rem; } }
"""


def esc(s):
    return html.escape(str(s), quote=True)


def linkify(escaped_text):
    return re.sub(r"https?://[^\s<]+",
                  lambda m: f'<a href="{m.group(0)}" target="_blank" rel="noreferrer">{m.group(0)}</a>',
                  escaped_text)


def parse_post(path):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.txt$", path.name)
    if not m:
        return None
    text = path.read_text(encoding="utf-8").replace("\r", "")
    lines = text.split("\n")
    title = ""
    while lines and not title:
        title = lines.pop(0).strip()
    paragraphs = [p.strip() for p in "\n".join(lines).strip().split("\n\n") if p.strip()]
    date_iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    date_h = f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}"
    return {"stem": path.stem, "title": title, "paragraphs": paragraphs,
            "date_iso": date_iso, "date_h": date_h,
            "page": f"news-{path.stem}.html"}


def render_post_page(p, others):
    title = f"{p['title']} | Boostyou.ai News"
    description = re.sub(r"\s+", " ", p["paragraphs"][0])[:300] if p["paragraphs"] else p["title"]
    jsonld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": p["title"], "datePublished": p["date_iso"],
        "url": f"{SITE}/content/{p['page']}",
        "publisher": {"@type": "Organization", "name": "Boostyou.ai", "url": SITE},
        "mainEntityOfPage": f"{SITE}/content/{p['page']}",
    }
    body_paras = "\n".join(
        "<p>" + linkify(esc(par)).replace("\n", "<br>") + "</p>" for par in p["paragraphs"])
    more = "\n".join(
        f'<li><a href="{o["page"]}">{esc(o["title"])}</a><span class="d">{esc(o["date_h"])}</span></li>'
        for o in others[:4])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>{esc(title)}</title>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="{esc(description)}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{SITE}/content/{p['page']}" />
  <meta name="author" content="Boostyou.ai" />
  <link rel="icon" href="../assets/favicon.ico" />
  <meta property="og:title" content="{esc(p['title'])}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{SITE}/content/{p['page']}" />
  <meta property="og:type" content="article" />
  <meta property="article:published_time" content="{p['date_iso']}" />
  <meta property="og:image" content="{SITE}/assets/og-image-mobile.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  {GA}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap">
  <style>{STYLE}</style>
  <link rel="stylesheet" href="../assets/cta.css" />
  <script src="../assets/cta.js" defer></script>
  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
<main class="page">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="newcontent.html">News</a> › {esc(p['title'])}</div>
<article>
<div class="post-date">{esc(p['date_h'])}</div>
<h1>{esc(p['title'])}</h1>
{body_paras}
</article>
<div class="more">
<h2>More news</h2>
<ul>
{more}
<li><a href="newcontent.html">← All news</a></li>
</ul>
</div>
<div class="cta-wrap"><div class="newsletter-cta"
     data-heading="WoW Classic news, straight to your inbox"
     data-sub="Subscribe and get a mail whenever new posts and BiS lists go live."></div></div>
</main>
</body>
</html>
"""


# ------------------------------------------------------- managed blocks

NEWS_START_HTML = "<!-- news-pages:start (generated by tools/post_pages.py) -->"
NEWS_END_HTML = "<!-- news-pages:end -->"


def replace_block(text, start, end, block, fallback_anchor):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)
    return text.replace(fallback_anchor, block + "\n" + fallback_anchor, 1)


def update_newcontent(posts):
    """Static, crawlable links to every post below the JS feed."""
    path = ROOT / "content" / "newcontent.html"
    html_text = path.read_text(encoding="utf-8")
    links = "\n".join(
        f'    <li><a href="{p["page"]}">{esc(p["title"])}</a> <span style="color:#94a3b8;font-size:0.85rem;">{esc(p["date_h"])}</span></li>'
        for p in posts)
    block = (f"{NEWS_START_HTML}\n"
             '<section class="news-static-list" aria-label="All news posts" style="margin-top:2rem;">\n'
             '  <h2 style="font-size:1.05rem;color:#f1f5f9;margin-bottom:0.6rem;">All posts</h2>\n'
             '  <ul style="list-style:none;padding:0;">\n'
             f"{links}\n"
             "  </ul>\n"
             "</section>\n"
             f"{NEWS_END_HTML}")
    updated = replace_block(html_text, NEWS_START_HTML, NEWS_END_HTML, block,
                            '<div id="blogSentinel"></div>')
    path.write_text(updated, encoding="utf-8")


SM_START, SM_END = "  <!-- news-pages:start (generated by tools/post_pages.py) -->", "  <!-- news-pages:end -->"


def update_sitemap(posts):
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    block = [SM_START]
    for p in posts:
        block.append(f"  <url>\n    <loc>{SITE}/content/{p['page']}</loc>\n    <lastmod>{p['date_iso']}</lastmod>\n"
                     f"    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>")
    block.append(SM_END)
    xml = replace_block(xml, SM_START, SM_END, "\n".join(block), "</urlset>")
    path.write_text(xml, encoding="utf-8")


LL_START, LL_END = "<!-- news-pages:start (generated by tools/post_pages.py) -->", "<!-- news-pages:end -->"


def update_llms(posts):
    path = ROOT / "llms.txt"
    txt = path.read_text(encoding="utf-8")
    lines = [LL_START, "", "### Latest news posts (static pages)", ""]
    for p in posts[:10]:
        lines += [f"- [{p['title']}]({SITE}/content/{p['page']}) ({p['date_iso']})"]
    lines += ["", LL_END]
    txt = replace_block(txt, LL_START, LL_END, "\n".join(lines), "## Leveling Routes")
    path.write_text(txt, encoding="utf-8")


def main():
    posts = [p for p in (parse_post(f) for f in sorted((ROOT / "posts").glob("*.txt"), reverse=True)) if p]
    if not posts:
        print("No posts found.")
        return 0

    for i, p in enumerate(posts):
        others = [o for o in posts if o is not p]
        (ROOT / "content" / p["page"]).write_text(render_post_page(p, others), encoding="utf-8")

    update_newcontent(posts)
    update_sitemap(posts)
    update_llms(posts)
    print(f"Generated {len(posts)} news pages; newcontent.html, sitemap.xml and llms.txt updated.")

    import subprocess
    subprocess.run([sys.executable, str(ROOT / "tools" / "stamp_nav.py")], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
