"""
Upload raw CSVs from data/raw/ to the S3 raw landing zone with boto3.

Layout in S3:
    s3://<bucket>/raw/<table>.csv                         <- latest copy (what dbt reads)
    s3://<bucket>/raw/_archive/load_date=YYYY-MM-DD/<table>.csv  <- history

Credentials come from your AWS CLI profile (`aws configure`), never from code.

Usage:
    python load/upload_to_s3.py               # bucket from .env (S3_BUCKET)
    python load/upload_to_s3.py --bucket my-bucket
"""

from __future__ import annotations

import argparse
import logging
import os
from datetime import date
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

TABLES = ["borrowers", "loans", "payments"]


def upload(bucket: str, raw_dir: Path, prefix: str = "raw") -> None:
    s3 = boto3.client("s3")
    today = date.today().isoformat()
    for table in TABLES:
        path = raw_dir / f"{table}.csv"
        if not path.exists():
            log.warning("missing %s - run extract/generate_loans.py first", path)
            continue
        for key in (f"{prefix}/{table}.csv", f"{prefix}/_archive/load_date={today}/{table}.csv"):
            try:
                s3.upload_file(str(path), bucket, key)
                log.info("uploaded %s -> s3://%s/%s", path.name, bucket, key)
            except ClientError as e:
                log.error("failed to upload %s: %s", key, e)
                raise


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--bucket", default=os.getenv("S3_BUCKET"))
    p.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    a = p.parse_args()
    if not a.bucket:
        raise SystemExit("Set S3_BUCKET in .env or pass --bucket")
    upload(a.bucket, a.raw_dir)


if __name__ == "__main__":
    main()
