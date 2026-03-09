# ============================================================
# STITCH IT UP - Level System
# Platforms, Stitch Points, Hazards, and Level Design
# ============================================================

import pygame
import math
try:
    from .constants import *
except ImportError:
    from constants import *

class Platform:
    """A platform the player can stand on"""
    
    def __init__(self, x, y, width, height, platform_type=PLATFORM_NORMAL):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.platform_type = platform_type
        self.original_x = x  # Store original position
        self.original_y = y
        
        # For movable platforms
        self.is_movable = platform_type == PLATFORM_MOVABLE
        self.vel_y = 0
        self.attached_thread = None
        
        # Visual
        self.wood_pattern_offset = 0
        
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def update(self, all_platforms=None, buttons=None, bridges=None):
        """Update platform state"""
        if self.is_movable and self.attached_thread:
            # Apply gravity - platform falls when thread is attached
            self.vel_y += 0.3  # Gravity
            self.vel_y = min(self.vel_y, 8)  # Terminal velocity
            new_y = self.y + self.vel_y
            slide_x = 0  # Horizontal sliding on slopes
            landed = False
            
            # Check collision with thread bridges first
            if bridges and not landed:
                block_center_x = self.x + self.width / 2
                block_bottom = new_y + self.height
                for bridge in bridges:
                    if bridge.active and bridge.is_bridge:
                        # Get bridge bounds
                        x1, x2 = min(bridge.point_a[0], bridge.point_b[0]), max(bridge.point_a[0], bridge.point_b[0])
                        # Check if block is within bridge x range
                        if x1 - 20 <= block_center_x <= x2 + 20:
                            bridge_y = bridge.get_y_at_x(block_center_x)
                            # Check if block is landing on bridge
                            if self.y + self.height <= bridge_y + 5 and block_bottom >= bridge_y - 5:
                                new_y = bridge_y - self.height
                                self.vel_y = 0
                                landed = True
                                
                                # Calculate slope and add sliding
                                dy = bridge.point_b[1] - bridge.point_a[1]
                                dx = bridge.point_b[0] - bridge.point_a[0]
                                if abs(dx) > 10:  # Not vertical
                                    slope = dy / dx
                                    if abs(slope) > 0.1:  # Significant slope
                                        # Slide down the slope (faster)
                                        slide_x = slope * 5
                                break
            
            # Check collision with other platforms
            if all_platforms and not landed:
                my_rect = pygame.Rect(self.x, new_y, self.width, self.height)
                for other in all_platforms:
                    if other is not self and not other.is_movable:
                        if my_rect.colliderect(other.rect):
                            # Land on this platform
                            new_y = other.y - self.height
                            self.vel_y = 0
                            landed = True
                            break
            
            # Check collision with buttons (stop on buttons)
            if buttons and not landed:
                my_rect = pygame.Rect(self.x, new_y, self.width, self.height)
                for button in buttons:
                    if my_rect.colliderect(button.detection_rect):
                        # Land on button - stop falling
                        new_y = button.y - self.height + 5
                        self.vel_y = 0
                        landed = True
                        break
                        
            self.y = new_y
            self.x += slide_x  # Apply sliding
            
    def attach_thread(self, thread_connection):
        """Attach thread for pulling"""
        if self.is_movable:
            self.attached_thread = thread_connection
            
    def detach_thread(self):
        """Detach thread"""
        self.attached_thread = None
        self.vel_y = 0
        
    def reset(self):
        """Reset to original position"""
        self.x = self.original_x
        self.y = self.original_y
        self.vel_y = 0
        self.attached_thread = None
        
    def draw(self, screen):
        """Draw the platform"""
        rect = self.rect
        
        # Draw shadow
        shadow_rect = pygame.Rect(rect.x + 4, rect.y + 4, rect.width, rect.height)
        pygame.draw.rect(screen, (30, 25, 20), shadow_rect, border_radius=3)
        
        # Main platform (wooden spool style)
        pygame.draw.rect(screen, COLORS['platform'], rect, border_radius=3)
        
        # Wood grain pattern
        grain_color = (COLORS['platform'][0] - 20, 
                      COLORS['platform'][1] - 15, 
                      COLORS['platform'][2] - 10)
        for i in range(0, self.width, 20):
            x = rect.x + i + self.wood_pattern_offset
            if x < rect.right - 5:
                pygame.draw.line(screen, grain_color, 
                               (x, rect.y + 3), 
                               (x, rect.bottom - 3), 1)
        
        # Outline
        pygame.draw.rect(screen, COLORS['platform_outline'], rect, 3, border_radius=3)
        
        # Decorative edges (like a spool)
        pygame.draw.rect(screen, COLORS['platform_outline'], 
                        (rect.x, rect.y, rect.width, 5), border_radius=2)
        pygame.draw.rect(screen, COLORS['platform_outline'], 
                        (rect.x, rect.bottom - 5, rect.width, 5), border_radius=2)
        
        # If movable, add indicator
        if self.is_movable:
            center = self.center
            pygame.draw.circle(screen, COLORS['thread'], center, 8, 2)
            pygame.draw.line(screen, COLORS['thread'], 
                           (center[0], center[1] - 5),
                           (center[0], center[1] + 5), 2)


