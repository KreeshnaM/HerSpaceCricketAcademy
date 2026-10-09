#!/usr/bin/env python3
"""
Check the built site for the mistakes that are easy to make and hard to see.

    python build.py && python scripts/check_site.py

Checks, per page:
  * no {{ placeholders }} left unresolved by the build
  * every <img> has alt text and explicit width/height
  * every local src/href points at a file that exists
  * every internal link resolves, including its #anchor
  * every form control has a label, aria-label or title
  * heading levels never skip (h1 -> h3)
  * exactly one <h1>
  * no duplicate id attributes

It also counts the [square bracket] placeholders still awaiting real content,
which is a to-do list rather than an error.

Exit code is 1 if anything failed, so this works in CI.
"""

from __future__ import annotations

import collections
import html.parser
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

SELF_CLOSING = {"img", "input", "br", "hr", "meta", "link", "source", "area"}
CONTROLS = {"input", "select", "textarea"}
NO_LABEL_NEEDED = {"hidden", "submit", "reset", "button", "image"}


class PageParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[dict] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.headings: list[tuple[int, int]] = []     # (level, line)
        self.ids: list[tuple[str, int]] = []
        self.label_for: set[str] = set()
        self.controls: list[dict] = []
        self.label_depth = 0
        self._heading: int | None = None

    def handle_starttag(self, tag: str, attrs_list: list) -> None:
        attrs = {k: (v or "") for k, v in attrs_list}
        line = self.getpos()[0]

        if "id" in attrs:
            self.ids.append((attrs["id"], line))

        if tag == "img":
            self.images.append({
                "src": attrs.get("src", ""),
                "alt": attrs.get("alt"),
                "width": attrs.get("width"),
                "height": attrs.get("height"),
                "line": line,
            })
            if attrs.get("src"):
                self.assets.append(attrs["src"])

        elif tag in {"script", "source"} and attrs.get("src"):
            self.assets.append(attrs["src"])

        elif tag == "link" and attrs.get("href") and "stylesheet" in attrs.get("rel", "") + attrs.get("as", ""):
            self.assets.append(attrs["href"])
        elif tag == "link" and attrs.get("rel", "").startswith("icon"):
            self.assets.append(attrs["href"])

        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

        elif tag == "label":
            self.label_depth += 1
            if attrs.get("for"):
                self.label_for.add(attrs["for"])

        elif tag in CONTROLS:
            self.controls.append({
                "tag": tag,
                "type": attrs.get("type", "text").lower(),
                "id": attrs.get("id", ""),
                "aria": attrs.get("aria-label", "") or attrs.get("title", ""),
                "wrapped": self.label_depth > 0,
                "line": line,
            })

        elif re.fullmatch(r"h[1-6]", tag):
            self._heading = int(tag[1])
            self.headings.append((self._heading, line))

        if tag in SELF_CLOSING:
            return

    def handle_endtag(self, tag: str) -> None:
        if tag == "label" and self.label_depth:
            self.label_depth -= 1


def anchors(page: pathlib.Path) -> set[str]:
    parser = PageParser()
    parser.feed(page.read_text(encoding="utf-8", errors="replace"))
    return {i for i, _ in parser.ids}


def check() -> int:
    pages = sorted(SITE.glob("*.html"))
    if not pages:
        print("No built pages found. Run `python build.py` first.")
        return 1

    anchor_cache = {page.name: anchors(page) for page in pages}
    problems: list[str] = []
    todo_total = 0

    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        parser = PageParser()
        parser.feed(text)
        issues: list[str] = []

        # --- unresolved template variables -------------------------------
        for leftover in sorted(set(re.findall(r"\{\{[^}]{0,60}\}\}", text))):
            issues.append(f"unresolved template variable {leftover}")

        # --- images ------------------------------------------------------
        for image in parser.images:
            where = f"line {image['line']} ({image['src'] or 'no src'})"
            if image["alt"] is None:
                issues.append(f"img with no alt attribute - {where}")
            elif not image["alt"].strip():
                issues.append(f"img with empty alt - {where}")
            if not image["width"] or not image["height"]:
                issues.append(f"img without width/height, will shift layout - {where}")

        # --- local assets exist ------------------------------------------
        for asset in parser.assets:
            if asset.startswith(("http://", "https://", "data:", "mailto:", "tel:", "//")):
                continue
            target = SITE / urllib.parse.unquote(asset.split("?")[0].split("#")[0])
            if not target.is_file():
                issues.append(f"missing file referenced: {asset}")

        # --- internal links ----------------------------------------------
        for href in parser.links:
            if href.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//")):
                continue
            if href.startswith("["):     # an unfilled placeholder URL
                continue
            path, _, fragment = href.partition("#")
            if path:
                target_name = pathlib.PurePosixPath(path).name
                if target_name not in anchor_cache:
                    issues.append(f"link to a page that does not exist: {href}")
                    continue
            else:
                target_name = page.name
            if fragment and fragment not in anchor_cache[target_name]:
                issues.append(f"link to a missing anchor: {href}")

        # --- form controls are labelled ----------------------------------
        for control in parser.controls:
            if control["type"] in NO_LABEL_NEEDED:
                continue
            labelled = (
                control["wrapped"]
                or control["aria"].strip()
                or (control["id"] and control["id"] in parser.label_for)
            )
            if not labelled:
                issues.append(
                    f"{control['tag']} with no label - line {control['line']}"
                    f"{' id=' + control['id'] if control['id'] else ''}"
                )

        # --- headings ----------------------------------------------------
        levels = [level for level, _ in parser.headings]
        h1s = levels.count(1)
        if h1s != 1:
            issues.append(f"page has {h1s} <h1> elements, expected exactly 1")
        previous = None
        for level, line in parser.headings:
            if previous is not None and level > previous + 1:
                issues.append(f"heading jumps from h{previous} to h{level} - line {line}")
            previous = level

        # --- duplicate ids ------------------------------------------------
        counts = collections.Counter(i for i, _ in parser.ids)
        for value, count in counts.items():
            if count > 1:
                issues.append(f"id \"{value}\" used {count} times")

        # --- content still to be written ---------------------------------
        todo = len(re.findall(r"\[[^\]\[<>{}]{2,90}\]", text))
        todo_total += todo

        status = f"{len(issues)} issue(s)" if issues else "clean"
        print(f"\n{page.name:20s} {status}, {todo} placeholder(s) to fill")
        for issue in issues:
            print(f"    - {issue}")
        problems.extend(f"{page.name}: {issue}" for issue in issues)

    print("\n" + "=" * 68)
    if problems:
        print(f"{len(problems)} issue(s) across {len(pages)} pages.")
    else:
        print(f"All {len(pages)} pages passed.")
    print(f"{todo_total} placeholders still waiting for real content "
          f"(see IMAGES.md and site.config.json).")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(check())
