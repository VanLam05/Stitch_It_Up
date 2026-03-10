# ============================================================
# STITCH IT UP - Constants & Configuration
# Game: 2D Puzzle-Platformer
# ============================================================

import pygame

# Window Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Stitch It Up"

# Colors (Fabric/Sewing Theme)
COLORS = {
    'background': (45, 42, 50),       # Dark fabric
    'platform': (139, 90, 43),         # Wooden spool brown
    'platform_outline': (101, 67, 33), # Darker brown
    'player': (255, 182, 193),         # Light pink (like a pin cushion)
    'player_outline': (199, 21, 133),  # Medium violet red
    'needle': (192, 192, 192),         # Silver
    'needle_tip': (255, 255, 255),     # White tip
    'thread': (220, 20, 60),           # Crimson red thread
    'thread_glow': (255, 99, 71),      # Tomato glow
    'stitch_point': (255, 215, 0),     # Gold (anchor points)
    'stitch_point_final': (0, 255, 127), # Spring green (goal)
    'hazard_scissors': (169, 169, 169), # Dark gray scissors
    'hazard_flame': (255, 69, 0),      # Red-orange flame
    'enemy_body': (131, 92, 173),      # Monster body
    'enemy_outline': (84, 57, 116),    # Monster outline
    'enemy_eye': (255, 245, 245),      # Monster eyes
    'button_inactive': (128, 128, 128), # Gray
    'button_active': (50, 205, 50),    # Lime green
    'ui_bg': (30, 30, 40),             # Dark UI
    'ui_text': (255, 255, 255),        # White text
    'thread_meter_bg': (60, 60, 80),   # Thread meter background
    'thread_meter_fill': (220, 20, 60), # Thread meter fill
    'bridge': (255, 182, 193, 150),    # Semi-transparent pink bridge
    'trampoline': (147, 112, 219),     # Medium purple
    'void': (20, 15, 25),              # Deep void color
}

# Physics
GRAVITY = 0.5
MAX_FALL_SPEED = 15
PLAYER_SPEED = 4.5
PLAYER_JUMP_FORCE = -10
FRICTION = 0.85

# Needle/Thread Mechanics
NEEDLE_SPEED = 25
NEEDLE_MAX_DISTANCE = 400
THREAD_WIDTH = 3
THREAD_GLOW_WIDTH = 6
BRIDGE_BOUNCE_FORCE = -15
TRAMPOLINE_BOUNCE_FORCE = -20
GRAPPLE_SWING_SPEED = 0.15
PULL_FORCE = 0.3

# Thread Resource
DEFAULT_THREAD_LENGTH = 800
THREAD_CONSUMPTION_RATE = 1.0  # pixels per pixel traveled
THREAD_RECOVERY_RATE = 0.8    # recovery when unstitching
MISS_SHOT_THREAD_COST = 50    # fixed thread lost when a shot misses everything

# Stitch Points
STITCH_POINT_RADIUS = 15
STITCH_POINT_PULSE_SPEED = 0.05

# Player Dimensions
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 45

# Platform Types
PLATFORM_NORMAL = 'normal'
PLATFORM_MOVABLE = 'movable'
PLATFORM_BUTTON = 'button'

# Game States
STATE_MENU = 'menu'
STATE_PLAYING = 'playing'
STATE_PAUSED = 'paused'
STATE_WIN = 'win'
STATE_LOSE = 'lose'
STATE_LEVEL_SELECT = 'level_select'

# Lose Reasons
LOSE_THREAD_OUT = 'thread_out'
LOSE_FALL = 'fall'
LOSE_HAZARD = 'hazard'

# Sound placeholders (keys for sound dict)
SOUNDS = {
    'needle_shoot': 'needle_shoot.wav',
    'needle_hit': 'needle_hit.wav',
    'thread_snap': 'thread_snap.wav',
    'stitch_complete': 'stitch_complete.wav',
    'player_jump': 'jump.wav',
    'bounce': 'bounce.wav',
    'button_press': 'button.wav',
    'win': 'win.wav',
    'lose': 'lose.wav',
}

# Key Bindings
KEYS = {
    'left': [pygame.K_LEFT, pygame.K_a],
    'right': [pygame.K_RIGHT, pygame.K_d],
    'jump': [pygame.K_SPACE, pygame.K_UP, pygame.K_w],
    'shoot': [pygame.K_LSHIFT, pygame.K_RSHIFT],  # Or mouse click
    'unstitch': [pygame.K_e],
    'restart': [pygame.K_r],
    'pause': [pygame.K_ESCAPE, pygame.K_p],
}