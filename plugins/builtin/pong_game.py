"""
Classic Pong game implementation.
Two-player paddle game with a bouncing ball.
"""

import random
import curses
import time
import math
from typing import Optional, Tuple
from enum import Enum

from plugins.base_game import BaseGame, GameMode

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"

class Ball:
    """Represents the ball in Pong."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.dx = random.choice([-1, 1]) * 0.5  # Random initial direction
        self.dy = random.uniform(-0.3, 0.3)
        self.speed = 0.5
        self.radius = 1
        self.trail = []  # Ball trail for visual effect
        
    def update(self, dt: float):
        """Update ball position."""
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        
        # Add to trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 3:
            self.trail.pop(0)
    
    def reset(self, x: float, y: float):
        """Reset ball to center."""
        self.x = x
        self.y = y
        self.dx = random.choice([-1, 1]) * 0.5
        self.dy = random.uniform(-0.3, 0.3)
        self.trail.clear()
    
    def accelerate(self, factor: float = 1.1):
        """Increase ball speed."""
        self.speed = min(2.0, self.speed * factor)

class Paddle:
    """Represents a player's paddle."""
    
    def __init__(self, x: float, y: float, is_left: bool = True):
        self.x = x
        self.y = y
        self.width = 1
        self.height = 4
        self.speed = 1.0
        self.is_left = is_left
        self.score = 0
        self.ai_controlled = False
        
    def update(self, dt: float, ball: Optional[Ball] = None):
        """Update paddle position."""
        if self.ai_controlled and ball:
            # Simple AI: move towards ball's y position
            target_y = ball.y - self.height / 2
            diff = target_y - self.y
            
            if abs(diff) > 0.5:
                if diff > 0:
                    self.y += min(self.speed, diff)
                else:
                    self.y -= min(self.speed, abs(diff))
    
    def move_up(self, dt: float):
        """Move paddle up."""
        self.y = max(0, self.y - self.speed)
    
    def move_down(self, dt: float, max_y: float):
        """Move paddle down."""
        self.y = min(max_y - self.height, self.y + self.speed)
    
    def get_rect(self) -> Tuple[float, float, float, float]:
        """Get paddle rectangle (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

class PongGame(BaseGame):
    """Classic Pong game implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "Pong Classic"
        self.description = "The timeless two-player paddle game"
        self.genre = "Arcade"
        self.author = "CLI Games Team"
        self.version = "1.0.0"
        self.controls = {
            "Player 1": "W/S keys",
            "Player 2": "Arrow keys", 
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
        self.max_players = 2
        
        # Game state
        self.width = 40
        self.height = 20
        self.game_state = GameState.PLAYING
        self.paused = False
        self.game_over = False
        
        # Game objects
        self.left_paddle = None
        self.right_paddle = None
        self.ball = None
        self.max_score = 5  # First to 5 wins
        
        # Timing
        self.last_update = 0
        self.game_start_time = 0
        self.rally_count = 0
        self.longest_rally = 0
        
        # Effects
        self.particles = []
        self.flash_timer = 0
        
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
            if self.game_state == GameState.PLAYING and not self.paused:
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
        self.rally_count = 0
        self.longest_rally = 0
        self.current_mode = mode
        self.game_start_time = time.time()
        
        # Mode-specific settings
        if mode == GameMode.TIME_ATTACK:
            self.time_limit = 180  # 3 minutes
            self.start_time = time.time()
        elif mode == GameMode.SPEEDRUN:
            self.time_limit = 120  # 2 minutes
            self.start_time = time.time()
            self.max_score = 3  # Faster for speedrun
        else:
            self.max_score = 5
        
        # Create paddles
        self.left_paddle = Paddle(2, self.height // 2 - 2, True)
        self.right_paddle = Paddle(self.width - 3, self.height // 2 - 2, False)
        
        # Set up AI opponent for single player
        self.right_paddle.ai_controlled = True
        
        # Create ball
        self.ball = Ball(self.width / 2, self.height / 2)
        
        # Reset game state
        self.game_state = GameState.PLAYING
        self.particles.clear()
        self.flash_timer = 0
    
    def _handle_game_input(self, screen):
        """Handle keyboard input."""
        key = screen.getch()
        
        if key == 27:  # ESC
            self.running = False
            return
        elif key in [ord('p'), ord('P')]:
            if self.game_state == GameState.PLAYING:
                self.paused = not self.paused
            return
        
        if self.game_state != GameState.PLAYING or self.paused:
            return
        
        # Player 1 controls (W/S)
        if key in [ord('w'), ord('W')]:
            self.left_paddle.move_up(0.1)
        elif key in [ord('s'), ord('S')]:
            self.left_paddle.move_down(0.1, self.height)
        
        # Player 2 controls (Arrow keys) - if not AI
        if not self.right_paddle.ai_controlled:
            if key == curses.KEY_UP:
                self.right_paddle.move_up(0.1)
            elif key == curses.KEY_DOWN:
                self.right_paddle.move_down(0.1, self.height)
    
    def _update(self, dt: float):
        """Update game state."""
        # Check time limit for timed modes
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                self._end_game()
                return
        
        # Update paddles
        self.left_paddle.update(dt, self.ball)
        self.right_paddle.update(dt, self.ball)
        
        # Update ball
        self.ball.update(dt)
        
        # Check collisions
        self._check_paddle_collisions()
        self._check_wall_collisions()
        
        # Check scoring
        if self.ball.x < 0:
            self._score_point(self.right_paddle)
        elif self.ball.x > self.width:
            self._score_point(self.left_paddle)
        
        # Update particles
        self._update_particles(dt)
        
        # Update flash timer
        if self.flash_timer > 0:
            self.flash_timer -= dt
    
    def _check_paddle_collisions(self):
        """Check ball-paddle collisions."""
        ball_rect = (self.ball.x - self.ball.radius, 
                     self.ball.y - self.ball.radius,
                     self.ball.radius * 2, self.ball.radius * 2)
        
        # Check left paddle
        left_rect = self.left_paddle.get_rect()
        if self._rects_collide(ball_rect, left_rect):
            if self.ball.dx < 0:  # Moving towards paddle
                self.ball.x = left_rect[0] + left_rect[2] + self.ball.radius
                self.ball.dx = abs(self.ball.dx)
                
                # Add spin based on paddle hit position
                hit_pos = (self.ball.y - self.left_paddle.y) / self.left_paddle.height
                self.ball.dy = (hit_pos - 0.5) * 1.0
                
                # Create impact effect
                self._create_impact_effect(self.ball.x, self.ball.y)
                
                # Accelerate ball slightly
                self.ball.accelerate(1.02)
        
        # Check right paddle
        right_rect = self.right_paddle.get_rect()
        if self._rects_collide(ball_rect, right_rect):
            if self.ball.dx > 0:  # Moving towards paddle
                self.ball.x = right_rect[0] - self.ball.radius
                self.ball.dx = -abs(self.ball.dx)
                
                # Add spin based on paddle hit position
                hit_pos = (self.ball.y - self.right_paddle.y) / self.right_paddle.height
                self.ball.dy = (hit_pos - 0.5) * 1.0
                
                # Create impact effect
                self._create_impact_effect(self.ball.x, self.ball.y)
                
                # Accelerate ball slightly
                self.ball.accelerate(1.02)
    
    def _check_wall_collisions(self):
        """Check ball-wall collisions."""
        # Top and bottom walls
        if self.ball.y - self.ball.radius <= 0:
            self.ball.y = self.ball.radius
            self.ball.dy = abs(self.ball.dy)
            self._create_impact_effect(self.ball.x, 0)
        elif self.ball.y + self.ball.radius >= self.height:
            self.ball.y = self.height - self.ball.radius
            self.ball.dy = -abs(self.ball.dy)
            self._create_impact_effect(self.ball.x, self.height)
    
    def _rects_collide(self, rect1: Tuple, rect2: Tuple) -> bool:
        """Check if two rectangles collide."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)
    
    def _create_impact_effect(self, x: float, y: float):
        """Create particle effect for ball impact."""
        for _ in range(5):
            dx = random.uniform(-2, 2)
            dy = random.uniform(-2, 2)
            self.particles.append({
                'x': x, 'y': y, 'dx': dx, 'dy': dy,
                'lifetime': 0.5, 'char': random.choice(['*', '+', '·'])
            })
    
    def _update_particles(self, dt: float):
        """Update particle effects."""
        surviving_particles = []
        
        for particle in self.particles:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['lifetime'] -= dt
            particle['dy'] += 5 * dt  # Gravity
            
            if particle['lifetime'] > 0:
                surviving_particles.append(particle)
        
        self.particles = surviving_particles
    
    def _score_point(self, paddle: Paddle):
        """Handle scoring a point."""
        paddle.score += 1
        self.rally_count = 0
        
        # Create celebration effect
        for _ in range(10):
            dx = random.uniform(-3, 3)
            dy = random.uniform(-3, 3)
            self.particles.append({
                'x': self.width / 2, 'y': self.height / 2,
                'dx': dx, 'dy': dy, 'lifetime': 1.0,
                'char': random.choice(['★', '✦', '✧'])
            })
        
        # Check for game over
        if paddle.score >= self.max_score:
            self._end_game()
        else:
            # Reset ball
            self.ball.reset(self.width / 2, self.height / 2)
            self.flash_timer = 0.5
    
    def _end_game(self):
        """End the game."""
        self.game_over = True
        self.game_state = GameState.GAME_OVER
        
        # Calculate score
        winner_score = max(self.left_paddle.score, self.right_paddle.score)
        self.score = winner_score * 100
        
        # Bonus for winning fast (speedrun mode)
        if self.current_mode == GameMode.SPEEDRUN:
            elapsed = time.time() - self.game_start_time
            if elapsed < 60:  # Under 1 minute
                self.score += 500
        
        # Bonus for rallies
        self.score += self.longest_rally * 10
    
    def _render(self, screen):
        """Render the game."""
        screen.clear()
        height, width = screen.getmaxyx()
        
        # Draw title
        title = f"PONG - {self.left_paddle.score} vs {self.right_paddle.score}"
        screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Calculate game area position (centered)
        game_width = self.width + 2
        game_height = self.height + 2
        game_x = (width - game_width) // 2
        game_y = (height - game_height) // 2 + 2
        
        # Draw game area
        self._draw_game_area(screen, game_x, game_y)
        
        # Draw game objects
        self._draw_game_objects(screen, game_x, game_y)
        
        # Draw UI
        self._draw_ui(screen, game_x, 2)
        
        # Draw pause overlay if paused
        if self.paused:
            self._draw_pause_overlay(screen)
        
        # Draw controls hint
        controls_text = "P1: W/S | P2: ↑/↓ | P: Pause | ESC: Quit"
        screen.addstr(height - 1, (width - len(controls_text)) // 2, controls_text)
        
        screen.refresh()
    
    def _draw_game_area(self, screen, x: int, y: int):
        """Draw the game area border."""
        # Flash effect on score
        if self.flash_timer > 0:
            border_char = '█'
            attr = curses.A_REVERSE
        else:
            border_char = '│'
            attr = 0
        
        # Draw borders
        for i in range(self.height):
            screen.addch(y + i, x, border_char, attr)
            screen.addch(y + i, x + self.width + 1, border_char, attr)
        
        # Draw center line
        for i in range(0, self.height, 2):
            screen.addch(y + i, x + self.width // 2, '│')
        
        # Draw corners
        screen.addch(y - 1, x - 1, '┌')
        screen.addch(y - 1, x + self.width + 2, '┐')
        screen.addch(y + self.height, x - 1, '└')
        screen.addch(y + self.height, x + self.width + 2, '┘')
        
        for i in range(self.width + 2):
            screen.addch(y - 1, x + i, '─')
            screen.addch(y + self.height, x + i, '─')
    
    def _draw_game_objects(self, screen, x: int, y: int):
        """Draw paddles, ball, and effects."""
        # Draw ball trail
        for tx, ty in self.ball.trail:
            if 0 <= int(ty) < self.height and 0 <= int(tx) < self.width:
                screen.addch(y + int(ty), x + int(tx), '·', 
                           curses.color_pair(2) if curses.has_colors() else 0)
        
        # Draw paddles
        left_x, left_y, left_w, left_h = self.left_paddle.get_rect()
        for i in range(int(left_h)):
            screen.addch(y + int(left_y + i), x + int(left_x), '█',
                       curses.color_pair(3) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        right_x, right_y, right_w, right_h = self.right_paddle.get_rect()
        for i in range(int(right_h)):
            screen.addch(y + int(right_y + i), x + int(right_x), '█',
                       curses.color_pair(3) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        # Draw ball
        ball_x = int(self.ball.x)
        ball_y = int(self.ball.y)
        if 0 <= ball_y < self.height and 0 <= ball_x < self.width:
            screen.addch(y + ball_y, x + ball_x, '●',
                       curses.color_pair(4) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        # Draw particles
        for particle in self.particles:
            px = int(particle['x'])
            py = int(particle['y'])
            if 0 <= py < self.height and 0 <= px < self.width:
                screen.addch(y + py, x + px, particle['char'])
    
    def _draw_ui(self, screen, x: int, y: int):
        """Draw UI elements."""
        # Game info
        info_lines = [
            f"First to {self.max_score} wins",
            f"Rally: {self.rally_count}",
            f"Best Rally: {self.longest_rally}",
            f"Ball Speed: {self.ball.speed:.1f}x"
        ]
        
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            info_lines.append(f"Time: {remaining:.1f}s")
        
        # Mode info
        mode_name = self.current_mode.value.replace('_', ' ').title()
        info_lines.append(f"Mode: {mode_name}")
        
        for i, line in enumerate(info_lines):
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
Player 1:
W - Move Up
S - Move Down

Player 2:
↑ - Move Up
↓ - Move Down

P - Pause/Resume
ESC - Quit Game

OBJECTIVE:
Hit the ball past your opponent's paddle to score.
First to reach the target score wins!

GAMEPLAY:
- Ball speeds up with each paddle hit
- Hit position affects ball angle
- Rally counter tracks consecutive hits

GAME MODES:
Normal: First to 5 points wins.
Time Attack: Score as many points as possible in 3 minutes!
Speedrun: First to 3 points wins, with time bonus.
Infinite: Play with extended scoring targets.

SCORING:
- Point: 100 points (base score)
- Rally Bonus: 10 points per hit in longest rally
- Speedrun Bonus: 500 points for winning under 1 minute
"""