import pygame
import os
from game.map_manager import MapManager
import game.settings as settings
from game.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SLATE_NAVY, NEON_BLUE, WHITE, DARK_SLATE, GRAY
)
from game.ui import Button, Panel, draw_grid_background
from game.data_manager import DataManager
from game.visuals import create_neon_text, draw_star
from game.audio_manager import audio_manager

class SongSelectScreen:
    """Song selection screen - selects song and passes to gameplay."""
    
    def __init__(self):
        self.next_screen = None
        self.selected_index = 0
        self.map_manager = MapManager()
        self.data_manager = DataManager()
        self.maps = self.map_manager.list_maps() # Load map list
        
        self.title_font = pygame.font.Font(None, 72)
        # Pre-render Glow
        self.title_surf = create_neon_text("SELECT MAP", self.title_font, WHITE, NEON_BLUE)
        
        self.song_font = pygame.font.Font(None, 28)
        self.detail_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.stat_font = pygame.font.Font(None, 22)
        
        btn_y = SCREEN_HEIGHT - 60
        btn_w = 120
        self.buttons = {
            'play': Button(SCREEN_WIDTH - 140, btn_y, btn_w, 45, "PLAY"),
            'back': Button(20, btn_y, 80, 45, "BACK"), 
        }
        
        self.list_panel = Panel(50, 100, 500, 550)
        self.preview_panel = Panel(600, 100, 400, 550)
        
        self.image_cache = {}
        
        self.current_preview = None
    
    def handle_event(self, event):
        for name, btn in self.buttons.items():
            if btn.is_clicked(event):
                if name == 'play' and self.maps:
                    selected_map = self.maps[self.selected_index]
                    settings.current_map_file = selected_map["filename"]
                    self.next_screen = 'gameplay'
                elif name == 'back':
                    audio_manager.stop()
                    self.next_screen = 'menu'
        
        if event.type == pygame.KEYDOWN:
            prev_index = self.selected_index
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.maps) - 1, self.selected_index + 1)
            elif event.key == pygame.K_RETURN:
                if self.maps:
                    selected_map = self.maps[self.selected_index]
                    settings.current_map_file = selected_map["filename"]
                    self.next_screen = 'gameplay'
            elif event.key == pygame.K_RETURN:
                if self.maps:
                    selected_map = self.maps[self.selected_index]
                    settings.current_map_file = selected_map["filename"]
                    self.next_screen = 'gameplay'
            elif event.key == pygame.K_ESCAPE:
                audio_manager.stop()
                self.next_screen = 'menu'
            
            if prev_index != self.selected_index:
                self._play_preview()
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            prev_index = self.selected_index
            for i in range(len(self.maps)):
                y = 115 + i * 50
                r = pygame.Rect(60, y, 480, 45)
                if y > 630: break
                if r.collidepoint(event.pos):
                    self.selected_index = i
            
            if prev_index != self.selected_index:
                self._play_preview()

    def _play_preview(self):
        if not self.maps: return
        
        selected_map = self.maps[self.selected_index]
        # Load map data to get audio file
        map_data = self.map_manager.load_map(selected_map["filename"])
        if map_data.audio_file and map_data.audio_file != self.current_preview:
            audio_manager.stop()
            if audio_manager.load(map_data.audio_file):
                audio_manager.play(map_data.offset_ms)
                self.current_preview = map_data.audio_file

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for b in self.buttons.values(): b.update(mp)

    def refresh_data(self):
        self.data_manager.load_scores()
        self.maps = self.map_manager.list_maps()
        self.selected_index = min(self.selected_index, max(0, len(self.maps) - 1))
        self._play_preview()

    def _load_image(self, song_title):
        """Load an image from assets/images based on song title."""
        if song_title in self.image_cache:
            return self.image_cache[song_title]
        
        # Check for common image extensions
        base_path = os.path.join("assets", "images", song_title)
        path = base_path + ".jpg"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path)
                img = pygame.transform.scale(img, (360, 200))
                self.image_cache[song_title] = img
                return img
            except pygame.error:
                pass
        
        # No image found
        self.image_cache[song_title] = None
        return None

    def draw(self, surface):
        surface.fill(SLATE_NAVY)
        draw_grid_background(surface, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        padding_offset = 30 # roughly
        surface.blit(self.title_surf, (50 - padding_offset, 10))
        
        self.list_panel.draw(surface)
        self.preview_panel.draw(surface)
        
        self._draw_list(surface)
        self._draw_preview(surface)
        
        for b in self.buttons.values(): b.draw(surface)

    def _draw_list(self, surface):
        count = 10
        visible_maps = self.maps[:count]
        
        if not visible_maps:
            no_map = self.song_font.render("No Maps Found", True, WHITE)
            surface.blit(no_map, (70, 123))
            return

        for i, map_info in enumerate(visible_maps):
            y = 115 + i * 50
            r = pygame.Rect(60, y, 480, 45)
            
            if i == self.selected_index:
                pygame.draw.rect(surface, (*NEON_BLUE, 50), r, border_radius=4)
                pygame.draw.rect(surface, NEON_BLUE, r, 2, border_radius=4)
            else:
                pygame.draw.rect(surface, (*DARK_SLATE, 150), r, border_radius=4)
                
            t = self.song_font.render(map_info["title"], True, WHITE)
            surface.blit(t, (70, y + 8))
            
            # Draw star rating
            diff = int(map_info["difficulty"])
            star_size = 6
            start_x = 350
            for s in range(diff):
                draw_star(surface, start_x + s * 15, y + 22, star_size, WHITE)
    
    def _draw_preview(self, surface):
        if not self.maps: return
            
        map_info = self.maps[self.selected_index]
        # Use filename as ID for score lookups for now
        score_data = self.data_manager.get_score(map_info["filename"]) 
        
        px, py = 600, 100
        art_rect = pygame.Rect(px + 20, py + 20, 360, 200)
        pygame.draw.rect(surface, DARK_SLATE, art_rect)
        
        # Load image from local assets
        img = self._load_image(map_info["title"])
        if img:
            surface.blit(img, art_rect)
            pygame.draw.rect(surface, NEON_BLUE, art_rect, 2)
        else:
            pygame.draw.rect(surface, NEON_BLUE, art_rect, 2)
            no_img_txt = self.detail_font.render("No Image", True, GRAY)
            surface.blit(no_img_txt, no_img_txt.get_rect(center=art_rect.center))

        # Info
        info_y = py + 240
        t = self.song_font.render(map_info["title"], True, WHITE)
        surface.blit(t, (px + 20, info_y))
        
        a = self.detail_font.render(f"by {map_info['artist']}", True, GRAY)
        surface.blit(a, (px + 20, info_y + 35))
        
        stats_y = info_y + 80
        stats = [
            ("High Score", f"{score_data['score']:,}"),
            ("Max Combo", f"{score_data['combo']}x"),
            ("Rank", score_data['rank']),
        ]
        
        for i, (l, v) in enumerate(stats):
            lp = self.stat_font.render(l, True, GRAY)
            vp = self.stat_font.render(v, True, WHITE)
            surface.blit(lp, (px + 20, stats_y + i*30))
            surface.blit(vp, (px + 200, stats_y + i*30))

    def get_next_screen(self):
        n = self.next_screen
        self.next_screen = None
        return n
