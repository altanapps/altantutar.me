#!/usr/bin/env python3
"""Regenerate the widgets on activity.html.

Bakes three inline SVGs into the page, between HTML marker comments:
  - a world map with visited countries filled in (scripts/visited.txt)
  - a GitHub-style year heatmap of GitHub contributions (via `gh api`)
  - the same heatmap for X posts (from account_analytics_content_*.csv exports)

Run from the repo root:  python3 scripts/build_activity.py
The page itself stays static — no JavaScript ships to the browser.
"""

import csv
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "activity.html")
GEOJSON = os.path.join(ROOT, "scripts", "countries.geo.json")
VISITED = os.path.join(ROOT, "scripts", "visited.txt")
GITHUB_LOGINS = ["altantutar", "altanapps"]
X_HANDLE = "altantutar"
# X analytics exports live in the main vault, not in this repo.
POST_CSV_GLOBS = [
    os.path.expanduser("~/Desktop/main/personal/tweets/account_analytics_content_*.csv"),
    os.path.expanduser("~/Desktop/main/personal/personal-brand/account_analytics_content_*.csv"),
]

# ---- world map ------------------------------------------------------------

MAP_W = 1000.0
LAT_TOP, LAT_BOT = 84.0, -56.0  # clip empty poles; Antarctica is skipped anyway
MAP_H = round(MAP_W * (LAT_TOP - LAT_BOT) / 360.0, 1)


