"""
CLI Games Launcher - Main Entry Point
A modular terminal game launcher with support for plugins and various game modes.
"""

import sys
import os
import curses
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.launcher import GameLauncher
from core.config import Config

def main():
    """Main entry point for the CLI Games Launcher."""
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize and start the launcher
        launcher = GameLauncher(config)
        launcher.start()
        
    except KeyboardInterrupt:
        print("\nGoodbye! Thanks for playing!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()