import pygame
import random
from game.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SLATE_NAVY, NEON_BLUE, WHITE, DARK_SLATE,
    BUTTON_WIDTH, BUTTON_HEIGHT, TITLE
)
from game.ui import Button, draw_grid_background
from game.visuals import create_neon_text

class FallingParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.randint(100, 300)
        self.size = random.randint(13, 17)
        self.alpha = 255
    
    def update(self, dt):
        self.y += self.speed * dt
        self.alpha -= 50 * dt
        if self.alpha < 0: self.alpha = 0
            
    def draw(self, surface):
        if self.alpha <= 0: return
        
        # Draw like a mini Note
        center = (self.x, self.y)
        r = self.size
        
        # Outer glow
        s = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*NEON_BLUE, int(self.alpha * 0.3)), (r*2, r*2), r*2)
        surface.blit(s, (self.x - r*2, self.y - r*2))
        
        # Core
        pygame.draw.circle(surface, (*NEON_BLUE, int(self.alpha)), center, r, 1)
        pygame.draw.circle(surface, (255, 255, 255, int(self.alpha)), center, max(1, r-2))


class HomeScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 160)
        self.next_screen = None
        
        # Pre-render Glow Title
        self.title_surf = create_neon_text(TITLE, self.title_font, (220, 240, 255), NEON_BLUE, blur_radius=20)
        
        self.row_center_y = SCREEN_HEIGHT // 2 + 100
        self.line_gap = 70
        self.top_line_y = self.row_center_y - self.line_gap // 2
        self.bot_line_y = self.row_center_y + self.line_gap // 2
        
        spacing = 40
        total_w = 4 * BUTTON_WIDTH + 3 * spacing  # 4 buttons
        start_x = (SCREEN_WIDTH - total_w) // 2
        btn_start_y = self.row_center_y - BUTTON_HEIGHT // 2
        
        self.buttons = {
            'play': Button(start_x, btn_start_y, BUTTON_WIDTH, BUTTON_HEIGHT, "PLAY"),
            'editor': Button(start_x + BUTTON_WIDTH + spacing, btn_start_y, BUTTON_WIDTH, BUTTON_HEIGHT, "EDITOR"),
            'settings': Button(start_x + 2*(BUTTON_WIDTH + spacing), btn_start_y, BUTTON_WIDTH, BUTTON_HEIGHT, "SETTINGS"),
            'quit': Button(start_x + 3*(BUTTON_WIDTH + spacing), btn_start_y, BUTTON_WIDTH, BUTTON_HEIGHT, "QUIT"),
        }
        
        self.particles = []
        self.spawn_timer = 0
    
    def handle_event(self, event):
        for name, btn in self.buttons.items():
            if btn.is_clicked(event):
                if name == 'play': self.next_screen = 'select'
                if name == 'editor': self.next_screen = 'map_select'
                if name == 'settings': self.next_screen = 'settings'
                if name == 'quit': return 'quit'
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: self.next_screen = 'select'
            if event.key == pygame.K_2: self.next_screen = 'map_select'
            if event.key == pygame.K_3: self.next_screen = 'settings'
            if event.key == pygame.K_4 or event.key == pygame.K_ESCAPE: return 'quit'

    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons.values():
            btn.update(mouse_pos)
            
        self.spawn_timer += dt
        if self.spawn_timer > 0.1:
            self.spawn_timer = 0
            px = random.randint(0, SCREEN_WIDTH)
            if random.random() < 0.5:
                px = random.randint(SCREEN_WIDTH//2 - 300, SCREEN_WIDTH//2 + 300)
            self.particles.append(FallingParticle(px, self.top_line_y - 100))
            
        for p in self.particles: 
            p.update(dt)
        self.particles = [p for p in self.particles if p.alpha > 0]

    def draw(self, surface):
        surface.fill(SLATE_NAVY)
        draw_grid_background(surface, SCREEN_WIDTH, SCREEN_HEIGHT)

        for p in self.particles: p.draw(surface)
        
        pygame.draw.line(surface, NEON_BLUE, (0, self.top_line_y), (SCREEN_WIDTH, self.top_line_y), 2)
        pygame.draw.line(surface, NEON_BLUE, (0, self.bot_line_y), (SCREEN_WIDTH, self.bot_line_y), 2)
        
        for i in range(1, 4):
            alpha = 100 - i * 30
            pygame.draw.line(surface, (*NEON_BLUE, alpha), (0, self.top_line_y-i), (SCREEN_WIDTH, self.top_line_y-i), 1)
            pygame.draw.line(surface, (*NEON_BLUE, alpha), (0, self.top_line_y+i), (SCREEN_WIDTH, self.top_line_y+i), 1)
            pygame.draw.line(surface, (*NEON_BLUE, alpha), (0, self.bot_line_y-i), (SCREEN_WIDTH, self.bot_line_y-i), 1)
            pygame.draw.line(surface, (*NEON_BLUE, alpha), (0, self.bot_line_y+i), (SCREEN_WIDTH, self.bot_line_y+i), 1)

        # Draw PIL Glow Title
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80
        r = self.title_surf.get_rect(center=(cx, cy))
        surface.blit(self.title_surf, r)

        for btn in self.buttons.values():
            btn.draw(surface)

    def get_next_screen(self):
        n = self.next_screen
        self.next_screen = None
        return n
