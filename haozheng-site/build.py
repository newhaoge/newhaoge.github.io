#!/usr/bin/env python3
"""
Build the site.

    python3 build.py            # write everything into dist/
    python3 build.py --serve    # build, then serve dist/ at http://localhost:8000

Reads content from data/*.json and the page shell from templates/base.html,
writes plain static HTML into dist/. Nothing outside the Python standard
library is required.

To change content, edit the JSON files in data/ and run this again.
To change design, edit assets/css/site.css.
To change page structure, edit the render_* functions below.
"""

import argparse
import datetime
import html
import json
import re
import shutil
import sys
from urllib.parse import quote_plus
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
OUT = ROOT / "dist"

# Author name to highlight in publication lists.
ME = "Hao Zheng"

# slug, nav label, page title suffix
PAGES = [
    ("index.html", "Home", None),
    ("research.html", "Research", "Research"),
    ("publications.html", "Publications", "Publications"),
    ("lab.html", "Lab", "iCAT Lab"),
    ("teaching.html", "Teaching", "Teaching"),
    ("service.html", "Service", "Service &amp; Awards"),
    ("news.html", "News", "News"),
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def load(name):
    path = DATA / f"{name}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Missing data file: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"{path.name} is not valid JSON — line {e.lineno}, column {e.colno}: {e.msg}\n"
                 f"  (a stray or missing comma is the usual cause)")


def fill(template, **values):
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def long_date(iso):
    """'2026-07' -> 'Jul 2026'"""
    parts = iso.split("-")
    if len(parts) >= 2:
        return f"{MONTHS[int(parts[1])]} {parts[0]}"
    return iso


def short_date(iso):
    """'2026-07' -> '07/2026'"""
    parts = iso.split("-")
    if len(parts) >= 2:
        return f"{parts[1]}/{parts[0]}"
    return iso


def authors_html(names):
    return ", ".join(f"<b>{n}</b>" if n.strip().rstrip("*") == ME else n for n in names)


# --------------------------------------------------------------------------
# page sections
# --------------------------------------------------------------------------

def render_home(site, news, pubs):
    hero = site["hero"]
    creds = "\n".join(f"            <li>{c}</li>" for c in hero["credentials"])
    about = "\n".join(f"        <p>{p}</p>" for p in site["about"])

    cutoff = site.get("home_feed_from_year", 0)
    feed_rows = []
    for item in news:
        if int(item["date"][:4]) < cutoff:
            continue
        feed_rows.append(
            f'          <li><time datetime="{item["date"]}">{short_date(item["date"])}</time>'
            f'<p>{item["title"]}</p></li>')
    feed = "\n".join(feed_rows)

    featured_venues = ("ISCA", "MICRO", "HPCA")
    picks = [
        p
        for group in pubs["groups"]
        if str(group["label"]) in {"2023", "2024", "2025", "2026"}
        for p in group["items"]
        if p["venue"].upper().startswith(featured_venues)
    ]
    selected = "\n".join(publication_html(p) for p in picks)

    return f"""
<div class="die-panel">
  <div class="veil" aria-hidden="true"></div>
  <div class="wrap">
    <div class="hero">
      <div>
        <p class="eyebrow">{hero["eyebrow"]}</p>
        <h1>{site["name"].replace(" ", "&nbsp;")}</h1>
        <p class="role">{site["dept"]}<span class="sep">/</span>{site["university"]}</p>
        <p class="lede">{hero["lede"]}</p>
        <ul class="creds">
{creds}
        </ul>
      </div>
      <figure class="portrait">
        <div class="frame">
          <img id="portrait" src="{site["photo"]}" alt="Portrait of {site["name"]}"
               width="600" height="600" decoding="async" fetchpriority="high">
          <div class="fallback" id="portraitFallback" hidden aria-hidden="true">{site["monogram"]}</div>
        </div>
        <figcaption>{site["photo_caption"]}</figcaption>
      </figure>
    </div>
  </div>
</div>

<div class="wrap" style="padding-top:clamp(48px,7vw,84px);padding-bottom:clamp(46px,7vw,84px)">
  <div class="about">
    <p class="eyebrow">About</p>
    <div class="prose">
{about}
    </div>
  </div>

  <hr class="rule">

  <div class="sec-head">
    <p class="eyebrow">News</p>
    <h2 class="sec-title">Latest updates</h2>
    <p class="sec-note">Papers, grants, and awards from the lab. <a href="news.html">Open the full timeline &rarr;</a></p>
  </div>
  <div class="feedwrap">
    <div class="feed" id="feed" tabindex="0" role="region" aria-label="Recent lab news">
      <ul>
{feed}
      </ul>
    </div>
  </div>

  <hr class="rule">

  <div class="sec-head">
    <p class="eyebrow">Selected work</p>
    <h2 class="sec-title">Selected Recent Publications</h2>
    <p class="sec-note">The complete list, with PDFs and code, is on the <a href="publications.html">publications page</a>.</p>
  </div>
  <div>
{selected}
  </div>
  <div class="btnrow"><a class="btn ghost" href="publications.html">All publications &amp; patents</a></div>

  <hr class="rule">

  <div class="panel accent chamfer">
    <h3>Joining <a href="https://ucf-icat.github.io/">{site["lab"]["short_name"]}</a></h3>
    <p>Graduate research and teaching assistantships are available for prospective Ph.D. students.
       If the work here interests you, send a CV and transcripts to
       <a href="mailto:{site["email"]}">{site["email"]}</a>.</p>
    <div class="btnrow"><a class="btn" href="https://ucf-icat.github.io/">What the lab is like</a></div>
  </div>
</div>
"""


