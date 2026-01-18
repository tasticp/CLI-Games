#!/usr/bin/env python3
"""
Quick demo of the CLI Games Launcher without the full ncurses interface.
Shows the functionality in a simple text format.
"""

from core.config import Config
from core.plugin_manager import PluginManager
from plugins.base_game import GameMode

def main():
    print("=" * 60)
    print("CLI GAMES LAUNCHER - DEMO")
    print("=" * 60)
    
    # Initialize system
    config = Config()
    plugin_manager = PluginManager(config)
    plugin_manager.load_all_plugins()
    
    print(f"\nConfiguration loaded from: {config.config_dir}")
    print(f"Plugins discovered: {len(plugin_manager.discover_plugins())}")
    print(f"Plugins loaded: {len(plugin_manager.get_all_plugins())}")
    
    # Show available games
    print("\n" + "=" * 40)
    print("AVAILABLE GAMES")
    print("=" * 40)
    
    plugins = plugin_manager.get_enabled_plugins()
    for plugin_id, info in plugins.items():
        metadata = info.metadata
        
        print(f"\n> {metadata.get('name', 'Unknown')}")
        print(f"   Description: {metadata.get('description', 'No description')}")
        print(f"   Genre: {metadata.get('genre', 'Unknown')}")
        print(f"   Author: {metadata.get('author', 'Unknown')}")
        print(f"   Version: {metadata.get('version', 'Unknown')}")
        print(f"   Controls: {', '.join(list(metadata.get('controls', {}).keys())[:3])}...")
        
        modes = metadata.get('supported_modes', [])
        mode_names = [mode.replace('_', ' ').title() for mode in modes]
        print(f"   Modes: {', '.join(mode_names)}")
    
    # Show plugin statistics
    print("\n" + "=" * 40)
    print("PLUGIN STATISTICS")
    print("=" * 40)
    
    stats = plugin_manager.get_plugin_stats()
    print(f"Total plugins: {stats['total_plugins']}")
    print(f"Enabled plugins: {stats['enabled_plugins']}")
    print(f"Disabled plugins: {stats['disabled_plugins']}")
    
    print("\nGenres:")
    for genre, count in stats['genres'].items():
        print(f"  {genre}: {count} game(s)")
    
    # Show ASCII art capabilities
    print("\n" + "=" * 40)
    print("ASCII ART DEMO")
    print("=" * 40)
    
    from ui.renderer import ASCIIRenderer, FontStyle
    
    renderer = ASCIIRenderer()
    
    # Render some text (simplified to avoid Unicode issues)
    print("\nBANNER TEXT:")
    print("   ____   ____  ____  ____  _____   ____   ___   ___  ____ ")
    print("  | _  | |    ||    ||    ||     | |    | |   | |   ||    |")
    print("  | | | |  _  ||  __||  __||  |--| | |- | |---| |---||  __|")
    print("  | |_| | |   || |    | |  |  |  | | | | |   | |   || |   ")
    print("  |____| |___||____||____||_____| |___| |   | |___||____|")
    
    # Show sprites (simplified)
    print("\nSPRITE EXAMPLES:")
    sprites = renderer.get_available_sprites()
    print(f"Available sprites: {', '.join(sprites)}")
    print("(Sprite rendering contains Unicode characters - run main launcher to see)")
    
    # Show configuration
    print("\n" + "=" * 40)
    print("CURRENT SETTINGS")
    print("=" * 40)
    
    print(f"Display theme: {config.get('theme.text_color', 'default')}")
    print(f"Game difficulty: {config.get('gameplay.difficulty', 'normal')}")
    print(f"FPS limit: {config.get('display.fps', 60)}")
    print(f"Sound enabled: {config.get('display.sound_enabled', True)}")
    print(f"Online features: {config.get('online.enable_online_features', True)}")
    
    print("\n" + "=" * 60)
    print("LAUNCHER READY!")
    print("=" * 60)
    print("To start the full interactive launcher, run:")
    print("  python main.py")
    print("\nTo run the test suite, run:")
    print("  python test_launcher.py")
    print("\nEnjoy playing CLI Games!")

if __name__ == "__main__":
    main()