# ============================================================
# STITCH IT UP
# 2D Puzzle Platformer
# GAMETOPIA 2024
# ============================================================

from .constants import *
from .player import Player
from .thread_system import ThreadManager, Needle, ThreadConnection
from .level_system import Level, Platform, StitchPoint, Hazard, get_level, get_level_count
from .ui_system import HUD, MainMenu, LevelSelectMenu

__version__ = "1.0.0"
__author__ = "GAMETOPIA Team"
__title__ = "Stitch It Up"