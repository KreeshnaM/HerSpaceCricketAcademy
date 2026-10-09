# [Academy Name] Girls Cricket Academy — website

A static website. No Node, no npm, no build tools to install — just Python 3,
which this machine already has.

---

## Run it

```bash
python build.py --serve --watch
```

Then open <http://localhost:8000>. With `--watch`, the site rebuilds whenever
you save a file, so you can leave it running while you edit.

To build once without serving:

```bash
python build.py
```

The finished, deployable website appears in `site/`.

---

## The first things to change

Everything that needs your real information is wrapped in `[square brackets]`.

**1. Fill in `site.config.json`.** The academy's name, email, phone, ground,
training times, ages, cost and social links all live in that one file. Change
them there and they update on every page.

**2. See what is still unfinished.** Add `?placeholders` to any URL — e.g.
<http://localhost:8000/index.html?placeholders> — and every unfinished detail
is highlighted in yellow. Or run:

```bash
python scripts/check_site.py
```

which lists the count per page, alongside real errors like a broken link or an
image with no alt text.

**3. Replace the photographs.** See [IMAGES.md](IMAGES.md). Every image is a
stock placeholder with a descriptive filename; you overwrite the file, keep the
name, and change no code.

**4. Connect the forms.** Paste a form endpoint into `form_endpoint` in
`site.config.json` (Formspree, Basin, Netlify Forms — anything that accepts a
POST). Until you do, the three forms fall back to opening the visitor's email
app with their message already written, so nothing is ever lost.

---

## How the site is put together

```
build.py              the build. Reads pages/ + components/, writes site/
site.config.json      every real detail, in one place
pages/                one file per page. Front matter, then content
components/           anything used more than once
  layouts/base.html     the HTML shell every page is poured into
  nav.html, footer.html
  page-header.html      the title band on inner pages
  section-*.html        whole sections shared between pages
  form-*.html           the three forms
assets/
  css/  tokens.css      colours, type, spacing - change the look here
        base.css        reset, typography, focus states
        layout.css      containers, section rhythm, cricket furniture
        components.css  buttons, nav, cards, photos, forms
        sections.css    the individual page sections
  js/   nav.js reveal.js counters.js forms.js
  images/               photographs, organised by where they are used
scripts/
  fetch_placeholder_images.py   re-downloads the stock placeholders
  check_site.py                 accessibility and link checks
site/                 the built website. Never edit by hand
```

### Pages

A page is front matter plus HTML:

```html
---
title: Academy
nav: academy
description: Used for search results and link previews.
---

<section class="section">...</section>
```

`nav` is what highlights the right link in the navigation.

### Components

Anything repeated is pulled in with an include:

```html
<!-- @include components/footer.html -->
```

Includes can take arguments, which is how one component renders differently on
different pages:

```html
<!-- @include components/page-header.html {"eyebrow": "About us", "title": "Our story", "lede": "One sentence."} -->
```

Inside the component, `{{ title }}` prints the argument. Values from
`site.config.json` are available everywhere, so `{{ email }}` works on any
page.

### Adding a page

1. Copy an existing file in `pages/` and change its front matter.
2. Add it to the list in `components/nav.html` and `components/footer.html`.
3. Add a line to the `body[data-page="..."]` blocks in `components.css` if you
   want the nav link to highlight.
4. Run the build.

---

## Deploying

`site/` is a plain folder of HTML. Any static host will take it.

- **Netlify or Cloudflare Pages** — drag the `site/` folder onto their dashboard.
  Or connect the repo with build command `python build.py` and publish
  directory `site`.
- **GitHub Pages** — commit `site/` and point Pages at it. The `.nojekyll` file
  is already there so GitHub serves the folder as-is.
- **Anywhere else** — upload the contents of `site/` by FTP.

Before you launch, set `site_url` in `site.config.json` and check
`python scripts/check_site.py` reports zero placeholders.

---

## Notes on the design

- **Colour** is warm cream paper and deep plum ink, with five joyful accents.
  All of it comes from `assets/css/tokens.css`.
- **Contrast** — every text-and-background pairing on the site meets WCAG AA.
  If you change a colour, re-check it; the comments in `tokens.css` explain the
  pairings that are close to the line.
- **Type** is Fraunces (headings) and Plus Jakarta Sans (body), from Google
  Fonts.
- **Animation** is deliberately light: the headline arrives, sections fade up as
  you scroll, numbers count, buttons press in. Everything respects
  `prefers-reduced-motion`, and nothing depends on JavaScript to become
  readable.
- **Accessibility** — keyboard navigable throughout, visible focus rings, a skip
  link, labelled forms, alt text on every image, and one `h1` per page.
