# ============================================================
# STITCH IT UP - Needle & Thread System
# Core mechanics for shooting, stitching, and grappling
# ============================================================

import pygame
import math
try:
    from .constants import *
except ImportError:
    from constants import *

class Needle:
    """The main tool - thrown to create stitch points"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.vel_x = 0
        self.vel_y = 0
        self.angle = 0
        self.active = False  # Is needle flying through air
        self.embedded = False  # Is needle stuck in something
        self.embed_point = None  # Where needle is stuck
        self.origin_point = None  # Where needle was thrown from
        self.length = 25
        self.width = 4
        
    @property
    def tip_position(self):
        """Get the tip of the needle"""
        return (
            self.x + math.cos(self.angle) * self.length,
            self.y + math.sin(self.angle) * self.length
        )
    
    @property
    def base_position(self):
        """Get the base of the needle (where thread attaches)"""
        return (self.x, self.y)
    
    def shoot(self, start_pos, target_pos):
        """Launch needle towards target"""
        self.x, self.y = start_pos
        self.origin_point = start_pos
        
        # Calculate direction
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.vel_x = (dx / distance) * NEEDLE_SPEED
            self.vel_y = (dy / distance) * NEEDLE_SPEED
            self.angle = math.atan2(dy, dx)
        
        self.active = True
        self.embedded = False
        self.embed_point = None
        
    def update(self, stitch_points, platforms):
        """Update needle position and check for hits"""
        if not self.active:
            return None

        prev_tip = self.tip_position
            
        # Move needle
        self.x += self.vel_x
        self.y += self.vel_y

        current_tip = self.tip_position
        
        # Check distance traveled
        if self.origin_point:
            dx = self.x - self.origin_point[0]
            dy = self.y - self.origin_point[1]
            distance = math.sqrt(dx**2 + dy**2)
            if distance > NEEDLE_MAX_DISTANCE:
                self.recall()
                return None
        
        # Check first collision along travel segment.
        hit = self._check_first_collision(prev_tip, current_tip, stitch_points, platforms)
        if hit:
            hit_type, hit_object, hit_pos = hit
            if hit_type == 'stitch_point':
                self.embed(hit_object.center)
                return ('stitch_point', hit_object)

            self.embed(hit_pos)
            return ('platform', hit_object)
            
        return None
    
    def _check_stitch_collision(self, stitch_points):
        """Check if needle hit a stitch point"""
        tip_x, tip_y = self.tip_position
        for sp in stitch_points:
            if sp.active:
                dx = tip_x - sp.center[0]
                dy = tip_y - sp.center[1]
                distance = math.sqrt(dx**2 + dy**2)
                if distance < sp.radius + 5:
                    return sp
        return None
    
    def _check_platform_collision(self, platforms):
        """Check if needle hit a platform"""
        tip_x, tip_y = self.tip_position
        needle_rect = pygame.Rect(tip_x - 2, tip_y - 2, 4, 4)
        for platform in platforms:
            if not getattr(platform, 'is_movable', False):
                continue
            if needle_rect.colliderect(platform.rect):
                return platform
        return None

    def _check_first_collision(self, start_tip, end_tip, stitch_points, platforms):
        """Return the first object hit along the needle segment this frame."""
        sx, sy = start_tip
        ex, ey = end_tip
        dx = ex - sx
        dy = ey - sy
        seg_len_sq = dx * dx + dy * dy
        seg_len = math.sqrt(seg_len_sq)

        if seg_len_sq == 0:
            return None

        best_t = 2.0
        best_hit = None

        # Stitch-point test using closest point on movement segment.
        for sp in stitch_points:
            if not sp.active:
                continue

            cx, cy = sp.center
            t = ((cx - sx) * dx + (cy - sy) * dy) / seg_len_sq
            t = max(0.0, min(1.0, t))
            closest_x = sx + t * dx
            closest_y = sy + t * dy
            dist = math.sqrt((cx - closest_x) ** 2 + (cy - closest_y) ** 2)

            if dist <= sp.radius + 5 and t < best_t:
                best_t = t
                best_hit = ('stitch_point', sp, (closest_x, closest_y))

        # Platform test using line-rect clip intersection.
        for platform in platforms:
            # Do not attach thread to normal path platforms.
            if not getattr(platform, 'is_movable', False):
                continue

            clipped = platform.rect.clipline((sx, sy), (ex, ey))
            if not clipped:
                continue

            if len(clipped) == 2 and isinstance(clipped[0], (tuple, list)):
                p1, p2 = clipped
            else:
                p1 = (clipped[0], clipped[1])
                p2 = (clipped[2], clipped[3])

            d1 = math.sqrt((p1[0] - sx) ** 2 + (p1[1] - sy) ** 2)
            d2 = math.sqrt((p2[0] - sx) ** 2 + (p2[1] - sy) ** 2)
            entry = p1 if d1 <= d2 else p2
            t = (math.sqrt((entry[0] - sx) ** 2 + (entry[1] - sy) ** 2) / seg_len)

            if t < best_t:
                best_t = t
                best_hit = ('platform', platform, entry)

        return best_hit
    
    def embed(self, point):
        """Embed needle at a point"""
        self.active = False
        self.embedded = True
        self.embed_point = point
        self.x, self.y = point
        
    def recall(self):
        """Recall the needle back"""
        self.active = False
        self.embedded = False
        self.embed_point = None
        self.origin_point = None
        
    def draw(self, screen):
        """Draw the needle"""
        if not self.active and not self.embedded:
            return
            
        # Needle body
        base = self.base_position
        tip = self.tip_position
        
        # Draw needle shaft
        pygame.draw.line(screen, COLORS['needle'], base, tip, self.width)
        
        # Draw needle tip (sharper, white)
        tip_start = (
            self.x + math.cos(self.angle) * self.length * 0.7,
            self.y + math.sin(self.angle) * self.length * 0.7
        )
        pygame.draw.line(screen, COLORS['needle_tip'], tip_start, tip, 3)
        
        # Draw eye of needle (hole for thread) at base
        eye_pos = (
            int(self.x - math.cos(self.angle) * 3),
            int(self.y - math.sin(self.angle) * 3)
        )
        pygame.draw.circle(screen, COLORS['thread'], eye_pos, 3)


class ThreadConnection:
    """A connection between two points via thread"""
    
    def __init__(self, point_a, point_b, connection_type='normal'):
        self.point_a = point_a  # (x, y) tuple
        self.point_b = point_b  # (x, y) tuple
        self.connection_type = connection_type  # 'normal', 'bridge', 'grapple', 'pull'
        self.active = True
        self.length = self._calculate_length()
        self.tension = 0  # For pulling mechanism
        self.age = 0  # Animation timer
        
        # Bridge properties
        self.is_bridge = False
        self.is_trampoline = False
        self._setup_bridge()
        
    def _calculate_length(self):
        """Calculate thread length"""
        dx = self.point_b[0] - self.point_a[0]
        dy = self.point_b[1] - self.point_a[1]
        return math.sqrt(dx**2 + dy**2)
    
    def _setup_bridge(self):
        """Setup bridge properties based on angle and length"""
        if self.connection_type == 'bridge':
            self.is_bridge = True
            # If thread is mostly horizontal and short, it's a trampoline
            dx = abs(self.point_b[0] - self.point_a[0])
            dy = abs(self.point_b[1] - self.point_a[1])
            if self.length < 150 and dx > dy * 2:
                self.is_trampoline = True
                
    def get_y_at_x(self, x):
        """Get Y position on thread at given X (for bridges)"""
        x1, y1 = self.point_a
        x2, y2 = self.point_b
        
        if x2 - x1 == 0:
            return y1
            
        t = (x - x1) / (x2 - x1)
        t = max(0, min(1, t))
        return y1 + t * (y2 - y1)
    
    def update(self):
        """Update thread state"""
        self.age += 1
        
    def get_thread_consumed(self):
        """Get amount of thread this connection uses"""
        return self.length * THREAD_CONSUMPTION_RATE
    
    def draw(self, screen):
        """Draw the thread connection"""
        if not self.active:
            return
            
        # Calculate wave effect for thread
        wave_offset = math.sin(self.age * 0.1) * 2
        
        # Draw glow
        glow_color = (*COLORS['thread_glow'][:3], 100)
        for i in range(-2, 3):
            start = (self.point_a[0], self.point_a[1] + wave_offset + i)
            end = (self.point_b[0], self.point_b[1] + wave_offset + i)
            pygame.draw.line(screen, COLORS['thread_glow'], start, end, 1)
        
        # Draw main thread
        pygame.draw.line(screen, COLORS['thread'], self.point_a, self.point_b, THREAD_WIDTH)
        
        # Draw knots at connection points
        pygame.draw.circle(screen, COLORS['thread'], (int(self.point_a[0]), int(self.point_a[1])), 5)
        pygame.draw.circle(screen, COLORS['thread'], (int(self.point_b[0]), int(self.point_b[1])), 5)
        
        # If bridge/trampoline, draw platform effect
        if self.is_bridge:
            self._draw_bridge_effect(screen)
            
    def _draw_bridge_effect(self, screen):
        """Draw visual effect for bridge"""
        # Draw thicker line to show it's walkable
        if self.is_trampoline:
            color = COLORS['trampoline']
            width = 8
        else:
            color = COLORS['bridge']
            width = 6
            
        pygame.draw.line(screen, color, self.point_a, self.point_b, width)
        
        # Draw stitching pattern
        num_stitches = max(3, int(self.length / 30))
        for i in range(num_stitches):
            t = (i + 0.5) / num_stitches
            x = self.point_a[0] + t * (self.point_b[0] - self.point_a[0])
            y = self.point_a[1] + t * (self.point_b[1] - self.point_a[1])
            
            # Draw small cross-stitch
            pygame.draw.line(screen, COLORS['needle'], (x-4, y-4), (x+4, y+4), 2)
            pygame.draw.line(screen, COLORS['needle'], (x+4, y-4), (x-4, y+4), 2)


class ThreadManager:
    """Manages all thread connections and needle"""
    
    def __init__(self, max_thread=DEFAULT_THREAD_LENGTH):
        self.needle = Needle()
        self.connections = []
        self.max_thread = max_thread
        self.thread_remaining = max_thread
        self.last_anchor_point = None
        self.grapple_connection = None
        
    @property
    def thread_percentage(self):
        return (self.thread_remaining / self.max_thread) * 100
    
    def shoot_needle(self, player_pos, target_pos):
        """Shoot needle from player position - only if enough thread"""
        # Allow shooting if needle is not currently flying
        # Embedded needles are auto-reset so player can shoot multiple times
        if not self.needle.active:
            # Calculate distance to target
            dx = target_pos[0] - player_pos[0]
            dy = target_pos[1] - player_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            # Check if we have enough thread to reach target
            thread_needed = distance * THREAD_CONSUMPTION_RATE
            if thread_needed > self.thread_remaining:
                # Not enough thread - don't shoot
                return False
            
            # Reset needle if it was embedded (allows multiple shots)
            if self.needle.embedded:
                self.needle.embedded = False
                self.needle.embed_point = None
            
            self.last_anchor_point = player_pos
            self.needle.shoot(player_pos, target_pos)
            return True
        return False
    
    def update(self, stitch_points, platforms, player=None):
        """Update needle and all thread connections"""
        needle_was_active = self.needle.active

        # Update needle
        hit = self.needle.update(stitch_points, platforms)
        embed_point = None
        
        if hit:
            hit_type, hit_object = hit
            # Save embed_point before _handle_hit resets it
            embed_point = self.needle.embed_point
            self._handle_hit(hit_type, hit_object, player)
        
        # Update all connections
        for conn in self.connections:
            conn.update()
            
        # Update grapple if active
        if self.grapple_connection and player and player.is_swinging:
            # Update grapple endpoint to player position
            self.grapple_connection.point_b = player.center
            
        # Return hit info and embed_point
        if hit:
            return (hit, embed_point)

        # Missed shot: needle stopped flying without attaching to anything.
        if needle_was_active and not self.needle.active and not self.needle.embedded:
            self.thread_remaining = max(0, self.thread_remaining - MISS_SHOT_THREAD_COST)

        return None
    
    def _handle_hit(self, hit_type, hit_object, player):
        """Handle needle hitting something"""
        if not self.last_anchor_point:
            return
            
        embed_point = self.needle.embed_point
        
        # Calculate thread cost
        dx = embed_point[0] - self.last_anchor_point[0]
        dy = embed_point[1] - self.last_anchor_point[1]
        distance = math.sqrt(dx**2 + dy**2)
        thread_cost = distance * THREAD_CONSUMPTION_RATE
        
        # Check if enough thread
        if thread_cost > self.thread_remaining:
            self.needle.recall()
            return
            
        # Determine connection type - always bridge (walkable path), never grapple
        if hit_type == 'platform' and hasattr(hit_object, 'is_movable') and hit_object.is_movable:
            # Hit a movable platform - attach thread and start falling
            conn_type = 'pull'
        else:
            # All other connections are bridges (walkable paths)
            conn_type = 'bridge'
            
        # Create connection
        connection = ThreadConnection(
            self.last_anchor_point,
            embed_point,
            conn_type
        )
        
        self.connections.append(connection)
        self.thread_remaining -= thread_cost
        
        # Reset needle so player can shoot again (multiple threads)
        self.needle.embedded = False
        self.needle.embed_point = None
        
        # No swinging - all threads are bridges/paths
            
        # Mark stitch point as used
        if hit_type == 'stitch_point':
            hit_object.stitched = True
            
        # Attach thread to movable platform and start it falling
        if hit_type == 'platform' and hasattr(hit_object, 'is_movable') and hit_object.is_movable:
            hit_object.attach_thread(connection)
            
    def create_bridge(self, point_a, point_b):
        """Manually create a bridge between two points"""
        dx = point_b[0] - point_a[0]
        dy = point_b[1] - point_a[1]
        distance = math.sqrt(dx**2 + dy**2)
        thread_cost = distance * THREAD_CONSUMPTION_RATE
        
        if thread_cost <= self.thread_remaining:
            connection = ThreadConnection(point_a, point_b, 'bridge')
            self.connections.append(connection)
            self.thread_remaining -= thread_cost
            return connection
        return None
    
    def unstitch_last(self):
        """Remove the last connection and recover some thread"""
        if self.connections:
            conn = self.connections.pop()
            recovered = conn.length * THREAD_RECOVERY_RATE
            self.thread_remaining = min(self.max_thread, self.thread_remaining + recovered)
            conn.active = False
            return True
        return False
    
    def unstitch_all(self):
        """Remove all connections"""
        for conn in self.connections:
            conn.active = False
        self.connections.clear()
        self.thread_remaining = self.max_thread
        self.needle.recall()
        self.grapple_connection = None
        
    def recall_needle(self, player=None):
        """Recall needle and stop any grapple"""
        self.needle.recall()
        if self.grapple_connection:
            self.grapple_connection = None
            if player:
                player.stop_swing()
                
    def get_bridges(self):
        """Get all active bridge connections"""
        return [c for c in self.connections if c.is_bridge and c.active]
    
    def cut_threads_at_position(self, pos, radius=20):
        """Cut threads that pass near a position (for hazards)"""
        cut_any = False
        for conn in self.connections[:]:
            if self._line_near_point(conn.point_a, conn.point_b, pos, radius):
                conn.active = False
                self.connections.remove(conn)
                cut_any = True
        return cut_any
    
    def _line_near_point(self, p1, p2, point, threshold):
        """Check if a line segment is near a point"""
        x1, y1 = p1
        x2, y2 = p2
        px, py = point
        
        # Vector from p1 to p2
        dx = x2 - x1
        dy = y2 - y1
        
        # Length squared
        len_sq = dx*dx + dy*dy
        if len_sq == 0:
            return math.sqrt((px-x1)**2 + (py-y1)**2) < threshold
            
        # Parameter t for closest point on line
        t = max(0, min(1, ((px-x1)*dx + (py-y1)*dy) / len_sq))
        
        # Closest point
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance to point
        distance = math.sqrt((px-closest_x)**2 + (py-closest_y)**2)
        return distance < threshold
    
    def draw(self, screen, player_pos=None):
        """Draw all threads and needle"""
        # Draw connections
        for conn in self.connections:
            conn.draw(screen)
            
        # Draw thread from player to needle if needle is flying
        if self.needle.active and self.last_anchor_point:
            pygame.draw.line(screen, COLORS['thread'], 
                           self.last_anchor_point, 
                           (self.needle.x, self.needle.y), 2)
        
        # Draw thread from player to embedded needle
        elif self.needle.embedded and player_pos and self.grapple_connection:
            pygame.draw.line(screen, COLORS['thread'],
                           player_pos,
                           self.needle.embed_point, 3)
        
        # Draw needle
        self.needle.draw(screen)
    
    def reset(self):
        """Reset thread manager to initial state"""
        self.needle.recall()
        self.connections.clear()
        self.thread_remaining = self.max_thread
        self.last_anchor_point = None
        self.grapple_connection = None