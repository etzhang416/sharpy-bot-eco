from typing import Dict, Optional

from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.combat2 import GenericMicro, Action, MoveType, MicroStep, CombatModel
from sharpy.general.extended_power import siege

high_priority: Dict[UnitTypeId, int] = {
    # Terran
    UnitTypeId.MULE: 3,
    UnitTypeId.SCV: 3,
    UnitTypeId.SIEGETANK: 30,
    UnitTypeId.SIEGETANKSIEGED: 30,  # sieged tanks are much higher priority than unsieged
    UnitTypeId.GHOST: 3,
    UnitTypeId.REAPER: 3,
    UnitTypeId.MARAUDER: 20,
    UnitTypeId.MARINE: 3,
    UnitTypeId.CYCLONE: 20,
    UnitTypeId.HELLION: 20,
    UnitTypeId.HELLIONTANK: 20,
    UnitTypeId.THOR: 30,
    UnitTypeId.MEDIVAC: -1,
    UnitTypeId.VIKINGFIGHTER: -1,
    UnitTypeId.VIKINGASSAULT: -1,
    UnitTypeId.LIBERATORAG: -1,
    UnitTypeId.LIBERATOR: -1,
    UnitTypeId.RAVEN: -1,
    UnitTypeId.BATTLECRUISER: -1,
    UnitTypeId.MISSILETURRET: 1,
    UnitTypeId.BUNKER: 20,
    # Zerg
    UnitTypeId.DRONE: 3,
    UnitTypeId.ZERGLING: 2,
    UnitTypeId.BANELING: 3,
    UnitTypeId.ULTRALISK: 4,
    UnitTypeId.QUEEN: 6,
    UnitTypeId.ROACH: 30,
    UnitTypeId.RAVAGER: 4,
    UnitTypeId.HYDRALISK: 8,
    UnitTypeId.HYDRALISKBURROWED: 8,
    UnitTypeId.LURKERMP: 30,
    UnitTypeId.LURKERMPBURROWED: 30,
    UnitTypeId.INFESTOR: 30,
    UnitTypeId.BROODLORD: -1,
    UnitTypeId.MUTALISK: -1,
    UnitTypeId.CORRUPTOR: -1,
    UnitTypeId.INFESTEDTERRAN: 1,
    UnitTypeId.LARVA: -1,
    UnitTypeId.EGG: -1,
    UnitTypeId.LOCUSTMP: -1,
    # Protoss
    UnitTypeId.SENTRY: 3,
    UnitTypeId.PROBE: 3,
    UnitTypeId.HIGHTEMPLAR: 10,
    UnitTypeId.DARKTEMPLAR: 30,
    UnitTypeId.ADEPT: 3,
    UnitTypeId.ZEALOT: 3,
    UnitTypeId.STALKER: 30,
    UnitTypeId.IMMORTAL: 30,
    UnitTypeId.COLOSSUS: 30,
    UnitTypeId.ARCHON: 20,
    UnitTypeId.SHIELDBATTERY: 1,
    UnitTypeId.PHOTONCANNON: 30,
    UnitTypeId.PYLON: 20,
    UnitTypeId.FLEETBEACON: 3,
}


class MicroImmortals(GenericMicro):
    def __init__(self):
        super().__init__()
        self.prio_dict = high_priority

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.model == CombatModel.StalkerToSiege and (
                self.move_type in {MoveType.SearchAndDestroy, MoveType.Assault, MoveType.Push, MoveType.ReGroup,
                                   MoveType.DefensiveRetreat, MoveType.ReGroup}
        ):
            siege_units = self.enemies_near_by.of_type(siege).filter(lambda u: (not u.is_flying) and u.is_armored)
            if siege_units:
                target = siege_units.closest_to(unit)
                if self.ready_to_shoot(unit) and current_command.is_attack:
                    return Action(target, True)

        if self.move_type in {MoveType.SearchAndDestroy, MoveType.Assault, MoveType.Push, MoveType.ReGroup,
                              MoveType.DefensiveRetreat, MoveType.ReGroup}:
            enemy_ground_force_armored = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 10) \
                .filter(lambda u: u.is_armored and not u.is_flying and not u.is_structure)
            if self.ready_to_shoot(unit) and current_command.is_attack and enemy_ground_force_armored.exists:
                return Action(enemy_ground_force_armored.closest_to(unit), True)

        return super().unit_solve_combat(unit, current_command)
