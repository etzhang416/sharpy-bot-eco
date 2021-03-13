from sc2 import UnitTypeId, Race
from sc2.position import Point2
from sharpy.managers.combat2 import Action, MicroStep
from sc2.unit import Unit
from sc2.units import Units


class MicroObservers(MicroStep):

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if isinstance(current_command.target, Unit):
            target_pos = current_command.target.position
        else:
            target_pos = current_command.target

        target_return = self.pather.find_path(self.group.center, self.group.center.towards(target_pos, 3), 3)  # move ahead of group

        enemies = self.cache.enemy_in_range(unit.position, 12, False)
        other_observers = self.cache.own(UnitTypeId.OBSERVER).tags_not_in([unit.tag])
        if other_observers.exists:
            # Try to keep observers separated from each other
            closest = other_observers.closest_to(unit)
            if closest.distance_to(unit) < 10:
                pos: Point2 = closest.position
                target = unit.position.towards(pos, -6)
                return Action(target, False)

        ACs = enemies.filter(lambda u: u.is_detector)
        if ACs.exists:
            nearest_AC = ACs.closest_to(unit)
            enemy_AA = self.cache.enemy_in_range(unit.position, 12, False).filter(lambda u: u.can_attack_air)
            if enemy_AA.exists:
                target = unit.position.towards(nearest_AC, -4)
                return Action(target, False)

        cloaked_enemy = self.cache.enemy_in_range(unit.position, 300, only_targetable=False). \
            filter(lambda u: u.is_cloaked)
        if cloaked_enemy.amount > 0 and self.knowledge.enemy_race == Race.Terran:
            if ACs is not None:
                target = self.pather.find_weak_influence_air(cloaked_enemy.closest_to(unit).position, 10).position
            else:
                target = cloaked_enemy.closest_to(unit).position
            return Action(target, False)

        return Action(target_return, False)
