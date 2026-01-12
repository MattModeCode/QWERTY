import pygame

import random
from game.settings import (
    NEON_BLUE, WHITE, DARK_SLATE, SLATE_NAVY, GRAY,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_RADIUS,
    SCREEN_WIDTH, SCREEN_HEIGHT
)


class Button:
    """Button matching mockup: border, icon placeholder, text, neon hover glow."""
    
    FONT = None
    SMALL_FONT = None

    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        
        if Button.FONT is None:
            Button.FONT = pygame.font.Font(None, 22)
            Button.SMALL_FONT = pygame.font.Font(None, 14)
            
        self.font = Button.FONT
        self.small_font = Button.SMALL_FONT
    
    def draw(self, surface):
        color = NEON_BLUE if self.hovered else WHITE
        
        # Glow effect when hovered
        if self.hovered:
            for i in range(3):
                glow_rect = self.rect.inflate(6 + i * 4, 6 + i * 4)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                alpha = 30 - i * 10
                pygame.draw.rect(glow_surf, (*NEON_BLUE, alpha), glow_surf.get_rect(), border_radius=BUTTON_RADIUS + 2)
                surface.blit(glow_surf, glow_rect.topleft)
        
        # Button border
        pygame.draw.rect(surface, color, self.rect, 2, BUTTON_RADIUS)
        
        # Text
        text_surf = self.font.render(self.text, True, color)
        text_x = self.rect.centerx - text_surf.get_width() // 2
        text_rect = text_surf.get_rect(midleft=(text_x, self.rect.centery + 2))
        surface.blit(text_surf, text_rect)

    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False



class Panel:
    """Container panel with neon border."""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, surface):
        # Semi-transparent fill
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((*SLATE_NAVY, 220))
        surface.blit(s, self.rect.topleft)
        
        # Neon border
        pygame.draw.rect(surface, NEON_BLUE, self.rect, 2, 8)


def draw_neon_title(surface, text, font, center_x, center_y):
    """Draw title with multi-layer neon glow effect"""
    # Outer glow layers
    for i in range(4):
        glow_alpha = 40 - i * 10
        glow_offset = (4 - i) * 2
        glow_surf = font.render(text, True, (*NEON_BLUE[:3], glow_alpha))
        glow_rect = glow_surf.get_rect(center=(center_x, center_y))
        # Create glow by drawing multiple offset versions
        for dx in range(-glow_offset, glow_offset + 1, 2):
            for dy in range(-glow_offset, glow_offset + 1, 2):
                surface.blit(glow_surf, (glow_rect.x + dx, glow_rect.y + dy))
    
    # Main text
    text_surf = font.render(text, True, NEON_BLUE)
    text_rect = text_surf.get_rect(center=(center_x, center_y))
    surface.blit(text_surf, text_rect)


def draw_grid_background(surface, width, height):
    """Draw perspective neon grid matching mockups exactly."""
    # Vertical grid lines
    grid_spacing = 60
    for x in range(0, width + grid_spacing, grid_spacing):
        pygame.draw.line(surface, DARK_SLATE, (x, 0), (x, height), 1)
    
    # Horizontal grid lines
    for y in range(0, height + grid_spacing, grid_spacing):
        pygame.draw.line(surface, DARK_SLATE, (0, y), (width, y), 1)

    
    # Center horizontal glow line
    center_y = height // 2 + 60
    pygame.draw.line(surface, NEON_BLUE, (0, center_y), (width, center_y), 2)
    
    # Additional glow effect on center line
    for i in range(1, 4):
        alpha = 60 - i * 15
        line_surf = pygame.Surface((width, 4), pygame.SRCALPHA)
        line_surf.fill((*NEON_BLUE, alpha))
        surface.blit(line_surf, (0, center_y - 2 + i))
        surface.blit(line_surf, (0, center_y - 2 - i))


def draw_hit_line_glow(surface, y, width, start_x):
    """Draw glowing hit line across lanes."""
    # Main line
    pygame.draw.line(surface, NEON_BLUE, (start_x, y), (start_x + width, y), 3)
    
    # Glow layers
    for i in range(1, 5):
        alpha = 50 - i * 10
        line_surf = pygame.Surface((width, 2), pygame.SRCALPHA)
        line_surf.fill((*NEON_BLUE, alpha))
        surface.blit(line_surf, (start_x, y - i * 2))
        surface.blit(line_surf, (start_x, y + i * 2))


