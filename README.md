# Cinema: two calendars

A ready-to-upload project for your `cinema-calendar` repository, covering Prince Charles Cinema, BFI Southbank, The Nickel, The Garden Cinema, Rio Cinema, Genesis Cinema and The Castle Cinema.

- **Cinema: Special Screenings**: timed entries for identifiable Q&As, film formats, previews, festivals, retrospectives, introductions and similar labelled events.
- **Cinema: Films Showing**: one all-day entry per film per cinema on its first upcoming London date. The description lists its upcoming showtimes and booking links. The entry moves forward as earlier showtimes pass.

Read **UPLOAD_GUIDE.md** first. Extract the ZIP and upload the contents of `cinema_two_calendars` to the repository root, including the hidden `.github` folder. No repository has been changed by creating this package.

## Included files

- `build_calendars.py`: retrieves all seven venue datasets and generates both feeds.
- `.github/workflows/update-calendars.yml`: tests, builds and publishes through GitHub Pages on pushes to `main`, manual runs, and every six hours at minute 17 UTC.
- `tests/test_calendars.py`: 16 behaviour tests with synthetic fixtures.
- `.gitignore`: excludes generated output and local caches.
- `UPLOAD_GUIDE.md`: upload and later activation instructions.
- `VERIFICATION.md`: checks performed on this replacement package.

Generated outputs: `site/special-screenings.ics`, `site/films-showing.ics`, `site/index.html`, `site/status.json`. Calendar snapshots are not bundled as subscriptions; the workflow generates fresh files when activated.

## Local use (optional)

Requires Python 3.9+ with timezone data and curl, included on GitHub's Ubuntu runner. No Python packages, API keys or paid dependencies are required. Run from the extracted folder:

```sh
python3 -m unittest discover -s tests -v
python3 build_calendars.py
```

For reproducible checks against saved venue JSON:

```sh
python3 build_calendars.py --data-dir /path/to/venue-json --output site --now 2026-11-03T23:40:00Z
```

## Behaviour and limitations

All published upcoming dates are included. The film calendar may still contain hundreds of films, but not an event for every showtime. Grouping uses the source's matched numeric film ID when available, otherwise category/title/year. Missing or incorrect source matches can cause duplicates or incorrect grouping.

Special-screening detection uses titles, performance notes and formats. Unlabelled retrospectives, festivals or one-offs may be missed, and a matching word in a film title can produce a false positive. Old films and lone showtimes are not automatically special. Performance-specific notes affect only that showtime. Special screenings also appear in the broader film calendar, intentionally.

Sold-out performances are retained and labelled. Confirm details on the cinema's booking page. End times use the published running time; Q&As and introductions may run longer. Missing durations are not guessed. Timed entries use UTC and all-day dates use Europe/London, accounting for daylight-saving time. Events have no alarms and are marked free/transparent.

If any download fails, is malformed or has no upcoming showtimes, publication stops and the previous GitHub Pages deployment remains available. A genuinely empty venue also needs investigation. Check Actions logs and the page's update time if updates stop. GitHub schedules can be delayed or disabled after prolonged repository inactivity, and Apple Calendar controls its own refresh timing.

## Sources

Screening data from [Clusterflick](https://clusterflick.com), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), filtered and grouped for these feeds. Attribution appears in the generated page, calendars and events.

- [Published datasets](https://clusterflick.com/datasets/)
- [JSON schema](https://clusterflick.com/datasets/schema.json)
- [Data licence](https://clusterflick.com/data-licence/)
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

No TMDB synopses, cast lists or artwork are reproduced. The matched numeric ID is used only as an internal grouping key.
