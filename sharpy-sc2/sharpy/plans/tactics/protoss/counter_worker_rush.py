from sc2.unit import Unit
from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sharpy.knowledges import Knowledge
from sc2 import UnitTypeId, AbilityId


class ProtossCounterWorkerRush(ActBase):
    def __init__(self):
        super().__init__()

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)

    async def execute(self) -> bool:
        # this actbase is just a place holder to document that
        # counter_worker_rush is handled in PlanZoneDefense() with:
        # (len(enemies) == 1 and enemies[0].type_id not in self.unit_values.worker_types)
        # removed to make sure there is no enemy worker attacking my worker
        return True