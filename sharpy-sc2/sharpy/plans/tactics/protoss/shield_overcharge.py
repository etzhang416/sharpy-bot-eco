from sharpy.managers.version_manager import GameVersion
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit

from sharpy.plans.acts.act_base import ActBase


class ShieldOvercharge(ActBase):
    # shield overcharge to defend base
    def __init__(self):
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

    async def execute(self) -> bool:
        version = (self.knowledge.version_manager.base_version == GameVersion.V_5_0_6)
        if version:
            for battery in self.cache.own(UnitTypeId.SHIELDBATTERY).ready:  # type: Unit
                if battery.energy_percentage <= 0.1:
                    if not battery.has_buff(BuffId.BATTERYOVERCHARGE):
                        nexuses = self.cache.own(UnitTypeId.NEXUS).filter(lambda base: base.energy >= 50)
                        if nexuses.amount > 0:
                            nexus = nexuses.closest_to(battery)
                            self.ai.do(nexus(AbilityId.BATTERYOVERCHARGE_BATTERYOVERCHARGE, battery))
        else:
            for battery in self.cache.own(UnitTypeId.SHIELDBATTERY).ready:  # type: Unit
                if battery.energy_percentage <= 0.1:
                    if not battery.has_buff(BuffId.BATTERYOVERCHARGE):
                        nexuses = self.cache.own(UnitTypeId.NEXUS).filter(lambda base: base.energy >= 50)
                        if nexuses.amount > 0:
                            nexus = nexuses.closest_to(battery)
                            self.ai.do(nexus(AbilityId.BATTERYOVERCHARGE_BATTERYOVERCHARGE, battery))
        return True