def publication_html(p):
    attrs = f' data-type="{p.get("type", "conf")}"'
    if p.get("tier"):
        attrs += f' data-tier="{p["tier"]}"'
    note = f' <span style="color:var(--ink-3)">({p["note"]})</span>' if p.get("note") else ""
    pub_links = list(p.get("links", []))
    if not any(link["label"].lower() == "pdf" for link in pub_links):
        query = quote_plus(f'"{html.unescape(p["title"])}" PDF')
        pub_links.append({"label": "PDF", "url": f"https://scholar.google.com/scholar?q={query}"})
    pub_links.append({"label": "BibTeX", "url": f'assets/files/bibtex/{p["bib_id"]}.bib', "download": True})
    anchors = "".join(
        f'<a href="{link["url"]}"' + (' download' if link.get("download") else '') + f'>{link["label"]}</a>'
        for link in pub_links
    )
    links = f'\n          <p class="pub-links">{anchors}</p>'
    return f"""        <article class="pub"{attrs}>
          <div><span class="tag">{p["venue"]}</span></div>
          <div>
            <h3 class="pub-title">{p["title"]}</h3>
            <p class="pub-authors">{authors_html(p["authors"])}{note}</p>
            <p class="pub-venue">{p["published"]}</p>{links}
          </div>
        </article>"""


def render_research(research, pubs):
    by_title = {p["title"]: p for group in pubs["groups"] for p in group["items"]}

    sections = []
    for d in research["directions"]:
        threads = "\n".join(
            f'        <li><span class="idx">{t["label"]}</span><span>{t["text"]}</span></li>'
            for t in d["threads"])

        papers_block = ""
        found = [by_title[title] for title in d.get("papers", []) if title in by_title]
        if found:
            papers = "\n".join(publication_html(p) for p in found)
            papers_block = f"""
    <h3 class="yearhead" style="margin-top:34px">Selected publications</h3>
    <div class="paperset">
{papers}
    </div>"""

        sections.append(f"""  <div class="direction">
    <div class="direction-head">
      <span class="dnum">{d["num"]}</span>
      <div>
        <p class="eyebrow">{d["eyebrow"]}</p>
        <h2 class="sec-title">{d["title"]}</h2>
      </div>
    </div>
    <div class="prose">
      <p>{d["summary"]}</p>
    </div>
    <ul class="topics" style="margin-top:22px">
{threads}
    </ul>{papers_block}
  </div>""")

    body = "\n\n  <hr class=\"rule\">\n\n".join(sections)
    intro = research["intro"]
    return f"""
<div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">{intro["eyebrow"]}</p>
    <h2 class="sec-title">{intro["title"]}</h2>
    <p class="sec-note">{intro["lede"]}</p>
  </div>

{body}

  <hr class="rule">

  <div class="panel accent chamfer">
    <h3>Working across the stack</h3>
    <p>All three directions share the same lab and the same students — see the full record on the
       <a href="publications.html">publications page</a>, or read about
       <a href="https://ucf-icat.github.io/">joining the iCAT lab</a>.</p>
  </div>
</div>
"""