class StitchPoint:
    """A point where the needle can anchor - represents tears in space"""
    
    def __init__(self, x, y, is_final=False):
        self.x = x
        self.y = y
        self.radius = STITCH_POINT_RADIUS
        self.is_final = is_final  # Goal point
        self.stitched = False
        self.active = True
        
        # Animation
        self.pulse_phase = 0
        self.glow_intensity = 0
        
    @property
    def center(self):
        return (self.x, self.y)
    
    @property
    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                          self.radius * 2, self.radius * 2)
    
    def update(self):
        """Update animation"""
        self.pulse_phase += STITCH_POINT_PULSE_SPEED
        self.glow_intensity = (math.sin(self.pulse_phase) + 1) / 2
        
    def draw(self, screen):
        """Draw the stitch point"""
        if not self.active:
            return
            
        # Calculate pulse size
        pulse_radius = self.radius + int(self.glow_intensity * 5)
        
        # Choose color based on type
        if self.is_final:
            main_color = COLORS['stitch_point_final']
            glow_color = (0, 200, 100)
        else:
            main_color = COLORS['stitch_point']
            glow_color = (255, 200, 100)
        
        # Draw outer glow
        glow_radius = pulse_radius + 10
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        glow_alpha = int(100 * self.glow_intensity)
        pygame.draw.circle(glow_surface, (*glow_color, glow_alpha), 
                          (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (self.x - glow_radius, self.y - glow_radius))
        
        # Draw tear/rip effect (zigzag)
        if not self.stitched:
            self._draw_tear_effect(screen, main_color)
        
        # Draw main point
        pygame.draw.circle(screen, main_color, (self.x, self.y), pulse_radius)
        
        # Draw inner ring
        inner_color = (min(255, main_color[0] + 50),
                      min(255, main_color[1] + 50),
                      min(255, main_color[2] + 50))
        pygame.draw.circle(screen, inner_color, (self.x, self.y), pulse_radius - 5)
        
        # Draw center dot
        pygame.draw.circle(screen, (255, 255, 255), (self.x, self.y), 4)
        
        # If stitched, show thread knot
        if self.stitched:
            pygame.draw.circle(screen, COLORS['thread'], (self.x, self.y), 6)
            pygame.draw.circle(screen, (200, 0, 0), (self.x, self.y), 3)
        
        # If final, add star effect
        if self.is_final:
            self._draw_star_effect(screen)
            
    def _draw_tear_effect(self, screen, color):
        """Draw zigzag tear effect around the point"""
        num_points = 8
        for i in range(num_points):
            angle1 = (i / num_points) * 2 * math.pi + self.pulse_phase
            angle2 = ((i + 0.5) / num_points) * 2 * math.pi + self.pulse_phase
            
            r1 = self.radius + 15
            r2 = self.radius + 8
            
            x1 = self.x + math.cos(angle1) * r1
            y1 = self.y + math.sin(angle1) * r1
            x2 = self.x + math.cos(angle2) * r2
            y2 = self.y + math.sin(angle2) * r2
            
            pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)
            
    def _draw_star_effect(self, screen):
        """Draw rotating star for final point"""
        num_rays = 4
        for i in range(num_rays):
            angle = (i / num_rays) * math.pi + self.pulse_phase * 0.5
            length = self.radius + 20 + self.glow_intensity * 10
            
            x1 = self.x + math.cos(angle) * (self.radius + 5)
            y1 = self.y + math.sin(angle) * (self.radius + 5)
            x2 = self.x + math.cos(angle) * length
            y2 = self.y + math.sin(angle) * length
            
            pygame.draw.line(screen, (255, 255, 200), (x1, y1), (x2, y2), 2)


