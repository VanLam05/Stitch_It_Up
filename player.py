# ============================================================
# STITCH IT UP - Player Class
# Handles player movement, physics, and state
# ============================================================

import pygame
import math
try:
    from .constants import *
except ImportError:
    from constants import *

class Player:
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
        # Draw a needle-like character: thin body, center hole, side eyes, mouth below.
        body_width = max(14, int(self.width * 0.55))
        body_height = int(self.height * 1.2)
        body_x = int(self.x + (self.width - body_width) / 2)
        body_y = int(self.y - (body_height - self.height) * 0.2)
        center_x = body_x + body_width // 2

        body_rect = pygame.Rect(body_x, body_y, body_width, body_height)

        # Shadow
        shadow_rect = pygame.Rect(body_x + 3, body_y + 3, body_width, body_height)
        pygame.draw.rect(screen, (20, 20, 30), shadow_rect, border_radius=body_width // 2)

        # Needle shaft
        pygame.draw.rect(screen, COLORS['needle'], body_rect, border_radius=body_width // 2)
        pygame.draw.rect(screen, COLORS['player_outline'], body_rect, 2, border_radius=body_width // 2)

        # Tip and eye-end cap to make body look longer and sharper
        tip = [(center_x, body_y - 8), (body_x + 3, body_y + 7), (body_x + body_width - 3, body_y + 7)]
        pygame.draw.polygon(screen, COLORS['needle_tip'], tip)
        pygame.draw.polygon(screen, COLORS['player_outline'], tip, 2)
        pygame.draw.ellipse(
            screen,
            COLORS['needle'],
            (body_x + 2, body_y + body_height - 8, body_width - 4, 12),
        )

        # Needle hole in the middle (eye of needle)
        hole_center = (center_x, int(body_y + body_height * 0.42))
        hole_outer = max(5, body_width // 2 - 1)
        hole_inner = max(3, hole_outer - 2)
        pygame.draw.circle(screen, COLORS['player_outline'], hole_center, hole_outer, 2)
        pygame.draw.circle(screen, COLORS['background'], hole_center, hole_inner)

        # Eyes on two sides of the hole
        eye_y = hole_center[1]
        side_offset = hole_outer + 5
        left_eye = (center_x - side_offset, eye_y)
        right_eye = (center_x + side_offset, eye_y)
        pupil_shift = 1 if self.facing_right else -1
        for ex, ey in (left_eye, right_eye):
            pygame.draw.circle(screen, (255, 255, 255), (int(ex), int(ey)), 4)
            pygame.draw.circle(screen, (20, 20, 20), (int(ex + pupil_shift), int(ey)), 2)

        # Mouth right under the hole
        mouth_rect = pygame.Rect(center_x - 8, hole_center[1] + 8, 16, 8)
        pygame.draw.arc(screen, (40, 40, 40), mouth_rect, math.radians(20), math.radians(160), 2)

        # Small highlight line on the shaft
        pygame.draw.line(
            screen,
            (235, 235, 235),
            (body_x + 4, body_y + 10),
            (body_x + 4, body_y + body_height - 16),
            1,
        )
            
    def check_hazard_collision(self, hazards):
        """Check if player touches any hazard"""
        player_rect = self.rect
        for hazard in hazards:
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
