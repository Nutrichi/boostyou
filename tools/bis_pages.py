#!/usr/bin/env python3
"""bis_pages.py — static SEO pages for the BiS lists.

The interactive browser (content/bis.html) renders bis-data/*.json client-side
behind hash URLs, which search engines and AI crawlers cannot index. This tool
generates one crawlable HTML page per list plus a hub page, and keeps
sitemap.xml and llms.txt in sync:

  content/bis-<exp>-<phase>-<class>-<spec>.html   one page per JSON list
  content/bis-all.html                            hub linking every list
  sitemap.xml                                     block between bis-pages markers
  llms.txt                                        section between bis-pages markers

Run after every content batch (BIS-PLAN.md workflow step 4b), then re-run
tools/stamp_nav.py so the new pages get the site nav. Idempotent.

The expansion/phase/class catalog below mirrors assets/bis.js — keep in sync.
"""

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "bis-data"
SITE = "https://boostyou.ai"

# ---------------------------------------------------------------- catalog
# Mirrors assets/bis.js (EXPANSIONS / CLASSES). Keep in sync.

EXPANSIONS = {
    "classic": ("Classic", {
        "preraid": "Pre-Raid", "p1": "Phase 1 — Molten Core & Onyxia",
        "p2": "Phase 2 — Dire Maul", "p3": "Phase 3 — Blackwing Lair",
        "p4": "Phase 4 — Zul'Gurub", "p5": "Phase 5 — Ahn'Qiraj",
        "p6": "Phase 6 — Naxxramas"}),
    "tbc": ("TBC", {
        "preraid": "Pre-Raid", "p1": "Phase 1 — Karazhan, Gruul & Mag",
        "p2": "Phase 2 — SSC & Tempest Keep", "p3": "Phase 3 — Hyjal & Black Temple",
        "p4": "Phase 4 — Zul'Aman", "p5": "Phase 5 — Sunwell Plateau"}),
    "wotlk": ("WotLK", {
        "preraid": "Pre-Raid", "p1": "Phase 1 — Naxx, OS & EoE",
        "p2": "Phase 2 — Ulduar", "p3": "Phase 3 — Trial of the Crusader",
        "p4": "Phase 4 — ICC & Ruby Sanctum"}),
    "cata": ("Cataclysm", {
        "preraid": "Pre-Raid", "p1": "Phase 1 — BWD, BoT & To4W",
        "p2": "Phase 2 — Firelands", "p3": "Phase 3 — Dragon Soul"}),
    "mop": ("MoP", {
        "preraid": "Pre-Raid", "p1": "Phase 1 — MSV, HoF & ToES",
        "p2": "Phase 2 — Throne of Thunder", "p3": "Phase 3 — Siege of Orgrimmar"}),
}

CLASS_LABELS = {
    "death-knight": "Death Knight", "druid": "Druid", "hunter": "Hunter",
    "mage": "Mage", "monk": "Monk", "paladin": "Paladin", "priest": "Priest",
    "rogue": "Rogue", "shaman": "Shaman", "warlock": "Warlock", "warrior": "Warrior",
}

SPEC_LABELS = {
    "beast-mastery": "Beast Mastery",
}  # every other spec id is just capitalized


def spec_label(spec_id):
    return SPEC_LABELS.get(spec_id, spec_id.replace("-", " ").title())


def esc(s):
    return html.escape(str(s), quote=True)


def wowhead_url(exp, item_name):
    name = re.sub(r"\s*\((.*?)\)\s*$", "", item_name)
    return f"https://www.wowhead.com/{exp}/search?q={html.escape(name).replace(' ', '+')}"


# ---------------------------------------------------------------- page template

