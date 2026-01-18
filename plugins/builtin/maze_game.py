"""
Procedurally generated maze game.
Navigate through randomly generated mazes with multiple difficulty levels and game modes.
"""

import random
import curses
import time
from typing import List, Tuple, Optional
from enum import Enum

from plugins.base_game import BaseGame, GameMode

class CellType(Enum):
    EMPTY = 0
    WALL = 1
    PLAYER = 2
    EXIT = 3
    COIN = 4
    ENEMY = 5
    VISITED = 6

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class MazeGame(BaseGame):
    """A procedurally generated maze game."""
    
    def __init__(self):
        super().__init__()
        self.name = "Maze Runner"
        self.description = "Navigate through procedurally generated mazes"
        self.genre = "Puzzle"
        self.author = "CLI Games Team"
        self.version = "1.0.0"
        self.controls = {
            "Arrow Keys": "Move player",
            "WASD": "Alternative movement",
            "ESC": "Quit game",
            "R": "Regenerate maze"
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
        self.maze = []
        self.width = 0
        self.height = 0
        self.player_pos = (0, 0)
        self.exit_pos = (0, 0)
        self.coins = []
        self.enemies = []
        self.visited_cells = set()
        self.moves = 0
        self.start_time = 0
        self.time_limit = 0
        self.game_over = False
        self.won = False
        self.difficulty = 1
        self.level = 1
        
        # Rendering
        self.render_buffer = []
    
    def run(self, screen, mode=GameMode.NORMAL, **kwargs):
        """Main game loop."""
        self.screen = screen
        self.setup_screen(screen)
        
        # Initialize game based on mode
        self._initialize_game(mode, **kwargs)
        
        # Game loop
        self.running = True
        clock = time.time()
        
        while self.running and not self.game_over:
            # Handle input
            self._handle_game_input(screen)
            
            # Update game state
            self._update()
            
            # Render
            self._render(screen)
            
            # Control frame rate
            current_time = time.time()
            elapsed = current_time - clock
            if elapsed < 0.05:  # 20 FPS
                time.sleep(0.05 - elapsed)
            clock = time.time()
        
        self.cleanup_screen(screen)
        return self.score
    
    def _initialize_game(self, mode, **kwargs):
        """Initialize game based on selected mode."""
        self.game_over = False
        self.won = False
        self.moves = 0
        self.level = 1
        self.difficulty = kwargs.get('difficulty', 1)
        
        # Get screen dimensions
        height, width = self.screen.getmaxyx()
        
        # Calculate maze size (leave room for UI)
        self.width = min(width - 4, 40)
        self.height = min(height - 6, 20)
        
        # Ensure odd dimensions for maze generation
        if self.width % 2 == 0:
            self.width -= 1
        if self.height % 2 == 0:
            self.height -= 1
        
        # Mode-specific initialization
        if mode == GameMode.TIME_ATTACK:
            self.time_limit = 120 + (30 * (3 - self.difficulty))  # 2-3 minutes
            self.start_time = time.time()
        elif mode == GameMode.INFINITE:
            self.level = 1
        elif mode == GameMode.SPEEDRUN:
            self.time_limit = 60 + (20 * (3 - self.difficulty))  # 1-2 minutes
            self.start_time = time.time()
        
        # Generate first maze
        self._generate_maze()
    
    def _generate_maze(self):
        """Generate a random maze using recursive backtracking."""
        # Initialize maze with walls
        self.maze = [[CellType.WALL for _ in range(self.width)] for _ in range(self.height)]
        
        # Generate maze using recursive backtracking
        self._carve_maze(1, 1)
        
        # Place player at top-left
        self.player_pos = (1, 1)
        self.maze[1][1] = CellType.PLAYER
        
        # Place exit at bottom-right area
        exit_area_x = self.width - 2
        exit_area_y = self.height - 2
        while self.maze[exit_area_y][exit_area_x] == CellType.WALL:
            exit_area_x -= 2
            exit_area_y -= 2
        self.exit_pos = (exit_area_x, exit_area_y)
        self.maze[exit_area_y][exit_area_x] = CellType.EXIT
        
        # Add coins based on difficulty
        self.coins.clear()
        coin_count = 5 + self.level * 2
        self._place_items(CellType.COIN, coin_count)
        
        # Add enemies for higher difficulties
        self.enemies.clear()
        if self.difficulty > 1:
            enemy_count = self.difficulty - 1
            self._place_items(CellType.ENEMY, enemy_count)
        
        # Clear visited cells
        self.visited_cells = {(1, 1)}
    
    def _carve_maze(self, x, y):
        """Carve maze paths using recursive backtracking."""
        self.maze[y][x] = CellType.EMPTY
        
        # Randomize directions
        directions = list(Direction)
        random.shuffle(directions)
        
        for direction in directions:
            dx, dy = direction.value
            nx, ny = x + dx * 2, y + dy * 2
            
            if (0 < nx < self.width - 1 and 
                0 < ny < self.height - 1 and 
                self.maze[ny][nx] == CellType.WALL):
                
                # Carve path
                self.maze[y + dy][x + dx] = CellType.EMPTY
                self._carve_maze(nx, ny)
    
    def _place_items(self, item_type: CellType, count: int):
        """Place items (coins, enemies) randomly in empty cells."""
        placed = 0
        attempts = 0
        max_attempts = count * 10
        
        while placed < count and attempts < max_attempts:
            x = random.randrange(1, self.width - 1)
            y = random.randrange(1, self.height - 1)
            
            if (self.maze[y][x] == CellType.EMPTY and 
                (x, y) != self.player_pos and 
                (x, y) != self.exit_pos):
                
                self.maze[y][x] = item_type
                if item_type == CellType.COIN:
                    self.coins.append((x, y))
                elif item_type == CellType.ENEMY:
                    self.enemies.append((x, y))
                placed += 1
            
            attempts += 1
    
    def _handle_game_input(self, screen):
        """Handle keyboard input."""
        key = screen.getch()
        
        if key == 27:  # ESC
            self.running = False
            return
        
        # Movement
        dx, dy = 0, 0
        if key in [curses.KEY_UP, ord('w'), ord('W')]:
            dy = -1
        elif key in [curses.KEY_DOWN, ord('s'), ord('S')]:
            dy = 1
        elif key in [curses.KEY_LEFT, ord('a'), ord('A')]:
            dx = -1
        elif key in [curses.KEY_RIGHT, ord('d'), ord('D')]:
            dx = 1
        elif key in [ord('r'), ord('R')]:
            # Regenerate maze
            self._generate_maze()
            return
        
        # Try to move
        if dx != 0 or dy != 0:
            new_x = self.player_pos[0] + dx
            new_y = self.player_pos[1] + dy
            
            # Check bounds and walls
            if (0 <= new_x < self.width and 
                0 <= new_y < self.height and 
                self.maze[new_y][new_x] != CellType.WALL):
                
                # Clear current position
                if self.maze[self.player_pos[1]][self.player_pos[0]] == CellType.PLAYER:
                    self.maze[self.player_pos[1]][self.player_pos[0]] = CellType.VISITED
                
                # Move player
                self.player_pos = (new_x, new_y)
                self.moves += 1
                self.visited_cells.add((new_x, new_y))
                
                # Check what the player stepped on
                cell_type = self.maze[new_y][new_x]
                
                if cell_type == CellType.COIN:
                    self.score += 10
                    self.coins.remove((new_x, new_y))
                    self.maze[new_y][new_x] = CellType.PLAYER
                elif cell_type == CellType.ENEMY:
                    self.score = max(0, self.score - 50)
                    self.maze[new_y][new_x] = CellType.PLAYER
                elif cell_type == CellType.EXIT:
                    self._handle_level_complete()
                else:
                    self.maze[new_y][new_x] = CellType.PLAYER
    
    def _update(self):
        """Update game state."""
        # Check time limit for timed modes
        if self.time_limit > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                self.game_over = True
                self.won = False
        
        # Move enemies (simple random movement)
        for i, (ex, ey) in enumerate(self.enemies[:]):
            if random.random() < 0.1:  # 10% chance to move
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                
                for dx, dy in directions:
                    new_ex, new_ey = ex + dx, ey + dy
                    
                    if (0 <= new_ex < self.width and 
                        0 <= new_ey < self.height and 
                        self.maze[new_ey][new_ex] == CellType.EMPTY):
                        
                        # Clear old position
                        if self.maze[ey][ex] == CellType.ENEMY:
                            self.maze[ey][ex] = CellType.EMPTY
                        
                        # Move enemy
                        self.enemies[i] = (new_ex, new_ey)
                        self.maze[new_ey][new_ex] = CellType.ENEMY
                        break
        
        # Check enemy collision with player
        if self.player_pos in self.enemies:
            self.score = max(0, self.score - 100)
            self.game_over = True
            self.won = False
    
    def _handle_level_complete(self):
        """Handle completion of a maze level."""
        # Calculate bonus
        time_bonus = 0
        if self.time_limit > 0:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            time_bonus = int(remaining * 2)
        
        move_bonus = max(0, 100 - self.moves)
        coin_bonus = len(self.coins) * 20
        
        self.score += 100 + time_bonus + move_bonus + coin_bonus
        
        # Handle infinite mode - next level
        if hasattr(self, 'current_mode') and self.current_mode == GameMode.INFINITE:
            self.level += 1
            self.difficulty = min(4, 1 + self.level // 3)
            self._generate_maze()
        else:
            self.game_over = True
            self.won = True
    
    def _render(self, screen):
        """Render the game."""
        screen.clear()
        height, width = screen.getmaxyx()
        
        # Draw title
        title = f"MAZE RUNNER - Level {self.level}"
        screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Calculate maze position (centered)
        maze_x = (width - self.width) // 2
        maze_y = (height - self.height) // 2
        
        # Draw maze
        for y in range(self.height):
            for x in range(self.width):
                screen_x = maze_x + x
                screen_y = maze_y + y
                
                if screen_y >= height or screen_x >= width:
                    continue
                
                cell = self.maze[y][x]
                
                if cell == CellType.WALL:
                    screen.addch(screen_y, screen_x, '█', curses.color_pair(1) if curses.has_colors() else 0)
                elif cell == CellType.EMPTY or cell == CellType.VISITED:
                    if cell == CellType.VISITED:
                        screen.addch(screen_y, screen_x, '·', curses.color_pair(2) if curses.has_colors() else 0)
                    else:
                        screen.addch(screen_y, screen_x, ' ')
                elif cell == CellType.PLAYER:
                    screen.addch(screen_y, screen_x, '@', curses.color_pair(3) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
                elif cell == CellType.EXIT:
                    screen.addch(screen_y, screen_x, '⚑', curses.color_pair(4) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
                elif cell == CellType.COIN:
                    screen.addch(screen_y, screen_x, '◉', curses.color_pair(5) if curses.has_colors() else 0)
                elif cell == CellType.ENEMY:
                    screen.addch(screen_y, screen_x, '♦', curses.color_pair(6) if curses.has_colors() else 0)
        
        # Draw UI
        self._draw_ui(screen)
        
        # Draw controls hint
        controls_text = "Arrow Keys/WASD: Move | R: Regenerate | ESC: Quit"
        screen.addstr(height - 1, (width - len(controls_text)) // 2, controls_text)
        
        screen.refresh()
    
    def _draw_ui(self, screen):
        """Draw UI elements."""
        height, width = screen.getmaxyx()
        
        # Score and info
        info_lines = [
            f"Score: {self.score}",
            f"Moves: {self.moves}",
            f"Coins: {len(self.coins)}",
            f"Difficulty: {self.difficulty}"
        ]
        
        if self.time_limit > 0:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            info_lines.append(f"Time: {remaining:.1f}s")
        
        for i, line in enumerate(info_lines):
            screen.addstr(2 + i, 2, line)
        
        # Mini-map (if space allows)
        if width > self.width + 20 and height > self.height + 10:
            self._draw_minimap(screen)
    
    def _draw_minimap(self, screen):
        """Draw a small minimap."""
        height, width = screen.getmaxyx()
        minimap_x = width - 20
        minimap_y = 2
        minimap_width = min(15, self.width)
        minimap_height = min(10, self.height)
        
        # Scale factor
        scale_x = self.width / minimap_width
        scale_y = self.height / minimap_height
        
        # Draw minimap border
        for x in range(minimap_width + 2):
            screen.addch(minimap_y - 1, minimap_x + x, '─')
            screen.addch(minimap_y + minimap_height, minimap_x + x, '─')
        
        for y in range(minimap_height):
            screen.addch(minimap_y + y, minimap_x - 1, '│')
            screen.addch(minimap_y + y, minimap_x + minimap_width + 1, '│')
        
        screen.addch(minimap_y - 1, minimap_x - 1, '┌')
        screen.addch(minimap_y - 1, minimap_x + minimap_width + 1, '┐')
        screen.addch(minimap_y + minimap_height, minimap_x - 1, '└')
        screen.addch(minimap_y + minimap_height, minimap_x + minimap_width + 1, '┘')
        
        # Draw minimap content
        for my in range(minimap_height):
            for mx in range(minimap_width):
                maze_x = int(mx * scale_x)
                maze_y = int(my * scale_y)
                
                if maze_x < self.width and maze_y < self.height:
                    screen_y = minimap_y + my
                    screen_x = minimap_x + mx
                    
                    if (maze_x, maze_y) == self.player_pos:
                        screen.addch(screen_y, screen_x, '@')
                    elif (maze_x, maze_y) == self.exit_pos:
                        screen.addch(screen_y, screen_x, 'E')
                    elif self.maze[maze_y][maze_x] == CellType.WALL:
                        screen.addch(screen_y, screen_x, '█')
                    elif (maze_x, maze_y) in self.visited_cells:
                        screen.addch(screen_y, screen_x, '·')
    
    def get_controls_help(self) -> str:
        """Return help text for game controls."""
        return """
CONTROLS:
↑/W - Move Up
↓/S - Move Down  
←/A - Move Left
→/D - Move Right
R - Regenerate Maze
ESC - Quit Game

OBJECTIVE:
Navigate to the flag (⚑) to complete the maze.
Collect coins (◉) for bonus points.
Avoid enemies (♦) or lose points!
Visited paths are marked with dots (·).

GAME MODES:
Normal: Complete the maze at your own pace.
Time Attack: Race against the clock!
Speedrun: Complete as fast as possible.
Infinite: Progressively harder mazes.
"""