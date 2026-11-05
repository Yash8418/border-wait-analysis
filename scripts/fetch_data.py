"""Download CBSA historical border wait time data and keep only the Windsor crossings.

Uses the Open Government Portal's CKAN API to discover every resource in the
"Historical Border Wait Times – Land Mode" dataset, downloads the English CSVs,
and writes the rows for the Ambassador Bridge and Detroit–Windsor Tunnel to
data/raw/. A manifest records where each file came from and what it contains.

Usage:
    python scripts/fetch_data.py
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATASET_ID = "000fe5aa-1d77-42d1-bfe7-458c51dacfef"
CKAN_URL = f"https://open.canada.ca/data/api/action/package_show?id={DATASET_ID}"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Port names have varied over the years, so match loosely.
WINDSOR_PATTERN = re.compile(r"ambassador|windsor|detroit", re.IGNORECASE)
FRENCH_PATTERN = re.compile(r"\b(fr|french|fran[cç]ais)\b|-fr\.|_fr\.|-fra\.", re.IGNORECASE)
USER_AGENT = "border-wait-analysis/1.0 (+https://github.com/Yash8418/border-wait-analysis)"


def fetch(url: str, retries: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 - report and retry any network failure
            if attempt == retries:
                raise
            print(f"  retry {attempt} for {url}: {error}", file=sys.stderr)
            time.sleep(2 * attempt)
    raise RuntimeError("unreachable")


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def is_english_csv(resource: dict) -> bool:
    fmt = (resource.get("format") or "").lower()
    url = resource.get("url") or ""
    if fmt != "csv" and not url.lower().endswith(".csv"):
        return False
    language = resource.get("language") or []
    if isinstance(language, str):
        language = [language]
    if language and "en" not in language:
        return False
    label = f"{resource.get('name', '')} {url}"
    return not FRENCH_PATTERN.search(label)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    package = json.loads(fetch(CKAN_URL))["result"]
    resources = [r for r in package["resources"] if is_english_csv(r)]
    print(f"Found {len(resources)} English CSV resources")

    manifest = {
        "dataset": package.get("title"),
        "dataset_id": DATASET_ID,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": [],
    }

    for resource in resources:
        name = resource.get("name") or resource["id"]
        print(f"- {name}")
        try:
            text = decode(fetch(resource["url"]))
        except Exception as error:  # noqa: BLE001
            manifest["files"].append({"name": name, "url": resource["url"], "error": str(error)})
            continue

        rows = list(csv.reader(io.StringIO(text)))
        if not rows:
            continue
        header, body = rows[0], rows[1:]
        windsor = [row for row in body if any(WINDSOR_PATTERN.search(cell) for cell in row)]

        out_name = f"{slugify(name)}.csv"
        with open(OUT_DIR / out_name, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(windsor)

        manifest["files"].append(
            {
                "name": name,
                "url": resource["url"],
                "output": out_name,
                "columns": header,
                "total_rows": len(body),
                "windsor_rows": len(windsor),
                "sample": windsor[:3],
                "ports": sorted({cell for row in windsor for cell in row if WINDSOR_PATTERN.search(cell)})[:10],
            }
        )

    with open(OUT_DIR / "manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    kept = sum(f.get("windsor_rows", 0) for f in manifest["files"])
    print(f"Wrote {len(manifest['files'])} files, {kept} Windsor rows, to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
