# =============================================================================
# visualization/dashboard.py — Analytics dashboard overlay
# =============================================================================

import pygame
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *
from simulation.intersection import Intersection
from controller.signal_controller import SignalController
from analytics.traffic_stats import TrafficStats


class Dashboard:
    """
    Draws a professional analytics panel on the right side of the screen.

    Sections
    ────────
    • Header / title bar
    • System status (safe / unsafe, phase)
    • Banker's Algorithm state table
    • Per-lane vehicle & wait cards
    • Global metrics
    • Safe-sequence display
    • Green-phase progress bar
    """

    PAD   = 12
    FONT_S = None
    FONT_M = None
    FONT_L = None
    FONT_XS = None

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._init_fonts()
        self._panel_surf = pygame.Surface((DASH_W, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._anim_phase  = 0.0

    def _init_fonts(self):
        pygame.font.init()
        try:
            Dashboard.FONT_XS = pygame.font.SysFont('consolas', 11, bold=False)
            Dashboard.FONT_S  = pygame.font.SysFont('consolas', 13, bold=False)
            Dashboard.FONT_M  = pygame.font.SysFont('consolas', 15, bold=True)
            Dashboard.FONT_L  = pygame.font.SysFont('consolas', 18, bold=True)
        except Exception:
            Dashboard.FONT_XS = pygame.font.Font(None, 14)
            Dashboard.FONT_S  = pygame.font.Font(None, 16)
            Dashboard.FONT_M  = pygame.font.Font(None, 18)
            Dashboard.FONT_L  = pygame.font.Font(None, 22)

    # ── Main draw ─────────────────────────────────────────────────────────────

    def draw(self, intersection: Intersection,
             controller: SignalController,
             stats: TrafficStats,
             fps: float):

        self._anim_phase = (self._anim_phase + 0.05) % (2 * math.pi)

        surf = self._panel_surf
        surf.fill((0, 0, 0, 0))   # transparent

        # Background panel
        pygame.draw.rect(surf, (*DASH_BG, 230),
                         pygame.Rect(0, 0, DASH_W, SCREEN_HEIGHT))
        # Left border accent line
        pygame.draw.line(surf, PANEL_BORDER, (0, 0), (0, SCREEN_HEIGHT), 2)

        y = self.PAD
        y = self._draw_header(surf, y, fps)
        y = self._draw_status(surf, y, controller)
        y = self._draw_phase_bar(surf, y, controller)
        y = self._draw_bankers_table(surf, y, controller, intersection)
        y = self._draw_lane_cards(surf, y, intersection, controller)
        y = self._draw_global_metrics(surf, y, intersection, stats)
        y = self._draw_safe_sequence(surf, y, controller)
        y = self._draw_allocation_view(surf, y, controller)
        self._draw_footer(surf, fps)

        self.screen.blit(surf, (DASH_X, 0))

    # ── Sections ──────────────────────────────────────────────────────────────

    def _draw_header(self, surf, y, fps):
        # Title
        title = self.FONT_L.render("SMART TRAFFIC", True, ACCENT_BLUE)
        surf.blit(title, (self.PAD, y));  y += 22
        sub   = self.FONT_M.render("Banker's Algorithm", True, (130, 180, 220))
        surf.blit(sub,   (self.PAD, y));  y += 20
        # Divider
        pygame.draw.line(surf, PANEL_BORDER, (self.PAD, y), (DASH_W - self.PAD, y), 1)
        y += 8
        return y

    def _draw_status(self, surf, y, controller):
        safe   = controller.is_safe
        color  = SAFE_COLOR if safe else UNSAFE_COLOR
        label  = "  SAFE STATE " if safe else " UNSAFE STATE "

        # Pulsing background for safe/unsafe badge
        pulse = 0.7 + 0.3 * math.sin(self._anim_phase)
        badge_surf = pygame.Surface((DASH_W - self.PAD * 2, 26), pygame.SRCALPHA)
        pygame.draw.rect(badge_surf,
                         (*color, int(60 * pulse)),
                         pygame.Rect(0, 0, DASH_W - self.PAD * 2, 26),
                         border_radius=4)
        pygame.draw.rect(badge_surf, (*color, 180),
                         pygame.Rect(0, 0, DASH_W - self.PAD * 2, 26), 1,
                         border_radius=4)
        surf.blit(badge_surf, (self.PAD, y))

        txt = self.FONT_M.render(label, True, color)
        surf.blit(txt, (self.PAD + 8, y + 5))

        icon = "✓" if safe else "✗"
        icon_surf = self.FONT_L.render(icon, True, color)
        surf.blit(icon_surf, (DASH_W - self.PAD - 22, y + 3))

        y += 32

        # Phase label
        phase = self.FONT_S.render(controller.phase_label, True, (200, 210, 220))
        surf.blit(phase, (self.PAD, y));  y += 18
        return y

    def _draw_phase_bar(self, surf, y, controller):
        """Green-phase countdown progress bar."""
        bar_w  = DASH_W - self.PAD * 2
        bar_h  = 8
        prog   = controller.green_progress

        pygame.draw.rect(surf, (30, 40, 55),
                         pygame.Rect(self.PAD, y, bar_w, bar_h), border_radius=3)
        if prog > 0:
            fill = max(4, int(bar_w * prog))
            pygame.draw.rect(surf, SIG_GRN_ON,
                             pygame.Rect(self.PAD, y, fill, bar_h), border_radius=3)
        y += bar_h + 8

        # Divider
        pygame.draw.line(surf, (40, 55, 75),
                         (self.PAD, y), (DASH_W - self.PAD, y), 1)
        y += 6
        return y

    def _draw_bankers_table(self, surf, y, controller, intersection):
        """Display Allocation / Need / Available table."""
        hdr = self.FONT_M.render("Banker's State", True, ACCENT_BLUE)
        surf.blit(hdr, (self.PAD, y));  y += 20

        bs = controller.banker_state
        col_w = (DASH_W - self.PAD * 2) // 4

        # Column headers
        headers = ["Lane", "Alloc", "Max", "Need"]
        colors  = [(160,180,200), (255,160,80), (100,200,255), (255,200,80)]
        for i, (h, c) in enumerate(zip(headers, colors)):
            t = self.FONT_XS.render(h, True, c)
            surf.blit(t, (self.PAD + i * col_w, y))
        y += 14

        pygame.draw.line(surf, (50, 65, 85), (self.PAD, y), (DASH_W - self.PAD, y), 1)
        y += 4

        # Row per lane
        for name in LANE_NAMES:
            lane_color = LANE_COLOURS[name]
            alloc = bs['allocation'][name]
            mx    = bs['max_need'][name]
            need  = bs['need'][name]

            row_data = [name[:1].upper() + name[1:], str(alloc), str(mx), str(need)]
            row_cols = [lane_color, (255,160,80), (100,200,255), (255,200,80)]
            for i, (val, col) in enumerate(zip(row_data, row_cols)):
                t = self.FONT_XS.render(val, True, col)
                surf.blit(t, (self.PAD + i * col_w, y))
            y += 14

        # Available / Total
        avail_txt = self.FONT_XS.render(
            f"Available: {bs['available']} / {bs['total']}",
            True, (140, 200, 140))
        surf.blit(avail_txt, (self.PAD, y));  y += 14

        dl_txt = self.FONT_XS.render(
            f"Evaluations: {bs['evaluations']}  Deadlocks: {bs['deadlocks']}",
            True, UNSAFE_COLOR if bs['deadlocks'] > 0 else (120, 140, 160))
        surf.blit(dl_txt, (self.PAD, y));  y += 16

        pygame.draw.line(surf, (40, 55, 75), (self.PAD, y), (DASH_W - self.PAD, y), 1)
        y += 6
        return y

    def _draw_lane_cards(self, surf, y, intersection, controller):
        """One card per lane showing signal + vehicle count + wait time."""
        hdr = self.FONT_M.render("Lane Status", True, ACCENT_BLUE)
        surf.blit(hdr, (self.PAD, y));  y += 18

        for name in LANE_NAMES:
            lane       = intersection.get_lane(name)
            is_green   = (name == controller.active_lane and
                          controller.state == controller._S_GREEN)
            is_yellow  = (name == controller.active_lane and
                          controller.state == controller._S_YELLOW)
            sig_col    = (SIG_GRN_ON if is_green
                          else SIG_YEL_ON if is_yellow
                          else SIG_RED_ON)

            # Card background
            card_rect = pygame.Rect(self.PAD, y, DASH_W - self.PAD * 2, 38)
            bg_alpha  = 80 if is_green else 40
            bg_color  = LANE_COLOURS[name]
            card_surf = pygame.Surface((card_rect.w, card_rect.h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (*bg_color, bg_alpha),
                             pygame.Rect(0, 0, card_rect.w, card_rect.h),
                             border_radius=4)
            pygame.draw.rect(card_surf, (*bg_color, 140),
                             pygame.Rect(0, 0, card_rect.w, card_rect.h), 1,
                             border_radius=4)
            surf.blit(card_surf, (card_rect.x, card_rect.y))

            # Signal dot
            pygame.draw.circle(surf, sig_col,
                                (self.PAD + 10, y + 19), 6)

            # Lane name
            lname = self.FONT_M.render(name.upper(), True, LANE_COLOURS[name])
            surf.blit(lname, (self.PAD + 22, y + 4))

            # Vehicle count bar
            cnt     = lane.waiting_count
            bar_max = LANE_CAPACITY
            bar_w   = 70
            bar_x   = self.PAD + 95
            pygame.draw.rect(surf, (30, 40, 55),
                             pygame.Rect(bar_x, y + 8, bar_w, 8), border_radius=3)
            fill_w  = int(bar_w * cnt / max(bar_max, 1))
            if fill_w > 0:
                bar_color = (SAFE_COLOR if cnt < 5 else WARN_COLOR if cnt < 7
                             else UNSAFE_COLOR)
                pygame.draw.rect(surf, bar_color,
                                 pygame.Rect(bar_x, y + 8, fill_w, 8), border_radius=3)

            # Count text
            ct = self.FONT_S.render(f"{cnt} veh", True, WHITE)
            surf.blit(ct, (bar_x, y + 20))

            # Avg wait
            wt = self.FONT_XS.render(f"wait {lane.avg_wait:.1f}s", True, (160, 170, 180))
            surf.blit(wt, (bar_x + 55, y + 22))

            y += 44

        pygame.draw.line(surf, (40, 55, 75), (self.PAD, y), (DASH_W - self.PAD, y), 1)
        y += 6
        return y

    def _draw_global_metrics(self, surf, y, intersection, stats):
        hdr = self.FONT_M.render("System Metrics", True, ACCENT_BLUE)
        surf.blit(hdr, (self.PAD, y));  y += 18

        rows = [
            ("Total Processed", f"{intersection.total_throughput} veh"),
            ("Active Vehicles", f"{intersection.total_vehicles}"),
            ("Avg Wait Time",   f"{intersection.overall_avg_wait:.1f} s"),
            ("Throughput/min",  f"{stats.throughput_per_minute(intersection):.1f}"),
            ("Efficiency",      f"{stats.efficiency_pct(intersection):.0f} %"),
        ]
        for label, val in rows:
            lt = self.FONT_XS.render(label, True, (150, 165, 180))
            vt = self.FONT_S.render(val,   True, WHITE)
            surf.blit(lt, (self.PAD, y))
            surf.blit(vt, (DASH_W - self.PAD - vt.get_width(), y))
            y += 16

        pygame.draw.line(surf, (40, 55, 75), (self.PAD, y), (DASH_W - self.PAD, y), 1)
        y += 6
        return y

    def _draw_safe_sequence(self, surf, y, controller):
        hdr = self.FONT_M.render("Safe Sequence", True, ACCENT_BLUE)
        surf.blit(hdr, (self.PAD, y));  y += 16

        seq = controller.safe_sequence
        if seq:
            x_off = self.PAD
            for i, name in enumerate(seq):
                col   = LANE_COLOURS.get(name, WHITE)
                abbr  = name[:1].upper()
                badge = pygame.Surface((24, 18), pygame.SRCALPHA)
                pygame.draw.rect(badge, (*col, 80),
                                 pygame.Rect(0, 0, 24, 18), border_radius=3)
                pygame.draw.rect(badge, (*col, 180),
                                 pygame.Rect(0, 0, 24, 18), 1, border_radius=3)
                surf.blit(badge, (x_off, y))
                t = self.FONT_S.render(abbr, True, col)
                surf.blit(t, (x_off + 8, y + 2))
                x_off += 28
                if i < len(seq) - 1:
                    arrow = self.FONT_XS.render("→", True, (100, 120, 140))
                    surf.blit(arrow, (x_off, y + 3))
                    x_off += 14
            y += 24
        else:
            none_t = self.FONT_XS.render("(no sequence — no traffic)", True, (100, 110, 120))
            surf.blit(none_t, (self.PAD, y));  y += 16

        pygame.draw.line(surf, (40, 55, 75), (self.PAD, y), (DASH_W - self.PAD, y), 1)
        y += 6
        return y

    def _draw_allocation_view(self, surf, y, controller):
        """Visual bar showing Banker's resource allocation."""
        hdr = self.FONT_M.render("Resource Pool", True, ACCENT_BLUE)
        surf.blit(hdr, (self.PAD, y));  y += 16

        bs    = controller.banker_state
        total = bs['total']
        avail = bs['available']
        used  = total - avail

        bar_w = DASH_W - self.PAD * 2
        bar_h = 14
        pygame.draw.rect(surf, (30, 40, 55),
                         pygame.Rect(self.PAD, y, bar_w, bar_h), border_radius=4)
        if used > 0:
            fill = int(bar_w * used / total)
            pygame.draw.rect(surf, ACCENT_BLUE,
                             pygame.Rect(self.PAD, y, fill, bar_h), border_radius=4)
        pygame.draw.rect(surf, (80, 100, 130),
                         pygame.Rect(self.PAD, y, bar_w, bar_h), 1, border_radius=4)
        y += bar_h + 4

        label = self.FONT_XS.render(
            f"Used {used}/{total} units  |  Free {avail}", True, (140, 160, 180))
        surf.blit(label, (self.PAD, y));  y += 14
        return y

    def _draw_footer(self, surf, fps):
        y = SCREEN_HEIGHT - 22
        pygame.draw.line(surf, (40, 55, 75), (self.PAD, y - 4), (DASH_W - self.PAD, y - 4), 1)
        fps_t = self.FONT_XS.render(f"FPS: {fps:.0f}", True, (100, 120, 140))
        surf.blit(fps_t, (self.PAD, y))
        key_t = self.FONT_XS.render("[Q]uit [R]eset [S]pawn", True, (80, 100, 120))
        surf.blit(key_t, (self.PAD, y + 10 if y + 10 < SCREEN_HEIGHT else y))
