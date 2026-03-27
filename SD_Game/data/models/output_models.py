"""
Filename: output_models.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
from dataclasses import dataclass, field
from typing import List


# RidershipRecord: One row of monthly synthetic output — mirrors the real data schema
@dataclass
class RidershipRecord:
    month: str                  # "January 2019"
    route: str
    service_category: str
    service_day: str            # "Weekday" / "Saturday" / "Sunday"
    avg_daily_boardings: float


# TrialResult: All records produced by a single simulation run
@dataclass
class TrialResult:
    trial_number: int
    city: str
    records: List[RidershipRecord] = field(default_factory=list)

    # add_record: Append one monthly ridership row
    def add_record(self, record: RidershipRecord):
        self.records.append(record)

    # to_rows: Return list-of-dicts ready for CSV/txt export
    def to_rows(self) -> List[dict]:
        return [
            {
                "Month": r.month,
                "Route": r.route,
                "Service Category": r.service_category,
                "Service Day of the Week": r.service_day,
                "Average Daily Boardings": f"{r.avg_daily_boardings:,.0f}",
            }
            for r in self.records
        ]