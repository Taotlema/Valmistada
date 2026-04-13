# txt_handler: Plain-text file helpers for reading GTFS tables and writing summaries.

import os
import logging
from typing import List

log = logging.getLogger(__name__)


# TXTHandler: Stateless helpers for reading and writing plain text files.
class TXTHandler:

    # read_lines: Return stripped non-empty lines from a text file.
    @staticmethod
    def read_lines(filepath: str) -> List[str]:
        if not os.path.exists(filepath):
            log.warning(f"File not found: {filepath}")
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.rstrip() for line in f if line.strip()]

    # write_lines: Write a list of strings one per line to a file.
    @staticmethod
    def write_lines(filepath: str, lines: List[str]):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        log.debug(f"Wrote {len(lines)} lines to {filepath}")
