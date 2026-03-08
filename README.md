# Stitch It Up

## Introduction
**Stitch It Up** is a 2D puzzle-platformer game developed for GAMETOPIA 2024.

> "Use a magical needle and thread to 'stitch' broken pieces of space together, bridge gaps, swing across gaps, and solve door puzzles in challenging levels."

## Installation & Running

### System Requirements
- Python 3.8+
- Pygame 2.5.0+

### Installation
```bash
cd stitch_it_up
pip install -r requirements.txt
```

### Run the Game
```bash
python main.py
```

## How to Play

### Controls
| Key | Action |
|-----|--------|
| A / D or Arrow Keys | Move left/right |
| Space / Up / W | Jump |
| Mouse Click | Shoot needle to create path |
| R | Restart level |
| ESC / P | Pause |

### Objective
- Shoot threads to create walkable paths across gaps
- Drop wood blocks on buttons to open doors
- Walk through the open door to complete the level

### Win Condition
- All levels: Walk through an open door to win

### Lose Conditions
- Fall into the void
- Run out of thread
- Touch hazards (scissors, flames)

## Game Mechanics

### 1. Stitching & Bridging
- Shoot needle at anchor points (golden circles)
- Thread automatically connects from your position to anchor
- If two points are horizontal and close, thread becomes a **walkable bridge** or **trampoline**

### 2. Thread Paths
- Shoot needle at anchor points to create walkable paths
- Walk on thread paths to cross gaps
- You can create multiple threads!

### 3. Thread Management
- Each level has a thread limit
- Each stitch consumes thread
- **You can shoot multiple threads!** Plan your path
- **THREAD meter** in corner shows remaining thread
- Cannot shoot if not enough thread for the distance

### 4. Door Puzzles
- Shoot needle at wood blocks (movable platforms) to attach thread
- Blocks with thread attached will fall due to gravity
- Falling blocks can press **buttons** on the ground
- Pressing a button opens the linked **door**
- Walk through the open door to complete the level!

## Levels

| Level | Name | Description |
|-------|------|-------------|
| 1 | First Stitch | Tutorial - learn controls and door mechanics |
| 2 | Bridge the Gap | Create thread bridges and open door |
| 3 | Swing Across | Navigate with threads + door puzzle |
| 4 | Open the Door | Advanced door puzzle |
| 5 | Final Challenge | Combine all mechanics |
| 6 | Double Trouble | Two blocks, two buttons - harder! |
| 7 | Scissor Maze | Navigate through multiple scissors |
| 8 | The Gauntlet | Ultimate challenge - 3 blocks, many hazards |

## Project Structure

```
stitch_it_up/
├── main.py           # Main game loop
├── constants.py      # Constants and configuration
├── player.py         # Player class
├── thread_system.py  # Needle and thread system
├── level_system.py   # Levels and game objects
├── ui_system.py      # User interface
├── requirements.txt  # Dependencies
└── README.md         # This file
```

## Visual Design

The game uses a warm pixel art style:
- **Background**: Dark fabric texture (#2D2A32)
- **Platforms**: Wood spool brown
- **Thread**: Crimson red (#DC143C)
- **Anchor Points**: Gold (#FFD700) and spring green (#00FF7F)
- **Player**: Pink pin cushion style

## Credits

**GAMETOPIA 2024** - GDD & Game Mechanics Documentation

---

Have fun playing!
