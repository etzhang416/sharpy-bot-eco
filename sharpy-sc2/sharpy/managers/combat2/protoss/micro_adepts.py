from typing import Dict, Optional

from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.combat2 import GenericMicro, Action, MoveType, MicroStep, CombatModel

high_priority: Dict[UnitTypeId, int] = {
    # Terran
    UnitTypeId.MULE: 30,
    UnitTypeId.SCV: 30,
    UnitTypeId.SIEGETANK: 3,
    UnitTypeId.SIEGETANKSIEGED: 5,  # sieged tanks are much higher priority than unsieged
    UnitTypeId.GHOST: 10,
    UnitTypeId.REAPER: 8,
    UnitTypeId.MARAUDER: 4,
    UnitTypeId.MARINE: 8,
    UnitTypeId.CYCLONE: 4,
    UnitTypeId.HELLION: 8,
    UnitTypeId.HELLIONTANK: 3,
    UnitTypeId.THOR: 3,
    UnitTypeId.MEDIVAC: -1,
    UnitTypeId.VIKINGFIGHTER: -1,
    UnitTypeId.VIKINGASSAULT: -1,
    UnitTypeId.LIBERATORAG: -1,
    UnitTypeId.LIBERATOR: -1,
    UnitTypeId.RAVEN: -1,
    UnitTypeId.BATTLECRUISER: -1,
    UnitTypeId.MISSILETURRET: 1,
    UnitTypeId.BUNKER: 2,
    # Zerg
    UnitTypeId.DRONE: 30,
    UnitTypeId.ZERGLING: 8,
    UnitTypeId.BANELING: 10,
    UnitTypeId.ULTRALISK: 4,
    UnitTypeId.QUEEN: 6,
    UnitTypeId.ROACH: 4,
    UnitTypeId.RAVAGER: 4,
    UnitTypeId.HYDRALISK: 8,
    UnitTypeId.HYDRALISKBURROWED: 8,
    UnitTypeId.LURKERMP: 3,
    UnitTypeId.LURKERMPBURROWED: 3,
    UnitTypeId.INFESTOR: 10,
    UnitTypeId.BROODLORD: -1,
    UnitTypeId.MUTALISK: -1,
    UnitTypeId.CORRUPTOR: -1,
    UnitTypeId.INFESTEDTERRAN: 1,
    UnitTypeId.LARVA: -1,
    UnitTypeId.EGG: -1,
    UnitTypeId.LOCUSTMP: -1,
    # Protoss
    UnitTypeId.SENTRY: 9,
    UnitTypeId.PROBE: 30,
    UnitTypeId.HIGHTEMPLAR: 10,
    UnitTypeId.DARKTEMPLAR: 9,
    UnitTypeId.ADEPT: 8,
    UnitTypeId.ZEALOT: 8,
    UnitTypeId.STALKER: 4,
    UnitTypeId.IMMORTAL: 2,
    UnitTypeId.COLOSSUS: 3,
    UnitTypeId.ARCHON: 4,
    UnitTypeId.SHIELDBATTERY: 1,
    UnitTypeId.PHOTONCANNON: 1,
    UnitTypeId.PYLON: 2,
    UnitTypeId.FLEETBEACON: 3,
}


