# Smart Traffic Signal Control System
### Deadlock Avoidance via Banker's Algorithm

A professional Python + Pygame traffic intersection simulator demonstrating
real-time deadlock avoidance using the **Banker's Algorithm** as the signal
decision engine.

---

## Quick Start

```bash
pip install pygame
cd smart_traffic_system
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| Q / Escape | Quit |
| R | Reset simulation |
| S | Manually spawn vehicles |
| 1 | Force green → North lane |
| 2 | Force green → South lane |
| 3 | Force green → East lane |
| 4 | Force green → West lane |
| F | Toggle FPS overlay |

---

## Project Architecture

```
smart_traffic_system/
├── main.py                          ← Entry point & game loop
├── config/
│   └── settings.py                  ← All constants & tuning parameters
├── simulation/
│   ├── vehicle.py                   ← Vehicle entity (physics + sprite drawing)
│   ├── lane.py                      ← Lane queue management & stop-line logic
│   └── intersection.py              ← 4-way intersection orchestrator
├── algorithm/
│   └── bankers_algorithm.py         ← Banker's Algorithm implementation
├── controller/
│   └── signal_controller.py         ← Signal state machine (uses Banker's)
├── visualization/
│   ├── renderer.py                  ← Layered scene renderer (Pygame)
│   └── dashboard.py                 ← Analytics dashboard overlay
└── analytics/
    └── traffic_stats.py             ← Metrics aggregation & rolling history
```

---

## Banker's Algorithm — Traffic Domain Mapping

| Algorithm Concept | Traffic Concept |
|-------------------|-----------------|
| Process           | Traffic lane (N/S/E/W) |
| Resource type     | Green-signal time units |
| Allocation[i]     | Units currently held by lane i |
| Max[i]            | Max units lane i could need (∝ vehicle count) |
| Need[i]           | Max[i] − Allocation[i] |
| Available         | Total pool − Σ Allocation |

### Decision cycle

1. **IDLE** — wait `DECISION_INTERVAL` frames between cycles.
2. **EVALUATE** — call `BankersAlgorithm.find_safe_allocation()`:
   - Update `max_need` from current queue depths.
   - For each candidate lane (sorted by queue length, descending):
     - Tentatively allocate `min(queue_len, MAX_UNITS_PER_LANE)` units.
     - Run the Banker's Safety Algorithm on the tentative state.
     - If safe → **select this lane**.
   - If no safe allocation exists → flag `UNSAFE`, serve busiest lane to break deadlock.
3. **GREEN** — signal the chosen lane green; vehicles flow for `units × FRAMES_PER_UNIT` frames.
4. **YELLOW** — 75-frame transition.
5. Return to **IDLE**.

---

## Render Pipeline (Painter's Algorithm)

1. Environment layer (grass, sidewalks, curb corners)
2. Road surface & lane markings
3. Intersection box
4. Traffic signal structures
5. Vehicle shadows (alpha-blended ellipses)
6. Vehicle sprites (procedurally drawn top-down cars)
7. Signal glow overlay (pulsing halos)
8. Dashboard analytics panel

---

## Tuning Parameters (`config/settings.py`)

| Parameter | Default | Effect |
|-----------|---------|--------|
| `GREEN_UNITS_TOTAL` | 16 | Total resource pool size |
| `MAX_UNITS_PER_LANE` | 4 | Max green-time a single lane can hold |
| `FRAMES_PER_UNIT` | 50 | How long one green-time unit lasts |
| `DECISION_INTERVAL` | 160 | Frames of idle time between evaluations |
| `YELLOW_FRAMES` | 75 | Duration of yellow transition |
| `SPAWN_INTERVAL` | 95 | Frames between automatic vehicle spawns |
| `LANE_CAPACITY` | 8 | Max vehicles queued per lane |
| `MAX_SPEED` | 2.6 | Vehicle top speed (pixels/frame) |
| `SAFE_DISTANCE` | 58 | Minimum gap between vehicles |

---

## Extensibility

The modular design supports future features:

- **Multiple intersections** — Add `Intersection` instances and extend the controller to manage cross-intersection coordination.
- **AI traffic prediction** — Replace `update_max_needs()` with a model that predicts future queue depths.
- **Emergency vehicle priority** — Add a priority flag to `Lane`; the controller checks it before running Banker's.
- **Smart city network** — Connect multiple `SignalController` instances via a shared resource manager.
