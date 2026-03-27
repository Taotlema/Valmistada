"""
Filename: aggregator.py
Author: Ayemhenre Isikhuemhen
Description: Rolls up per-day simulation tallies into monthly ridership records.
Last Updated: March, 2026
"""

# Libraries
from collections import defaultdict
from typing import Dict, List, Tuple

# Modules
from data.models.output_models import RidershipRecord, TrialResult


# Aggregator: Converts (month, route, day_type) daily lists into monthly averages
class Aggregator:

    # __init__: Internal accumulator keyed by (month_label, route, day_type)
    def __init__(self):
        # key → list of daily boarding totals
        self._daily: Dict[Tuple[str, str, str, str], List[float]] = defaultdict(list)

    # record_day (month_label, route_short, service_cat, day_type, boardings)
    def record_day(self, month_label: str, route_short: str,
                   service_cat: str, day_type: str, boardings: float):
        key = (month_label, route_short, service_cat, day_type)
        self._daily[key].append(boardings)

    # flush (trial_number, city): Average each bucket and return a TrialResult
    def flush(self, trial_number: int, city: str) -> TrialResult:
        result = TrialResult(trial_number=trial_number, city=city)
        for (month, route, cat, day_type), values in self._daily.items():
            avg = sum(values) / len(values) if values else 0.0
            result.add_record(RidershipRecord(
                month=month,
                route=route,
                service_category=cat,
                service_day=day_type,
                avg_daily_boardings=round(avg),
            ))
        self._daily.clear()
        return result