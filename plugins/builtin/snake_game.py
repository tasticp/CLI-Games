"""
Classic Snake game implementation.
Guide the snake to eat food and grow longer while avoiding walls and yourself.
"""

import random
import curses
import time
from typing import List, Tuple
from enum import Enum

from plugins.base_game import BaseGame, GameMode

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class SnakeGame(BaseGame):
    """Classic Snake game with multiple modes and difficulty levels."""
    
    def __init__(self):
        super().__init__()
        self.name = "Snake Classic"
        self.description = "The timeless snake game - eat, grow, don't crash!"
        self.genre = "Arcade"
        self.author = "CLI Games Team"
        self.version = "1.0.0"
        self.controls = {
            "Arrow Keys": "Control snake direction",
            "WASD": "Alternative controls",
            "P": "Pause game",
            "ESC": "Quit game"
        }
        self.supported_modes = [
            GameMode.NORMAL,
            GameMode.TIME_ATTACK,
            GameMode.INFINITE,
            GameMode.SPEEDRUN
        ]
        self.min_players = 1
        self.max_players = 1
        
        # Game state
        self.snake = []
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.food_pos = (0, 0)
        self.special_food = None
        self.special_food_timer = 0
        self.width = 0
        self.height = 0
        self.game_speed = 100  # milliseconds between updates
        self.moves = 0
        self.food_eaten = 0
        self.level = 1
        self.paused = False
        self.game_over = False
        self.start_time = 0
        self.time_limit = 0
        self.last_update = 0
        
    def run(self, screen, mode=GameMode.NORMAL, **kwargs):
        """Main game loop."""
        self.screen = screen
        self.setup_screen(screen)
        
        # Initialize game
        self._initialize_game(mode, **kwargs)
        
        # Game loop
        self.running = True
        clock = time.time()
        
        while self.running and not self.game_over:
            current_time = time.time()
            
            # Handle input
            self._handle_game_input(screen)
            
            # Update game state (at game speed)
            if current_time - self.last_update >= self.game_speed / 1000.0:
                self._update()
                self.last_update = current_time
            
            # Render
            self._render(screen)
            
            # Small delay to prevent CPU hogging
            time.sleep(0.01)
        
        self.cleanup_screen(screen)
        return self.score
    
    def _initialize_game(self, mode, **kwargs):
        """Initialize game state."""
        self.game_over = False
        self.paused = False
        self.score = 0
        self.moves = 0
        self.food_eaten = 0
        self.level = 1
        self.current_mode = mode
        
        # Get screen dimensions
        height, width = self.screen.getmaxyx()
        
        # Calculate game area (leave room for UI)
        self.width = min(width - 4, 30)
        self.height = min(height - 6, 20)
        
        # Mode-specific settings
        if mode == GameMode.NORMAL:
            self.game_speed = 150
        elif mode == GameMode.TIME_ATTACK:
            self.game_speed = 120
            self.time_limit = 180  # 3 minutes
            self.start_time = time.time()
        elif mode == GameMode.INFINITE:
            self.game_speed = 100
        elif mode == GameMode.SPEEDRUN:
            self.game_speed = 80  # Faster for speedrun
            self.time_limit = 120  # 2 minutes
            self.start_time = time.time()
        
        # Initialize snake
        self._initialize_snake()
        
        # Place first food
        self._place_food()
    
    def _initialize_snake(self):
        """Initialize the snake in the center of the screen."""
        start_x = self.width // 2
        start_y = self.height // 2
        
        self.snake = [
            (start_x, start_y),      # Head
            (start_x - 1, start_y),  # Body
            (start_x - 2, start_y)   # Tail
        ]
        
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
    
    def _place_food(self):
        """Place food at a random position not occupied by the snake."""
        available_positions = []
        
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in self.snake:
                    available_positions.append((x, y))
        
        if available_positions:
            self.food_pos = random.choice(available_positions)
            
            # Occasionally place special food
            if random.random() < 0.1:  # 10% chance
                self.special_food = self.food_pos
                self.special_food_timer = 50  # 5 seconds at 10 FPS
    
    def _handle_game_input(self, screen):
        """Handle keyboard input."""
        key = screen.getch()
        
        if key == 27:  # ESC
            self.running = False
            return
        elif key in [ord('p'), ord('P')]:
            self.paused = not self.paused
            return
        
        if self.paused:
            return
        
        # Direction changes (prevent reversing into self)
        if key in [curses.KEY_UP, ord('w'), ord('W')] and self.direction != Direction.DOWN:
            self.next_direction = Direction.UP
        elif key in [curses.KEY_DOWN, ord('s'), ord('S')] and self.direction != Direction.UP:
            self.next_direction = Direction.DOWN
        elif key in [curses.KEY_LEFT, ord('a'), ord('A')] and self.direction != Direction.RIGHT:
            self.next_direction = Direction.LEFT
        elif key in [curses.KEY_RIGHT, ord('d'), ord('D')] and self.direction != Direction.LEFT:
            self.next_direction = Direction.RIGHT
    
    def _update(self):
        """Update game state."""
        if self.paused or self.game_over:
            return
        
        # Check time limit for timed modes
        if self.time_limit > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                self.game_over = True
                return
        
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        
        # Check collisions
        if (new_head[0] < 0 or new_head[0] >= self.width or
            new_head[1] < 0 or new_head[1] >= self.height or
            new_head in self.snake):
            self.game_over = True
            return
        
        # Move snake
        self.snake.insert(0, new_head)
        self.moves += 1
        
        # Check if food eaten
        food_eaten = False
        if new_head == self.food_pos:
            self.food_eaten += 1
            self.score += 10
            food_eaten = True
            self._place_food()
            
            # Level progression
            if self.food_eaten % 5 == 0:
                self.level += 1
                self.game_speed = max(50, self.game_speed - 10)  # Speed up
        elif new_head == self.special_food:
            self.score += 50
            self.special_food = None
            self.special_food_timer = 0
        else:
            # Remove tail if no food eaten
            self.snake.pop()
        
        # Update special food timer
        if self.special_food_timer > 0:
            self.special_food_timer -= 1
            if self.special_food_timer <= 0:
                self.special_food = None
        
        # Bonus for efficient movement (in speedrun mode)
        if self.current_mode == GameMode.SPEEDRUN and food_eaten:
            efficiency_bonus = max(0, 20 - len(self.snake))
            self.score += efficiency_bonus
    
    def _render(self, screen):
        """Render the game."""
        screen.clear()
        height, width = screen.getmaxyx()
        
        # Draw title
        title = f"SNAKE - Level {self.level}"
        screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Calculate game area position (centered)
        game_x = (width - self.width) // 2
        game_y = (height - self.height) // 2
        
        # Draw border
        for x in range(self.width + 2):
            screen.addch(game_y - 1, game_x + x, '─')
            screen.addch(game_y + self.height, game_x + x, '─')
        
        for y in range(self.height):
            screen.addch(game_y + y, game_x - 1, '│')
            screen.addch(game_y + y, game_x + self.width + 1, '│')
        
        # Draw corners
        screen.addch(game_y - 1, game_x - 1, '┌')
        screen.addch(game_y - 1, game_x + self.width + 1, '┐')
        screen.addch(game_y + self.height, game_x - 1, '└')
        screen.addch(game_y + self.height, game_x + self.width + 1, '┘')
        
        # Draw snake
        for i, (x, y) in enumerate(self.snake):
            screen_x = game_x + x
            screen_y = game_y + y
            
            if i == 0:  # Head
                char = self._get_head_char()
                attr = curses.A_BOLD | (curses.color_pair(3) if curses.has_colors() else 0)
            else:  # Body
                char = '█'
                attr = curses.color_pair(2) if curses.has_colors() else 0
            
            screen.addch(screen_y, screen_x, char, attr)
        
        # Draw food
        food_x, food_y = self.food_pos
        screen.addch(game_y + food_y, game_x + food_x, '●', 
                    curses.color_pair(4) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        # Draw special food if present
        if self.special_food:
            sfx, sfy = self.special_food
            screen.addch(game_y + sfy, game_x + sfx, '★',
                        curses.color_pair(5) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        # Draw UI
        self._draw_ui(screen)
        
        # Draw pause overlay if paused
        if self.paused:
            self._draw_pause_overlay(screen)
        
        # Draw controls hint
        controls_text = "Arrow Keys/WASD: Move | P: Pause | ESC: Quit"
        screen.addstr(height - 1, (width - len(controls_text)) // 2, controls_text)
        
        screen.refresh()
    
    def _get_head_char(self):
        """Get the character for the snake head based on direction."""
        chars = {
            Direction.UP: '▲',
            Direction.DOWN: '▼',
            Direction.LEFT: '◄',
            Direction.RIGHT: '►'
        }
        return chars.get(self.direction, '●')
    
    def _draw_ui(self, screen):
        """Draw UI elements."""
        height, width = screen.getmaxyx()
        
        # Score and stats
        info_lines = [
            f"Score: {self.score}",
            f"Length: {len(self.snake)}",
            f"Food: {self.food_eaten}",
            f"Speed: {1000//self.game_speed} FPS"
        ]
        
        if self.time_limit > 0:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            info_lines.append(f"Time: {remaining:.1f}s")
        
        for i, line in enumerate(info_lines):
            screen.addstr(2 + i, 2, line)
        
        # Next level progress
        progress = self.food_eaten % 5
        progress_text = f"Next Level: {progress}/5"
        screen.addstr(2 + len(info_lines), 2, progress_text)
    
    def _draw_pause_overlay(self, screen):
        """Draw pause overlay."""
        height, width = screen.getmaxyx()
        
        pause_text = [
            "╔" + "═" * 20 + "╗",
            "║" + " " * 20 + "║",
            "║" + "     PAUSED     " + "║",
            "║" + " " * 20 + "║",
            "║" + "  Press P to   " + "║",
            "║" + "   resume       " + "║",
            "║" + " " * 20 + "║",
            "╚" + "═" * 20 + "╝"
        ]
        
        start_y = (height - len(pause_text)) // 2
        start_x = (width - 22) // 2
        
        for i, line in enumerate(pause_text):
            screen.addstr(start_y + i, start_x, line, curses.A_REVERSE)
    
    def get_controls_help(self) -> str:
        """Return help text for game controls."""
        return """
CONTROLS:
↑/W - Move Up
↓/S - Move Down
←/A - Move Left  
→/D - Move Right
P - Pause/Resume
ESC - Quit Game

OBJECTIVE:
Guide the snake to eat food (●) and grow longer.
Avoid hitting walls or your own body!

SPECIAL FOOD:
Watch for golden stars (★) for bonus points!

GAME MODES:
Normal: Classic snake gameplay.
Time Attack: Score as much as possible before time runs out!
Speedrun: Complete levels as quickly as possible.
Infinite: Endless gameplay with increasing speed.

SCORING:
Regular Food: +10 points
Special Food: +50 points
Efficiency Bonus: +20 points (Speedrun mode)
Level Progression: Every 5 foods eaten
"""