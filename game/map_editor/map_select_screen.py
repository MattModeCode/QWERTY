"""
Map Selection Screen for Editor - Choose existing maps or create new ones.
"""
import pygame
import os
from game.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SLATE_NAVY, NEON_BLUE, WHITE, DARK_SLATE, GRAY
)
from game.ui import Button, Panel, draw_grid_background
from game.map_manager import MapManager, MAPS_DIR
from game.visuals import create_neon_text, draw_star
from game.audio_manager import audio_manager


# Define Assets Path
ASSETS_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "audio")

STATE_SELECT = 0
STATE_IMPORT = 1

class MapSelectScreen:
    """Screen for selecting maps to edit or creating new ones."""
    
    def __init__(self):
        self.next_screen = None
        self.map_manager = MapManager()
        
        self.state = STATE_SELECT
        
        # Select State Data
        self.maps = self.map_manager.list_maps()
        self.selected_index = 0
        
        # Import State Data
        self.audio_files = []
        self.import_index = 0
        
        self.title_font = pygame.font.Font(None, 64)
        self.title_surf = create_neon_text("MAP EDITOR", self.title_font, WHITE, NEON_BLUE)
        
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        
        btn_y = SCREEN_HEIGHT - 70
        self.buttons = {
            'new': Button(50, btn_y, 140, 45, "NEW MAP"),
            'edit': Button(210, btn_y, 140, 45, "EDIT"),
            'back': Button(SCREEN_WIDTH - 130, btn_y, 100, 45, "BACK"),
            'import': Button(SCREEN_WIDTH - 250, btn_y, 100, 45, "IMPORT"), # New Import Button
        }
        
        self.list_panel = Panel(50, 100, SCREEN_WIDTH - 100, 500)
        self.message = ""
        self.message_timer = 0
        

        
    def handle_event(self, event):
        # Universal Back
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == STATE_IMPORT:
                self.state = STATE_SELECT
                self.message = ""
            else:
                audio_manager.stop()
                self.next_screen = 'menu'
            return

        # Handle States
        if self.state == STATE_SELECT:
            self._handle_select_event(event)
        elif self.state == STATE_IMPORT:
            self._handle_import_event(event)

        # Draw & Drop always active
        if event.type == pygame.DROPFILE:
            if event.file.lower().endswith(('.mp3', '.ogg', '.wav')):
                self._import_audio_file(event.file)
            else:
                self.message = "Only mp3/ogg/wav allowed"
                self.message_timer = 3.0

    def _handle_select_event(self, event):
        for name, btn in self.buttons.items():
            if btn.is_clicked(event):
                if name == 'new':
                    self._switch_to_import()
                elif name == 'edit':
                    self._edit_selected()
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
                self._edit_selected()
            elif event.key == pygame.K_n:
                self._switch_to_import()
            
            if prev_index != self.selected_index:
                self._load_preview()
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            prev_index = self.selected_index
            # List click logic
            for i in range(len(self.maps)):
                y = 115 + i * 45
                if y > 580: break
                r = pygame.Rect(60, y, SCREEN_WIDTH - 120, 40)
                if r.collidepoint(event.pos):
                    self.selected_index = i
            
            if prev_index != self.selected_index:
                self._load_preview()

    def _handle_import_event(self, event):
        # Navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.import_index = max(0, self.import_index - 1)
            elif event.key == pygame.K_DOWN:
                self.import_index = min(len(self.audio_files) - 1, self.import_index + 1)
            elif event.key == pygame.K_RETURN:
                if self.audio_files:
                     fname = self.audio_files[self.import_index]
                     full_path = os.path.join(ASSETS_AUDIO_DIR, fname)
                     self._import_audio_file(full_path)
            elif event.key == pygame.K_BACKSPACE:
                self.state = STATE_SELECT

        # Click handling for import list
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check back button mainly
            if self.buttons['back'].is_clicked(event):
                self.state = STATE_SELECT
                return
            
            if self.buttons['import'].is_clicked(event):
                 if self.audio_files:
                     fname = self.audio_files[self.import_index]
                     full_path = os.path.join(ASSETS_AUDIO_DIR, fname)
                     self._import_audio_file(full_path)
                 return

            for i in range(len(self.audio_files)):
                y = 115 + i * 45
                if y > 580: break
                r = pygame.Rect(60, y, SCREEN_WIDTH - 120, 40)
                if r.collidepoint(event.pos):
                    self.import_index = i
                    # Double click logic could go here, but single click select + enter is fine
                    # Or maybe creating on click? No, let's stick to select-then-action or similar.
                    # Actually standard UI is: click to select. Double click to confirm.
                    # For simplicity: Click selects. Enter confirms.
                    pass

    def _switch_to_import(self):
        self.state = STATE_IMPORT
        self.audio_files = []
        if os.path.exists(ASSETS_AUDIO_DIR):
            for f in os.listdir(ASSETS_AUDIO_DIR):
                if f.lower().endswith(('.mp3', '.ogg', '.wav')):
                    self.audio_files.append(f)
            self.audio_files.sort()
        else:
            self.message = f"Audio dir not found: {ASSETS_AUDIO_DIR}"
            self.message_timer = 4.0
        self.import_index = 0

    def _import_audio_file(self, source_path):
        """Create a new map from the source audio file."""
        filename = os.path.basename(source_path)
        
        map_name = os.path.splitext(filename)[0]
        # Avoid duplicate map names
        base_name = map_name
        counter = 1
        while os.path.exists(os.path.join(MAPS_DIR, f"{map_name}.json")):
            map_name = f"{base_name}_{counter}"
            counter += 1

        new_map = self.map_manager.create_empty_map(map_name, bpm=120)
        new_map["audio"]["file"] = filename
        
        map_filename = f"{map_name}.json"
        
        if self.map_manager.save_map(map_filename, new_map):
            self.maps = self.map_manager.list_maps()
            # Find new map index
            for i, m in enumerate(self.maps):
                if m["filename"] == map_filename:
                    self.selected_index = i
                    break
            
            # Switch to editor
            audio_manager.stop()
            self.next_screen = ('editor', map_filename)
        else:
            self.message = "Failed to save map JSON"
            self.message_timer = 3.0
    
    def _edit_selected(self):
        """Start editing the selected map."""
        if self.maps and 0 <= self.selected_index < len(self.maps):
            selected = self.maps[self.selected_index]
            audio_manager.stop()
            self.next_screen = ('editor', selected["filename"])
    
    def _load_preview(self):
        """Load and play audio preview for selected map."""
        if self.state != STATE_SELECT: return
        
        if not self.maps or self.selected_index >= len(self.maps):
            return
        
        selected_map = self.maps[self.selected_index]
        pass
    
    def update(self, dt):
        mp = pygame.mouse.get_pos()
        if self.state == STATE_SELECT:
             for btn in self.buttons.values():
                 btn.update(mp)
        elif self.state == STATE_IMPORT:
             # Back and Import active
             self.buttons['back'].update(mp)
             self.buttons['import'].update(mp)
        
        if self.message_timer > 0:
            self.message_timer -= dt
    
    def draw(self, surface):
        surface.fill(SLATE_NAVY)
        draw_grid_background(surface, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        title_text = "NEW MAP: SELECT AUDIO" if self.state == STATE_IMPORT else "MAP EDITOR"
        t_surf = create_neon_text(title_text, self.title_font, WHITE, NEON_BLUE)
        t_rect = t_surf.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(t_surf, t_rect)
        
        self.list_panel.draw(surface)
        
        if self.state == STATE_SELECT:
            self._draw_map_list(surface)
            # Only draw specific buttons for this state (Hide import)
            self.buttons['new'].draw(surface)
            self.buttons['edit'].draw(surface)
            self.buttons['back'].draw(surface)
            
        elif self.state == STATE_IMPORT:
            self._draw_import_list(surface)
            self.buttons['back'].draw(surface)
            self.buttons['import'].draw(surface)
            
            # Instructions removed as requested
            # instr = self.small_font.render("UP/DOWN: Select | ENTER: Import | ESC/BACK: Cancel", True, GRAY)
            # surface.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, SCREEN_HEIGHT - 25))

        if self.message_timer > 0:
            msg_surf = self.font.render(self.message, True, (255, 100, 100))
            surface.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, 85))

    def _draw_map_list(self, surface):
        if not self.maps:
            no_map = self.font.render("No maps found. Press N to create.", True, GRAY)
            surface.blit(no_map, (70, 130))
            return
        
        # Simple pagination logic could be added here, currently just top 10
        max_visible = 10
        start = 0
        if self.selected_index >= max_visible:
             start = self.selected_index - max_visible + 1
             
        visible_maps = self.maps[start : start + max_visible]
        
        for i, map_info in enumerate(visible_maps):
            real_index = start + i
            y = 115 + i * 45
            r = pygame.Rect(60, y, SCREEN_WIDTH - 120, 40)
            
            if real_index == self.selected_index:
                pygame.draw.rect(surface, (*NEON_BLUE, 50), r, border_radius=4)
                pygame.draw.rect(surface, NEON_BLUE, r, 2, border_radius=4)
            else:
                pygame.draw.rect(surface, (*DARK_SLATE, 150), r, border_radius=4)
            
            title = self.font.render(map_info["title"], True, WHITE)
            surface.blit(title, (70, y + 8))
            
            diff_val = int(map_info['difficulty'])
            star_size = 5
            # Draw from right side
            star_start_x = SCREEN_WIDTH - 180
            for s in range(diff_val):
                draw_star(surface, star_start_x + s * 12, y + 20, star_size, WHITE)

    def _draw_import_list(self, surface):
        if not self.audio_files:
            no_audio = self.font.render("No audio files found in assets/audio", True, GRAY)
            surface.blit(no_audio, (70, 130))
            return
        
        max_visible = 10
        start = 0
        if self.import_index >= max_visible:
             start = self.import_index - max_visible + 1
             
        visible_files = self.audio_files[start : start + max_visible]
        for i, fname in enumerate(visible_files):
            real_index = start + i
            y = 115 + i * 45
            r = pygame.Rect(60, y, SCREEN_WIDTH - 120, 40)
            
            if real_index == self.import_index:
                pygame.draw.rect(surface, (*NEON_BLUE, 50), r, border_radius=4)
                pygame.draw.rect(surface, NEON_BLUE, r, 2, border_radius=4)
            else:
                pygame.draw.rect(surface, (*DARK_SLATE, 150), r, border_radius=4)
            
            name_surf = self.font.render(fname, True, WHITE)
            surface.blit(name_surf, (70, y + 8))

    def get_next_screen(self):
        n = self.next_screen
        self.next_screen = None
        return n
