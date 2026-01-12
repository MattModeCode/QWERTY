import pygame
from game.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SLATE_NAVY, NEON_BLUE, WHITE
)
from game.ui import Button, draw_grid_background
from game.visuals import create_neon_text

class SettingsScreen:
    """Settings screen - Currently Work In Progress."""
    
    def __init__(self):
        self.next_screen = None
        self.font = pygame.font.Font(None, 64)
        self.small_font = pygame.font.Font(None, 32)
        
        # Glow Title
        self.title_surf = create_neon_text("SETTINGS", self.font, WHITE, NEON_BLUE)
        
        # Back Button
        self.back_btn = Button(20, SCREEN_HEIGHT - 60, 100, 45, "BACK")
        
    def handle_event(self, event):
        if self.back_btn.is_clicked(event):
            self.next_screen = 'menu'
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_screen = 'menu'

    def update(self, dt):
        self.back_btn.update(pygame.mouse.get_pos())

    def draw(self, surface):
        surface.fill(SLATE_NAVY)
        draw_grid_background(surface, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Title
        t_rect = self.title_surf.get_rect(center=(SCREEN_WIDTH//2, 80))
        surface.blit(self.title_surf, t_rect)
        
        # WIP Text
        wip_text = "WORK IN PROGRESS"
        w_surf = self.small_font.render(wip_text, True, WHITE)
        surface.blit(w_surf, w_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
        
        self.back_btn.draw(surface)

    def get_next_screen(self):
        n = self.next_screen
        self.next_screen = None
        return n
