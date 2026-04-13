# output_models: Mirror the real SFMTA ridership schema for exported results.

from dataclasses import dataclass, field
from typing import List


# RidershipRecord: One row of monthly synthetic output matching the SFMTA schema.
@dataclass
class RidershipRecord:
    month:               str    # "January 2019"
    route:               str
    service_category:    str
    service_day:         str    # "Weekday" | "Saturday" | "Sunday"
    avg_daily_boardings: float


# TrialResult: All records produced by a single completed simulation run.
@dataclass
class TrialResult:
    trial_number: int
    city:         str
    records:      List[RidershipRecord] = field(default_factory=list)

    # add_record: Append one monthly ridership row to the result.
    def add_record(self, record: RidershipRecord):
        self.records.append(record)

    # to_rows: Return list-of-dicts ready for CSV/TXT export.
    def to_rows(self) -> List[dict]:
        return [
            {
                "Month":                   r.month,
                "Route":                   r.route,
                "Service Category":        r.service_category,
                "Service Day of the Week": r.service_day,
                "Average Daily Boardings": f"{r.avg_daily_boardings:,.0f}",
            }
            for r in self.records
        ]
