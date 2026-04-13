# passenger_flow: Stateless demand-factor calculator used by RidershipSystem each sim day.


# PassengerFlow: Combines day type, season, peak hours, and population into one demand multiplier.
class PassengerFlow:

    def __init__(self, sim_config: dict, modifier_loader=None):
        self._cfg      = sim_config["simulation"]
        self._modifier = modifier_loader

    # demand_factor: Combined multiplier for a given hour, day type, and month.
    def demand_factor(self, hour: float, day_type: str, month: int) -> float:
        factor = 1.0

        # Day-type weight: Weekday=1.0, Saturday=0.72, Sunday=0.58
        factor *= self._cfg["day_type_multipliers"].get(day_type, 1.0)

        # Seasonal index varies Jan to Dec
        factor *= self._cfg["seasonal_index"].get(month, 1.0)

        # AM and PM peak boost for commute hours
        peak  = self._cfg["peak_boost"]
        in_am = peak["am_start"] <= hour < peak["am_end"]
        in_pm = peak["pm_start"] <= hour < peak["pm_end"]
        if in_am or in_pm:
            factor *= peak["factor"]

        # Night-time dip before 5 AM fades in proportionally
        if hour < 5.0:
            factor *= 0.3 + 0.7 * (hour / 5.0)

        # Scale by city population density relative to a 1M-person baseline
        if self._modifier:
            factor *= self._modifier.density_factor()

        return max(factor, 0.0)

    # noise_factor: Gaussian daily randomness centred on 1.0.
    def noise_factor(self, rng) -> float:
        std = self._cfg.get("noise_std", 0.08)
        return max(0.5, 1.0 + rng.gauss(0, std))
