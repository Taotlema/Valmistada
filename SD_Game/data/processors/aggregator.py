# aggregator: Accumulates per-day boarding tallies and flushes them as monthly averages.

from collections import defaultdict
from typing import Dict, List, Tuple

from data.models.output_models import RidershipRecord, TrialResult


# Aggregator: Collects daily counts keyed by (month, route, category, day_type) then averages them.
class Aggregator:

    def __init__(self):
        # Key: (month_label, route_short, service_cat, day_type) -> list of daily boarding floats
        self._daily: Dict[Tuple[str, str, str, str], List[float]] = defaultdict(list)

    # record_day: Store one day's boarding count under its composite key.
    def record_day(self, month_label: str, route_short: str,
                   service_cat: str, day_type: str, boardings: float):
        self._daily[(month_label, route_short, service_cat, day_type)].append(boardings)

    # flush: Average each bucket and return a completed TrialResult; clears internal state.
    def flush(self, trial_number: int, city: str) -> TrialResult:
        result = TrialResult(trial_number=trial_number, city=city)
        for (month, route, cat, day_type), values in self._daily.items():
            avg = sum(values) / len(values) if values else 0.0
            result.add_record(RidershipRecord(
                month=month, route=route,
                service_category=cat, service_day=day_type,
                avg_daily_boardings=round(avg),
            ))
        self._daily.clear()
        return result
