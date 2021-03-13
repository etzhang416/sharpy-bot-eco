from sc2 import UnitTypeId
from sc2.unit import Unit

from sharpy.plans.acts.act_base import ActBase


class DefensivePylons(ActBase):
    """Act of starting to build new buildings up to specified count"""

    def __init__(self, to_base_index: int):
        self.to_base_index = to_base_index

        super().__init__()

    async def execute(self) -> bool:
        map_center = self.ai.game_info.map_center

        # Go through zones so that furthest expansions are fortified first
        zones = self.knowledge.expansion_zones
        for i in range(0, len(zones)):
            zone = zones[i]
            # Filter out zones that aren't ours and own zones that we are about to lose.
            if zone.our_townhall is None or zone.known_enemy_power.ground_power > zone.our_power.ground_presence:
                continue

            if self.to_base_index is not None and i != self.to_base_index:
                # Defenses are not ordered to that base
                continue

            closest_pylon: Unit = None
            pylons = zone.our_units(UnitTypeId.PYLON)
            if pylons.exists:
                closest_pylon = pylons.closest_to(zone.center_location)

            available_minerals = self.ai.minerals - self.knowledge.reserved_minerals
            can_afford = available_minerals >= 100

            if closest_pylon is None or closest_pylon.distance_to(zone.center_location) > 10:
                # We need a pylon, but only if one isn't already on the way
                if not self.pending_build(UnitTypeId.PYLON) and can_afford:
                    await self.ai.build(UnitTypeId.PYLON, near=zone.center_location.towards(map_center, 4))
        return True


class MineralCannons(ActBase):
    """Act of starting to build new buildings up to specified count"""

    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        all_ready = True
        zones = self.knowledge.our_zones
        for zone in zones:
            # Filter out zones that aren't ours and own zones that we are about to lose.
            if zone.our_townhall is None or zone.known_enemy_power.ground_power > zone.our_power.ground_presence:
                continue
            if zone.our_photon_cannons.exists:
                continue
            if zone.our_townhall is not None and zone.our_townhall.build_progress < 1:
                continue
            energy_pylon: Unit = None

            field_pylon = zone.our_units(UnitTypeId.PYLON).filter(lambda u: u.distance_to(
                zone.behind_mineral_position_center.towards(zone.center_location, -1)) <= 7)
            if field_pylon.exists:
                energy_pylon = field_pylon.first

            if energy_pylon is None:
                all_ready = False
                # We need a pylon, but only if one isn't already on the way
                can_afford: bool = (self.ai.minerals - self.knowledge.reserved_minerals >= 100)
                if (not self.pending_build(UnitTypeId.PYLON)) and can_afford:
                    pos = zone.behind_mineral_position_center.towards(zone.center_location, -1)
                    await self.ai.build(UnitTypeId.PYLON, near=pos)
                continue

            mineral_cannon_pos = zone.center_location.towards(zone.behind_mineral_position_center, 4)
            mineral_cannon_num = zone.our_units(UnitTypeId.PHOTONCANNON).filter(lambda u: u.distance_to(
                mineral_cannon_pos) <= 5).amount

            if mineral_cannon_num < 1:
                all_ready = False
                can_afford_cannon: bool = (self.ai.minerals - self.knowledge.reserved_minerals >= 150)
                if energy_pylon.is_ready and can_afford_cannon and (not self.pending_build(UnitTypeId.PHOTONCANNON)):
                    await self.ai.build(UnitTypeId.PHOTONCANNON, near=mineral_cannon_pos)
        return all_ready

class MineralBatteries(ActBase):
    """Act of starting to build new buildings up to specified count"""

    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        all_ready = True
        zones = self.knowledge.our_zones
        for zone in zones:
            # Filter out zones that aren't ours and own zones that we are about to lose.
            if zone.our_townhall is None or zone.known_enemy_power.ground_power > zone.our_power.ground_presence:
                continue
            if zone.our_photon_cannons.exists:
                continue
            if zone.our_townhall is not None and zone.our_townhall.build_progress < 1:
                continue
            energy_pylon: Unit = None

            field_pylon = zone.our_units(UnitTypeId.PYLON).filter(lambda u: u.distance_to(
                zone.behind_mineral_position_center.towards(zone.center_location, -1)) <= 7)
            if field_pylon.exists:
                energy_pylon = field_pylon.first

            if energy_pylon is None:
                all_ready = False
                # We need a pylon, but only if one isn't already on the way
                can_afford: bool = (self.ai.minerals - self.knowledge.reserved_minerals >= 100)
                if (not self.pending_build(UnitTypeId.PYLON)) and can_afford:
                    pos = zone.behind_mineral_position_center.towards(zone.center_location, -1)
                    await self.ai.build(UnitTypeId.PYLON, near=pos)
                continue

            mineral_battery_pos = zone.center_location.towards(zone.behind_mineral_position_center, 4)
            mineral_battery_num = zone.our_units(UnitTypeId.SHIELDBATTERY).filter(lambda u: u.distance_to(
                mineral_battery_pos) <= 5).amount

            if mineral_battery_num < 1:
                all_ready = False
                can_afford: bool = (self.ai.minerals - self.knowledge.reserved_minerals >= 75)
                if energy_pylon.is_ready and can_afford and (not self.pending_build(UnitTypeId.SHIELDBATTERY)):
                    await self.ai.build(UnitTypeId.SHIELDBATTERY, near=mineral_battery_pos)
        return all_ready
