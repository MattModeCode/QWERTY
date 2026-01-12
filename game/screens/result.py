import pygame
import game.settings as settings
from game.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SLATE_NAVY, NEON_BLUE, WHITE, DARK_SLATE, GRAY
)
from game.ui import Button, draw_grid_background
from game.visuals import create_neon_text

class ResultScreen:
    def __init__(self, stats):
        self.stats = stats 
        self.next_screen = None
        
        # Pre-render Glow Title
        self.title_font = pygame.font.Font(None, 80)
        self.label_font = pygame.font.Font(None, 40)

        self.value_font = pygame.font.Font(None, 60)
        self.small_font = pygame.font.Font(None, 30)
        self.rank_font = pygame.font.Font(None, 200)
        
        # Determine Title based on result
        title_txt = "RESULT"
        color = NEON_BLUE
        if stats.get('rank') == 'F':
            title_txt = "FAILED"
            color = (255, 50, 50)
        else:
            title_txt = "COMPLETE"
            color = NEON_BLUE
            
        self.title_surf = create_neon_text(title_txt, self.title_font, WHITE, color, blur_radius=15)
        
        btn_y = SCREEN_HEIGHT - 80
        btn_w = 120
        self.buttons = {
            'retry': Button(SCREEN_WIDTH - 280, btn_y, btn_w, 45, "RETRY"),
            'back': Button(SCREEN_WIDTH - 140, btn_y, btn_w, 45, "BACK"),
        }

    def handle_event(self, event):
        for name, btn in self.buttons.items():
            if btn.is_clicked(event):
                if name == 'retry':
                    self.next_screen = 'gameplay' # Retry same song
                elif name == 'back':
                    self.next_screen = 'select'
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r: self.next_screen = 'gameplay'
            if event.key == pygame.K_ESCAPE: self.next_screen = 'select'

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for b in self.buttons.values(): b.update(mp)

    def draw(self, surface):
        surface.fill(SLATE_NAVY)
        draw_grid_background(surface, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Title
        t_rect = self.title_surf.get_rect(center=(SCREEN_WIDTH//2, 80))
        surface.blit(self.title_surf, t_rect)
        
        # Song Title
        s_title = self.small_font.render(self.stats.get('song_title', 'Unknown'), True, GRAY)
        surface.blit(s_title, s_title.get_rect(center=(SCREEN_WIDTH//2, 130)))
        
        # Big Rank
        rank = self.stats.get('rank', 'F')
        rank_col = NEON_BLUE
        if rank == 'F': rank_col = (255, 50, 50)
        elif rank == 'SS': rank_col = (255, 255, 0)
        elif rank == 'S': rank_col = (200, 255, 0)
        

        rank_s = self.rank_font.render(rank, True, rank_col)
        
        # Ensure single blit
        surface.blit(rank_s, rank_s.get_rect(center=(SCREEN_WIDTH//2 + 200, 300)))
        
        # Stats List
        x_base = 150
        y_start = 200
        gap = 50
        
        items = [
            ("Score", f"{self.stats['score']:,}"),
            ("Combo", f"{self.stats['combo']}x"),
            ("Accuracy", f"{self.stats['accuracy']:.2f}%"),
            ("Perfect", str(self.stats['perfect'])),
            ("Great", str(self.stats['great'])),
            ("Miss", str(self.stats['miss'])),
        ]
        
        for i, (label, val) in enumerate(items):
            y = y_start + i * gap
            l = self.label_font.render(label, True, GRAY)
            v = self.value_font.render(val, True, WHITE)
            
            surface.blit(l, (x_base, y))
            surface.blit(v, (x_base + 200, y - 5))
            
        for btn in self.buttons.values(): btn.draw(surface)

    def get_next_screen(self):
        n = self.next_screen
        self.next_screen = None
        return n, None 
