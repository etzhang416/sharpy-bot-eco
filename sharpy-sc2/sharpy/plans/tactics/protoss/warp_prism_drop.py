from sc2.ids.buff_id import BuffId
from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sharpy.knowledges import Knowledge
from sc2 import UnitTypeId, AbilityId


# for PVT
class WarpPrismHarass(ActBase):
    def __init__(self):
        super().__init__()
        self.prism_tag = None
        self.attack_dt_tag = None
        self.ninja_dt_1_tag = None
        self.ninja_dt_2_tag = None
        # before attack
        self.dark_shrine_ready = False
        self.money_reserved = False
        self.already_phased = False
        self.already_warped_dt = False
        self.already_loaded_dt = False

        self.enemy_air_detector = False
        self.no_more_harass = False

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)

    async def execute(self) -> bool:
        if self.no_more_harass:
            return True

        if self.knowledge.unit_cache.own(UnitTypeId.DARKSHRINE).ready.amount + \
                self.knowledge.unit_cache.own(UnitTypeId.DARKSHRINE).not_ready.amount == 0:
            return True

        dark_shrine_num = self.knowledge.unit_cache.own(UnitTypeId.DARKSHRINE).ready.amount
        if (dark_shrine_num >= 1) and not self.dark_shrine_ready:
            self.dark_shrine_ready = True
            return True

        prism = self.knowledge.unit_cache.own(UnitTypeId.WARPPRISM).ready
        if (self.prism_tag is None) and (prism.amount >= 1):
            self.prism_tag = prism.first.tag
            return True

        if self.prism_tag is not None:
            harass_prism: Unit = self.knowledge.unit_cache.by_tag(self.prism_tag)

            if harass_prism is None:
                self.no_more_harass = True
                return True

            if self.already_loaded_dt:
                if not self.enemy_air_detector:
                    await self.harass_with_dt_prism()
                else:
                    self.knowledge.roles.clear_task(harass_prism)
                    self.no_more_harass = True
                return True
            else:
                self.knowledge.roles.set_task(UnitTask.Reserved, harass_prism)
                if (not self.dark_shrine_ready) or (harass_prism.distance_to(self.get_warp_position()) >= 4):
                    self.do(harass_prism.move(self.get_warp_position()))
                    if not self.money_reserved:
                        self.money_reserved = True
                        self.knowledge.reserve(125 * 3, 125 * 3)
                    return True
                else:
                    if not self.already_phased:
                        self.do(harass_prism(AbilityId.MORPH_WARPPRISMPHASINGMODE))
                        if self.cd_manager.is_ready(harass_prism.tag, AbilityId.MORPH_WARPPRISMPHASINGMODE, 3.5):
                            self.already_phased = True
                        return True
                    else:
                        warp_gates = self.knowledge.unit_cache.own(UnitTypeId.WARPGATE).ready
                        if not self.already_warped_dt:
                            for warp_gate in warp_gates:
                                if self.cd_manager.is_ready(warp_gate.tag, AbilityId.WARPGATETRAIN_DARKTEMPLAR):
                                    pos = harass_prism.position.to2.random_on_distance(4)
                                    placement = await self.ai.find_placement(AbilityId.WARPGATETRAIN_DARKTEMPLAR, pos,
                                                                             placement_step=2)
                                    if placement is None:
                                        self.knowledge.print("can't find place to warp in")
                                        self.already_phased = False
                                        return True
                                    self.do(warp_gate.warp_in(UnitTypeId.DARKTEMPLAR, placement))

                            dts = self.knowledge.unit_cache.own(UnitTypeId.DARKTEMPLAR).ready
                            if dts.amount >= 3:
                                self.already_warped_dt = True
                                attack_dt = dts[0]
                                harass_dt_1 = dts[1]
                                harass_dt_2 = dts[2]
                                self.attack_dt_tag = attack_dt.tag
                                self.ninja_dt_1_tag = harass_dt_1.tag
                                self.ninja_dt_2_tag = harass_dt_2.tag
                            return True
                        else:
                            if not self.already_loaded_dt:
                                if self.cd_manager.is_ready(
                                        harass_prism.tag, AbilityId.MORPH_WARPPRISMTRANSPORTMODE, 6):
                                    self.do(harass_prism(AbilityId.MORPH_WARPPRISMTRANSPORTMODE))

                                attack_dt: Unit = self.knowledge.unit_cache.by_tag(self.attack_dt_tag)
                                harass_dt_1: Unit = self.knowledge.unit_cache.by_tag(self.ninja_dt_1_tag)
                                harass_dt_2: Unit = self.knowledge.unit_cache.by_tag(self.ninja_dt_2_tag)
                                if harass_dt_1 is not None:
                                    self.do(harass_prism.smart(harass_dt_1))
                                if harass_dt_2 is not None:
                                    self.do(harass_prism.smart(harass_dt_2))
                                if harass_prism.cargo_used >= 4 and self.cd_manager.is_ready(
                                        harass_prism.tag, AbilityId.MORPH_WARPPRISMPHASINGMODE, 6):
                                    self.already_loaded_dt = True
                                return True
                        return True
        return True

    def get_warp_position(self):
        return self.knowledge.enemy_expansion_zones[3].center_location. \
            towards(self.knowledge.own_main_zone.center_location, 7)

    def get_first_flank_position(self):
        return self.knowledge.enemy_expansion_zones[0].center_location. \
            towards(self.get_warp_position(), 12)

    def get_enemy_main_platform(self):
        return self.knowledge.enemy_expansion_zones[0].center_location. \
            towards(self.get_warp_position(), 6)

    async def harass_with_dt_prism(self):
        if self.prism_tag is not None:
            harass_prism = self.knowledge.unit_cache.by_tag(self.prism_tag)
            self.knowledge.roles.set_task(UnitTask.Reserved, harass_prism)
            if harass_prism is not None:
                # still have prism
                await self.up_and_down(harass_prism)

                if self.ninja_dt_1_tag is not None:
                    harass_dt_1 = self.knowledge.unit_cache.by_tag(self.ninja_dt_1_tag)
                    if harass_dt_1 is not None:
                        self.knowledge.roles.set_task(UnitTask.Reserved, harass_dt_1)
                        await self.harass_command(harass_dt_1, harass_prism)
                if self.ninja_dt_2_tag is not None:
                    harass_dt_2: Unit = self.knowledge.unit_cache.by_tag(self.ninja_dt_2_tag)
                    if harass_dt_2 is not None:
                        self.knowledge.roles.set_task(UnitTask.Reserved, harass_dt_2)
                        await self.harass_command(harass_dt_2, harass_prism)

                if self.attack_dt_tag is not None:
                    attack_dt = self.knowledge.unit_cache.by_tag(self.attack_dt_tag)
                    if attack_dt is not None:
                        await self.attack_command(attack_dt, harass_prism)
                return True
            return True
        return True

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
                amount_of_evade = 13 - distance
                position = position.towards(aa, - amount_of_evade)
            for aa in enemy_anti_air_structure:
                distance = harass_prism.distance_to(aa.position3d)
                amount_of_evade = 13 - distance
                position = position.towards(aa, - amount_of_evade)
            # after the for loop, position is the best vector away from enemy
            distance_to_best_evade_point = 5
            should_go = position.towards(position_to, distance_to_best_evade_point)
            self.do(harass_prism.move(should_go))
        else:
            self.do(harass_prism.move(position_to))

        return True

    async def up_and_down(self, harass_prism: Unit):
        self.knowledge.roles.set_task(UnitTask.Reserved, harass_prism)

        if harass_prism.has_buff(BuffId.LOCKON):
            cyclones = self.knowledge.unit_cache.enemy_in_range(harass_prism.position3d, 20).of_type(
                UnitTypeId.CYCLONE)
            if cyclones:
                closest_cyclone = cyclones.closest_to(harass_prism)
                position = harass_prism.position.towards(closest_cyclone, - 18)
                self.do(harass_prism.move(position))
                return True

        if harass_prism.health_percentage <= 0.2:
            self.do(harass_prism(AbilityId.UNLOADALLAT_WARPPRISM, harass_prism.position))
            return True

        if harass_prism.distance_to(self.get_enemy_main_platform()) <= 12 and \
                (not self.is_revealed_by_enemy(harass_prism)) and \
                harass_prism.cargo_used > 0:
            self.do(harass_prism(AbilityId.UNLOADALLAT_WARPPRISM, harass_prism.position))
            return True
        target = self.get_enemy_main_platform()

        dts = self.knowledge.unit_cache.by_tags([self.ninja_dt_1_tag, self.ninja_dt_2_tag])
        if dts.exists and harass_prism.cargo_used < 4:
            target = dts.center
            for dt in dts:
                if self.is_revealed_by_enemy(dt):
                    self.do(harass_prism.move(dt.position))
                    return True
        self.prism_evasive_move_to(harass_prism, target)
        return True

    async def attack_command(self, unit: Unit, prism: Unit):
        self.knowledge.roles.set_task(UnitTask.Reserved, unit)
        if self.is_revealed_by_enemy(unit):
            if unit.distance_to(prism) <= 8 and prism.shield_health_percentage >= 0.4:
                self.do(unit.smart(prism))
                return True

            else:
                base = self.knowledge.own_main_zone.center_location
                self.do(unit.move(base))
                return True

        else:
            await self.attack_priority_targets(unit, prism)
        return True

    async def harass_command(self, dt: Unit, prism: Unit):
        self.knowledge.roles.set_task(UnitTask.Reserved, dt)
        if self.is_revealed_by_enemy(dt):
            if dt.distance_to(prism) <= 5 and prism.shield_health_percentage >= 0.4:
                self.do(dt.smart(prism))
                return True
            else:
                self.do(dt.move(prism))
                return True
        else:
            await self.attack_priority_targets(dt, prism)
        return True

    def is_revealed_by_enemy(self, dt: Unit) -> bool:
        detectors = self.knowledge.unit_cache.enemy_in_range(dt.position, 20) \
            .filter(lambda x: (x.detect_range - 1) > dt.distance_to(x.position))
        if detectors.exists:
            if detectors.filter(lambda x: x.is_flying).exists:
                self.enemy_air_detector = True
            return True
        for effect in self.ai.state.effects:
            if effect.id == EffectId.SCANNERSWEEP:
                if Point2.center(effect.positions).distance_to(dt.position) < 15:
                    return True
        return False

    async def attack_priority_targets(self, dt: Unit, prism: Unit):
        self.knowledge.roles.set_task(UnitTask.Reserved, dt)

        enemy_ground_ACs = self.knowledge.unit_cache.enemy_in_range(dt.position, 15).of_type(
            [UnitTypeId.SPORECRAWLER, UnitTypeId.MISSILETURRET]
        )
        if enemy_ground_ACs:
            target = enemy_ground_ACs.closest_to(dt)
            self.do(dt.attack(target))
            return True

        enemy_bad_AAs = self.knowledge.unit_cache.enemy_in_range(prism.position, 15) \
            .filter(lambda u: u.can_attack_air and not u.is_flying
                              and u.distance_to(prism) <= 10)

        if enemy_bad_AAs:
            target = enemy_bad_AAs.closest_to(dt)
            self.do(dt.attack(target))
            return True

        enemy_workers = self.knowledge.unit_cache.enemy_in_range(dt.position, 13).of_type(
            [UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE]
        )
        if enemy_workers:
            target = enemy_workers.closest_to(dt)
            self.do(dt.attack(target))
            return True

        enemy_add_ons = self.knowledge.unit_cache.enemy_in_range(dt.position, 7).of_type(
            [UnitTypeId.STARPORTTECHLAB]
        )
        if enemy_add_ons:
            target = enemy_add_ons.closest_to(dt)
            self.do(dt.attack(target))
            return True

        enemy_add_ons = self.knowledge.unit_cache.enemy_in_range(dt.position, 7).of_type(
            [UnitTypeId.FACTORYTECHLAB, UnitTypeId.BARRACKSTECHLAB, UnitTypeId.STARPORTREACTOR]
        )
        if enemy_add_ons:
            target = enemy_add_ons.closest_to(dt)
            self.do(dt.attack(target))
            return True

        enemy_ground_AAs = self.knowledge.unit_cache.enemy_in_range(dt.position, 7) \
            .filter(lambda u: u.can_attack_air and not u.is_flying)

        if enemy_ground_AAs:
            target = enemy_ground_AAs.closest_to(dt)
            self.do(dt.attack(target))
            return True

        self.do(dt.attack(self.knowledge.enemy_start_location))
        return True
