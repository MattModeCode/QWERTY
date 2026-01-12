import pygame
import math
from PIL import Image, ImageFilter

def draw_star(surface, x, y, size, color):
    """Draws a 5-pointed star centered at (x,y)."""
    points = []
    outer_radius = size
    inner_radius = size * 0.4
    angle = -math.pi / 2 # Start top
    
    for i in range(5):
        # Outer point
        points.append((x + math.cos(angle) * outer_radius, y + math.sin(angle) * outer_radius))
        angle += math.pi / 5
        # Inner point
        points.append((x + math.cos(angle) * inner_radius, y + math.sin(angle) * inner_radius))
        angle += math.pi / 5
        
    pygame.draw.polygon(surface, color, points)

def create_neon_text(text, font, color, glow_color, blur_radius=10):
    """Creates a text surface with a high-quality PIL-based neon glow."""
    # Render base text
    text_surf = font.render(text, True, color)
    w, h = text_surf.get_size()
    
    # Add padding for glow
    padding = blur_radius * 3
    new_w = w + padding * 2
    new_h = h + padding * 2
    
    # Surface for glow
    glow_surf = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
    
    # Draw text onto center of glow surf, using glow color
    
    temp_surf = font.render(text, True, glow_color)
    glow_surf.blit(temp_surf, (padding, padding))
    
    # Convert to PIL Image
    # Pygame -> String -> PIL
    rgba_data = pygame.image.tostring(glow_surf, 'RGBA')
    pil_img = Image.frombytes('RGBA', (new_w, new_h), rgba_data)
    
    # Blur
    blurred_img = pil_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # Convert back to Pygame
    raw_str = blurred_img.tobytes()
    final_glow = pygame.image.fromstring(raw_str, (new_w, new_h), 'RGBA')
    
    # Composite Core Text on top
    final_glow.blit(text_surf, (padding, padding))
    
    return final_glow
