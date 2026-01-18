"""
Enhanced achievements system with notifications and progress tracking.
Works with the leaderboard system to unlock achievements based on gameplay.
"""

import time
import math
from typing import Dict, List, Any, Optional
from enum import Enum

class AchievementCategory(Enum):
    """Categories of achievements."""
    GENERAL = "general"
    GAMEPLAY = "gameplay" 
    SCORE = "score"
    TIME = "time"
    COLLECTION = "collection"
    MASTERY = "mastery"
    SPECIAL = "special"

class AchievementRequirement:
    """Represents a condition for unlocking an achievement."""
    
    def __init__(self, requirement_type: str, target: int, comparison: str = "="):
        self.requirement_type = requirement_type  # e.g., "score", "games_played", "time"
        self.target = target
        self.comparison = comparison  # "=", ">=", "<=", etc.
    
    def check(self, value: Any) -> bool:
        """Check if requirement is met."""
        if self.comparison == "=":
            return value == self.target
        elif self.comparison == ">=":
            return value >= self.target
        elif self.comparison == ">":
            return value > self.target
        elif self.comparison == "<=":
            return value <= self.target
        elif self.comparison == "<":
            return value < self.target
        return False

class Achievement:
    """Enhanced achievement with progress tracking."""
    
    def __init__(self, id: str, name: str, description: str, 
                 category: AchievementCategory, points: int = 10,
                 icon: str = "🏆", rarity: str = "common",
                 secret: bool = False, requirements: List[AchievementRequirement] = None):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.points = points
        self.icon = icon
        self.rarity = rarity
        self.secret = secret
        self.requirements = requirements or []
        
        # Progress tracking
        self.unlocked = False
        self.unlocked_at = None
        self.unlock_count = 0
        self.progress = 0.0
        self.last_progress_update = 0
        
        # Notification state
        self.notification_shown = False
        self.newly_unlocked = False
    
    def check_unlock(self, context: Dict[str, Any]) -> bool:
        """Check if achievement should be unlocked."""
        if self.unlocked:
            return False
        
        # Check all requirements
        all_met = True
        progress_values = []
        
        for req in self.requirements:
            if req.requirement_type in context:
                value = context[req.requirement_type]
                progress_values.append((value, req.target, req.comparison))
                
                if not req.check(value):
                    all_met = False
            else:
                all_met = False
        
        # Update progress
        if progress_values:
            total_progress = 0.0
            for current, target, comparison in progress_values:
                if target > 0:
                    progress = min(1.0, current / target)
                    total_progress += progress
                else:
                    total_progress += 1.0 if current > 0 else 0.0
            
            self.progress = total_progress / len(progress_values)
            self.last_progress_update = time.time()
        
        return all_met
    
    def unlock(self) -> bool:
        """Unlock the achievement."""
        if not self.unlocked:
            self.unlocked = True
            self.unlocked_at = time.time()
            self.unlock_count += 1
            self.newly_unlocked = True
            self.progress = 1.0
            return True
        return False
    
    def mark_notification_shown(self):
        """Mark that the achievement notification has been shown."""
        self.notification_shown = True
        self.newly_unlocked = False
    
    def get_progress_text(self) -> str:
        """Get progress display text."""
        if self.unlocked:
            return "Completed"
        elif self.progress > 0:
            return f"{self.progress * 100:.0f}%"
        else:
            return "Locked"
    
    def get_rarity_color(self) -> int:
        """Get color code based on rarity."""
        if self.rarity == "legendary":
            return 5  # Gold
        elif self.rarity == "epic":
            return 4  # Purple
        elif self.rarity == "rare":
            return 3  # Blue
        elif self.rarity == "uncommon":
            return 2  # Green
        else:  # common
            return 1  # White

