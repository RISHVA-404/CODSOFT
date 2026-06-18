# =============================================================================
# controller/signal_controller.py — Smart Signal Controller
# =============================================================================
#
# State machine per signal cycle:
#
#   IDLE  ──(decision_timer expires)──► EVALUATING
#   EVALUATING ──(Banker's picks lane)──► GREEN  (active_lane = winner)
#   GREEN ──(green_timer expires)──► YELLOW
#   YELLOW ──(yellow_timer expires)──► IDLE  (all signals → red)
#
# =============================================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import *
from algorithm.bankers_algorithm import BankersAlgorithm
from simulation.intersection import Intersection


class SignalController:
    """
    Reads traffic density from the intersection, runs the Banker's Algorithm
    to determine which lane receives the green signal, and drives the
    signal state machine.
    """

    # Internal states
    _S_IDLE       = 'idle'
    _S_GREEN      = 'green'
    _S_YELLOW     = 'yellow'

    def __init__(self, intersection: Intersection):
        self.intersection = intersection
        self.banker       = BankersAlgorithm()

        self.state        = self._S_IDLE
        self.active_lane  : str | None = None   # currently green lane
        self.green_frames = 0        # remaining green frames for active lane
        self.yellow_frames= 0        # remaining yellow frames
        self.idle_timer   = DECISION_INTERVAL // 2  # initial boot delay

        # Analytics
        self.is_safe         = True
        self.safe_sequence   : list[str] = []
        self.last_decision   = "Initialising…"
        self.green_units_given = 0   # units allocated to current green lane

        # Set all signals red at startup
        self._set_all_red()

    # ── Main update (called every frame) ──────────────────────────────────────

    def update(self):
        if   self.state == self._S_IDLE:
            self._tick_idle()
        elif self.state == self._S_GREEN:
            self._tick_green()
        elif self.state == self._S_YELLOW:
            self._tick_yellow()

    # ── State handlers ────────────────────────────────────────────────────────

    def _tick_idle(self):
        self.idle_timer -= 1
        if self.idle_timer <= 0:
            self._evaluate_and_switch()

    def _tick_green(self):
        self.green_frames -= 1
        if self.green_frames <= 0:
            # Transition to yellow
            self._set_all_red()
            if self.active_lane:
                self.intersection.set_signal(self.active_lane, 'yellow')
            self.yellow_frames = YELLOW_FRAMES
            self.state = self._S_YELLOW
            # Release banker allocation
            self.banker.release_all()

    def _tick_yellow(self):
        self.yellow_frames -= 1
        if self.yellow_frames <= 0:
            self._set_all_red()
            self.active_lane  = None
            self.idle_timer   = DECISION_INTERVAL
            self.state        = self._S_IDLE

    # ── Decision logic (Banker's Algorithm) ───────────────────────────────────

    def _evaluate_and_switch(self):
        counts = self.intersection.waiting_counts()
        total_waiting = sum(counts.values())

        if total_waiting == 0:
            # Nothing to serve; stay idle a bit longer
            self.idle_timer = DECISION_INTERVAL // 2
            self.last_decision = "No vehicles – waiting"
            return

        # Ask Banker's Algorithm for the safest lane
        best_lane, safe, seq = self.banker.find_safe_allocation(counts)
        self.is_safe       = safe
        self.safe_sequence = seq

        if best_lane is None:
            self.idle_timer   = DECISION_INTERVAL // 4
            self.last_decision = "No candidate lane found"
            return

        # Compute green duration from units allocated
        units = min(counts.get(best_lane, 1), MAX_UNITS_PER_LANE)
        units = max(units, 1)

        # Formally request the resource through Banker's API
        ok, reason = self.banker.request_resource(best_lane, units)
        if not ok and safe:
            # Fallback: grant anyway (safety already checked in find_safe_allocation)
            self.banker.allocation[LANE_NAMES.index(best_lane)] = units
            self.banker.available = max(0, self.banker.available - units)

        self.active_lane       = best_lane
        self.green_units_given = units
        self.green_frames      = units * FRAMES_PER_UNIT
        self.state             = self._S_GREEN
        self.last_decision     = (
            f"{'SAFE' if safe else 'UNSAFE'} → {best_lane.upper()} "
            f"({units} units × {FRAMES_PER_UNIT}f = {self.green_frames}f)"
        )

        # Set signals
        self._set_all_red()
        self.intersection.set_signal(best_lane, 'green')

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_all_red(self):
        for name in LANE_NAMES:
            self.intersection.set_signal(name, 'red')

    # ── Properties for dashboard ──────────────────────────────────────────────

    @property
    def green_progress(self) -> float:
        """0.0 → 1.0 fraction of current green phase elapsed."""
        if self.state != self._S_GREEN:
            return 0.0
        total = self.green_units_given * FRAMES_PER_UNIT
        if total == 0:
            return 0.0
        return 1.0 - self.green_frames / total

    @property
    def banker_state(self) -> dict:
        return self.banker.state_summary()

    @property
    def phase_label(self) -> str:
        if self.state == self._S_GREEN:
            return f"GREEN — {self.active_lane.upper()}"
        elif self.state == self._S_YELLOW:
            return f"YELLOW — clearing"
        else:
            return "RED — evaluating"
