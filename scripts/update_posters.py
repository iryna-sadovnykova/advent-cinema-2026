#!/usr/bin/env python3
"""Resolve Advent Cinema titles to TMDB poster paths, once, at build time.

Requires TMDB_READ_ACCESS_TOKEN (v4 bearer token) or TMDB_API_KEY (v3).
Stores only poster paths in posters.json; never store or publish the credential.
Review unmatched items in the Actions job summary before considering the task done.
"""
import json
import os
import pathlib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

FILMS = [
    ("Miracle on 34th Street", 1947, "movie"),
    ("The Man Who Invented Christmas", 2017, "movie"),
    ("Plácido", 1961, "movie"),
    ("The Shop Around the Corner", 1940, "movie"),
    ("Batman Returns", 1992, "movie"),
    ("Arthur Christmas", 2011, "movie"),
    ("Tangerine", 2015, "movie"),
    ("Little Women", 1994, "movie"),
    ("Better Watch Out", 2016, "movie"),
    ("Kiss Kiss Bang Bang", 2005, "movie"),
    ("Gremlins", 1984, "movie"),
    ("Scrooge", 1951, "movie"),
    ("A Christmas Story", 1983, "movie"),
    ("Remember the Night", 1940, "movie"),
    ("Anna and the Apocalypse", 2017, "movie"),
    ("A Christmas Tale", 2008, "movie"),
    ("Rare Exports: A Christmas Tale", 2010, "movie"),
    ("Carol", 2015, "movie"),
    ("A Biltmore Christmas", 2023, "movie"),
    ("The Muppet Christmas Carol", 1992, "movie"),
    ("Hogfather", 2006, "tv"),
    ("Edward Scissorhands", 1990, "movie"),
    ("Happiest Season", 2020, "movie"),
    ("Tokyo Godfathers", 2003, "movie"),
    ("The Holdovers", 2023, "movie"),
    ("Die Hard", 1988, "movie"),
    ("The Thin Man", 1934, "movie"),
    ("Trading Places", 1983, "movie"),
    ("The Gold Rush", 1925, "movie"),
    ("Holiday", 1938, "movie"),
    ("After the Thin Man", 1936, "movie"),
    ("The Apartment", 1960, "movie"),
]
ALIASES = {16: "Rare Exports"}  # TMDB's shorter title for the 2010 film
# To choose a specific record, set its TMDB numeric ID here and rerun the action.
OVERRIDE_IDS = {}

def norm(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", text.casefold())

def get_api(path, params=None):
    token = os.getenv("TMDB_READ_ACCESS_TOKEN")
    key = os.getenv("TMDB_API_KEY")
    if not (token or key):
        sys.exit("Missing TMDB_READ_ACCESS_TOKEN or TMDB_API_KEY repository secret")
    payload = dict(params or {})
    if not token:
        payload["api_key"] = key
    url = "https://api.themoviedb.org/3/" + path
    if payload:
        url += "?" + urllib.parse.urlencode(payload)
    headers = {"Accept": "application/json", "User-Agent": "AdventCinemaPosterSetup/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                return json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            if attempt == 2 or isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403):
                raise
            time.sleep(1 + attempt * 2)

def pick(title, year, kind, index):
    if index in OVERRIDE_IDS:
        return get_api(f"{kind}/{OVERRIDE_IDS[index]}")
    query = ALIASES.get(index, title)
    date_param = "year" if kind == "movie" else "first_air_date_year"
    data = get_api(f"search/{kind}", {"query": query, date_param: year, "include_adult": "false"})
    candidates = data.get("results", [])
    expected = norm(query)
    title_key = "title" if kind == "movie" else "name"
    original_key = "original_title" if kind == "movie" else "original_name"
    date_key = "release_date" if kind == "movie" else "first_air_date"
    exact = [
        record for record in candidates
        if str(record.get(date_key, "")).startswith(str(year))
        and expected in (norm(record.get(title_key, "")), norm(record.get(original_key, "")))
    ]
    if not exact:
        return None
    exact.sort(key=lambda record: (bool(record.get("poster_path")), record.get("popularity", 0)), reverse=True)
    return exact[0]

def main():
    posters = {}
    records = {}
    missing = []
    for i, (title, year, kind) in enumerate(FILMS):
        try:
            item = pick(title, year, kind, i)
        except Exception as exc:
            print(f"Error retrieving {title} ({year}): {exc}", file=sys.stderr)
            missing.append(f"{i+1:02d}. {title} ({year}) — API error")
            continue
        path = item.get("poster_path") if item else None
        if not (isinstance(path, str) and re.fullmatch(r"/[A-Za-z0-9_.-]+\.(jpg|png|webp)", path)):
            missing.append(f"{i+1:02d}. {title} ({year}) — no verified poster match")
            continue
        posters[str(i)] = path
        records[str(i)] = {"title": title, "year": year, "tmdb_id": item["id"], "media_type": kind}
        print(f"{i+1:02d}. {title} ({year}) → TMDB {kind} {item['id']} → {path}")
    target = pathlib.Path("posters.json")
    target.write_text(json.dumps({"source": "TMDB", "posters": posters, "records": records}, ensure_ascii=False, indent=2) + "\n")
    report = f"### TMDB posters: {len(posters)}/32 selected\n\n"
    report += "The website uses static poster paths from this generated file; no browser API key.\n\n"
    if missing:
        report += "**Needs review**\n\n" + "\n".join(f"- {x}" for x in missing) + "\n"
    else:
        report += "All 32 titles found. Review the image choices visually before calling them final.\n"
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(report)
    print(report)
    return 0 if posters else 1

if __name__ == "__main__":
    raise SystemExit(main())
