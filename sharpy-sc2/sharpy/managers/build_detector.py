import enum
import sys
from typing import Dict, List, Optional, Set, TYPE_CHECKING
from sharpy.managers.manager_base import ManagerBase

if TYPE_CHECKING:
    from sharpy.managers import *

from sc2 import UnitTypeId, AbilityId, Race
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

townhall_start_types = {
    UnitTypeId.NEXUS,
    UnitTypeId.HATCHERY,
    UnitTypeId.COMMANDCENTER,
}


class EnemyRushBuild(enum.IntEnum):
    Macro = 0

    # protoss rushes:
    CannonRush = 1
    ProxyZealots = 2
    Zealots = 3
    ProxyRobo = 4
    RoboRush = 5
    AdeptRush = 6
    EarlyExpand = 7
    FastDT = 8
    AirOneBase = 9
    SafeExpand = 10
    ProxyBase = 11
    # AdeptRush = adepts/stalkers

    # zerg rushes:
    # for zerg, there's only fast expand or ealy rushes
    WorkerRush = 12
    LingRush = 13
    RoachRush = 14
    EcoExpand = 15
    NySwarm = 16

    # terran rushes:
    ProxyMarauders = 17
    ProxyFactory = 18
    TerranMacro = 19
    ProxyMarine = 20
    TerranOneBase = 21
    Bunker = 22
    TerranLate = 23


class EnemyMacroBuild(enum.IntEnum):
    StandardMacro = 0
    BattleCruisers = 1
    Banshees = 2
    Tempests = 3
    Carriers = 4
    DarkTemplars = 5
    Lurkers = 6
    Mutalisks = 7
    Mmm = 8


