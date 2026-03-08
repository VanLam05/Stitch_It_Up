# ============================================================
# STITCH IT UP - Main Game
# Khâu Vá Thế Giới - 2D Puzzle Platformer
# GAMETOPIA 2024
# ============================================================

import pygame
import sys
import math
import random

try:
    from .constants import *
    from .player import Player
    from .thread_system import ThreadManager
    from .level_system import Level, get_level, get_level_count, LEVELS
    from .ui_system import (HUD, MainMenu, LevelSelectMenu, PauseOverlay, 
                           GameOverOverlay, TutorialOverlay)
except ImportError:
    from constants import *
    from player import Player
    from thread_system import ThreadManager
    from level_system import Level, get_level, get_level_count, LEVELS
    from ui_system import (HUD, MainMenu, LevelSelectMenu, PauseOverlay, 
                          GameOverOverlay, TutorialOverlay)

class Game:
    """Main game class - manages game states and main loop"""
    
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        # Game state
        self.state = STATE_MENU
        self.running = True
        
        # Level management
        self.current_level_index = 0
        self.current_level = None
        self.unlocked_levels = [True] + [False] * (get_level_count() - 1)
        
        # Game objects
        self.player = None
        self.thread_manager = None
        
        # UI
        self.hud = HUD()
        self.main_menu = MainMenu()
        self.level_select = None
        self.pause_overlay = PauseOverlay()
        self.game_over_overlay = GameOverOverlay()
        self.tutorial_overlay = TutorialOverlay()
        
        # Gameplay state
        self.is_aiming = False
        self.aim_start_pos = None
        
        # Visual effects
        self.screen_shake = 0
        self.particles = []
        
        # Lose message
        self.lose_message = ""
        
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()
        
    def handle_events(self):
        """Process all events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            if self.state == STATE_MENU:
                self._handle_menu_events(event)
            elif self.state == 'tutorial':
                self._handle_tutorial_events(event)
            elif self.state == STATE_LEVEL_SELECT:
                self._handle_level_select_events(event)
            elif self.state == STATE_PLAYING:
                self._handle_playing_events(event)
            elif self.state == STATE_PAUSED:
                self._handle_pause_events(event)
            elif self.state in (STATE_WIN, STATE_LOSE):
                self._handle_game_over_events(event)
                
    def _handle_menu_events(self, event):
        """Handle main menu events"""
        result = self.main_menu.handle_input(event)
        
        if result == 'Start':
            self.start_level(0)
        elif result == 'Select Level':
            self.level_select = LevelSelectMenu(get_level_count(), self.unlocked_levels)
            self.state = STATE_LEVEL_SELECT
        elif result == 'Tutorial':
            self.tutorial_overlay.page = 0
            self.state = 'tutorial'
        elif result == 'Exit':
            self.running = False
            
    def _handle_tutorial_events(self, event):
        """Handle tutorial overlay events"""
        result = self.tutorial_overlay.handle_input(event)
        if result == 'close':
            self.state = STATE_MENU
            
    def _handle_level_select_events(self, event):
        """Handle level selection events"""
        result = self.level_select.handle_input(event)
        
        if result == 'back':
            self.state = STATE_MENU
        elif isinstance(result, int):
            if result < len(self.unlocked_levels) and self.unlocked_levels[result]:
                self.start_level(result)
            
    def _handle_playing_events(self, event):
        """Handle gameplay events"""
        if event.type == pygame.KEYDOWN:
            # Jump
            for key in KEYS['jump']:
                if event.key == key:
                    self.player.jump()
                    break
                    
            # Detach from thread (E key) - stop swinging but keep thread visible
            if event.key == pygame.K_e:
                if self.player.is_swinging:
                    self.player.stop_swing()
                    # Keep grapple_connection visible - don't remove it
                    
            # Restart
            for key in KEYS['restart']:
                if event.key == key:
                    self.restart_level()
                    break
                    
            # Pause
            for key in KEYS['pause']:
                if event.key == key:
                    self.state = STATE_PAUSED
                    break
                    
        # Mouse events for aiming and shooting
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.is_aiming = True
                self.aim_start_pos = self.player.center
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_aiming:
                self.is_aiming = False
                mouse_pos = pygame.mouse.get_pos()
                self._shoot_needle(mouse_pos)
                
    def _handle_pause_events(self, event):
        """Handle pause menu events"""
        result = self.pause_overlay.handle_input(event)
        
        if result == 'Continue':
            self.state = STATE_PLAYING
        elif result == 'Restart':
            self.restart_level()
        elif result == 'Main Menu':
            self.state = STATE_MENU
            
    def _handle_game_over_events(self, event):
        """Handle win/lose screen events"""
        result = self.game_over_overlay.handle_input(event)
        
        if result == 'Continue':
            if self.state == STATE_WIN:
                next_level = self.current_level_index + 1
                if next_level < get_level_count():
                    self.start_level(next_level)
                else:
                    self.state = STATE_MENU
            else:
                self.restart_level()
        elif result == 'Restart':
            self.restart_level()
        elif result == 'Main Menu':
            self.state = STATE_MENU
            
    def _shoot_needle(self, target_pos):
        """Shoot needle towards target"""
        if not self.player.is_swinging:
            player_pos = self.player.center
            if self.thread_manager.shoot_needle(player_pos, target_pos):
                self._add_shoot_particles(player_pos)
                
    def start_level(self, level_index):
        """Start a specific level"""
        self.current_level_index = level_index
        self.current_level = get_level(level_index)
        
        if self.current_level:
            # Initialize player
            start_x, start_y = self.current_level.player_start
            self.player = Player(start_x, start_y)
            
            # Initialize thread manager
            self.thread_manager = ThreadManager(self.current_level.thread_limit)
            
            # Reset UI
            self.hud = HUD()
            
            self.state = STATE_PLAYING
            
    def restart_level(self):
        """Restart current level"""
        if self.current_level:
            self.current_level.reset()
            start_x, start_y = self.current_level.player_start
            self.player.reset(start_x, start_y)
            self.thread_manager.reset()
            self.particles.clear()
            self.state = STATE_PLAYING
            
    def update(self):
        """Update game state"""
        if self.state == STATE_MENU:
            self.main_menu.update()
        elif self.state == 'tutorial':
            pass  # Tutorial is static
        elif self.state == STATE_PLAYING:
            self._update_gameplay()
        elif self.state == STATE_PAUSED:
            pass  # Paused, no updates
        elif self.state in (STATE_WIN, STATE_LOSE):
            self.game_over_overlay.update()
            
        # Update particles
        self._update_particles()
        
    def _update_gameplay(self):
        """Update gameplay logic"""
        # Get input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # Update thread system
        bridges = self.thread_manager.get_bridges()
        hit = self.thread_manager.update(
            self.current_level.stitch_points,
            self.current_level.platforms,
            self.player
        )
        
        if hit:
            hit_info, embed_point = hit
            if embed_point:
                self._add_hit_particles(embed_point)
            
        # Update player
        self.player.update(self.current_level.platforms, bridges)
        
        # Update level objects (pass bridges for movable block collision)
        self.current_level.update(bridges)
        
        # Update button presses (check if movable objects or player are on buttons)
        for button in self.current_level.buttons:
            objects_on_button = []
            # Check movable objects (falling blocks)
            for movable in self.current_level.movable_objects:
                if button.detection_rect.colliderect(movable.rect):
                    objects_on_button.append(movable)
            # Check player
            if button.detection_rect.colliderect(self.player.rect):
                objects_on_button.append(self.player)
            button.update(objects_on_button)
        
        # Update HUD
        self.hud.update(self.thread_manager.thread_percentage)
        
        # Check win/lose conditions
        self._check_game_conditions()
        
        # Check hazard thread cutting (scissors cut threads)
        for hazard in self.current_level.hazards:
            # Check if grapple thread is cut while swinging
            if self.player.is_swinging and self.thread_manager.grapple_connection:
                grapple = self.thread_manager.grapple_connection
                if self.thread_manager._line_near_point(
                    grapple.point_a, grapple.point_b, hazard.center, 35
                ):
                    # Thread cut while swinging - player falls with momentum!
                    self._add_cut_particles(hazard.center)
                    self.thread_manager.grapple_connection.active = False
                    if self.thread_manager.grapple_connection in self.thread_manager.connections:
                        self.thread_manager.connections.remove(self.thread_manager.grapple_connection)
                    self.thread_manager.grapple_connection = None
                    self.player.stop_swing()  # This preserves momentum
                    self.screen_shake = 8
                    continue
            
            # Cut other threads near hazard
            if self.thread_manager.cut_threads_at_position(hazard.center, 30):
                self._add_cut_particles(hazard.center)
            
    def _check_game_conditions(self):
        """Check win/lose conditions"""
        # Win condition 1: If level has doors, must go through an open door
        if self.current_level.doors:
            for door in self.current_level.doors:
                if door.open and door.open_amount > 0.8:  # Door is fully open
                    # Check if player is touching the door
                    door_rect = pygame.Rect(door.x, door.y, door.width, door.height)
                    if self.player.rect.colliderect(door_rect):
                        self._trigger_win()
                        return
        else:
            # Win condition 2: If no doors, reach final stitch point
            final_point = self.current_level.get_final_stitch_point()
            if final_point and final_point.stitched:
                # Check if player is near the final point
                dx = self.player.center[0] - final_point.x
                dy = self.player.center[1] - final_point.y
                if math.sqrt(dx**2 + dy**2) < 100:  # Within range
                    self._trigger_win()
                    return
            
            # Also win if player touches the final point directly
            if final_point:
                player_center = self.player.center
                dx = player_center[0] - final_point.x
                dy = player_center[1] - final_point.y
                if math.sqrt(dx**2 + dy**2) < final_point.radius + 20:
                    self._trigger_win()
                    return
        
        # Lose condition: fall into void
        if self.player.check_void(SCREEN_HEIGHT):
            self._trigger_lose(LOSE_FALL, "Fell into the void!")
            return
            
        # Lose condition: hit hazard
        if self.player.check_hazard_collision(self.current_level.hazards):
            self._trigger_lose(LOSE_HAZARD, "Hit a hazard!")
            return
            
        # Lose condition: out of thread (only if needle not embedded and can't reach goal)
        if self.thread_manager.thread_remaining <= 0:
            if not self.thread_manager.needle.embedded:
                # Check if player can still reach goal
                if not self._can_reach_goal():
                    self._trigger_lose(LOSE_THREAD_OUT, "Out of thread!")
                    
    def _can_reach_goal(self):
        """Check if player can potentially reach goal without more thread"""
        # If level has doors, check if any door is open
        if self.current_level.doors:
            for door in self.current_level.doors:
                if door.open:
                    # Check if player can reach an open door
                    dx = abs(self.player.x - door.x)
                    dy = abs(self.player.y - door.y)
                    if dx < 200 and dy < 200:
                        return True
            return False
        
        # For levels with final stitch point
        final_point = self.current_level.get_final_stitch_point()
        if not final_point:
            return True
            
        # Simple check: is player close enough to walk/jump to goal?
        dx = abs(self.player.x - final_point.x)
        dy = abs(self.player.y - final_point.y)
        
        # Very generous estimation
        return dx < 200 and dy < 200
        
    def _trigger_win(self):
        """Handle winning the level"""
        self.state = STATE_WIN
        self.game_over_overlay.set_mode(True)  # Win mode
        
        # Unlock next level
        next_level = self.current_level_index + 1
        if next_level < len(self.unlocked_levels):
            self.unlocked_levels[next_level] = True
            
        # Victory particles
        for _ in range(50):
            self._add_victory_particle()
            
    def _trigger_lose(self, reason, message):
        """Handle losing"""
        self.state = STATE_LOSE
        self.lose_message = message
        self.game_over_overlay.set_mode(False)  # Lose mode
        self.screen_shake = 10
        
    def draw(self):
        """Render everything"""
        # Apply screen shake
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = int((pygame.time.get_ticks() % 10 - 5) * (self.screen_shake / 10))
            offset_y = int((pygame.time.get_ticks() % 8 - 4) * (self.screen_shake / 10))
            self.screen_shake -= 0.5
            
        # Create offset surface for shake
        if self.screen_shake > 0:
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            draw_target = temp_surface
        else:
            draw_target = self.screen
            
        # Draw based on state
        if self.state == STATE_MENU:
            self.main_menu.draw(draw_target)
        elif self.state == 'tutorial':
            self.main_menu.draw(draw_target)
            self.tutorial_overlay.draw(draw_target)
        elif self.state == STATE_LEVEL_SELECT:
            level_names = [l['name'] for l in LEVELS]
            self.level_select.draw(draw_target, level_names)
        else:
            # Draw gameplay
            self._draw_gameplay(draw_target)
            
            # Draw overlays
            if self.state == STATE_PAUSED:
                self.pause_overlay.draw(draw_target)
            elif self.state == STATE_WIN:
                self.game_over_overlay.draw(draw_target, True)
            elif self.state == STATE_LOSE:
                self.game_over_overlay.draw(draw_target, False, self.lose_message)
                
        # Draw particles on top
        self._draw_particles(draw_target)
        
        # Apply shake offset
        if self.screen_shake > 0:
            self.screen.fill(COLORS['void'])
            self.screen.blit(temp_surface, (offset_x, offset_y))
            
        pygame.display.flip()
        
    def _draw_gameplay(self, screen):
        """Draw the main gameplay"""
        # Background
        self._draw_background(screen)
        
        # Level objects
        self.current_level.draw(screen)
        
        # Thread manager (threads and needle)
        self.thread_manager.draw(screen, self.player.center)
        
        # Aim line when aiming
        if self.is_aiming:
            self._draw_aim_line(screen)
            
        # Player
        self.player.draw(screen)
        
        # HUD
        self.hud.draw(screen, self.current_level.level_name)
        
    def _draw_background(self, screen):
        """Draw the game background"""
        screen.fill(COLORS['background'])
        
        # Fabric texture pattern
        for x in range(0, SCREEN_WIDTH, 30):
            pygame.draw.line(screen, (50, 47, 55), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 30):
            pygame.draw.line(screen, (50, 47, 55), (0, y), (SCREEN_WIDTH, y), 1)
            
        # Void at bottom
        void_rect = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 100)
        pygame.draw.rect(screen, COLORS['void'], void_rect)
        
        # Danger line
        pygame.draw.line(screen, (80, 20, 20), 
                        (0, SCREEN_HEIGHT - 50), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 2)
        
    def _draw_aim_line(self, screen):
        """Draw aiming trajectory"""
        if not self.aim_start_pos:
            return
            
        mouse_pos = pygame.mouse.get_pos()
        start = self.player.center
        
        # Draw dotted line
        dx = mouse_pos[0] - start[0]
        dy = mouse_pos[1] - start[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            # Normalize and extend to max range
            nx = dx / distance
            ny = dy / distance
            
            # Draw dots along trajectory
            max_dist = min(distance, NEEDLE_MAX_DISTANCE)
            for d in range(0, int(max_dist), 20):
                x = start[0] + nx * d
                y = start[1] + ny * d
                
                alpha = 255 - int(200 * (d / NEEDLE_MAX_DISTANCE))
                pygame.draw.circle(screen, (*COLORS['needle'], alpha), (int(x), int(y)), 3)
                
            # Draw target reticle
            end_x = start[0] + nx * max_dist
            end_y = start[1] + ny * max_dist
            pygame.draw.circle(screen, COLORS['stitch_point'], (int(end_x), int(end_y)), 10, 2)
            
    # Particle system
    def _add_shoot_particles(self, pos):
        """Add particles when shooting needle"""
        for _ in range(10):
            angle = random.random() * math.pi * 2
            speed = 2 + random.random() * 3
            self.particles.append({
                'x': pos[0],
                'y': pos[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 30,
                'color': COLORS['thread'],
                'size': 4,
            })
            
    def _add_hit_particles(self, pos):
        """Add particles when needle hits"""
        for i in range(15):
            angle = i / 15 * math.pi * 2
            speed = 3
            self.particles.append({
                'x': pos[0],
                'y': pos[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 25,
                'color': COLORS['stitch_point'],
                'size': 5,
            })
            
    def _add_cut_particles(self, pos):
        """Add particles when thread is cut"""
        for i in range(8):
            angle = i / 8 * math.pi * 2
            self.particles.append({
                'x': pos[0],
                'y': pos[1],
                'vx': math.cos(angle) * 2,
                'vy': math.sin(angle) * 2 - 1,
                'life': 20,
                'color': COLORS['thread'],
                'size': 3,
            })
            
    def _add_victory_particle(self):
        """Add celebration particle"""
        colors = [COLORS['stitch_point'], COLORS['stitch_point_final'], 
                 COLORS['thread'], (255, 255, 255)]
        self.particles.append({
            'x': random.randint(100, SCREEN_WIDTH - 100),
            'y': SCREEN_HEIGHT + 10,
            'vx': random.uniform(-1, 1),
            'vy': random.uniform(-8, -4),
            'life': random.randint(60, 120),
            'color': random.choice(colors),
            'size': random.randint(4, 8),
        })
        
    def _update_particles(self):
        """Update all particles"""
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1  # Gravity
            p['life'] -= 1
            p['size'] = max(1, p['size'] - 0.1)
            
            if p['life'] <= 0:
                self.particles.remove(p)
                
    def _draw_particles(self, screen):
        """Draw all particles"""
        for p in self.particles:
            alpha = min(255, p['life'] * 8)
            color = p['color']
            pygame.draw.circle(screen, color, (int(p['x']), int(p['y'])), int(p['size']))


def main():
    """Entry point"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
