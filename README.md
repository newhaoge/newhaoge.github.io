# haozheng.us

Content lives in `data/*.json`. Design lives in `assets/`. Running `build.py`
combines them into plain static HTML in `dist/`, which is what you upload.

Nothing outside the Python standard library is needed. No npm, no Ruby, no
accounts.

```
python3 build.py           # write dist/
python3 build.py --serve   # write dist/ and preview at http://localhost:8000
```

---

## Folder map

```
├── build.py               the build script — run this after any edit
├── data/                  ← everything you will normally change
│   ├── site.json          name, title, email, address, About text, lab text
│   ├── news.json          dated updates
│   ├── publications.json  papers, journals, patents
│   ├── people.json        students, alumni, sponsors
│   ├── courses.json       teaching
│   ├── service.json       editorial, program committees, reviewing
│   └── awards.json        awards and honors
├── templates/
│   └── base.html          the shell every page shares: head, nav, footer
├── assets/                copied into dist/ untouched
│   ├── css/site.css       all styling
│   ├── js/site.js         search, filters, portrait fallback
│   ├── js/fabric.js       the animated hero background
│   ├── img/               your photo + sponsor logos
│   └── files/             paper PDFs
└── dist/                  generated — never edit by hand, never commit
```

`dist/` is disposable. Delete it any time and rebuild.

---

## Common edits

### Add a news item

Add one object to the top of `data/news.json`. Entries are re-sorted by date
automatically, so exact position does not matter.

```json
{
  "date": "2026-09",
  "title": "Two papers accepted at HPCA ’27",
  "detail": "Optional second line, shown only on the news page."
}
```

This appears in three places at once: the news page, the year menu on that
page, and the feed on the home page. The home feed shows anything from
`home_feed_from_year` in `site.json` onward — currently 2024.

### Add a publication

Add an object to the right year group in `data/publications.json`.

```json
{
  "venue": "ISCA’27",
  "type": "conf",
  "tier": "top",
  "selected": true,
  "title": "Paper title here",
  "authors": ["Student Name", "Hao Zheng"],
  "published": "ACM/IEEE International Symposium on Computer Architecture (ISCA) · City · Jun 2027",
  "links": [{"label": "PDF", "url": "assets/files/paper.pdf"}]
}
```

| field | what it does |
|---|---|
| `venue` | the tag on the left |
| `type` | `conf`, `journal`, or `patent` — drives the filter buttons |
| `tier` | `"top"` turns the tag amber; omit otherwise |
| `selected` | `true` puts it in the six-item list on the home page |
| `authors` | a list — your name is bolded automatically, no markup needed |
| `links` | optional; omit the key entirely if there are none |
| `note` | optional, e.g. `"* co-first authors"` |

To start a new year, copy an existing `{"label": ..., "items": [...]}` block to
the top of `groups`.

### Add a student, alumnus, or sponsor

`data/people.json`, under `phd`, `undergrad`, `alumni`, or `sponsors`. When a
student graduates, move their object from `phd` to `alumni` and give it a
`dest` line.

### Change the About text or any other prose

`data/site.json`. HTML is allowed inside any text field, so links and `<em>`
work as expected.

---

## Files you need to supply

These are referenced by the data files but were not part of the migration:

- `assets/img/hao-zheng.jpg` — your portrait, roughly 3:4. Until it exists the
  site shows an `HZ` monogram instead, so nothing breaks.
- `assets/img/sponsors/` — `nsf.png`, `doe.png`, `darpa.png`, `nih.png`,
  `l3harris.svg`, `arilinc.png`, `sponsor.png`, `xilinx.jpg`, `nvidia.png`.
  Copy these from your old site's `assets/images/` and rename. One logo I could
  not identify is currently labelled "Research sponsor" in `people.json` —
  correct that name when you rename its file.
- `assets/files/` — the eight paper PDFs from your old site's `assets/files/`.

---

## Deploying

Upload the **contents** of `dist/` to your web root. That is the whole deploy
step — the output is ordinary HTML, CSS, JS, and images with no server
requirements.

If you keep this in Git, add a `.gitignore` containing `dist/`.

---

## Gotchas

**JSON is strict.** No trailing comma after the last item in a list, and use
straight `"` quotes around keys and values. If you get it wrong, `build.py`
prints the file, line, and column rather than a stack trace.

**Curly quotes and en dashes** can be pasted directly into the JSON — the files
are UTF-8. Prefer `’` over `'` in titles for typographic consistency.

**Preview with `--serve`, not by double-clicking.** Opening `dist/index.html`
from the file system works, but relative paths behave more like the real server
under `--serve`.

---

## If you later want a framework

This build script is about 300 readable lines and has no dependencies, which is
its main virtue. If you eventually want themes, plugins, or automatic
deployment, the data files here port cleanly to:

- **Eleventy** — closest match. `data/*.json` drops into `_data/` almost
  unchanged; `templates/base.html` becomes a Nunjucks layout. Needs Node.
- **Hugo** — fastest, ships as a single binary, no runtime to install. Content
  would move to `data/` and templates to Go templates.
- **Jekyll on GitHub Pages** — rebuilds and deploys on every push, so you could
  edit `news.json` in the GitHub web UI from a phone and the site updates
  itself. Slowest builds, but the least local tooling.

All three produce the same kind of static output, so the CSS and JS in
`assets/` carry over untouched in every case.
