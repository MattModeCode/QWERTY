"""
Map Manager - Handles loading, saving, and validating beatmap JSON files.
"""
import json
import os

MAPS_DIR = os.path.join(os.path.dirname(__file__), "maps")

class MapData:
    """Represents a loaded beatmap."""
    
    def __init__(self, data: dict):
        self.metadata = data.get("metadata", {})
        self.audio = data.get("audio", {})
        self.hit_objects = data.get("hit_objects", [])
        
        # Convenience accessors
        self.title = self.metadata.get("title", "Untitled")
        self.artist = self.metadata.get("artist", "Unknown")
        self.mapper = self.metadata.get("mapper", "Unknown")
        self.difficulty = self.metadata.get("difficulty", 1)
        
        self.bpm = self.audio.get("bpm", 120)
        self.offset_ms = self.audio.get("offset_ms", 0)
        self.audio_file = self.audio.get("file", None)
        
        # Sort hit objects by time
        self.hit_objects.sort(key=lambda x: x.get("time", 0))
        
    def get_duration_ms(self):
        """Get total duration based on last hit object."""
        if not self.hit_objects:
            return 0
        last = self.hit_objects[-1]
        end_time = last.get("time", 0)
        if last.get("type") == "hold":
            end_time += last.get("duration", 0)
        return end_time + 1000  # Add 1s buffer


class MapManager:
    """Handles I/O for beatmap files."""
    
    def __init__(self):
        self.maps_dir = MAPS_DIR
        os.makedirs(self.maps_dir, exist_ok=True)
    
    def list_maps(self):
        """List all available beatmaps."""
        maps = []
        for filename in os.listdir(self.maps_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.maps_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    maps.append({
                        "filename": filename,
                        "path": filepath,
                        "title": data.get("metadata", {}).get("title", filename),
                        "difficulty": data.get("metadata", {}).get("difficulty", 0),
                        "artist": data.get("metadata", {}).get("artist", "Unknown")
                    })
        return sorted(maps, key=lambda x: x["difficulty"])
    
    def load_map(self, filename: str):
        """Load a beatmap from JSON file."""
        filepath = os.path.join(self.maps_dir, filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        return MapData(data)
    
    def save_map(self, filename: str, map_data: dict):
        """Save a beatmap to JSON file."""
        filepath = os.path.join(self.maps_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(map_data, f, indent=2)
        return True
    
    def create_empty_map(self, title: str, bpm: int = 120):
        """Create a new empty map template."""
        return {
            "metadata": {
                "title": title,
                "artist": "",
                "mapper": "",
                "difficulty": 1
            },
            "audio": {
                "file": None,
                "bpm": bpm,
                "offset_ms": 0
            },
            "hit_objects": []
        }