class Button:
    """A pressure button that can be activated by weight"""
    
    def __init__(self, x, y, width=50, height=15, linked_object=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.pressed = False
        self.linked_object = linked_object  # Object this button controls
        self.press_timer = 0
        
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def detection_rect(self):
        """Larger rect for detection"""
        return pygame.Rect(self.x - 5, self.y - 20, self.width + 10, 25)
    
    def update(self, objects_on_button):
        """Check if something is pressing the button"""
        self.pressed = len(objects_on_button) > 0
        
        if self.pressed:
            self.press_timer = min(10, self.press_timer + 1)
        else:
            self.press_timer = max(0, self.press_timer - 1)
        
        # Don't directly activate door here - Level.update() handles multi-button logic
            
    def draw(self, screen):
        """Draw the button"""
        press_offset = self.press_timer // 2
        
        # Base
        base_rect = pygame.Rect(self.x - 5, self.y + 5, self.width + 10, 10)
        pygame.draw.rect(screen, (80, 80, 80), base_rect, border_radius=2)
        
        # Button top
        button_rect = pygame.Rect(self.x, self.y + press_offset, 
                                  self.width, self.height - press_offset)
        color = COLORS['button_active'] if self.pressed else COLORS['button_inactive']
        pygame.draw.rect(screen, color, button_rect, border_radius=3)
        
        # Highlight
        highlight_rect = pygame.Rect(self.x + 3, self.y + press_offset + 2,
                                    self.width - 6, 4)
        highlight_color = (color[0] + 40, color[1] + 40, color[2] + 40)
        pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=2)


class Door:
    """A door that can be opened by buttons"""
    
    def __init__(self, x, y, width=40, height=80):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.open = False
        self.open_amount = 0  # 0-1 for animation
        self.linked_buttons = []  # List of buttons that control this door
        
    def link_button(self, button):
        """Add a button that controls this door"""
        if button not in self.linked_buttons:
            self.linked_buttons.append(button)
            
    def check_buttons(self):
        """Check if all linked buttons are pressed"""
        if not self.linked_buttons:
            return False
        # ALL buttons must be pressed simultaneously
        return all(button.pressed for button in self.linked_buttons)
        
    @property
    def rect(self):
        """Collision rect (shrinks when open)"""
        effective_height = self.height * (1 - self.open_amount)
        return pygame.Rect(self.x, self.y, self.width, effective_height)
    
    def activate(self):
        self.open = True
        
    def deactivate(self):
        self.open = False
        
    def update(self):
        """Animate door"""
        if self.open:
            self.open_amount = min(1, self.open_amount + 0.05)
        else:
            self.open_amount = max(0, self.open_amount - 0.05)
            
    def draw(self, screen):
        """Draw the door"""
        # Frame
        frame_rect = pygame.Rect(self.x - 5, self.y - 5, self.width + 10, self.height + 5)
        pygame.draw.rect(screen, (60, 50, 40), frame_rect, border_radius=3)
        
        # Door (slides up when open)
        door_height = self.height * (1 - self.open_amount)
        door_y = self.y + (self.height - door_height)
        door_rect = pygame.Rect(self.x, door_y, self.width, door_height)
        
        pygame.draw.rect(screen, (100, 80, 60), door_rect)
        pygame.draw.rect(screen, (80, 60, 40), door_rect, 3)
        
        # Door handle
        if door_height > 20:
            handle_y = door_y + door_height // 2
            pygame.draw.circle(screen, (150, 130, 100), 
                             (self.x + self.width - 10, int(handle_y)), 5)


