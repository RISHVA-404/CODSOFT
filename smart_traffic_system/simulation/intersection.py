# =============================================================================
# simulation/intersection.py — 4-way intersection, spawn scheduler
# =============================================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import *
from simulation.lane import Lane


class Intersection:
    """
    The 4-way intersection.

    Responsibilities:
    • Hold all four Lane objects
    • Manage per-lane spawn timers
    • Route update calls to each lane each frame
    """

    def __init__(self):
        self.lanes: dict[str, Lane] = {
            name: Lane(name) for name in LANE_NAMES
        }

        # Stagger spawn timers so vehicles don't all appear at once
        self._spawn_timers = {
            'north': 10,
            'south': SPAWN_INTERVAL // 2,
            'east':  SPAWN_INTERVAL // 4,
            'west':  SPAWN_INTERVAL * 3 // 4,
        }

        self.frame = 0

    # ── Public interface ──────────────────────────────────────────────────────

    def update(self):
        """Called once per frame by the main loop."""
        self.frame += 1
        self._tick_spawners()
        for lane in self.lanes.values():
            lane.update()

    def set_signal(self, lane_id: str, state: str):
        self.lanes[lane_id].set_signal(state)

    def get_lane(self, lane_id: str) -> Lane:
        return self.lanes[lane_id]

    # ── Spawn management ──────────────────────────────────────────────────────

    def _tick_spawners(self):
        for name, lane in self.lanes.items():
            self._spawn_timers[name] -= 1
            if self._spawn_timers[name] <= 0:
                self._spawn_timers[name] = SPAWN_INTERVAL
                if lane.can_spawn():
                    lane.spawn_vehicle()

    # ── Aggregate statistics ──────────────────────────────────────────────────

    @property
    def total_vehicles(self) -> int:
        return sum(len(l.vehicles) for l in self.lanes.values())

    @property
    def total_throughput(self) -> int:
        return sum(l.throughput for l in self.lanes.values())

    @property
    def overall_avg_wait(self) -> float:
        waits  = [l.avg_wait for l in self.lanes.values() if l.throughput > 0]
        return sum(waits) / len(waits) if waits else 0.0

    def waiting_counts(self) -> dict[str, int]:
        return {name: lane.waiting_count for name, lane in self.lanes.items()}
