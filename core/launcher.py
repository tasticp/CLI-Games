"""
Main game launcher that coordinates the menu system, plugins, and game execution.
"""

import curses
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from core.config import Config
from core.plugin_manager import PluginManager
from core.leaderboard import LeaderboardSystem
from ui.menu import Menu, MenuItem, MenuAction
from plugins.base_game import BaseGame, GameMode

class GameLauncher:
    """Main launcher for CLI games."""
    
    def __init__(self, config: Config):
        self.config = config
        self.plugin_manager = PluginManager(config)
        self.leaderboard_system = LeaderboardSystem(config)
        self.running = True
        self.current_player = "Player"  # Default player name
        
        # Load all plugins
        self.plugin_manager.load_all_plugins()
        self.plugin_manager._load_plugin_settings()
    
    def start(self):
        """Start the launcher main menu."""
        try:
            curses.wrapper(self._main_menu)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error in launcher: {e}")
            traceback.print_exc()
    
    def _main_menu(self, stdscr):
        """Display and handle the main menu."""
        # Create main menu
        main_menu = Menu("CLI GAMES LAUNCHER", "Choose Your Game")
        
        # Add game categories
        main_menu.add_submenu("🎮 Browse Games", self._create_games_menu())
        main_menu.add_submenu("🎯 Game Modes", self._create_modes_menu())
        main_menu.add_submenu("🏆 Leaderboards", self._create_leaderboards_menu())
        main_menu.add_submenu("⚙️ Settings", self._create_settings_menu())
        main_menu.add_submenu("🔌 Plugin Manager", self._create_plugin_menu())
        main_menu.add_submenu("❓ Help", self._create_help_menu())
        main_menu.add_exit()
        
        # Show menu and handle selection
        while self.running:
            result = main_menu.show(stdscr, self._get_theme())
            
            if result:
                if result.action == MenuAction.EXIT:
                    break
                elif result.action == MenuAction.BACK:
                    continue
                elif result.action == MenuAction.SELECT:
                    self._handle_menu_selection(stdscr, result)
    
    def _create_games_menu(self) -> Menu:
        """Create the games browser menu."""
        games_menu = Menu("BROWSE GAMES", "Select a game to play")
        
        # Get all enabled plugins
        plugins = self.plugin_manager.get_enabled_plugins()
        
        if not plugins:
            games_menu.add_text("No games available", "Install some plugins to get started!")
        else:
            # Group games by genre
            genres = {}
            for plugin_id, info in plugins.items():
                genre = info.metadata.get('genre', 'Unknown')
                if genre not in genres:
                    genres[genre] = []
                genres[genre].append((plugin_id, info))
            
            # Add genre submenus
            for genre, game_list in sorted(genres.items()):
                genre_menu = Menu(f"{genre.upper()} GAMES")
                
                for plugin_id, info in sorted(game_list, key=lambda x: x[1].metadata.get('name', '')):
                    name = info.metadata.get('name', plugin_id)
                    description = info.metadata.get('description', '')
                    
                    # Create game selection item
                    game_item = MenuItem(
                        name,
                        MenuAction.CUSTOM,
                        ('play_game', plugin_id),
                        description
                    )
                    genre_menu.add_item(game_item)
                
                genre_menu.add_back()
                games_menu.add_submenu(genre, genre_menu)
        
        games_menu.add_back()
        return games_menu
    
    def _create_modes_menu(self) -> Menu:
        """Create the game modes menu."""
        modes_menu = Menu("GAME MODES", "Select a game mode")
        
        modes_menu.add_text("Time Attack", "Race against the clock!")
        modes_menu.add_text("Speedrun", "Complete games as fast as possible")
        modes_menu.add_text("Infinite", "Endless gameplay with increasing difficulty")
        modes_menu.add_text("Practice", "Learn the ropes without pressure")
        modes_menu.add_text("Multiplayer", "Compete with friends (coming soon)")
        modes_menu.add_back()
        
        return modes_menu
    
    def _create_leaderboards_menu(self) -> Menu:
        """Create the leaderboards menu."""
        leaderboard_menu = Menu("LEADERBOARDS", "View high scores and achievements")
        
        leaderboard_menu.add_submenu("Game Leaderboards", self._create_game_leaderboards_menu())
        leaderboard_menu.add_submenu("Global Top 10", self._create_global_leaderboard_menu())
        leaderboard_menu.add_submenu("Player Statistics", self._create_player_stats_menu())
        leaderboard_menu.add_submenu("Achievements", self._create_achievements_menu())
        leaderboard_menu.add_submenu("Recent Scores", self._create_recent_scores_menu())
        leaderboard_menu.add_back()
        
        return leaderboard_menu
    
    def _create_settings_menu(self) -> Menu:
        """Create the settings menu."""
        settings_menu = Menu("SETTINGS", "Configure your experience")
        
        settings_menu.add_submenu("Display", self._create_display_settings_menu())
        settings_menu.add_submenu("Gameplay", self._create_gameplay_settings_menu())
        settings_menu.add_submenu("Controls", self._create_controls_settings_menu())
        settings_menu.add_text("Reset to Defaults", "Restore default settings")
        settings_menu.add_back()
        
        return settings_menu
    
    def _create_display_settings_menu(self) -> Menu:
        """Create display settings submenu."""
        display_menu = Menu("DISPLAY SETTINGS")
        
        display_menu.add_text("Theme", "Choose color theme")
        display_menu.add_text("FPS", "Set frame rate limit")
        display_menu.add_text("Sound", "Enable/disable sound effects")
        display_menu.add_text("Screen Shake", "Toggle visual effects")
        display_menu.add_back()
        
        return display_menu
    
    def _create_gameplay_settings_menu(self) -> Menu:
        """Create gameplay settings submenu."""
        gameplay_menu = Menu("GAMEPLAY SETTINGS")
        
        gameplay_menu.add_text("Difficulty", "Set game difficulty")
        gameplay_menu.add_text("Auto-Save", "Toggle automatic saving")
        gameplay_menu.add_text("Show Controls", "Display controls during gameplay")
        gameplay_menu.add_back()
        
        return gameplay_menu
    
    def _create_controls_settings_menu(self) -> Menu:
        """Create controls settings submenu."""
        controls_menu = Menu("CONTROLS SETTINGS")
        
        controls_menu.add_text("Keyboard Layout", "Configure key bindings")
        controls_menu.add_text("Controller", "Setup gamepad support")
        controls_menu.add_text("Reset Controls", "Restore default controls")
        controls_menu.add_back()
        
        return controls_menu
    
    def _create_plugin_menu(self) -> Menu:
        """Create the plugin manager menu."""
        plugin_menu = Menu("PLUGIN MANAGER", "Manage your game plugins")
        
        # Get plugin stats
        stats = self.plugin_manager.get_plugin_stats()
        plugin_menu.add_text(f"Total: {stats['total_plugins']} | Enabled: {stats['enabled_plugins']}")
        
        plugin_menu.add_submenu("Installed", self._create_installed_plugins_menu())
        plugin_menu.add_submenu("Browse", self._create_browse_plugins_menu())
        plugin_menu.add_text("Install from URL", "Install a plugin from the internet")
        plugin_menu.add_text("Check for Updates", "Update your plugins")
        plugin_menu.add_back()
        
        return plugin_menu
    
    def _create_installed_plugins_menu(self) -> Menu:
        """Create installed plugins submenu."""
        installed_menu = Menu("INSTALLED PLUGINS")
        
        plugins = self.plugin_manager.get_all_plugins()
        
        if not plugins:
            installed_menu.add_text("No plugins installed")
        else:
            for plugin_id, info in plugins.items():
                name = info.metadata.get('name', plugin_id)
                status = "✓" if info.enabled else "✗"
                version = info.metadata.get('version', '?.?.?')
                
                installed_menu.add_text(f"{status} {name} v{version}")
        
        installed_menu.add_back()
        return installed_menu
    
    def _create_game_leaderboards_menu(self) -> Menu:
        """Create game-specific leaderboards menu."""
        game_leaderboards_menu = Menu("GAME LEADERBOARDS", "Choose a game")
        
        plugins = self.plugin_manager.get_enabled_plugins()
        for plugin_id, info in plugins.items():
            game_name = info.metadata.get('name', 'Unknown')
            description = info.metadata.get('description', '')
            
            # Create submenu for this game's modes
            game_modes_menu = Menu(f"{game_name.upper()} SCORES")
            
            for mode in info.metadata.get('supported_modes', []):
                mode_name = mode.value if hasattr(mode, 'value') else str(mode)
                mode_display = mode_name.replace('_', ' ').title()
                game_modes_menu.add_submenu(
                    mode_display, 
                    self._create_mode_leaderboard_menu(plugin_id, mode_name, game_name)
                )
            
            game_modes_menu.add_back()
            game_leaderboards_menu.add_submenu(
                f"{game_name} - {description[:30]}...", 
                game_modes_menu
            )
        
        game_leaderboards_menu.add_back()
        return game_leaderboards_menu
    
    def _create_mode_leaderboard_menu(self, plugin_id: str, mode: str, game_name: str) -> Menu:
        """Create leaderboard for specific game mode."""
        menu = Menu(f"{game_name.upper()} - {mode.upper()}")
        
        # Get top scores
        scores = self.leaderboard_system.get_leaderboard(game_name, mode, limit=10)
        
        if not scores:
            menu.add_text("No scores yet", "Be the first to play!")
        else:
            for i, entry in enumerate(scores, 1):
                # Format the score entry
                score_text = f"{i}. {entry.player_name}: {entry.score}"
                
                # Add timestamp if recent
                time_diff = time.time() - entry.timestamp
                if time_diff < 86400:  # Less than 24 hours
                    score_text += " (new)"
                
                menu.add_text(score_text, f"Played {datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d')}")
        
        menu.add_back()
        return menu
    
    def _create_global_leaderboard_menu(self) -> Menu:
        """Create global leaderboard menu."""
        global_menu = Menu("GLOBAL TOP 10")
        
        scores = self.leaderboard_system.get_global_leaderboard(limit=10)
        
        if not scores:
            global_menu.add_text("No scores yet", "Play some games to see rankings!")
        else:
            for i, entry in enumerate(scores, 1):
                score_text = f"{i}. {entry.player_name}: {entry.score}"
                game_info = f"{entry.game_name} ({entry.game_mode})"
                global_menu.add_text(score_text, game_info)
        
        global_menu.add_back()
        return global_menu
    
    def _create_player_stats_menu(self) -> Menu:
        """Create player statistics menu."""
        stats_menu = Menu("PLAYER STATISTICS")
        
        stats = self.leaderboard_system.get_player_stats(self.current_player)
        if not stats:
            stats_menu.add_text("No stats yet", "Play some games to see your statistics!")
        else:
            stats_menu.add_text(f"Total Games: {stats['total_games']}")
            stats_menu.add_text(f"Total Score: {stats['total_score']}")
            
            # Games played
            if stats['games_played']:
                stats_menu.add_text("Games Played:")
                for game_name, count in stats['games_played'].items():
                    stats_menu.add_text(f"  {game_name}: {count}")
        
        # Top players
        stats_menu.add_submenu("Top Players", self._create_top_players_menu())
        stats_menu.add_back()
        return stats_menu
    
    def _create_top_players_menu(self) -> Menu:
        """Create top players menu."""
        top_menu = Menu("TOP PLAYERS")
        
        top_players = self.leaderboard_system.get_top_players(limit=10)
        
        if not top_players:
            top_menu.add_text("No players yet")
        else:
            for i, (player_name, total_score) in enumerate(top_players, 1):
                top_menu.add_text(f"{i}. {player_name}: {total_score}", f"Total score")
        
        top_menu.add_back()
        return top_menu
    
    def _create_achievements_menu(self) -> Menu:
        """Create achievements menu."""
        achievements_menu = Menu("ACHIEVEMENTS", "Your accomplishments")
        
        # Get statistics
        stats = self.leaderboard_system.get_statistics()
        achievements_menu.add_text(f"Unlocked: {stats['achievements_unlocked']}/{stats['total_achievements']}")
        achievements_menu.add_text(f"Progress: {stats['achievement_percentage']:.1f}%")
        
        # Unlocked achievements
        unlocked = self.leaderboard_system.get_unlocked_achievements()
        if unlocked:
            achievements_menu.add_submenu("Unlocked", self._create_unlocked_achievements_menu(unlocked))
        
        # Locked achievements
        locked = self.leaderboard_system.get_locked_achievements()
        if locked:
            achievements_menu.add_submenu("Locked", self._create_locked_achievements_menu(locked))
        
        achievements_menu.add_back()
        return achievements_menu
    
    def _create_unlocked_achievements_menu(self, achievements: list) -> Menu:
        """Create unlocked achievements menu."""
        menu = Menu("UNLOCKED ACHIEVEMENTS")
        
        for achievement in achievements:
            name = f"{achievement.icon} {achievement.name}"
            description = f"{achievement.description} (+{achievement.points} pts)"
            menu.add_text(name, description)
        
        menu.add_back()
        return menu
    
    def _create_locked_achievements_menu(self, achievements: list) -> Menu:
        """Create locked achievements menu."""
        menu = Menu("LOCKED ACHIEVEMENTS")
        
        for achievement in achievements:
            name = f"??? {achievement.name}"
            description = f"???"  # Hide description for locked achievements
            menu.add_text(name, description)
        
        menu.add_back()
        return menu
    
    def _create_recent_scores_menu(self) -> Menu:
        """Create recent scores menu."""
        recent_menu = Menu("RECENT SCORES", "Latest scores from past 24 hours")
        
        scores = self.leaderboard_system.get_recent_scores(hours=24, limit=10)
        
        if not scores:
            recent_menu.add_text("No recent scores", "Play some games to see recent activity!")
        else:
            for entry in scores:
                time_str = datetime.fromtimestamp(entry.timestamp).strftime('%H:%M')
                score_text = f"[{time_str}] {entry.player_name}: {entry.score}"
                game_info = f"{entry.game_name} ({entry.game_mode})"
                recent_menu.add_text(score_text, game_info)
        
        recent_menu.add_back()
        return recent_menu
    
    def _create_browse_plugins_menu(self) -> Menu:
        """Create browse plugins submenu."""
        browse_menu = Menu("BROWSE PLUGINS")
        
        browse_menu.add_text("Official Repository", "Browse official plugins")
        browse_menu.add_text("Community Plugins", "Explore community creations")
        browse_menu.add_text("Recent Uploads", "Latest additions")
        browse_menu.add_text("Top Rated", "Most popular plugins")
        browse_menu.add_back()
        
        return browse_menu
    
    def _create_help_menu(self) -> Menu:
        """Create the help menu."""
        help_menu = Menu("HELP & INFO")
        
        help_menu.add_text("Controls", "Learn the controls")
        help_menu.add_text("How to Play", "Get started guide")
        help_menu.add_text("Plugin Development", "Create your own games")
        help_menu.add_text("About", "Information about CLI Games")
        help_menu.add_back()
        
        return help_menu
    
    def _handle_menu_selection(self, stdscr, selection: MenuItem):
        """Handle a menu selection."""
        if selection.data and isinstance(selection.data, tuple):
            action, param = selection.data
            
            if action == 'play_game':
                self._launch_game(stdscr, param)
    
    def _launch_game(self, stdscr, plugin_id: str):
        """Launch a game."""
        plugin_info = self.plugin_manager.get_plugin(plugin_id)
        if not plugin_info:
            return
        
        try:
            # Create game instance
            game = plugin_info.create_instance()
            
            # Show game mode selection
            mode = self._select_game_mode(stdscr, game)
            if mode is None:
                return
            
            # Run the game
            stdscr.clear()
            stdscr.refresh()
            
            score = game.run(stdscr, mode)
            
            # Save score to leaderboard
            game_name = plugin_info.metadata.get('name', 'Unknown Game')
            mode_name = mode.value if hasattr(mode, 'value') else str(mode)
            
            self.leaderboard_system.add_score(
                self.current_player, score, game_name, mode_name,
                additional_data={'plugin_id': plugin_id}
            )
            
            # Update high score in metadata
            if score > plugin_info.metadata.get('high_score', 0):
                plugin_info.metadata['high_score'] = score
            
            # Show game over screen
            game.game_over(stdscr)
            
        except Exception as e:
            self._show_error(stdscr, f"Error launching game: {e}")
            traceback.print_exc()
    
    def _select_game_mode(self, stdscr, game: BaseGame) -> Optional[GameMode]:
        """Let user select a game mode."""
        if len(game.supported_modes) == 1:
            return game.supported_modes[0]
        
        mode_menu = Menu(f"SELECT MODE - {game.name}", "Choose your game mode")
        
        for mode in game.supported_modes:
            mode_text = mode.value.replace('_', ' ').title()
            mode_menu.add_text(mode_text, f"Play {mode_text} mode")
        
        mode_menu.add_text("Back", "Return to game selection")
        
        result = mode_menu.show(stdscr, self._get_theme())
        
        if result and result.text != "Back":
            for mode in game.supported_modes:
                if mode.value.replace('_', ' ').title() == result.text:
                    return mode
        
        return None
    
    def _show_error(self, stdscr, message: str):
        """Display an error message."""
        height, width = stdscr.getmaxyx()
        
        stdscr.clear()
        stdscr.border()
        
        # Error message
        msg_lines = message.split('\n')
        start_y = (height - len(msg_lines) - 4) // 2
        
        for i, line in enumerate(msg_lines):
            if start_y + i < height - 2:
                stdscr.addstr(start_y + i, 2, line[:width-4])
        
        # Instructions
        stdscr.addstr(height - 3, 2, "Press any key to continue...")
        stdscr.refresh()
        
        stdscr.getch()
    
    def _get_theme(self) -> Dict[str, Any]:
        """Get the current color theme."""
        return {
            'text': curses.COLOR_WHITE,
            'selected': curses.COLOR_CYAN,
            'title': curses.COLOR_YELLOW,
            'border': curses.COLOR_BLUE,
            'description': curses.COLOR_GREEN
        }