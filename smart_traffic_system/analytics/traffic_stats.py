# =============================================================================
# analytics/traffic_stats.py — Real-time traffic metrics aggregation
# =============================================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *
from collections import deque


class TrafficStats:
    """
    Aggregates and exposes real-time metrics for the dashboard and
    post-simulation reports.

    Tracks
    ------
    • per-lane throughput and average wait
    • system-wide throughput rate (vehicles / minute)
    • banker's algorithm utilisation and deadlock events
    • rolling history for sparklines (last 60 samples)
    """

    HISTORY_LEN = 60    # data points stored in rolling window

    def __init__(self):
        self.frame        = 0
        self.sample_every = FPS   # one sample per second

        # Rolling history (for sparklines / trend lines)
        self.throughput_history = deque(maxlen=self.HISTORY_LEN)
        self.wait_history       = deque(maxlen=self.HISTORY_LEN)

        self._prev_throughput = 0   # snapshot for per-second delta

        # Banker's
        self.safe_decisions   = 0
        self.unsafe_decisions = 0
        self.deadlock_events  = 0

    # ── Called every frame ────────────────────────────────────────────────────

    def update(self, intersection, controller):
        self.frame += 1
        if self.frame % self.sample_every == 0:
            self._sample(intersection, controller)

    def _sample(self, intersection, controller):
        current_tp = intersection.total_throughput
        delta      = current_tp - self._prev_throughput
        self._prev_throughput = current_tp

        self.throughput_history.append(delta)
        self.wait_history.append(intersection.overall_avg_wait)

        banker = controller.banker_state
        self.deadlock_events = banker['deadlocks']

    # ── Accessors for dashboard ───────────────────────────────────────────────

    def throughput_per_minute(self, intersection) -> float:
        """Estimate vehicles/minute from the rolling window."""
        if not self.throughput_history:
            return 0.0
        rate_per_sec = sum(self.throughput_history) / len(self.throughput_history)
        return rate_per_sec * 60

    def efficiency_pct(self, intersection) -> float:
        """
        Rough efficiency: ratio of current throughput rate to theoretical max.
        Theoretical max ≈ 4 lanes × MAX_SPEED veh/s (very rough).
        """
        vpm = self.throughput_per_minute(intersection)
        theoretical = 4 * (60 / (SPAWN_INTERVAL / FPS))  # approx veh/min
        return min(100.0, vpm / max(theoretical, 1) * 100)
