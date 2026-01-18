#!/usr/bin/env python3
"""
Test script for CLI Games Launcher.
Verifies all components are working correctly.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test if all modules can be imported."""
    print("Testing imports...")
    
    try:
        from core.config import Config
        print("+ Config module imported")
    except Exception as e:
        print(f"- Config import failed: {e}")
        return False
    
    try:
        from ui.menu import Menu
        print("+ Menu module imported")
    except Exception as e:
        print(f"- Menu import failed: {e}")
        return False
    
    try:
        from core.plugin_manager import PluginManager
        print("+ Plugin Manager imported")
    except Exception as e:
        print(f"- Plugin Manager import failed: {e}")
        return False
    
    try:
        from plugins.base_game import BaseGame
        print("+ Base Game module imported")
    except Exception as e:
        print(f"- Base Game import failed: {e}")
        return False
    
    try:
        from plugins.builtin.maze_game import MazeGame
        print("+ Maze Game imported")
    except Exception as e:
        print(f"- Maze Game import failed: {e}")
        return False
    
    try:
        from plugins.builtin.snake_game import SnakeGame
        print("+ Snake Game imported")
    except Exception as e:
        print(f"- Snake Game import failed: {e}")
        return False
    
    return True

def test_plugin_system():
    """Test the plugin system."""
    print("\nTesting plugin system...")
    
    try:
        from core.config import Config
        from core.plugin_manager import PluginManager
        
        config = Config()
        plugin_manager = PluginManager(config)
        
        # Test plugin discovery
        plugins = plugin_manager.discover_plugins()
        print(f"+ Discovered {len(plugins)} plugins")
        
        # Test plugin loading
        plugin_manager.load_all_plugins()
        loaded = plugin_manager.get_all_plugins()
        print(f"+ Loaded {len(loaded)} plugins")
        
        # Test plugin metadata
        for plugin_id, info in loaded.items():
            metadata = info.metadata
            print(f"  - {metadata.get('name', 'Unknown')}: {metadata.get('genre', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"- Plugin system test failed: {e}")
        traceback.print_exc()
        return False

def test_games():
    """Test individual games."""
    print("\nTesting games...")
    
    try:
        from plugins.builtin.maze_game import MazeGame
        from plugins.builtin.snake_game import SnakeGame
        
        # Test Maze Game
        maze = MazeGame()
        print(f"+ Maze Game: {maze.name} - {maze.description}")
        print(f"  Controls: {list(maze.controls.keys())}")
        print(f"  Modes: {[mode.value for mode in maze.supported_modes]}")
        
        # Test Snake Game
        snake = SnakeGame()
        print(f"+ Snake Game: {snake.name} - {snake.description}")
        print(f"  Controls: {list(snake.controls.keys())}")
        print(f"  Modes: {[mode.value for mode in snake.supported_modes]}")
        
        return True
        
    except Exception as e:
        print(f"- Games test failed: {e}")
        traceback.print_exc()
        return False

def test_ascii_renderer():
    """Test ASCII renderer."""
    print("\nTesting ASCII renderer...")
    
    try:
        from ui.renderer import ASCIIRenderer, FontStyle
        
        renderer = ASCIIRenderer()
        
        # Test text rendering
        text = renderer.render_text("HELLO", FontStyle.STANDARD)
        print(f"+ Text rendering: {len(text)} lines")
        
        # Test available fonts
        fonts = renderer.get_available_fonts()
        print(f"+ Available fonts: {fonts}")
        
        # Test sprites
        sprites = renderer.get_available_sprites()
        print(f"+ Available sprites: {sprites}")
        
        return True
        
    except Exception as e:
        print(f"- ASCII renderer test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("CLI Games Launcher - Test Suite")
    print("=" * 40)
    
    tests = [
        ("Import Tests", test_imports),
        ("Plugin System", test_plugin_system),
        ("Games", test_games),
        ("ASCII Renderer", test_ascii_renderer)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"- {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("* All tests passed! The launcher is ready to run.")
        print("\nTo start the launcher, run:")
        print("python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())