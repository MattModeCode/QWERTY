# Game configuration
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TITLE = "QWERTY"
FPS = 60

# Theme Colors (RGB)
SLATE_NAVY = (15, 23, 42)
NEON_BLUE = (56, 189, 248)
DARK_SLATE = (30, 41, 59)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

# Keys for 8 lanes (asdfjkl;)
LANE_KEYS = ['a', 's', 'd', 'f', 'j', 'k', 'l', ';']
LANE_LETTERS = ['A', 'S', 'D', 'F', 'J', 'K', 'L', ';']

# Lane configuration
NUM_LANES = 8
LANE_WIDTH = 80
LANE_SPACING = 8
PLAYFIELD_WIDTH = NUM_LANES * (LANE_WIDTH + LANE_SPACING)
PLAYFIELD_X = (SCREEN_WIDTH - PLAYFIELD_WIDTH) // 2

# Note configuration (base values - modified by difficulty)
NOTE_RADIUS = 30
BASE_NOTE_SPEED = 200  # pixels per second (will scale with difficulty)
HIT_LINE_Y = SCREEN_HEIGHT - 100
HIT_WINDOW = 60  # pixels tolerance for hit detection

# Scoring
BASE_SCORE = 300
COMBO_MULTIPLIER = 0.1  # Each combo adds 10% bonus

# Health
MAX_HEALTH = 100
HEALTH_DRAIN_PER_MISS = 20
HEALTH_GAIN_PER_HIT = 2

# UI Configuration
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 45
BUTTON_RADIUS = 4

# Font sizes
FONT_TITLE = 100
FONT_LARGE = 48
FONT_MEDIUM = 24
FONT_SMALL = 16

# Map file reference for gameplay
current_map_file = None