def render_publications(pubs):
    groups = []
    for group in pubs["groups"]:
        items = "\n".join(publication_html(p) for p in group["items"])
        groups.append(f"""      <div class="yeargroup"><h3 class="yearhead">{group["label"]}</h3>
{items}
      </div>""")
    body = "\n\n".join(groups)
    return f"""
<div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Publications</p>
    <h2 class="sec-title">Papers, journals, and patents</h2>
    <p class="sec-note">Venues marked in amber are top-tier computer science conferences as listed on
      <a href="https://csrankings.org/">csrankings.org</a>. Search by title, author, or venue.</p>
  </div>

  <div class="pubtools">
    <input class="pubsearch" id="pubsearch" type="search" placeholder="Search publications…" aria-label="Search publications">
    <div class="filters" role="group" aria-label="Filter publications">
      <button data-filter="all" aria-pressed="true">All</button>
      <button data-filter="top" aria-pressed="false">Top-tier</button>
      <button data-filter="conf" aria-pressed="false">Conference</button>
      <button data-filter="journal" aria-pressed="false">Journal</button>
      <button data-filter="patent" aria-pressed="false">Patents</button>
    </div>
    <span class="count" id="pubcount"></span>
  </div>

  <div id="publist">

{body}

  </div>
  <p class="empty" id="pubempty" hidden>No publications match that search.</p>
</div>
"""


def render_lab(site, people):
    lab = site["lab"]
    reqs = "\n".join(
        f'        <li><span class="idx">{r["label"]}</span><span>{r["text"]}</span></li>'
        for r in lab["requirements"])
    prospective = "\n".join(f"        <p>{p}</p>" for p in lab["prospective"])

    def card_list(members):
        return "\n".join(
            "      <li class=\"card\">\n"
            f"        <h4>{m['name']}</h4>\n"
            + (f'        <p class="meta">{m["meta"]}</p>\n' if m.get("meta") else "")
            + (f'        <p class="honors">{m["honors"]}</p>\n' if m.get("honors") else "")
            + "      </li>"
            for m in members)

    alumni = "\n".join(
        f'      <li>{a["name"]}<span class="dest">{a["dest"]}</span></li>' for a in people["alumni"])
    sponsors = "\n".join(
        f'      <div><img src="{s["img"]}" alt="{s["name"]}" loading="lazy" '
        f'onerror="this.hidden=true;this.nextElementSibling.hidden=false">'
        f'<span hidden>{s["name"]}</span></div>'
        for s in people["sponsors"])

    return f"""
<div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">{lab["short_name"]}</p>
    <h2 class="sec-title">{lab["full_name"]}</h2>
    <p class="sec-note">{lab["intro"]}</p>
  </div>

  <div class="panel accent chamfer" style="margin-bottom:clamp(34px,5vw,54px)">
    <h3>{lab["prospective_heading"]}</h3>
    <div class="prose">
{prospective}
    </div>
    <ul class="topics" style="margin-top:18px">
{reqs}
    </ul>
    <div class="prose" style="margin-top:20px"><p>{lab["closing"]}</p></div>
  </div>

  <h3 class="yearhead">Ph.D. students</h3>
  <ul class="cards" style="margin-top:18px">
{card_list(people["phd"])}
  </ul>

  <h3 class="yearhead">Undergraduate researchers</h3>
  <ul class="cards" style="margin-top:18px">
{card_list(people["undergrad"])}
  </ul>

  <h3 class="yearhead">Alumni</h3>
  <ul class="alumni" style="margin-top:18px">
{alumni}
  </ul>

  <h3 class="yearhead">Research support</h3>
  <div class="sponsors" style="margin-top:18px">
{sponsors}
  </div>
</div>
"""


