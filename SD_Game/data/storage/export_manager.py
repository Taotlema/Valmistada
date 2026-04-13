# export_manager: Writes a completed TrialResult to disk as monthly txt files.

import os
import csv
import logging

from data.models.output_models import TrialResult

log = logging.getLogger(__name__)

# Column order matches the real SFMTA ridership schema exactly
_FIELDS = [
    "Month", "Route", "Service Category",
    "Service Day of the Week", "Average Daily Boardings",
]


# ExportManager: Writes one txt file per month inside a numbered trial folder.
class ExportManager:

    def __init__(self, output_root: str):
        self.output_root = output_root

    # export: Group rows by month and write each group to its own txt file.
    def export(self, result: TrialResult) -> str:
        trial_dir = os.path.join(self.output_root, f"trial_{result.trial_number}")
        os.makedirs(trial_dir, exist_ok=True)

        # Group all records by their month label
        months: dict = {}
        for row in result.to_rows():
            months.setdefault(row["Month"], []).append(row)

        for month_label, rows in months.items():
            safe_name = month_label.replace(" ", "_") + ".txt"
            filepath  = os.path.join(trial_dir, safe_name)
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_FIELDS)
                writer.writeheader()
                writer.writerows(rows)

        log.info(f"Trial {result.trial_number} exported - "
                 f"{len(months)} files to {trial_dir}")
        return trial_dir
