import json
import os

SCORE_FILE = "scores.json"

class DataManager:
    """Manages persistent game data (scores, settings)."""
    
    def __init__(self):
        self.scores = {}
        self.load_scores()

    def load_scores(self):
        if os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, 'r') as f:
                self.scores = json.load(f)
        else:
            self.scores = {}

    def save_scores(self):
        """Save scores to JSON file."""
        with open(SCORE_FILE, 'w') as f:
            json.dump(self.scores, f, indent=4)

    def get_score(self, song_id):
        """Get best score data for a song."""
        return self.scores.get(str(song_id), {
            "score": 0,
            "combo": 0,
            "rank": "-",
            "accuracy": 0,
            "perfect": 0,
            "great": 0,
            "miss": 0
        })

    def submit_score(self, song_id, score, combo, rank, accuracy, stats):
        """Submit a new score. Updates if score is higher."""
        str_id = str(song_id)
        current = self.get_score(str_id)
        
        if score > current["score"]:
            self.scores[str_id] = {
                "score": score,
                "combo": max(combo, current["combo"]),
                "rank": rank,
                "accuracy": accuracy,
                "perfect": stats.get('perfect', 0),
                "great": stats.get('great', 0),
                "miss": stats.get('miss', 0)
            }
            self.save_scores()
            return True
        return False
