# =============================================================================
# simulation/vehicle.py — Vehicle entity with physics & drawing
# =============================================================================

import pygame
import random
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *


class Vehicle:
    """
    Represents one vehicle in the simulation.

    Each vehicle knows its direction, lane position, target speed,
    and draws itself as a stylised top-down car sprite using Pygame
    primitives (no external assets required).
    """

    _id_counter = 0

    def __init__(self, x: float, y: float, direction: str, color=None):
        Vehicle._id_counter += 1
        self.vid        = Vehicle._id_counter
        self.x          = float(x)
        self.y          = float(y)
        self.direction  = direction          # 'north','south','east','west'
        self.speed      = 0.0
        self.target_speed = MAX_SPEED
        self.color      = color or random.choice(VEHICLE_COLORS)
        self.wait_time  = 0                  # frames spent at speed < 0.3
        self.passed     = False              # crossed intersection?
        self.alpha      = 255               # for fade-in

        # Derived geometry
        if direction in ('north', 'south'):
            self.w, self.h = VEH_NS_W, VEH_NS_H
        else:
            self.w, self.h = VEH_EW_W, VEH_EW_H

        # Roof / windscreen tint derived from body colour
        r, g, b = self.color
        self.roof_color  = (min(r+40,255), min(g+40,255), min(b+40,255))
        self.glass_color = (min(r+80,255), min(g+80,255), min(b+80,255), 160)
        self.dark_color  = (max(r-60,0),   max(g-60,0),   max(b-60,0))

    # ── Physics ──────────────────────────────────────────────────────────────

    def accelerate(self):
        self.speed = min(self.speed + ACCELERATION, self.target_speed)

    def decelerate(self):
        self.speed = max(self.speed - DECELERATION, 0.0)

    def stop(self):
        self.decelerate()

    def move(self):
        """Apply current speed in the vehicle's direction."""
        if self.direction == 'south':
            self.y += self.speed
        elif self.direction == 'north':
            self.y -= self.speed
        elif self.direction == 'east':
            self.x += self.speed
        elif self.direction == 'west':
            self.x -= self.speed

    def is_off_screen(self) -> bool:
        margin = 100
        return (self.x < -margin or self.x > SCREEN_WIDTH + margin or
                self.y < -margin or self.y > SCREEN_HEIGHT + margin)

    def tick_wait(self):
        if self.speed < 0.3:
            self.wait_time += 1

    # ── Rendering ────────────────────────────────────────────────────────────

    def _rect(self) -> pygame.Rect:
        """Bounding rect centred on (x, y)."""
        return pygame.Rect(self.x - self.w / 2, self.y - self.h / 2, self.w, self.h)

    def draw_shadow(self, surface: pygame.Surface):
        """Draw a subtle drop shadow beneath the vehicle."""
        sx = int(self.x + 4)
        sy = int(self.y + 5)
        shadow_surf = pygame.Surface((self.w + 4, self.h + 4), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 70),
                            (0, 0, self.w + 4, self.h + 4))
        surface.blit(shadow_surf, (sx - (self.w + 4) // 2, sy - (self.h + 4) // 2))

    def draw(self, surface: pygame.Surface):
        """Draw the vehicle as a detailed top-down car sprite."""
        x, y   = int(self.x), int(self.y)
        hw, hh = self.w // 2, self.h // 2

        # ── Body ─────────────────────────────────────────────────────────────
        body_rect = pygame.Rect(x - hw, y - hh, self.w, self.h)
        pygame.draw.rect(surface, self.color, body_rect, border_radius=5)

        # ── Roof panel (slightly inset, brighter) ────────────────────────────
        roof_inset = 4
        if self.direction in ('north', 'south'):
            roof_rect = pygame.Rect(x - hw + roof_inset,
                                    y - hh + self.h // 5,
                                    self.w - roof_inset * 2,
                                    self.h * 3 // 5)
        else:
            roof_rect = pygame.Rect(x - hw + self.w // 5,
                                    y - hh + roof_inset,
                                    self.w * 3 // 5,
                                    self.h - roof_inset * 2)
        pygame.draw.rect(surface, self.roof_color, roof_rect, border_radius=3)

        # ── Windscreen (semi-transparent glass look) ─────────────────────────
        glass_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        r, g, b = self.glass_color[:3]
        alpha   = self.glass_color[3] if len(self.glass_color) == 4 else 160

        if self.direction == 'south':
            g_rect = pygame.Rect(roof_inset + 2, self.h // 5,
                                 self.w - (roof_inset + 2) * 2, self.h // 4)
        elif self.direction == 'north':
            g_rect = pygame.Rect(roof_inset + 2, self.h * 8 // 15,
                                 self.w - (roof_inset + 2) * 2, self.h // 4)
        elif self.direction == 'east':
            g_rect = pygame.Rect(self.w // 5, roof_inset + 2,
                                 self.w // 4, self.h - (roof_inset + 2) * 2)
        else:   # west
            g_rect = pygame.Rect(self.w * 8 // 15, roof_inset + 2,
                                 self.w // 4, self.h - (roof_inset + 2) * 2)

        pygame.draw.rect(glass_surf, (r, g, b, alpha), g_rect, border_radius=2)
        surface.blit(glass_surf, (x - hw, y - hh))

        # ── Wheels (4 dark rects at corners) ─────────────────────────────────
        ww, wh = 6, 9  # wheel dims for N/S
        if self.direction in ('east', 'west'):
            ww, wh = 9, 6
        offsets = [
            (-hw + 1,       -hh + 1),
            ( hw - ww - 1,  -hh + 1),
            (-hw + 1,        hh - wh - 1),
            ( hw - ww - 1,   hh - wh - 1),
        ]
        for ox, oy in offsets:
            pygame.draw.rect(surface, (20, 20, 20),
                             pygame.Rect(x + ox, y + oy, ww, wh), border_radius=2)

        # ── Outline ───────────────────────────────────────────────────────────
        pygame.draw.rect(surface, self.dark_color, body_rect, width=1, border_radius=5)

        # ── Headlights / tail-lights tiny dots ───────────────────────────────
        hl_color = (255, 255, 180)
        tl_color = (200, 20, 20)
        if self.direction == 'south':
            # headlights at bottom
            pygame.draw.circle(surface, hl_color, (x - hw + 4, y + hh - 3), 2)
            pygame.draw.circle(surface, hl_color, (x + hw - 5, y + hh - 3), 2)
            pygame.draw.circle(surface, tl_color, (x - hw + 4, y - hh + 3), 2)
            pygame.draw.circle(surface, tl_color, (x + hw - 5, y - hh + 3), 2)
        elif self.direction == 'north':
            pygame.draw.circle(surface, hl_color, (x - hw + 4, y - hh + 3), 2)
            pygame.draw.circle(surface, hl_color, (x + hw - 5, y - hh + 3), 2)
            pygame.draw.circle(surface, tl_color, (x - hw + 4, y + hh - 3), 2)
            pygame.draw.circle(surface, tl_color, (x + hw - 5, y + hh - 3), 2)
        elif self.direction == 'east':
            pygame.draw.circle(surface, hl_color, (x + hw - 3, y - hh + 4), 2)
            pygame.draw.circle(surface, hl_color, (x + hw - 3, y + hh - 5), 2)
            pygame.draw.circle(surface, tl_color, (x - hw + 3, y - hh + 4), 2)
            pygame.draw.circle(surface, tl_color, (x - hw + 3, y + hh - 5), 2)
        else:  # west
            pygame.draw.circle(surface, hl_color, (x - hw + 3, y - hh + 4), 2)
            pygame.draw.circle(surface, hl_color, (x - hw + 3, y + hh - 5), 2)
            pygame.draw.circle(surface, tl_color, (x + hw - 3, y - hh + 4), 2)
            pygame.draw.circle(surface, tl_color, (x + hw - 3, y + hh - 5), 2)
