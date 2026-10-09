# Replacing the photographs

Every image on the site right now is **free stock photography standing in for
your own**. None of it shows your girls, and some of it is not even cricket —
see [the honest caveat](#the-honest-caveat) at the bottom.

## How to replace one

1. Find the row below for the slot you want to fill.
2. Save your photograph over the file at that path, **keeping the filename**.
3. Reload. That is the whole job — no code changes.

Filenames describe the *shot that belongs there*, not the stock photo that is
currently in it, so you can work down this list like a shot list on a Saturday
morning.

### What makes a good file

| | |
|---|---|
| **Format** | JPEG for photographs. |
| **Width** | Roughly the pixel width in the table. Twice that is fine; four times is wasted. |
| **Weight** | Aim under 300 KB each. |
| **Crop** | Match the shape in the table — a portrait photo in a landscape slot gets its top and bottom cut off. |

If you change a photograph's shape, also update its `width` and `height`
attributes in the HTML. They stop the page jumping about while images load.

---

## The shot list

### Hero — `assets/images/hero/`

| File | Shape | The shot |
|---|---|---|
| `hero-batter-ready.jpg` | 4:5 portrait, 1100px | A girl in full kit, bat in hand, about to face up. Confident, not posed. This is the first thing anyone sees. |
| `hero-team-laughing.jpg` | 4:3 landscape, 1000px | Teammates on the boundary bench, mid-laugh. Friendship over technique. |
| `hero-high-five.jpg` | square, 800px | Two players high-fiving between overs. |

### Girls in action — `assets/images/action/`

The homepage collage and the photo strip on Stories.

| File | Shape | The shot |
|---|---|---|
| `action-team-huddle.jpg` | 3:2 landscape, 1200px | The huddle before the first ball. Arms around shoulders. |
| `action-batting-drive.jpg` | 4:5 portrait, 1000px | A batter just after contact — bat high, eyes following the ball. |
| `action-bowling-delivery.jpg` | 4:5 portrait, 900px | A bowler at the top of her delivery stride, arm coming over. |
| `action-fielding-ready.jpg` | 4:5 portrait, 900px | Hands ready in the field, or a fielder holding up the ball after a catch. |
| `action-celebration-hug.jpg` | 4:3 landscape, 1100px | Players piling in to celebrate a wicket or a win. |
| `action-laughing-teammates.jpg` | 4:3 landscape, 1000px | Close in on two or three players laughing at something off-camera. |
| `action-running-onto-field.jpg` | 3:2 landscape, 1200px | Girls running onto the field at the start of a match. |
| `action-training-session.jpg` | 3:2 landscape, 1200px | A normal training night — cones out, everyone working. |
| `action-girls-on-bench.jpg` | 3:2 landscape, 1100px | Waiting to bat, pads on, watching the game together. |
| `action-coach-teaching.jpg` | 3:2 landscape, 1200px | A volunteer coach showing a grip or a stance to a small group. |

### The academy — `assets/images/academy/`

| File | Shape | The shot |
|---|---|---|
| `academy-nets-training.jpg` | 3:2 landscape, 1200px | Your nets, ideally with players in them. |
| `academy-ground-wide.jpg` | 16:9 landscape, 1400px | A wide shot of the home ground, so parents recognise the place. |
| `academy-match-day.jpg` | 16:9 landscape, 1400px | Match day from the boundary — players out, families watching. |

### Player stories — `assets/images/stories/`

| File | Shape | The shot |
|---|---|---|
| `story-player-01.jpg` | square, 560px | Headshot for the first story. Relaxed and smiling, not a school photo. |
| `story-player-02.jpg` | square, 560px | Headshot for the second story — holding a ball works well. |
| `story-player-03.jpg` | square, 560px | Headshot for the third story. |

### Coaches and volunteers — `assets/images/coaches/`

| File | Shape | The shot |
|---|---|---|
| `coach-01.jpg` | 4:5 portrait, 640px | Volunteer coach portrait. |
| `coach-02.jpg` | 4:5 portrait, 640px | Volunteer coach portrait. |
| `coach-03.jpg` | 4:5 portrait, 640px | Team manager or another volunteer. |

The coaches section on the About page does more work than anything else on the
site for a nervous parent. Real faces with real names are worth the effort of
asking.

### Cricket detail — `assets/images/texture/`

Used as section texture and in the photo strip. These are the only images that
do **not** need to be yours — a ball in the grass is a ball in the grass.

| File | Shape | The shot |
|---|---|---|
| `cricket-ball-grass.jpg` | 16:9, 1400px | A cricket ball sitting in the grass. |
| `cricket-ball-seam-closeup.jpg` | square, 1000px | Tight crop on the seam of a well-used ball. |
| `cricket-stumps-ground.jpg` | 3:2, 1200px | Stumps, bat and ball on the ground before play. |

---

## Alt text

Every image already has alt text describing the placeholder. **Update it when
you swap the photo** — it is what screen-reader users and anyone on a failed
connection gets instead of the picture. Describe what is happening, not what
the file is:

> ✅ `alt="Priya driving through the covers on her way to 30 not out."`
> ❌ `alt="cricket photo"` · `alt="image of girls"`

Search the `pages/` and `components/` folders for the filename to find its alt
text.

---

## Permission

Publishing photographs of children needs their family's consent. Two practical
habits:

- Keep a list of which girls are cleared for photos, and check it before
  posting.
- Put a line on the Stories page — there is one there already — saying that you
  will take a photograph down the same day if a family asks.

---

## The honest caveat

These placeholders were pulled from Unsplash, and **Unsplash has almost no
photographs of girls playing cricket**. Searches for "girls cricket" and
"women's cricket" return men in whites; searches for "girls sports team" return
football and softball.

So the placeholders are a compromise:

- A handful are genuinely female cricketers (the hero shot is one).
- The friendship, celebration and coaching images are women's and girls' team
  sport, but **not cricket**.
- The detail shots are real cricket, with no people in them.

That compromise is the exact opposite of what this website is for, so treat the
photography as the first job rather than a finishing touch. One good Saturday
with a decent phone will beat all of it.

Sources for each placeholder are listed in [CREDITS.md](CREDITS.md). To
re-download them all:

```bash
python scripts/fetch_placeholder_images.py --force
```
