"""
AudioManager - Handles music playback for editor, selection, and gameplay.
"""
import pygame
import os
# Define Assets Path here to avoid circular imports or redefining constantly
ASSETS_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")

class AudioManager:
    """Manages audio playback with seeking and time tracking."""
    
    def __init__(self):
        # Ensure mixer is initialized with custom settings
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self.current_file = None
        self.is_playing = False
        self.start_time = 0  # When playback started (in ms)
        self.play_offset = 0  # Where in the song we started (in ms)
        self.paused_time = 0  # Time when paused
        
    def load(self, audio_filename):
        """Load an audio file from the assets/audio directory."""
        if not audio_filename:
            return False
        
        audio_path = os.path.join(ASSETS_AUDIO_DIR, audio_filename)
        if not os.path.exists(audio_path):
            return False
        
        
        pygame.mixer.music.load(audio_path)
        self.current_file = audio_filename
        return True
    
    def play(self, start_ms=0):
        """Start/resume playback from a specific time (in milliseconds)."""
        if not self.current_file:
            return
        
        pygame.mixer.music.play(start=start_ms / 1000.0)
        self.is_playing = True
        self.start_time = pygame.time.get_ticks()
        self.play_offset = start_ms
    
    def pause(self):
        """Pause playback."""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.paused_time = self.get_position()
            self.is_playing = False
    
    def unpause(self):
        """Resume from pause."""
        if not self.is_playing:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.start_time = pygame.time.get_ticks()
            self.play_offset = self.paused_time
    
    def stop(self):
        """Stop playback completely."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.start_time = 0
        self.play_offset = 0
    
    def get_position(self):
        """Get current playback position in milliseconds."""
        if not self.is_playing:
            return self.paused_time
        
        elapsed = pygame.time.get_ticks() - self.start_time
        return self.play_offset + elapsed
    
    def seek(self, time_ms):
        """Seek to a specific time in the song."""
        was_playing = self.is_playing
        self.stop()
        if was_playing:
            self.play(time_ms)
        else:
            self.paused_time = time_ms


# Global instance
audio_manager = AudioManager()
