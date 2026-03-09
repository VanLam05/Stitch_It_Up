# ============================================================
# STITCH IT UP - UI System
# HUD, Menus, Thread Meter, and Overlays
# ============================================================

import pygame
import math
import os
import re
try:
    from .constants import *
except ImportError:
    from constants import *

class ThreadMeter:
    """Visual display of remaining thread"""
    
    def __init__(self, x, y, width=200, height=20):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.displayed_value = 100  # Smooth animation
        self.pulse_phase = 0
        
    def update(self, actual_percentage):
        """Smooth animation towards actual value"""
        diff = actual_percentage - self.displayed_value
        self.displayed_value += diff * 0.1
        self.pulse_phase += 0.1
        
        # Pulse faster when low
        if actual_percentage < 25:
            self.pulse_phase += 0.1
            
    def draw(self, screen, font):
        """Draw the thread meter"""
        # Background
        bg_rect = pygame.Rect(self.x - 5, self.y - 5, self.width + 10, self.height + 30)
        pygame.draw.rect(screen, COLORS['ui_bg'], bg_rect, border_radius=8)
        pygame.draw.rect(screen, (60, 60, 70), bg_rect, 2, border_radius=8)
        
        # Draw thread spool icon
        spool_x = self.x + 10
        spool_y = self.y + self.height // 2
        self._draw_spool_icon(screen, spool_x, spool_y)
        
        # Meter background
        meter_x = self.x + 30
        meter_rect = pygame.Rect(meter_x, self.y, self.width - 30, self.height)
        pygame.draw.rect(screen, COLORS['thread_meter_bg'], meter_rect, border_radius=5)
        
        # Meter fill
        fill_width = int((self.width - 30) * (self.displayed_value / 100))
        if fill_width > 0:
            fill_rect = pygame.Rect(meter_x, self.y, fill_width, self.height)
            
            # Color based on amount
            if self.displayed_value > 50:
                fill_color = COLORS['thread_meter_fill']
            elif self.displayed_value > 25:
                fill_color = (255, 165, 0)  # Orange warning
            else:
                # Pulsing red
                pulse = (math.sin(self.pulse_phase) + 1) / 2
                fill_color = (255, int(50 + 50 * pulse), 50)
                
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=5)
            
        # Meter outline
        pygame.draw.rect(screen, (100, 100, 110), meter_rect, 2, border_radius=5)
        
        # Percentage text
        text = f"{int(self.displayed_value)}%"
        text_surface = font.render(text, True, COLORS['ui_text'])
        text_rect = text_surface.get_rect(center=(meter_x + (self.width - 30) // 2, 
                                                   self.y + self.height + 12))
        screen.blit(text_surface, text_rect)
        
        # "THREAD" label
        label = font.render("THREAD", True, COLORS['thread'])
        screen.blit(label, (self.x, self.y + self.height + 5))
        
    def _draw_spool_icon(self, screen, x, y):
        """Draw a small thread spool icon"""
        # Main spool
        pygame.draw.ellipse(screen, COLORS['platform'], (x - 8, y - 6, 16, 12))
        pygame.draw.ellipse(screen, COLORS['thread'], (x - 6, y - 4, 12, 8))
        
        # Thread line
        thread_offset = math.sin(self.pulse_phase * 2) * 2
        pygame.draw.line(screen, COLORS['thread'], 
                        (x, y), (x + 15 + thread_offset, y - 5), 2)


