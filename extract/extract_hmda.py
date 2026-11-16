"""
Pull REAL public loan application records from the CFPB / FFIEC HMDA Data Browser API.

HMDA (Home Mortgage Disclosure Act) data is public, free, and needs no API key.
This shows a production-style `requests` extractor: retries, timeouts, streaming,
and landing the raw file untouched (transform later in dbt, not here).

Usage:
    python extract/extract_hmda.py --state TX --year 2023
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"


def session_with_retries() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=5, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def extract(state: str, year: int, out_dir: Path) -> Path:
    params = {"states": state, "years": year, "actions_taken": "1"}  # 1 = loan originated
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"hmda_{state.lower()}_{year}.csv"

    log.info("requesting HMDA %s %s ...", state, year)
    with session_with_retries().get(BASE_URL, params=params, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)

    log.info("saved %s (%.1f MB)", out_path, out_path.stat().st_size / 1e6)
    return out_path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--state", default="TX")
    p.add_argument("--year", type=int, default=2023)
    p.add_argument("--out", type=Path, default=Path("data/raw/hmda"))
    a = p.parse_args()
    extract(a.state, a.year, a.out)


if __name__ == "__main__":
    main()