class Hazard:
    """Base class for hazards that can hurt player or cut thread"""
    
    def __init__(self, x, y, width, height, hazard_type='scissors'):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hazard_type = hazard_type
        self.animation_frame = 0
        
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def update(self):
        self.animation_frame += 1
        
    def draw(self, screen):
        if self.hazard_type == 'scissors':
            self._draw_scissors(screen)
        elif self.hazard_type == 'flame':
            self._draw_flame(screen)
            
    def _draw_scissors(self, screen):
        """Draw animated scissors"""
        cx, cy = self.center
        
        # Scissor animation (opening and closing)
        open_angle = math.sin(self.animation_frame * 0.1) * 0.3
        
        # Left blade
        blade_length = self.width // 2
        left_angle = math.pi * 0.75 + open_angle
        left_tip = (cx + math.cos(left_angle) * blade_length,
                   cy + math.sin(left_angle) * blade_length)
        
        # Right blade
        right_angle = math.pi * 0.25 - open_angle
        right_tip = (cx + math.cos(right_angle) * blade_length,
                    cy + math.sin(right_angle) * blade_length)
        
        # Draw blades
        pygame.draw.line(screen, COLORS['hazard_scissors'], 
                        (cx, cy), left_tip, 6)
        pygame.draw.line(screen, COLORS['hazard_scissors'], 
                        (cx, cy), right_tip, 6)
        
        # Blade edges (shiny)
        pygame.draw.line(screen, (220, 220, 220), 
                        (cx, cy), left_tip, 2)
        pygame.draw.line(screen, (220, 220, 220), 
                        (cx, cy), right_tip, 2)
        
        # Handles
        handle_color = (200, 50, 50)
        handle1 = (cx + math.cos(left_angle + math.pi) * 15,
                  cy + math.sin(left_angle + math.pi) * 15)
        handle2 = (cx + math.cos(right_angle + math.pi) * 15,
                  cy + math.sin(right_angle + math.pi) * 15)
        pygame.draw.circle(screen, handle_color, (int(handle1[0]), int(handle1[1])), 8)
        pygame.draw.circle(screen, handle_color, (int(handle2[0]), int(handle2[1])), 8)
        
        # Center pivot
        pygame.draw.circle(screen, (100, 100, 100), (cx, cy), 5)
        
    def _draw_flame(self, screen):
        """Draw animated flame"""
        cx, cy = self.center
        
        # Multiple flame layers
        for i in range(3):
            phase = self.animation_frame * 0.15 + i * 0.5
            flicker = math.sin(phase) * 5
            
            # Flame shape (polygon)
            flame_width = self.width // 2 - i * 5
            flame_height = self.height - i * 8
            
            points = [
                (cx, cy - flame_height // 2 + flicker),  # Top
                (cx + flame_width, cy + flame_height // 3),  # Right
                (cx + flame_width // 2, cy + flame_height // 2),  # Bottom right
                (cx, cy + flame_height // 3 + flicker * 0.5),  # Bottom center
                (cx - flame_width // 2, cy + flame_height // 2),  # Bottom left
                (cx - flame_width, cy + flame_height // 3),  # Left
            ]
            
            # Color gradient (outer to inner: red -> orange -> yellow)
            colors = [
                (255, 50, 0),    # Red
                (255, 150, 0),   # Orange
                (255, 255, 100), # Yellow
            ]
            
            pygame.draw.polygon(screen, colors[i], points)


class Level:
    """Contains all objects for a game level"""
    
    def __init__(self, level_data):
        self.platforms = []
        self.stitch_points = []
        self.hazards = []
        self.buttons = []
        self.doors = []
        self.movable_objects = []
        
        self.player_start = (100, 500)
        self.thread_limit = DEFAULT_THREAD_LENGTH
        self.level_name = "Level"
        
        if level_data:
            self._load_level(level_data)
            
    def _load_level(self, data):
        """Load level from data dictionary"""
        self.level_name = data.get('name', 'Unknown Level')
        self.player_start = data.get('player_start', (100, 500))
        self.thread_limit = data.get('thread_limit', DEFAULT_THREAD_LENGTH)
        
        # Load platforms
        for p in data.get('platforms', []):
            platform = Platform(p['x'], p['y'], p['width'], p['height'],
                              p.get('type', PLATFORM_NORMAL))
            self.platforms.append(platform)
            if platform.is_movable:
                self.movable_objects.append(platform)
        
        # Load stitch points
        for sp in data.get('stitch_points', []):
            stitch_point = StitchPoint(sp['x'], sp['y'], sp.get('is_final', False))
            self.stitch_points.append(stitch_point)
            
        # Load hazards
        for h in data.get('hazards', []):
            hazard = Hazard(h['x'], h['y'], h.get('width', 40), h.get('height', 40),
                          h.get('type', 'scissors'))
            self.hazards.append(hazard)
            
        # Load buttons and doors
        for d in data.get('doors', []):
            door = Door(d['x'], d['y'], d.get('width', 40), d.get('height', 80))
            self.doors.append(door)
            
        for b in data.get('buttons', []):
            linked_door = None
            if 'linked_door' in b:
                door_index = b['linked_door']
                if door_index < len(self.doors):
                    linked_door = self.doors[door_index]
            button = Button(b['x'], b['y'], b.get('width', 50), b.get('height', 15),
                          linked_door)
            self.buttons.append(button)
            # Link button to door for multi-button checking
            if linked_door:
                linked_door.link_button(button)
    
    def get_final_stitch_point(self):
        """Get the goal stitch point"""
        for sp in self.stitch_points:
            if sp.is_final:
                return sp
        return None
    
    def update(self, bridges=None):
        """Update all level objects"""
        for sp in self.stitch_points:
            sp.update()
        for h in self.hazards:
            h.update()
        # Update movable platforms with collision detection including bridges
        for p in self.platforms:
            if p.is_movable:
                p.update(self.platforms, self.buttons, bridges)
            else:
                p.update()
        
        # Check door opening based on ALL linked buttons being pressed
        for d in self.doors:
            if d.check_buttons():
                d.open = True
            else:
                d.open = False
            d.update()
            
    def draw(self, screen):
        """Draw all level objects"""
        # Draw platforms
        for platform in self.platforms:
            platform.draw(screen)
            
        # Draw doors
        for door in self.doors:
            door.draw(screen)
            
        # Draw buttons
        for button in self.buttons:
            button.draw(screen)
            
        # Draw stitch points
        for sp in self.stitch_points:
            sp.draw(screen)
            
        # Draw hazards
        for hazard in self.hazards:
            hazard.draw(screen)
            
    def reset(self):
        """Reset all level objects"""
        for p in self.platforms:
            p.reset()
        for sp in self.stitch_points:
            sp.stitched = False
        for d in self.doors:
            d.open = False
            d.open_amount = 0
        for b in self.buttons:
            b.pressed = False
            b.press_timer = 0


# ============================================================
# LEVEL DEFINITIONS
# ============================================================

LEVELS = [
    # Level 1: Tutorial - Basic Stitching with Door
    {
        'name': 'First Stitch',
        'player_start': (100, 550),
        'thread_limit': 700,
        'platforms': [
            {'x': 50, 'y': 600, 'width': 200, 'height': 30},   # Start platform
            {'x': 400, 'y': 600, 'width': 200, 'height': 30},  # Middle platform
            {'x': 500, 'y': 300, 'width': 60, 'height': 25, 'type': 'movable'},  # Movable block
            {'x': 750, 'y': 550, 'width': 200, 'height': 30},  # End platform with door
        ],
        'stitch_points': [
            {'x': 200, 'y': 500},
            {'x': 400, 'y': 250},   # High point to shoot block
            {'x': 600, 'y': 450},
        ],
        'hazards': [],
        'buttons': [
            {'x': 480, 'y': 585, 'linked_door': 0},  # Button on middle platform
        ],
        'doors': [
            {'x': 900, 'y': 470, 'width': 40, 'height': 80},  # Exit door
        ],
    },
    
    # Level 2: Bridge Building with Door
    {
        'name': 'Bridge the Gap',
        'player_start': (100, 450),
        'thread_limit': 900,
        'platforms': [
            {'x': 50, 'y': 500, 'width': 150, 'height': 30},
            {'x': 350, 'y': 200, 'width': 60, 'height': 25, 'type': 'movable'},  # Movable block
            {'x': 500, 'y': 500, 'width': 150, 'height': 30},
            {'x': 950, 'y': 450, 'width': 150, 'height': 30},
        ],
        'stitch_points': [
            {'x': 150, 'y': 480},
            {'x': 300, 'y': 150},   # High point for block
            {'x': 350, 'y': 480},   # Bridge points
            {'x': 550, 'y': 480},
            {'x': 750, 'y': 430},
        ],
        'hazards': [
            {'x': 560, 'y': 455, 'width': 40, 'height': 40, 'type': 'flame'},
        ],
        'buttons': [
            {'x': 520, 'y': 485, 'linked_door': 0},  # Button
        ],
        'doors': [
            {'x': 1050, 'y': 370, 'width': 40, 'height': 80},  # Exit door
        ],
    },
    
    # Level 3: Grappling Introduction with Door
    {
        'name': 'Swing Across',
        'player_start': (100, 550),
        'thread_limit': 1000,
        'platforms': [
            {'x': 50, 'y': 600, 'width': 180, 'height': 30},
            {'x': 450, 'y': 180, 'width': 60, 'height': 25, 'type': 'movable'},  # Movable block
            {'x': 700, 'y': 550, 'width': 200, 'height': 30},
            {'x': 1000, 'y': 500, 'width': 180, 'height': 30},
        ],
        'stitch_points': [
            {'x': 400, 'y': 200},   # Ceiling anchor for grapple
            {'x': 500, 'y': 130},   # High point to hit block
            {'x': 600, 'y': 180},   # Another ceiling anchor
            {'x': 900, 'y': 250},
        ],
        'hazards': [
            {'x': 350, 'y': 500, 'width': 50, 'height': 50, 'type': 'scissors'},
            {'x': 550, 'y': 520, 'width': 40, 'height': 40, 'type': 'scissors'},
        ],
        'buttons': [
            {'x': 750, 'y': 535, 'linked_door': 0},  # Button on platform
        ],
        'doors': [
            {'x': 1120, 'y': 420, 'width': 40, 'height': 80},  # Exit door
        ],
    },
    
    # Level 4: Door Puzzle - Shoot wood block to press button and open door
    {
        'name': 'Open the Door',
        'player_start': (100, 450),
        'thread_limit': 1000,
        'platforms': [
            {'x': 50, 'y': 500, 'width': 200, 'height': 30},      # Start platform
            {'x': 400, 'y': 200, 'width': 80, 'height': 25, 'type': 'movable'},  # Movable wood block (above button)
            {'x': 600, 'y': 500, 'width': 200, 'height': 30},     # Middle platform
            {'x': 950, 'y': 400, 'width': 200, 'height': 30},     # End platform (with door)
        ],
        'stitch_points': [
            {'x': 200, 'y': 400},     # For swing/bridge
            {'x': 350, 'y': 150},     # High point to grapple
            {'x': 550, 'y': 250},     # Another grapple
            {'x': 750, 'y': 350},
        ],
        'hazards': [
            {'x': 380, 'y': 400, 'width': 44, 'height': 44, 'type': 'flame'},
        ],
        'buttons': [
            {'x': 420, 'y': 485, 'linked_door': 0},  # Button under the movable block
        ],
        'doors': [
            {'x': 1100, 'y': 320, 'width': 40, 'height': 80},  # Door to pass through
        ],
    },
    
    # Level 5: Final Challenge - Combined mechanics with door puzzle
    {
        'name': 'Final Challenge',
        'player_start': (80, 550),
        'thread_limit': 1200,
        'platforms': [
            {'x': 30, 'y': 600, 'width': 150, 'height': 30},      # Start
            {'x': 300, 'y': 550, 'width': 120, 'height': 30},     
            {'x': 550, 'y': 200, 'width': 70, 'height': 25, 'type': 'movable'},  # Movable block
            {'x': 550, 'y': 450, 'width': 100, 'height': 30},     
            {'x': 800, 'y': 350, 'width': 150, 'height': 30},     
            {'x': 1050, 'y': 300, 'width': 150, 'height': 30},    # Final platform with door
        ],
        'stitch_points': [
            {'x': 100, 'y': 500},
            {'x': 350, 'y': 450},
            {'x': 280, 'y': 250},   # Ceiling grapple
            {'x': 500, 'y': 150},   # High grapple (to hit movable block)
            {'x': 650, 'y': 350},
            {'x': 900, 'y': 200},   # High grapple
        ],
        'hazards': [
            {'x': 420, 'y': 550, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 720, 'y': 400, 'width': 50, 'height': 50, 'type': 'scissors'},
            {'x': 930, 'y': 320, 'width': 40, 'height': 40, 'type': 'flame'},
        ],
        'buttons': [
            {'x': 560, 'y': 435, 'linked_door': 0},  # Button under movable block
        ],
        'doors': [
            {'x': 1150, 'y': 220, 'width': 40, 'height': 80},  # Exit door
        ],
    },
    
    # Level 6: Double Trouble - Two blocks, two buttons
    {
        'name': 'Double Trouble',
        'player_start': (80, 550),
        'thread_limit': 1400,
        'platforms': [
            {'x': 30, 'y': 600, 'width': 150, 'height': 30},      # Start
            {'x': 250, 'y': 150, 'width': 60, 'height': 25, 'type': 'movable'},  # Block 1
            {'x': 300, 'y': 500, 'width': 120, 'height': 30},     
            {'x': 600, 'y': 180, 'width': 60, 'height': 25, 'type': 'movable'},  # Block 2
            {'x': 550, 'y': 400, 'width': 120, 'height': 30},     
            {'x': 800, 'y': 300, 'width': 150, 'height': 30},     
            {'x': 1050, 'y': 250, 'width': 150, 'height': 30},    # Final platform with door
        ],
        'stitch_points': [
            {'x': 100, 'y': 500},
            {'x': 200, 'y': 100},   # High point for block 1
            {'x': 350, 'y': 400},
            {'x': 550, 'y': 130},   # High point for block 2
            {'x': 700, 'y': 300},
            {'x': 950, 'y': 200},
        ],
        'hazards': [
            {'x': 450, 'y': 500, 'width': 50, 'height': 50, 'type': 'scissors'},
            {'x': 750, 'y': 350, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 980, 'y': 260, 'width': 44, 'height': 44, 'type': 'scissors'},
        ],
        'buttons': [
            {'x': 320, 'y': 485, 'linked_door': 0},  # Button 1 - under block 1
            {'x': 570, 'y': 385, 'linked_door': 0},  # Button 2 - under block 2 (same door)
        ],
        'doors': [
            {'x': 1150, 'y': 170, 'width': 40, 'height': 80},
        ],
    },
    
    # Level 7: Scissor Maze - Navigate through scissors
    {
        'name': 'Scissor Maze',
        'player_start': (80, 450),
        'thread_limit': 1500,
        'platforms': [
            {'x': 30, 'y': 500, 'width': 150, 'height': 30},
            {'x': 250, 'y': 450, 'width': 100, 'height': 30},
            {'x': 450, 'y': 120, 'width': 70, 'height': 25, 'type': 'movable'},  # Block
            {'x': 450, 'y': 400, 'width': 100, 'height': 30},
            {'x': 650, 'y': 350, 'width': 100, 'height': 30},
            {'x': 850, 'y': 300, 'width': 100, 'height': 30},
            {'x': 1050, 'y': 250, 'width': 150, 'height': 30},
        ],
        'stitch_points': [
            {'x': 120, 'y': 400},
            {'x': 300, 'y': 350},
            {'x': 400, 'y': 80},    # High point for block
            {'x': 500, 'y': 300},
            {'x': 700, 'y': 250},
            {'x': 900, 'y': 200},
            {'x': 1100, 'y': 150},
        ],
        'hazards': [
            {'x': 200, 'y': 380, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 380, 'y': 330, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 580, 'y': 280, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 780, 'y': 230, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 980, 'y': 200, 'width': 38, 'height': 38, 'type': 'flame'},
        ],
        'buttons': [
            {'x': 470, 'y': 385, 'linked_door': 0},
        ],
        'doors': [
            {'x': 1150, 'y': 170, 'width': 40, 'height': 80},
        ],
    },
    
    # Level 8: The Gauntlet - Ultimate challenge
    {
        'name': 'The Gauntlet',
        'player_start': (60, 550),
        'thread_limit': 1800,
        'platforms': [
            {'x': 30, 'y': 600, 'width': 120, 'height': 30},
            {'x': 200, 'y': 100, 'width': 60, 'height': 25, 'type': 'movable'},   # Block 1
            {'x': 200, 'y': 500, 'width': 100, 'height': 30},
            {'x': 400, 'y': 450, 'width': 80, 'height': 30},
            {'x': 550, 'y': 150, 'width': 60, 'height': 25, 'type': 'movable'},   # Block 2
            {'x': 600, 'y': 380, 'width': 80, 'height': 30},
            {'x': 780, 'y': 320, 'width': 80, 'height': 30},
            {'x': 900, 'y': 45, 'width': 60, 'height': 25, 'type': 'movable'},   # Block 3 (raised much higher)
            {'x': 950, 'y': 260, 'width': 100, 'height': 30},
            {'x': 1100, 'y': 200, 'width': 100, 'height': 30},
        ],
        'stitch_points': [
            {'x': 100, 'y': 500},
            {'x': 180, 'y': 50},    # Block 1 high
            {'x': 250, 'y': 400},
            {'x': 420, 'y': 350},
            {'x': 520, 'y': 100},   # Block 2 high
            {'x': 650, 'y': 280},
            {'x': 800, 'y': 220},
            {'x': 1000, 'y': 185},  # Right anchor near Block 3 lowered slightly
            {'x': 1150, 'y': 120},
        ],
        'hazards': [
            {'x': 320, 'y': 480, 'width': 50, 'height': 50, 'type': 'scissors'},
            {'x': 500, 'y': 400, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 700, 'y': 350, 'width': 50, 'height': 50, 'type': 'scissors'},
            {'x': 860, 'y': 290, 'width': 40, 'height': 40, 'type': 'flame'},
            {'x': 1020, 'y': 230, 'width': 40, 'height': 40, 'type': 'scissors'},
            {'x': 1120, 'y': 180, 'width': 38, 'height': 38, 'type': 'flame'},
        ],
        'buttons': [
            {'x': 220, 'y': 485, 'linked_door': 0},   # Button 1
            {'x': 620, 'y': 365, 'linked_door': 0},   # Button 2
            {'x': 970, 'y': 245, 'linked_door': 0},   # Button 3
        ],
        'doors': [
            {'x': 1150, 'y': 120, 'width': 40, 'height': 80},
        ],
    },
]


def _generate_advanced_level(level_number):
    """Generate challenge levels from 9 to 30 with stronger scaling."""
    difficulty = level_number - 8
    movable_count = min(3, 1 + difficulty // 6)
    button_count = max(1, movable_count)

    # Later levels have tighter thread economy.
    thread_limit = max(700, 1300 - difficulty * 22)

    # Core traversal path rises and narrows with difficulty.
    step = max(140, 185 - difficulty * 2)
    width_main = max(88, 150 - difficulty * 2)
    y_gain = min(250, 70 + difficulty * 8)

    platforms = [
        {'x': 35, 'y': 620, 'width': 180, 'height': 30},
    ]
    for i in range(1, 7):
        px = 35 + i * step
        py = 620 - int((i / 6) * y_gain) - (i % 2) * 25
        py = max(250, py)
        platforms.append({'x': px, 'y': py, 'width': width_main, 'height': 28})

    exit_platform = platforms[-1]
    exit_y = exit_platform['y']

    # Stitch points for upward pathing.
    stitch_points = [
        {'x': 105, 'y': 545},
    ]
    for i, platform in enumerate(platforms[1:], start=1):
        offset_up = 85 + (i % 2) * 12
        stitch_points.append({
            'x': platform['x'] + platform['width'] // 2,
            'y': max(80, platform['y'] - offset_up),
        })

    buttons = []

    # Door button logic: early advanced levels require player press,
    # later levels require moving block drops.
    for i in range(button_count):
        button_host = platforms[min(2 + i, len(platforms) - 2)]
        button_x = button_host['x'] + button_host['width'] // 2 - 24
        button_y = button_host['y'] - 15
        buttons.append({'x': button_x, 'y': button_y, 'linked_door': 0})

        if movable_count > 0 and i < movable_count:
            block_x = button_x - 2
            block_y = max(95, 180 - difficulty * 3 + i * 28)
            platforms.append({'x': block_x, 'y': block_y, 'width': 58, 'height': 24, 'type': 'movable'})
            stitch_points.append({'x': block_x + 24, 'y': max(55, block_y - 65)})

    # Hazards: scissors become thread traps, flames punish direct contact.
    scissor_count = min(7, 2 + difficulty // 3)
    flame_count = min(6, 2 + difficulty // 4)
    hazards = []

    for i in range(scissor_count):
        hx = 220 + i * max(110, 150 - difficulty)
        hy = 560 - (i % 3) * 70
        hazards.append({'x': hx, 'y': hy, 'width': 44, 'height': 44, 'type': 'scissors'})

    for i in range(flame_count):
        host = platforms[min(i + 1, len(platforms) - 1)]
        fx = host['x'] + host['width'] // 2 - 18
        fy = host['y'] - 42
        hazards.append({'x': fx, 'y': fy, 'width': 38, 'height': 38, 'type': 'flame'})

    return {
        'name': f'Needle Trial {level_number:02d}',
        'player_start': (70, 560),
        'thread_limit': thread_limit,
        'platforms': platforms,
        'stitch_points': stitch_points,
        'hazards': hazards,
        'buttons': buttons,
        'doors': [
            {'x': exit_platform['x'] + exit_platform['width'] - 40, 'y': exit_y - 82, 'width': 40, 'height': 82},
        ],
    }


for level_number in range(9, 31):
    LEVELS.append(_generate_advanced_level(level_number))


def get_level(level_index):
    """Get a level by index"""
    if 0 <= level_index < len(LEVELS):
        return Level(LEVELS[level_index])
    return None

def get_level_count():
    """Get total number of levels"""
    return len(LEVELS)