class HUD:
    """Heads-Up Display showing game information"""
    
    def __init__(self):
        self.thread_meter = ThreadMeter(20, 20)
        self.font_large = None
        self.font_small = None
        self.font_tiny = None
        
    def init_fonts(self):
        """Initialize fonts after pygame is set up"""
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)
        
    def update(self, thread_percentage):
        """Update HUD elements"""
        self.thread_meter.update(thread_percentage)
        
    def draw(self, screen, level_name="", show_controls=True):
        """Draw the HUD"""
        if not self.font_small:
            self.init_fonts()
            
        # Thread meter
        self.thread_meter.draw(screen, self.font_tiny)
        
        # Level name (top center)
        if level_name:
            name_surface = self.font_small.render(level_name, True, COLORS['ui_text'])
            name_rect = name_surface.get_rect(center=(SCREEN_WIDTH // 2, 30))
            
            # Background
            bg_rect = name_rect.inflate(20, 10)
            pygame.draw.rect(screen, (*COLORS['ui_bg'], 200), bg_rect, border_radius=5)
            screen.blit(name_surface, name_rect)
            
        # Control hints (bottom right)
        if show_controls:
            self._draw_controls(screen)
            
    def _draw_controls(self, screen):
        """Draw control hints"""
        controls = [
            ("A/D", "Move"),
            ("Space", "Jump"),
            ("Click", "Shoot"),
            ("R", "Restart"),
        ]
        
        start_y = SCREEN_HEIGHT - 30 * len(controls) - 10
        x = SCREEN_WIDTH - 150
        
        # Background
        bg_rect = pygame.Rect(x - 10, start_y - 10, 160, 30 * len(controls) + 20)
        pygame.draw.rect(screen, (*COLORS['ui_bg'], 180), bg_rect, border_radius=8)
        
        for i, (key, action) in enumerate(controls):
            y = start_y + i * 30
            
            # Key
            key_surface = self.font_tiny.render(key, True, COLORS['stitch_point'])
            screen.blit(key_surface, (x, y))
            
            # Action
            action_surface = self.font_tiny.render(action, True, (180, 180, 180))
            screen.blit(action_surface, (x + 70, y))


class Menu:
    """Base menu class"""
    
    def __init__(self):
        self.font_title = None
        self.font_option = None
        self.font_small = None
        self.selected_index = 0
        self.options = []
        self.animation_phase = 0
        
    def init_fonts(self):
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 72)
        self.font_option = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 28)
        
    def handle_input(self, event):
        """Handle menu navigation"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
                return 'navigate'
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
                return 'navigate'
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected_index]
        return None
        
    def update(self):
        self.animation_phase += 0.05


class MainMenu(Menu):
    """Main menu screen"""
    
    def __init__(self):
        super().__init__()
        self.options = ['Start', 'Select Level', 'Tutorial', 'Exit']
        self.needle_pos = [200, 300]
        self.needle_vel = [2, 1.5]
        self.kim_frames = []
        self.kim_frame_ms = 110
        self._load_kim_ui_frames()

    def _load_kim_ui_frames(self):
        """Load animated needle frames from assets/KIM for UI."""
        folder_path = os.path.join(os.path.dirname(__file__), 'assets', 'KIM')
        try:
            files = [
                f for f in os.listdir(folder_path)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
            ]

            def natural_key(name):
                return [int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', name)]

            files.sort(key=natural_key)
            self.kim_frames = [
                pygame.image.load(os.path.join(folder_path, filename)).convert_alpha()
                for filename in files
            ]
        except (pygame.error, FileNotFoundError):
            self.kim_frames = []

    def _get_ui_kim_frame(self):
        """Get current animated frame for UI needle."""
        if not self.kim_frames:
            return None
        frame_index = (pygame.time.get_ticks() // self.kim_frame_ms) % len(self.kim_frames)
        return self.kim_frames[frame_index]
        
    def draw(self, screen):
        if not self.font_title:
            self.init_fonts()
            
        # Background with fabric pattern
        self._draw_background(screen)
        
        # Title with sewing theme
        self._draw_title(screen)
        
        # Menu options
        start_y = SCREEN_HEIGHT // 2
        for i, option in enumerate(self.options):
            self._draw_option(screen, option, i, start_y + i * 60)
            
        # Decorative floating needle
        self._update_floating_needle()
        self._draw_floating_needle(screen)
        
        # Credits
        credit = self.font_small.render("GAMETOPIA 2024 - Stitch It Up", 
                                        True, (100, 100, 110))
        screen.blit(credit, (SCREEN_WIDTH // 2 - credit.get_width() // 2, 
                            SCREEN_HEIGHT - 40))
        
    def _draw_background(self, screen):
        """Draw fabric-textured background"""
        screen.fill(COLORS['background'])
        
        # Fabric weave pattern
        for x in range(0, SCREEN_WIDTH, 20):
            alpha = 20 + int(10 * math.sin(x * 0.1 + self.animation_phase))
            pygame.draw.line(screen, (50, 47, 55), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 20):
            pygame.draw.line(screen, (50, 47, 55), (0, y), (SCREEN_WIDTH, y), 1)
            
        # Decorative thread curves
        for i in range(3):
            self._draw_decorative_thread(screen, i)
            
    def _draw_decorative_thread(self, screen, index):
        """Draw wavy decorative thread"""
        y_base = 150 + index * 200
        points = []
        for x in range(0, SCREEN_WIDTH + 50, 10):
            y = y_base + math.sin(x * 0.02 + self.animation_phase + index) * 30
            points.append((x, y))
        
        if len(points) > 2:
            color = [(220, 20, 60), (255, 182, 193), (192, 192, 192)][index]
            pygame.draw.lines(screen, color, False, points, 2)
            
    def _draw_title(self, screen):
        """Draw the game title"""
        # Shadow
        shadow = self.font_title.render("STITCH IT UP", True, (30, 25, 35))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 4, 124))
        screen.blit(shadow, shadow_rect)
        
        # Main title
        title = self.font_title.render("STITCH IT UP", True, COLORS['thread'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_option.render("Stitch the World Together", True, COLORS['stitch_point'])
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 170))
        screen.blit(subtitle, sub_rect)
        
        # Underline stitch
        stitch_y = 190
        for x in range(SCREEN_WIDTH // 2 - 150, SCREEN_WIDTH // 2 + 150, 30):
            pygame.draw.line(screen, COLORS['thread'], 
                           (x, stitch_y), (x + 15, stitch_y), 2)
            pygame.draw.line(screen, COLORS['thread'], 
                           (x + 15, stitch_y), (x + 15, stitch_y + 5), 2)
            
    def _draw_option(self, screen, text, index, y):
        """Draw a menu option"""
        is_selected = index == self.selected_index
        
        if is_selected:
            # Pulsing effect
            pulse = (math.sin(self.animation_phase * 3) + 1) / 2
            color = (255, 200 + int(55 * pulse), 200)
            
            # Selection indicator (animated needle frame)
            needle_x = SCREEN_WIDTH // 2 - 120
            frame = self._get_ui_kim_frame()
            if frame:
                indicator = pygame.transform.smoothscale(frame, (34, 34))
                screen.blit(indicator, (needle_x - 8, y - 2))
                thread_start = (needle_x + 26, y + 15)
            else:
                pygame.draw.polygon(screen, COLORS['needle'], [
                    (needle_x, y + 10),
                    (needle_x + 20, y + 15),
                    (needle_x, y + 20),
                ])
                thread_start = (needle_x + 20, y + 15)
            
            # Thread connecting to text
            pygame.draw.line(screen, COLORS['thread'],
                           thread_start,
                           (SCREEN_WIDTH // 2 - 80, y + 15), 2)
        else:
            color = (180, 180, 190)
            
        # Option text
        option_surface = self.font_option.render(text, True, color)
        option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, y + 15))
        screen.blit(option_surface, option_rect)
        
    def _update_floating_needle(self):
        """Update decorative floating needle"""
        self.needle_pos[0] += self.needle_vel[0]
        self.needle_pos[1] += self.needle_vel[1]
        
        if self.needle_pos[0] < 50 or self.needle_pos[0] > SCREEN_WIDTH - 50:
            self.needle_vel[0] *= -1
        if self.needle_pos[1] < 50 or self.needle_pos[1] > SCREEN_HEIGHT - 50:
            self.needle_vel[1] *= -1
            
    def _draw_floating_needle(self, screen):
        """Draw decorative floating needle"""
        x, y = self.needle_pos
        frame = self._get_ui_kim_frame()
        if frame:
            # Rotate sprite so it follows floating direction.
            angle_deg = -math.degrees(math.atan2(self.needle_vel[1], self.needle_vel[0]))
            sprite = pygame.transform.smoothscale(frame, (74, 74))
            rotated = pygame.transform.rotate(sprite, angle_deg)
            rect = rotated.get_rect(center=(int(x), int(y)))
            screen.blit(rotated, rect)
            return

        angle = math.atan2(self.needle_vel[1], self.needle_vel[0])
        length = 40

        tip_x = x + math.cos(angle) * length
        tip_y = y + math.sin(angle) * length

        pygame.draw.line(screen, COLORS['needle'], (x, y), (tip_x, tip_y), 4)
        pygame.draw.line(screen, (255, 255, 255),
                        (x + math.cos(angle) * length * 0.7, y + math.sin(angle) * length * 0.7),
                        (tip_x, tip_y), 2)


class LevelSelectMenu(Menu):
    """Level selection screen"""
    
    def __init__(self, level_count, unlocked_levels=None):
        super().__init__()
        self.level_count = level_count
        self.unlocked_levels = unlocked_levels or [True] + [False] * (level_count - 1)
        self.options = list(range(level_count)) + ['back']
        self.levels_per_page = 9
        
    def draw(self, screen, level_names):
        if not self.font_title:
            self.init_fonts()
            
        screen.fill(COLORS['background'])
        
        # Title
        title = self.font_title.render("Select Level", True, COLORS['thread'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title, title_rect)
        
        # Level grid (paged to support large level counts)
        cols = 3
        rows = (self.levels_per_page + cols - 1) // cols
        total_pages = (self.level_count + self.levels_per_page - 1) // self.levels_per_page

        if self.selected_index == len(self.options) - 1:
            current_page = max(0, total_pages - 1)
        else:
            current_page = self.selected_index // self.levels_per_page

        start_level = current_page * self.levels_per_page
        end_level = min(self.level_count, start_level + self.levels_per_page)
        
        box_width = 300
        box_height = 80
        spacing_x = 50
        spacing_y = 20
        
        start_x = (SCREEN_WIDTH - (cols * box_width + (cols - 1) * spacing_x)) // 2
        start_y = 180
        
        for i in range(start_level, end_level):
            display_index = i - start_level
            row = display_index // cols
            col = display_index % cols
            
            x = start_x + col * (box_width + spacing_x)
            y = start_y + row * (box_height + spacing_y)
            
            is_selected = i == self.selected_index
            is_unlocked = self.unlocked_levels[i] if i < len(self.unlocked_levels) else False
            
            self._draw_level_box(screen, x, y, box_width, box_height,
                                i + 1, level_names[i] if i < len(level_names) else f"Level {i+1}",
                                is_selected, is_unlocked)
        
        # Back button
        back_y = start_y + rows * (box_height + spacing_y) + 30
        is_back_selected = self.selected_index == len(self.options) - 1
        back_color = COLORS['thread'] if is_back_selected else (150, 150, 160)
        
        back_text = self.font_option.render("<- Back", True, back_color)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, back_y))
        screen.blit(back_text, back_rect)

        page_text = self.font_small.render(
            f"Page {current_page + 1}/{max(1, total_pages)}  (Use Up/Down to navigate)",
            True,
            (180, 180, 190),
        )
        page_rect = page_text.get_rect(center=(SCREEN_WIDTH // 2, 140))
        screen.blit(page_text, page_rect)
        
    def _draw_level_box(self, screen, x, y, width, height, level_num, name, selected, unlocked):
        """Draw a level selection box"""
        rect = pygame.Rect(x, y, width, height)
        
        if selected:
            # Glowing border
            glow_rect = rect.inflate(8, 8)
            pygame.draw.rect(screen, COLORS['stitch_point'], glow_rect, border_radius=12)
            
        # Background
        if unlocked:
            bg_color = COLORS['ui_bg'] if not selected else (50, 45, 60)
        else:
            bg_color = (40, 35, 45)
            
        pygame.draw.rect(screen, bg_color, rect, border_radius=10)
        pygame.draw.rect(screen, (80, 75, 90), rect, 2, border_radius=10)
        
        # Level number
        num_color = COLORS['stitch_point'] if unlocked else (80, 80, 90)
        num_surface = self.font_option.render(str(level_num), True, num_color)
        screen.blit(num_surface, (x + 15, y + height // 2 - num_surface.get_height() // 2))
        
        # Level name
        if unlocked:
            name_color = COLORS['ui_text']
        else:
            name_color = (100, 100, 110)
            name = "Locked"
            
        name_surface = self.font_small.render(name, True, name_color)
        screen.blit(name_surface, (x + 60, y + height // 2 - name_surface.get_height() // 2))


class PauseOverlay:
    """Pause menu overlay"""
    
    def __init__(self):
        self.options = ['Continue', 'Restart', 'Main Menu']
        self.selected_index = 0
        self.font_title = None
        self.font_option = None
        
    def init_fonts(self):
        self.font_title = pygame.font.Font(None, 56)
        self.font_option = pygame.font.Font(None, 36)
        
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected_index]
            elif event.key == pygame.K_ESCAPE:
                return 'Continue'
        return None
    
    def draw(self, screen):
        if not self.font_title:
            self.init_fonts()
            
        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Pause box
        box_width = 400
        box_height = 300
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, COLORS['ui_bg'], box_rect, border_radius=15)
        pygame.draw.rect(screen, COLORS['thread'], box_rect, 3, border_radius=15)
        
        # Title
        title = self.font_title.render("PAUSED", True, COLORS['ui_text'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, box_y + 50))
        screen.blit(title, title_rect)
        
        # Options
        for i, option in enumerate(self.options):
            y = box_y + 120 + i * 50
            is_selected = i == self.selected_index
            
            color = COLORS['stitch_point'] if is_selected else (180, 180, 190)
            option_surface = self.font_option.render(option, True, color)
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, y))
            screen.blit(option_surface, option_rect)
            
            if is_selected:
                # Arrow indicator
                pygame.draw.polygon(screen, color, [
                    (option_rect.left - 30, y),
                    (option_rect.left - 15, y - 8),
                    (option_rect.left - 15, y + 8),
                ])


class GameOverOverlay:
    """Win/Lose overlay"""
    
    def __init__(self):
        self.win_options = ['Continue', 'Restart', 'Main Menu']
        self.lose_options = ['Restart', 'Main Menu']
        self.is_win_mode = True
        self.selected_index = 0
        self.font_title = None
        self.font_message = None
        self.font_option = None
        self.animation_phase = 0
        
    def set_mode(self, is_win):
        """Set win or lose mode"""
        self.is_win_mode = is_win
        self.selected_index = 0
        
    @property
    def options(self):
        return self.win_options if self.is_win_mode else self.lose_options
        
    def init_fonts(self):
        self.font_title = pygame.font.Font(None, 64)
        self.font_message = pygame.font.Font(None, 32)
        self.font_option = pygame.font.Font(None, 36)
        
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected_index]
        return None
    
    def update(self):
        self.animation_phase += 0.05
        
    def draw(self, screen, is_win, message=""):
        if not self.font_title:
            self.init_fonts()
            
        self.update()
        
        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        if is_win:
            self._draw_win(screen)
        else:
            self._draw_lose(screen, message)
            
        # Options (uses self.options which depends on mode)
        for i, option in enumerate(self.options):
            y = SCREEN_HEIGHT // 2 + 50 + i * 50
            is_selected = i == self.selected_index
            
            color = COLORS['stitch_point'] if is_selected else (180, 180, 190)
            option_surface = self.font_option.render(option, True, color)
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, y))
            screen.blit(option_surface, option_rect)
            
    def _draw_win(self, screen):
        """Draw victory screen"""
        # Animated celebration
        for i in range(8):
            angle = (i / 8) * 2 * math.pi + self.animation_phase
            x = SCREEN_WIDTH // 2 + math.cos(angle) * 150
            y = SCREEN_HEIGHT // 3 + math.sin(angle) * 50
            
            color = [(255, 215, 0), (255, 182, 193), (147, 112, 219)][i % 3]
            pygame.draw.circle(screen, color, (int(x), int(y)), 10)
        
        # Title
        title = self.font_title.render("LEVEL COMPLETE!", True, COLORS['stitch_point_final'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        screen.blit(title, title_rect)
        
        # Stitched heart
        self._draw_stitched_heart(screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 - 80)
        
    def _draw_lose(self, screen, message):
        """Draw game over screen"""
        # Title
        title = self.font_title.render("GAME OVER", True, (255, 100, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        screen.blit(title, title_rect)
        
        # Message
        if message:
            msg_surface = self.font_message.render(message, True, (200, 200, 200))
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 50))
            screen.blit(msg_surface, msg_rect)
            
        # Broken thread visual
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 3 - 60
        
        # Left part of broken thread
        pygame.draw.line(screen, COLORS['thread'], (cx - 80, cy), (cx - 10, cy), 4)
        # Right part
        pygame.draw.line(screen, COLORS['thread'], (cx + 10, cy + 15), (cx + 80, cy + 15), 4)
        # Frayed ends
        for i in range(3):
            offset = i * 5
            pygame.draw.line(screen, COLORS['thread'], 
                           (cx - 10, cy), (cx - 5 + offset, cy + 10), 2)
            pygame.draw.line(screen, COLORS['thread'],
                           (cx + 10, cy + 15), (cx + 5 - offset, cy + 5), 2)
            
    def _draw_stitched_heart(self, screen, x, y):
        """Draw a stitched heart shape"""
        size = 30
        
        # Heart points
        points = []
        for i in range(30):
            t = i / 30 * 2 * math.pi
            hx = 16 * (math.sin(t) ** 3)
            hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            points.append((x + hx * size / 16, y + hy * size / 16))
            
        # Draw heart outline with stitch pattern
        for i in range(len(points) - 1):
            if i % 3 == 0:
                pygame.draw.line(screen, COLORS['thread'], points[i], points[i+1], 3)


class TutorialOverlay:
    """Tutorial/Instructions overlay"""
    
    def __init__(self):
        self.font_title = None
        self.font_text = None
        self.page = 0
        self.pages = [
            {
                'title': 'Basic Controls',
                'content': [
                    'A / D or Arrow Keys: Move left/right',
                    'Space or Up Arrow: Jump',
                    'Mouse Click: Shoot needle to create path',
                    'R: Restart level',
                    'ESC: Pause game',
                ]
            },
            {
                'title': 'Stitching Mechanics',
                'content': [
                    'Shoot needle at anchor points (golden circles)',
                    'You can shoot MULTIPLE threads!',
                    'Threads create WALKABLE PATHS between points',
                    'Walk on threads to cross gaps!',
                    'Shoot wood blocks to pull them down!',
                ]
            },
            {
                'title': 'Door Puzzles',
                'content': [
                    'Shoot needle at wood blocks to make them fall',
                    'Falling blocks can press buttons on the ground',
                    'Pressing a button opens the linked door',
                    'Walk through the open door to complete the level!',
                    'Plan your shots - thread is permanent!',
                ]
            },
            {
                'title': 'Goals & Challenges',
                'content': [
                    'Open the door and walk through to win!',
                    'Shoot wood blocks to make them fall on buttons',
                    'You can shoot multiple threads - plan wisely!',
                    'Scissors cut your thread - you will fall!',
                    'Flames burn thread and hurt you',
                ]
            },
        ]
        
    def init_fonts(self):
        self.font_title = pygame.font.Font(None, 48)
        self.font_text = pygame.font.Font(None, 28)
        
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE, pygame.K_RETURN):
                self.page += 1
                if self.page >= len(self.pages):
                    return 'close'
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.page = max(0, self.page - 1)
            elif event.key == pygame.K_ESCAPE:
                return 'close'
        return None
    
    def draw(self, screen):
        if not self.font_title:
            self.init_fonts()
            
        # Background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        # Content box
        box_width = 700
        box_height = 450
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, COLORS['ui_bg'], box_rect, border_radius=15)
        pygame.draw.rect(screen, COLORS['thread'], box_rect, 3, border_radius=15)
        
        # Page content
        page_data = self.pages[self.page]
        
        # Title
        title = self.font_title.render(page_data['title'], True, COLORS['stitch_point'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, box_y + 50))
        screen.blit(title, title_rect)
        
        # Content lines
        for i, line in enumerate(page_data['content']):
            y = box_y + 120 + i * 40
            text = self.font_text.render(line, True, COLORS['ui_text'])
            screen.blit(text, (box_x + 40, y))
            
        # Navigation
        nav_y = box_y + box_height - 50
        
        # Page indicator
        for i in range(len(self.pages)):
            x = SCREEN_WIDTH // 2 + (i - len(self.pages) // 2) * 30
            color = COLORS['stitch_point'] if i == self.page else (100, 100, 110)
            pygame.draw.circle(screen, color, (x, nav_y), 8 if i == self.page else 6)
        
        # Instructions
        if self.page < len(self.pages) - 1:
            hint = "-> Next Page"
        else:
            hint = "Press Enter to close"
        hint_surface = self.font_text.render(hint, True, (150, 150, 160))
        hint_rect = hint_surface.get_rect(center=(SCREEN_WIDTH // 2, nav_y + 30))
        screen.blit(hint_surface, hint_rect)