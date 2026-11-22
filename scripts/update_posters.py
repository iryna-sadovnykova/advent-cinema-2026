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
    ("Remember the Night", 1940, "movie"),
    ("Plácido", 1961, "movie"),
    ("The Shop Around the Corner", 1940, "movie"),
    ("Batman Returns", 1992, "movie"),
    ("Arthur Christmas", 2011, "movie"),
    ("Tangerine", 2015, "movie"),
    ("Trading Places", 1983, "movie"),
    ("Better Watch Out", 2016, "movie"),
    ("Kiss Kiss Bang Bang", 2005, "movie"),
    ("Gremlins", 1984, "movie"),
    ("Scrooge", 1951, "movie"),
    ("A Christmas Story", 1983, "movie"),
    ("Щедрик", 2022, "movie"),
    ("Anna and the Apocalypse", 2017, "movie"),
    ("A Christmas Tale", 2008, "movie"),
    ("Rare Exports: A Christmas Tale", 2010, "movie"),
    ("Carol", 2015, "movie"),
    ("Пекельна хоругва, або Різдво козацьке", 2019, "movie"),
    ("Tokyo Godfathers", 2003, "movie"),
    ("Hogfather", 2006, "tv"),
    ("Edward Scissorhands", 1990, "movie"),
    ("Happiest Season", 2020, "movie"),
    ("The Muppet Christmas Carol", 1992, "movie"),
    ("The Holdovers", 2023, "movie"),
    ("Die Hard", 1988, "movie"),
    ("The Thin Man", 1934, "movie"),
    ("Памфір", 2022, "movie"),
    ("The Gold Rush", 1925, "movie"),
    ("Holiday", 1938, "movie"),
    ("After the Thin Man", 1936, "movie"),
    ("The Apartment", 1960, "movie"),
]
ALIASES = {16: "Rare Exports"}  # TMDB's shorter title for the 2010 film
# IMDb identifiers disambiguate films with alternative years and accented titles.
IMDB_IDS = {
    2: "tt0055310",  # Plácido (1961), Luis García Berlanga
    8: "tt4443658",  # Better Watch Out (2016/2017)
    14: "tt6433880", # Anna and the Apocalypse (2017/2018)
    13: "tt8332658",  # Щедрик / Carol of the Bells
    27: "tt9455468",  # Памфір / Pamfir
    18: "tt10272460", # Пекельна хоругва
}
# To choose a specific record, set its TMDB numeric ID here and rerun the action.
OVERRIDE_IDS = {13: 853079, 27: 850297}  # Verified TMDB entries for Щедрик and Памфір

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

def year_matches(record, target_year, date_key):
    """Allow distribution-year differences, but not unrelated remakes."""
    date = record.get(date_key, "")
    return bool(date and date[:4].isdigit() and abs(int(date[:4]) - target_year) <= 2)

def pick(title, year, kind, index):
    if index in OVERRIDE_IDS:
        return get_api(f"{kind}/{OVERRIDE_IDS[index]}")

    # Prefer the definitive external identifier for the three problematic entries.
    if kind == "movie" and index in IMDB_IDS:
        found = get_api(f"find/{IMDB_IDS[index]}", {"external_source": "imdb_id"})
        options = found.get("movie_results", [])
        if options:
            return options[0]

    query = ALIASES.get(index, title)
    title_key = "title" if kind == "movie" else "name"
    original_key = "original_title" if kind == "movie" else "original_name"
    date_key = "release_date" if kind == "movie" else "first_air_date"
    expected = norm(query)

    # Search by title without hard filtering by year; festival and theatrical
    # premiere years are often different in TMDB's catalog.
    data = get_api(f"search/{kind}", {"query": query, "include_adult": "false"})
    candidates = data.get("results", [])
    exact = [
        item for item in candidates
        if expected in (norm(item.get(title_key, "")), norm(item.get(original_key, "")))
        and year_matches(item, year, date_key)
    ]
    # Alternative title, if TMDB indexes the Spanish film without its accent.
    if not exact and index == 2:
        data = get_api("search/movie", {"query": "Placido", "include_adult": "false"})
        exact = [
            item for item in data.get("results", [])
            if norm(item.get("title", "")) == "placido"
            and year_matches(item, year, "release_date")
        ]
    if not exact:
        return None
    exact.sort(key=lambda item: (bool(item.get("poster_path")), item.get("popularity", 0)), reverse=True)
    return exact[0]

def poster_for(item, kind):
    path = item.get("poster_path") if item else None
    if path:
        return path
    if not item:
        return None
    # A title may be correctly matched even when its default poster is unset.
    images = get_api(f"{kind}/{item['id']}/images", {"include_image_language": "en,null,es"})
    options = images.get("posters", [])
    options.sort(key=lambda p: (
        p.get("iso_639_1") == "en",
        p.get("vote_average", 0),
        p.get("width", 0)
    ), reverse=True)
    return options[0].get("file_path") if options else None

def runtime_minutes(item, kind):
    """Fetch a title's runtime from TMDB details, not search summaries."""
    details = get_api(f"{kind}/{item['id']}")
    if kind == "movie":
        value = details.get("runtime")
        return value if isinstance(value, int) and value > 0 else None

    # Miniseries: show its combined duration, rather than one episode.
    total = 0
    counted = 0
    for season in details.get("seasons", []):
        number = season.get("season_number")
        if not isinstance(number, int) or number < 1:
            continue
        season_data = get_api(f"tv/{item['id']}/season/{number}")
        for episode in season_data.get("episodes", []):
            minutes = episode.get("runtime")
            if isinstance(minutes, int) and minutes > 0:
                total += minutes
                counted += 1
    if counted:
        return total
    typical = details.get("episode_run_time") or []
    episode_count = details.get("number_of_episodes")
    if typical and isinstance(typical[0], int) and typical[0] > 0 and isinstance(episode_count, int) and episode_count > 0:
        return typical[0] * episode_count
    return None

def main():
    posters = {}
    records = {}
    runtimes = {}
    missing = []
    for i, (title, year, kind) in enumerate(FILMS):
        try:
            item = pick(title, year, kind, i)
        except Exception as exc:
            print(f"Error retrieving {title} ({year}): {exc}", file=sys.stderr)
            missing.append(f"{i+1:02d}. {title} ({year}) — API error")
            continue
        if not item:
            missing.append(f"{i+1:02d}. {title} ({year}) — no verified TMDB match")
            continue
        records[str(i)] = {"title": title, "year": year, "tmdb_id": item["id"], "media_type": kind}
        try:
            duration = runtime_minutes(item, kind)
            if duration:
                runtimes[str(i)] = duration
        except Exception as exc:
            print(f"Could not retrieve runtime for {title}: {exc}", file=sys.stderr)

        path = poster_for(item, kind)
        if not (isinstance(path, str) and re.fullmatch(r"/[A-Za-z0-9_.-]+\.(jpg|png|webp)", path)):
            missing.append(f"{i+1:02d}. {title} ({year}) — no verified poster match")
            continue
        posters[str(i)] = path
        print(f"{i+1:02d}. {title} ({year}) → TMDB {kind} {item['id']} → {path} ({runtimes.get(str(i), 'unknown')} min)")
    target = pathlib.Path("posters.json")
    target.write_text(json.dumps({"source": "TMDB", "posters": posters, "runtimes": runtimes, "records": records}, ensure_ascii=False, indent=2) + "\n")
    report = f"### TMDB posters: {len(posters)}/32 selected\n\n"
    report += f"Runtimes collected: {len(runtimes)}/32. The website uses static TMDB data; no browser API key.\\n\\n"
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
