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


class Enemy:
    """Moving monster that can kill the player and be tied by thread."""

    def __init__(
        self,
        x,
        y,
        width=44,
        height=36,
        speed=1.5,
        patrol_range=120,
        left=None,
        right=None,
        movement='ground',
        fly_range_y=28,
    ):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.speed = speed

        self.start_x = float(x)
        self.start_y = float(y)
        self.left_bound = float(left) if left is not None else self.start_x - patrol_range
        self.right_bound = float(right) if right is not None else self.start_x + patrol_range
        self.direction = 1
        self.movement = movement
        self.fly_range_y = fly_range_y

        self.active = True
        self.is_tied = False
        self.tied_anchor = None
        self.tied_timer = 0
        self.vel_y = 0
        self.anim_phase = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    @property
    def center(self):
        return (int(self.x + self.width // 2), int(self.y + self.height // 2))

    @property
    def can_hurt_player(self):
        return self.active and not self.is_tied

    @property
    def can_be_targeted(self):
        return self.active and not self.is_tied

    def hit_by_thread(self, anchor_point):
        """Enter tied state and start falling when shot by the needle."""
        if not self.can_be_targeted:
            return False
        self.is_tied = True
        self.tied_anchor = anchor_point
        self.tied_timer = 30
        self.vel_y = 1.5
        return True

    def update(self, platforms=None):
        if not self.active:
            return

        self.anim_phase += 1

        if self.is_tied:
            self.tied_timer = max(0, self.tied_timer - 1)
            self.vel_y = min(self.vel_y + 0.35, 10)
            self.y += self.vel_y
            if self.y > SCREEN_HEIGHT + 120:
                self.active = False
            return

        self.x += self.direction * self.speed
        if self.x <= self.left_bound:
            self.x = self.left_bound
            self.direction = 1
        elif self.x + self.width >= self.right_bound:
            self.x = self.right_bound - self.width
            self.direction = -1

        if self.movement == 'flying':
            self.y = self.start_y + math.sin(self.anim_phase * 0.12) * self.fly_range_y
        else:
            self.y = self.start_y + math.sin(self.anim_phase * 0.09) * 2

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.direction = 1
        self.active = True
        self.is_tied = False
        self.tied_anchor = None
        self.tied_timer = 0
        self.vel_y = 0
        self.anim_phase = 0

    def draw(self, screen):
        if not self.active:
            return

        body_color = COLORS.get('enemy_body', (131, 92, 173))
        outline_color = COLORS.get('enemy_outline', (84, 57, 116))
        eye_color = COLORS.get('enemy_eye', (255, 245, 245))

        body_rect = self.rect
        pygame.draw.ellipse(screen, body_color, body_rect)
        pygame.draw.ellipse(screen, outline_color, body_rect, 3)

        # Feet
        if self.movement == 'flying':
            wing_span = 8 + int(math.sin(self.anim_phase * 0.25) * 3)
            left_wing = [
                (body_rect.x + 4, body_rect.centery),
                (body_rect.x - wing_span, body_rect.centery - 6),
                (body_rect.x - wing_span, body_rect.centery + 6),
            ]
            right_wing = [
                (body_rect.right - 4, body_rect.centery),
                (body_rect.right + wing_span, body_rect.centery - 6),
                (body_rect.right + wing_span, body_rect.centery + 6),
            ]
            pygame.draw.polygon(screen, body_color, left_wing)
            pygame.draw.polygon(screen, body_color, right_wing)
            pygame.draw.polygon(screen, outline_color, left_wing, 2)
            pygame.draw.polygon(screen, outline_color, right_wing, 2)
        else:
            leg_y = body_rect.bottom - 4
            pygame.draw.line(screen, outline_color, (body_rect.x + 10, leg_y), (body_rect.x + 6, leg_y + 8), 3)
            pygame.draw.line(screen, outline_color, (body_rect.right - 10, leg_y), (body_rect.right - 6, leg_y + 8), 3)

        # Eyes
        eye_y = body_rect.y + 12
        left_eye_x = body_rect.x + 14
        right_eye_x = body_rect.right - 14
        if self.is_tied:
            pygame.draw.line(screen, outline_color, (left_eye_x - 3, eye_y - 3), (left_eye_x + 3, eye_y + 3), 2)
            pygame.draw.line(screen, outline_color, (left_eye_x - 3, eye_y + 3), (left_eye_x + 3, eye_y - 3), 2)
            pygame.draw.line(screen, outline_color, (right_eye_x - 3, eye_y - 3), (right_eye_x + 3, eye_y + 3), 2)
            pygame.draw.line(screen, outline_color, (right_eye_x - 3, eye_y + 3), (right_eye_x + 3, eye_y - 3), 2)
        else:
            pygame.draw.circle(screen, eye_color, (left_eye_x, eye_y), 4)
            pygame.draw.circle(screen, eye_color, (right_eye_x, eye_y), 4)
            pygame.draw.circle(screen, (20, 20, 20), (left_eye_x + 1, eye_y), 2)
            pygame.draw.circle(screen, (20, 20, 20), (right_eye_x + 1, eye_y), 2)

        # Mouth
        mouth_y = body_rect.y + 24
        pygame.draw.arc(screen, outline_color, (body_rect.centerx - 8, mouth_y - 2, 16, 10), math.pi * 0.1, math.pi * 0.9, 2)

        # Thread tie effect
        if self.is_tied:
            thread_color = COLORS['thread']
            pygame.draw.line(screen, thread_color, (body_rect.x + 6, body_rect.y + 10), (body_rect.right - 6, body_rect.y + 14), 3)
            pygame.draw.line(screen, thread_color, (body_rect.x + 6, body_rect.y + 22), (body_rect.right - 6, body_rect.y + 26), 3)
            if self.tied_anchor and self.tied_timer > 0:
                pygame.draw.line(screen, thread_color, self.tied_anchor, self.center, 2)


class Level:
    """Contains all objects for a game level"""
    
    def __init__(self, level_data):
        self.platforms = []
        self.stitch_points = []
        self.hazards = []
        self.enemies = []
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

        # Load enemies
        for e in data.get('enemies', []):
            enemy = Enemy(
                e['x'],
                e['y'],
                e.get('width', 44),
                e.get('height', 36),
                e.get('speed', 1.5),
                e.get('patrol_range', 120),
                e.get('left'),
                e.get('right'),
                e.get('movement', 'ground'),
                e.get('fly_range_y', 28),
            )
            self.enemies.append(enemy)
            
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
        for enemy in self.enemies:
            enemy.update(self.platforms)
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

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(screen)

    def has_enemy_collision(self, player_rect):
        """Return True if player collides with any active untied enemy."""
        for enemy in self.enemies:
            if enemy.can_hurt_player and player_rect.colliderect(enemy.rect):
                return True
        return False
            
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
        for enemy in self.enemies:
            enemy.reset()


# ============================================================
# LEVEL DEFINITIONS
# ============================================================

LEVELS = [
    # Level 1:
    {
        'name': 'Level 1',
        'player_start': (20, 570),
        'thread_limit': 1500,
        'platforms': [
            {'x': 10, 'y': 600, 'width': 100, 'height': 30},  
            {'x': 300, 'y': 400, 'width': 150, 'height': 30},  
            {'x': 650, 'y': 100, 'width': 60, 'height': 25, 'type': 'movable'},  # Movable block
            {'x': 600, 'y': 400, 'width': 200, 'height': 30}, 
            {'x': 1000, 'y': 250, 'width': 150, 'height': 30},
        ],
        'stitch_points': [
            {'x': 200, 'y': 470},
            {'x': 520, 'y': 300},
            {'x': 900, 'y': 300},
        ],
        'enemies': [
        ],
        'hazards': [],
        'buttons': [
            {'x': 650, 'y': 385, 'linked_door': 0},  # Button on middle platform
        ],
        'doors': [
            {'x': 1050, 'y': 170, 'width': 40, 'height': 80},  # Exit door
        ],
    },
    
    # Level 2:
    {
        'name': 'Level 2',
        'player_start': (50, 470),
        'thread_limit': 2000,
        'platforms': [
            {'x': 10, 'y': 500, 'width': 150, 'height': 30},
            {'x': 350, 'y': 200, 'width': 60, 'height': 25, 'type': 'movable'},  # Movable block
            {'x': 500, 'y': 500, 'width': 200, 'height': 30},
            {'x': 950, 'y': 450, 'width': 150, 'height': 30},
        ],
        'stitch_points': [
            {'x': 275, 'y': 350},   # High point for block
            {'x': 350, 'y': 480},   # Bridge points
            {'x': 550, 'y': 480},
            {'x': 750, 'y': 430},
        ],
        'enemies': [
            {'x': 700, 'y': 375, 'movement': 'flying', 'speed': 1.6, 'left': 520, 'right': 860, 'fly_range_y': 24},
        ],
        'hazards': [
            {'x': 650, 'y': 460, 'width': 40, 'height': 40, 'type': 'flame'},
        ],
        'buttons': [
            {'x': 520, 'y': 485, 'linked_door': 0},  # Button
        ],
        'doors': [
            {'x': 1050, 'y': 370, 'width': 40, 'height': 80},  # Exit door
        ],
    },
    
    # Level 3:
    {
        'name': 'Level 3',
        'player_start': (100, 550),
        'thread_limit': 3000,
        'platforms': [
            {'x': 50, 'y': 600, 'width': 180, 'height': 30},
            {'x': 470, 'y': 230, 'width': 60, 'height': 25, 'type': 'movable'},  # Movable block
            {'x': 700, 'y': 550, 'width': 200, 'height': 30},
            {'x': 1000, 'y': 400, 'width': 180, 'height': 30},
        ],
        'stitch_points': [
            {'x': 400, 'y': 200},   # Ceiling anchor for grapple
            {'x': 500, 'y': 300},   # High point to hit block
            {'x': 600, 'y': 200},   # Another ceiling anchor
            {'x': 950, 'y': 470},
        ],
        'enemies': [
            {'x': 760, 'y': 514, 'width': 42, 'height': 34, 'speed': 1.2, 'left': 710, 'right': 900},
        ],
        'hazards': [
            {'x': 275, 'y': 400, 'width': 50, 'height': 50, 'type': 'scissors'},
            {'x': 800, 'y': 515, 'width': 40, 'height': 40, 'type': 'flame'},
        ],
        'buttons': [
            {'x': 705, 'y': 535, 'linked_door': 0},  # Button on platform
        ],
        'doors': [
            {'x': 1120, 'y': 320, 'width': 40, 'height': 80},  # Exit door
        ],
    },
    
    # Level 4: 
    {
        'name': 'Level 4',
        'player_start': (100, 450),
        'thread_limit': 1000,
        'platforms': [
            {'x': 50, 'y': 500, 'width': 200, 'height': 30},      # Start platform
            {'x': 400, 'y': 200, 'width': 80, 'height': 25, 'type': 'movable'},  # Movable wood block (above button)
            {'x': 600, 'y': 500, 'width': 200, 'height': 30},     # Middle platform
            {'x': 950, 'y': 400, 'width': 200, 'height': 30},     # End platform (with door)
        ],
        'stitch_points': [
            {'x': 300, 'y': 300},     # For swing/bridge
            {'x': 550, 'y': 250},     # Another grapple
            {'x': 750, 'y': 350},
        ],
        'enemies': [
            {'x': 700, 'y': 430, 'movement': 'flying', 'speed': 1.7, 'left': 600, 'right': 1000, 'fly_range_y': 30},
        ],
        'hazards': [
            # {'x': 380, 'y': 400, 'width': 44, 'height': 44, 'type': 'flame'},
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
        'enemies': [
            {'x': 320, 'y': 514, 'speed': 1.4, 'left': 300, 'right': 420},
            {'x': 840, 'y': 314, 'speed': 1.6, 'left': 810, 'right': 940},
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
        'enemies': [
            {'x': 330, 'y': 464, 'speed': 1.5, 'left': 305, 'right': 420},
            {'x': 820, 'y': 264, 'speed': 1.7, 'left': 805, 'right': 950},
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
        'enemies': [
            {'x': 270, 'y': 414, 'speed': 1.7, 'left': 250, 'right': 350},
            {'x': 670, 'y': 314, 'speed': 1.8, 'left': 650, 'right': 750},
            {'x': 1060, 'y': 214, 'speed': 1.9, 'left': 1045, 'right': 1190},
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
        'enemies': [
            {'x': 430, 'y': 310, 'movement': 'flying', 'speed': 1.8, 'left': 350, 'right': 560, 'fly_range_y': 26},
            {'x': 880, 'y': 170, 'movement': 'flying', 'speed': 2.0, 'left': 760, 'right': 1080, 'fly_range_y': 30},
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



# Levels 9-30 (static data)
LEVELS.extend(
[{'name': 'Ramp Trial 09',
  'player_start': (70, 560),
  'thread_limit': 1260,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 220, 'y': 565, 'width': 150, 'height': 28},
                {'x': 400, 'y': 525, 'width': 150, 'height': 28},
                {'x': 580, 'y': 490, 'width': 150, 'height': 28},
                {'x': 760, 'y': 450, 'width': 150, 'height': 28},
                {'x': 940, 'y': 410, 'width': 150, 'height': 28},
                {'x': 1100, 'y': 360, 'width': 150, 'height': 28},
                {'x': 448, 'y': 186, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 295, 'y': 478},
                    {'x': 475, 'y': 453},
                    {'x': 655, 'y': 403},
                    {'x': 835, 'y': 378},
                    {'x': 1015, 'y': 323},
                    {'x': 1175, 'y': 288},
                    {'x': 473, 'y': 124}],
  'hazards': [{'x': 261, 'y': 511, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 453, 'y': 461, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 449, 'y': 485, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 451, 'y': 510, 'linked_door': 0}],
  'doors': [{'x': 1210, 'y': 278, 'width': 40, 'height': 82}]},
 {'name': 'Ramp Trial 10',
  'player_start': (70, 560),
  'thread_limit': 1240,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 220, 'y': 562, 'width': 144, 'height': 28},
                {'x': 400, 'y': 522, 'width': 144, 'height': 28},
                {'x': 580, 'y': 487, 'width': 144, 'height': 28},
                {'x': 760, 'y': 447, 'width': 144, 'height': 28},
                {'x': 940, 'y': 407, 'width': 144, 'height': 28},
                {'x': 1100, 'y': 357, 'width': 144, 'height': 28},
                {'x': 445, 'y': 182, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 292, 'y': 475},
                    {'x': 472, 'y': 450},
                    {'x': 652, 'y': 400},
                    {'x': 832, 'y': 375},
                    {'x': 1012, 'y': 320},
                    {'x': 1172, 'y': 285},
                    {'x': 470, 'y': 120}],
  'hazards': [{'x': 258, 'y': 508, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 450, 'y': 458, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 642, 'y': 433, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 446, 'y': 482, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 448, 'y': 507, 'linked_door': 0}],
  'doors': [{'x': 1204, 'y': 275, 'width': 40, 'height': 82}]},
 {'name': 'Ramp Trial 11',
  'player_start': (70, 560),
  'thread_limit': 1220,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 220, 'y': 559, 'width': 138, 'height': 28},
                {'x': 400, 'y': 519, 'width': 138, 'height': 28},
                {'x': 580, 'y': 484, 'width': 138, 'height': 28},
                {'x': 760, 'y': 444, 'width': 138, 'height': 28},
                {'x': 940, 'y': 404, 'width': 138, 'height': 28},
                {'x': 1100, 'y': 354, 'width': 138, 'height': 28},
                {'x': 442, 'y': 178, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 289, 'y': 472},
                    {'x': 469, 'y': 447},
                    {'x': 649, 'y': 397},
                    {'x': 829, 'y': 372},
                    {'x': 1009, 'y': 317},
                    {'x': 1169, 'y': 282},
                    {'x': 467, 'y': 116}],
  'hazards': [{'x': 255, 'y': 505, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 447, 'y': 455, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 639, 'y': 430, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 443, 'y': 479, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 819, 'y': 404, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 445, 'y': 504, 'linked_door': 0}],
  'doors': [{'x': 1198, 'y': 272, 'width': 40, 'height': 82}]},
 {'name': 'Ramp Trial 12',
  'player_start': (70, 560),
  'thread_limit': 1200,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 220, 'y': 556, 'width': 132, 'height': 28},
                {'x': 400, 'y': 516, 'width': 132, 'height': 28},
                {'x': 580, 'y': 481, 'width': 132, 'height': 28},
                {'x': 760, 'y': 441, 'width': 132, 'height': 28},
                {'x': 940, 'y': 401, 'width': 132, 'height': 28},
                {'x': 1100, 'y': 351, 'width': 132, 'height': 28},
                {'x': 439, 'y': 174, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 286, 'y': 469},
                    {'x': 466, 'y': 444},
                    {'x': 646, 'y': 394},
                    {'x': 826, 'y': 369},
                    {'x': 1006, 'y': 314},
                    {'x': 1166, 'y': 279},
                    {'x': 464, 'y': 112}],
  'hazards': [{'x': 252, 'y': 502, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 444, 'y': 452, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 636, 'y': 427, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 792, 'y': 377, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 440, 'y': 476, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 816, 'y': 401, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 442, 'y': 501, 'linked_door': 0}],
  'doors': [{'x': 1192, 'y': 269, 'width': 40, 'height': 82}]},
 {'name': 'Ramp Trial 13',
  'player_start': (70, 560),
  'thread_limit': 1180,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 220, 'y': 553, 'width': 126, 'height': 28},
                {'x': 400, 'y': 513, 'width': 126, 'height': 28},
                {'x': 580, 'y': 478, 'width': 126, 'height': 28},
                {'x': 760, 'y': 438, 'width': 126, 'height': 28},
                {'x': 940, 'y': 398, 'width': 126, 'height': 28},
                {'x': 1100, 'y': 348, 'width': 126, 'height': 28},
                {'x': 436, 'y': 170, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 283, 'y': 466},
                    {'x': 463, 'y': 441},
                    {'x': 643, 'y': 391},
                    {'x': 823, 'y': 366},
                    {'x': 1003, 'y': 311},
                    {'x': 1163, 'y': 276},
                    {'x': 461, 'y': 108}],
  'hazards': [{'x': 249, 'y': 499, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 441, 'y': 449, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 633, 'y': 424, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 789, 'y': 374, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 437, 'y': 473, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 813, 'y': 398, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 439, 'y': 498, 'linked_door': 0}],
  'doors': [{'x': 1186, 'y': 266, 'width': 40, 'height': 82}]},
 {'name': 'Ramp Trial 14',
  'player_start': (70, 560),
  'thread_limit': 1160,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 220, 'y': 550, 'width': 120, 'height': 28},
                {'x': 400, 'y': 510, 'width': 120, 'height': 28},
                {'x': 580, 'y': 475, 'width': 120, 'height': 28},
                {'x': 760, 'y': 435, 'width': 120, 'height': 28},
                {'x': 940, 'y': 395, 'width': 120, 'height': 28},
                {'x': 1100, 'y': 345, 'width': 120, 'height': 28},
                {'x': 433, 'y': 166, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 280, 'y': 463},
                    {'x': 460, 'y': 438},
                    {'x': 640, 'y': 388},
                    {'x': 820, 'y': 363},
                    {'x': 1000, 'y': 308},
                    {'x': 1160, 'y': 273},
                    {'x': 458, 'y': 104}],
  'hazards': [{'x': 246, 'y': 496, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 438, 'y': 446, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 630, 'y': 421, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 786, 'y': 371, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 978, 'y': 341, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 434, 'y': 470, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 810, 'y': 395, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1134, 'y': 305, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 436, 'y': 495, 'linked_door': 0}],
  'doors': [{'x': 1180, 'y': 263, 'width': 40, 'height': 82}]},
 {'name': 'Split Weave 15',
  'player_start': (70, 560),
  'thread_limit': 1110,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 210, 'y': 520, 'width': 132, 'height': 26},
                {'x': 360, 'y': 590, 'width': 132, 'height': 26},
                {'x': 520, 'y': 455, 'width': 132, 'height': 26},
                {'x': 690, 'y': 560, 'width': 132, 'height': 26},
                {'x': 850, 'y': 415, 'width': 132, 'height': 26},
                {'x': 1010, 'y': 500, 'width': 132, 'height': 26},
                {'x': 1140, 'y': 335, 'width': 132, 'height': 26},
                {'x': 399, 'y': 162, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 729, 'y': 182, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 276, 'y': 429},
                    {'x': 426, 'y': 514},
                    {'x': 586, 'y': 364},
                    {'x': 756, 'y': 484},
                    {'x': 916, 'y': 324},
                    {'x': 1076, 'y': 424},
                    {'x': 1206, 'y': 244},
                    {'x': 424, 'y': 100},
                    {'x': 754, 'y': 120}],
  'hazards': [{'x': 242, 'y': 466, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 404, 'y': 526, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 576, 'y': 401, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 722, 'y': 496, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 894, 'y': 361, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 400, 'y': 548, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 746, 'y': 518, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1050, 'y': 458, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 266, 'y': 478, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 402, 'y': 575, 'linked_door': 0}, {'x': 732, 'y': 545, 'linked_door': 0}],
  'doors': [{'x': 1232, 'y': 253, 'width': 40, 'height': 82}]},
 {'name': 'Split Weave 16',
  'player_start': (70, 560),
  'thread_limit': 1090,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 210, 'y': 516, 'width': 127, 'height': 26},
                {'x': 360, 'y': 586, 'width': 127, 'height': 26},
                {'x': 520, 'y': 451, 'width': 127, 'height': 26},
                {'x': 690, 'y': 556, 'width': 127, 'height': 26},
                {'x': 850, 'y': 411, 'width': 127, 'height': 26},
                {'x': 1010, 'y': 496, 'width': 127, 'height': 26},
                {'x': 1140, 'y': 331, 'width': 127, 'height': 26},
                {'x': 396, 'y': 158, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 726, 'y': 178, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 273, 'y': 425},
                    {'x': 423, 'y': 510},
                    {'x': 583, 'y': 360},
                    {'x': 753, 'y': 480},
                    {'x': 913, 'y': 320},
                    {'x': 1073, 'y': 420},
                    {'x': 1203, 'y': 240},
                    {'x': 421, 'y': 96},
                    {'x': 751, 'y': 116}],
  'hazards': [{'x': 239, 'y': 462, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 401, 'y': 522, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 573, 'y': 397, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 719, 'y': 492, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 891, 'y': 357, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1063, 'y': 432, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 397, 'y': 544, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 743, 'y': 514, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1047, 'y': 454, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 263, 'y': 474, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 399, 'y': 571, 'linked_door': 0}, {'x': 729, 'y': 541, 'linked_door': 0}],
  'doors': [{'x': 1227, 'y': 249, 'width': 40, 'height': 82}]},
 {'name': 'Split Weave 17',
  'player_start': (70, 560),
  'thread_limit': 1070,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 210, 'y': 512, 'width': 122, 'height': 26},
                {'x': 360, 'y': 582, 'width': 122, 'height': 26},
                {'x': 520, 'y': 447, 'width': 122, 'height': 26},
                {'x': 690, 'y': 552, 'width': 122, 'height': 26},
                {'x': 850, 'y': 407, 'width': 122, 'height': 26},
                {'x': 1010, 'y': 492, 'width': 122, 'height': 26},
                {'x': 1140, 'y': 327, 'width': 122, 'height': 26},
                {'x': 394, 'y': 154, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 724, 'y': 174, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 271, 'y': 421},
                    {'x': 421, 'y': 506},
                    {'x': 581, 'y': 356},
                    {'x': 751, 'y': 476},
                    {'x': 911, 'y': 316},
                    {'x': 1071, 'y': 416},
                    {'x': 1201, 'y': 236},
                    {'x': 419, 'y': 92},
                    {'x': 749, 'y': 112}],
  'hazards': [{'x': 237, 'y': 458, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 399, 'y': 518, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 571, 'y': 393, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 717, 'y': 488, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 889, 'y': 353, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1061, 'y': 428, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 395, 'y': 540, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 741, 'y': 510, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1045, 'y': 450, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 261, 'y': 470, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 555, 'y': 405, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 397, 'y': 567, 'linked_door': 0}, {'x': 727, 'y': 537, 'linked_door': 0}],
  'doors': [{'x': 1222, 'y': 245, 'width': 40, 'height': 82}]},
 {'name': 'Split Weave 18',
  'player_start': (70, 560),
  'thread_limit': 1050,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 210, 'y': 508, 'width': 117, 'height': 26},
                {'x': 360, 'y': 578, 'width': 117, 'height': 26},
                {'x': 520, 'y': 443, 'width': 117, 'height': 26},
                {'x': 690, 'y': 548, 'width': 117, 'height': 26},
                {'x': 850, 'y': 403, 'width': 117, 'height': 26},
                {'x': 1010, 'y': 488, 'width': 117, 'height': 26},
                {'x': 1140, 'y': 323, 'width': 117, 'height': 26},
                {'x': 391, 'y': 150, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 721, 'y': 170, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 268, 'y': 417},
                    {'x': 418, 'y': 502},
                    {'x': 578, 'y': 352},
                    {'x': 748, 'y': 472},
                    {'x': 908, 'y': 312},
                    {'x': 1068, 'y': 412},
                    {'x': 1198, 'y': 232},
                    {'x': 416, 'y': 88},
                    {'x': 746, 'y': 108}],
  'hazards': [{'x': 234, 'y': 454, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 396, 'y': 514, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 568, 'y': 389, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 714, 'y': 484, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 886, 'y': 349, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1058, 'y': 424, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1164, 'y': 269, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 392, 'y': 536, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 738, 'y': 506, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1042, 'y': 446, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 258, 'y': 466, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 552, 'y': 401, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 394, 'y': 563, 'linked_door': 0}, {'x': 724, 'y': 533, 'linked_door': 0}],
  'doors': [{'x': 1217, 'y': 241, 'width': 40, 'height': 82}]},
 {'name': 'Split Weave 19',
  'player_start': (70, 560),
  'thread_limit': 1030,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 210, 'y': 504, 'width': 112, 'height': 26},
                {'x': 360, 'y': 574, 'width': 112, 'height': 26},
                {'x': 520, 'y': 439, 'width': 112, 'height': 26},
                {'x': 690, 'y': 544, 'width': 112, 'height': 26},
                {'x': 850, 'y': 399, 'width': 112, 'height': 26},
                {'x': 1010, 'y': 484, 'width': 112, 'height': 26},
                {'x': 1140, 'y': 319, 'width': 112, 'height': 26},
                {'x': 389, 'y': 146, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 719, 'y': 166, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 266, 'y': 413},
                    {'x': 416, 'y': 498},
                    {'x': 576, 'y': 348},
                    {'x': 746, 'y': 468},
                    {'x': 906, 'y': 308},
                    {'x': 1066, 'y': 408},
                    {'x': 1196, 'y': 228},
                    {'x': 414, 'y': 84},
                    {'x': 744, 'y': 104}],
  'hazards': [{'x': 232, 'y': 450, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 394, 'y': 510, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 566, 'y': 385, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 712, 'y': 480, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 884, 'y': 345, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1056, 'y': 420, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1162, 'y': 265, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 390, 'y': 532, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 736, 'y': 502, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1040, 'y': 442, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 256, 'y': 462, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 550, 'y': 397, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 392, 'y': 559, 'linked_door': 0}, {'x': 722, 'y': 529, 'linked_door': 0}],
  'doors': [{'x': 1212, 'y': 237, 'width': 40, 'height': 82}]},
 {'name': 'Split Weave 20',
  'player_start': (70, 560),
  'thread_limit': 1010,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 210, 'y': 500, 'width': 107, 'height': 26},
                {'x': 360, 'y': 570, 'width': 107, 'height': 26},
                {'x': 520, 'y': 435, 'width': 107, 'height': 26},
                {'x': 690, 'y': 540, 'width': 107, 'height': 26},
                {'x': 850, 'y': 395, 'width': 107, 'height': 26},
                {'x': 1010, 'y': 480, 'width': 107, 'height': 26},
                {'x': 1140, 'y': 315, 'width': 107, 'height': 26},
                {'x': 386, 'y': 142, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 716, 'y': 162, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 263, 'y': 409},
                    {'x': 413, 'y': 494},
                    {'x': 573, 'y': 344},
                    {'x': 743, 'y': 464},
                    {'x': 903, 'y': 304},
                    {'x': 1063, 'y': 404},
                    {'x': 1193, 'y': 224},
                    {'x': 411, 'y': 80},
                    {'x': 741, 'y': 100}],
  'hazards': [{'x': 229, 'y': 446, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 391, 'y': 506, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 563, 'y': 381, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 709, 'y': 476, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 881, 'y': 341, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1053, 'y': 416, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1159, 'y': 261, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 241, 'y': 436, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 387, 'y': 528, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 733, 'y': 498, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1037, 'y': 438, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 253, 'y': 458, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 547, 'y': 393, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 893, 'y': 353, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 389, 'y': 555, 'linked_door': 0}, {'x': 719, 'y': 525, 'linked_door': 0}],
  'doors': [{'x': 1207, 'y': 233, 'width': 40, 'height': 82}]},
 {'name': 'Zigzag Rift 21',
  'player_start': (70, 560),
  'thread_limit': 960,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 190, 'y': 555, 'width': 116, 'height': 24},
                {'x': 330, 'y': 470, 'width': 116, 'height': 24},
                {'x': 470, 'y': 590, 'width': 116, 'height': 24},
                {'x': 610, 'y': 430, 'width': 116, 'height': 24},
                {'x': 760, 'y': 560, 'width': 116, 'height': 24},
                {'x': 920, 'y': 385, 'width': 116, 'height': 24},
                {'x': 1080, 'y': 505, 'width': 116, 'height': 24},
                {'x': 1170, 'y': 310, 'width': 116, 'height': 24},
                {'x': 361, 'y': 138, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 641, 'y': 158, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 248, 'y': 460},
                    {'x': 388, 'y': 390},
                    {'x': 528, 'y': 495},
                    {'x': 668, 'y': 350},
                    {'x': 818, 'y': 465},
                    {'x': 978, 'y': 305},
                    {'x': 1138, 'y': 410},
                    {'x': 1228, 'y': 230},
                    {'x': 640, 'y': 180},
                    {'x': 386, 'y': 76},
                    {'x': 666, 'y': 96}],
  'hazards': [{'x': 214, 'y': 501, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 366, 'y': 406, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 518, 'y': 536, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 634, 'y': 366, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 796, 'y': 506, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 968, 'y': 321, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1104, 'y': 451, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 226, 'y': 491, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 362, 'y': 426, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 658, 'y': 386, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 952, 'y': 341, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 238, 'y': 511, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 502, 'y': 546, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 808, 'y': 516, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1112, 'y': 461, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 364, 'y': 455, 'linked_door': 0}, {'x': 644, 'y': 415, 'linked_door': 0}],
  'doors': [{'x': 1246, 'y': 228, 'width': 40, 'height': 82}]},
 {'name': 'Zigzag Rift 22',
  'player_start': (70, 560),
  'thread_limit': 940,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 190, 'y': 550, 'width': 112, 'height': 24},
                {'x': 330, 'y': 465, 'width': 112, 'height': 24},
                {'x': 470, 'y': 585, 'width': 112, 'height': 24},
                {'x': 610, 'y': 425, 'width': 112, 'height': 24},
                {'x': 760, 'y': 555, 'width': 112, 'height': 24},
                {'x': 920, 'y': 380, 'width': 112, 'height': 24},
                {'x': 1080, 'y': 500, 'width': 112, 'height': 24},
                {'x': 1170, 'y': 305, 'width': 112, 'height': 24},
                {'x': 359, 'y': 134, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 639, 'y': 154, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 949, 'y': 174, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 246, 'y': 455},
                    {'x': 386, 'y': 385},
                    {'x': 526, 'y': 490},
                    {'x': 666, 'y': 345},
                    {'x': 816, 'y': 460},
                    {'x': 976, 'y': 300},
                    {'x': 1136, 'y': 405},
                    {'x': 1226, 'y': 225},
                    {'x': 640, 'y': 180},
                    {'x': 384, 'y': 72},
                    {'x': 664, 'y': 92},
                    {'x': 974, 'y': 112}],
  'hazards': [{'x': 212, 'y': 496, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 364, 'y': 401, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 516, 'y': 531, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 632, 'y': 361, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 794, 'y': 501, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 966, 'y': 316, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1102, 'y': 446, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1204, 'y': 241, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 236, 'y': 496, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 360, 'y': 421, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 656, 'y': 381, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 950, 'y': 336, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1216, 'y': 261, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 360, 'y': 421, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 656, 'y': 381, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 950, 'y': 336, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 362, 'y': 450, 'linked_door': 0},
              {'x': 642, 'y': 410, 'linked_door': 0},
              {'x': 952, 'y': 365, 'linked_door': 0}],
  'doors': [{'x': 1242, 'y': 223, 'width': 40, 'height': 82}]},
 {'name': 'Zigzag Rift 23',
  'player_start': (70, 560),
  'thread_limit': 920,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 190, 'y': 545, 'width': 108, 'height': 24},
                {'x': 330, 'y': 460, 'width': 108, 'height': 24},
                {'x': 470, 'y': 580, 'width': 108, 'height': 24},
                {'x': 610, 'y': 420, 'width': 108, 'height': 24},
                {'x': 760, 'y': 550, 'width': 108, 'height': 24},
                {'x': 920, 'y': 375, 'width': 108, 'height': 24},
                {'x': 1080, 'y': 495, 'width': 108, 'height': 24},
                {'x': 1170, 'y': 300, 'width': 108, 'height': 24},
                {'x': 357, 'y': 130, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 637, 'y': 150, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 947, 'y': 170, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 244, 'y': 450},
                    {'x': 384, 'y': 380},
                    {'x': 524, 'y': 485},
                    {'x': 664, 'y': 340},
                    {'x': 814, 'y': 455},
                    {'x': 974, 'y': 295},
                    {'x': 1134, 'y': 400},
                    {'x': 1224, 'y': 220},
                    {'x': 640, 'y': 180},
                    {'x': 382, 'y': 68},
                    {'x': 662, 'y': 88},
                    {'x': 972, 'y': 108}],
  'hazards': [{'x': 210, 'y': 491, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 362, 'y': 396, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 514, 'y': 526, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 630, 'y': 356, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 792, 'y': 496, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 964, 'y': 311, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1100, 'y': 441, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1202, 'y': 236, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 234, 'y': 491, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 358, 'y': 416, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 654, 'y': 376, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 948, 'y': 331, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1214, 'y': 256, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 358, 'y': 416, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 654, 'y': 376, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 948, 'y': 331, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1214, 'y': 256, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 360, 'y': 445, 'linked_door': 0},
              {'x': 640, 'y': 405, 'linked_door': 0},
              {'x': 950, 'y': 360, 'linked_door': 0}],
  'doors': [{'x': 1238, 'y': 218, 'width': 40, 'height': 82}]},
 {'name': 'Zigzag Rift 24',
  'player_start': (70, 560),
  'thread_limit': 900,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 190, 'y': 540, 'width': 104, 'height': 24},
                {'x': 330, 'y': 455, 'width': 104, 'height': 24},
                {'x': 470, 'y': 575, 'width': 104, 'height': 24},
                {'x': 610, 'y': 415, 'width': 104, 'height': 24},
                {'x': 760, 'y': 545, 'width': 104, 'height': 24},
                {'x': 920, 'y': 370, 'width': 104, 'height': 24},
                {'x': 1080, 'y': 490, 'width': 104, 'height': 24},
                {'x': 1170, 'y': 295, 'width': 104, 'height': 24},
                {'x': 355, 'y': 126, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 635, 'y': 146, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 945, 'y': 166, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 242, 'y': 445},
                    {'x': 382, 'y': 375},
                    {'x': 522, 'y': 480},
                    {'x': 662, 'y': 335},
                    {'x': 812, 'y': 450},
                    {'x': 972, 'y': 290},
                    {'x': 1132, 'y': 395},
                    {'x': 1222, 'y': 215},
                    {'x': 640, 'y': 180},
                    {'x': 380, 'y': 64},
                    {'x': 660, 'y': 84},
                    {'x': 970, 'y': 104}],
  'hazards': [{'x': 208, 'y': 486, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 360, 'y': 391, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 512, 'y': 521, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 628, 'y': 351, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 790, 'y': 491, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 962, 'y': 306, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1098, 'y': 436, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1200, 'y': 231, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 232, 'y': 486, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 356, 'y': 411, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 652, 'y': 371, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 946, 'y': 326, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1212, 'y': 251, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 356, 'y': 411, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 652, 'y': 371, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 946, 'y': 326, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1212, 'y': 251, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 358, 'y': 440, 'linked_door': 0},
              {'x': 638, 'y': 400, 'linked_door': 0},
              {'x': 948, 'y': 355, 'linked_door': 0}],
  'doors': [{'x': 1234, 'y': 213, 'width': 40, 'height': 82}]},
 {'name': 'Zigzag Rift 25',
  'player_start': (70, 560),
  'thread_limit': 880,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 190, 'y': 535, 'width': 100, 'height': 24},
                {'x': 330, 'y': 450, 'width': 100, 'height': 24},
                {'x': 470, 'y': 570, 'width': 100, 'height': 24},
                {'x': 610, 'y': 410, 'width': 100, 'height': 24},
                {'x': 760, 'y': 540, 'width': 100, 'height': 24},
                {'x': 920, 'y': 365, 'width': 100, 'height': 24},
                {'x': 1080, 'y': 485, 'width': 100, 'height': 24},
                {'x': 1170, 'y': 290, 'width': 100, 'height': 24},
                {'x': 353, 'y': 122, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 633, 'y': 142, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 943, 'y': 162, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 240, 'y': 440},
                    {'x': 380, 'y': 370},
                    {'x': 520, 'y': 475},
                    {'x': 660, 'y': 330},
                    {'x': 810, 'y': 445},
                    {'x': 970, 'y': 285},
                    {'x': 1130, 'y': 390},
                    {'x': 1220, 'y': 210},
                    {'x': 640, 'y': 180},
                    {'x': 378, 'y': 60},
                    {'x': 658, 'y': 80},
                    {'x': 968, 'y': 100}],
  'hazards': [{'x': 206, 'y': 481, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 358, 'y': 386, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 510, 'y': 516, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 626, 'y': 346, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 788, 'y': 486, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 960, 'y': 301, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1096, 'y': 431, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1198, 'y': 226, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 230, 'y': 481, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 354, 'y': 406, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 650, 'y': 366, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 944, 'y': 321, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1210, 'y': 246, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 354, 'y': 406, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 650, 'y': 366, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 944, 'y': 321, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1210, 'y': 246, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 356, 'y': 435, 'linked_door': 0},
              {'x': 636, 'y': 395, 'linked_door': 0},
              {'x': 946, 'y': 350, 'linked_door': 0}],
  'doors': [{'x': 1230, 'y': 208, 'width': 40, 'height': 82}]},
 {'name': 'Zigzag Rift 26',
  'player_start': (70, 560),
  'thread_limit': 860,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 190, 'y': 530, 'width': 96, 'height': 24},
                {'x': 330, 'y': 445, 'width': 96, 'height': 24},
                {'x': 470, 'y': 565, 'width': 96, 'height': 24},
                {'x': 610, 'y': 405, 'width': 96, 'height': 24},
                {'x': 760, 'y': 535, 'width': 96, 'height': 24},
                {'x': 920, 'y': 360, 'width': 96, 'height': 24},
                {'x': 1080, 'y': 480, 'width': 96, 'height': 24},
                {'x': 1170, 'y': 285, 'width': 96, 'height': 24},
                {'x': 351, 'y': 118, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 631, 'y': 138, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 941, 'y': 158, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 238, 'y': 435},
                    {'x': 378, 'y': 365},
                    {'x': 518, 'y': 470},
                    {'x': 658, 'y': 325},
                    {'x': 808, 'y': 440},
                    {'x': 968, 'y': 280},
                    {'x': 1128, 'y': 385},
                    {'x': 1218, 'y': 205},
                    {'x': 640, 'y': 180},
                    {'x': 376, 'y': 56},
                    {'x': 656, 'y': 76},
                    {'x': 966, 'y': 96}],
  'hazards': [{'x': 204, 'y': 476, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 356, 'y': 381, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 508, 'y': 511, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 624, 'y': 341, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 786, 'y': 481, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 958, 'y': 296, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1094, 'y': 426, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1196, 'y': 221, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 228, 'y': 476, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 352, 'y': 401, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 648, 'y': 361, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 942, 'y': 316, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1208, 'y': 241, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 352, 'y': 401, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 648, 'y': 361, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 942, 'y': 316, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1208, 'y': 241, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 354, 'y': 430, 'linked_door': 0},
              {'x': 634, 'y': 390, 'linked_door': 0},
              {'x': 944, 'y': 345, 'linked_door': 0}],
  'doors': [{'x': 1226, 'y': 203, 'width': 40, 'height': 82}]},
 {'name': 'Chaos Loom 27',
  'player_start': (70, 560),
  'thread_limit': 810,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 160, 'y': 575, 'width': 94, 'height': 22},
                {'x': 270, 'y': 525, 'width': 94, 'height': 22},
                {'x': 390, 'y': 490, 'width': 94, 'height': 22},
                {'x': 510, 'y': 435, 'width': 94, 'height': 22},
                {'x': 640, 'y': 405, 'width': 94, 'height': 22},
                {'x': 770, 'y': 355, 'width': 94, 'height': 22},
                {'x': 900, 'y': 330, 'width': 94, 'height': 22},
                {'x': 1030, 'y': 285, 'width': 94, 'height': 22},
                {'x': 1140, 'y': 265, 'width': 94, 'height': 22},
                {'x': 290, 'y': 114, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 530, 'y': 134, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 790, 'y': 154, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 207, 'y': 476},
                    {'x': 317, 'y': 441},
                    {'x': 437, 'y': 391},
                    {'x': 557, 'y': 351},
                    {'x': 687, 'y': 306},
                    {'x': 817, 'y': 271},
                    {'x': 947, 'y': 231},
                    {'x': 1077, 'y': 201},
                    {'x': 1187, 'y': 166},
                    {'x': 640, 'y': 180},
                    {'x': 930, 'y': 145},
                    {'x': 315, 'y': 52},
                    {'x': 555, 'y': 72},
                    {'x': 815, 'y': 92}],
  'hazards': [{'x': 173, 'y': 521, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 295, 'y': 461, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 427, 'y': 436, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 523, 'y': 371, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 665, 'y': 351, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 807, 'y': 291, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 913, 'y': 276, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1055, 'y': 221, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1177, 'y': 211, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 291, 'y': 479, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 547, 'y': 389, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 791, 'y': 309, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1067, 'y': 239, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 181, 'y': 529, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 427, 'y': 444, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 661, 'y': 359, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 937, 'y': 284, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 293, 'y': 510, 'linked_door': 0},
              {'x': 533, 'y': 420, 'linked_door': 0},
              {'x': 793, 'y': 340, 'linked_door': 0}],
  'doors': [{'x': 1194, 'y': 183, 'width': 40, 'height': 82}]},
 {'name': 'Chaos Loom 28',
  'player_start': (70, 560),
  'thread_limit': 790,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 160, 'y': 571, 'width': 91, 'height': 22},
                {'x': 270, 'y': 521, 'width': 91, 'height': 22},
                {'x': 390, 'y': 486, 'width': 91, 'height': 22},
                {'x': 510, 'y': 431, 'width': 91, 'height': 22},
                {'x': 640, 'y': 401, 'width': 91, 'height': 22},
                {'x': 770, 'y': 351, 'width': 91, 'height': 22},
                {'x': 900, 'y': 326, 'width': 91, 'height': 22},
                {'x': 1030, 'y': 281, 'width': 91, 'height': 22},
                {'x': 1140, 'y': 261, 'width': 91, 'height': 22},
                {'x': 288, 'y': 110, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 528, 'y': 130, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 788, 'y': 150, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 205, 'y': 472},
                    {'x': 315, 'y': 437},
                    {'x': 435, 'y': 387},
                    {'x': 555, 'y': 347},
                    {'x': 685, 'y': 302},
                    {'x': 815, 'y': 267},
                    {'x': 945, 'y': 227},
                    {'x': 1075, 'y': 197},
                    {'x': 1185, 'y': 162},
                    {'x': 640, 'y': 180},
                    {'x': 930, 'y': 145},
                    {'x': 313, 'y': 52},
                    {'x': 553, 'y': 68},
                    {'x': 813, 'y': 88}],
  'hazards': [{'x': 171, 'y': 517, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 293, 'y': 457, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 425, 'y': 432, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 521, 'y': 367, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 663, 'y': 347, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 805, 'y': 287, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 911, 'y': 272, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1053, 'y': 217, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1175, 'y': 207, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 289, 'y': 475, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 545, 'y': 385, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 789, 'y': 305, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1065, 'y': 235, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 179, 'y': 525, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 425, 'y': 440, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 659, 'y': 355, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 935, 'y': 280, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 291, 'y': 506, 'linked_door': 0},
              {'x': 531, 'y': 416, 'linked_door': 0},
              {'x': 791, 'y': 336, 'linked_door': 0}],
  'doors': [{'x': 1191, 'y': 179, 'width': 40, 'height': 82}]},
 {'name': 'Chaos Loom 29',
  'player_start': (70, 560),
  'thread_limit': 770,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 160, 'y': 567, 'width': 88, 'height': 22},
                {'x': 270, 'y': 517, 'width': 88, 'height': 22},
                {'x': 390, 'y': 482, 'width': 88, 'height': 22},
                {'x': 510, 'y': 427, 'width': 88, 'height': 22},
                {'x': 640, 'y': 397, 'width': 88, 'height': 22},
                {'x': 770, 'y': 347, 'width': 88, 'height': 22},
                {'x': 900, 'y': 322, 'width': 88, 'height': 22},
                {'x': 1030, 'y': 277, 'width': 88, 'height': 22},
                {'x': 1140, 'y': 257, 'width': 88, 'height': 22},
                {'x': 287, 'y': 106, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 527, 'y': 126, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 787, 'y': 146, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 204, 'y': 468},
                    {'x': 314, 'y': 433},
                    {'x': 434, 'y': 383},
                    {'x': 554, 'y': 343},
                    {'x': 684, 'y': 298},
                    {'x': 814, 'y': 263},
                    {'x': 944, 'y': 223},
                    {'x': 1074, 'y': 193},
                    {'x': 1184, 'y': 158},
                    {'x': 640, 'y': 180},
                    {'x': 930, 'y': 145},
                    {'x': 312, 'y': 52},
                    {'x': 552, 'y': 64},
                    {'x': 812, 'y': 84}],
  'hazards': [{'x': 170, 'y': 513, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 292, 'y': 453, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 424, 'y': 428, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 520, 'y': 363, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 662, 'y': 343, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 804, 'y': 283, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 910, 'y': 268, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1052, 'y': 213, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1174, 'y': 203, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 288, 'y': 471, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 544, 'y': 381, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 788, 'y': 301, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1064, 'y': 231, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 178, 'y': 521, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 424, 'y': 436, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 658, 'y': 351, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 934, 'y': 276, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 290, 'y': 502, 'linked_door': 0},
              {'x': 530, 'y': 412, 'linked_door': 0},
              {'x': 790, 'y': 332, 'linked_door': 0}],
  'doors': [{'x': 1188, 'y': 175, 'width': 40, 'height': 82}]},
 {'name': 'Chaos Loom 30',
  'player_start': (70, 560),
  'thread_limit': 750,
  'platforms': [{'x': 35, 'y': 620, 'width': 180, 'height': 30},
                {'x': 160, 'y': 563, 'width': 85, 'height': 22},
                {'x': 270, 'y': 513, 'width': 85, 'height': 22},
                {'x': 390, 'y': 478, 'width': 85, 'height': 22},
                {'x': 510, 'y': 423, 'width': 85, 'height': 22},
                {'x': 640, 'y': 393, 'width': 85, 'height': 22},
                {'x': 770, 'y': 343, 'width': 85, 'height': 22},
                {'x': 900, 'y': 318, 'width': 85, 'height': 22},
                {'x': 1030, 'y': 273, 'width': 85, 'height': 22},
                {'x': 1140, 'y': 253, 'width': 85, 'height': 22},
                {'x': 285, 'y': 102, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 525, 'y': 122, 'width': 58, 'height': 24, 'type': 'movable'},
                {'x': 785, 'y': 142, 'width': 58, 'height': 24, 'type': 'movable'}],
  'stitch_points': [{'x': 105, 'y': 545},
                    {'x': 202, 'y': 464},
                    {'x': 312, 'y': 429},
                    {'x': 432, 'y': 379},
                    {'x': 552, 'y': 339},
                    {'x': 682, 'y': 294},
                    {'x': 812, 'y': 259},
                    {'x': 942, 'y': 219},
                    {'x': 1072, 'y': 189},
                    {'x': 1182, 'y': 154},
                    {'x': 640, 'y': 180},
                    {'x': 930, 'y': 145},
                    {'x': 310, 'y': 52},
                    {'x': 550, 'y': 60},
                    {'x': 810, 'y': 80}],
  'hazards': [{'x': 168, 'y': 509, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 290, 'y': 449, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 422, 'y': 424, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 518, 'y': 359, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 660, 'y': 339, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 802, 'y': 279, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 908, 'y': 264, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1050, 'y': 209, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 1172, 'y': 199, 'width': 44, 'height': 44, 'type': 'scissors'},
              {'x': 286, 'y': 467, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 542, 'y': 377, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 786, 'y': 297, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 1062, 'y': 227, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 176, 'y': 517, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 422, 'y': 432, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 656, 'y': 347, 'width': 38, 'height': 38, 'type': 'flame'},
              {'x': 932, 'y': 272, 'width': 38, 'height': 38, 'type': 'flame'}],
  'buttons': [{'x': 288, 'y': 498, 'linked_door': 0},
              {'x': 528, 'y': 408, 'linked_door': 0},
              {'x': 788, 'y': 328, 'linked_door': 0}],
  'doors': [{'x': 1185, 'y': 171, 'width': 40, 'height': 82}]}]
)



def get_level(level_index):
    """Get a level by index"""
    if 0 <= level_index < len(LEVELS):
        return Level(LEVELS[level_index])
    return None

def get_level_count():
    """Get total number of levels"""
    return len(LEVELS)