def project(lon, lat):
    x = (lon + 180.0) / 360.0 * MAP_W
    y = (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MAP_H
    return x, y


def ring_to_path(ring):
    """One polygon ring -> SVG subpath, with light point decimation."""
    pts = []
    last = None
    for lon, lat in ring:
        x, y = project(lon, lat)
        if last is not None and abs(x - last[0]) < 0.7 and abs(y - last[1]) < 0.7:
            continue
        pts.append((x, y))
        last = (x, y)
    if len(pts) < 3:
        return ""
    return (
        "M" + " ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
    )


def build_map():
    with open(VISITED) as f:
        visited = set()
        for line in f:
            code = line.split("#")[0].strip().upper()
            if code:
                visited.add(code)

    with open(GEOJSON) as f:
        world = json.load(f)

    import html as html_mod

    paths = []
    known = set()
    label_y = MAP_H - 8
    for feat in world["features"]:
        iso = feat.get("id", "")
        if iso == "ATA":
            continue
        known.add(iso)
        name = html_mod.escape(feat.get("properties", {}).get("name", iso))
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        d = "".join(ring_to_path(poly[0]) for poly in polys)  # outer rings only
        if not d:
            continue
        cls = "country v" if iso in visited else "country"
        # The <text> immediately after each path powers the CSS-only hover
        # label (path:hover + text). Safari ignores SVG <title> tooltips.
        paths.append(
            f'<path class="{cls}" d="{d}"></path>'
            f'<text class="label" x="6" y="{label_y:.0f}">{name}</text>'
        )

    missing = visited - known
    if missing:
        print(f"warning: visited codes not in the map data: {sorted(missing)}", file=sys.stderr)

    svg = (
        f'<div class="worldmap"><svg viewBox="0 0 {MAP_W:g} {MAP_H:g}" role="img" '
        f'aria-label="World map, countries I have visited filled in">'
        + "".join(paths)
        + "</svg></div>"
    )
    return svg


# ---- heatmaps -------------------------------------------------------------

CELL, GAP = 12, 3
STEP = CELL + GAP
LEFT_PAD, TOP_PAD = 30, 16
RAMP = ["#efeadf", "#e6ccae", "#cf9e77", "#b06a42", "#9c4221"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level(count, thresholds):
    for i, t in enumerate(thresholds):
        if count <= t:
            return i
    return len(thresholds)


def heatmap_svg(counts_by_date, thresholds, aria):
    """counts_by_date: {date: n}. Renders the last 53 weeks, weeks start Sunday."""
    today = dt.date.today()
    week_start = today - dt.timedelta(days=(today.weekday() + 1) % 7)  # this week's Sunday
    first_sunday = week_start - dt.timedelta(weeks=52)

    cells, month_labels = [], []
    seen_month = None
    for w in range(53):
        sunday = first_sunday + dt.timedelta(weeks=w)
        if sunday.month != seen_month and sunday.day <= 21:
            month_labels.append(
                f'<text x="{LEFT_PAD + w * STEP}" y="10">{MONTHS[sunday.month - 1]}</text>'
            )
            seen_month = sunday.month
        for d in range(7):
            day = sunday + dt.timedelta(days=d)
            if day > today:
                break
            n = counts_by_date.get(day, 0)
            fill = RAMP[level(n, thresholds)]
            label = f"{day.isoformat()}: {n}"
            cells.append(
                f'<rect x="{LEFT_PAD + w * STEP}" y="{TOP_PAD + d * STEP}" '
                f'width="{CELL}" height="{CELL}" rx="2" fill="{fill}"><title>{label}</title></rect>'
            )

    day_texts = "".join(
        f'<text x="0" y="{TOP_PAD + d * STEP + CELL - 2}">{t}</text>'
        for d, t in DAY_LABELS.items()
    )
    width = LEFT_PAD + 53 * STEP
    height = TOP_PAD + 7 * STEP
    return (
        f'<div class="heatmap"><svg viewBox="0 0 {width} {height}" role="img" aria-label="{aria}">'
        f"{''.join(month_labels)}{day_texts}{''.join(cells)}</svg></div>"
    )


def build_github():
    counts = {}
    for login in GITHUB_LOGINS:
        query = (
            'query { user(login: "%s") { contributionsCollection { contributionCalendar { '
            "totalContributions weeks { contributionDays { date contributionCount } } } } } }"
            % login
        )
        out = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True, text=True, check=True,
        ).stdout
        cal = json.loads(out)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        for week in cal["weeks"]:
            for day in week["contributionDays"]:
                d = dt.date.fromisoformat(day["date"])
                counts[d] = counts.get(d, 0) + day["contributionCount"]
    return heatmap_svg(counts, [0, 2, 5, 9], "A year of GitHub contributions")


def fetch_timeline_posts():
    """Own posts from X's public syndication timeline (~100 most recent).
    Returns {post_id: date}. Empty on any failure — the CSVs still render."""
    import urllib.request

    cache = os.path.join(ROOT, "scripts", "x-timeline-cache.json")
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{X_HANDLE}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        html = urllib.request.urlopen(req, timeout=20).read().decode()
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
        entries = json.loads(m.group(1))["props"]["pageProps"]["timeline"]["entries"]
        with open(cache, "w") as f:
            json.dump(entries, f)
    except Exception as e:
        if os.path.exists(cache):
            print(f"warning: X timeline fetch failed ({e}); using cached copy", file=sys.stderr)
            entries = json.load(open(cache))
        else:
            print(f"warning: could not fetch X timeline ({e}); using CSVs only", file=sys.stderr)
            return {}
    posts = {}
    for entry in entries:
        tweet = entry.get("content", {}).get("tweet", {})
        if tweet.get("user", {}).get("screen_name", "").lower() != X_HANDLE:
            continue
        when = dt.datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S %z %Y")
        posts[str(tweet["id_str"])] = when.date()
    return posts


def build_posts():
    # Post id -> date, accumulated in scripts/post-history.json so CI runs
    # keep the full picture without needing the private analytics CSVs.
    # Sources merged in: the history file, any CSV exports found locally,
    # and the live public timeline.
    history_path = os.path.join(ROOT, "scripts", "post-history.json")
    posts = {}
    if os.path.exists(history_path):
        posts = {pid: dt.date.fromisoformat(d) for pid, d in json.load(open(history_path)).items()}

    files = sorted(set(f for pat in POST_CSV_GLOBS for f in glob.glob(pat)))
    for path in files:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                pid = row.get("Post id")
                raw = row.get("Date", "").strip()
                m = re.match(r"\w+, (\w+) (\d+), (\d+)", raw)
                if not pid or not m:
                    continue
                month = MONTHS.index(m.group(1)[:3]) + 1
                posts[pid] = dt.date(int(m.group(3)), month, int(m.group(2)))
    for pid, day in fetch_timeline_posts().items():
        posts.setdefault(pid, day)

    with open(history_path, "w") as f:
        json.dump({pid: d.isoformat() for pid, d in sorted(posts.items())}, f, indent=0)

    counts = {}
    for day in posts.values():
        counts[day] = counts.get(day, 0) + 1
    return heatmap_svg(counts, [0, 1, 3, 6], "A year of posts on X")


# ---- injection ------------------------------------------------------------

def inject(html, name, payload):
    start, end = f"<!-- WIDGET:{name} -->", f"<!-- /WIDGET:{name} -->"
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.S)
    if not pattern.search(html):
        sys.exit(f"marker {start} not found in activity.html")
    return pattern.sub(start + "\n" + payload + "\n      " + end, html)


def main():
    with open(PAGE) as f:
        html = f.read()
    html = inject(html, "map", build_map())
    html = inject(html, "github", build_github())
    html = inject(html, "posts", build_posts())
    with open(PAGE, "w") as f:
        f.write(html)
    print(f"wrote {PAGE} ({os.path.getsize(PAGE) // 1024} KB)")


if __name__ == "__main__":
    main()
