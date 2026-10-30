#!/usr/bin/env python3
"""Generate an SVG bar chart of annual GitHub profile contributions."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


USERNAME = "LittleTheFu"
API_URL = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=all"
OUTPUT = Path("profile/contributions-by-year.svg")


def fetch_yearly_totals() -> list[tuple[int, int]]:
    request = Request(
        API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "LittleTheFu-profile-stats/1.0",
        },
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    raw_totals = payload.get("total")
    if not isinstance(raw_totals, dict):
        raise ValueError("The contributions API returned no yearly totals.")

    totals: list[tuple[int, int]] = []
    for year, count in raw_totals.items():
        if str(year).isdigit():
            totals.append((int(year), int(count)))

    totals.sort(key=lambda item: item[0])
    if not totals:
        raise ValueError("The contributions API returned an empty history.")
    return totals


def build_svg(totals: list[tuple[int, int]]) -> str:
    width = 760
    top = 104
    row_height = 39
    height = top + len(totals) * row_height + 62
    bar_x = 126
    max_bar_width = 490
    max_value = max((count for _, count in totals), default=1) or 1
    current_year = date.today().year

    rows: list[str] = []
    for index, (year, count) in enumerate(totals):
        y = top + index * row_height
        bar_width = max(2, round(count / max_value * max_bar_width)) if count else 0
        year_label = f"{year} (YTD)" if year == current_year else str(year)
        rows.append(
            f"""
    <text x="36" y="{y + 19}" class="year">{escape(year_label)}</text>
    <rect x="{bar_x}" y="{y}" width="{max_bar_width}" height="20" rx="6" class="track"/>
    <rect x="{bar_x}" y="{y}" width="{bar_width}" height="20" rx="6" class="bar"/>
    <text x="{bar_x + max_bar_width + 16}" y="{y + 16}" class="value">{count:,}</text>"""
        )

    updated = date.today().isoformat()
    description = "Annual contribution totals from the public GitHub contribution graph."
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
  viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">GitHub Contributions by Year</title>
  <desc id="desc">{escape(description)}</desc>
  <style>
    .title {{ font: 700 22px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #24292f; }}
    .subtitle {{ font: 13px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #57606a; }}
    .year {{ font: 600 13px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #57606a; }}
    .value {{ font: 600 13px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #24292f; }}
    .track {{ fill: #eaf2ff; }}
    .bar {{ fill: #2f80ed; }}
    .footer {{ font: 11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #6e7781; }}
  </style>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12"
    fill="#ffffff" stroke="#d0d7de"/>
  <text x="30" y="39" class="title">GitHub Contributions by Year</text>
  <text x="30" y="63" class="subtitle">Annual totals · {USERNAME}</text>
  {''.join(rows)}
  <text x="30" y="{height - 22}" class="footer">Source: public GitHub contribution graph · Updated {updated}</text>
</svg>
"""


def main() -> None:
    try:
        totals = fetch_yearly_totals()
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Could not fetch yearly contribution history: {error}") from error

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(totals), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(totals)} calendar years.")


if __name__ == "__main__":
    main()