def render_teaching(site, courses):
    cards = "\n".join(f"""    <div class="course">
      <p class="code">{c["code"]}</p>
      <h3>{c["title"]}</h3>
      <p>{c["meta"]}</p>
    </div>""" for c in courses)
    panel = site["teaching_panel"]
    return f"""
<div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Teaching</p>
    <h2 class="sec-title">Courses at {site["university"]}</h2>
    <p class="sec-note">{site["teaching_note"]}</p>
  </div>
  <div class="courses">
{cards}
  </div>
  <div class="panel chamfer" style="margin-top:clamp(30px,4vw,44px)">
    <h3>{panel["heading"]}</h3>
    <p>{panel["body"]}</p>
  </div>
</div>
"""


def render_service(site, service, awards):
    rows = "\n".join(f"      <dt>{s['label']}</dt>\n      <dd>{s['body']}</dd>" for s in service)
    items = "\n".join(
        f'    <li><span class="yr">{a["year"]}</span><span>{a["title"]}'
        + (f'<span class="note">{a["note"]}</span>' if a.get("note") else "")
        + "</span></li>" for a in awards)
    panel = site["service_panel"]
    return f"""
<div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">Professional activities</p>
  </div>

  <dl class="deflist">
{rows}
  </dl>

  <div class="panel accent chamfer" style="margin-top:clamp(30px,4vw,44px)">
    <h3>{panel["heading"]}</h3>
    <p>{panel["body"]}</p>
  </div>

  <h3 class="yearhead">Awards &amp; honors</h3>
  <ul class="plainlist" style="margin-top:16px">
{items}
  </ul>
</div>
"""


def render_news(news):
    rows = []
    for item in news:
        extra = ""
        if item.get("detail"):
            extra += f'<p>{item["detail"]}</p>'
        if item.get("list"):
            entries = "".join(f"<li>{x}</li>" for x in item["list"])
            extra += f"<ol>{entries}</ol>"
        rows.append(f'    <li><time datetime="{item["date"]}">{long_date(item["date"])}</time>'
                    f'<div><h3>{item["title"]}</h3>{extra}</div></li>')
    body = "\n".join(rows)
    return f"""
<div class="wrap">
  <div class="sec-head">
    <p class="eyebrow">News</p>
    <h2 class="sec-title">A record of what the lab has been doing</h2>
  </div>
  <div class="newstools">
    <label for="newsyear">Show</label>
    <select class="newsselect" id="newsyear">
      <option value="all">All years</option>
    </select>
    <span class="count" id="newscount"></span>
  </div>
  <ul class="timeline">
{body}
  </ul>
</div>
"""


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def prepare_bibtex(pubs):
    """Assign stable citation IDs and write one downloadable BibTeX file per entry."""
    bib_dir = OUT / "assets" / "files" / "bibtex"
    bib_dir.mkdir(parents=True, exist_ok=True)
    used = set()
    for group in pubs["groups"]:
        fallback_year = str(group["label"])[:4] if str(group["label"])[:4].isdigit() else ""
        for p in group["items"]:
            year_match = re.search(r"\b(19|20)\d{2}\b", p.get("published", ""))
            year = year_match.group(0) if year_match else fallback_year or "n.d."
            first_author = html.unescape(p["authors"][0]).replace("*", "").strip().split()[-1]
            title_word = re.sub(r"[^A-Za-z0-9]", "", html.unescape(p["title"]).split()[0]) or "work"
            base = re.sub(r"[^A-Za-z0-9]", "", f"{first_author}{year}{title_word}")
            cite_id = base
            suffix = 2
            while cite_id.lower() in used:
                cite_id = f"{base}{suffix}"
                suffix += 1
            used.add(cite_id.lower())
            p["bib_id"] = cite_id
            entry_type = "article" if p.get("type") == "journal" else "misc" if p.get("type") == "patent" else "inproceedings"
            venue_field = "journal" if entry_type == "article" else "booktitle" if entry_type == "inproceedings" else "note"
            def clean(value):
                return html.unescape(str(value)).replace("{", "\\{").replace("}", "\\}")
            bib = (
                f"@{entry_type}{{{cite_id},\n"
                f"  title = {{{clean(p['title'])}}},\n"
                f"  author = {{{' and '.join(clean(a).replace('*', '') for a in p['authors'])}}},\n"
                f"  {venue_field} = {{{clean(p['published'])}}},\n"
                f"  year = {{{year}}}\n"
                f"}}\n"
            )
            (bib_dir / f"{cite_id}.bib").write_text(bib, encoding="utf-8")

