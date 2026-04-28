"""Parse a GitHub issue-form body into key/value pairs.

Input  : issue body on stdin (UTF-8).
Output : `key=value` lines on stdout, suitable for `>> $GITHUB_OUTPUT`.

Recognised keys (lower-cased, emoji + "(optional)" stripped, words joined by `_`):
  - username, project_id, country_id (single-line text inputs)
  - languages                         (checkbox list, comma-joined)

Empty fields and the GitHub placeholder "_No response_" are skipped.
"""

from __future__ import annotations

import re
import sys
import unicodedata


HEADER_RE = re.compile(r"^#{2,6}\s+(.*?)\s*$")
CHECKED_RE = re.compile(r"^\s*-\s*\[\s*[xX]\s*\]\s*(.+?)\s*$")
KEY_MAP = {
    "inaturalist_username": "username",
    "inaturalist_project_id": "project_id",
    "inaturalist_country_place_id": "country_id",
    "wikipedia_languages_to_include": "languages",
}
PLACEHOLDER = "_no response_"


def normalise(header: str) -> str:
    # Strip emoji / symbols, drop "(optional)" hints, collapse to snake_case.
    header = re.sub(r"\(optional\)", "", header, flags=re.IGNORECASE)
    cleaned = "".join(
        ch for ch in header
        if unicodedata.category(ch)[0] in {"L", "N", "Z"} or ch in " /-_"
    )
    cleaned = cleaned.replace("/", " ")
    tokens = re.findall(r"[A-Za-z0-9]+", cleaned)
    return "_".join(t.lower() for t in tokens)


def parse(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in body.splitlines():
        line = raw.rstrip()
        m = HEADER_RE.match(line)
        if m:
            current = normalise(m.group(1))
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)

    out: dict[str, str] = {}
    for key, lines in sections.items():
        mapped = KEY_MAP.get(key)
        if mapped is None:
            continue
        if mapped == "languages":
            langs = [
                CHECKED_RE.match(l).group(1).strip()
                for l in lines
                if CHECKED_RE.match(l)
            ]
            if langs:
                out["languages"] = ",".join(langs)
        else:
            value = "\n".join(lines).strip()
            if value and value.lower() != PLACEHOLDER:
                out[mapped] = value
    return out


def main() -> int:
    body = sys.stdin.read()
    fields = parse(body)
    for key, value in fields.items():
        # GITHUB_OUTPUT cannot contain raw newlines without heredoc syntax;
        # all our values here are single-line.
        if "\n" in value or "\r" in value:
            print(f"refusing to emit multi-line value for {key!r}", file=sys.stderr)
            continue
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
