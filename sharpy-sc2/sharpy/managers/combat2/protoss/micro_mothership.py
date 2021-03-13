from sharpy.managers.combat2 import GenericMicro, Action
from sc2 import AbilityId
from sc2.unit import Unit


class MicroMotherShip(GenericMicro):
    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        enemy = self.knowledge.unit_cache.enemy_in_range(unit.position3d, 12)
        if unit.shield_health_percentage <= 0.3 and enemy:
            enemy_closest = enemy.closest_to(unit.position3d)
            return Action(enemy_closest.position.towards(unit.position, 5), False)

        if self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_TIMEWARP):
            stormable_enemies = self.cache.enemy_in_range(unit.position, 13).not_structure
            if len(stormable_enemies) >= 7:
                center = stormable_enemies.center
                target = stormable_enemies.closest_to(center)
                return Action(target.position, False, AbilityId.EFFECT_TIMEWARP)

        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            if self.group.units.amount >= 10:
                # Regroup with the army
                return Action(self.group.center, True)

        return super().unit_solve_combat(unit, current_command)