def nav_html(current):
    out = []
    for slug, label, _ in PAGES:
        if slug == "lab.html":
            out.append('      <a href="https://ucf-icat.github.io/">Lab</a>')
            continue
        mark = ' aria-current="page"' if slug == current else ""
        out.append(f'      <a href="{slug}"{mark}>{label}</a>')
    return "\n".join(out)


def write_page(shell, site, slug, title, content, scripts="", wrap=True):
    address = "\n".join(f"          {line}<br>" for line in site["address"])
    elsewhere = "\n".join(
        f'          <li><a href="{l["url"]}">{l["label"]}</a></li>' for l in site["elsewhere"])
    if wrap:
        content = f'<section class="view">{content}</section>'
    canonical_url = site["base_url"].rstrip("/") + ("/" if slug == "index.html" else f"/{slug}")
    html = fill(
        shell,
        title=title,
        description=site["meta_description"],
        base_url=site["base_url"],
        canonical_url=canonical_url,
        slug="" if slug == "index.html" else slug,
        photo=site["photo"],
        monogram=site["monogram"],
        name=site["name"],
        email=site["email"],
        nav=nav_html(slug),
        content=content,
        address=address,
        map_url=site["map_url"],
        elsewhere=elsewhere,
        footer_note=site["footer_note"],
        colophon=site["colophon"],
        year=datetime.date.today().year,
        scripts=scripts,
    )
    (OUT / slug).write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="serve dist/ after building")
    args = parser.parse_args()

    site = load("site")
    news = sorted(load("news"), key=lambda n: n["date"], reverse=True)
    pubs = load("publications")
    people = load("people")
    courses = load("courses")
    service = load("service")
    awards = load("awards")
    research = load("research")

    shell = (TEMPLATES / "base.html").read_text(encoding="utf-8")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ASSETS, OUT / "assets")
    shutil.copy2(ROOT / "CNAME", OUT / "CNAME")
    shutil.copy2(ROOT / ".nojekyll", OUT / ".nojekyll")
    prepare_bibtex(pubs)

    site_js = '<script src="assets/js/site.js" defer></script>'
    home_js = site_js

    full = f'{site["name"]} — {site["role"]}, {site["dept"]}, {site["university"]}'
    write_page(shell, site, "index.html", full, render_home(site, news, pubs), home_js, wrap=False)
    write_page(shell, site, "research.html", f'Research — {site["name"]}',
               render_research(research, pubs))
    write_page(shell, site, "publications.html", f'Publications — {site["name"]}',
               render_publications(pubs), site_js)
    write_page(shell, site, "lab.html", f'{site["lab"]["short_name"]} Lab — {site["name"]}',
               render_lab(site, people))
    write_page(shell, site, "teaching.html", f'Teaching — {site["name"]}',
               render_teaching(site, courses))
    write_page(shell, site, "service.html", f'Service &amp; Awards — {site["name"]}',
               render_service(site, service, awards))
    write_page(shell, site, "news.html", f'News — {site["name"]}', render_news(news), site_js)

    count = sum(len(g["items"]) for g in pubs["groups"])
    print(f"Built {len(PAGES)} pages into {OUT}")
    print(f"  {count} publications · {len(news)} news items · "
          f"{len(people['phd']) + len(people['undergrad'])} current members · {len(awards)} awards")

    if args.serve:
        import http.server, socketserver, functools
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            print("Serving http://localhost:8000  (Ctrl-C to stop)")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
