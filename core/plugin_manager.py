"""
Plugin manager for the CLI Games Launcher.
Handles dynamic loading, unloading, and management of game plugins.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
import traceback

from plugins.base_game import BaseGame

class PluginInfo:
    """Information about a loaded plugin."""
    
    def __init__(self, module_path: Path, game_class: Type[BaseGame]):
        self.module_path = module_path
        self.game_class = game_class
        self.game_instance = None
        self.enabled = True
        self.metadata = {}
        
        # Create instance to get metadata
        try:
            temp_instance = game_class()
            self.metadata = temp_instance.get_metadata()
        except Exception:
            pass
    
    def create_instance(self) -> BaseGame:
        """Create a new instance of the game."""
        return self.game_class()

class PluginManager:
    """Manages loading and execution of game plugins."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.plugins: Dict[str, PluginInfo] = {}
        self.search_paths = [
            Path(__file__).parent.parent / "plugins" / "builtin",  # Built-in plugins
            Path(__file__).parent.parent / "plugins" / "external",  # External plugins
            Path.home() / '.cli-games' / 'plugins'  # User plugins
        ]
        
        # Ensure directories exist
        for path in self.search_paths:
            path.mkdir(parents=True, exist_ok=True)
    
    def discover_plugins(self) -> List[str]:
        """Discover all available plugins in search paths."""
        discovered = []
        
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
                
            # Look for Python files that contain game classes
            for file_path in search_path.rglob("*.py"):
                if file_path.name.startswith("__"):
                    continue
                
                plugin_id = str(file_path.relative_to(search_path).with_suffix(""))
                discovered.append(plugin_id)
        
        return discovered
    
    def load_plugin(self, plugin_path: str) -> Optional[PluginInfo]:
        """Load a single plugin by path."""
        # Try to find the plugin file
        plugin_file = None
        base_path = None
        
        for search_path in self.search_paths:
            potential_path = search_path / plugin_path
            if potential_path.with_suffix(".py").exists():
                plugin_file = potential_path.with_suffix(".py")
                base_path = search_path
                break
            elif potential_path.is_dir() and (potential_path / "__init__.py").exists():
                plugin_file = potential_path / "__init__.py"
                base_path = potential_path
                break
        
        if not plugin_file or not plugin_file.exists():
            return None
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(plugin_path, plugin_file)
            if spec is None or spec.loader is None:
                return None
                
            module = importlib.util.module_from_spec(spec)
            
            # Add the plugin's directory to sys.path for imports
            if base_path:
                sys.path.insert(0, str(base_path))
            
            spec.loader.exec_module(module)
            
            # Remove from sys.path after loading
            if base_path and str(base_path) in sys.path:
                sys.path.remove(str(base_path))
            
            # Look for BaseGame subclasses in the module
            game_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseGame) and 
                    attr is not BaseGame):
                    game_classes.append(attr)
            
            if not game_classes:
                return None
            
            # Use the first game class found (could be enhanced to handle multiple)
            game_class = game_classes[0]
            
            # Create plugin info
            plugin_info = PluginInfo(plugin_file, game_class)
            
            return plugin_info
            
        except Exception as e:
            print(f"Error loading plugin {plugin_path}: {e}")
            traceback.print_exc()
            return None
    
    def load_all_plugins(self):
        """Load all discovered plugins."""
        discovered = self.discover_plugins()
        
        for plugin_id in discovered:
            if plugin_id not in self.plugins:
                plugin_info = self.load_plugin(plugin_id)
                if plugin_info:
                    self.plugins[plugin_id] = plugin_info
    
    def unload_plugin(self, plugin_id: str):
        """Unload a plugin."""
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get a loaded plugin by ID."""
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """Get all loaded plugins."""
        return self.plugins.copy()
    
    def get_enabled_plugins(self) -> Dict[str, PluginInfo]:
        """Get only enabled plugins."""
        return {pid: info for pid, info in self.plugins.items() if info.enabled}
    
    def enable_plugin(self, plugin_id: str):
        """Enable a plugin."""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = True
            self._save_plugin_settings()
    
    def disable_plugin(self, plugin_id: str):
        """Disable a plugin."""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = False
            self._save_plugin_settings()
    
    def get_plugins_by_genre(self, genre: str) -> Dict[str, PluginInfo]:
        """Get plugins filtered by genre."""
        return {pid: info for pid, info in self.get_enabled_plugins().items() 
                if info.metadata.get('genre', '').lower() == genre.lower()}
    
    def search_plugins(self, query: str) -> Dict[str, PluginInfo]:
        """Search plugins by name, description, or genre."""
        query = query.lower()
        results = {}
        
        for plugin_id, info in self.get_enabled_plugins().items():
            metadata = info.metadata
            
            # Check name, description, and genre
            if (query in metadata.get('name', '').lower() or
                query in metadata.get('description', '').lower() or
                query in metadata.get('genre', '').lower()):
                results[plugin_id] = info
        
        return results
    
    def _save_plugin_settings(self):
        """Save plugin enabled/disabled settings."""
        plugins_config = self.config.load_plugins_config()
        
        enabled_plugins = []
        disabled_plugins = []
        
        for plugin_id, info in self.plugins.items():
            if info.enabled:
                enabled_plugins.append(plugin_id)
            else:
                disabled_plugins.append(plugin_id)
        
        plugins_config['enabled_plugins'] = enabled_plugins
        plugins_config['disabled_plugins'] = disabled_plugins
        
        self.config.save_plugins_config(plugins_config)
    
    def _load_plugin_settings(self):
        """Load plugin enabled/disabled settings."""
        plugins_config = self.config.load_plugins_config()
        
        enabled = set(plugins_config.get('enabled_plugins', []))
        disabled = set(plugins_config.get('disabled_plugins', []))
        
        # Apply settings to loaded plugins
        for plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = (
                plugin_id in enabled or 
                (plugin_id not in disabled and plugin_id not in enabled)
            )
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin."""
        if plugin_id in self.plugins:
            # Unload first
            old_info = self.plugins[plugin_id]
            del self.plugins[plugin_id]
            
            # Load fresh
            new_info = self.load_plugin(plugin_id)
            if new_info:
                # Restore enabled state
                new_info.enabled = old_info.enabled
                self.plugins[plugin_id] = new_info
                return True
        
        return False
    
    def install_plugin(self, plugin_url: str) -> bool:
        """Install a plugin from URL (future enhancement)."""
        # This would involve downloading and installing plugins
        # For now, return False as not implemented
        return False
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded plugins."""
        total = len(self.plugins)
        enabled = len(self.get_enabled_plugins())
        
        genres = {}
        for info in self.get_enabled_plugins().values():
            genre = info.metadata.get('genre', 'Unknown')
            genres[genre] = genres.get(genre, 0) + 1
        
        return {
            'total_plugins': total,
            'enabled_plugins': enabled,
            'disabled_plugins': total - enabled,
            'genres': genres
        }