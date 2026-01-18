"""
Retro Pac-Man style game implementation.
Navigate through mazes while collecting dots and avoiding ghosts.
"""

import random
import curses
import time
import math
from typing import List, Optional, Tuple, Set
from enum import Enum

from plugins.base_game import BaseGame, GameMode

class CellType(Enum):
    """Types of maze cells."""
    WALL = 0
    EMPTY = 1
    DOT = 2
    POWER_PELLET = 3
    GHOST_SPAWN = 4
    PACMAN_SPAWN = 5

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

class Ghost:
    """Represents a ghost enemy."""
    
    def __init__(self, x: float, y: float, color: str, personality: str):
        self.x = x
        self.y = y
        self.color = color
        self.personality = personality
        self.direction = Direction.NONE
        self.speed = 0.08
        self.scared = False
        self.scared_timer = 0
        self.eaten = False
        self.respawn_timer = 0
        self.home_x = x
        self.home_y = y
    
    def update(self, dt: float, maze: List[List[int]], player_pos: Tuple[float, float]):
        """Update ghost AI."""
        if self.eaten:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.eaten = False
                self.x = self.home_x
                self.y = self.home_y
            return
        
        # Update scared timer
        if self.scared_timer > 0:
            self.scared_timer -= dt
            if self.scared_timer <= 0:
                self.scared = False
        
        # Simple AI: move towards player when not scared, away when scared
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        
        if self.scared:
            dx = -dx  # Run away from player
            self.speed = 0.04
        else:
            self.speed = 0.08
        
        # Choose direction based on personality
        if self.personality == "aggressive":
            # Direct chase
            if abs(dx) > abs(dy):
                self.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
            else:
                self.direction = Direction.DOWN if dy > 0 else Direction.UP
        elif self.personality == "ambusher":
            # Try to cut off player
            target_ahead_x = player_pos[0] + (1 if dx > 0 else -1) * 3
            target_ahead_y = player_pos[1]
            dx_ahead = target_ahead_x - self.x
            dy_ahead = target_ahead_y - self.y
            if abs(dx_ahead) > abs(dy_ahead):
                self.direction = Direction.RIGHT if dx_ahead > 0 else Direction.LEFT
            else:
                self.direction = Direction.DOWN if dy_ahead > 0 else Direction.UP
        else:
            # Random movement
            if random.random() < 0.1:  # 10% chance to change direction
                self.direction = random.choice(list(Direction)[:-1])
        
        # Move
        new_x = self.x + self.direction.value[0] * self.speed * dt * 10
        new_y = self.y + self.direction.value[1] * self.speed * dt * 10
        
        # Check collision with walls
        grid_x = int(new_x)
        grid_y = int(new_y)
        
        if (0 <= grid_x < len(maze[0]) and 0 <= grid_y < len(maze) and
            maze[grid_y][grid_x] != CellType.WALL):
            self.x = new_x
            self.y = new_y