class BuildDetector(ManagerBase):
    """Enemy build detector."""

    def __init__(self):
        super().__init__()
        self.rush_build = EnemyRushBuild.Macro
        self.macro_build = EnemyMacroBuild.StandardMacro

        # Dictionary of unit or structure types that have been handled. tag is key
        # Note that snapshots of units / structures have a different tag.
        # Only visible buildings should be handled
        self.handled_unit_tags: Dict[int, UnitTypeId] = dict()
        # Timings when the unit was first seen or our estimate when structure was started building
        self.timings: Dict[UnitTypeId, List[float]] = dict()

    async def start(self, knowledge: "Knowledge"):
        # Just put them all her in order to avoid any issues with random enemy types
        if knowledge.ai.enemy_race == Race.Terran:
            self.timings[UnitTypeId.COMMANDCENTER] = [0]
        elif knowledge.ai.enemy_race == Race.Protoss:
            self.timings[UnitTypeId.NEXUS] = [0]
        elif knowledge.ai.enemy_race == Race.Zerg:
            self.timings[UnitTypeId.HATCHERY] = [0]
        elif knowledge.ai.enemy_race == Race.Random:
            self.timings[UnitTypeId.COMMANDCENTER] = [0]
            self.timings[UnitTypeId.NEXUS] = [0]
            self.timings[UnitTypeId.HATCHERY] = [0]

        return await super().start(knowledge)

    @property
    def rush_detected(self):
        return self.rush_build != EnemyRushBuild.Macro

    async def update(self):
        self._update_timings()
        self._rush_detection()
        self._build_detection()

    def _update_timings(self):
        # Let's update just seen structures for now
        for unit in self.ai.enemy_structures:
            if unit.is_snapshot:
                continue

            if unit.tag not in self.handled_unit_tags or self.handled_unit_tags.get(unit.tag) != unit.type_id:
                self.handled_unit_tags[unit.tag] = unit.type_id

                if self.is_first_townhall(unit):
                    continue  # Don't add it to timings

                real_type = self.real_type(unit.type_id)
                list = self.timings.get(real_type, None)
                if not list:
                    list = []
                    self.timings[real_type] = list

                start_time = self.unit_values.building_start_time(self.ai.time, real_type, unit.build_progress)
                list.append(start_time)

    def started(self, type_id: UnitTypeId, index: int = 0) -> float:
        """ Returns an absurdly large number when the building isn't started yet"""
        list = self.timings.get(type_id, None)
        if not list:
            return sys.float_info.max
        if len(list) > index:
            return list[index]
        return sys.float_info.max

    def is_first_townhall(self, structure: Unit) -> bool:
        """Returns true if the structure is the first townhall for a player."""
        # note: this does not handle a case if Terran flies its first CC to another position
        return (
                structure.position == self.knowledge.likely_enemy_start_location
                and structure.type_id in townhall_start_types
        )

    async def post_update(self):
        if self.debug:
            if self.rush_build != EnemyRushBuild.Macro:
                msg = f"Enemy build: {self.rush_build.name}"
            else:
                msg = f"Enemy build: {self.macro_build.name}"

            if hasattr(self.ai, "plan"):
                build_order = self.ai.plan
                if hasattr(build_order, "orders"):
                    plan = build_order.orders[0]
                    if hasattr(plan, "response"):
                        msg += f"\nOwn build: {plan.response.name}"
                    else:
                        msg += f"\nOwn build: {type(plan).__name__}"
            self.client.debug_text_2d(msg, Point2((0.75, 0.15)), None, 14)

    def _set_rush(self, value: EnemyRushBuild):
        if self.rush_build == value:
            # Trying to set the value to what it already was, skip.
            return
        self.rush_build = value
        self.print(f"POSSIBLE RUSH: {value.name}.")

    def _rush_detection(self):
        if self.ai.time > 8 * 60 + 15:
            if self.knowledge.enemy_race == Race.Protoss:
                self._set_rush(EnemyRushBuild.Macro)
                return
            elif self.knowledge.enemy_race == Race.Zerg:
                self._set_rush(EnemyRushBuild.EcoExpand)
                return
            elif self.knowledge.enemy_race == Race.Terran:
                self._set_rush(EnemyRushBuild.TerranLate)
                return
            else:
                # ??? random??
                self._set_rush(EnemyRushBuild.TerranLate)
                return

        if self.rush_build == EnemyRushBuild.WorkerRush:
            # Worker rush can never change to anything else
            return

        if self.rush_build == EnemyRushBuild.CannonRush and self.ai.time < 100:
            # will handle it at least to 1:40
            return

        workers_close = self.knowledge.known_enemy_workers.filter(
            lambda u: u.distance_to(self.ai.start_location) < u.distance_to(self.knowledge.likely_enemy_start_location)
        )

        if workers_close.amount > 9 and self.rush_build != EnemyRushBuild.LingRush:
            self._set_rush(EnemyRushBuild.WorkerRush)

        if self.knowledge.enemy_race == Race.Zerg:
            self._zerg_rushes()

        if self.knowledge.enemy_race == Race.Terran:
            self._terran_rushes()

        if self.knowledge.enemy_race == Race.Protoss:
            self._protoss_rushes()

    def _protoss_rushes(self):

        # Macro
        # CannonRush
        # ProxyZealots
        # Zealots
        # ProxyRobo =
        # AdeptRush or stalkers
        # WorkerRush

        # these are all one way rushes (can not adjust to another in time)
        if len(self.cache.enemy(UnitTypeId.NEXUS)) > 1:
            if 1 * 60 + 50 <= self.ai.time <= 2 * 60 + 10:
                self._set_rush(EnemyRushBuild.EarlyExpand)
                return
            if self.ai.time >= 2 * 60 + 40 and self.rush_build != EnemyRushBuild.EarlyExpand and \
                    self.rush_build != EnemyRushBuild.RoboRush and self.rush_build != EnemyRushBuild.ProxyRobo \
                    and self.rush_build != EnemyRushBuild.CannonRush and self.rush_build != EnemyRushBuild.AirOneBase:
                self._set_rush(EnemyRushBuild.SafeExpand)
                return  # enemy has expanded, no rush detection
        if 2 * 60 + 15 < self.ai.time <= 3 * 60 + 20 and \
                self.cache.enemy(UnitTypeId.PHOTONCANNON).ready.amount >= 1 and \
                self.rush_build == EnemyRushBuild.EarlyExpand:
            self._set_rush(EnemyRushBuild.SafeExpand)
            return  # enemy has expanded, no rush detection

        # at 1:05 eco build will scout 2nd and see cannon rush
        # if they didn't pylon here, that's a bad cannon rush and they will gg
        enemy_near_my_2nd = self.cache.enemy_in_range(self.ai.start_location, 50).structure
        if enemy_near_my_2nd and self.ai.time <= 2 * 60:
            self._set_rush(EnemyRushBuild.CannonRush)
            return

        # my firt scout goes to enemy 2nd base at ~ 1:50 base ramp at ~ 1:55
        # see most of the plain ~ 2:20

        if 2 * 60 + 15 <= self.ai.time <= 3 * 60:
            if self.cache.enemy(UnitTypeId.GATEWAY).amount >= 3:
                if self.cache.enemy(UnitTypeId.CYBERNETICSCORE).amount >= 1:
                    self._set_rush(EnemyRushBuild.AdeptRush)
                    return
            if self.cache.enemy(UnitTypeId.FORGE).amount >= 1:
                if self.cache.enemy(UnitTypeId.GATEWAY).amount == 0 and \
                        self.cache.enemy(UnitTypeId.ASSIMILATOR).amount == 0:
                    self._set_rush(EnemyRushBuild.CannonRush)
                    return
                elif self.cache.enemy(UnitTypeId.ASSIMILATOR).amount >= 1:
                    self._set_rush(EnemyRushBuild.FastDT)
                    return

            if self.cache.enemy(UnitTypeId.PYLON).amount < 2:
                # must be cheeseing something
                if self.cache.enemy(UnitTypeId.ASSIMILATOR).amount < 1 and \
                        self.rush_build == EnemyRushBuild.Macro:
                    # must be cheeseing ProxyZealots because no gas
                    if self.cache.enemy(UnitTypeId.ADEPT).amount >= 4:
                        self._set_rush(EnemyRushBuild.AdeptRush)
                        return
                    # he blocked himself
                    if self.cache.enemy(UnitTypeId.NEXUS).amount == 0:
                        self._set_rush(EnemyRushBuild.ProxyRobo)
                    else:
                        self._set_rush(EnemyRushBuild.ProxyZealots)
                    return
            else:
                if self.cache.enemy(UnitTypeId.STARGATE).amount >= 1 and \
                        self.cache.enemy(UnitTypeId.GATEWAY).amount == 1:
                    self._set_rush(EnemyRushBuild.AirOneBase)
                    return

                if self.cache.enemy(UnitTypeId.ROBOTICSFACILITY).amount >= 1:
                    self._set_rush(EnemyRushBuild.RoboRush)
                    return

                if self.cache.enemy(UnitTypeId.GATEWAY).amount < 2 and \
                        self.cache.enemy(UnitTypeId.CYBERNETICSCORE).amount >= 1 and \
                        self.cache.enemy(UnitTypeId.ASSIMILATOR).amount > 1 and \
                        self.rush_build == EnemyRushBuild.Macro:
                    self._set_rush(EnemyRushBuild.ProxyRobo)
                    return
                elif self.cache.enemy(UnitTypeId.GATEWAY).amount >= 2 and \
                        self.cache.enemy(UnitTypeId.CYBERNETICSCORE).amount >= 1 and \
                        self.rush_build == EnemyRushBuild.Macro:
                    if self.cache.enemy(UnitTypeId.ROBOTICSFACILITY).amount >= 1:
                        self._set_rush(EnemyRushBuild.RoboRush)
                    elif self.cache.enemy(UnitTypeId.ASSIMILATOR).amount >= 1:
                        self._set_rush(EnemyRushBuild.Macro)
                    else:
                        self._set_rush(EnemyRushBuild.ProxyZealots)
                    return

        # fastest proxy robo has 2 robo finished at ~ 2:50
        # ~3:20 1 immortal+ 1 prism
        # ~3:30 to my base 1st/2nd
        close_buildings = self.cache.enemy_in_range(self.ai.start_location, 80).structure
        if close_buildings:
            if close_buildings(UnitTypeId.ROBOTICSFACILITY) and self.rush_build == EnemyRushBuild.Macro:
                self._set_rush(EnemyRushBuild.ProxyRobo)
                return

        # ~ 3:30 HallucinatedPhoenixScout reach enemy base
        if 2 * 60 + 15 < self.ai.time <= 4 * 60 + 20 and \
                self.cache.enemy(UnitTypeId.NEXUS).ready.amount < 2 and \
                self.rush_build != EnemyRushBuild.CannonRush \
                and self.rush_build != EnemyRushBuild.EarlyExpand \
                and self.rush_build != EnemyRushBuild.ProxyZealots:
            # possible one base tech all in
            if self.cache.enemy(UnitTypeId.GATEWAY).amount + \
                    self.cache.enemy(UnitTypeId.STARGATE).amount + \
                    self.cache.enemy(UnitTypeId.ROBOTICSFACILITY).amount >= 3:
                if self.cache.enemy(UnitTypeId.DARKSHRINE).amount > 0:
                    self._set_rush(EnemyRushBuild.FastDT)
                    return
                if self.cache.enemy(UnitTypeId.STARGATE).amount > 0 and \
                        self.rush_build != EnemyRushBuild.RoboRush:
                    self._set_rush(EnemyRushBuild.AirOneBase)
                    return
                if self.cache.enemy(UnitTypeId.ROBOTICSFACILITY).amount > 0 and \
                        self.rush_build != EnemyRushBuild.AirOneBase:
                    self._set_rush(EnemyRushBuild.RoboRush)
                    return
            elif self.rush_build != EnemyRushBuild.ProxyRobo and \
                    self.rush_build != EnemyRushBuild.RoboRush and \
                    self.rush_build != EnemyRushBuild.AirOneBase and \
                    self.rush_build != EnemyRushBuild.AdeptRush and \
                    self.rush_build != EnemyRushBuild.ProxyZealots and \
                    self.rush_build != EnemyRushBuild.FastDT:
                # must be proxying base
                self._set_rush(EnemyRushBuild.Macro)
                return

    def _zerg_rushes(self):
        # for zerg, there's only fast expand or ealy rushes
        # WorkerRush = 12 handled in reush detection function
        # LingRush = 13
        # EcoExpand = 14
        enemy_near_my_2nd = self.cache.enemy_in_range(self.ai.start_location, 45).structure
        if enemy_near_my_2nd and self.ai.time <= 2 * 60:
            self._set_rush(EnemyRushBuild.LingRush)
            return

        if self.rush_build == EnemyRushBuild.Macro:
            hatcheries: Units = self.cache.enemy(UnitTypeId.HATCHERY)
            if 70 <= self.ai.time <= 90:
                if len(hatcheries) >= 2:
                    return self._set_rush(EnemyRushBuild.EcoExpand)

            roachwarren: Units = self.cache.enemy(UnitTypeId.ROACHWARREN)
            roaches: Units = self.cache.enemy(UnitTypeId.ROACH)
            lings: Units = self.cache.enemy(UnitTypeId.ZERGLING)
            if 75 <= self.ai.time <= 95:
                if len(roaches) + len(roachwarren) >= 1:
                    return self._set_rush(EnemyRushBuild.RoachRush)
                elif len(lings) >= 1:
                    return self._set_rush(EnemyRushBuild.LingRush)

            if self.ai.time > 95:
                return self._set_rush(EnemyRushBuild.LingRush)
        if self.rush_build == EnemyRushBuild.LingRush:
            if 95 <= self.ai.time <= 101 and \
                    len(self.cache.enemy(UnitTypeId.HATCHERY)) >= 2:
                return self._set_rush(EnemyRushBuild.EcoExpand)
        if self.ai.time <= 3*60+50 and \
                len(self.cache.enemy(UnitTypeId.HATCHERY)) >= 2:
            return self._set_rush(EnemyRushBuild.EcoExpand)

    def _terran_rushes(self):

        if self.rush_build == EnemyRushBuild.ProxyMarine or self.rush_build == EnemyRushBuild.ProxyMarauders or \
                self.rush_build == EnemyRushBuild.ProxyFactory:
            if len(self.cache.enemy(
                    [UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS])) > 1:
                self._set_rush(EnemyRushBuild.TerranMacro)
                return

        if len(self.cache.enemy(
                [UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS])) > 1:
            if 1 * 60 + 20 <= self.ai.time <= 1 * 60 + 33:
                self._set_rush(EnemyRushBuild.EarlyExpand)
                return
            if 2 * 60 <= self.ai.time <= 2 * 60 + 20 and self.rush_build != EnemyRushBuild.EarlyExpand:
                self._set_rush(EnemyRushBuild.TerranMacro)
                return

        main_barracks_num = self.knowledge.known_enemy_structures(UnitTypeId.BARRACKS) \
            .closer_than(30, self.knowledge.enemy_main_zone.center_location).amount
        main_factory_num = self.knowledge.known_enemy_structures(UnitTypeId.FACTORY) \
            .closer_than(30, self.knowledge.enemy_main_zone.center_location).amount
        bases = len(self.cache.enemy(
            [UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS]))
        fortress = len(self.cache.enemy([UnitTypeId.PLANETARYFORTRESS]))
        bunker = len(self.cache.enemy(
            [UnitTypeId.BUNKER]).closer_than(40, self.knowledge.enemy_main_zone.center_location))

        enemy_near_my_2nd = self.cache.enemy_in_range(self.ai.start_location, 50).structure
        if 1 * 60 + 39 <= self.ai.time <= 3 * 60 + 41:
            if enemy_near_my_2nd:
                self._set_rush(EnemyRushBuild.Bunker)
                return

        if 1 * 60 + 39 <= self.ai.time <= 1 * 60 + 41 and self.rush_build != EnemyRushBuild.EarlyExpand:
            # see all gas positions
            if main_barracks_num + main_factory_num > 1:
                self._set_rush(EnemyRushBuild.TerranOneBase)
                return
            if main_barracks_num == 0:
                if self.cache.enemy(UnitTypeId.REFINERY).amount == 0:
                    self._set_rush(EnemyRushBuild.ProxyMarine)
                    return
                elif self.cache.enemy(UnitTypeId.REFINERY).amount == 1:
                    self._set_rush(EnemyRushBuild.ProxyMarauders)
                    return
                elif self.cache.enemy(UnitTypeId.REFINERY).amount == 2:
                    self._set_rush(EnemyRushBuild.ProxyFactory)
                    return
            elif main_barracks_num == 1:
                if self.cache.enemy(UnitTypeId.REFINERY).amount == 1:
                    self._set_rush(EnemyRushBuild.TerranMacro)
                    return
                elif self.cache.enemy(UnitTypeId.REFINERY).amount == 2:
                    self._set_rush(EnemyRushBuild.TerranOneBase)
                    return
                else:
                    self._set_rush(EnemyRushBuild.ProxyMarine)
                    return
            elif self.cache.enemy(UnitTypeId.REFINERY).amount == 0:
                # a lot of barracks
                self._set_rush(EnemyRushBuild.ProxyMarine)
                return
            else:
                self._set_rush(EnemyRushBuild.TerranOneBase)
                return

        if 2 * 60 <= self.ai.time <= 2 * 60 + 10:
            if self.rush_build == EnemyRushBuild.TerranMacro and \
                    self.knowledge.unit_cache.enemy(UnitTypeId.MARAUDER).ready.exists:
                self._set_rush(EnemyRushBuild.TerranOneBase)
            if bases < 2 and self.rush_build == EnemyRushBuild.TerranMacro:
                self._set_rush(EnemyRushBuild.TerranOneBase)
                return

        if 2 * 60 + 20 <= self.ai.time <= 2 * 60 + 30:
            if bases >= 2 and self.rush_build == EnemyRushBuild.TerranOneBase:
                self._set_rush(EnemyRushBuild.TerranMacro)
                return

        if 3 * 60 + 50 <= self.ai.time <= 5 * 60 + 50:
            if fortress >= 1:
                self._set_rush(EnemyRushBuild.TerranLate)

            # TODO might wanna check 4BB RUSH at 3:05

    def _build_detection(self):
        if self.macro_build != EnemyMacroBuild.StandardMacro:
            # Only set macro build once
            return

        if self.knowledge.enemy_race == Race.Terran:
            if self.ai.time < 7 * 60 and self.cache.enemy(UnitTypeId.BATTLECRUISER):
                self.macro_build = EnemyMacroBuild.BattleCruisers
            elif self.ai.time < 7 * 60 and self.cache.enemy(UnitTypeId.BANSHEE):
                self.macro_build = EnemyMacroBuild.Banshees
            elif 7 * 60 < self.ai.time < 8 * 60:
                mmm_check = (
                        self.knowledge.enemy_units_manager.unit_count(UnitTypeId.MARINE)
                        > self.knowledge.enemy_units_manager.unit_count(UnitTypeId.MARAUDER)
                        > 15
                        > self.knowledge.enemy_units_manager.unit_count(UnitTypeId.MEDIVAC)
                        > 0
                )
                if mmm_check:
                    self.macro_build = EnemyMacroBuild.Mmm

        if self.knowledge.enemy_race == Race.Protoss:
            if self.ai.time < 7 * 60 and self.cache.enemy(UnitTypeId.TEMPEST):
                self.macro_build = EnemyMacroBuild.Tempests
            if self.ai.time < 7 * 60 and self.cache.enemy(UnitTypeId.CARRIER):
                self.macro_build = EnemyMacroBuild.Carriers
            if self.ai.time < 7 * 60 and self.cache.enemy(UnitTypeId.DARKTEMPLAR):
                self.macro_build = EnemyMacroBuild.DarkTemplars

        if self.knowledge.enemy_race == Race.Zerg:
            if self.ai.time < 7 * 60 and self.cache.enemy(UnitTypeId.MUTALISK):
                self.macro_build = EnemyMacroBuild.Mutalisks
            if self.ai.time < 7 * 60 and self.cache.enemy(UnitTypeId.LURKERMP):
                self.macro_build = EnemyMacroBuild.Lurkers

        if self.macro_build != EnemyMacroBuild.StandardMacro:
            self.print(f"Enemy normal build recognized as {self.macro_build.name}")
