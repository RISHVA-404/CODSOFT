# =============================================================================
# algorithm/bankers_algorithm.py — Deadlock-Avoidance via Banker's Algorithm
# =============================================================================
#
# Concept mapping for traffic domain:
#   Process  →  Traffic lane  (N, S, E, W)
#   Resource →  Green-signal time units
#   Allocation[i] → units currently held by lane i
#   Max[i]        → max units lane i could ever need
#   Need[i]       → Max[i] − Allocation[i]
#   Available     → total pool − Σ Allocation[i]
#
# =============================================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *


class BankersAlgorithm:
    """
    Resource-Allocation and Deadlock-Avoidance algorithm.

    Uses a single resource type (green_time_units).  The total pool is
    GREEN_UNITS_TOTAL; at most one lane holds a non-zero allocation at
    any given moment (traffic can only flow in one direction at a time).

    Key operations
    --------------
    check_safety()        – Is the *current* state safe?
    find_safe_allocation()– Which lane should receive green next?
    request_resource()    – Attempt to give resources to one process.
    """

    def __init__(self):
        self.n   = N_LANES              # number of processes (lanes)
        self.m   = 1                    # number of resource types (1 = green_time)
        self.total = GREEN_UNITS_TOTAL  # total resource pool

        # State arrays  (index order: north=0, south=1, east=2, west=3)
        self.allocation  = [0] * self.n    # units currently allocated
        self.max_need    = [0] * self.n    # maximum units each lane needs
        self.available   = self.total       # currently unallocated units

        # Audit trail for analytics
        self.last_safe_sequence : list[int] = []
        self.deadlock_count      = 0
        self.total_evaluations   = 0

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _need(self, i: int) -> int:
        return max(0, self.max_need[i] - self.allocation[i])

    def _safety_check_state(self,
                             allocation : list[int],
                             max_need   : list[int],
                             available  : int) -> tuple[bool, list[int]]:
        """
        Run the Banker's Safety Algorithm on an explicit state snapshot.
        Returns (is_safe, safe_sequence_of_process_indices).
        """
        work    = available
        finish  = [False] * self.n
        seq     = []

        # Iterate until all processes are 'finished' or we're stuck
        while len(seq) < self.n:
            found = False
            for i in range(self.n):
                if not finish[i]:
                    need_i = max(0, max_need[i] - allocation[i])
                    if need_i <= work:
                        # Process i can complete; release its allocation
                        work      += allocation[i]
                        finish[i]  = True
                        seq.append(i)
                        found      = True
                        # Restart inner loop for correctness
                        break
            if not found:
                break

        is_safe = all(finish)
        return is_safe, seq

    # ── Public API ───────────────────────────────────────────────────────────

    def update_max_needs(self, vehicle_counts: dict[str, int]):
        """
        Recompute max_need for every lane based on current queue depth.
        A lane with k waiting vehicles needs up to min(k, MAX_UNITS_PER_LANE) units.
        """
        for idx, name in enumerate(LANE_NAMES):
            cnt = vehicle_counts.get(name, 0)
            self.max_need[idx] = min(cnt, MAX_UNITS_PER_LANE) if cnt > 0 else 0

    def check_safety(self) -> tuple[bool, list[str]]:
        """
        Check whether the *current* resource-allocation state is safe.
        Returns (is_safe, safe_sequence_as_lane_names).
        """
        self.total_evaluations += 1
        is_safe, seq_idx = self._safety_check_state(
            self.allocation, self.max_need, self.available
        )
        seq_names = [LANE_NAMES[i] for i in seq_idx]
        self.last_safe_sequence = seq_names
        if not is_safe:
            self.deadlock_count += 1
        return is_safe, seq_names

    def release_all(self):
        """Release all currently allocated resources (end of green phase)."""
        self.available  = self.total
        self.allocation = [0] * self.n

    def request_resource(self, lane_id: str, units: int) -> tuple[bool, str]:
        """
        Try to allocate `units` green-time to `lane_id`.
        Returns (success, reason_string).
        Implements the full Banker's request algorithm:
          1. Check request ≤ need
          2. Check request ≤ available
          3. Tentatively allocate
          4. Run safety check
          5. Commit if safe, else roll back
        """
        idx = LANE_NAMES.index(lane_id)

        need_i = self._need(idx)
        if units > need_i:
            return False, f"Request {units} > Need {need_i} (error condition)"

        if units > self.available:
            return False, f"Request {units} > Available {self.available} (wait)"

        # Tentative allocation
        tentative_alloc = list(self.allocation)
        tentative_avail = self.available - units
        tentative_alloc[idx] += units

        is_safe, _ = self._safety_check_state(
            tentative_alloc, self.max_need, tentative_avail
        )

        if is_safe:
            # Commit
            self.allocation  = tentative_alloc
            self.available   = tentative_avail
            return True, "OK – safe state confirmed"
        else:
            return False, "UNSAFE – allocation rolled back"

    def find_safe_allocation(self, vehicle_counts: dict[str, int]) -> tuple[str | None, bool, list[str]]:
        """
        Evaluate every candidate lane and return the best safe choice.

        Returns
        -------
        best_lane   – lane_id to give green, or None if no vehicles anywhere
        is_safe     – True if a safe choice was found
        safe_seq    – the projected safe execution sequence
        """
        self.update_max_needs(vehicle_counts)

        # First do a global safety check on the current state
        is_safe_now, _ = self.check_safety()

        # Rank candidates: lanes with vehicles, sorted by count (desc)
        candidates = sorted(
            [(name, vehicle_counts.get(name, 0)) for name in LANE_NAMES
             if vehicle_counts.get(name, 0) > 0],
            key=lambda t: t[1], reverse=True
        )

        if not candidates:
            return None, True, []

        # Try allocating to each candidate, pick first safe option
        for lane_id, cnt in candidates:
            idx   = LANE_NAMES.index(lane_id)
            units = min(cnt, MAX_UNITS_PER_LANE)
            if units == 0:
                continue

            # Simulate the allocation
            sim_alloc  = [0] * self.n   # fresh state (no lane is green yet)
            sim_avail  = self.total - units
            sim_alloc[idx] = units

            ok, seq = self._safety_check_state(sim_alloc, self.max_need, sim_avail)
            if ok:
                return lane_id, True, [LANE_NAMES[i] for i in seq]

        # Nothing is safe (congestion deadlock scenario)
        self.deadlock_count += 1
        # Fall back: serve the busiest lane anyway to clear deadlock
        best = candidates[0][0]
        return best, False, []

    # ── State summary ─────────────────────────────────────────────────────────

    def state_summary(self) -> dict:
        return {
            'allocation' : {LANE_NAMES[i]: self.allocation[i] for i in range(self.n)},
            'max_need'   : {LANE_NAMES[i]: self.max_need[i]   for i in range(self.n)},
            'need'       : {LANE_NAMES[i]: self._need(i)       for i in range(self.n)},
            'available'  : self.available,
            'total'      : self.total,
            'deadlocks'  : self.deadlock_count,
            'evaluations': self.total_evaluations,
        }
