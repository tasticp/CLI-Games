"""
Classic Tetris game implementation.
Stack falling blocks and clear lines to score points.
"""

import random
import curses
import time
from typing import List, Tuple, Optional
from enum import Enum

from plugins.base_game import BaseGame, GameMode

class TetrominoType(Enum):
    """Types of Tetris pieces."""
    I = ((1, 1, 1, 1),)  # Line
    O = ((1, 1), (1, 1))  # Square
    T = ((0, 1, 0), (1, 1, 1))  # T-shape
    S = ((0, 1, 1), (1, 1, 0))  # S-shape
    Z = ((1, 1, 0), (0, 1, 1))  # Z-shape
    J = ((1, 0, 0), (1, 1, 1))  # J-shape
    L = ((0, 0, 1), (1, 1, 1))  # L-shape

class Tetromino:
    """Represents a single Tetris piece."""
    
    def __init__(self, tetromino_type: TetrominoType, x: int, y: int):
        self.type = tetromino_type
        self.x = x
        self.y = y
        self.shape = tetromino_type.value
        self.rotation = 0
        
    def get_rotated_shape(self) -> Tuple[Tuple[int, ...], ...]:
        """Get the current rotation of the shape."""
        shape = self.shape
        rotations = [shape]
        
        # Generate all rotations
        current = shape
        for _ in range(3):
            # Rotate 90 degrees clockwise
            height = len(current)
            width = len(current[0])
            rotated = []
            
            for x in range(width):
                row = []
                for y in range(height - 1, -1, -1):
                    row.append(current[y][x])
                rotated.append(tuple(row))
            
            current = tuple(rotated)
            rotations.append(current)
        
        return rotations[self.rotation % len(rotations)]
    
    def get_width(self) -> int:
        """Get width of current rotation."""
        shape = self.get_rotated_shape()
        return len(shape[0]) if shape else 0
    
    def get_height(self) -> int:
        """Get height of current rotation."""
        shape = self.get_rotated_shape()
        return len(shape)
    
    def rotate(self):
        """Rotate the piece."""
        self.rotation += 1
    
    def get_blocks(self) -> List[Tuple[int, int]]:
        """Get all block positions for current rotation."""
        shape = self.get_rotated_shape()
        blocks = []
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    blocks.append((self.x + x, self.y + y))
        
        return blocks

