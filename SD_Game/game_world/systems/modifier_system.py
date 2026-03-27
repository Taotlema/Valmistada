"""
Filename: modifier_system.py
Author: Ayemhenre Isikhuemhen
Description: Applies loaded modifier data (population, land use) to scale
             per-stop demand weights across the network.
Last Updated: March, 2026
"""

# Libraries
from typing import List

# Modules
from game_world.entities.station import Station


# ModifierSystem: One-time demand weight assignment at simulation start
class ModifierSystem:

    # __init__ (modifier_loader)
    def __init__(self, modifier_loader):
        self._modifier = modifier_loader

    # apply (stations): Adjust base_demand on each station using modifier data
    def apply(self, stations: List[Station]):
        if not self._modifier:
            return

        density = self._modifier.density_factor()
        for station in stations:
            station.base_demand *= density

        res_parcels   = self._modifier.land_use_counts.get("RESIDENT", 0)
        mixed_parcels = self._modifier.land_use_counts.get("MIXRES", 0)
        total_parcels = sum(self._modifier.land_use_counts.values()) or 1
        res_share     = (res_parcels + mixed_parcels) / total_parcels

        for station in stations:
            station.base_demand *= (0.8 + 0.4 * res_share)