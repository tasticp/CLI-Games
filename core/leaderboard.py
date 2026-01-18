"""
Leaderboard and scoring system for CLI Games Launcher.
Handles local and global high scores, achievements, and statistics.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

class ScoreType(Enum):
    """Types of scores."""
    HIGH_SCORE = "high_score"
    SPEEDRUN = "speedrun"
    TIME_ATTACK = "time_attack"
    INFINITE = "infinite"
    TOTAL_SCORES = "total_scores"

class Achievement:
    """Represents an achievement."""
    
    def __init__(self, id: str, name: str, description: str, 
                 points: int = 10, icon: str = "🏆"):
        self.id = id
        self.name = name
        self.description = description
        self.points = points
        self.icon = icon
        self.unlocked = False
        self.unlocked_at = None
        self.unlock_count = 0

class LeaderboardEntry:
    """Represents a single leaderboard entry."""
    
    def __init__(self, player_name: str, score: int, game_name: str,
                 game_mode: str, timestamp: Optional[float] = None,
                 additional_data: Optional[Dict] = None):
        self.player_name = player_name
        self.score = score
        self.game_name = game_name
        self.game_mode = game_mode
        self.timestamp = timestamp or time.time()
        self.additional_data = additional_data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            'player_name': self.player_name,
            'score': self.score,
            'game_name': self.game_name,
            'game_mode': self.game_mode,
            'timestamp': self.timestamp,
            'additional_data': self.additional_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LeaderboardEntry':
        """Create from dictionary."""
        return cls(
            data['player_name'],
            data['score'],
            data['game_name'],
            data['game_mode'],
            data.get('timestamp'),
            data.get('additional_data', {})
        )

class LeaderboardSystem:
    """Manages leaderboards and achievements."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.data_file = config.config_dir / 'leaderboard.json'
        self.achievements_file = config.config_dir / 'achievements.json'
        
        # Load data
        self.leaderboards = self._load_leaderboards()
        self.player_stats = self._load_player_stats()
        self.achievements = self._load_achievements()
        
        # Initialize default achievements
        self._initialize_default_achievements()
    
    def _load_leaderboards(self) -> Dict[str, List[LeaderboardEntry]]:
        """Load leaderboard data."""
        data = self.config.load_leaderboard()
        leaderboards = {}
        
        for key, entries in data.get('leaderboards', {}).items():
            leaderboards[key] = [
                LeaderboardEntry.from_dict(entry) for entry in entries
            ]
        
        return leaderboards
    
    def _load_player_stats(self) -> Dict[str, Any]:
        """Load player statistics."""
        data = self.config.load_leaderboard()
        return data.get('player_stats', {})
    
    def _load_achievements(self) -> Dict[str, Achievement]:
        """Load achievements."""
        data = self.config.load_leaderboard()
        achievements = {}
        
        for ach_id, ach_data in data.get('achievements', {}).items():
            achievement = Achievement(
                ach_data['id'],
                ach_data['name'],
                ach_data['description'],
                ach_data.get('points', 10),
                ach_data.get('icon', '🏆')
            )
            achievement.unlocked = ach_data.get('unlocked', False)
            achievement.unlocked_at = ach_data.get('unlocked_at')
            achievement.unlock_count = ach_data.get('unlock_count', 0)
            achievements[ach_id] = achievement
        
        return achievements
    
    def _initialize_default_achievements(self):
        """Initialize default achievements."""
        default_achievements = [
            Achievement("first_game", "First Steps", "Play your first game", 10, "🎮"),
            Achievement("score_100", "Century", "Score 100 points in any game", 20, "💯"),
            Achievement("score_500", "High Scorer", "Score 500 points in any game", 50, "🌟"),
            Achievement("score_1000", "Master", "Score 1000 points in any game", 100, "👑"),
            Achievement("maze_master", "Maze Master", "Complete 5 maze levels", 30, "🗺️"),
            Achievement("snake_expert", "Snake Expert", "Reach length 20 in Snake", 40, "🐍"),
            Achievement("speedrunner", "Speed Demon", "Complete a game in under 2 minutes", 25, "⚡"),
            Achievement("perfectionist", "Perfectionist", "Play a game without dying", 50, "✨"),
            Achievement("veteran", "Veteran", "Play 50 games total", 75, "🎖️"),
            Achievement("collector", "Game Collector", "Play 10 different games", 60, "📚"),
            Achievement("explorer", "Explorer", "Try all game modes", 35, "🔍"),
        ]
        
        # Add any missing achievements
        for achievement in default_achievements:
            if achievement.id not in self.achievements:
                self.achievements[achievement.id] = achievement
    
    def save_data(self):
        """Save all leaderboard data."""
        # Convert leaderboards to dict
        leaderboard_data = {}
        for key, entries in self.leaderboards.items():
            leaderboard_data[key] = [entry.to_dict() for entry in entries]
        
        # Convert achievements to dict
        achievement_data = {}
        for ach_id, achievement in self.achievements.items():
            achievement_data[ach_id] = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'points': achievement.points,
                'icon': achievement.icon,
                'unlocked': achievement.unlocked,
                'unlocked_at': achievement.unlocked_at,
                'unlock_count': achievement.unlock_count
            }
        
        # Combine all data
        all_data = {
            'leaderboards': leaderboard_data,
            'player_stats': self.player_stats,
            'achievements': achievement_data
        }
        
        self.config.save_leaderboard(all_data)
    
    def add_score(self, player_name: str, score: int, game_name: str,
                 game_mode: str, additional_data: Optional[Dict] = None):
        """Add a score to the leaderboard."""
        entry = LeaderboardEntry(
            player_name, score, game_name, game_mode,
            additional_data=additional_data
        )
        
        # Get leaderboard key
        key = f"{game_name}_{game_mode}"
        
        # Add to appropriate leaderboard
        if key not in self.leaderboards:
            self.leaderboards[key] = []
        
        self.leaderboards[key].append(entry)
        
        # Sort by score (descending) and keep top 100
        self.leaderboards[key].sort(key=lambda x: x.score, reverse=True)
        self.leaderboards[key] = self.leaderboards[key][:100]
        
        # Update player stats
        self._update_player_stats(player_name, score, game_name, game_mode)
        
        # Check achievements
        self._check_score_achievements(player_name, score, game_name, game_mode)
        
        # Save data
        self.save_data()
    
    def _update_player_stats(self, player_name: str, score: int, game_name: str, game_mode: str):
        """Update player statistics."""
        if player_name not in self.player_stats:
            self.player_stats[player_name] = {
                'total_games': 0,
                'total_score': 0,
                'high_scores': {},
                'games_played': {},
                'first_played': time.time(),
                'last_played': time.time()
            }
        
        stats = self.player_stats[player_name]
        
        # Update general stats
        stats['total_games'] += 1
        stats['total_score'] += score
        stats['last_played'] = time.time()
        
        # Update high scores
        game_key = f"{game_name}_{game_mode}"
        if game_key not in stats['high_scores'] or score > stats['high_scores'][game_key]:
            stats['high_scores'][game_key] = score
        
        # Update games played
        if game_name not in stats['games_played']:
            stats['games_played'][game_name] = 0
        stats['games_played'][game_name] += 1
    
    def _check_score_achievements(self, player_name: str, score: int, game_name: str, game_mode: str):
        """Check and unlock score-based achievements."""
        # First game achievement
        if self.player_stats[player_name]['total_games'] == 1:
            self.unlock_achievement("first_game")
        
        # Score achievements
        if score >= 100:
            self.unlock_achievement("score_100")
        if score >= 500:
            self.unlock_achievement("score_500")
        if score >= 1000:
            self.unlock_achievement("score_1000")
        
        # Game-specific achievements
        if game_name == "Maze Runner":
            # Check for maze completion
            if game_mode == "normal" and score >= 200:
                self.unlock_achievement("maze_master")
        
        if game_name == "Snake Classic":
            # Check for snake length (assuming score includes length bonus)
            if additional_data and additional_data.get('snake_length', 0) >= 20:
                self.unlock_achievement("snake_expert")
        
        # Speedrun achievement
        if game_mode == "speedrun":
            # Would need timestamp data from game
            pass
        
        # Veteran achievement
        if self.player_stats[player_name]['total_games'] >= 50:
            self.unlock_achievement("veteran")
        
        # Collector achievement
        if len(self.player_stats[player_name]['games_played']) >= 10:
            self.unlock_achievement("collector")
    
    def unlock_achievement(self, achievement_id: str):
        """Unlock an achievement."""
        if achievement_id in self.achievements:
            achievement = self.achievements[achievement_id]
            
            if not achievement.unlocked:
                achievement.unlocked = True
                achievement.unlocked_at = time.time()
                achievement.unlock_count += 1
                return True
            else:
                achievement.unlock_count += 1
                return False
        
        return False
    
    def get_leaderboard(self, game_name: str, game_mode: str, 
                      limit: int = 10) -> List[LeaderboardEntry]:
        """Get leaderboard for a specific game and mode."""
        key = f"{game_name}_{game_mode}"
        entries = self.leaderboards.get(key, [])
        return entries[:limit]
    
    def get_global_leaderboard(self, limit: int = 10) -> List[LeaderboardEntry]:
        """Get global top scores across all games."""
        all_entries = []
        for entries in self.leaderboards.values():
            all_entries.extend(entries)
        
        # Sort by score and return top
        all_entries.sort(key=lambda x: x.score, reverse=True)
        return all_entries[:limit]
    
    def get_player_stats(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific player."""
        return self.player_stats.get(player_name)
    
    def get_achievements(self, player_name: Optional[str] = None) -> List[Achievement]:
        """Get all achievements (optionally filtered by unlock status)."""
        if player_name:
            # Could implement player-specific achievements in future
            pass
        
        return list(self.achievements.values())
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get unlocked achievements."""
        return [ach for ach in self.achievements.values() if ach.unlocked]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """Get locked achievements."""
        return [ach for ach in self.achievements.values() if not ach.unlocked]
    
    def get_player_rank(self, player_name: str, game_name: str, game_mode: str) -> Optional[int]:
        """Get player's rank on a specific leaderboard."""
        leaderboard = self.get_leaderboard(game_name, game_mode, limit=1000)
        
        for i, entry in enumerate(leaderboard, 1):
            if entry.player_name == player_name:
                return i
        
        return None
    
    def get_top_players(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top players by total score."""
        player_totals = {}
        
        for player_name, stats in self.player_stats.items():
            player_totals[player_name] = stats.get('total_score', 0)
        
        # Sort by total score
        sorted_players = sorted(player_totals.items(), key=lambda x: x[1], reverse=True)
        return sorted_players[:limit]
    
    def search_scores(self, query: str, limit: int = 10) -> List[LeaderboardEntry]:
        """Search scores by player name or game name."""
        all_entries = []
        
        for entries in self.leaderboards.values():
            all_entries.extend(entries)
        
        # Filter by query
        filtered = [
            entry for entry in all_entries
            if query.lower() in entry.player_name.lower() or 
               query.lower() in entry.game_name.lower()
        ]
        
        # Sort by score and return top
        filtered.sort(key=lambda x: x.score, reverse=True)
        return filtered[:limit]
    
    def get_recent_scores(self, hours: int = 24, limit: int = 10) -> List[LeaderboardEntry]:
        """Get recent scores within the specified time frame."""
        cutoff_time = time.time() - (hours * 3600)
        
        all_entries = []
        for entries in self.leaderboards.values():
            all_entries.extend([
                entry for entry in entries
                if entry.timestamp >= cutoff_time
            ])
        
        # Sort by timestamp (newest first) and return top
        all_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return all_entries[:limit]
    
    def reset_player_data(self, player_name: str):
        """Reset data for a specific player."""
        if player_name in self.player_stats:
            del self.player_stats[player_name]
        
        # Remove player's entries from leaderboards
        for key, entries in self.leaderboards.items():
            self.leaderboards[key] = [
                entry for entry in entries
                if entry.player_name != player_name
            ]
        
        self.save_data()
    
    def reset_all_data(self):
        """Reset all leaderboard and achievement data."""
        self.leaderboards.clear()
        self.player_stats.clear()
        
        # Reset achievements
        for achievement in self.achievements.values():
            achievement.unlocked = False
            achievement.unlocked_at = None
            achievement.unlock_count = 0
        
        self.save_data()
    
    def export_data(self, filepath: str):
        """Export leaderboard data to file."""
        export_data = {
            'leaderboards': {
                key: [entry.to_dict() for entry in entries]
                for key, entries in self.leaderboards.items()
            },
            'player_stats': self.player_stats,
            'achievements': {
                ach_id: {
                    'id': ach.id,
                    'name': ach.name,
                    'description': ach.description,
                    'points': ach.points,
                    'icon': ach.icon,
                    'unlocked': ach.unlocked,
                    'unlocked_at': ach.unlocked_at,
                    'unlock_count': ach.unlock_count
                }
                for ach_id, ach in self.achievements.items()
            },
            'export_timestamp': time.time(),
            'export_version': '1.0'
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics."""
        total_entries = sum(len(entries) for entries in self.leaderboards.values())
        unlocked_count = len(self.get_unlocked_achievements())
        total_achievements = len(self.achievements)
        
        return {
            'total_scores': total_entries,
            'total_players': len(self.player_stats),
            'total_games': len(set(
                entry.game_name 
                for entries in self.leaderboards.values()
                for entry in entries
            )),
            'achievements_unlocked': unlocked_count,
            'total_achievements': total_achievements,
            'achievement_percentage': (unlocked_count / total_achievements * 100) if total_achievements > 0 else 0
        }