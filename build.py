#!/usr/bin/env python3
"""
Build the academy website.

    python build.py                 build once into site/
    python build.py --serve         build, then serve site/ on localhost:8000
    python build.py --serve --watch rebuild whenever a source file changes
    python build.py --port 4000 --serve

How it works
------------
Pages live in pages/. Each one starts with a small front-matter block and is
poured into a layout from components/layouts/. Anything repeated - the nav, the
footer, a call-to-action band - lives once in components/ and is pulled in with
an include:

    <!-- @include components/nav.html -->

Includes can take arguments, which is how one component renders differently on
different pages:

    <!-- @include components/page-header.html {"title": "About", "tint": "pitch"} -->

Inside a component, {{ title }} prints an argument. Values from
site.config.json are available on every page, so the academy's name, email and
address are written down in exactly one place.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import pathlib
import re
import shutil
import socketserver
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
PAGES = ROOT / "pages"
COMPONENTS = ROOT / "components"
ASSETS = ROOT / "assets"
OUT = ROOT / "site"
CONFIG = ROOT / "site.config.json"

INCLUDE = re.compile(
    # Arguments may span several lines, but can never swallow a closing "-->",
    # so a stray directive inside a comment fails loudly instead of recursing.
    r"^([ \t]*)<!--\s*@include\s+(?P<path>[\w./\-]+)\s*"
    r"(?P<args>\{(?:(?!-->).)*?\})?\s*-->[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
VARIABLE = re.compile(r"\{\{\s*(?P<name>[\w.\-]+)\s*\}\}")
FRONT_MATTER = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)

MAX_INCLUDE_DEPTH = 12


class BuildError(Exception):
    pass


# ---------------------------------------------------------------- parsing ----

def parse_front_matter(text: str, source: pathlib.Path) -> tuple[dict, str]:
    """Pull `key: value` lines off the top of a page."""
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text

    data: dict[str, str] = {}
    for number, line in enumerate(match.group("body").splitlines(), start=2):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise BuildError(f"{source.name}:{number}: expected 'key: value', got {line!r}")
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip()

    return data, text[match.end():]


def indent_block(text: str, pad: str) -> str:
    if not pad:
        return text
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


@functools.lru_cache(maxsize=None)
def read(path: pathlib.Path) -> str:
    if not path.is_file():
        raise BuildError(f"missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def expand(text: str, scope: dict, origin: str, depth: int = 0) -> str:
    """Resolve @include directives, innermost arguments winning."""
    if depth > MAX_INCLUDE_DEPTH:
        raise BuildError(f"include nested more than {MAX_INCLUDE_DEPTH} deep in {origin} "
                         "- most likely a component includes itself")

    def replace(match: re.Match) -> str:
        pad, rel, raw_args = match.group(1), match.group("path"), match.group("args")
        try:
            args = json.loads(raw_args) if raw_args else {}
        except json.JSONDecodeError as exc:
            raise BuildError(f"{origin}: include arguments for {rel} are not valid JSON - {exc}") from exc

        child_scope = {**scope, **{str(k): v for k, v in args.items()}}
        body = expand(read(ROOT / rel), child_scope, rel, depth + 1)
        # Substitute now so an argument cannot leak out into the parent page.
        body = substitute(body, child_scope, rel, strict=False)
        return indent_block(body, pad)

    return INCLUDE.sub(replace, text)


def substitute(text: str, scope: dict, origin: str, strict: bool) -> str:
    unknown: set[str] = set()

    def replace(match: re.Match) -> str:
        name = match.group("name")
        if name in scope:
            value = scope[name]
            return "" if value is None else str(value)
        if name == "content":          # filled in by the layout step
            return match.group(0)
        unknown.add(name)
        return match.group(0) if strict else ""

    result = VARIABLE.sub(replace, text)
    if strict and unknown:
        raise BuildError(f"{origin}: no value for {', '.join(sorted('{{' + u + '}}' for u in unknown))}")
    return result


# ---------------------------------------------------------------- building ----

def load_config() -> dict:
    if not CONFIG.is_file():
        raise BuildError("site.config.json is missing - it holds the academy's name, "
                         "contact details and other one-place-only content")
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BuildError(f"site.config.json is not valid JSON - {exc}") from exc

    # Flatten one level of nesting so {"social": {"instagram": "..."}} reads as
    # {{ social.instagram }} in a template.
    for key, value in list(config.items()):
        if isinstance(value, dict):
            for inner, inner_value in value.items():
                config[f"{key}.{inner}"] = inner_value

    config["year"] = time.strftime("%Y")
    return config


def discard(path: pathlib.Path) -> None:
    """Delete a file, shrugging if something else is holding it open.

    This project can live inside a synced folder (OneDrive, Dropbox), and a
    sync client will occasionally have a file locked at exactly the wrong
    moment. A stale file left behind is never worth failing a build over.
    """
    try:
        path.unlink()
    except (PermissionError, OSError):
        pass


def sync_tree(source: pathlib.Path, target: pathlib.Path) -> int:
    """Mirror `source` into `target`, touching only what actually changed.

    Copying just the changed files (rather than deleting the whole tree and
    starting again) keeps rebuilds quick and stops a sync client from fighting
    us over a directory it has open.
    """
    target.mkdir(parents=True, exist_ok=True)
    wanted: set[pathlib.Path] = set()
    copied = 0

    for item in source.rglob("*"):
        relative = item.relative_to(source)
        destination = target / relative
        wanted.add(relative)

        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue

        fresh = destination.is_file()
        if fresh:
            old, new = destination.stat(), item.stat()
            fresh = old.st_size == new.st_size and old.st_mtime >= new.st_mtime

        if not fresh:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)
            copied += 1

    # Remove anything that is no longer in the source tree.
    for item in target.rglob("*"):
        if item.is_file() and item.relative_to(target) not in wanted:
            discard(item)

    return copied


def build_page(path: pathlib.Path, config: dict) -> str:
    front_matter, body = parse_front_matter(read(path), path)

    scope = {
        **config,
        "nav": "",
        "body_class": "",
        "description": config.get("default_description", ""),
        **front_matter,
    }
    scope.setdefault("title", path.stem.replace("-", " ").title())
    scope["page_title"] = (
        config.get("academy_name", "")
        if front_matter.get("nav") == "home"
        else f"{scope['title']} - {config.get('academy_name', '')}"
    )

    content = expand(body, scope, path.name)

    layout_name = front_matter.get("layout", "base")
    layout = read(COMPONENTS / "layouts" / f"{layout_name}.html")
    html = layout.replace("{{ content }}", content).replace("{{content}}", content)
    html = expand(html, scope, f"layouts/{layout_name}.html")

    return substitute(html, scope, path.name, strict=True).strip() + "\n"


def build(verbose: bool = True) -> int:
    read.cache_clear()
    config = load_config()

    pages = sorted(PAGES.glob("*.html"))
    if not pages:
        raise BuildError("no pages found in pages/")

    OUT.mkdir(parents=True, exist_ok=True)

    built = {page.name for page in pages}
    for stale in OUT.glob("*.html"):
        if stale.name not in built:
            discard(stale)

    for page in pages:
        (OUT / page.name).write_text(build_page(page, config), encoding="utf-8")
        if verbose:
            print(f"  site/{page.name}")

    if ASSETS.exists():
        copied = sync_tree(ASSETS, OUT / "assets")
        if verbose:
            print(f"  site/assets/ ({copied} files updated)")

    for extra in ("robots.txt", "CNAME", "_headers", ".nojekyll"):
        source = ROOT / extra
        if source.is_file():
            shutil.copy2(source, OUT / extra)

    return len(pages)


# ----------------------------------------------------------------- serving ----

def sources() -> list[pathlib.Path]:
    found: list[pathlib.Path] = [CONFIG]
    for folder in (PAGES, COMPONENTS, ASSETS):
        found.extend(p for p in folder.rglob("*") if p.is_file())
    return found


def fingerprint() -> dict[pathlib.Path, float]:
    prints = {}
    for path in sources():
        try:
            prints[path] = path.stat().st_mtime
        except OSError:
            pass
    return prints


def serve(port: int, watch: bool) -> None:
    handler = functools.partial(QuietHandler, directory=str(OUT))
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"\nServing the site at http://localhost:{port}/  (ctrl+c to stop)")
        if not watch:
            httpd.serve_forever()
            return

        print("Watching for changes.\n")
        import threading
        threading.Thread(target=httpd.serve_forever, daemon=True).start()

        last = fingerprint()
        while True:
            time.sleep(0.6)
            current = fingerprint()
            if current == last:
                continue
            last = current
            stamp = time.strftime("%H:%M:%S")
            try:
                count = build(verbose=False)
                print(f"[{stamp}] rebuilt {count} pages")
            except BuildError as exc:
                print(f"[{stamp}] build failed: {exc}")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Same as the default, but without a log line for every asset, and with
    /about resolving to about.html so local URLs match a deployed host."""

    def log_message(self, fmt, *args):
        pass

    def send_response(self, *args, **kwargs):
        super().send_response(*args, **kwargs)
        self.send_header("Cache-Control", "no-store")

    def translate_path(self, path: str) -> str:
        resolved = super().translate_path(path)
        candidate = pathlib.Path(resolved)
        if not candidate.exists() and not candidate.suffix:
            with_html = candidate.with_suffix(".html")
            if with_html.is_file():
                return str(with_html)
        return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the academy website.")
    parser.add_argument("--serve", action="store_true", help="serve site/ after building")
    parser.add_argument("--watch", action="store_true", help="rebuild when sources change")
    parser.add_argument("--port", type=int, default=8000, help="port for --serve (default 8000)")
    args = parser.parse_args()

    try:
        print("Building the site...")
        count = build()
        print(f"\nBuilt {count} pages into site/")
    except BuildError as exc:
        print(f"\nBuild failed: {exc}", file=sys.stderr)
        return 1

    if args.serve:
        try:
            serve(args.port, args.watch)
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