STYLE = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: rgb(15, 23, 42); color: #e2e8f0; font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; }
    .page { max-width: 900px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
    .crumbs { font-size: 0.85rem; color: #94a3b8; margin: 1rem 0 1.5rem; }
    .crumbs a { color: #60a5fa; text-decoration: none; }
    h1 { font-size: 1.9rem; font-weight: 900; color: #f1f5f9; line-height: 1.25; margin-bottom: 0.5rem; }
    .meta-line { color: #94a3b8; font-size: 0.95rem; margin-bottom: 1rem; }
    .draft-badge { display: inline-block; background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.4); border-radius: 0.4rem; padding: 0.1rem 0.55rem; font-size: 0.8rem; font-weight: 700; }
    .notes { background: rgba(59, 130, 246, 0.08); border-left: 3px solid #3b82f6; border-radius: 0 0.5rem 0.5rem 0; padding: 0.9rem 1.1rem; margin: 1.25rem 0; color: #cbd5e1; font-size: 0.95rem; }
    .app-link { display: inline-block; margin: 0.25rem 0 1.5rem; color: #60a5fa; font-weight: 600; text-decoration: none; }
    .app-link:hover { text-decoration: underline; }
    h2 { font-size: 1.3rem; font-weight: 800; color: #f1f5f9; margin: 2rem 0 0.75rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.93rem; }
    th, td { text-align: left; padding: 0.6rem 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.15); vertical-align: top; }
    th { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }
    td.slot { color: #94a3b8; font-weight: 600; white-space: nowrap; }
    a.item { color: #60a5fa; font-weight: 600; text-decoration: none; }
    a.item:hover { text-decoration: underline; }
    .src { color: #94a3b8; font-size: 0.85rem; display: block; }
    .alt { color: #cbd5e1; font-size: 0.88rem; margin-top: 0.35rem; }
    .alt-rank { color: #fbbf24; font-size: 0.75rem; font-weight: 700; margin-right: 0.3rem; }
    .gem-meta { color: #e2e8f0; } .gem-red { color: #f87171; } .gem-yellow { color: #fbbf24; } .gem-blue { color: #60a5fa; }
    .related { margin-top: 2.5rem; padding-top: 1.25rem; border-top: 1px solid rgba(148, 163, 184, 0.2); font-size: 0.92rem; color: #94a3b8; }
    .related a { color: #60a5fa; text-decoration: none; }
    .cta-wrap { margin-top: 2.5rem; }
    .hub-group h2 { margin-top: 2rem; }
    .hub-list { list-style: none; columns: 2; column-gap: 2rem; }
    .hub-list li { margin: 0.3rem 0; break-inside: avoid; }
    .hub-list a { color: #60a5fa; text-decoration: none; }
    .hub-list a:hover { text-decoration: underline; }
    @media (max-width: 640px) { .hub-list { columns: 1; } h1 { font-size: 1.5rem; } }
"""

GA = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-V8NDLSEBGZ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag('js', new Date());
    gtag('config', 'G-V8NDLSEBGZ');
  </script>"""


def head(title, description, canonical_file, jsonld=None):
    j = f'\n  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>{esc(title)}</title>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="{esc(description)}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{SITE}/content/{canonical_file}" />
  <meta name="author" content="Boostyou.ai" />
  <link rel="icon" href="../assets/favicon.ico" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{SITE}/content/{canonical_file}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="{SITE}/assets/og-image-mobile.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  {GA}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap">
  <style>{STYLE}</style>
  <link rel="stylesheet" href="../assets/cta.css" />
  <script src="../assets/cta.js" defer></script>{j}
</head>
<body>
"""


def render_list_page(d, key, all_keys):
    exp_label, phases = EXPANSIONS[d["expansion"]]
    phase_label = phases[d["phase"]]
    cls = CLASS_LABELS[d["class"]]
    spec = spec_label(d["spec"])
    fname = f"bis-{key}.html"
    hash_url = f"bis.html#{d['expansion']}/{d['phase']}/{d['class']}/{d['spec']}"

    title = f"{spec} {cls} BiS — {exp_label} {phase_label.split(' — ')[0]} | Boostyou.ai"
    top_items = ", ".join(re.sub(r" \(.*?\)$", "", s["items"][0]["name"]) for s in d["slots"][:3])
    description = (f"{spec} {cls} best in slot for {exp_label} {phase_label}: full PvE BiS gear with drop "
                   f"sources, enchants and gems. Includes {top_items} and more.")[:300]

    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "BiS Lists", "item": f"{SITE}/content/bis-all.html"},
                {"@type": "ListItem", "position": 3, "name": f"{spec} {cls} — {exp_label} {phase_label}",
                 "item": f"{SITE}/content/{fname}"}]},
            {"@type": "ItemList",
             "name": f"{spec} {cls} Best in Slot — {exp_label} {phase_label}",
             "numberOfItems": len(d["slots"]),
             "itemListElement": [
                 {"@type": "ListItem", "position": i + 1,
                  "name": f"{s['slot']}: {s['items'][0]['name']}",
                  "description": s["items"][0].get("source", "")}
                 for i, s in enumerate(d["slots"])]},
        ],
    }

    out = [head(title, description, fname, jsonld)]
    out.append('<main class="page">')
    out.append(f'<div class="crumbs"><a href="../index.html">Home</a> › <a href="bis-all.html">BiS Lists</a> › '
               f'{esc(exp_label)} · {esc(phase_label.split(" — ")[0])} › {esc(spec)} {esc(cls)}</div>')
    out.append(f"<h1>{esc(spec)} {esc(cls)} Best in Slot — {esc(exp_label)}, {esc(phase_label)}</h1>")
    badge = ' <span class="draft-badge">Draft — being verified</span>' if d.get("status") == "draft" else ""
    out.append(f'<p class="meta-line">{esc(d.get("role", ""))} · Updated {esc(d.get("updated", ""))}{badge}</p>')
    if d.get("notes"):
        out.append(f'<div class="notes">{esc(d["notes"])}</div>')
    out.append(f'<a class="app-link" href="{esc(hash_url)}">Open in the interactive BiS browser →</a>')

    out.append("<h2>Best in Slot by gear slot</h2>")
    out.append("<table><thead><tr><th>Slot</th><th>Item &amp; alternatives</th></tr></thead><tbody>")
    for s in d["slots"]:
        best, alts = s["items"][0], s["items"][1:]
        cell = (f'<a class="item" href="{wowhead_url(d["expansion"], best["name"])}" target="_blank" rel="noreferrer">'
                f'{esc(best["name"])}</a><span class="src">{esc(best.get("source", ""))}</span>')
        for i, alt in enumerate(alts):
            cell += (f'<div class="alt"><span class="alt-rank">{i + 2}{"nd" if i == 0 else "rd"}</span>'
                     f'<a class="item" href="{wowhead_url(d["expansion"], alt["name"])}" target="_blank" rel="noreferrer">'
                     f'{esc(alt["name"])}</a><span class="src">{esc(alt.get("source", ""))}</span></div>')
        out.append(f'<tr><td class="slot">{esc(s["slot"])}</td><td>{cell}</td></tr>')
    out.append("</tbody></table>")

    if d.get("enchants"):
        out.append("<h2>Enchants</h2>")
        out.append("<table><thead><tr><th>Slot</th><th>Enchant</th></tr></thead><tbody>")
        for e in d["enchants"]:
            out.append(f'<tr><td class="slot">{esc(e["slot"])}</td><td>{esc(e["name"])}'
                       f'<span class="src">{esc(e.get("source", ""))}</span></td></tr>')
        out.append("</tbody></table>")

    if d.get("gems"):
        out.append("<h2>Gems</h2>")
        out.append("<table><thead><tr><th>Socket</th><th>Gem</th></tr></thead><tbody>")
        for g in d["gems"]:
            out.append(f'<tr><td class="slot gem-{esc(g["color"].lower())}">{esc(g["color"])}</td><td>{esc(g["name"])}</td></tr>')
        out.append("</tbody></table>")

    # sibling links: same phase, same class (other specs) + full phase hub
    siblings = [k for k in all_keys
                if k != key and k.startswith(f"{d['expansion']}-{d['phase']}-{d['class']}-")]
    prefix_len = len(d["expansion"]) + len(d["phase"]) + len(d["class"]) + 3
    rel_html = " · ".join(f'<a href="bis-{k}.html">{esc(spec_label(k[prefix_len:]))} {esc(cls)}</a>' for k in siblings)
    out.append('<div class="related">')
    if rel_html:
        out.append(f"Other {esc(cls)} specs this phase: {rel_html}<br>")
    out.append(f'All lists: <a href="bis-all.html">BiS list index</a> · <a href="{esc(hash_url)}">interactive browser</a></div>')

    out.append('<div class="cta-wrap"><div class="newsletter-cta" '
               'data-heading="New BiS lists, straight to your inbox" '
               'data-sub="We publish lists phase by phase. Subscribe and get a mail when new BiS lists go live."></div></div>')
    out.append("</main>\n</body>\n</html>\n")
    return "\n".join(out)


def render_hub(entries):
    title = "All WoW Classic BiS Lists — Every Expansion, Phase & Spec | Boostyou.ai"
    description = (f"Index of all {len(entries)} published Best in Slot lists for WoW Classic, TBC, WotLK, "
                   "Cataclysm and MoP Classic — per phase and spec, with drop sources, enchants and gems.")
    jsonld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title,
              "url": f"{SITE}/content/bis-all.html", "about": "World of Warcraft Classic best in slot gear lists"}
    out = [head(title, description, "bis-all.html", jsonld)]
    out.append('<main class="page">')
    out.append('<div class="crumbs"><a href="../index.html">Home</a> › BiS Lists</div>')
    out.append("<h1>All BiS Lists</h1>")
    out.append(f'<p class="meta-line">{len(entries)} published lists · <a class="item" href="bis.html">'
               "Prefer picking your spec interactively? Open the BiS browser →</a></p>")
    groups = {}
    for key, d in entries:
        exp_label, phases = EXPANSIONS[d["expansion"]]
        groups.setdefault((exp_label, phases[d["phase"]]), []).append((key, d))
    for (exp_label, phase_label), items in groups.items():
        out.append(f'<div class="hub-group"><h2>{esc(exp_label)} — {esc(phase_label)}</h2><ul class="hub-list">')
        for key, d in sorted(items, key=lambda kd: (kd[1]["class"], kd[1]["spec"])):
            label = f"{spec_label(d['spec'])} {CLASS_LABELS[d['class']]}"
            draft = " (draft)" if d.get("status") == "draft" else ""
            out.append(f'<li><a href="bis-{key}.html">{esc(label)}</a>{draft}</li>')
        out.append("</ul></div>")
    out.append('<div class="cta-wrap"><div class="newsletter-cta" '
               'data-heading="New BiS lists, straight to your inbox" '
               'data-sub="We publish lists phase by phase. Subscribe and get a mail when new BiS lists go live."></div></div>')
    out.append("</main>\n</body>\n</html>\n")
    return "\n".join(out)


# ---------------------------------------------------------------- sitemap & llms.txt

SM_START, SM_END = "  <!-- bis-pages:start (generated by tools/bis_pages.py) -->", "  <!-- bis-pages:end -->"
LLMS_START, LLMS_END = "<!-- bis-pages:start (generated by tools/bis_pages.py) -->", "<!-- bis-pages:end -->"


def update_sitemap(entries):
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    today = date.today().isoformat()

    def url(loc, lastmod, prio):
        return (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
                f"    <changefreq>weekly</changefreq>\n    <priority>{prio}</priority>\n  </url>")

    block = [SM_START, url(f"{SITE}/content/bis-all.html", today, "0.9")]
    for key, d in entries:
        block.append(url(f"{SITE}/content/bis-{key}.html", d.get("updated", today), "0.8"))
    block.append(SM_END)
    block_text = "\n".join(block)

    pattern = re.compile(re.escape(SM_START) + r".*?" + re.escape(SM_END), re.S)
    if pattern.search(xml):
        xml = pattern.sub(lambda _: block_text, xml, count=1)
    else:
        xml = xml.replace("</urlset>", block_text + "\n\n</urlset>", 1)
    path.write_text(xml, encoding="utf-8")


def update_llms(entries):
    path = ROOT / "llms.txt"
    txt = path.read_text(encoding="utf-8")
    n = len(entries)
    phases = sorted({f"{EXPANSIONS[d['expansion']][0]} {d['phase']}" for _, d in entries})
    section = [LLMS_START, "", "## BiS Lists (PvE Best in Slot)", "",
               f"- [BiS list index]({SITE}/content/bis-all.html): {n} published lists — per-spec BiS gear "
               f"with exact drop sources, enchants and gems. Covered so far: {', '.join(phases)}. "
               "Individual pages: /content/bis-<expansion>-<phase>-<class>-<spec>.html, "
               "e.g. /content/bis-mop-p3-warrior-arms.html.",
               f"- [Interactive BiS browser]({SITE}/content/bis.html): same data, pick expansion → phase → class → spec.",
               f"- Raw data (JSON, one file per list): {SITE}/content/bis-data/<expansion>-<phase>-<class>-<spec>.json",
               "", LLMS_END]
    section_text = "\n".join(section)
    pattern = re.compile(re.escape(LLMS_START) + r".*?" + re.escape(LLMS_END), re.S)
    if pattern.search(txt):
        txt = pattern.sub(lambda _: section_text, txt, count=1)
    else:
        txt = txt.replace("## Optional", section_text + "\n\n## Optional", 1)
    path.write_text(txt, encoding="utf-8")


# ---------------------------------------------------------------- main

def main():
    entries = []
    for f in sorted(DATA.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        key = f"{d['expansion']}-{d['phase']}-{d['class']}-{d['spec']}"
        if f.stem != key:
            print(f"WARNING: {f.name} skipped (filename does not match content)")
            continue
        entries.append((key, d))

    all_keys = [k for k, _ in entries]
    for key, d in entries:
        (ROOT / "content" / f"bis-{key}.html").write_text(render_list_page(d, key, all_keys), encoding="utf-8")
    (ROOT / "content" / "bis-all.html").write_text(render_hub(entries), encoding="utf-8")

    update_sitemap(entries)  # news post pages are managed by tools/post_pages.py
    update_llms(entries)
    print(f"Generated {len(entries)} list pages + bis-all.html; sitemap.xml and llms.txt updated.")

    # generated pages are written without the site nav — re-stamp automatically
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "tools" / "stamp_nav.py")], check=True)


if __name__ == "__main__":
    sys.exit(main())
