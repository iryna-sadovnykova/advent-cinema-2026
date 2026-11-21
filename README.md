# Advent Cinema 2026 🎄🎬

A 32-day Christmas-season film advent calendar, running from **December 1, 2026 through January 1, 2027**.

## Features

- 32 dated film doors, including a special January 1 door
- Doors become unlocked and visually opened **automatically on their scheduled date in Europe/Kyiv**, whether or not you've clicked them
- A **Preview all doors** toggle to explore the calendar early
- A responsive layout for desktop and mobile
- Film titles, years and a poster area with a consistent **2:3** aspect ratio
- Poster images currently retrieved from film-specific Wikipedia articles; this is best-effort and some images may be missing, low resolution or unsuitable. A curated local poster collection is a future improvement.

## Publishing with GitHub Pages

1. Open **Settings → Pages** in this repository.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select **main** and **/(root)**, then save.
4. Once GitHub finishes publishing, the usual site URL will be:
   `https://iryna-sadovnykova.github.io/advent-cinema-2026/`

This site has no build step or backend; it runs directly from `index.html`.

## Updating

Changes to `index.html` on the published branch will be redeployed by GitHub Pages. The site uses Wikipedia and Google Fonts over the internet, so the artwork and fonts require a connection.

> All movie titles are present in the page source. Date-gating is for the Advent experience, not spoiler-proof security.