class PacManGame(BaseGame):
    """Retro Pac-Man style game implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "Pac-Man Retro"
        self.description = "Classic maze navigation with dots and ghosts"
        self.genre = "Arcade"
        self.author = "CLI Games Team"
        self.version = "1.0.0"
        self.controls = {
            "Arrow Keys": "Move Pac-Man",
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
        self.width = 31
        self.height = 21
        self.maze = []
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_direction = Direction.NONE
        self.next_direction = Direction.NONE
        self.ghosts = []
        self.dots_collected = set()
        self.total_dots = 0
        self.power_pellets = set()
        self.power_timer = 0
        self.lives = 3
        self.score = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.animation_frame = 0
        self.animation_timer = 0
        
        # Timing
        self.last_update = 0
        self.start_time = 0
        
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
            dt = current_time - clock
            clock = current_time
            
            # Handle input
            self._handle_game_input(screen)
            
            # Update game state
            if not self.paused:
                self._update(dt)
            
            # Render
            self._render(screen)
            
            # Small delay
            time.sleep(0.016)  # ~60 FPS
        
        self.cleanup_screen(screen)
        return self.score
    
    def _initialize_game(self, mode, **kwargs):
        """Initialize game state."""
        self.game_over = False
        self.paused = False
        self.score = 0
        self.level = 1
        self.lives = 3
        self.current_mode = mode
        self.start_time = time.time()
        
        # Mode-specific settings
        if mode == GameMode.TIME_ATTACK:
            self.time_limit = 300  # 5 minutes
        elif mode == GameMode.SPEEDRUN:
            self.time_limit = 240  # 4 minutes
            self.ghost_speed_multiplier = 1.5
        else:
            self.ghost_speed_multiplier = 1.0
        
        # Create maze
        self._create_maze()
        
        # Spawn Pac-Man
        self._spawn_pacman()
        
        # Spawn ghosts
        self._spawn_ghosts()
        
        # Initialize counters
        self._count_maze_items()
    
    def _create_maze(self):
        """Create the classic Pac-Man maze layout."""
        # Basic maze template (simplified version of classic layout)
        maze_template = [
            "───────────────────────────────",
            "│............│....│........│",
            "│.──.│──.│.──.│.──.│──.│",
            "│o..│.o..│o..│.o..│.o..│.o│",
            "│.──.└──.└──.└──.└──.──.│",
            "│...........................│",
            "│.──.───┐...┌───.──.──.│",
            "│o..│....o│...│....│.o..│.o│",
            "│.──.└──.│.──.└──.└──.──.│",
            "│........│..............│",
            "└──────.┴────.┬──────.┘",
            "        │.......│        ",
            "        │.──.──.│        ",
            "        │.o....o│        ",
            "        │.─────.│        ",
            "        │.......│        ",
            "───────────────────────"
        ]
        
        self.maze = []
        for y, row in enumerate(maze_template):
            maze_row = []
            for x, char in enumerate(row):
                if char == '│':
                    maze_row.append(CellType.WALL)
                elif char == '─':
                    maze_row.append(CellType.WALL)
                elif char == '└' or char == '┘' or char == '┐' or char == '┌':
                    maze_row.append(CellType.WALL)
                elif char == '┴' or char == '┬' or char == '├' or char == '┤':
                    maze_row.append(CellType.WALL)
                elif char == '.':
                    maze_row.append(CellType.DOT)
                elif char == 'o':
                    maze_row.append(CellType.POWER_PELLET)
                elif char == ' ':
                    maze_row.append(CellType.EMPTY)
                else:
                    maze_row.append(CellType.EMPTY)
            self.maze.append(maze_row)
        
        # Set spawn points
        self.maze[15][15] = CellType.PACMAN_SPAWN
        self.maze[9][13] = CellType.GHOST_SPAWN
        self.maze[9][17] = CellType.GHOST_SPAWN
        self.maze[11][15] = CellType.GHOST_SPAWN
        self.maze[11][17] = CellType.GHOST_SPAWN
    
    def _spawn_pacman(self):
        """Spawn Pac-Man at the starting position."""
        for y in range(len(self.maze)):
            for x in range(len(self.maze[y])):
                if self.maze[y][x] == CellType.PACMAN_SPAWN:
                    self.player_x = x + 0.5
                    self.player_y = y + 0.5
                    self.player_direction = Direction.NONE
                    self.next_direction = Direction.NONE
                    return
    
    def _spawn_ghosts(self):
        """Spawn ghosts at their starting positions."""
        self.ghosts.clear()
        ghost_colors = ['red', 'pink', 'cyan', 'orange']
        ghost_personalities = ['aggressive', 'ambusher', 'random', 'random']
        spawn_points = []
        
        for y in range(len(self.maze)):
            for x in range(len(self.maze[y])):
                if self.maze[y][x] == CellType.GHOST_SPAWN:
                    spawn_points.append((x, y))
        
        # Create ghosts at spawn points
        for i in range(min(4, len(spawn_points))):
            x, y = spawn_points[i]
            ghost = Ghost(
                x + 0.5, y + 0.5,
                ghost_colors[i % len(ghost_colors)],
                ghost_personalities[i % len(ghost_personalities)]
            )
            
            # Apply speed multiplier for speedrun mode
            ghost.speed *= self.ghost_speed_multiplier
            self.ghosts.append(ghost)
    
    def _count_maze_items(self):
        """Count total dots and power pellets."""
        self.total_dots = 0
        self.power_pellets.clear()
        self.dots_collected.clear()
        
        for y in range(len(self.maze)):
            for x in range(len(self.maze[y])):
                if self.maze[y][x] == CellType.DOT:
                    self.total_dots += 1
                elif self.maze[y][x] == CellType.POWER_PELLET:
                    self.total_dots += 1
                    self.power_pellets.add((x, y))
    
    def _handle_game_input(self, screen):
        """Handle keyboard input."""
        key = screen.getch()
        
        if key == 27:  # ESC
            self.running = False
            return
        elif key in [ord('p'), ord('P')]:
            self.paused = not self.paused
            return
        
        if self.paused or self.game_over:
            return
        
        # Movement input
        if key in [curses.KEY_UP, ord('w'), ord('W')]:
            self.next_direction = Direction.UP
        elif key in [curses.KEY_DOWN, ord('s'), ord('S')]:
            self.next_direction = Direction.DOWN
        elif key in [curses.KEY_LEFT, ord('a'), ord('A')]:
            self.next_direction = Direction.LEFT
        elif key in [curses.KEY_RIGHT, ord('d'), ord('D')]:
            self.next_direction = Direction.RIGHT
    
    def _update(self, dt: float):
        """Update game state."""
        # Check time limit for timed modes
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                self.game_over = True
                return
        
        # Update animation
        self.animation_timer += dt
        if self.animation_timer > 0.1:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
        
        # Update power timer
        if self.power_timer > 0:
            self.power_timer -= dt
            
            # When power wears off, unscare ghosts
            if self.power_timer <= 0:
                for ghost in self.ghosts:
                    ghost.scared = False
                    ghost.speed *= 2  # Return to normal speed
        
        # Try to change direction
        self._try_change_direction()
        
        # Move player
        self._move_player(dt)
        
        # Collect dots and power pellets
        self._collect_items()
        
        # Update ghosts
        for ghost in self.ghosts:
            ghost.update(dt, self.maze, (self.player_x, self.player_y))
        
        # Check ghost collisions
        self._check_ghost_collisions()
        
        # Check level completion
        if len(self.dots_collected) >= self.total_dots:
            self._next_level()
    
    def _try_change_direction(self):
        """Try to change player direction."""
        if self.next_direction == Direction.NONE:
            return
        
        # Calculate new position
        dx, dy = self.next_direction.value
        new_x = self.player_x + dx * 0.5
        new_y = self.player_y + dy * 0.5
        
        # Check if can move
        grid_x = int(new_x)
        grid_y = int(new_y)
        
        if (0 <= grid_x < len(self.maze[0]) and 0 <= grid_y < len(self.maze) and
            self.maze[grid_y][grid_x] != CellType.WALL):
            self.player_direction = self.next_direction
            self.next_direction = Direction.NONE
    
    def _move_player(self, dt: float):
        """Move the player."""
        if self.player_direction == Direction.NONE:
            return
        
        dx, dy = self.player_direction.value
        speed = 0.15 * dt * 10  # Pac-Man speed
        
        new_x = self.player_x + dx * speed
        new_y = self.player_y + dy * speed
        
        # Wrap around tunnel
        if new_x < 0:
            new_x = len(self.maze[0]) - 1
        elif new_x >= len(self.maze[0]):
            new_x = 0
        
        # Check collision with walls
        grid_x = int(new_x)
        grid_y = int(new_y)
        
        if (0 <= grid_x < len(self.maze[0]) and 0 <= grid_y < len(self.maze) and
            self.maze[grid_y][grid_x] != CellType.WALL):
            self.player_x = new_x
            self.player_y = new_y
    
    def _collect_items(self):
        """Collect dots and power pellets."""
        grid_x = int(self.player_x)
        grid_y = int(self.player_y)
        
        if (0 <= grid_x < len(self.maze[0]) and 0 <= grid_y < len(self.maze)):
            cell = self.maze[grid_y][grid_x]
            pos = (grid_x, grid_y)
            
            if cell == CellType.DOT and pos not in self.dots_collected:
                self.dots_collected.add(pos)
                self.score += 10
                self.maze[grid_y][grid_x] = CellType.EMPTY
                
            elif cell == CellType.POWER_PELLET and pos not in self.dots_collected:
                self.dots_collected.add(pos)
                self.score += 50
                self.maze[grid_y][grid_x] = CellType.EMPTY
                self.power_timer = 8.0  # 8 seconds of power
                
                # Make ghosts scared
                for ghost in self.ghosts:
                    ghost.scared = True
                    ghost.scared_timer = 8.0
                    ghost.speed /= 2  # Half speed when scared
    
    def _check_ghost_collisions(self):
        """Check collision with ghosts."""
        for ghost in self.ghosts:
            if ghost.eaten:
                continue
                
            distance = math.sqrt((self.player_x - ghost.x)**2 + (self.player_y - ghost.y)**2)
            
            if distance < 0.8:  # Collision threshold
                if ghost.scared:
                    # Eat ghost
                    ghost.eaten = True
                    ghost.respawn_timer = 5.0
                    self.score += 200
                    
                    # Create effect
                    # (Would add particles here)
                else:
                    # Lose a life
                    self.lives -= 1
                    
                    if self.lives <= 0:
                        self.game_over = True
                    else:
                        # Respawn
                        self._spawn_pacman()
                        self._spawn_ghosts()
    
    def _next_level(self):
        """Start next level."""
        self.level += 1
        self.score += 500  # Level completion bonus
        
        # Reset maze
        self._create_maze()
        self._spawn_pacman()
        self._spawn_ghosts()
        self._count_maze_items()
        
        # Increase ghost speed
        for ghost in self.ghosts:
            ghost.speed *= 1.1
    
    def _render(self, screen):
        """Render the game."""
        screen.clear()
        height, width = screen.getmaxyx()
        
        # Draw title
        title = f"PAC-MAN - Level {self.level}"
        screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Calculate game area position (centered)
        game_x = (width - self.width) // 2
        game_y = (height - self.height) // 2 + 1
        
        # Draw maze and game objects
        self._draw_maze(screen, game_x, game_y)
        
        # Draw UI
        self._draw_ui(screen, game_x, 2)
        
        # Draw pause overlay if paused
        if self.paused:
            self._draw_pause_overlay(screen)
        
        # Draw controls hint
        controls_text = "Arrow Keys/WASD: Move | P: Pause | ESC: Quit"
        screen.addstr(height - 1, (width - len(controls_text)) // 2, controls_text)
        
        screen.refresh()
    
    def _draw_maze(self, screen, x: int, y: int):
        """Draw the maze and game objects."""
        # Draw maze
        for my in range(len(self.maze)):
            for mx in range(len(self.maze[my])):
                cell = self.maze[my][mx]
                screen_y = y + my
                screen_x = x + mx
                
                if cell == CellType.WALL:
                    screen.addch(screen_y, screen_x, '█')
                elif cell == CellType.DOT and (mx, my) not in self.dots_collected:
                    screen.addch(screen_y, screen_x, '·')
                elif cell == CellType.POWER_PELLET and (mx, my) not in self.dots_collected:
                    screen.addch(screen_y, screen_x, '●', curses.A_BOLD)
        
        # Draw ghosts
        for ghost in self.ghosts:
            if not ghost.eaten:
                screen_y = y + int(ghost.y)
                screen_x = x + int(ghost.x)
                
                if ghost.scared:
                    # Blue when scared
                    screen.addch(screen_y, screen_x, '👻')
                else:
                    # Normal ghost colors (using different characters)
                    if ghost.color == 'red':
                        screen.addch(screen_y, screen_x, '👹')
                    elif ghost.color == 'pink':
                        screen.addch(screen_y, screen_x, '👺')
                    elif ghost.color == 'cyan':
                        screen.addch(screen_y, screen_x, '👻')
                    else:  # orange
                        screen.addch(screen_y, screen_x, '👾')
        
        # Draw Pac-Man
        pac_y = y + int(self.player_y)
        pac_x = x + int(self.player_x)
        
        if self.animation_frame == 0:
            pac_char = '😊'
        else:
            pac_char = '😮'
        
        screen.addch(pac_y, pac_x, pac_char, curses.A_BOLD)
    
    def _draw_ui(self, screen, x: int, y: int):
        """Draw UI elements."""
        # Score and stats
        ui_lines = [
            f"Score: {self.score}",
            f"Level: {self.level}",
            f"Lives: {'😊' * self.lives}",
            f"Dots: {len(self.dots_collected)}/{self.total_dots}"
        ]
        
        if self.power_timer > 0:
            ui_lines.append(f"POWER: {self.power_timer:.1f}s")
        
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            ui_lines.append(f"Time: {remaining:.1f}s")
        
        for i, line in enumerate(ui_lines):
            screen.addstr(y + i, x, line)
    
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
←/A - Move Left
→/D - Move Right
↑/W - Move Up
↓/S - Move Down
P - Pause/Resume
ESC - Quit Game

OBJECTIVE:
Navigate the maze and collect all dots while avoiding ghosts!

GAMEPLAY:
- Dots (·): 10 points
- Power Pellets (●): 50 points + 8 seconds of power
- When powered up: Eat ghosts for 200 points each
- Complete level for 500 bonus points

GHOSTS:
👹 Red - Aggressive (chases directly)
👺 Pink - Ambusher (tries to cut you off)
👻 Cyan - Random movement
👾 Orange - Random movement

GAME MODES:
Normal: Classic Pac-Man gameplay.
Time Attack: Score as much as possible in 5 minutes!
Speedrun: Complete levels quickly with faster ghosts.
Infinite: Endless gameplay with increasing difficulty.

SCORING:
Dot: 10 points
Power Pellet: 50 points
Ghost (powered): 200 points
Level Complete: 500 points
"""