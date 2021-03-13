from sc2.ids.buff_id import BuffId
from sharpy.managers.combat2 import GenericMicro, Action
from sc2 import AbilityId
from sc2.unit import Unit


class MicroHighTemplars(GenericMicro):
    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        # before death
        if unit.shield_health_percentage <= 0.3:
            if self.cd_manager.is_ready(unit.tag, AbilityId.FEEDBACK_FEEDBACK):
                feedback_enemies = self.cache.enemy_in_range(unit.position, 10).filter(
                    lambda u: u.energy_percentage > 0.5 and not u.is_structure
                )
                if feedback_enemies:
                    closest = feedback_enemies.closest_to(unit)
                    return Action(closest, False, AbilityId.FEEDBACK_FEEDBACK)

        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        # center range = 9 and radius ~= 2
        if self.cd_manager.is_ready(unit.tag, AbilityId.PSISTORM_PSISTORM):
            enemies = self.cache.enemy_in_range(unit.position, 12).not_structure
            target = enemies.filter(lambda u: not u.has_buff(BuffId.PSISTORM))
            if len(target) >= 5:
                center = target.center
                return Action(center, False, AbilityId.PSISTORM_PSISTORM)

        if self.cd_manager.is_ready(unit.tag, AbilityId.FEEDBACK_FEEDBACK):
            feedback_enemies = self.cache.enemy_in_range(unit.position, 11).filter(
                lambda u: u.energy_percentage > 0.5 and not u.is_structure
            )
            if feedback_enemies:
                closest = feedback_enemies.closest_to(unit)
                return Action(closest, False, AbilityId.FEEDBACK_FEEDBACK)

        return super().unit_solve_combat(unit, current_command)
