# csv_handler: Low-level CSV read and write helpers.

import csv
import os
import logging
from typing import List, Dict

log = logging.getLogger(__name__)


# CSVHandler: Stateless helpers for reading and writing CSV files.
class CSVHandler:

    # write_rows: Write a list-of-dicts to a CSV file with a given header order.
    @staticmethod
    def write_rows(filepath: str, fieldnames: List[str], rows: List[Dict]):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log.debug(f"Wrote {len(rows)} rows to {filepath}")

    # read_rows: Return list-of-dicts from a CSV file; empty list if missing.
    @staticmethod
    def read_rows(filepath: str) -> List[Dict]:
        if not os.path.exists(filepath):
            log.warning(f"CSV not found: {filepath}")
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
