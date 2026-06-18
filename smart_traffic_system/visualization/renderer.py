# =============================================================================
# visualization/renderer.py — Layered scene rendering pipeline
# =============================================================================
#
# Render order (painter's algorithm):
#   1. Environment  (sky / grass)
#   2. Road surface & markings
#   3. Intersection box
#   4. Traffic signal structures
#   5. Vehicle shadows
#   6. Vehicle sprites
#   7. Overlay effects (signal glow)
#
# =============================================================================

import pygame
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *
from simulation.intersection import Intersection
from controller.signal_controller import SignalController


class Renderer:
    """Stateless drawing helpers; call draw() each frame."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w      = SCREEN_WIDTH
        self.h      = SCREEN_HEIGHT

        # Pre-build road surface (constant, drawn once per frame)
        self._build_road_surface()

        # Signal animation phase per lane (for pulse glow)
        self._glow_phase = {name: 0.0 for name in LANE_NAMES}

    # ── Pre-build helpers ─────────────────────────────────────────────────────

    def _build_road_surface(self):
        """Build a surface containing the static road geometry."""
        surf = pygame.Surface((self.w, self.h))

        # ── Grass background ─────────────────────────────────────────────────
        surf.fill(GRASS_COLOR)

        # Subtle grass grid texture
        for gx in range(0, self.w, 18):
            pygame.draw.line(surf, GRASS_DARK, (gx, 0), (gx, self.h), 1)
        for gy in range(0, self.h, 18):
            pygame.draw.line(surf, GRASS_DARK, (0, gy), (self.w, gy), 1)

        # ── Sidewalk squares at the four corners ────────────────────────────
        margin = HALF_ROAD + 18
        corners = [
            (0, 0, CENTER_X - margin, CENTER_Y - margin),
            (CENTER_X + margin, 0, self.w - CENTER_X - margin, CENTER_Y - margin),
            (0, CENTER_Y + margin, CENTER_X - margin, self.h - CENTER_Y - margin),
            (CENTER_X + margin, CENTER_Y + margin,
             self.w - CENTER_X - margin, self.h - CENTER_Y - margin),
        ]
        for cx, cy, cw, ch in corners:
            pygame.draw.rect(surf, SIDEWALK, pygame.Rect(cx, cy, cw, ch))

        # ── Curb border around each sidewalk ─────────────────────────────────
        for cx, cy, cw, ch in corners:
            pygame.draw.rect(surf, CURB, pygame.Rect(cx, cy, cw, ch), 3)

        # ── Horizontal road (E-W) ────────────────────────────────────────────
        road_h_rect = pygame.Rect(0, CENTER_Y - HALF_ROAD, DASH_X, HALF_ROAD * 2)
        pygame.draw.rect(surf, ROAD_COLOR, road_h_rect)

        # ── Vertical road (N-S) ──────────────────────────────────────────────
        road_v_rect = pygame.Rect(CENTER_X - HALF_ROAD, 0, HALF_ROAD * 2, self.h)
        pygame.draw.rect(surf, ROAD_COLOR, road_v_rect)

        # ── Road edge kerbs ──────────────────────────────────────────────────
        kerb_w = 3
        # Horizontal road kerbs (top & bottom)
        pygame.draw.rect(surf, CURB,
                         pygame.Rect(0, CENTER_Y - HALF_ROAD, DASH_X, kerb_w))
        pygame.draw.rect(surf, CURB,
                         pygame.Rect(0, CENTER_Y + HALF_ROAD - kerb_w, DASH_X, kerb_w))
        # Vertical road kerbs (left & right)
        pygame.draw.rect(surf, CURB,
                         pygame.Rect(CENTER_X - HALF_ROAD, 0, kerb_w, self.h))
        pygame.draw.rect(surf, CURB,
                         pygame.Rect(CENTER_X + HALF_ROAD - kerb_w, 0, kerb_w, self.h))

        # ── Centre-line dashes (yellow) ───────────────────────────────────────
        # Horizontal centre line
        for x in range(0, INTER_LEFT, 30):
            pygame.draw.rect(surf, MARKING_YELL, pygame.Rect(x, CENTER_Y - 1, 18, 2))
        for x in range(INTER_RIGHT, DASH_X, 30):
            pygame.draw.rect(surf, MARKING_YELL, pygame.Rect(x, CENTER_Y - 1, 18, 2))
        # Vertical centre line
        for y in range(0, INTER_TOP, 30):
            pygame.draw.rect(surf, MARKING_YELL, pygame.Rect(CENTER_X - 1, y, 2, 18))
        for y in range(INTER_BOTTOM, self.h, 30):
            pygame.draw.rect(surf, MARKING_YELL, pygame.Rect(CENTER_X - 1, y, 2, 18))

        # ── Lane markings (white dashes on each side) ─────────────────────────
        # NS road – left of centre
        for y in range(10, INTER_TOP, 30):
            pygame.draw.rect(surf, MARKING_WHITE,
                             pygame.Rect(CENTER_X - HALF_ROAD + 6, y, 3, 18))
        for y in range(INTER_BOTTOM + 10, self.h, 30):
            pygame.draw.rect(surf, MARKING_WHITE,
                             pygame.Rect(CENTER_X - HALF_ROAD + 6, y, 3, 18))
        # EW road – above centre
        for x in range(10, INTER_LEFT, 30):
            pygame.draw.rect(surf, MARKING_WHITE,
                             pygame.Rect(x, CENTER_Y - HALF_ROAD + 6, 18, 3))
        for x in range(INTER_RIGHT + 10, DASH_X, 30):
            pygame.draw.rect(surf, MARKING_WHITE,
                             pygame.Rect(x, CENTER_Y - HALF_ROAD + 6, 18, 3))

        # ── Stop lines ────────────────────────────────────────────────────────
        line_len = HALF_ROAD - 4
        # North approach
        pygame.draw.rect(surf, MARKING_WHITE,
                         pygame.Rect(CENTER_X, STOP_N, HALF_ROAD - 4, 3))
        # South approach
        pygame.draw.rect(surf, MARKING_WHITE,
                         pygame.Rect(CENTER_X - HALF_ROAD + 4, STOP_S, HALF_ROAD - 4, 3))
        # East approach
        pygame.draw.rect(surf, MARKING_WHITE,
                         pygame.Rect(STOP_E, CENTER_Y - HALF_ROAD + 4, 3, HALF_ROAD - 4))
        # West approach
        pygame.draw.rect(surf, MARKING_WHITE,
                         pygame.Rect(STOP_W, CENTER_Y, 3, HALF_ROAD - 4))

        self._road_surf = surf

    # ── Main draw entry point ─────────────────────────────────────────────────

    def draw(self, intersection: Intersection, controller: SignalController):
        # Layer 1 + 2: Environment & roads (pre-built)
        self.screen.blit(self._road_surf, (0, 0))

        # Layer 3: Intersection box highlight
        self._draw_intersection_box()

        # Layer 4: Signal structures
        self._draw_signals(intersection)

        # Layer 5: Vehicle shadows
        for lane in intersection.lanes.values():
            for v in lane.vehicles:
                v.draw_shadow(self.screen)

        # Layer 6: Vehicle sprites
        for lane in intersection.lanes.values():
            for v in lane.vehicles:
                v.draw(self.screen)

        # Layer 7: Signal glow overlay
        self._draw_signal_glow(intersection)

    # ── Intersection box ──────────────────────────────────────────────────────

    def _draw_intersection_box(self):
        box = pygame.Rect(INTER_LEFT, INTER_TOP,
                          INTER_RIGHT - INTER_LEFT, INTER_BOTTOM - INTER_TOP)
        pygame.draw.rect(self.screen, ROAD_DARK, box)
        # Subtle grid lines inside intersection
        mid_x = CENTER_X
        mid_y = CENTER_Y
        pygame.draw.line(self.screen, (60, 60, 64),
                         (mid_x, INTER_TOP), (mid_x, INTER_BOTTOM), 1)
        pygame.draw.line(self.screen, (60, 60, 64),
                         (INTER_LEFT, mid_y), (INTER_RIGHT, mid_y), 1)

    # ── Traffic signals ───────────────────────────────────────────────────────

    def _signal_positions(self) -> dict:
        """Return (pole_base_x, pole_base_y, face_towards) per lane."""
        return {
            'north': (INTER_LEFT  - 14, INTER_TOP    - 10, 'east'),
            'south': (INTER_RIGHT + 14, INTER_BOTTOM + 10, 'west'),
            'east':  (INTER_RIGHT + 10, INTER_TOP    - 14, 'south'),
            'west':  (INTER_LEFT  - 10, INTER_BOTTOM + 14, 'north'),
        }

    def _draw_signals(self, intersection: Intersection):
        positions = self._signal_positions()
        for name, lane in intersection.lanes.items():
            px, py, _ = positions[name]
            state      = lane.signal
            self._draw_signal_unit(px, py, state, name)

    def _draw_signal_unit(self, cx: int, cy: int, state: str, name: str):
        """Draw a traffic light at (cx, cy)."""
        # Pole
        pole_h = 36
        pygame.draw.rect(self.screen, SIG_POLE,
                         pygame.Rect(cx - 3, cy, 6, pole_h))
        # Housing box
        box_w, box_h = 22, 58
        bx = cx - box_w // 2
        by = cy - box_h - 2
        pygame.draw.rect(self.screen, SIG_HOUSING,
                         pygame.Rect(bx, by, box_w, box_h), border_radius=4)
        pygame.draw.rect(self.screen, (60, 60, 60),
                         pygame.Rect(bx, by, box_w, box_h), 1, border_radius=4)

        # Lights
        r_centre = (cx, by + 10)
        y_centre = (cx, by + 28)
        g_centre = (cx, by + 46)
        radius   = 7

        r_color = SIG_RED_ON  if state == 'red'    else SIG_OFF
        y_color = SIG_YEL_ON  if state == 'yellow' else SIG_OFF
        g_color = SIG_GRN_ON  if state == 'green'  else SIG_OFF

        pygame.draw.circle(self.screen, r_color, r_centre, radius)
        pygame.draw.circle(self.screen, y_color, y_centre, radius)
        pygame.draw.circle(self.screen, g_color, g_centre, radius)

        # Lens rim
        pygame.draw.circle(self.screen, (80, 80, 80), r_centre, radius, 1)
        pygame.draw.circle(self.screen, (80, 80, 80), y_centre, radius, 1)
        pygame.draw.circle(self.screen, (80, 80, 80), g_centre, radius, 1)

    def _draw_signal_glow(self, intersection: Intersection):
        """Animated halo around the active light."""
        glow_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        positions  = self._signal_positions()

        for name, lane in intersection.lanes.items():
            state = lane.signal
            if state == 'red':
                color_rgb = SIG_RED_ON
                offset    = (0, -44)    # red light is top of housing
            elif state == 'yellow':
                color_rgb = SIG_YEL_ON
                offset    = (0, -28)
            elif state == 'green':
                color_rgb = SIG_GRN_ON
                offset    = (0, -12)
            else:
                continue

            self._glow_phase[name] = (self._glow_phase[name] + 0.08) % (2 * math.pi)
            pulse = 0.55 + 0.45 * math.sin(self._glow_phase[name])

            px, py, _ = positions[name]
            # Housing by position
            by = py - 58 - 2
            cx = px
            if state == 'red':
                lcy = by + 10
            elif state == 'yellow':
                lcy = by + 28
            else:
                lcy = by + 46

            r, g, b = color_rgb
            alpha   = int(80 * pulse)
            for radius in (18, 26):
                pygame.draw.circle(glow_surf, (r, g, b, alpha // 2 if radius == 26 else alpha),
                                   (cx, lcy), radius)

        self.screen.blit(glow_surf, (0, 0))
