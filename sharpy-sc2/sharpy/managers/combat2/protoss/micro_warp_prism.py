from typing import Dict

from sc2.ids.buff_id import BuffId
from sharpy.managers.combat2 import Action, MicroStep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.managers import *
from sharpy.general.extended_power import ExtendedPower
from sc2 import AbilityId, UnitTypeId
from sc2.unit import Unit
from sc2.units import Units


class MicroWarpPrism(MicroStep):
    def __init__(self):
        self.release_tags: Dict[int, float] = dict()
        self.tag_unloading: Dict[int, float] = dict()
        super().__init__()

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        prism = unit
        warpgates: Units = self.knowledge.unit_cache.own(UnitTypeId.WARPGATE)

        count = len(warpgates)
        ready = 0

        for gate in warpgates:  # type: Unit
            if gate.is_transforming or self.cd_manager.is_ready(gate.tag, AbilityId.WARPGATETRAIN_ZEALOT):
                ready += 1

        if (
                ready >= 2
                and ready >= count
                and unit.type_id == UnitTypeId.WARPPRISM
                and self.ai.supply_left > 3
                and self.cd_manager.is_ready(prism.tag, AbilityId.MORPH_WARPPRISMTRANSPORTMODE, 6)
        ):
            # TODO: Is it safe to warp in?
            self.cd_manager.used_ability(prism.tag, AbilityId.MORPH_WARPPRISMPHASINGMODE)
            return Action(None, False, AbilityId.MORPH_WARPPRISMPHASINGMODE)

        elif unit.type_id == UnitTypeId.WARPPRISMPHASING:
            not_ready = self.knowledge.unit_cache.own(self.unit_values.gate_types).not_ready

            if self.cd_manager.is_ready(prism.tag, AbilityId.MORPH_WARPPRISMPHASINGMODE, 2.5) and (
                    len(not_ready) < 1 or not_ready.closest_distance_to(prism) > 4
            ):
                self.cd_manager.used_ability(prism.tag, AbilityId.MORPH_WARPPRISMTRANSPORTMODE)
                return Action(None, False, AbilityId.MORPH_WARPPRISMTRANSPORTMODE)

        if prism.cargo_used:
            for passenger in prism.passengers:  # type: Unit
                if self.release_tags.get(passenger.tag, 0) < self.ai.time:
                    if not self.ai.in_pathing_grid(prism):
                        break

                    stop_drop = False

                    for enemy in self.knowledge.unit_cache.enemy_in_range(prism.position, 4):  # type: Unit
                        if enemy.radius + 1 > prism.distance_to(enemy):
                            stop_drop = True
                            break

                    if stop_drop:
                        break

                    # return CombatAction(prism, passenger, False, AbilityId.UNLOADALLAT_WARPPRISM)
                    return Action(prism, False, AbilityId.UNLOADALLAT_WARPPRISM)

        power = ExtendedPower(self.unit_values)
        power.add_units(self.knowledge.unit_cache.enemy_in_range(prism.position, 12))

        if prism.cargo_left and prism.shield > 0 and prism.shield + prism.health > 50:
            best_score = 0
            best_unit = None
            for own_unit in self.knowledge.unit_cache.own_in_range(prism.position, 14):  # type: Unit
                if own_unit.has_buff(BuffId.LOCKON):
                    return Action(own_unit, False, AbilityId.SMART)

                if own_unit.cargo_size > prism.cargo_left:
                    continue
                if own_unit.shield:
                    continue
                if own_unit.weapon_cooldown < 2:
                    continue
                if own_unit.distance_to(prism) > 12:
                    continue

                score = (
                        self.unit_values.ground_range(own_unit)
                        * (1.1 - own_unit.health_percentage)
                        * self.unit_values.power(own_unit)
                        - 1
                )

                if score > best_score:
                    best_score = score
                    best_unit = own_unit

            if best_unit is not None:
                self.release_tags[best_unit.tag] = self.ai.time + best_unit.weapon_cooldown / 22.4
                return Action(best_unit, False, AbilityId.SMART)

        return self.find_safe_position(current_command, unit)

    def find_safe_position(self, current_command: Action, unit: Unit):
        priority_units: Units = self.knowledge.unit_cache.own(
            [UnitTypeId.COLOSSUS, UnitTypeId.IMMORTAL, UnitTypeId.ARCHON, UnitTypeId.HIGHTEMPLAR]
        ).filter(lambda u: u.distance_to(unit) <= 10)
        # Let's find the safest position that's closest to enemies
        if priority_units:
            focus = priority_units.center
        else:
            # No other friendly units to use as anchor point
            focus = current_command.target.position
        return self.prism_evasive_move_to(unit, focus)

    def prism_evasive_move_to(self, harass_prism, position_to):
        position = harass_prism.position3d

        enemy_anti_air_structure = self.knowledge.unit_cache.enemy_in_range(harass_prism.position3d, 13) \
            .of_type(UnitTypeId.BUNKER)
        enemy_anti_air_units = self.knowledge.unit_cache.enemy_in_range(harass_prism.position3d, 13) \
            .filter(lambda unit: unit.can_attack_air)

        if harass_prism.has_buff(BuffId.LOCKON):
            cyclones = self.knowledge.unit_cache.enemy_in_range(harass_prism.position3d, 20).of_type(
                UnitTypeId.CYCLONE)
            if cyclones:
                closest_cyclone = cyclones.closest_to(harass_prism)
                position = position.towards(closest_cyclone, - 18)

        if enemy_anti_air_units.exists or enemy_anti_air_structure.exists:
            for aa in enemy_anti_air_units:
                distance = harass_prism.distance_to(aa.position3d)
                amount_of_evade = 15 - distance
                position = position.towards(aa, - amount_of_evade)
            for aa in enemy_anti_air_structure:
                distance = harass_prism.distance_to(aa.position3d)
                amount_of_evade = 15 - distance
                position = position.towards(aa, - amount_of_evade)
            # after the for loop, position is the best vector away from enemy
            distance_to_best_evade_point = 3
            should_go = position.towards(position_to, distance_to_best_evade_point)
            return Action(should_go, False)
        else:
            return Action(position_to, False)