class MicroAdepts(GenericMicro):
    def __init__(self, micro_shades: bool = True):
        super().__init__()
        self.prio_dict = high_priority
        self.micro_shades = micro_shades

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        shuffler = unit.tag % 10

        target: Optional[Unit] = None
        enemy: Unit

        target = self.get_target(self.enemies_near_by, target, unit, shuffler)
        if self.micro_shades:
            shade_tag = self.cd_manager.adept_to_shade.get(unit.tag, None)
            if shade_tag:
                shade = self.cache.by_tag(shade_tag)
                if shade:
                    if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
                        self.ai.do(shade.move(self.knowledge.expansion_zones[0].center_location))
                    else:
                        if target is None:
                            nearby: Units = self.knowledge.unit_cache.enemy_in_range(shade.position, 12)
                            target = self.get_target(nearby, target, shade, shuffler)
                        if target is not None:
                            pos: Point2 = target.position
                            self.ai.do(shade.move(pos.towards(unit, -1)))

        if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            if self.cd_manager.is_ready(unit.tag, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT):
                base = self.knowledge.expansion_zones[0].center_location
                return Action(base, False, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT)

        if self.move_type in {MoveType.Harass}:
            if self.cd_manager.is_ready(unit.tag, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT):
                if target is not None:
                    return Action(target.position, False, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT)
            else:
                enemy_bunker = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 10).of_type(
                    [UnitTypeId.BUNKER, UnitTypeId.WIDOWMINE, UnitTypeId.WIDOWMINEBURROWED, UnitTypeId.PHOTONCANNON]
                ).filter(lambda u: u.is_ready)
                if enemy_bunker.exists:
                    return Action(
                        unit.position.towards(enemy_bunker.closest_to(unit), -4),
                        False)

                enemy_workers = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 9).of_type(
                    [UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE]
                )
                half_dead = enemy_workers.filter(lambda u: u.shield_health_percentage <= 0.6)
                enemy_ground_force = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 10).of_type(
                    [UnitTypeId.STALKER, UnitTypeId.ADEPT, UnitTypeId.QUEEN]
                )
                enemy_lings = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 8).of_type(
                    [UnitTypeId.ZERGLING, UnitTypeId.MARINE, UnitTypeId.ZEALOT, UnitTypeId.REAPER]
                )
                if half_dead.exists and self.ready_to_shoot(unit):
                    return Action(half_dead.closest_to(unit), True)
                else:
                    if enemy_lings.exists:
                        if self.ready_to_shoot(unit):
                            return Action(enemy_lings.closest_to(unit), True)
                        else:
                            return Action(
                                unit.position.towards(enemy_lings.closest_to(unit), -2),
                                False)
                    if enemy_workers.exists and self.ready_to_shoot(unit):
                        return Action(enemy_workers.closest_to(unit), True)

                    if enemy_ground_force.exists:
                        return Action(
                            unit.position.towards(enemy_ground_force.closest_to(unit), -3),
                            False)

        if self.move_type in \
                {MoveType.SearchAndDestroy, MoveType.Assault, MoveType.Push, MoveType.ReGroup} \
                and self.model in \
                {CombatModel.RoachToStalker, CombatModel.AssaultRamp, CombatModel.StalkerToSiege,
                 CombatModel.StalkerToRoach}:
            if self.cd_manager.is_ready(unit.tag, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT):
                if target is not None:
                    return Action(target.position, False, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT)
            else:
                shade_tag = self.cd_manager.adept_to_shade.get(unit.tag, None)
                if shade_tag is not None:
                    shade = self.cache.by_tag(shade_tag)
                    if self.knowledge.enemy_units_manager.danger_value(
                            unit, unit.position
                    ) < self.knowledge.enemy_units_manager.danger_value(unit, shade.position):
                        # It's safer to not phase shift
                        return Action(unit.position, False, AbilityId.CANCEL_ADEPTPHASESHIFT)

                enemy_workers = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 6).of_type(
                    [UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE]
                )
                enemy_ground_force_light = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 8) \
                    .filter(lambda u: u.is_light and not u.is_flying)
                if enemy_workers.exists and self.ready_to_shoot(unit):
                    return Action(enemy_workers.closest_to(unit), True)
                elif enemy_ground_force_light.exists and self.ready_to_shoot(unit):
                    return Action(enemy_ground_force_light.closest_to(unit), True)

        return super().unit_solve_combat(unit, current_command)

    def get_target(self, nearby: Units, target: Optional[Unit], unit: Unit, shuffler: float) -> Optional[Unit]:
        best_score = 0

        for enemy in nearby:
            d = enemy.distance_to(unit)
            if d < 12 and not enemy.is_flying:
                score = d * 0.2 - self.unit_values.power(enemy)
                if enemy.is_structure:
                    score -= 15
                if enemy.is_light:
                    score += 5
                if enemy.type_id == UnitTypeId.SCV or enemy.type_id == UnitTypeId.PROBE or \
                        enemy.type_id == UnitTypeId.DRONE or enemy.type_id == UnitTypeId.MULE:
                    score += 4
                    if enemy.shield_health_percentage <= 0.5:
                        score += 4

                score += 0.1 * (enemy.tag % (shuffler + 2))

                if score > best_score:
                    target = enemy
                    best_score = score
        return target

    # TODO: Adepts shade on top of marines
    # TODO: Adepts put out a escape shade
    # TODO: Adepts shade to kill workers?
