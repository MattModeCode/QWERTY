"""
Main Map Editor Screen - Osu-style timeline editor.
"""
import pygame
import math
from game.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SLATE_NAVY, NEON_BLUE, WHITE, DARK_SLATE, GRAY,
    NUM_LANES, LANE_WIDTH, LANE_SPACING, PLAYFIELD_X,
    LANE_LETTERS
)
from game.ui import Button, draw_grid_background, InputField, Dropdown
from game.map_manager import MapManager
from game.audio_manager import audio_manager


class EditorScreen:
    """Osu-style map editor with vertical timeline, flexible snapping, and variable playback."""
    
    def __init__(self, map_filename: str):
        self.next_screen = None
        self.map_manager = MapManager()
        self.map_data = self.map_manager.load_map(map_filename)
        self.filename = map_filename
        
        # --- Map Metadata ---
        self.map_title = self.map_data.title
        self.bpm = float(self.map_data.bpm)
        self.offset_ms = float(self.map_data.offset_ms)
        self.audio_file = self.map_data.audio_file
        
        # --- Editor State ---
        self.hit_objects = self.map_data.hit_objects.copy()
        self.current_time = 0
        self.playing = False
        
        # Timeline settings
        self.pixels_per_ms = 0.5    # Zoom level
        self.grid_start_y = 100
        self.grid_height = 500
        self.hit_line_y = self.grid_start_y + self.grid_height - 50 # Where "now" is
        
        # Snap & Speed Settings
        self.snap_options = ["1/1", "1/2", "1/4", "1/8"]
        self.speed_options = ["100%", "75%", "50%", "25%"]
        
        # Hold creation state
        self.creating_hold = False
        self.hold_start_lane = None
        self.hold_start_time = None
        
        # Audio
        audio_manager.load(self.audio_file)
        
        # --- UI Components ---
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # Inputs (Manual typing)
        self.bpm_input = InputField(SCREEN_WIDTH - 220, 150, 80, 30, "BPM", str(self.bpm))
        self.offset_input = InputField(SCREEN_WIDTH - 120, 150, 80, 30, "Offset", str(self.offset_ms))
        self.diff_input = InputField(SCREEN_WIDTH - 220, 290, 80, 30, "Stars", str(self.map_data.difficulty))
        
        # Dropdowns
        self.snap_dropdown = Dropdown(SCREEN_WIDTH - 220, 80, 180, 30, "Snap Divisor", self.snap_options)
        self.snap_dropdown.set_value("1/4") # Default
        
        self.speed_dropdown = Dropdown(SCREEN_WIDTH - 220, 220, 180, 30, "Playback Speed", self.speed_options)
        
        # Buttons
        btn_y = SCREEN_HEIGHT - 60
        self.buttons = {
            'save': Button(SCREEN_WIDTH - 260, btn_y, 120, 45, "SAVE"),
            'back': Button(SCREEN_WIDTH - 130, btn_y, 100, 45, "BACK"),
        }
        
        self.save_message = ""
        self.save_message_timer = 0

    def handle_event(self, event):
        # Update inputs
        self.bpm_input.handle_event(event)
        self.offset_input.handle_event(event)
        self.diff_input.handle_event(event)
        
        # If inputs changed, update values
        if self.bpm_input.value and self.bpm_input.value != str(self.bpm):
             self.bpm = float(self.bpm_input.value)
        if self.offset_input.value and self.offset_input.value != str(self.offset_ms):
             self.offset_ms = float(self.offset_input.value)
        if self.diff_input.value and self.diff_input.value != str(self.map_data.difficulty):
             self.map_data.difficulty = float(self.diff_input.value)
        
        # Click handling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # UI Clicks
                if self.snap_dropdown.handle_click(event): return
                if self.speed_dropdown.handle_click(event): 
                    # Handle speed change logic if needed immediately
                    pass
                for name, btn in self.buttons.items():
                    if btn.is_clicked(event):
                        if name == 'save': self._save_map()
                        if name == 'back': 
                            audio_manager.stop()
                            self.next_screen = 'map_select'
                        return
                
                # Input focus check is handled inside their classes, but check click area
                if not (self.bpm_input.rect.collidepoint(event.pos) or \
                        self.offset_input.rect.collidepoint(event.pos) or \
                        self.diff_input.rect.collidepoint(event.pos)):
                     # Grid interaction
                     self._handle_grid_click(event.pos)

        # Mouse Up (Finish Hold)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.creating_hold:
                self._finish_hold(event.pos)

        # Scrolling (Seek / Zoom)
        if event.type == pygame.MOUSEWHEEL:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                # Zoom
                self.pixels_per_ms = max(0.1, min(2.0, self.pixels_per_ms + event.y * 0.05))
            else:
                # Seek
                audio_manager.stop()
                self.playing = False
                scroll_amount = 200 * (1 if self.speed_dropdown.get_value() == "100%" else 0.5)
                self.current_time = max(0, self.current_time - event.y * scroll_amount)

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if self.bpm_input.focused or self.offset_input.focused or self.diff_input.focused:
                return # Don't trigger shortcuts while typing
                
            if event.key == pygame.K_SPACE:
                self._toggle_play()
            elif event.key == pygame.K_RIGHT:
                self.current_time += 100
                audio_manager.seek(self.current_time)
            elif event.key == pygame.K_LEFT:
                self.current_time = max(0, self.current_time - 100)
                audio_manager.seek(self.current_time)
            elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                self._delete_nearest()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        
        # Update UI
        self.bpm_input.update(dt)
        self.offset_input.update(dt)
        self.diff_input.update(dt)
        self.snap_dropdown.update(mp)
        self.speed_dropdown.update(mp)
        for btn in self.buttons.values(): btn.update(mp)
        
        # Audio Sync
        if self.playing:
            # Handle speed simulation (visual only for now as pygame doesn't support variable rate easily)
            rate_str = self.speed_dropdown.get_value()
            rate = 1.0
            if rate_str == "75%": rate = 0.75
            elif rate_str == "50%": rate = 0.5
            elif rate_str == "25%": rate = 0.25
            
            if rate == 1.0:
                 if audio_manager.is_playing:
                     self.current_time = audio_manager.get_position() + self.offset_ms
                 else:
                     self.playing = False # Audio stopped
            else:
                # Simulated playback for slow motion
                self.current_time += (dt * 1000) * rate
        
        if self.save_message_timer > 0:
            self.save_message_timer -= dt

    def draw(self, surface):
        surface.fill(SLATE_NAVY)
        draw_grid_background(surface, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Draw Main Grid
        self._draw_grid(surface)
        
        # Draw Sidebar Timeline
        self._draw_sidebar_timeline(surface)
        
        # Draw UI
        self.bpm_input.draw(surface)
        self.offset_input.draw(surface)
        self.diff_input.draw(surface)
        self.snap_dropdown.draw(surface)
        self.speed_dropdown.draw(surface)
        
        for btn in self.buttons.values(): btn.draw(surface)
        
        # Text Info
        title_surf = self.title_font.render(f"Edit: {self.map_title}", True, WHITE)
        surface.blit(title_surf, (20, 20))
        
        time_str = f"Time: {int(self.current_time)}ms | Snap: {self.snap_dropdown.get_value()}"
        time_surf = self.font.render(time_str, True, NEON_BLUE)
        surface.blit(time_surf, (20, 60))
        
        status_color = (100, 255, 100) if self.playing else (255, 100, 100)
        status_text = "PLAYING" if self.playing else "PAUSED"
        if not self.audio_file: status_text += " (No Audio)"
        
        stat_surf = self.font.render(f"State: {status_text}", True, status_color)
        surface.blit(stat_surf, (20, 90))
        
        if self.save_message_timer > 0:
            msg = self.font.render(self.save_message, True, (100, 255, 100))
            surface.blit(msg, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100))

    def _draw_grid(self, surface):
        # Background for lanes
        for i in range(NUM_LANES):
            x = PLAYFIELD_X + i * (LANE_WIDTH + LANE_SPACING)
            lane_rect = pygame.Rect(x, self.grid_start_y, LANE_WIDTH, self.grid_height)
            pygame.draw.rect(surface, (20, 20, 30), lane_rect)
            pygame.draw.rect(surface, (50, 50, 70), lane_rect, 1)
            
            # Draw Hit Line (Current Time)
            pygame.draw.line(surface, WHITE, (x, self.hit_line_y), (x + LANE_WIDTH, self.hit_line_y), 2)
            
            # Lane Key
            let = self.font.render(LANE_LETTERS[i], True, GRAY)
            surface.blit(let, (x + LANE_WIDTH//2 - 5, self.hit_line_y + 10))

        # Render Notes
        # We render from [current_time - view_ms, current_time + view_ms]
        view_ms = (self.hit_line_y - self.grid_start_y) / self.pixels_per_ms
        
        for obj in self.hit_objects:
            # Check visibility
            if obj["time"] < self.current_time - 1000 or obj["time"] > self.current_time + view_ms:
                continue
                
            lane_x = PLAYFIELD_X + obj["lane"] * (LANE_WIDTH + LANE_SPACING)
            
            # Position relative to hit_line_y
            # Note Time > Current Time -> appears above (y smaller)
            dt = obj["time"] - self.current_time
            y_pos = self.hit_line_y - (dt * self.pixels_per_ms)
            
            if y_pos < self.grid_start_y: continue
            
            color = NEON_BLUE
            
            if obj["type"] == "hold":
                dur_px = obj["duration"] * self.pixels_per_ms
                # Draw tail
                pygame.draw.rect(surface, (*color, 100), (lane_x + 5, y_pos - dur_px, LANE_WIDTH - 10, dur_px))
                # Head
                pygame.draw.circle(surface, color, (lane_x + LANE_WIDTH//2, y_pos), LANE_WIDTH//2 - 4)
                # End circle
                pygame.draw.circle(surface, color, (lane_x + LANE_WIDTH//2, y_pos - dur_px), LANE_WIDTH//2 - 8)
            else:
                pygame.draw.circle(surface, color, (lane_x + LANE_WIDTH//2, y_pos), LANE_WIDTH//2 - 4)
                pygame.draw.circle(surface, WHITE, (lane_x + LANE_WIDTH//2, y_pos), LANE_WIDTH//2 - 8, 2)

    def _draw_sidebar_timeline(self, surface):
        """Draw mathematical beat ticks on the right side."""
        x_base = SCREEN_WIDTH - 40
        y_base = self.hit_line_y
        
        # Line for current time
        pygame.draw.line(surface, WHITE, (x_base - 10, y_base), (x_base + 10, y_base), 2)
        
        # Calculate Beat Range
        ms_per_beat = 60000 / self.bpm if self.bpm > 0 else 1000
        view_ms = (self.hit_line_y - self.grid_start_y) / self.pixels_per_ms
        
        start_time = self.current_time
        end_time = self.current_time + view_ms
        
        # Find first beat index before start time logic... actually easier to iterate forward
        # Beat time = offset + index * ms_per_beat
        # index = (time - offset) / ms_per_beat
        
        start_index = math.floor((start_time - self.offset_ms) / ms_per_beat)
        end_index = math.ceil((end_time - self.offset_ms) / ms_per_beat)
        
        # We need to draw subdivisions too based on snaps.
        # Max snap is 1/8, so iterate by 0.125 beats
        
        # Optimize loop
        step = 0.125 
        current_beat = start_index
        
        while current_beat <= end_index + 1:
            beat_time = self.offset_ms + current_beat * ms_per_beat
            
            if beat_time > end_time:
                break
                
            if beat_time >= start_time - 100: # Small buffer
                dt = beat_time - start_time
                y_pos = y_base - (dt * self.pixels_per_ms)
                
                if self.grid_start_y <= y_pos <= self.grid_start_y + self.grid_height:
                    # Determine Tick Color/Size
                    is_beat = abs(current_beat % 1) < 0.001
                    is_half = abs(current_beat % 0.5) < 0.001
                    is_quarter = abs(current_beat % 0.25) < 0.001
                    is_eighth = abs(current_beat % 0.125) < 0.001
                    
                    color = None
                    width = 0
                    
                    if is_beat:
                        color = WHITE
                        width = 30
                        thickness = 3
                    elif is_half:
                        color = (255, 50, 50) # Red
                        width = 20
                        thickness = 2
                    elif is_quarter:
                        color = (50, 50, 255) # Blue
                        width = 15
                        thickness = 1
                    elif is_eighth:
                        color = (200, 200, 50) # Yellowish
                        width = 10
                        thickness = 1
                    
                    if color:
                        pygame.draw.line(surface, color, (x_base - width//2, y_pos), (x_base + width//2, y_pos), thickness)
            
            current_beat += step

    def _toggle_play(self):
        if self.speed_dropdown.get_value() != "100%":
            # Simulate play
            self.playing = not self.playing
            if self.playing: audio_manager.stop() # Silence real audio
        else:
            # Normal play
            if self.playing:
                audio_manager.pause()
                self.playing = False
            else:
                audio_manager.play(self.current_time)
                self.playing = True

    def _handle_grid_click(self, pos):
        # Convert Y to Time
        # y = hit_line - (dt * pixels_per_ms)
        # dt = (hit_line - y) / pixels
        # time = current + dt
        
        if pos[1] < self.grid_start_y or pos[1] > self.hit_line_y:
            return
            
        lane = self._get_lane_at_x(pos[0])
        if lane is None: return
        
        click_dt = (self.hit_line_y - pos[1]) / self.pixels_per_ms
        raw_time = self.current_time + click_dt
        
        # Snap Logic
        snapped_time = self._snap_time(raw_time)
        
        # Creating or Placing?
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_SHIFT:
            self._start_hold(lane, snapped_time)
        else:
            self._place_note(lane, snapped_time)

    def _snap_time(self, t):
        """Snap time to nearest divisor beat."""
        if self.bpm <= 0: return t
        
        ms_per_beat = 60000 / self.bpm
        snap_str = self.snap_dropdown.get_value()
        
        divisor = 1
        if snap_str == "1/2": divisor = 0.5
        elif snap_str == "1/4": divisor = 0.25
        elif snap_str == "1/8": divisor = 0.125
        
        snap_interval = ms_per_beat * divisor
        
        # Transform to beat-space relative to offset
        rel_t = t - self.offset_ms
        
        # Round to nearest interval
        snapped_rel = round(rel_t / snap_interval) * snap_interval
        
        return self.offset_ms + snapped_rel

    def _place_note(self, lane, time):
        # Remove existing at same spot
        for obj in self.hit_objects[:]:
            if obj["lane"] == lane and abs(obj["time"] - time) < 10:
                self.hit_objects.remove(obj)
                return
        
        # Add new
        self.hit_objects.append({
            "type": "beat",
            "lane": lane,
            "time": time
        })

    def _start_hold(self, lane, time):
        self.creating_hold = True
        self.hold_start_lane = lane
        self.hold_start_time = time

    def _finish_hold(self, pos):
        if not self.creating_hold: return
        
        # Logic similar to grid click to find end time
        click_dt = (self.hit_line_y - pos[1]) / self.pixels_per_ms
        raw_time = self.current_time + click_dt
        snapped_end = self._snap_time(raw_time)
        
        if snapped_end > self.hold_start_time:
             self.hit_objects.append({
                "type": "hold",
                "lane": self.hold_start_lane,
                "time": self.hold_start_time,
                "duration": snapped_end - self.hold_start_time
            })
        
        self.creating_hold = False

    def _delete_nearest(self):
        # Find closest note to current time and remove
        closest = None
        min_dist = 200
        for obj in self.hit_objects:
            dist = abs(obj["time"] - self.current_time)
            if dist < min_dist:
                min_dist = dist
                closest = obj
        
        if closest:
            self.hit_objects.remove(closest)

    def _get_lane_at_x(self, x):
        if x < PLAYFIELD_X: return None
        rel = x - PLAYFIELD_X
        # Gap math
        total_lane_w = LANE_WIDTH + LANE_SPACING
        idx = int(rel // total_lane_w)
        if 0 <= idx < NUM_LANES:
            # Check if inside lane rect (ignore spacing gap)
            lane_start = idx * total_lane_w
            if rel - lane_start <= LANE_WIDTH:
                return idx
        return None

    def _save_map(self):
        # Sort objects by time
        self.hit_objects.sort(key=lambda x: x["time"])
        
        map_dict = {
            "metadata": {
                "title": self.map_title,
                "artist": "Unknown",
                "mapper": "Crowvic",
                "difficulty": self.map_data.difficulty
            },
            "audio": {
                "file": self.audio_file,
                "bpm": self.bpm,
                "offset_ms": self.offset_ms
            },
            "hit_objects": self.hit_objects
        }
        
        if self.map_manager.save_map(self.filename, map_dict):
            self.save_message = "Map Saved!"
            self.save_message_timer = 2.0
            
    def get_next_screen(self):
        n = self.next_screen
        self.next_screen = None
        return n
