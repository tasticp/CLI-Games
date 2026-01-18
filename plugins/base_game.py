"""
Base game interface for all CLI games.
Provides common functionality and standardization across all games.
"""

import curses
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum

class GameMode(Enum):
    """Supported game modes."""
    NORMAL = "normal"
    TIME_ATTACK = "time_attack"
    INFINITE = "infinite"
    SPEEDRUN = "speedrun"
    PRACTICE = "practice"
    MULTIPLAYER = "multiplayer"

class BaseGame(ABC):
    """Base class for all games in the launcher."""
    
    def __init__(self):
        self.name = "Unknown Game"
        self.description = "No description available"
        self.genre = "Unknown"
        self.author = "Unknown"
        self.version = "1.0.0"
        self.controls = {}
        self.supported_modes = [GameMode.NORMAL]
        self.min_players = 1
        self.max_players = 1
        self.screen = None
        self.running = False
        self.score = 0
        self.high_score = 0
        
    @abstractmethod
    def run(self, screen, mode=GameMode.NORMAL, **kwargs) -> int:
        """
        Main game loop.
        
        Args:
            screen: curses screen object
            mode: game mode to play
            **kwargs: additional game-specific parameters
            
        Returns:
            Final score achieved
        """
        pass
    
    @abstractmethod
    def get_controls_help(self) -> str:
        """Return help text for game controls."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return game metadata for the launcher."""
        return {
            'name': self.name,
            'description': self.description,
            'genre': self.genre,
            'author': self.author,
            'version': self.version,
            'controls': self.controls,
            'supported_modes': [mode.value for mode in self.supported_modes],
            'min_players': self.min_players,
            'max_players': self.max_players,
            'high_score': self.high_score
        }
    
    def validate_mode(self, mode: GameMode) -> bool:
        """Check if a game mode is supported."""
        return mode in self.supported_modes
    
    def setup_screen(self, screen):
        """Setup the screen for this game."""
        self.screen = screen
        curses.curs_set(0)  # Hide cursor
        screen.nodelay(1)  # Non-blocking input
        screen.timeout(100)  # Input timeout in ms
        
    def cleanup_screen(self, screen):
        """Clean up the screen after the game."""
        curses.curs_set(1)  # Show cursor
        screen.nodelay(0)  # Blocking input
        screen.clear()
        screen.refresh()
    
    def show_controls(self, screen):
        """Display controls on screen."""
        height, width = screen.getmaxyx()
        controls_text = self.get_controls_help()
        lines = controls_text.split('\n')
        
        # Display controls at bottom of screen
        for i, line in enumerate(lines):
            if i + 1 < height:
                screen.addstr(height - len(lines) + i, 2, line[:width-3])
    
    def show_score(self, screen):
        """Display current score."""
        if self.screen:
            self.screen.addstr(0, 0, f"Score: {self.score} | High Score: {self.high_score}")
    
    def game_over(self, screen, message="Game Over!"):
        """Display game over screen."""
        height, width = screen.getmaxyx()
        
        # Clear screen
        screen.clear()
        
        # Display game over message
        msg_lines = [
            "╔" + "═" * (width - 4) + "╗",
            "║" + " " * (width - 4) + "║",
            f"║{message:^{width - 2}}║",
            f"║{'':^{width - 2}}║",
            f"║{'Final Score:':^{width - 2}}║",
            f"║{self.score:^{width - 2}}║",
            f"║{'':^{width - 2}}║",
            f"║{'Press any key to continue...':^{width - 2}}║",
            "║" + " " * (width - 4) + "║",
            "╚" + "═" * (width - 4) + "╝"
        ]
        
        for i, line in enumerate(msg_lines):
            if i < height:
                screen.addstr(i, 0, line)
        
        screen.refresh()
        screen.nodelay(0)  # Wait for keypress
        screen.getch()
        screen.nodelay(1)  # Resume non-blocking
    
    def handle_input(self, screen):
        """Handle game input. Override in subclasses."""
        key = screen.getch()
        if key == 27:  # ESC key
            self.running = False
        return key