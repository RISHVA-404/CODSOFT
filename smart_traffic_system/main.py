#!/usr/bin/env python3
# =============================================================================
# main.py — Smart Traffic Signal Control System
#           Deadlock Avoidance via Banker's Algorithm
# =============================================================================
#
#  Run:  python main.py
#  Requires:  pip install pygame
#
#  Controls
#  --------
#  Q / Escape  — quit
#  R           — reset simulation
#  S           — manually spawn one vehicle on each lane
#  1-4         — force green on lane N/S/E/W respectively (debug)
#  F           — toggle FPS display
#
# =============================================================================

import sys
import os

# Ensure sub-packages are importable regardless of working directory
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
import time

from config.settings          import *
from simulation.intersection  import Intersection
from controller.signal_controller import SignalController
from visualization.renderer   import Renderer
from visualization.dashboard  import Dashboard
from analytics.traffic_stats  import TrafficStats


# =============================================================================
#  Simulation wrapper – groups all subsystems for easy reset
# =============================================================================

class Simulation:
    def __init__(self):
        self.intersection = Intersection()
        self.controller   = SignalController(self.intersection)
        self.stats        = TrafficStats()

    def update(self):
        self.intersection.update()
        self.controller.update()
        self.stats.update(self.intersection, self.controller)

    def force_spawn(self):
        """Manually spawn one vehicle on every lane that has room."""
        for lane in self.intersection.lanes.values():
            if lane.can_spawn():
                lane.spawn_vehicle()

    def force_green(self, lane_id: str):
        """Debug: immediately switch green to the requested lane."""
        if lane_id in self.intersection.lanes:
            self.controller._set_all_red()
            self.controller.active_lane  = lane_id
            self.controller.green_frames = FRAMES_PER_UNIT * 3
            self.controller.state        = self.controller._S_GREEN
            self.intersection.set_signal(lane_id, 'green')


# =============================================================================
#  Main entry point
# =============================================================================

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    flags  = pygame.DOUBLEBUF | pygame.HWSURFACE
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    clock  = pygame.time.Clock()

    renderer  = Renderer(screen)
    dashboard = Dashboard(screen)
    sim       = Simulation()

    # Pre-populate each lane with 2 vehicles so the demo starts lively
    for _ in range(2):
        sim.force_spawn()
        # tick a bit so vehicles space out
        for __ in range(40):
            sim.intersection.update()

    show_fps   = True
    running    = True
    frame_count = 0

    print("=" * 60)
    print("  Smart Traffic Signal Control System")
    print("  Deadlock Avoidance — Banker's Algorithm")
    print("=" * 60)
    print(f"  Resources (green_time_units): {GREEN_UNITS_TOTAL}")
    print(f"  Lanes: {', '.join(LANE_NAMES)}")
    print(f"  Decision interval: every {DECISION_INTERVAL} frames")
    print()
    print("  Press Q/Escape to quit | R to reset | S to spawn")
    print()

    while running:
        dt  = clock.tick(FPS)
        fps = clock.get_fps()
        frame_count += 1

        # ── Event handling ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                key = event.key

                if key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

                elif key == pygame.K_r:
                    sim = Simulation()
                    print("[RESET] Simulation restarted")

                elif key == pygame.K_s:
                    sim.force_spawn()
                    print("[SPAWN] Manual spawn triggered")

                elif key == pygame.K_f:
                    show_fps = not show_fps

                elif key == pygame.K_1:
                    sim.force_green('north')
                    print("[DEBUG] Forced GREEN → North")
                elif key == pygame.K_2:
                    sim.force_green('south')
                    print("[DEBUG] Forced GREEN → South")
                elif key == pygame.K_3:
                    sim.force_green('east')
                    print("[DEBUG] Forced GREEN → East")
                elif key == pygame.K_4:
                    sim.force_green('west')
                    print("[DEBUG] Forced GREEN → West")

        # ── Simulation step ───────────────────────────────────────────────────
        sim.update()

        # ── Render ────────────────────────────────────────────────────────────
        renderer.draw(sim.intersection, sim.controller)
        dashboard.draw(sim.intersection, sim.controller, sim.stats, fps)

        # Simulation area border
        pygame.draw.rect(screen, (30, 45, 65),
                         pygame.Rect(0, 0, DASH_X, SCREEN_HEIGHT), 1)

        pygame.display.flip()

        # Console heartbeat every 5 seconds
        if frame_count % (FPS * 5) == 0:
            bs = sim.controller.banker_state
            wc = sim.intersection.waiting_counts()
            print(f"[{frame_count//FPS:>4}s] "
                  f"Throughput: {sim.intersection.total_throughput:>4}  "
                  f"Active: {sim.intersection.total_vehicles}  "
                  f"Safe: {sim.controller.is_safe}  "
                  f"Deadlocks: {bs['deadlocks']}  "
                  f"Queue: {dict(wc)}")

    pygame.quit()
    print("\n[EXIT] Simulation ended.")
    print(f"  Total vehicles processed : {sim.intersection.total_throughput}")
    print(f"  Avg wait time            : {sim.intersection.overall_avg_wait:.2f} s")
    print(f"  Deadlock events          : {sim.controller.banker_state['deadlocks']}")
    sys.exit(0)


if __name__ == '__main__':
    main()