class FloatingText:
    """Floating judgement text with random tilt and fade out."""
    
    def __init__(self, text, x, y, color, duration=0.5):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.timer = duration
        self.angle = random.uniform(-15, 15)  # Random tilt
        
        if not hasattr(FloatingText, 'FONT'):
             FloatingText.FONT = pygame.font.Font(None, 28)
        self.font = FloatingText.FONT
        
        self.active = True
        self.velocity_y = -50  # Float upward
        
    def update(self, dt):
        if not self.active:
            return
        self.timer -= dt
        self.y += self.velocity_y * dt
        if self.timer <= 0:
            self.active = False
    
    def draw(self, surface):
        if not self.active:
            return
            
        # Calculate alpha based on remaining time
        alpha = int(255 * (self.timer / self.duration))
        
        # Render text
        text_surf = self.font.render(self.text, True, self.color)
        
        # Rotate
        rotated = pygame.transform.rotate(text_surf, self.angle)
        
        # Apply alpha
        rotated.set_alpha(alpha)
        
        # Draw centered at position
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect)


class InputField:
    """Text input field for numerical values like BPM and Offset."""
    
    def __init__(self, x, y, width, height, label, initial_value=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = str(initial_value)
        self.focused = False
        self.cursor_visible = True
        self.cursor_timer = 0
        
        if not hasattr(InputField, 'FONT'):
            InputField.FONT = pygame.font.Font(None, 24)
            InputField.LABEL_FONT = pygame.font.Font(None, 18)
            
        self.font = InputField.FONT
        self.label_font = InputField.LABEL_FONT
    
    def handle_event(self, event):
        """Handle keyboard input when focused."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.rect.collidepoint(event.pos)
        
        if self.focused and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.focused = False
            elif event.unicode.isdigit() or event.unicode in ['.', '-']:
                self.value += event.unicode
    
    def update(self, dt):
        """Update cursor blink."""
        if self.focused:
            self.cursor_timer += dt
            if self.cursor_timer > 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
    
    def draw(self, surface):
        """Draw the input field."""
        color = NEON_BLUE if self.focused else GRAY
        pygame.draw.rect(surface, DARK_SLATE, self.rect, border_radius=4)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=4)
        
        # Label above
        label_surf = self.label_font.render(self.label, True, GRAY)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 20))
        
        # Value text
        text_surf = self.font.render(self.value, True, WHITE)
        text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surf, text_rect)
        
        # Cursor
        if self.focused and self.cursor_visible:
            cursor_x = text_rect.right + 2
            pygame.draw.line(surface, WHITE, 
                           (cursor_x, self.rect.y + 8), 
                           (cursor_x, self.rect.bottom - 8), 2)
    
    def get_value(self):
        """Get the numeric value (returns 0 if invalid)."""
        return float(self.value) if '.' in self.value else int(self.value)


class Dropdown:
    """Dropdown/Cycle button for snap divisor and playback speed."""
    
    def __init__(self, x, y, width, height, label, options):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.label = label
        self.options = options  # List of strings
        self.selected_index = 0
        
        if not hasattr(Dropdown, 'FONT'):
            Dropdown.FONT = pygame.font.Font(None, 20)
            Dropdown.LABEL_FONT = pygame.font.Font(None, 16)
            
        self.font = Dropdown.FONT
        self.label_font = Dropdown.LABEL_FONT
        self.hovered = False
    
    def handle_click(self, event):
        """Cycle to next option on click."""
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return True
        return False
    
    def update(self, mouse_pos):
        """Update hover state."""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        """Draw the dropdown."""
        color = NEON_BLUE if self.hovered else GRAY
        pygame.draw.rect(surface, DARK_SLATE, self.rect, border_radius=3)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=3)
        
        # Label above
        label_surf = self.label_font.render(self.label, True, GRAY)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 18))
        
        # Current value
        value_surf = self.font.render(self.options[self.selected_index], True, WHITE)
        value_rect = value_surf.get_rect(center=self.rect.center)
        surface.blit(value_surf, value_rect)
        
        # Arrow indicator
        arrow_x = self.rect.right - 12
        arrow_y = self.rect.centery
        pygame.draw.polygon(surface, color, [
            (arrow_x, arrow_y - 4),
            (arrow_x + 6, arrow_y - 4),
            (arrow_x + 3, arrow_y + 2)
        ])
    
    def get_value(self):
        """Get the currently selected option."""
        return self.options[self.selected_index]
    
    def set_value(self, value):
        """Set the selected option by value."""
        if value in self.options:
            self.selected_index = self.options.index(value)
