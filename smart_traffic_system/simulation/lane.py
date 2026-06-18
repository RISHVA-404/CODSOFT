# =============================================================================
# simulation/lane.py — Traffic lane with vehicle queue management
# =============================================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import *
from simulation.vehicle import Vehicle
import random


class Lane:
    """
    A single traffic approach lane.

    Manages:
    • vehicle spawning & queue ordering
    • stop-line enforcement (red / green signal)
    • throughput and wait-time statistics
    """

    def __init__(self, lane_id: str):
        self.lane_id     = lane_id          # 'north','south','east','west'
        self.vehicles    : list[Vehicle] = []
        self.signal      = 'red'            # 'red' | 'yellow' | 'green'
        self.throughput  = 0                # vehicles that passed through
        self.total_wait  = 0               # cumulative wait frames

        # ── Geometry derived from lane_id ──────────────────────────────────
        cfg = self._config()
        self.direction   = cfg['direction']
        self.spawn_x     = cfg['spawn_x']
        self.spawn_y     = cfg['spawn_y']
        self.stop_coord  = cfg['stop_coord']  # the coordinate at the stop line
        self.axis        = cfg['axis']        # 'y' for N/S, 'x' for E/W
        self.travel_sign = cfg['travel_sign'] # +1 or -1 (increasing or decreasing)

    # ── Configuration lookup ──────────────────────────────────────────────────

    def _config(self) -> dict:
        cfgs = {
            'north': dict(
                direction='south',
                spawn_x=NORTH_LANE_X, spawn_y=-55,
                stop_coord=STOP_N, axis='y', travel_sign=+1,
            ),
            'south': dict(
                direction='north',
                spawn_x=SOUTH_LANE_X, spawn_y=SCREEN_HEIGHT + 55,
                stop_coord=STOP_S, axis='y', travel_sign=-1,
            ),
            'east': dict(
                direction='west',
                spawn_x=DASH_X + 60, spawn_y=EAST_LANE_Y,
                stop_coord=STOP_E, axis='x', travel_sign=-1,
            ),
            'west': dict(
                direction='east',
                spawn_x=-55, spawn_y=WEST_LANE_Y,
                stop_coord=STOP_W, axis='x', travel_sign=+1,
            ),
        }
        return cfgs[self.lane_id]

    # ── Vehicle spawning ──────────────────────────────────────────────────────

    def can_spawn(self) -> bool:
        if len(self.vehicles) >= LANE_CAPACITY:
            return False
        # Don't spawn if last vehicle is too close to spawn point
        if self.vehicles:
            last = self.vehicles[-1]
            if self.axis == 'y':
                dist = abs(last.y - self.spawn_y)
            else:
                dist = abs(last.x - self.spawn_x)
            if dist < VEH_NS_H + 10:
                return False
        return True

    def spawn_vehicle(self):
        """Add a new vehicle at the spawn point."""
        color = random.choice(VEHICLE_COLORS)
        v = Vehicle(self.spawn_x, self.spawn_y, self.direction, color)
        v.speed = MAX_SPEED * 0.4   # start slow
        self.vehicles.append(v)
        return v

    # ── Update logic ──────────────────────────────────────────────────────────

    def _get_position(self, v: Vehicle) -> float:
        return v.y if self.axis == 'y' else v.x

    def _distance_to_stop(self, v: Vehicle) -> float:
        """Signed distance remaining to the stop line (positive = must travel further)."""
        pos = self._get_position(v)
        return (self.stop_coord - pos) * self.travel_sign

    def _gap_to_leader(self, v: Vehicle, leader: Vehicle) -> float:
        """Bumper-to-bumper gap to the vehicle ahead."""
        if self.axis == 'y':
            size = v.h
            return abs(leader.y - v.y) - size
        else:
            size = v.w
            return abs(leader.x - v.x) - size

    def update(self):
        """Step all vehicles forward by one frame."""
        passed_vehicles = []

        for idx, v in enumerate(self.vehicles):
            leader  = self.vehicles[idx - 1] if idx > 0 else None
            dist_to_stop = self._distance_to_stop(v)

            # Has this vehicle already cleared the intersection?
            if v.passed:
                v.accelerate()
                v.move()
                v.tick_wait()
                if v.is_off_screen():
                    passed_vehicles.append(v)
                continue

            # ── Determine whether to brake ─────────────────────────────────
            brake = False

            # 1. Stop line enforcement
            if self.signal in ('red', 'yellow'):
                if dist_to_stop > 0 and dist_to_stop < SAFE_DISTANCE * 2:
                    brake = True
                # Hard stop at line
                if dist_to_stop <= 2 and dist_to_stop >= -2:
                    v.speed = 0.0
                    if self.axis == 'y':
                        v.y = self.stop_coord
                    else:
                        v.x = self.stop_coord
                    v.tick_wait()
                    continue
                if dist_to_stop < 0:
                    # Already at or past stop, stay put
                    v.speed = 0.0
                    v.tick_wait()
                    continue

            # 2. Following distance (queue behind leader)
            if leader and not leader.passed:
                gap = self._gap_to_leader(v, leader)
                if gap < SAFE_DISTANCE:
                    brake = True
                elif gap < SAFE_DISTANCE * 1.8:
                    brake = True  # gentle pre-brake

            # ── Accelerate / decelerate ────────────────────────────────────
            if brake:
                v.decelerate()
            else:
                v.accelerate()

            v.move()
            v.tick_wait()

            # Mark as passed once it clears the intersection box
            if not v.passed:
                pos = self._get_position(v)
                if self.travel_sign == +1 and pos > self.stop_coord + HALF_ROAD * 2 + 10:
                    v.passed = True
                    self.throughput += 1
                    self.total_wait += v.wait_time
                elif self.travel_sign == -1 and pos < self.stop_coord - HALF_ROAD * 2 - 10:
                    v.passed = True
                    self.throughput += 1
                    self.total_wait += v.wait_time

        # Remove off-screen passed vehicles
        for v in passed_vehicles:
            self.vehicles.remove(v)

    # ── Statistics ────────────────────────────────────────────────────────────

    @property
    def waiting_count(self) -> int:
        """Vehicles queued before the stop line."""
        return sum(1 for v in self.vehicles if not v.passed)

    @property
    def avg_wait(self) -> float:
        if self.throughput == 0:
            return 0.0
        return self.total_wait / self.throughput / FPS  # seconds

    def set_signal(self, state: str):
        self.signal = state
        # When signal goes green, mark vehicles' target speed
        if state == 'green':
            for v in self.vehicles:
                v.target_speed = MAX_SPEED
