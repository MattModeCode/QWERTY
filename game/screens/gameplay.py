import pygame
import math
import game.settings as settings
from game.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SLATE_NAVY, NEON_BLUE, WHITE, DARK_SLATE, GRAY,
    NUM_LANES, LANE_WIDTH, LANE_SPACING, PLAYFIELD_X, PLAYFIELD_WIDTH,
    LANE_KEYS, LANE_LETTERS,
    NOTE_RADIUS, HIT_LINE_Y, HIT_WINDOW,
    BASE_SCORE, COMBO_MULTIPLIER,
    MAX_HEALTH, HEALTH_DRAIN_PER_MISS, HEALTH_GAIN_PER_HIT,
    current_map_file
)
from game.map_manager import MapManager
from game.ui import draw_grid_background, draw_hit_line_glow, Button, FloatingText
from game.note import Note, HoldNote
from game.data_manager import DataManager
from game.visuals import create_neon_text
from game.audio_manager import audio_manager

# Judgement settings
JUDGEMENT_TIME = 0.5

class GameplayScreen:
    """Main gameplay screen."""
    
    def __init__(self):
        self.next_screen = None
        self.next_screen_args = None
        self.paused = False
        self.game_over = False
        self.song_complete = False
        self.game_over = False
        self.failed = False
        self.fail_timer = 0
        self.song_complete = False
        self.auto_end_timer = 0
        self.data_manager = DataManager()
        self.map_manager = MapManager()
        
        # Load Map
        if settings.current_map_file:
            self.map_data = self.map_manager.load_map(settings.current_map_file)
        else:
            # Fallback (should not happen in normal flow)
            self.map_data = self.map_manager.create_empty_map("No Map Loaded")
            
        self.song_title = self.map_data.title
        self.song_id = settings.current_map_file # Use filename as ID for now
        
        # Audio Init
        # Modified for 2s grace period
        self.playing_audio = False
        
        # Spawning Logic
        # Filter notes < 2000ms (Grace period ignore)
        self.hit_objects = [h for h in self.map_data.hit_objects if h['time'] >= 2000]
        self.active_notes = []
        self.current_time = -2000 # Start 2 seconds early (Grace wait)
        self.note_speed = 300 # pixels per second
        self.spawn_distance = SCREEN_HEIGHT + 100        
        # Stats
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.health = MAX_HEALTH
        
        self.perfects = 0
        self.greats = 0
        self.misses = 0
        self.spam_count = 0 
        
        # Visuals
        self.score_font = pygame.font.Font(None, 64)
        self.combo_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        self.lane_font = pygame.font.Font(None, 28)
        self.judge_font = pygame.font.Font(None, 40)
        self.percent_font = pygame.font.Font(None, 48)
        self.big_font = pygame.font.Font(None, 64)
        
        # Pre-render static neon texts
        self.paused_text = create_neon_text("PAUSED", self.big_font, WHITE, NEON_BLUE)
        
        # PAUSE MENU BUTTONS
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        btn_w, btn_h = 200, 50
        self.pause_buttons = {
            'resume': Button(cx - btn_w//2, cy + 50, btn_w, btn_h, "RESUME"),
            'restart': Button(cx - btn_w//2, cy + 120, btn_w, btn_h, "RESTART"),
            'select': Button(cx - btn_w//2, cy + 190, btn_w, btn_h, "SELECT SONG"),
            'menu': Button(cx - btn_w//2, cy + 260, btn_w, btn_h, "MAIN MENU"),
        }
        
        self.key_pressed = [False] * NUM_LANES
        self.hit_flash = [0] * NUM_LANES
        self.last_judgement = "" 
        self.judgement_timer = 0
        self.judgement_color = WHITE
        self.floating_texts = []
        
    def handle_event(self, event):
        # Pause Menu Interaction
        if self.paused:
            mp = pygame.mouse.get_pos()
            # Handle hover updates for buttons? Pass.
            
            for name, btn in self.pause_buttons.items():
                if btn.is_clicked(event):
                    if name == 'resume':
                        self.paused = False
                        audio_manager.unpause()
                    elif name == 'restart':
                        audio_manager.stop()
                        self.next_screen = 'gameplay' 
                    elif name == 'select':
                        audio_manager.stop()
                        self.next_screen = 'select'
                    elif name == 'menu':
                        audio_manager.stop()
                        self.next_screen = 'menu'
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.paused = False 
                audio_manager.unpause() 
            
            # Consume all other inputs while paused
            return 

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = True
                audio_manager.pause()
                return 

            if event.key == pygame.K_SPACE:
                if not (self.game_over or self.song_complete):
                    self.paused = not self.paused
                    if self.paused: audio_manager.pause()
                    else: audio_manager.unpause()
                return 

            if self.paused or self.game_over or self.song_complete or self.failed: return

            key_name = pygame.key.name(event.key)
            if key_name in LANE_KEYS:
                lane = LANE_KEYS.index(key_name)
                self.key_pressed[lane] = True
                
                # Check for Hit
                hit_note = None
                for note in self.active_notes:
                    if note.lane == lane and note.active and not note.hit:
                        if note.check_hit(HIT_LINE_Y, HIT_WINDOW):
                            if note.is_hold:
                                if not note.being_held and not note.was_held:
                                    note.being_held = True
                                    note.was_held = True
                                    note.initial_hit_offset = abs(note.y - HIT_LINE_Y)
                                    hit_note = note
                                    break
                            else:
                                note.active = False
                                note.hit = True
                                hit_note = note
                                break
                
                if hit_note:
                    if hit_note.is_hold:
                        self.hit_flash[lane] = 0.1
                        self._register_hit(hit_note, lane, is_initial_hold=True)
                    else:
                        self._register_hit(hit_note, lane)
                else:
                    # Spam Punish Check
                    nearby_note = False
                    for note in self.active_notes:
                        if note.lane == lane and note.active:
                            if abs(note.y - HIT_LINE_Y) < 200:
                                nearby_note = True
                                break
                    if not nearby_note:
                        self._register_limitless_spam_punish()

        elif event.type == pygame.KEYUP:
            key_name = pygame.key.name(event.key)
            if key_name in LANE_KEYS:
                lane = LANE_KEYS.index(key_name)
                self.key_pressed[lane] = False
                
                # Release Hold Logic
                for note in self.active_notes:
                    if note.lane == lane and note.is_hold and note.being_held and note.active:
                        note.being_held = False
                        # Early release punishment
                        self.combo = 0
                        self.last_judgement = "BREAK"
                        self.judgement_color = (200, 200, 200)
                        self.judgement_timer = 0.5
                        break 

    def update(self, dt):
        if self.paused: 
            mp = pygame.mouse.get_pos()
            for btn in self.pause_buttons.values(): btn.update(mp)
            return
        
        if self.failed:
            self.fail_timer -= dt
            if self.fail_timer <= 0:
                self.game_over = True
                self._finish_song()
            return # FREEZE everything else

        if self.health <= 0 and not self.failed and not self.game_over:
            self.failed = True
            self.fail_timer = 2.0 # Wait 2 seconds before showing result screen
            audio_manager.stop()
            # Screen Freeze
            return

            
        # Audio Start (Grace Period End)
        if not self.playing_audio and self.current_time >= 0:
             if self.map_data.audio_file:
                 if audio_manager.load(self.map_data.audio_file):
                     audio_manager.play(0)
                 self.playing_audio = True

        # Map Spawning Logic
        if self.playing_audio and audio_manager.is_playing:
            # Sync to audio time (more accurate)
            self.current_time = audio_manager.get_position()
        else:
            # Fallback or end of song
            self.current_time += dt * 1000 # Convert to ms
        
        # Spawn notes (look ahead)
        spawn_ahead_time = (self.spawn_distance / self.note_speed) * 1000 # ms
        
        while self.hit_objects and self.hit_objects[0]["time"] <= self.current_time + spawn_ahead_time:
            obj = self.hit_objects.pop(0)
            lane = obj["lane"]
            # Start position off-screen based on time difference
            time_until_hit = obj["time"] - self.current_time
            start_y = HIT_LINE_Y - (time_until_hit / 1000.0) * self.note_speed
            
            if obj["type"] == "hold":
                length_px = (obj.get("duration", 0) / 1000.0) * self.note_speed
                new_note = HoldNote(lane, self.note_speed, length_px, spawn_y=start_y)
            else:
                new_note = Note(lane, self.note_speed, spawn_y=start_y)
            
            self.active_notes.append(new_note)
            
        # Update active notes
        for note in self.active_notes:
            note.update(dt)
            # Check for misses (passed hit line)
            if not note.active and note.missed:
                 pass # Will be cleared below
        
        # Clear inactive/missed notes
        missed_count = 0
        active_list = []
        for n in self.active_notes:
            if n.missed:
                missed_count += 1
            elif n.active or (n.is_hold and (n.being_held or not n.was_held)): # Keep holds that are active or being held
                 # Slight hack for holds: check if fully done
                 if n.is_hold and not n.active: 
                     pass # It's done
                 else:
                     active_list.append(n)
            else:
                pass # Normal note hit
        self.active_notes = active_list
        
        for _ in range(missed_count):
            self._register_miss()

        # Check for song completion
        if not self.hit_objects and not self.active_notes and not self.song_complete:
            self.song_complete = True
            self._save_score()

        if self.game_over or self.song_complete:
            self.auto_end_timer += dt
            if self.auto_end_timer > 2.0:
                 self._finish_song()
        if self.game_over or self.song_complete:
            self.auto_end_timer += dt
            if self.auto_end_timer > 2.0:
                 self._finish_song()
            return 

        # Handle Hold Ticks
        for lane in range(NUM_LANES):
            if self.key_pressed[lane]:
                # Check active notes for holds being held
                for note in self.active_notes:
                    if note.lane == lane and note.is_hold and note.being_held and note.active:
                        # Check tick
                         tail_y = note.y - note.length
                         if tail_y >= HIT_LINE_Y:
                             note.active = False
                             note.hit = True
                             self._register_hit(None, lane, is_hold_complete=True)
                         else:
                             # Tick
                             self.score += 5 
                             self.health = min(MAX_HEALTH, self.health + 0.05)
                             self.hit_flash[lane] = 0.1
        
        for i in range(NUM_LANES):
            if self.hit_flash[i] > 0: self.hit_flash[i] -= dt
            
        if self.judgement_timer > 0:
            self.judgement_timer -= dt
        
        # Update floating texts
        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if ft.active]

    def _register_hit(self, note, lane=0, is_hold_complete=False, is_initial_hold=False):
        judgement = "PERFECT"
        value = 0
        color = (0, 255, 0)  # Green for Perfect
        
        if is_hold_complete:
            judgement = "PERFECT"
            value = 300
            self.perfects += 1
            color = (0, 255, 0)  # Green
        elif is_initial_hold:
            offset = note.initial_hit_offset
            if offset < 20:
                judgement = "PERFECT"
                value = 300
                self.perfects += 1
                color = (0, 255, 0)  # Green
            else:
                judgement = "GREAT"
                value = 100
                self.greats += 1
                color = (0, 150, 255)  # Blue
        elif note:
            offset = abs(note.y - HIT_LINE_Y)
            if offset < 20: 
                judgement = "PERFECT"
                value = 300
                self.perfects += 1
                self.health = min(MAX_HEALTH, self.health + 2)
                color = (0, 255, 0)  # Green
            else:
                judgement = "GREAT"
                value = 100
                self.greats += 1
                self.health = min(MAX_HEALTH, self.health + 1)
                color = (0, 150, 255)  # Blue

        self.last_judgement = judgement
        self.judgement_timer = JUDGEMENT_TIME
        self.judgement_color = color
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        
        # Score = Value * (Combo * DifficultyMultiplier)
        multiplier = getattr(self.map_data, "difficulty", 1)
        self.score += value * (self.combo * multiplier)
        
        # Spawn floating text at lane position
        lane_x = PLAYFIELD_X + lane * (LANE_WIDTH + LANE_SPACING) + LANE_WIDTH // 2
        self.floating_texts.append(FloatingText(judgement, lane_x, HIT_LINE_Y - 30, color))

    def _register_miss(self, lane=None):
        self.misses += 1
        self.combo = 0
        self.health = max(0, self.health - HEALTH_DRAIN_PER_MISS)
        self.last_judgement = "MISS"
        self.judgement_color = (255, 50, 50)
        self.judgement_timer = JUDGEMENT_TIME
        
        # Spawn floating text (center if lane unknown)
        if lane is not None:
            lane_x = PLAYFIELD_X + lane * (LANE_WIDTH + LANE_SPACING) + LANE_WIDTH // 2
        else:
            lane_x = SCREEN_WIDTH // 2
        self.floating_texts.append(FloatingText("MISS", lane_x, HIT_LINE_Y - 30, (255, 50, 50)))

    def _register_limitless_spam_punish(self):
        self.health = max(0, self.health - 5)
        if self.combo > 0: self.combo = 0
        # Spam penalty
        self.spam_count += 1

    def _get_accuracy(self):
        total_hits = self.perfects + self.greats + self.misses + self.spam_count
        if total_hits > 0:
            weighted_score = (self.perfects * 300 + self.greats * 100)
            max_possible = total_hits * 300
            return (weighted_score / max_possible) * 100
        return 100.0 if total_hits == 0 else 0.0


    def _save_score(self):
        accuracy = self._get_accuracy()
        if self.game_over: rank = "F"
        elif accuracy == 100: rank = "SS"
        elif accuracy >= 95: rank = "S"
        elif accuracy >= 90: rank = "A"
        elif accuracy >= 80: rank = "B"
        elif accuracy >= 70: rank = "C"
        else: rank = "D"

        stats = {
            'score': self.score,
            'combo': self.max_combo,
            'accuracy': accuracy,
            'rank': rank,
            'perfect': self.perfects,
            'great': self.greats,
            'miss': self.misses,
            'song_title': self.song_title
        }
        
        if not self.game_over:
            self.data_manager.submit_score(self.song_id, self.score, self.max_combo, rank, accuracy, stats)
        self.next_screen_args = stats

    def _finish_song(self):
        if not self.next_screen_args: self._save_score()
        audio_manager.stop()
        self.next_screen = 'result'

    def draw(self, surface):
        surface.fill(SLATE_NAVY)
        draw_grid_background(surface, SCREEN_WIDTH, SCREEN_HEIGHT)
        self._draw_lanes(surface)
        draw_hit_line_glow(surface, HIT_LINE_Y, PLAYFIELD_WIDTH, PLAYFIELD_X)
        self._draw_notes(surface)
        self._draw_hud(surface)
        
        if self.paused: 
            o = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            o.fill((0, 0, 0, 200))
            surface.blit(o, (0,0))
            
            r = self.paused_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            surface.blit(self.paused_text, r)
            
            for btn in self.pause_buttons.values():
                btn.draw(surface)
            return 
        
        if self.game_over or self.song_complete:
            o = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            o.fill((0, 0, 0, 100))
            surface.blit(o, (0,0))
        
        # Draw floating texts
        for ft in self.floating_texts:
            ft.draw(surface)

    def _draw_lanes(self, surface):
        for i in range(NUM_LANES):
            if i <= 3:
                x = PLAYFIELD_X + i * (LANE_WIDTH + LANE_SPACING) - 25
            else:
                x = PLAYFIELD_X + i * (LANE_WIDTH + LANE_SPACING) + 25

            if self.hit_flash[i] > 0:
                s = pygame.Surface((LANE_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((*NEON_BLUE, 30))
                surface.blit(s, (x, 0))
            pygame.draw.rect(surface, DARK_SLATE, (x, 0, LANE_WIDTH, SCREEN_HEIGHT))
            pygame.draw.line(surface, (*NEON_BLUE, 80), (x, 0), (x, SCREEN_HEIGHT), 1)
            hit_x = x + LANE_WIDTH // 2
            pygame.draw.circle(surface, NEON_BLUE, (hit_x, HIT_LINE_Y), NOTE_RADIUS, 2)
            if self.key_pressed[i]:
               pygame.draw.circle(surface, (*NEON_BLUE, 100), (hit_x, HIT_LINE_Y), NOTE_RADIUS-5)
            l = self.lane_font.render(LANE_LETTERS[i], True, GRAY)
            surface.blit(l, l.get_rect(center=(hit_x, HIT_LINE_Y+55)))

    def _draw_notes(self, surface):
        for note in self.active_notes:
            if note.lane <= 3:
                lane_x = PLAYFIELD_X + note.lane * (LANE_WIDTH + LANE_SPACING) + LANE_WIDTH // 2 - 25
            else:
                lane_x = PLAYFIELD_X + note.lane * (LANE_WIDTH + LANE_SPACING) + LANE_WIDTH // 2 + 25
            note.draw(surface, lane_x)

    def _draw_hud(self, surface):
        w, h = 300, 15
        x, y = 20, 20
        pygame.draw.rect(surface, DARK_SLATE, (x, y, w, h), border_radius=4)
        fill = int(w * (self.health / MAX_HEALTH))
        if fill > 0: pygame.draw.rect(surface, NEON_BLUE, (x, y, fill, h), border_radius=4)
        
        s_txt = self.score_font.render(f"{int(self.score):08d}", True, WHITE)
        score_rect = s_txt.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        surface.blit(s_txt, score_rect)
        
        acc = self._get_accuracy()
        acc_text = f"{acc:.2f}%"
        a_surf = self.percent_font.render(acc_text, True, NEON_BLUE)
        a_rect = a_surf.get_rect(topright=(SCREEN_WIDTH - 60, score_rect.bottom + 10))
        surface.blit(a_surf, a_rect)
        
        radius = 12
        cx = a_rect.left - 25
        cy = a_rect.centery
        pygame.draw.circle(surface, GRAY, (cx, cy), radius, 2)
        
        duration = self.map_data.get_duration_ms()
        progress = (self.current_time / duration) if duration > 0 else 0
        if progress > 0:
            r = radius - 2
            pie_s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            points = [(r, r)]
            start_angle = -90
            end_angle = start_angle + (360 * progress)
            step = 10
            for ang in range(int(start_angle), int(end_angle), step):
                rad = math.radians(ang)
                px = r + math.cos(rad) * r
                py = r + math.sin(rad) * r
                points.append((px, py))
            rad = math.radians(end_angle)
            px = r + math.cos(rad) * r
            py = r + math.sin(rad) * r
            points.append((px, py))
            if len(points) > 2:
                pygame.draw.polygon(pie_s, NEON_BLUE, points)
                surface.blit(pie_s, (cx-r, cy-r))

        if self.combo > 0:
            c_txt = self.combo_font.render(f"{self.combo}x", True, WHITE)
            surface.blit(c_txt, (20, SCREEN_HEIGHT - 80))


    def get_next_screen(self):
        n = self.next_screen
        self.next_screen = None
        return n, self.next_screen_args
