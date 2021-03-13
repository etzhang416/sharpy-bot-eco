from sharpy.plans.require.require_base import RequireBase


class EnemyBases(RequireBase):
    """
    Checks if enemy has at least the requested amount of bases.
    """

    def __init__(self, count: int):
        assert count is not None and isinstance(count, int)
        super().__init__()
        self.count = count

    def check(self) -> bool:
        zone_count = 0
        for zone in self.knowledge.enemy_expansion_zones:
            if zone.is_enemys:
                zone_count += 1

        return zone_count >= self.count
