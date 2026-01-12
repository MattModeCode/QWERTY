import pygame
from game.settings import (
    LANE_LETTERS, NOTE_RADIUS, HIT_LINE_Y, NEON_BLUE, WHITE, HIT_WINDOW
)


class Note:
    """Standard failing note."""
    FONT = None

    def __init__(self, lane, note_speed, spawn_y=0):
        self.lane = lane
        self.letter = LANE_LETTERS[lane]
        
        if Note.FONT is None:
            Note.FONT = pygame.font.Font(None, 32)
        self.font = Note.FONT
        
        self.y = float(spawn_y)
        self.speed = note_speed
        self.active = True
        self.hit = False
        self.missed = False
        self.is_hold = False

    def update(self, dt):
        if self.active:
            self.y += self.speed * dt
            if self.y > HIT_LINE_Y + HIT_WINDOW + 20: 
                self.active = False
                self.missed = True

    def draw(self, surface, x):
        if not self.active: return
        
        center = (x, self.y)
        for i in range(2):
            r = NOTE_RADIUS + 4 + i*4
            s = pygame.Surface((int(r*2), int(r*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*NEON_BLUE, 50-i*20), (r, r), r, 2)
            surface.blit(s, (x-r, self.y-r))
            
        pygame.draw.circle(surface, NEON_BLUE, center, NOTE_RADIUS, 3)
        pygame.draw.circle(surface, (*NEON_BLUE, 40), center, NOTE_RADIUS-4)
        
        txt = self.font.render(self.letter, True, WHITE)
        surface.blit(txt, txt.get_rect(center=(int(x), int(self.y))))

    def check_hit(self, hit_y, tolerance):
        return self.active and abs(self.y - hit_y) <= tolerance

class HoldNote(Note):
    """Note that must be held for a duration."""
    def __init__(self, lane, note_speed, length_px, spawn_y=0):
        super().__init__(lane, note_speed, spawn_y)
        self.is_hold = True
        self.length = float(length_px)
        self.being_held = False
        self.was_held = False
        self.initial_hit_offset = 0
        
    def update(self, dt):
        if self.active:
            self.y += self.speed * dt
            
            if not self.being_held:
                if self.was_held:
                    tail_y = self.y - self.length
                    if tail_y > HIT_LINE_Y + HIT_WINDOW + 20:
                        self.active = False
                else:
                    if self.y > HIT_LINE_Y + HIT_WINDOW + 20:
                        self.active = False
                        self.missed = True

    def draw(self, surface, x):
        if not self.active: return
        
        width = int(NOTE_RADIUS * 1.2)
        tail_y = self.y - self.length
        
        if self.being_held:
            if tail_y < HIT_LINE_Y:
                rect_h = HIT_LINE_Y - tail_y
                trail_rect = (x - width/2, tail_y, width, rect_h)
                
                pygame.draw.rect(surface, (200, 255, 255), trail_rect, border_radius=width//2)
                pygame.draw.rect(surface, NEON_BLUE, trail_rect, 3, border_radius=width//2)
                pygame.draw.circle(surface, WHITE, (x, HIT_LINE_Y), NOTE_RADIUS, 2)
        else:
            trail_rect = (x - width/2, tail_y, width, self.length)
            
            color = NEON_BLUE
            alpha = 100
            
            if self.was_held and not self.being_held:
                color = (50, 50, 50) 
                alpha = 80 
                pygame.draw.rect(surface, (100, 100, 100), trail_rect, 1, border_radius=width//2)
            else:
                pygame.draw.rect(surface, color, trail_rect, 2, border_radius=width//2)
            
            s = pygame.Surface((width, int(self.length)), pygame.SRCALPHA)
            pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=width//2)
            surface.blit(s, (x - width//2, tail_y))
            
            if not self.was_held:
                super().draw(surface, x)
