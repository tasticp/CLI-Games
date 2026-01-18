"""
Main game launcher that coordinates the menu system, plugins, and game execution.
"""

import curses
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from core.config import Config
from core.plugin_manager import PluginManager
from ui.menu import Menu, MenuItem, MenuAction
from plugins.base_game import BaseGame, GameMode

class GameLauncher:
    """Main launcher for CLI games."""
    
    def __init__(self, config: Config):
        self.config = config
        self.plugin_manager = PluginManager(config)
        self.running = True
        
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
        leaderboard_menu = Menu("LEADERBOARDS", "View high scores")
        
        leaderboard_menu.add_text("Local Scores", "Your personal best scores")
        leaderboard_menu.add_text("Global Scores", "Top scores worldwide")
        leaderboard_menu.add_text("Friends", "Compete with your friends")
        leaderboard_menu.add_text("Achievements", "View your accomplishments")
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
            
            # Update high score
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