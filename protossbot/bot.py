import random
from typing import Callable, List, Dict, Optional
from sc2 import UnitTypeId
from sc2 import Race
from sc2.ids.upgrade_id import UpgradeId
from sharpy.knowledges import KnowledgeBot
from sharpy.managers import ManagerBase, DataManager
from sharpy.plans.protoss import *
from sharpy.managers.build_detector import EnemyRushBuild


# python run_custom.py -m OdysseyLE -p1 protossbot -p2 banshee

class ProtossBot(KnowledgeBot):
    data_manager: DataManager

    def __init__(self, build_name: str = "default"):
        super().__init__("EZ bot PVP")
        self.conceded = False
        self.builds: Dict[str, Callable[[], BuildOrder]] = {
            "pvp": lambda: self.pvp_build(),
            "pvz": lambda: self.pvz_build(),
            "pvt": lambda: self.pvt_build(),
            "pvr": lambda: self.pvr_build(),
        }
        self.build_name = build_name
        self.enemy_last_intel = None
        self.enemy_intel = None

    def configure_managers(self) -> Optional[List[ManagerBase]]:
        self.knowledge.roles.set_tag_each_iteration = True
        return None

    async def on_step(self, iteration):
        self.enemy_intel = self.knowledge.build_detector.rush_build

        if self.enemy_last_intel is None:
            self.enemy_last_intel = self.enemy_intel

        if self.enemy_last_intel != self.enemy_intel:
            shit_talk = "Looks like you wanna "
            shit_talk += self.enemy_intel.name
            self.enemy_last_intel = self.enemy_intel
            await self.chat_send(shit_talk)
        return await super().on_step(iteration)

    async def create_plan(self) -> BuildOrder:
        if self.build_name == "default":
            if self.knowledge.enemy_race == Race.Protoss:
                self.build_name = "pvp"
            elif self.knowledge.enemy_race == Race.Zerg:
                self.build_name = "pvz"
            elif self.knowledge.enemy_race == Race.Terran:
                self.build_name = "pvt"
            else:
                self.build_name = self.build_name = "pvr"
        self.knowledge.data_manager.set_build(self.build_name)
        return self.builds[self.build_name]()

    def pvz_build(self) -> BuildOrder:
        return BuildOrder(
            self.pvz_main_force(),
            self.pvz_create_common_strategy()
        )

    def pvt_build(self) -> BuildOrder:
        return BuildOrder(
            self.pvt_main_force(),
            self.pvt_create_common_strategy()
        )

    def pvp_build(self) -> BuildOrder:
        return BuildOrder(
            self.pvp_main_force(),
            self.pvp_create_common_strategy()
        )

    def pvr_build(self) -> BuildOrder:
        return BuildOrder(
            self.pvr_main_force(),
            self.pvz_create_common_strategy()
        )

    def pvp_create_common_strategy(self) -> SequentialList:

        return SequentialList(
            ShieldOvercharge(),
            DistributeWorkers(),
            PlanHallucination(),
            HallucinatedPhoenixScout(),
            PlanCancelBuilding(),
            WorkerRallyPoint(),
            PlanZoneGather(),
            OracleHarass(),
            PlanZoneDefense(),
            PlanZoneAttack(),
            PlanFinishEnemy()
        )

    def pvz_create_common_strategy(self) -> SequentialList:

        return SequentialList(
            ShieldOvercharge(),
            DistributeWorkers(),
            PlanHallucination(),
            HallucinatedPhoenixScout(),
            PlanCancelBuilding(),
            WorkerRallyPoint(),
            PlanZoneGather(),
            OracleHarass(),
            PlanZoneDefense(),
            PlanZoneAttack(),
            PlanFinishEnemy()
        )

    def pvt_create_common_strategy(self) -> SequentialList:
        return SequentialList(
            ShieldOvercharge(),
            DistributeWorkers(),
            PlanHallucination(),
            HallucinatedPhoenixScout(),
            PlanCancelBuilding(),
            WorkerRallyPoint(),
            PlanZoneGather(),
            OracleHarass(),
            PlanZoneDefense(),
            PlanZoneAttack(),
            PlanFinishEnemy()
        )

    # TODO: these are pvp related functions
    def pvp_main_force(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.Macro, self.pvp_micro()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.SafeExpand, self.pvp_micro()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.WorkerRush, self.counter_ProxyZealots()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.ProxyZealots, self.counter_ProxyZealots()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.CannonRush, self.counter_CannonRush()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.ProxyBase, self.counter_4BG()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.Zealots, self.counter_4BG()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.AdeptRush, self.counter_4BG()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.AirOneBase, self.counter_air()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.ProxyRobo, self.counter_Robo()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.RoboRush, self.counter_Robo()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.EarlyExpand, self.pvp_punish_early_expand()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.FastDT, self.counter_FastDT()),
        )

    def pvp_micro(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            ChronoAnyTech(50),

            SequentialList(
                self.pvp_eco_start_up(),
                self.pvp_micro_build()
            )
        )

    def pvp_punish_early_expand(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            DoubleAdeptScout(2),
            ChronoAnyTech(0),
            ChronoUnit(UnitTypeId.ADEPT, UnitTypeId.GATEWAY, count=2),

            SequentialList(
                GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
                Workers(22),
                GridBuilding(unit_type=UnitTypeId.PYLON, to_count=2, priority=True),
                Workers(23),
                Tech(UpgradeId.WARPGATERESEARCH),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=2),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=4),
                ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=6),
                BuildOrder(
                    Step(Gas(400), ProtossUnit(UnitTypeId.SENTRY, priority=True)),
                    ProtossUnit(UnitTypeId.STALKER, priority=True),
                ),
            )
        )

    def pvp_eco_start_up(self) -> SequentialList:
        return SequentialList(
            Workers(13),
            GridBuilding(unit_type=UnitTypeId.PYLON, to_count=1, priority=True),
            Workers(14),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=1, priority=True),
            # 0:40 enemy open worker rush build
            Step(UnitExists(UnitTypeId.NEXUS), action=ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 1)),
            Workers(16),
            BuildGas(1),
            Workers(17),
            BuildGas(2),
            # 1:05 perfect time for detect enemy cannon rush at 2 nd base location
            Scout(UnitTypeId.PROBE, 1, ScoutLocation.scout_own2_behind()),
            Workers(18),
            Workers(19),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
            # probe scout after 2BG
            # reach enemy base ramp at ~ 1:55
            # scout_main_2 is move around

            WorkerScout(),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            Workers(22),
            GridBuilding(unit_type=UnitTypeId.PYLON, to_count=2, priority=True),

            Workers(23),
            Tech(UpgradeId.WARPGATERESEARCH),
            ProtossUnit(UnitTypeId.STALKER, 1, only_once=True, priority=True),
            ProtossUnit(UnitTypeId.SENTRY, 1, only_once=True, priority=True),
            ProtossUnit(UnitTypeId.STALKER, 3, only_once=True, priority=True),
            # my 2nd base ~ 2:45
            Expand(2),
            # 3 stalker+1sentry at ~ 3:20 for early adept
            # ~ 3:30 HallucinatedPhoenixScout reach enemy base
            # the HallucinatedPhoenixScout() is modified to scout more enemy tech line
            DefensivePylons(to_base_index=1),
            GridBuilding(unit_type=UnitTypeId.TWILIGHTCOUNCIL, to_count=1, priority=True),
            ProtossUnit(UnitTypeId.STALKER, 5, only_once=True, priority=True),
            DefensiveCannons(0, 1, 1),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True),
            Tech(UpgradeId.BLINKTECH),
            GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
            ProtossUnit(UnitTypeId.STALKER, 8, only_once=True, priority=True),
            ProtossUnit(UnitTypeId.SENTRY, 2, only_once=True, priority=True),
            ProtossUnit(UnitTypeId.OBSERVER, 1, only_once=True, priority=True),
            BuildGas(4),
            GridBuilding(unit_type=UnitTypeId.ROBOTICSBAY, to_count=1, priority=True),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=6, priority=True),
            ProtossUnit(UnitTypeId.STALKER, 11, only_once=True, priority=True),
            ProtossUnit(UnitTypeId.DISRUPTOR, 1, only_once=True, priority=True),
        )

    def pvp_micro_build(self) -> BuildOrder:
        return BuildOrder(
            # TODO
            # keep optimize
            AutoWorker(),
            AutoPylon(),


            Step(EnemyUnitExists(UnitTypeId.DARKTEMPLAR),
                 ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1)),

            ChronoAnyTech(save_to_energy=50),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 5),
            ChronoUnit(UnitTypeId.CARRIER, UnitTypeId.STARGATE, 5),
            ChronoUnit(UnitTypeId.MOTHERSHIP, UnitTypeId.NEXUS, 2),

            ProtossUnit(UnitTypeId.ADEPT, 4, only_once=True, priority=True),

            Step(Supply(90),
                 Expand(3, priority=True)),
            Step(EnemyUnitExists(UnitTypeId.NEXUS, 3), Expand(3, priority=True)),
            Step(EnemyUnitExists(UnitTypeId.PHOTONCANNON, 2), Expand(3, priority=True)),

            ProtossUnit(UnitTypeId.DISRUPTOR, 3, priority=True),

            Step(Time(time_in_seconds=4 * 60),
                 Scout(UnitTypeId.PROBE, 1,
                       ScoutLocation.scout_enemy3(),
                       ScoutLocation.scout_enemy4(),
                       ScoutLocation.scout_enemy5(),
                       )
                 ),

            Step(EnemyUnitExists(UnitTypeId.ZEALOT),
                 ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=4)),
            Step(EnemyUnitExists(UnitTypeId.VOIDRAY),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=12)),
            Step(EnemyUnitExists(UnitTypeId.STALKER, 8),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=4)),

            DefensiveCannons(0, 1, 2),
            DefensiveCannons(0, 1, 3),

            SequentialList(
                Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1),
                Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1),
                Tech(UpgradeId.PROTOSSSHIELDSLEVEL1),
                Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
            ),

            # eco plan
            StepBuildGas(to_count=6, requirement=UnitExists(UnitTypeId.NEXUS, 3)),

            Step(Supply(80), GridBuilding(unit_type=UnitTypeId.STARGATE, to_count=1)),

            # this is the final golden armada
            Step(Supply(120), self.pvt_macro_build()),

            # units

            ProtossUnit(UnitTypeId.OBSERVER, to_count=1, priority=True),
            Step(UnitExists(UnitTypeId.IMMORTAL, 2), ProtossUnit(UnitTypeId.WARPPRISM, to_count=1, priority=True)),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=4),
            ProtossUnit(UnitTypeId.VOIDRAY, priority=True, to_count=4),
            ProtossUnit(UnitTypeId.STALKER, priority=True),

        )

    def counter_CannonRush(self) -> BuildOrder:
        # as long as I detected the cannon rush,
        # bot will go 4bg stalker pressure
        # this is tested 2020-08-06 with 100% clear advantage wins
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            Cancel2ndBase(),

            ChronoUnit(UnitTypeId.STALKER, UnitTypeId.GATEWAY, 10),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 10),
            ProtossUnit(UnitTypeId.SENTRY, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True),
            ProtossUnit(UnitTypeId.STALKER, priority=True),
            Tech(UpgradeId.WARPGATERESEARCH),

            Step(UnitExists(UnitTypeId.CYBERNETICSCORE),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True)),
            Step(UnitExists(UnitTypeId.CYBERNETICSCORE),
                 GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True)),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
        )

    def counter_ProxyZealots(self) -> BuildOrder:
        # as long as I detected the proxy zealot by getting no gas in enemy base,
        # bot will go 4bg stalker pressure
        # this is tested 2020-08-06 with 100% clear advantage wins
        # gotta say stalker micro is too OP!
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            Cancel2ndBase(),

            ChronoUnit(UnitTypeId.STALKER, UnitTypeId.GATEWAY, 10),

            Tech(UpgradeId.WARPGATERESEARCH),
            Step(UnitExists(UnitTypeId.STALKER, 5),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True)),
            Step(UnitExists(UnitTypeId.CYBERNETICSCORE),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True)),

            ProtossUnit(UnitTypeId.STALKER, to_count=3, priority=True),
            ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=6),
            DoubleAdeptScout(6),

            ProtossUnit(UnitTypeId.STALKER, priority=True),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=1, priority=True),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            BuildGas(2),
        )

    def counter_4BG(self) -> BuildOrder:
        # 4BG = adept rush/stalker rush/ zealot rush
        # general eco strategy to counter 4 BG rush
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),

            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 10),

            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            BuildGas(2),
            ProtossUnit(UnitTypeId.STALKER, to_count=2, priority=True, only_once=True),

            Tech(UpgradeId.WARPGATERESEARCH),
            Expand(2, priority=True),
            DefensiveCannons(0, 1, 1),

            Step(EnemyUnitExists(UnitTypeId.STALKER, 6),
                 ProtossUnit(UnitTypeId.SENTRY, priority=True, to_count=1)),

            Step(EnemyUnitExists(UnitTypeId.VOIDRAY),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8)),
            Step(EnemyUnitExists(UnitTypeId.ADEPT, 4),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=6)),
            Step(EnemyUnitExists(UnitTypeId.STALKER, 4),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=4)),
            Step(EnemyUnitExists(UnitTypeId.STALKER, 8),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=8)),

            Step(Supply(60),
                 BuildGas(3)),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True),
            Step(UnitExists(UnitTypeId.GATEWAY, 6),
                 GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True)),
            Step(Supply(64),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=6, priority=True)),
            ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.STALKER, priority=True),
        )

    def counter_air(self) -> BuildOrder:
        return BuildOrder(
            AutoPylon(),
            AutoWorker(),
            Step(EnemyUnitExists(UnitTypeId.DARKTEMPLAR),
                 ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1)),

            Expand(2, priority=True),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            ProtossUnit(UnitTypeId.SENTRY, priority=True, to_count=1, only_once=True),
            ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=2, only_once=True),
            ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=2, only_once=True),
            DefensiveCannons(0, 1, 1),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=1, only_once=True),
            Step(Time(time_in_seconds=4 * 60),
                 Scout(UnitTypeId.PROBE, 1,
                       ScoutLocation.scout_enemy2(),
                       ScoutLocation.scout_enemy3(),
                       ScoutLocation.scout_enemy4(),
                       )
                 ),
            # chrono
            ChronoAnyTech(save_to_energy=0),

            Tech(UpgradeId.WARPGATERESEARCH),
            StepBuildGas(2, UnitExists(UnitTypeId.ROBOTICSFACILITY, 1)),
            Step(Supply(60),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=8, priority=True)),
            StepBuildGas(4, UnitExists(UnitTypeId.GATEWAY, 6)),

            # units

            Step(EnemyUnitExists(UnitTypeId.STALKER, 3),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=2)),
            Step(EnemyUnitExists(UnitTypeId.TEMPEST),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8)),
            Step(UnitExists(UnitTypeId.IMMORTAL, 5),
                 ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1)),
            Step(EnemyUnitExists(UnitTypeId.VOIDRAY),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8)),
            Step(EnemyUnitExists(UnitTypeId.IMMORTAL),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True)),

            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=4),
            ProtossUnit(UnitTypeId.STALKER, priority=True),
        )

    def counter_Robo(self) -> BuildOrder:
        # the only way to defeat early robo rush is to robo yourself!
        # and use the advantage of defense
        # this blink immortal is very OP and takes the advantage of
        # enemy not having air units
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            Cancel2ndBase(),
            Step(EnemyUnitExists(UnitTypeId.DARKTEMPLAR),
                 ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1)),

            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 10),
            ChronoUnit(UnitTypeId.STALKER, UnitTypeId.GATEWAY, 10),
            ChronoUnit(UnitTypeId.WARPPRISM, UnitTypeId.ROBOTICSFACILITY, 1),

            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            BuildGas(2),
            DefensiveCannons(0, 1, 0),
            Step(Supply(60),
                 Expand(2, priority=True)),
            StepBuildGas(requirement=UnitExists(UnitTypeId.PROBE, 36), to_count=4),

            Step(EnemyUnitExists(UnitTypeId.VOIDRAY),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8)),

            GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=2),

            Step(UnitExists(UnitTypeId.IMMORTAL, 2),
                 ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1)),
            Step(UnitExists(UnitTypeId.IMMORTAL, 2),
                 ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1)),
            Step(UnitExists(UnitTypeId.IMMORTAL, 2),
                 ProtossUnit(UnitTypeId.STALKER, priority=True)),

            ProtossUnit(UnitTypeId.SENTRY, priority=True, to_count=1, only_once=True),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True),
        )

    def counter_Robo_old(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            Cancel2ndBase(),
            Step(EnemyUnitExists(UnitTypeId.DARKTEMPLAR),
                 ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1)),

            ChronoUnit(UnitTypeId.ORACLE, UnitTypeId.STARGATE, 1),
            ChronoUnit(UnitTypeId.STALKER, UnitTypeId.GATEWAY, 10),

            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            BuildGas(2),
            DefensiveCannons(0, 1, 0),
            Step(Supply(54),
                 Expand(2, priority=True)),
            StepBuildGas(requirement=UnitExists(UnitTypeId.PROBE, 36), to_count=4),

            Step(EnemyUnitExists(UnitTypeId.TEMPEST),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8)),
            Step(UnitExists(UnitTypeId.IMMORTAL, 5),
                 ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1)),
            Step(EnemyUnitExists(UnitTypeId.VOIDRAY),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8)),
            Step(EnemyUnitExists(UnitTypeId.IMMORTAL),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True)),

            GridBuilding(unit_type=UnitTypeId.STARGATE, to_count=1),
            GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1),

            ProtossUnit(UnitTypeId.ORACLE, priority=True, to_count=1, only_once=True),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=3),
            ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.STALKER, priority=True),
        )

    def counter_FastDT(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1),

            ChronoUnit(UnitTypeId.OBSERVER, UnitTypeId.ROBOTICSFACILITY, 1),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=1, priority=True),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),

            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 3),

            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
            ProtossUnit(UnitTypeId.STALKER, to_count=3, priority=True),
            Tech(UpgradeId.WARPGATERESEARCH),
            Expand(2),
            DefensiveCannons(0, 1, 1),

            Step(UnitExists(UnitTypeId.IMMORTAL, 2),
                 ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1)),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=3),

            ProtossUnit(UnitTypeId.STALKER),

            StepBuildGas(requirement=UnitExists(UnitTypeId.PROBE, 36), to_count=4),
            Step(UnitExists(UnitTypeId.STALKER, 8),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True)),
            Step(UnitExists(UnitTypeId.PROBE, 38),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=7)),
        )

    # TODO: these are pvz related functions

    def pvz_main_force(self) -> BuildOrder:
        return BuildOrder(
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.Macro, self.pvz_eco_start_up()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.EcoExpand, self.pvz_micro_build()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.LingRush, self.couter_ling_rush()),

            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.RoachRush, self.couter_roach_rush()),
            # Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.NySwarm, self.couter_nyd_rush()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.NySwarm, self.couter_ling_rush()),
            Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.WorkerRush, self.pvz_micro_build()),
        )

    def pvz_eco_start_up(self) -> SequentialList:
        return SequentialList(
            Workers(13),
            GridBuilding(unit_type=UnitTypeId.PYLON, to_count=1, priority=True),
            Workers(14),

            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=1, priority=True),
            WorkerScout(),
            Workers(17),
            BuildGas(1),
            Workers(19),
            Expand(2, priority=True),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            # should have seen enemy 2nd base at ~ 1:12
            # either 2 base eco or 1 base rushes
        )

    def couter_roach_rush(self) -> BuildOrder:
        return BuildOrder(

            AutoPylon(),
            AutoWorker(),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 2),
            ChronoUnit(UnitTypeId.WARPPRISM, UnitTypeId.ROBOTICSFACILITY, 2),
            DoubleAdeptScout(2),

            Step(UnitExists(UnitTypeId.WARPPRISM, include_not_ready=True, include_killed=True), self.pvz_micro_build()),

            Step(EnemyUnitExists(UnitTypeId.ZERGLING, 4),
                 ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=1)),
            Step(EnemyUnitExists(UnitTypeId.ZERGLING, 8),
                 ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=6)),

            SequentialList(
                BuildGas(2),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
                GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
                GridBuilding(unit_type=UnitTypeId.PYLON, to_count=2, priority=True),
                ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=1, only_once=True),
                Step(UnitExists(UnitTypeId.PYLON, 2, include_not_ready=False),
                     GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True)),

                BuildOrder(
                    ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=1),
                    ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=4, only_once=True),
                ),

                BuildOrder(
                    ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
                    ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=4),
                    Tech(UpgradeId.WARPGATERESEARCH),
                    ProtossUnit(UnitTypeId.ADEPT, priority=True),
                    ProtossUnit(UnitTypeId.IMMORTAL, priority=True),
                ),
            ),
        )

    def couter_ling_rush(self) -> BuildOrder:
        return BuildOrder(
            ChronoAnyTech(save_to_energy=100),
            ChronoUnit(UnitTypeId.ZEALOT, UnitTypeId.GATEWAY, 1),
            ChronoUnit(UnitTypeId.ADEPT, UnitTypeId.GATEWAY, 4),
            Cancel2ndBase(),

            AutoPylon(),
            AutoWorker(),

            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            GridBuilding(unit_type=UnitTypeId.PYLON, to_count=2, priority=True),
            BuildGas(1),
            ProtossUnit(UnitTypeId.ZEALOT, to_count=1, priority=True, only_once=True),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
            ProtossUnit(UnitTypeId.ADEPT, to_count=2, priority=True, only_once=True),
            ProtossUnit(UnitTypeId.ZEALOT, to_count=2, priority=True),

            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True),
            ProtossUnit(UnitTypeId.ADEPT, to_count=6, priority=True),
            DoubleAdeptScout(5),

            Step(Supply(32),
                 Tech(UpgradeId.WARPGATERESEARCH)),
            Step(Supply(32),
                 BuildGas(2)),
            Step(Supply(44),
                 Expand(2, priority=True)),
            Step(UnitExists(UnitTypeId.NEXUS, 2),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=8, priority=True)),
            StepBuildGas(4, UnitExists(UnitTypeId.GATEWAY, 6)),

            Step(EnemyUnitExists(UnitTypeId.ZERGLING, 8),
                 ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=14)),

            ProtossUnit(UnitTypeId.STALKER, priority=True),
        )

    def couter_nyd_rush(self) -> BuildOrder:
        return BuildOrder(
            ChronoAnyTech(save_to_energy=0),
            ChronoUnit(UnitTypeId.ZEALOT, UnitTypeId.GATEWAY, 3),
            ChronoUnit(UnitTypeId.STALKER, UnitTypeId.GATEWAY, 8),

            Cancel2ndBase(),
            BuildGas(2),
            Step(UnitExists(UnitTypeId.STALKER, 8),
                 Expand(2, priority=True)),
            AutoPylon(),
            AutoWorker(),

            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
            GridBuilding(unit_type=UnitTypeId.PYLON, to_count=2, priority=True),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
            ProtossUnit(UnitTypeId.STALKER, to_count=2, priority=True),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True),
            ProtossUnit(UnitTypeId.STALKER, to_count=8, priority=True),
            Tech(UpgradeId.WARPGATERESEARCH),
            Step(Supply(44),
                 GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=8, priority=True)),
            StepBuildGas(4, UnitExists(UnitTypeId.GATEWAY, 6)),

            Step(EnemyUnitExists(UnitTypeId.ZERGLING, 8),
                 ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=14)),

            ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=3, only_once=True),
            ProtossUnit(UnitTypeId.STALKER, priority=True),
        )

    def pvz_micro_build(self) -> BuildOrder:
        # when enemy goes for 2nd base
        return BuildOrder(

            AutoPylon(),
            AutoWorker(),

            ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 2),
            ChronoUnit(UnitTypeId.PHOENIX, UnitTypeId.STARGATE, 3),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 13),
            ChronoUnit(UnitTypeId.COLOSSUS, UnitTypeId.ROBOTICSFACILITY, 4),
            Step(EnemyUnitExists(UnitTypeId.ZERGLING, 6),
                 ChronoUnit(UnitTypeId.ADEPT, UnitTypeId.GATEWAY, 1)),

            DoubleAdeptScout(1),
            Step(EnemyUnitExists(UnitTypeId.ZERGLING, 10),
                 ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=3)),
            Step(Supply(100),
                 Expand(3, priority=True)),

            StepBuildGas(3, Supply(56)),
            StepBuildGas(4, Supply(66)),
            SequentialList(
                BuildGas(1),
                Expand(2, priority=True),
                GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True),
                BuildGas(2),
                GridBuilding(unit_type=UnitTypeId.PYLON, to_count=2, priority=True),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=1, only_once=True),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
                Tech(UpgradeId.WARPGATERESEARCH),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=2, priority=True),
                ProtossUnit(UnitTypeId.STALKER, to_count=1, priority=True),

                ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=1, only_once=True),
                ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=2, only_once=True),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True),
                ProtossUnit(UnitTypeId.WARPPRISM, to_count=1, priority=True),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True),

                BuildOrder(
                    ProtossUnit(UnitTypeId.WARPPRISM, to_count=1, priority=True),
                    ProtossUnit(UnitTypeId.OBSERVER, to_count=1, priority=True),
                    ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=6),
                    ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=3),
                    ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=3, only_once=True),
                ),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSBAY, to_count=1, priority=True),
                BuildOrder(
                    Step(UnitExists(UnitTypeId.ROBOTICSBAY, include_not_ready=False),
                         ProtossUnit(UnitTypeId.COLOSSUS, priority=True, to_count=2)),
                    ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=5),
                    ProtossUnit(UnitTypeId.STALKER, to_count=8),
                    ProtossUnit(UnitTypeId.OBSERVER, to_count=2, priority=True),
                    GridBuilding(unit_type=UnitTypeId.STARGATE, to_count=1, priority=True),
                    ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=8),
                    ProtossUnit(UnitTypeId.PHOENIX, priority=True, to_count=6),
                    ProtossUnit(UnitTypeId.DISRUPTOR, to_count=2),
                    ProtossUnit(UnitTypeId.ADEPT, to_count=8),
                ),

                BuildOrder(
                    ProtossUnit(UnitTypeId.VOIDRAY, priority=True),
                    ProtossUnit(UnitTypeId.IMMORTAL, priority=True),
                    ProtossUnit(UnitTypeId.STALKER, priority=True),
                ),
            ),
        )

    # python run_custom.py -m OdysseyLE -p1 protossbot -p2 200roach

    def pvt_main_force(self) -> BuildOrder:
        return BuildOrder(
            SequentialList(
                self.pvt_eco_start_up(),
                BuildOrder(
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.TerranMacro, self.pvt_templar_build()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.ProxyMarine, self.pvt_macro_build()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.ProxyMarauders,
                         self.pvt_macro_build()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.ProxyFactory,
                         self.pvt_templar_build()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.EarlyExpand, self.pvt_templar_build()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.WorkerRush, self.counter_bunker()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.TerranOneBase, self.pvt_macro_build()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.Bunker, self.counter_bunker()),
                    Step(lambda k: k.build_detector.rush_build == EnemyRushBuild.TerranLate, self.pvt_macro_build()),
                )
            )
        )

    def pvt_eco_start_up(self) -> SequentialList:
        return SequentialList(
            Workers(13),
            GridBuilding(unit_type=UnitTypeId.PYLON, to_count=1, priority=True),
            Workers(15),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=1, priority=True),
            WorkerScout(),
            # 0:40 enemy open worker rush build
            Step(UnitExists(UnitTypeId.PYLON), action=ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 1)),
            Workers(17),
            BuildGas(1),
            Workers(19),
            GridBuilding(unit_type=UnitTypeId.CYBERNETICSCORE, to_count=1, priority=True)
        )

    def pvt_dt_build(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(notready_count=0),
            AutoPylon(),
            WarpPrismHarass(),

            ChronoUnit(UnitTypeId.WARPPRISM, UnitTypeId.ROBOTICSFACILITY, 1),
            ChronoAnyTech(save_to_energy=50),

            Step(
                Time(5 * 60 + 15),
                SequentialList(
                    Expand(3, priority=True),
                    self.pvt_mid_game_build()
                )
            ),

            SequentialList(
                Expand(2, priority=True),
                BuildGas(2),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=1, only_once=True),
                ChronoUnit(UnitTypeId.ADEPT, UnitTypeId.GATEWAY, 1),
                DefensivePylons(to_base_index=1),
                Tech(UpgradeId.WARPGATERESEARCH),
                GridBuilding(unit_type=UnitTypeId.TWILIGHTCOUNCIL, to_count=1, priority=True),
                DefensiveCannons(to_base_index=1, additional_batteries=1, to_count_pre_base=0),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=1, only_once=True),
                Step(UnitExists(UnitTypeId.TWILIGHTCOUNCIL, include_not_ready=False),
                     GridBuilding(unit_type=UnitTypeId.DARKSHRINE, to_count=1, priority=True)),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True),
                ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
                BuildGas(3),
                Tech(UpgradeId.BLINKTECH),
            ),
        )

    def pvt_micro_build(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),

            ChronoUnit(UnitTypeId.WARPPRISM, UnitTypeId.ROBOTICSFACILITY, 1),
            ChronoAnyTech(save_to_energy=50),

            SequentialList(
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 1),
                Expand(2, priority=True),
                BuildGas(2),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=1, only_once=True),
                Tech(UpgradeId.WARPGATERESEARCH),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=2, only_once=True),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True),
                GridBuilding(unit_type=UnitTypeId.TWILIGHTCOUNCIL, to_count=1, priority=True),
                BuildGas(4),
                Tech(UpgradeId.BLINKTECH),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=7, priority=True),
            ),
            ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.STALKER, priority=True),
        )

    def pvt_templar_build(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),
            DoubleAdeptScout(3),

            ChronoUnit(UnitTypeId.WARPPRISM, UnitTypeId.ROBOTICSFACILITY, 1),
            ChronoUnit(UnitTypeId.COLOSSUS, UnitTypeId.ROBOTICSFACILITY, 7),
            ChronoAnyTech(save_to_energy=50),
            Step(EnemyUnitExists(UnitTypeId.PLANETARYFORTRESS), Expand(to_count=3, priority=True)),

            SequentialList(
                Expand(2, priority=True),
                BuildGas(2),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=1, only_once=True),
                ChronoUnit(UnitTypeId.ADEPT, UnitTypeId.GATEWAY, 1),
                Tech(UpgradeId.WARPGATERESEARCH),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=2, only_once=True),
                GridBuilding(unit_type=UnitTypeId.TWILIGHTCOUNCIL, to_count=1, priority=True),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=3, only_once=True),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True),
                Tech(UpgradeId.BLINKTECH),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=1, only_once=True),

                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
                ProtossUnit(UnitTypeId.SENTRY, priority=True, to_count=1, only_once=True),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=2, only_once=True),
                BuildGas(3),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=4, only_once=True),
                ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1),
                Expand(3, priority=True),

                ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=1, only_once=True),
                Tech(UpgradeId.CHARGE),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=7, only_once=True),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSBAY, to_count=1, priority=True),
                ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=3, only_once=True),
                ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1, only_once=True),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=6, priority=True),
                Tech(UpgradeId.EXTENDEDTHERMALLANCE),
                ProtossUnit(UnitTypeId.DISRUPTOR, priority=True, to_count=1, only_once=True),
                GridBuilding(unit_type=UnitTypeId.FORGE, to_count=2, priority=True),
                ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=13, only_once=True),
                ProtossUnit(UnitTypeId.COLOSSUS, priority=True, to_count=1, only_once=True),
                Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1),
                Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1),
                ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8, only_once=True),
                Expand(4, priority=True),

                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=10, priority=True),

                BuildOrder(
                    ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=15),
                    ProtossUnit(UnitTypeId.DISRUPTOR, priority=True, to_count=1),
                    ProtossUnit(UnitTypeId.COLOSSUS, priority=True, to_count=3),
                    ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=25),
                    ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=4),
                    ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8),
                    ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=12),
                ),
            ),
        )

    def counter_onebase(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(notready_count=0),
            AutoPylon(),
            Step(Time(4 * 60), ChronoAnyTech(save_to_energy=50)),
            DoubleAdeptScout(1),

            Step(EnemyUnitExists(UnitTypeId.PLANETARYFORTRESS), Expand(to_count=3, priority=True)),
            Step(UnitExists(UnitTypeId.STARGATE), self.pvt_mid_game_build()),

            SequentialList(
                Expand(2, priority=True),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=1, only_once=True),
                ChronoUnit(UnitTypeId.ADEPT, UnitTypeId.GATEWAY, 1),
                DefensivePylons(to_base_index=1),
                Tech(UpgradeId.WARPGATERESEARCH),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=1, only_once=True),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
                DefensiveCannons(to_base_index=1, additional_batteries=1, to_count_pre_base=0),
                ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=1, only_once=True),
                ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 1),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=3, priority=True),
                BuildGas(2),
                ProtossUnit(UnitTypeId.SENTRY, priority=True, to_count=1),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=2, only_once=True),
                ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=4, only_once=True),
                BuildGas(3),
                GridBuilding(unit_type=UnitTypeId.TWILIGHTCOUNCIL, to_count=1, priority=True),
                ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
                BuildGas(4),
                Step(UnitExists(UnitTypeId.NEXUS, 3),
                     GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=8, priority=True)),
                ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=2, only_once=True),
                ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=6, only_once=True),
                Tech(UpgradeId.BLINKTECH),
                GridBuilding(unit_type=UnitTypeId.STARGATE, to_count=1, priority=True),
            )
        )

    def pvt_macro_build(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(notready_count=0),
            AutoPylon(),

            # final battle
            Step(
                UnitExists(UnitTypeId.NEXUS, 3, include_not_ready=False),
                self.pvt_final_build(),
            ),

            # mid game
            self.counter_onebase(),
        )

    def counter_bunker(self) -> BuildOrder:
        return BuildOrder(
            Step(UnitExists(UnitTypeId.NEXUS, 2), self.pvt_micro_build()),
            AutoWorker(notready_count=0),
            AutoPylon(),
            Cancel2ndBase(),

            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY),
            SequentialList(
                BuildGas(2),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=2, priority=True),
                GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1, priority=True),
                Tech(UpgradeId.WARPGATERESEARCH),
                GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4, priority=True),
            ),

            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=1, only_once=True),
            ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1),
            Step(
                Supply(58),
                Expand(2, priority=True),
            ),
            DoubleAdeptScout(4),

            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=4),
            ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=2),
            ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1),
        )

    def pvt_mid_game_build(self) -> BuildOrder:
        return BuildOrder(

            Expand(to_count=2, priority=True),
            ChronoAnyTech(save_to_energy=50),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY),
            Tech(UpgradeId.BLINKTECH),
            Tech(UpgradeId.CHARGE),

            Step(Supply(72), Expand(to_count=3, priority=True)),
            Step(EnemyUnitExists(UnitTypeId.PLANETARYFORTRESS), Expand(to_count=3, priority=True)),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=4),
            Step(
                UnitExists(UnitTypeId.NEXUS, 3),
                BuildOrder(
                    GridBuilding(unit_type=UnitTypeId.ROBOTICSFACILITY, to_count=1),
                    GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=6),
                )
            ),
            ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=1),

            Step(EnemyUnitExists(UnitTypeId.BATTLECRUISER, 1),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=10)),
            Step(EnemyUnitExists(UnitTypeId.BANSHEE, 1),
                 ProtossUnit(UnitTypeId.PHOENIX, priority=True, to_count=2)),
            Step(EnemyUnitExists(UnitTypeId.BANSHEE, 1),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=4)),

            Step(EnemyUnitExists(UnitTypeId.MARAUDER, 4),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=2)),
            Step(EnemyUnitExists(UnitTypeId.MARINE, 4),
                 ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=4)),

            GridBuilding(unit_type=UnitTypeId.STARGATE, to_count=1, priority=True),

            ProtossUnit(UnitTypeId.WARPPRISM, priority=True, to_count=1),
            ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=3),
            ProtossUnit(UnitTypeId.PHOENIX, priority=True, to_count=4),
            ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8),
            ProtossUnit(UnitTypeId.ADEPT, priority=True, to_count=6),
            ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=13),
        )

    def pvt_final_build(self) -> BuildOrder:
        return BuildOrder(
            AutoWorker(),
            AutoPylon(),

            ChronoAnyTech(save_to_energy=50),
            ChronoUnit(UnitTypeId.TEMPEST, UnitTypeId.STARGATE, 10),
            ChronoUnit(UnitTypeId.MOTHERSHIP, UnitTypeId.NEXUS, 3),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 5),
            GridBuilding(unit_type=UnitTypeId.GATEWAY, to_count=6),

            Step(
                Minerals(700),
                ProtossUnit(UnitTypeId.ZEALOT, priority=True),
            ),

            Step(
                Gas(700),
                SequentialList(
                    GridBuilding(unit_type=UnitTypeId.TEMPLARARCHIVE, to_count=1),
                    ProtossUnit(UnitTypeId.HIGHTEMPLAR, priority=True),
                    Archon([UnitTypeId.HIGHTEMPLAR]),
                )
            ),

            Step(
                UnitExists(UnitTypeId.NEXUS, 4),
                SequentialList(
                    Tech(UpgradeId.PROTOSSSHIELDSLEVEL1),
                    Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2),
                    Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
                    Tech(UpgradeId.PROTOSSSHIELDSLEVEL2),
                )
            ),

            Step(
                UnitExists(UnitTypeId.NEXUS, 4),
                SequentialList(
                    GridBuilding(unit_type=UnitTypeId.STARGATE, to_count=1, priority=True),
                    GridBuilding(unit_type=UnitTypeId.FLEETBEACON, to_count=1, priority=True),
                    ProtossUnit(UnitTypeId.PHOENIX, priority=True, to_count=6),
                    ProtossUnit(UnitTypeId.MOTHERSHIP, priority=True, to_count=1),
                )
            ),
            ProtossUnit(UnitTypeId.OBSERVER, priority=True, to_count=2),

            Step(EnemyUnitExists(UnitTypeId.BATTLECRUISER, 2),
                 ProtossUnit(UnitTypeId.TEMPEST, priority=True, to_count=4)),
            Step(EnemyUnitExists(UnitTypeId.BANSHEE, 1),
                 ProtossUnit(UnitTypeId.STALKER, priority=True, to_count=8)),
            Step(EnemyUnitExists(UnitTypeId.CYCLONE, 1),
                 ProtossUnit(UnitTypeId.PHOENIX, priority=True, to_count=2)),
            Step(EnemyUnitExists(UnitTypeId.BANSHEE, 1),
                 ProtossUnit(UnitTypeId.PHOENIX, priority=True, to_count=6)),

            Step(EnemyUnitExists(UnitTypeId.MARAUDER, 4),
                 ProtossUnit(UnitTypeId.IMMORTAL, priority=True, to_count=3)),
            Step(EnemyUnitExists(UnitTypeId.SIEGETANKSIEGED, 4),
                 ProtossUnit(UnitTypeId.ZEALOT, priority=True, to_count=25)),

            self.pvt_templar_build()
        )

    def pvr_main_force(self) -> BuildOrder:
        return BuildOrder(
            SequentialList(
                self.pvz_eco_start_up(),
                BuildOrder(
                    self.pvz_main_force(),
                    self.pvp_main_force(),
                    self.pvt_main_force(),
                )
            )
        )
