#!/usr/bin/env python3
"""
Download the PLACEHOLDER photography for the academy site.

Everything this script downloads is free stock photography from Unsplash,
standing in until real academy photographs are available. The filenames
describe the shot that belongs in each slot, so replacing a placeholder is a
drag-and-drop: overwrite the file, keep the name, change no code.

    python scripts/fetch_placeholder_images.py

Add --force to re-download files that already exist.

See CREDITS.md for the source of every image and IMAGES.md for the full
replacement guide.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMAGES = ROOT / "assets" / "images"

UNSPLASH = "https://images.unsplash.com/photo-{id}?w={w}&h={h}&fit=crop&crop=faces,entropy&q=72&fm=jpg"

# (path, unsplash id, width, height, "the shot that belongs here")
MANIFEST: list[tuple[str, str, int, int, str]] = [
    # ---- Hero -------------------------------------------------------------
    ("hero/hero-batter-ready.jpg", "1785906359975-3b9e7fd8d230", 1100, 1375,
     "A girl in full kit, bat in hand, about to face up. Confident, not posed."),
    ("hero/hero-team-laughing.jpg", "1528024719646-5360a944bd74", 1000, 750,
     "Teammates on the boundary bench, mid-laugh. Friendship over technique."),
    ("hero/hero-high-five.jpg", "1611095966422-50a79dd5313b", 800, 800,
     "Two players high-fiving between overs."),

    # ---- Girls in action gallery -----------------------------------------
    ("action/action-batting-drive.jpg", "1785906359459-f531f678d991", 1000, 1250,
     "A batter just after making contact - bat high, eyes following the ball."),
    ("action/action-bowling-delivery.jpg", "1774285947510-3bdf68d9972c", 900, 1125,
     "A bowler at the top of her delivery stride, arm coming over."),
    ("action/action-fielding-ready.jpg", "1743343179056-d235b33c4f0c", 900, 1125,
     "Hands ready in the field, or a fielder balancing the ball after a catch."),
    ("action/action-team-huddle.jpg", "1752681304960-bd4e018a04bb", 1200, 800,
     "The team huddle before the first ball. Arms around shoulders."),
    ("action/action-celebration-hug.jpg", "1567989995326-46ed902b0494", 1100, 825,
     "Players piling in to celebrate a wicket or a win."),
    ("action/action-training-session.jpg", "1554539484-e4fab56d4a5c", 1200, 800,
     "A normal training night - cones out, everyone working."),
    ("action/action-coach-teaching.jpg", "1754547368658-eaca43a67f81", 1200, 800,
     "A volunteer coach showing a grip or a stance to a small group."),
    ("action/action-running-onto-field.jpg", "1598880513655-d1c6d4b2dfbf", 1200, 800,
     "Girls running onto the field at the start of a match."),
    ("action/action-girls-on-bench.jpg", "1528024522223-f295b5bae7b1", 1100, 733,
     "Waiting to bat, pads on, watching the game together."),
    ("action/action-laughing-teammates.jpg", "1565490129165-bd6a24996c25", 1000, 750,
     "Close in on two or three players laughing at something off-camera."),

    # ---- Academy / places -------------------------------------------------
    ("academy/academy-nets-training.jpg", "1587716856188-ef47793f3fb7", 1200, 800,
     "The nets at your ground, ideally with players in them."),
    ("academy/academy-ground-wide.jpg", "1746053301234-f7f95dc669e0", 1400, 800,
     "A wide shot of the home ground so parents recognise the place."),
    ("academy/academy-match-day.jpg", "1779623283546-2f337cf24c85", 1400, 800,
     "Match day from the boundary - players out, families watching."),

    # ---- Player stories ---------------------------------------------------
    ("stories/story-player-01.jpg", "1754951876112-1846e4baed27", 560, 560,
     "Headshot for the first player story. Relaxed and smiling, not a school photo."),
    ("stories/story-player-02.jpg", "1743342399580-ce568503049a", 560, 560,
     "Headshot for the second player story - holding a ball works well."),
    ("stories/story-player-03.jpg", "1774285947226-1b7d038507d6", 560, 560,
     "Headshot for the third player story."),

    # ---- Coaches / volunteers --------------------------------------------
    ("coaches/coach-01.jpg", "1659081422899-379c50e7a7b5", 640, 800,
     "Volunteer coach portrait."),
    ("coaches/coach-02.jpg", "1611095968462-3dc56b14454a", 640, 800,
     "Volunteer coach portrait."),
    ("coaches/coach-03.jpg", "1510947565940-a38e2443c426", 640, 800,
     "Volunteer coach or team manager portrait."),

    # ---- Cricket texture / detail shots ----------------------------------
    ("texture/cricket-ball-grass.jpg", "1531415074968-036ba1b575da", 1400, 800,
     "A cricket ball sitting in the grass. Used as a section background."),
    ("texture/cricket-ball-seam-closeup.jpg", "1690111354184-cceee42df518", 1000, 1000,
     "Tight crop on the seam of a well-used ball."),
    ("texture/cricket-stumps-ground.jpg", "1674986778924-7a33c1531443", 1200, 800,
     "Stumps, bat and ball on the ground before play."),
]


def download(item: tuple[str, str, int, int, str], force: bool) -> tuple[str, str]:
    rel, photo_id, w, h, _shot = item
    dest = IMAGES / rel
    if dest.exists() and not force:
        return rel, "skipped (already there)"

    dest.parent.mkdir(parents=True, exist_ok=True)
    url = UNSPLASH.format(id=photo_id, w=w, h=h)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        return rel, f"FAILED ({exc})"

    if len(payload) < 2048:
        return rel, f"FAILED (only {len(payload)} bytes back)"

    dest.write_bytes(payload)
    return rel, f"ok, {len(payload) / 1024:.0f} KB"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="re-download images that already exist")
    args = parser.parse_args()

    print(f"Fetching {len(MANIFEST)} placeholder images into {IMAGES}\n")
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(download, item, args.force) for item in MANIFEST]
        for future in concurrent.futures.as_completed(futures):
            rel, status = future.result()
            if status.startswith("FAILED"):
                failures += 1
            print(f"  {rel:46s} {status}")

    print()
    if failures:
        print(f"{failures} image(s) failed. Re-run to retry just those.")
        return 1
    print("All placeholder images in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
