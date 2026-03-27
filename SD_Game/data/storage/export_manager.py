"""
Filename: export_manager.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
import os
import csv
import logging

# Modules
from data.models.output_models import TrialResult

log = logging.getLogger(__name__)


# ExportManager: Handles writing trial output to disk
class ExportManager:

    # __init__ (output_root: path to output/trials/)
    def __init__(self, output_root: str):
        self.output_root = output_root

    # export (result): Write one .txt file per month inside trial_N/ folder
    def export(self, result: TrialResult) -> str:
        trial_dir = os.path.join(self.output_root, f"trial_{result.trial_number}")
        os.makedirs(trial_dir, exist_ok=True)

        # Group rows by month
        months: dict = {}
        for row in result.to_rows():
            months.setdefault(row["Month"], []).append(row)

        for month_label, rows in months.items():
            safe_name = month_label.replace(" ", "_") + ".txt"
            filepath = os.path.join(trial_dir, safe_name)
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["Month", "Route", "Service Category",
                                "Service Day of the Week", "Average Daily Boardings"]
                )
                writer.writeheader()
                writer.writerows(rows)

        log.info(f"Trial {result.trial_number} exported → {trial_dir} "
                 f"({len(months)} monthly files)")
        return trial_dir