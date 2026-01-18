"""
Configuration management for the CLI Games Launcher.
Handles settings, preferences, and plugin configuration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for the game launcher."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.cli-games'
        self.config_file = self.config_dir / 'config.json'
        self.plugins_file = self.config_dir / 'plugins.json'
        self.leaderboard_file = self.config_dir / 'leaderboard.json'
        
        # Default configuration
        self.default_config = {
            'theme': {
                'background_color': 'black',
                'text_color': 'white',
                'accent_color': 'cyan',
                'error_color': 'red',
                'success_color': 'green'
            },
            'display': {
                'fps': 60,
                'show_fps': False,
                'sound_enabled': True,
                'vibration_enabled': False,
                'screen_shake': False
            },
            'gameplay': {
                'difficulty': 'normal',
                'auto_save': True,
                'show_controls': True,
                'pause_on_focus_loss': True
            },
            'ui': {
                'menu_animation_speed': 0.3,
                'show_game_previews': True,
                'sort_games_by': 'name',
                'show_favorites_first': True
            },
            'online': {
                'enable_online_features': True,
                'auto_sync_leaderboards': True,
                'enable_multiplayer': True,
                'anonymous_data': True
            },
            'plugins': {
                'auto_update': True,
                'enable_community_plugins': True,
                'plugin_source': 'official'
            }
        }
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating defaults if needed."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_configs(self.default_config, loaded_config)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return default config if file doesn't exist or is invalid
        self.save_config(self.default_config)
        return self.default_config.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file."""
        config_to_save = config if config is not None else self.config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2)
            if config is not None:
                self.config = config_to_save
        except IOError:
            pass
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'theme.background_color')."""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key_path.split('.')
        config_section = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config_section:
                config_section[key] = {}
            config_section = config_section[key]
        
        # Set the final value
        config_section[keys[-1]] = value
        self.save_config()
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded config with defaults."""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def load_plugins_config(self) -> Dict[str, Any]:
        """Load plugin configuration."""
        if self.plugins_file.exists():
            try:
                with open(self.plugins_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            'enabled_plugins': [],
            'disabled_plugins': [],
            'plugin_settings': {},
            'last_check': None
        }
    
    def save_plugins_config(self, config: Dict[str, Any]):
        """Save plugin configuration."""
        try:
            with open(self.plugins_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except IOError:
            pass
    
    def load_leaderboard(self) -> Dict[str, Any]:
        """Load leaderboard data."""
        if self.leaderboard_file.exists():
            try:
                with open(self.leaderboard_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            'local_scores': {},
            'global_scores': {},
            'personal_best': {},
            'achievements': {}
        }
    
    def save_leaderboard(self, leaderboard: Dict[str, Any]):
        """Save leaderboard data."""
        try:
            with open(self.leaderboard_file, 'w', encoding='utf-8') as f:
                json.dump(leaderboard, f, indent=2)
        except IOError:
            pass
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = self.default_config.copy()
        self.save_config()