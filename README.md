# Advent Cinema 2026 🎄🎬

A 32-day Christmas-season film calendar, December 1, 2026 through January 1, 2027.

## Features

- All 32 doors previewable by default
- Past dates turn gray automatically in the Europe/Kyiv timezone
- Modern, flat red / green / deep-gold layout
- 2:3 film poster frame (no cropping)
- Static TMDB poster paths; no browser-facing API token or Wikipedia search

## One-time TMDB poster setup

This step has **not been run yet**. The initial `posters.json` is intentionally empty, so the site displays movie title cards until you generate the poster list.

1. Create a free TMDB account at https://www.themoviedb.org/signup
2. Request developer API access at https://www.themoviedb.org/settings/api
3. In GitHub, visit **Settings → Secrets and variables → Actions**:
   https://github.com/iryna-sadovnykova/advent-cinema-2026/settings/secrets/actions
4. Choose **New repository secret**. Create **TMDB_READ_ACCESS_TOKEN** and paste your **API Read Access Token** from TMDB settings. (Alternatively, use **TMDB_API_KEY** with your API Key v3.)
5. Visit **Actions → Curate TMDB posters → Run workflow**:
   https://github.com/iryna-sadovnykova/advent-cinema-2026/actions/workflows/update-posters.yml
6. The action matches each film by title and release year, chooses its TMDB `poster_path`, and commits the resulting `posters.json` automatically. **The API key stays in the GitHub Actions secret**, and the public site only uses the resulting image paths.
7. Check the workflow run's summary for missing or ambiguous films. You can edit `OVERRIDE_IDS` in `scripts/update_posters.py` to pin a specific TMDB record, then rerun the action.

**Note:** Automated matching is not a final manual review. Verify that each movie has the desired poster version after the first run. For film #21, `Hogfather` (2006), the script searches TMDB TV rather than movies.

TMDB attribution: This product uses the TMDB API but is not endorsed or certified by TMDB. Poster artworks remain the property of their respective owners. Consult TMDB's attribution/logo rules at https://www.themoviedb.org/about/logos-attribution.

## Publishing with GitHub Pages

1. Open **Settings → Pages** in the repository.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select **main** and **/(root)**, then save.
4. Website: https://iryna-sadovnykova.github.io/advent-cinema-2026/

GitHub Pages redeploys when `index.html` or `posters.json` changes on `main`.

> The site is an Advent experience, not spoiler-proof security. The movie titles are present in the public source.
