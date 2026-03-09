# ============================================================
# STITCH IT UP - Player Class
# Handles player movement, physics, and state
# ============================================================

import pygame
import math
import os
import re
try:
    from .constants import *
except ImportError:
    from constants import *

class Player:
    _kim_frames = []
    _kim_frame_ms = 110

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.vel_x = 0
        self.vel_y = 0
        
        # States
        self.on_ground = False
        self.is_swinging = False
        self.swing_anchor = None
        self.swing_length = 0
        self.swing_angle = 0
        self.swing_angular_vel = 0
        
        # Jump responsiveness
        self.coyote_time = 0  # Frames since leaving ground (can still jump)
        self.coyote_time_max = 8  # Allow jump within 8 frames of leaving ground
        self.jump_buffer = 0  # Frames since jump was pressed
        self.jump_buffer_max = 10  # Remember jump input for 10 frames
        
        # Visual
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        
        # On bridge/trampoline
        self.on_bridge = False

        # Load animated needle frames once and reuse for all player instances.
        if not Player._kim_frames:
            self._load_kim_sprite()

    @classmethod
    def _load_kim_sprite(cls):
        """Load needle animation frames from assets/KIM folder."""
        folder_path = os.path.join(os.path.dirname(__file__), "assets", "KIM")
        try:
            files = [
                f for f in os.listdir(folder_path)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
            ]

            # Sort naturally: Kim_1, Kim_2, ... Kim_10
            def natural_key(name):
                return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]

            files.sort(key=natural_key)
            cls._kim_frames = []
            for filename in files:
                path = os.path.join(folder_path, filename)
                cls._kim_frames.append(pygame.image.load(path).convert_alpha())
        except (pygame.error, FileNotFoundError):
            cls._kim_frames = []
        
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def feet_pos(self):
        return (self.x + self.width // 2, self.y + self.height)
    
    def handle_input(self, keys_pressed):
        """Process player input for movement"""
        if self.is_swinging:
            # Swing controls
            for key in KEYS['left']:
                if keys_pressed[key]:
                    self.swing_angular_vel -= GRAPPLE_SWING_SPEED
            for key in KEYS['right']:
                if keys_pressed[key]:
                    self.swing_angular_vel += GRAPPLE_SWING_SPEED
            return
        
        # Normal movement
        moving = False
        for key in KEYS['left']:
            if keys_pressed[key]:
                self.vel_x = -PLAYER_SPEED
                self.facing_right = False
                moving = True
                break
        
        if not moving:
            for key in KEYS['right']:
                if keys_pressed[key]:
                    self.vel_x = PLAYER_SPEED
                    self.facing_right = True
                    moving = True
                    break
        
        if not moving:
            self.vel_x *= FRICTION
            if abs(self.vel_x) < 0.1:
                self.vel_x = 0
    
    def jump(self):
        """Make player jump - uses coyote time for better feel"""
        can_jump = self.on_ground or self.coyote_time > 0
        
        if can_jump:
            self.vel_y = PLAYER_JUMP_FORCE
            self.on_ground = False
            self.coyote_time = 0
            self.jump_buffer = 0
            return True
        else:
            # Buffer the jump input for later
            self.jump_buffer = self.jump_buffer_max
        return False
    
    def start_swing(self, anchor_point):
        """Start swinging from an anchor point"""
        self.is_swinging = True
        self.swing_anchor = anchor_point
        
        # Calculate initial swing parameters
        dx = self.center[0] - anchor_point[0]
        dy = self.center[1] - anchor_point[1]
        self.swing_length = math.sqrt(dx**2 + dy**2)
        self.swing_angle = math.atan2(dx, dy)
        
        # Convert current velocity to angular velocity
        tangent_vel = self.vel_x * math.cos(self.swing_angle) - self.vel_y * math.sin(self.swing_angle)
        self.swing_angular_vel = tangent_vel / max(self.swing_length, 1) * 0.1
        
    def stop_swing(self):
        """Stop swinging and convert to normal physics"""
        if self.is_swinging:
            # Convert angular velocity back to linear velocity
            self.vel_x = self.swing_angular_vel * self.swing_length * math.cos(self.swing_angle) * 0.5
            self.vel_y = self.swing_angular_vel * self.swing_length * math.sin(self.swing_angle) * 0.3
            
        self.is_swinging = False
        self.swing_anchor = None
        
    def update(self, platforms, bridges=None):
        """Update player physics and position"""
        if self.is_swinging:
            self._update_swing()
        else:
            self._update_normal(platforms, bridges)
        
        # Update coyote time
        if self.on_ground:
            self.coyote_time = self.coyote_time_max
        elif self.coyote_time > 0:
            self.coyote_time -= 1
            
        # Update jump buffer and auto-jump if buffered
        if self.jump_buffer > 0:
            self.jump_buffer -= 1
            if self.on_ground:
                # Execute buffered jump
                self.vel_y = PLAYER_JUMP_FORCE
                self.on_ground = False
                self.jump_buffer = 0
                self.coyote_time = 0
        
        # Animation
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
            
    def _update_swing(self):
        """Update pendulum swing physics"""
        if not self.swing_anchor:
            self.stop_swing()
            return
            
        # Pendulum physics
        gravity_effect = GRAVITY * math.sin(self.swing_angle) / max(self.swing_length, 1) * 0.5
        self.swing_angular_vel += gravity_effect
        self.swing_angular_vel *= 0.995  # Damping
        self.swing_angle += self.swing_angular_vel
        
        # Update position based on swing
        self.x = self.swing_anchor[0] + math.sin(self.swing_angle) * self.swing_length - self.width // 2
        self.y = self.swing_anchor[1] + math.cos(self.swing_angle) * self.swing_length - self.height // 2
        
    def _update_normal(self, platforms, bridges=None):
        """Update normal physics with gravity and collisions"""
        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED
            
        # Move horizontally
        self.x += self.vel_x
        self._check_horizontal_collision(platforms)
        
        # Move vertically
        self.y += self.vel_y
        self.on_ground = False
        self.on_bridge = False
        self._check_vertical_collision(platforms)
        
        # Check bridge collisions
        if bridges:
            self._check_bridge_collision(bridges)
            
    def _check_horizontal_collision(self, platforms):
        """Check and resolve horizontal collisions"""
        player_rect = self.rect
        for platform in platforms:
            if player_rect.colliderect(platform.rect):
                if self.vel_x > 0:  # Moving right
                    self.x = platform.rect.left - self.width
                elif self.vel_x < 0:  # Moving left
                    self.x = platform.rect.right
                self.vel_x = 0
                
    def _check_vertical_collision(self, platforms):
        """Check and resolve vertical collisions"""
        player_rect = self.rect
        for platform in platforms:
            if player_rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling
                    self.y = platform.rect.top - self.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # Jumping up
                    self.y = platform.rect.bottom
                    self.vel_y = 0
                    
    def _check_bridge_collision(self, bridges):
        """Check collision with thread bridges"""
        player_feet = pygame.Rect(self.x, self.y + self.height - 10, self.width, 10)
        
        for bridge in bridges:
            if bridge.active and bridge.is_bridge:
                # Check if player is above the bridge line
                if self._is_on_bridge_line(bridge):
                    if self.vel_y > 0:  # Only when falling
                        if bridge.is_trampoline:
                            self.vel_y = TRAMPOLINE_BOUNCE_FORCE
                        else:
                            self.vel_y = 0
                            self.on_ground = True
                        self.on_bridge = True
                        self.y = bridge.get_y_at_x(self.center[0]) - self.height
                        
    def _is_on_bridge_line(self, bridge):
        """Check if player is touching a bridge line"""
        px, py = self.center[0], self.y + self.height
        
        # Get bridge endpoints
        x1, y1 = bridge.point_a
        x2, y2 = bridge.point_b
        
        # Check if player x is between bridge endpoints
        if not (min(x1, x2) <= px <= max(x1, x2)):
            return False
            
        # Calculate expected y on bridge line
        if x2 - x1 != 0:
            t = (px - x1) / (x2 - x1)
            expected_y = y1 + t * (y2 - y1)
            
            # Check if player feet are near the line
            return abs(py - expected_y) < 15 and self.vel_y >= 0
        return False
    
    def bounce(self, force=BRIDGE_BOUNCE_FORCE):
        """Apply bounce force"""
        self.vel_y = force
        self.on_ground = False
        
    def draw(self, screen):
        """Draw the player"""
        if Player._kim_frames:
            # Keep sprite larger than collision box so the needle remains readable.
            target_h = int(self.height * 2.5)
            current_frame = (pygame.time.get_ticks() // Player._kim_frame_ms) % len(Player._kim_frames)
            base_image = Player._kim_frames[current_frame]
            aspect = base_image.get_width() / max(1, base_image.get_height())
            target_w = int(target_h * aspect)

            sprite = pygame.transform.smoothscale(base_image, (target_w, target_h))

            # Optional horizontal flip to follow movement direction.
            if not self.facing_right:
                sprite = pygame.transform.flip(sprite, True, False)

            draw_x = int(self.x + self.width // 2 - target_w // 2)
            # Align sprite bottom with collision-box bottom so the tip matches ground contact.
            draw_y = int(self.y + self.height - target_h)
            screen.blit(sprite, (draw_x, draw_y))
            return

        # Fallback if image is unavailable.
        pygame.draw.rect(screen, COLORS['needle'], self.rect, border_radius=6)
            
    def check_hazard_collision(self, hazards, hazard_types=None):
        """Check if player touches hazards, optionally filtered by hazard type."""
        player_rect = self.rect
        for hazard in hazards:
            if hazard_types and hazard.hazard_type not in hazard_types:
                continue
            if player_rect.colliderect(hazard.rect):
                return True
        return False
    
    def check_void(self, screen_height):
        """Check if player fell into void"""
        return self.y > screen_height + 100
    
    def reset(self, x, y):
        """Reset player to starting position"""
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.is_swinging = False
        self.swing_anchor = None
        self.coyote_time = 0
        self.jump_buffer = 0