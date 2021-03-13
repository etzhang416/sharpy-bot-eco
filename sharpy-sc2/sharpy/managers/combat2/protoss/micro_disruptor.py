from typing import List

from sc2 import AbilityId, Dict
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.combat2 import Action, MicroStep, MoveType

INTERVAL = 2.2
NOVA_DURATION = 2.1


class MicroDisruptor(MicroStep):
    def __init__(self):
        super().__init__()
        self.last_used_any = 0
        self.tags_ready: List[int] = []

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.move_type == MoveType.DefensiveRetreat:
            return current_command

        closest = self.closest_units.get(unit.tag)
        if not closest or closest.distance_to(unit) > 14:
            # not in combat, follow the army
            return current_command

        time = self.knowledge.ai.time
        relevant_enemies = self.cache.enemy_in_range(unit.position, 14).not_structure.not_flying

        if time < self.last_used_any + INTERVAL or len(relevant_enemies) < 4:
            return self.stay_safe()

        center = relevant_enemies.center

        if self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_PURIFICATIONNOVA):
            distance = self.pather.walk_distance(unit.position, center)
            if distance <= 12:
                self.last_used_any = time
                return Action(center, False, AbilityId.EFFECT_PURIFICATIONNOVA)
            else:
                return Action(center, False)

        return self.stay_safe()

    def stay_safe(self):
        # TODO: Backstep
        pos = self.pather.find_weak_influence_ground(self.group.center.position, 3)
        return Action(pos, False)


class MicroPurificationNova(MicroStep):
    def __init__(self):
        super().__init__()
        self.spawned: Dict[int, float] = dict()

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if unit.tag not in self.spawned:
            self.spawned[unit.tag] = self.ai.time

        time_percentage = 1 - (self.ai.time - self.spawned.get(unit.tag, self.ai.time)) / NOVA_DURATION

        relevant_enemies = self.cache.enemy_in_range(unit.position, 10 * time_percentage).not_structure.not_flying

        if relevant_enemies.exists:
            if time_percentage >= 0.4:
                target = relevant_enemies.center
            else:
                target = relevant_enemies.closest_to(unit)
            return Action(target, False)
        else:
            own_relevant = self.cache.own_in_range(unit.position, 4).not_structure.not_flying
            if own_relevant:
                pos = unit.position.towards(own_relevant.center.position, -10)
                return Action(pos, False)

        return current_command
