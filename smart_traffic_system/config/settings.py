# =============================================================================
# Smart Traffic Signal Control System — Configuration & Constants
# =============================================================================

# ── Display ───────────────────────────────────────────────────────────────────
SCREEN_WIDTH   = 1280
SCREEN_HEIGHT  = 720
FPS            = 60
TITLE          = "Smart Traffic Signal Control — Banker's Algorithm"

# ── Simulation area (dashboard sits on the right) ────────────────────────────
DASH_X         = 960          # dashboard starts at this x
DASH_W         = SCREEN_WIDTH - DASH_X   # 320 px dashboard width

# ── Colour Palette ───────────────────────────────────────────────────────────
BLACK         = (0,   0,   0)
WHITE         = (255, 255, 255)
ROAD_COLOR    = (38,  40,  46)
ROAD_DARK     = (28,  30,  34)
MARKING_WHITE = (220, 220, 220)
MARKING_YELL  = (240, 190, 20)
GRASS_COLOR   = (28,  76,  28)
GRASS_DARK    = (20,  60,  20)
SIDEWALK      = (155, 148, 138)
CURB          = (120, 114, 106)

SIG_RED_ON    = (230, 30,  30)
SIG_YEL_ON    = (255, 185, 0)
SIG_GRN_ON    = (30,  220, 55)
SIG_OFF       = (45,  45,  45)
SIG_HOUSING   = (22,  22,  22)
SIG_POLE      = (55,  55,  55)

DASH_BG       = (10,  16,  26)
PANEL_BG      = (16,  26,  42)
PANEL_BORDER  = (0,   140, 255)
ACCENT_BLUE   = (0,   160, 255)
SAFE_COLOR    = (40,  210, 90)
UNSAFE_COLOR  = (220, 55,  55)
WARN_COLOR    = (255, 170, 0)

# ── Intersection Geometry ─────────────────────────────────────────────────────
CENTER_X    = 480             # centre of simulation area (half of 960)
CENTER_Y    = 360
HALF_ROAD   = 62              # half of total road width → road = 124 px wide

INTER_LEFT   = CENTER_X - HALF_ROAD
INTER_RIGHT  = CENTER_X + HALF_ROAD
INTER_TOP    = CENTER_Y - HALF_ROAD
INTER_BOTTOM = CENTER_Y + HALF_ROAD

# Lane x/y offsets from centre-line
LANE_OFFSET = 20

# Exact lane travel lines
NORTH_LANE_X = CENTER_X + LANE_OFFSET    # N-approach (going south) right side
SOUTH_LANE_X = CENTER_X - LANE_OFFSET    # S-approach (going north) right side
EAST_LANE_Y  = CENTER_Y - LANE_OFFSET    # E-approach (going west)  upper lane
WEST_LANE_Y  = CENTER_Y + LANE_OFFSET    # W-approach (going east)  lower lane

# Stop-line positions
STOP_N = INTER_TOP    - 4
STOP_S = INTER_BOTTOM + 4
STOP_E = INTER_RIGHT  + 4
STOP_W = INTER_LEFT   - 4

# ── Vehicle Dimensions ───────────────────────────────────────────────────────
VEH_NS_W = 26    # North/South vehicle width
VEH_NS_H = 42    # North/South vehicle height
VEH_EW_W = 42    # East/West vehicle width
VEH_EW_H = 26    # East/West vehicle height

# ── Vehicle Physics ──────────────────────────────────────────────────────────
MAX_SPEED     = 2.6
ACCELERATION  = 0.11
DECELERATION  = 0.22
SAFE_DISTANCE = 58   # min gap (front of follower to rear of leader), px

# ── Spawn ────────────────────────────────────────────────────────────────────
SPAWN_INTERVAL = 95      # frames between auto-spawns per lane
LANE_CAPACITY  = 8       # max queued vehicles per lane
VEHICLE_COLORS = [
    (210, 45,  45),    # red
    (45,  100, 215),   # blue
    (45,  175, 60),    # green
    (215, 175, 30),    # yellow
    (175, 70,  185),   # purple
    (220, 115, 30),    # orange
    (60,  195, 205),   # cyan
    (210, 210, 215),   # silver
    (120, 80,  50),    # brown
    (240, 120, 170),   # pink
]

# ── Banker's Algorithm Parameters ────────────────────────────────────────────
N_LANES           = 4
GREEN_UNITS_TOTAL = 16    # total pool of green-time units
MAX_UNITS_PER_LANE = 4    # max a single lane can request

# ── Signal Timing ─────────────────────────────────────────────────────────────
FRAMES_PER_UNIT   = 50    # frames one green-time-unit lasts
YELLOW_FRAMES     = 75    # yellow transition duration
DECISION_INTERVAL = 160   # idle frames before next evaluation

LANE_NAMES    = ['north', 'south', 'east', 'west']
LANE_COLOURS  = {
    'north': (255, 80,  80),
    'south': (80,  180, 255),
    'east':  (80,  230, 130),
    'west':  (255, 200, 60),
}
