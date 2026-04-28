# iNotWiki: Missing Wikipedia Articles CLI Tool

A command-line tool to find **missing Wikipedia articles** for biological taxa using
**iNaturalist** and **Wikidata**.

## Features
- Fetches observations from **iNaturalist** with pagination via `id_above`
  (works for projects with more than 10 000 observations).
- Looks up each taxon on **Wikidata** and checks for Wikipedia articles in the
  requested languages.
- Generates a Markdown report with a table per taxon and PNG plots of the
  top observers / most-observed species.
- Identifies as `iNotListed/<version>` and retries on transient HTTP errors
  (429 / 5xx) with exponential backoff.

---

## Installation
Requires **Python 3.9+**.

```sh
pip install requests matplotlib
```

---

## Usage
```sh
python iNotWiki.py [options]
```

Provide exactly **one** of `--project_id`, `--username`, or `--country_id`.
If none is provided, the script falls back to the project `biohackathon-2025`.

| Option            | Description                                                       |
|-------------------|-------------------------------------------------------------------|
| `--project_id`    | iNaturalist project ID or slug (e.g. `biohackathon-2025`)         |
| `--username`      | iNaturalist username                                              |
| `--country_id`    | iNaturalist place ID                                              |
| `--languages`     | Comma-separated Wikipedia language codes (default: `en,es,ja,ar,nl,pt,fr`) |
| `--output-folder` | Folder to write the Markdown report and PNG plots (default: `reports`) |

The script prints the path of the generated Markdown report on stdout, so it
plays well with shell capture:

```sh
REPORT_PATH=$(python iNotWiki.py --project_id biohackathon-2025)
```

When run inside GitHub Actions it also writes `report_path=…` to
`$GITHUB_OUTPUT`.

---

## Examples

```sh
# Project (slug or numeric id)
python iNotWiki.py --project_id biohackathon-2025

# User, restricted to a few languages
python iNotWiki.py --username johndoe --languages en,nl,de

# Place / country
python iNotWiki.py --country_id 7088 --output-folder reports/colombia
```

---

## GitHub-issue interface
Two issue templates trigger the workflows in `.github/workflows/`:

- **`[Wikiblitz]: …`** — runs the project-only workflow.
- **`[Missing Wikipedia]: …`** — runs the full form (project / user / country
  + language checkboxes).

Both workflows commit the generated report under `reports/issue-<n>/` and
post (a truncated copy of) the Markdown back as an issue comment.

---

## Development
The CLI lives in a single file (`iNotWiki.py`) for now. A small Telegram bot
that wraps it is in development — see the issue tracker.

## License
MIT.
