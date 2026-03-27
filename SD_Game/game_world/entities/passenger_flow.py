"""
Filename: passenger_flow.py
Author: Ayemhenre Isikhuemhen
Description: Computes a demand multiplier for any given sim tick based on
             time of day, day type, seasonal index, and modifier data.
Last Updated: March, 2026
"""


# PassengerFlow: Stateless demand-factor calculator
class PassengerFlow:

    # __init__ (sim_config: simulation_config.yaml dict, modifier_loader)
    def __init__(self, sim_config: dict, modifier_loader=None):
        self._cfg      = sim_config["simulation"]
        self._modifier = modifier_loader

    # demand_factor (hour, day_type, month): Combined multiplier for one tick
    def demand_factor(self, hour: float, day_type: str, month: int) -> float:
        factor = 1.0

        dt_mult = self._cfg["day_type_multipliers"]
        factor *= dt_mult.get(day_type, 1.0)

        seasonal = self._cfg["seasonal_index"]
        factor *= seasonal.get(month, 1.0)

        peak  = self._cfg["peak_boost"]
        am_on = peak["am_start"] <= hour < peak["am_end"]
        pm_on = peak["pm_start"] <= hour < peak["pm_end"]
        if am_on or pm_on:
            factor *= peak["factor"]

        # Night-time dip before 5 AM
        if hour < 5.0:
            factor *= 0.3 + 0.7 * (hour / 5.0)

        if self._modifier:
            factor *= self._modifier.density_factor()

        return max(factor, 0.0)

    # noise_factor: Stochastic daily noise
    def noise_factor(self, rng) -> float:
        std = self._cfg.get("noise_std", 0.08)
        return max(0.5, 1.0 + rng.gauss(0, std))