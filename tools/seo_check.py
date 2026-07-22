#!/usr/bin/env python3
"""seo_check.py — site-wide SEO / crawler / AI-search / social audit.

Run before every push: python3 tools/seo_check.py
Exit code 1 if any FAIL is found. Checks every HTML page for:

  - <title> present, unique across the site
  - meta description present (and <= 320 chars)
  - canonical URL present and matching the file's real path
  - Open Graph tags (og:title, og:description, og:url, og:image) — social shares
  - twitter:card tag — X/Twitter link previews
  - <html lang> attribute
  - noindex accidents (robots meta must not say noindex)

Plus site-level checks:
  - every HTML page is in sitemap.xml (and no sitemap entry points to a missing file)
  - robots.txt references the sitemap
  - llms.txt links resolve to existing local files
  - posts/index.json lists every posts/*.txt

See "SEO & discoverability" in CLAUDE.md for the rules new pages must follow.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://boostyou.ai"

fails, warns = [], []


def fail(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


def check_pages():
    titles = {}
    pages = [ROOT / "index.html"] + sorted((ROOT / "content").glob("*.html"))
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        html = p.read_text(encoding="utf-8", errors="ignore")
        head = html.split("</head>", 1)[0]

        m = re.search(r"<title>(.*?)</title>", head, re.S)
        if not m or not m.group(1).strip():
            fail(f"{rel}: missing <title>")
        else:
            t = m.group(1).strip()
            if t in titles:
                fail(f"{rel}: duplicate <title> (same as {titles[t]})")
            titles[t] = rel

        if not re.search(r'<meta\s+name="description"\s+content="[^"]{20,}"', head):
            fail(f"{rel}: missing/short meta description")
        else:
            desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', head).group(1)
            if len(desc) > 320:
                warn(f"{rel}: meta description > 320 chars ({len(desc)})")

        m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', head)
        if not m:
            fail(f"{rel}: missing canonical")
        elif m.group(1) != f"{SITE}/{rel}" and not (rel == "index.html" and m.group(1).rstrip("/") == SITE):
            fail(f"{rel}: canonical mismatch ({m.group(1)})")

        for og in ("og:title", "og:description", "og:url", "og:image"):
            if f'property="{og}"' not in head:
                fail(f"{rel}: missing {og}")
        if 'name="twitter:card"' not in head:
            fail(f"{rel}: missing twitter:card")

        if "noindex" in head:
            fail(f"{rel}: page is set to noindex")
        if not re.search(r"<html[^>]+lang=", html):
            warn(f"{rel}: missing <html lang>")
    return {p.relative_to(ROOT).as_posix() for p in pages}


def check_sitemap(page_set):
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = set(re.findall(r"<loc>(.*?)</loc>", xml))
    mapped = {l.replace(SITE + "/", "") for l in locs} - {SITE, ""}
    for page in page_set:
        if page != "index.html" and page not in mapped:
            fail(f"sitemap.xml: missing entry for {page}")
    for entry in mapped:
        if entry.endswith(".html") and not (ROOT / entry).exists():
            fail(f"sitemap.xml: entry points to missing file {entry}")
        if entry.startswith("posts/") and not (ROOT / entry).exists():
            fail(f"sitemap.xml: entry points to missing post {entry}")


def check_txt_files():
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap:" not in robots:
        fail("robots.txt: missing Sitemap: line")

    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    for url in re.findall(r"\((https://boostyou\.ai/[^)\s]+)\)", llms):
        rel = url.replace(SITE + "/", "")
        if "<" in rel:  # pattern placeholders like bis-<expansion>-...
            continue
        if not (ROOT / rel).exists():
            fail(f"llms.txt: link to missing file {rel}")

    idx = json.loads((ROOT / "posts" / "index.json").read_text(encoding="utf-8"))
    listed = set(idx.get("posts", []))
    actual = {p.name for p in (ROOT / "posts").glob("*.txt")}
    for missing in actual - listed:
        fail(f"posts/index.json: missing {missing}")
    for stale in listed - actual:
        fail(f"posts/index.json: lists non-existent {stale}")


def main():
    pages = check_pages()
    check_sitemap(pages)
    check_txt_files()

    for w in warns:
        print(f"WARN  {w}")
    for f in fails:
        print(f"FAIL  {f}")
    print(f"\nChecked {len(pages)} pages — {len(fails)} failures, {len(warns)} warnings.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