class TetrisGame(BaseGame):
    """Classic Tetris game implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "Tetris Classic"
        self.description = "The classic block-stacking puzzle game"
        self.genre = "Puzzle"
        self.author = "CLI Games Team"
        self.version = "1.0.0"
        self.controls = {
            "Arrow Keys": "Move and rotate pieces",
            "Space": "Drop piece instantly",
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
        self.width = 10
        self.height = 20
        self.board = []
        self.current_piece = None
        self.next_piece_type = None
        self.game_over = False
        self.paused = False
        self.level = 1
        self.lines_cleared = 0
        self.score = 0
        self.drop_timer = 0
        self.drop_speed = 1.0
        self.last_update = 0
        
        # Controls
        self.drop_key_pressed = False
        
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
            
            # Update game state
            if not self.paused:
                self._update(current_time - clock)
                clock = current_time
            
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
        self.lines_cleared = 0
        self.current_mode = mode
        
        # Initialize board
        self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Mode-specific settings
        if mode == GameMode.TIME_ATTACK:
            self.time_limit = 300  # 5 minutes
            self.start_time = time.time()
        elif mode == GameMode.SPEEDRUN:
            self.drop_speed = 2.0  # Faster for speedrun
            self.time_limit = 180  # 3 minutes
            self.start_time = time.time()
        else:
            self.drop_speed = 1.0
        
        # Create first pieces
        self.next_piece_type = random.choice(list(TetrominoType))
        self._spawn_new_piece()
    
    def _spawn_new_piece(self):
        """Spawn a new piece at the top."""
        if not self.next_piece_type:
            self.next_piece_type = random.choice(list(TetrominoType))
        
        piece_type = self.next_piece_type
        self.next_piece_type = random.choice(list(TetrominoType))
        
        # Start position (top center)
        start_x = self.width // 2 - 1
        start_y = 0
        
        self.current_piece = Tetromino(piece_type, start_x, start_y)
        
        # Check if piece can be placed (game over condition)
        if self._check_collision(self.current_piece):
            self.game_over = True
    
    def _check_collision(self, piece: Tetromino, dx: int = 0, dy: int = 0) -> bool:
        """Check if piece would collide."""
        test_x = piece.x + dx
        test_y = piece.y + dy
        
        for x, y in piece.get_blocks():
            new_x = test_x + (x - piece.x)
            new_y = test_y + (y - piece.y)
            
            # Check boundaries
            if new_x < 0 or new_x >= self.width or new_y >= self.height:
                return True
            
            # Check board collision
            if new_y >= 0 and self.board[new_y][new_x]:
                return True
        
        return False
    
    def _lock_piece(self):
        """Lock current piece to the board."""
        if not self.current_piece:
            return
        
        # Add piece to board
        for x, y in self.current_piece.get_blocks():
            if 0 <= y < self.height and 0 <= x < self.width:
                self.board[y][x] = 1
        
        # Check for completed lines
        self._clear_lines()
        
        # Spawn new piece
        self._spawn_new_piece()
    
    def _clear_lines(self):
        """Clear completed lines and update score."""
        lines_cleared = 0
        
        y = self.height - 1
        while y >= 0:
            if all(self.board[y]):  # Line is full
                # Remove line
                del self.board[y]
                # Add empty line at top
                self.board.insert(0, [0 for _ in range(self.width)])
                lines_cleared += 1
            else:
                y -= 1
        
        # Update score based on lines cleared
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            line_scores = [0, 100, 300, 500, 800]  # 0, 1, 2, 3, 4 lines
            line_score = line_scores[min(lines_cleared, 4)] * self.level
            self.score += line_score
            
            # Level progression
            if self.lines_cleared >= self.level * 10:
                self.level += 1
                self.drop_speed = max(0.5, self.drop_speed - 0.1)  # Speed up
    
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
        
        # Piece controls
        if not self.current_piece:
            return
        
        if key in [curses.KEY_LEFT, ord('a'), ord('A')]:
            if not self._check_collision(self.current_piece, dx=-1):
                self.current_piece.x -= 1
        
        elif key in [curses.KEY_RIGHT, ord('d'), ord('D')]:
            if not self._check_collision(self.current_piece, dx=1):
                self.current_piece.x += 1
        
        elif key in [curses.KEY_DOWN, ord('s'), ord('S')]:
            if not self._check_collision(self.current_piece, dy=1):
                self.current_piece.y += 1
                self.score += 1  # Soft drop bonus
        
        elif key in [ord(' ')] and not self.drop_key_pressed:  # Space
            # Hard drop
            drop_distance = 0
            while not self._check_collision(self.current_piece, dy=1):
                self.current_piece.y += 1
                drop_distance += 1
            
            self.score += drop_distance * 2  # Hard drop bonus
            self.drop_key_pressed = True
        
        elif key in [curses.KEY_UP, ord('w'), ord('W')]:
            # Rotate
            self.current_piece.rotate()
            if self._check_collision(self.current_piece):
                # Try wall kicks
                if not self._check_collision(self.current_piece, dx=-1):
                    self.current_piece.x -= 1
                elif not self._check_collision(self.current_piece, dx=1):
                    self.current_piece.x += 1
                else:
                    # Can't rotate, revert
                    self.current_piece.rotation -= 1
        
        # Reset drop key
        if key not in [ord(' ')]:
            self.drop_key_pressed = False
    
    def _update(self, dt: float):
        """Update game state."""
        # Check time limit for timed modes
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                self.game_over = True
                return
        
        # Auto drop piece
        self.drop_timer += dt
        drop_interval = 1.0 / self.drop_speed
        
        if self.drop_timer >= drop_interval:
            self.drop_timer = 0
            
            if self.current_piece and not self.paused:
                if not self._check_collision(self.current_piece, dy=1):
                    self.current_piece.y += 1
                else:
                    self._lock_piece()
    
    def _render(self, screen):
        """Render the game."""
        screen.clear()
        height, width = screen.getmaxyx()
        
        # Draw title
        title = f"TETRIS - Level {self.level}"
        screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Calculate game area position (centered)
        game_width = self.width + 4  # Include borders
        game_height = self.height + 2  # Include borders
        game_x = (width - game_width) // 2
        game_y = (height - game_height) // 2
        
        # Draw game board
        self._draw_board(screen, game_x, game_y)
        
        # Draw UI
        self._draw_ui(screen, game_x + game_width + 2, game_y)
        
        # Draw pause overlay if paused
        if self.paused:
            self._draw_pause_overlay(screen)
        
        # Draw controls hint
        controls_text = "Arrow Keys/WASD: Move/Rotate | Space: Drop | P: Pause | ESC: Quit"
        screen.addstr(height - 1, (width - len(controls_text)) // 2, controls_text)
        
        screen.refresh()
    
    def _draw_board(self, screen, x: int, y: int):
        """Draw the game board."""
        # Draw border
        screen.addch(y - 1, x - 1, '┌')
        screen.addch(y - 1, x + self.width, '┐')
        screen.addch(y + self.height, x - 1, '└')
        screen.addch(y + self.height, x + self.width, '┘')
        
        for i in range(self.width):
            screen.addch(y - 1, x + i, '─')
            screen.addch(y + self.height, x + i, '─')
        
        for i in range(self.height):
            screen.addch(y + i, x - 1, '│')
            screen.addch(y + i, x + self.width, '│')
        
        # Draw board content
        for py in range(self.height):
            for px in range(self.width):
                board_val = self.board[py][px]
                if board_val:
                    screen.addch(y + py, x + px, '█', curses.color_pair(3) if curses.has_colors() else 0)
                else:
                    screen.addch(y + py, x + px, '·', curses.color_pair(2) if curses.has_colors() else 0)
        
        # Draw current piece
        if self.current_piece:
            for px, py in self.current_piece.get_blocks():
                if 0 <= py < self.height and 0 <= px < self.width:
                    screen.addch(y + py, x + px, '■', 
                               curses.color_pair(4) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        # Draw ghost piece (where piece will land)
        if self.current_piece:
            ghost_y = self.current_piece.y
            while not self._check_collision(self.current_piece, dy=ghost_y - self.current_piece.y + 1):
                ghost_y += 1
            
            for px, py in self.current_piece.get_blocks():
                ghost_px = px + (ghost_y - self.current_piece.y)
                if 0 <= py < self.height and 0 <= px < self.width:
                    screen.addch(y + ghost_py, x + ghost_px, '□', 
                               curses.color_pair(2) if curses.has_colors() else 0)
    
    def _draw_ui(self, screen, x: int, y: int):
        """Draw UI elements."""
        # Score and stats
        ui_lines = [
            f"Score: {self.score}",
            f"Level: {self.level}",
            f"Lines: {self.lines_cleared}",
            f"Speed: {self.drop_speed:.1f}x"
        ]
        
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            ui_lines.append(f"Time: {remaining:.1f}s")
        
        for i, line in enumerate(ui_lines):
            screen.addstr(y + i, x, line)
        
        # Next piece preview
        screen.addstr(y + len(ui_lines) + 2, x, "Next:", curses.A_BOLD)
        if self.next_piece_type:
            self._draw_tetromino_preview(screen, self.next_piece_type, x + 2, y + len(ui_lines) + 4)
    
    def _draw_tetromino_preview(self, screen, tetromino_type: TetrominoType, x: int, y: int):
        """Draw a small preview of a tetromino."""
        shape = tetromino_type.value
        
        for py, row in enumerate(shape):
            for px, cell in enumerate(row):
                if cell:
                    screen.addch(y + py, x + px, '█', curses.color_pair(4) if curses.has_colors() else 0)
    
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
↓/S - Soft Drop
↑/W - Rotate
Space - Hard Drop
P - Pause/Resume
ESC - Quit Game

OBJECTIVE:
Stack falling tetrominoes to create complete lines.
Clear lines to score points and increase level.

SCORING:
Soft Drop: +1 point per line
Hard Drop: +2 points per line
1 Line: 100 × level points
2 Lines: 300 × level points
3 Lines: 500 × level points
4 Lines (Tetris): 800 × level points

GAME MODES:
Normal: Classic Tetris gameplay.
Time Attack: Score as much as possible in 5 minutes!
Speedrun: Play as fast as possible with increased drop speed.
Infinite: Endless gameplay with level progression.
"""