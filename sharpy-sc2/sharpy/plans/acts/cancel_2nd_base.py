from typing import Optional

from sc2 import UnitTypeId, BotAI, AbilityId
from sc2.game_data import AbilityData
from sc2.unit import Unit, UnitOrder
from .act_base import ActBase


class Cancel2ndBase(ActBase):

    def __init__(self):
        super().__init__()
        self.canceled = False

    async def execute(self) -> bool:
        if not self.canceled:
            if self.ai.townhalls.amount == 1:
                self.canceled = True
                return True
            for base in self.ai.townhalls:  # type: Unit
                if 1 > base.build_progress > 0 and self.ai.time <= 4*60:
                    self.print(
                        f"Cancelled {base.type_id.name} at {base.position} with {base.health} health"
                    )
                    self.do(base(AbilityId.CANCEL_BUILDINPROGRESS))
                    self.canceled = True
                    return True
        return True