class AchievementsSystem:
    """Enhanced achievements system with notifications and tracking."""
    
    def __init__(self, config_manager, leaderboard_system):
        self.config = config_manager
        self.leaderboard = leaderboard_system
        self.achievements: Dict[str, Achievement] = {}
        self.player_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Initialize all achievements
        self._initialize_achievements()
        
        # Load saved achievement data
        self._load_saved_data()
    
    def _initialize_achievements(self):
        """Initialize all achievement definitions."""
        achievements = [
            # General Achievements
            Achievement("first_game", "First Steps", "Play your first game", 
                       AchievementCategory.GENERAL, 10, "🎮", "common",
                       [AchievementRequirement("games_played", 1)]),
            
            Achievement("veteran", "Veteran", "Play 100 games total",
                       AchievementCategory.GENERAL, 75, "🎖️", "rare",
                       [AchievementRequirement("games_played", 100)]),
            
            Achievement("explorer", "Explorer", "Try all game modes",
                       AchievementCategory.GENERAL, 35, "🔍", "uncommon",
                       [AchievementRequirement("modes_tried", 4)]),
            
            # Score Achievements
            Achievement("century", "Century", "Score 100 points in any game",
                       AchievementCategory.SCORE, 20, "💯", "common",
                       [AchievementRequirement("high_score", 100)]),
            
            Achievement("high_scorer", "High Scorer", "Score 500 points in any game",
                       AchievementCategory.SCORE, 50, "🌟", "uncommon",
                       [AchievementRequirement("high_score", 500)]),
            
            Achievement("master_scorer", "Master Scorer", "Score 1000 points in any game",
                       AchievementCategory.SCORE, 100, "👑", "rare",
                       [AchievementRequirement("high_score", 1000)]),
            
            Achievement("legendary", "Legendary", "Score 5000 points in any game",
                       AchievementCategory.SCORE, 200, "🏆", "legendary",
                       [AchievementRequirement("high_score", 5000)]),
            
            # Gameplay Achievements
            Achievement("maze_runner", "Maze Master", "Complete 10 maze levels",
                       AchievementCategory.GAMEPLAY, 30, "🗺️", "uncommon",
                       [AchievementRequirement("maze_levels_completed", 10)]),
            
            Achievement("snake_expert", "Snake Expert", "Reach length 30 in Snake",
                       AchievementCategory.GAMEPLAY, 40, "🐍", "rare",
                       [AchievementRequirement("snake_max_length", 30)]),
            
            Achievement("tetris_king", "Tetris King", "Clear 100 lines in Tetris",
                       AchievementCategory.GAMEPLAY, 60, "🧱", "epic",
                       [AchievementRequirement("tetris_lines_cleared", 100)]),
            
            Achievement("pong_champion", "Pong Champion", "Win 10 Pong matches",
                       AchievementCategory.GAMEPLAY, 45, "🏓", "rare",
                       [AchievementRequirement("pong_wins", 10)]),
            
            Achievement("space_hero", "Space Hero", "Complete 10 waves in Space Invaders",
                       AchievementCategory.GAMEPLAY, 55, "🚀", "epic",
                       [AchievementRequirement("space_invaders_waves", 10)]),
            
            Achievement("pac_ghostbuster", "Ghost Buster", "Complete 5 Pac-Man levels",
                       AchievementCategory.GAMEPLAY, 50, "👻", "rare",
                       [AchievementRequirement("pacman_levels_completed", 5)]),
            
            # Time Achievements
            Achievement("speed_demon", "Speed Demon", "Complete any game in under 1 minute",
                       AchievementCategory.TIME, 25, "⚡", "uncommon",
                       [AchievementRequirement("fastest_completion", 60)]),
            
            Achievement("marathoner", "Marathoner", "Play for over 2 hours total",
                       AchievementCategory.TIME, 40, "⏱️", "rare",
                       [AchievementRequirement("total_playtime", 7200)]),
            
            # Collection Achievements
            Achievement("game_collector", "Game Collector", "Play all available games",
                       AchievementCategory.COLLECTION, 60, "📚", "epic",
                       [AchievementRequirement("unique_games_played", 6)]),
            
            # Mastery Achievements
            Achievement("maze_perfectionist", "Maze Perfectionist", "Complete maze without dying",
                       AchievementCategory.MASTERY, 70, "✨", "rare",
                       [AchievementRequirement("maze_perfect_runs", 1)]),
            
            Achievement("snake_perfectionist", "Snake Perfectionist", "Play Snake for 5 minutes without dying",
                       AchievementCategory.MASTERY, 75, "🐍", "epic",
                       [AchievementRequirement("snake_survival_time", 300)]),
            
            Achievement("tetris_perfectionist", "Tetris Perfectionist", "Get 5 Tetrises in one game",
                       AchievementCategory.MASTERY, 80, "🧱", "epic",
                       [AchievementRequirement("tetris_tetrises", 5)]),
            
            # Special/Secret Achievements
            Achievement("secret_code", "Secret Discovery", "Find the secret code (spoiler: type 'konami' in main menu)",
                       AchievementCategory.SPECIAL, 150, "🔐", "legendary", True,
                       [AchievementRequirement("secret_code_found", 1)]),
            
            Achievement("achievement_hunter", "Achievement Hunter", "Unlock 50% of all achievements",
                       AchievementCategory.SPECIAL, 100, "🏆", "epic",
                       [AchievementRequirement("achievement_percentage", 50, ">=")]),
            
            Achievement("completionist", "Completionist", "Unlock all achievements",
                       AchievementCategory.SPECIAL, 500, "💎", "legendary", True,
                       [AchievementRequirement("achievement_percentage", 100, ">=")]),
        ]
        
        for achievement in achievements:
            self.achievements[achievement.id] = achievement
    
    def _load_saved_data(self):
        """Load saved achievement data."""
        data = self.config.load_leaderboard()
        
        # Load achievement states
        saved_achievements = data.get('achievements', {})
        
        for ach_id, achievement in self.achievements.items():
            if ach_id in saved_achievements:
                saved_data = saved_achievements[ach_id]
                achievement.unlocked = saved_data.get('unlocked', False)
                achievement.unlocked_at = saved_data.get('unlocked_at')
                achievement.unlock_count = saved_data.get('unlock_count', 0)
                achievement.progress = saved_data.get('progress', 0.0)
                achievement.notification_shown = saved_data.get('notification_shown', True)
    
    def save_data(self):
        """Save achievement data."""
        achievements_data = {}
        
        for ach_id, achievement in self.achievements.items():
            achievements_data[ach_id] = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'category': achievement.category.value,
                'points': achievement.points,
                'icon': achievement.icon,
                'rarity': achievement.rarity,
                'secret': achievement.secret,
                'unlocked': achievement.unlocked,
                'unlocked_at': achievement.unlocked_at,
                'unlock_count': achievement.unlock_count,
                'progress': achievement.progress,
                'notification_shown': achievement.notification_shown
            }
        
        # Update config data
        config_data = self.config.load_leaderboard()
        config_data['achievements'] = achievements_data
        self.config.save_leaderboard(config_data)
    
    def update_player_context(self, player_name: str, context_key: str, context_value: Any):
        """Update player's context for achievement checking."""
        if player_name not in self.player_contexts:
            self.player_contexts[player_name] = {}
        
        current_value = self.player_contexts[player_name].get(context_key, 0)
        
        # Handle different types of updates
        if isinstance(current_value, (int, float)):
            # Accumulate numeric values
            if context_key in ['games_played', 'total_score', 'total_playtime']:
                self.player_contexts[player_name][context_key] = current_value + context_value
            elif context_key in ['high_score', 'fastest_completion', 'maze_levels_completed']:
                self.player_contexts[player_name][context_key] = max(current_value, context_value)
            else:
                self.player_contexts[player_name][context_key] = current_value + context_value
        else:
            # Set or append for other types
            if context_key == 'unique_games_played':
                games_played = set(self.player_contexts[player_name].get('unique_games_played', set()))
                games_played.add(str(context_value))
                self.player_contexts[player_name]['unique_games_played'] = games_played
            else:
                self.player_contexts[player_name][context_key] = context_value
        
        # Check for newly unlocked achievements
        newly_unlocked = self._check_achievements(player_name)
        
        # Save data if anything changed
        if newly_unlocked:
            self.save_data()
        
        return newly_unlocked
    
    def _check_achievements(self, player_name: str) -> List[Achievement]:
        """Check all achievements for unlock conditions."""
        newly_unlocked = []
        
        context = self.player_contexts.get(player_name, {})
        
        # Calculate derived values
        total_games = context.get('games_played', 0)
        unique_games = len(context.get('unique_games_played', set()))
        
        # Game-specific counters
        maze_levels = context.get('maze_levels_completed', 0)
        snake_length = context.get('snake_max_length', 0)
        tetris_lines = context.get('tetris_lines_cleared', 0)
        pong_wins = context.get('pong_wins', 0)
        space_waves = context.get('space_invaders_waves', 0)
        pacman_levels = context.get('pacman_levels_completed', 0)
        
        # Time-based values
        fastest_time = context.get('fastest_completion', float('inf'))
        total_playtime = context.get('total_playtime', 0)
        
        # Build comprehensive context
        full_context = {
            **context,
            'games_played': total_games,
            'unique_games_played': unique_games,
            'high_score': max(context.get('high_score', 0), 
                           context.get('total_score', 0)),
            'maze_levels_completed': maze_levels,
            'snake_max_length': snake_length,
            'tetris_lines_cleared': tetris_lines,
            'pong_wins': pong_wins,
            'space_invaders_waves': space_waves,
            'pacman_levels_completed': pacman_levels,
            'fastest_completion': fastest_time,
            'total_playtime': total_playtime,
            'achievement_percentage': (len([a for a in self.achievements.values() if a.unlocked]) / 
                                  len(self.achievements)) * 100
        }
        
        # Check each achievement
        for achievement in self.achievements.values():
            if not achievement.secret or achievement.unlocked:  # Don't check secret unless already unlocked
                if achievement.check_unlock(full_context):
                    if achievement.unlock():
                        newly_unlocked.append(achievement)
        
        return newly_unlocked
    
    def get_achievements_by_category(self, category: AchievementCategory, 
                                   include_secret: bool = False) -> List[Achievement]:
        """Get achievements filtered by category."""
        achievements = []
        
        for achievement in self.achievements.values():
            if achievement.category == category:
                if not achievement.secret or include_secret:
                    achievements.append(achievement)
        
        return sorted(achievements, key=lambda x: (x.points, x.id))
    
    def get_unlocked_achievements(self, player_name: Optional[str] = None) -> List[Achievement]:
        """Get all unlocked achievements."""
        return [ach for ach in self.achievements.values() if ach.unlocked]
    
    def get_locked_achievements(self, include_secret: bool = False) -> List[Achievement]:
        """Get all locked achievements."""
        achievements = []
        
        for achievement in self.achievements.values():
            if not achievement.unlocked:
                if not achievement.secret or include_secret:
                    achievements.append(achievement)
        
        return sorted(achievements, key=lambda x: (x.points, x.id))
    
    def get_newly_unlocked(self, player_name: str) -> List[Achievement]:
        """Get newly unlocked achievements that haven't been notified."""
        return [ach for ach in self.achievements.values() 
                if ach.newly_unlocked and not ach.notification_shown]
    
    def mark_notifications_shown(self, player_name: str):
        """Mark all achievements as having their notifications shown."""
        for achievement in self.achievements.values():
            if achievement.newly_unlocked:
                achievement.mark_notification_shown()
    
    def get_player_progress(self, player_name: str) -> Dict[str, Any]:
        """Get achievement progress for a player."""
        context = self.player_contexts.get(player_name, {})
        unlocked_count = len(self.get_unlocked_achievements())
        total_count = len(self.achievements)
        total_points = sum(ach.points for ach in self.achievements.values() if ach.unlocked)
        
        return {
            'achievements_unlocked': unlocked_count,
            'total_achievements': total_count,
            'completion_percentage': (unlocked_count / total_count) * 100 if total_count > 0 else 0,
            'total_points': total_points,
            'games_played': context.get('games_played', 0),
            'unique_games_played': len(context.get('unique_games_played', set())),
            'high_score': max(context.get('high_score', 0), context.get('total_score', 0)),
            'total_playtime': context.get('total_playtime', 0)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall achievement statistics."""
        total_achievements = len(self.achievements)
        unlocked_achievements = len(self.get_unlocked_achievements())
        
        category_stats = {}
        for category in AchievementCategory:
            category_achievements = self.get_achievements_by_category(category)
            unlocked_in_category = len([a for a in category_achievements if a.unlocked])
            category_stats[category.value] = {
                'total': len(category_achievements),
                'unlocked': unlocked_in_category,
                'percentage': (unlocked_in_category / len(category_achievements)) * 100 if len(category_achievements) > 0 else 0
            }
        
        return {
            'total_achievements': total_achievements,
            'unlocked_achievements': unlocked_achievements,
            'completion_percentage': (unlocked_achievements / total_achievements) * 100 if total_achievements > 0 else 0,
            'category_breakdown': category_stats,
            'total_points_possible': sum(ach.points for ach in self.achievements.values()),
            'total_points_earned': sum(ach.points for ach in self.achievements.values() if ach.unlocked)
        }
    
    def search_achievements(self, query: str) -> List[Achievement]:
        """Search achievements by name or description."""
        query = query.lower()
        results = []
        
        for achievement in self.achievements.values():
            if (query in achievement.name.lower() or 
                query in achievement.description.lower() or
                query in achievement.category.value.lower()):
                results.append(achievement)
        
        return sorted(results, key=lambda x: (x.points, x.id))
    
    def get_achievement_notification(self, player_name: str) -> Optional[str]:
        """Generate achievement unlock notification text."""
        newly_unlocked = self.get_newly_unlocked(player_name)
        
        if not newly_unlocked:
            return None
        
        achievement = newly_unlocked[0]  # Show first newly unlocked
        
        rarity_text = achievement.rarity.title()
        notification = f"""
🏆 ACHIEVEMENT UNLOCKED! 🏆

{achievement.icon} {achievement.name} ({rarity_text})
{achievement.description}

+{achievement.points} Achievement Points

Press any key to continue...
        """.strip()
        
        return notification
    
    def reset_all_achievements(self):
        """Reset all achievements (for testing)."""
        for achievement in self.achievements.values():
            achievement.unlocked = False
            achievement.unlocked_at = None
            achievement.unlock_count = 0
            achievement.progress = 0.0
            achievement.notification_shown = False
            achievement.newly_unlocked = False
        
        self.player_contexts.clear()
        self.save_data()