"""
Retro Mario-style platformer game.
Jump, run, and collect coins while avoiding enemies.
"""

import random
import curses
import time
import math
from typing import List, Optional, Tuple
from enum import Enum

from plugins.base_game import BaseGame, GameMode

class CellType(Enum):
    """Types of level cells."""
    EMPTY = 0
    GROUND = 1
    BRICK = 2
    QUESTION_BLOCK = 3
    COIN = 4
    ENEMY = 5
    FLAG = 6
    PIPE = 7

class Direction(Enum):
    LEFT = -1
    RIGHT = 1
    NONE = 0

class Player:
    """Represents the player character."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.width = 1
        self.height = 1
        self.on_ground = False
        self.jumping = False
        self.facing_right = True
        self.coins = 0
        self.lives = 3
        
    def jump(self):
        """Make the player jump."""
        if self.on_ground and not self.jumping:
            self.vy = -0.8  # Jump velocity
            self.jumping = True
            self.on_ground = False
    
    def move_left(self, dt: float):
        """Move player left."""
        self.vx = -0.3
        self.facing_right = False
    
    def move_right(self, dt: float):
        """Move player right."""
        self.vx = 0.3
        self.facing_right = True
    
    def stop_horizontal(self):
        """Stop horizontal movement."""
        self.vx = 0
    
    def update(self, dt: float, gravity: float = 2.0):
        """Update player physics."""
        # Apply gravity
        if not self.on_ground:
            self.vy += gravity * dt
        
        # Update position
        self.x += self.vx * dt * 10
        self.y += self.vy * dt * 10
        
        # Apply friction
        if self.on_ground:
            self.vx *= 0.8
        
        # Landing
        if self.vy > 0 and self.on_ground:
            self.vy = 0
            self.jumping = False

class Enemy:
    """Represents an enemy."""
    
    def __init__(self, x: float, y: float, enemy_type: str = "goomba"):
        self.x = x
        self.y = y
        self.vx = -0.1  # Slow movement
        self.vy = 0
        self.width = 1
        self.height = 1
        self.type = enemy_type
        self.alive = True
        self.patrol_center = x
        self.patrol_range = 3
        
    def update(self, dt: float):
        """Update enemy AI."""
        if not self.alive:
            return
        
        # Simple patrol movement
        self.x += self.vx * dt * 10
        
        # Reverse direction at patrol limits
        if abs(self.x - self.patrol_center) > self.patrol_range:
            self.vx = -self.vx
    
    def defeat(self):
        """Defeat the enemy."""
        self.alive = False

class MarioGame(BaseGame):
    """Retro Mario-style platformer game."""
    
    def __init__(self):
        super().__init__()
        self.name = "Mario Platformer"
        self.description = "Jump through levels in this retro platformer"
        self.genre = "Platformer"
        self.author = "CLI Games Team"
        self.version = "1.0.0"
        self.controls = {
            "Arrow Keys": "Move and jump",
            "A/D": "Alternative movement",
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
        self.width = 40
        self.height = 20
        self.level = []
        self.player = None
        self.enemies = []
        self.coins = []
        self.particles = []
        self.camera_x = 0
        self.level_width = 0
        self.level_complete = False
        self.game_over = False
        self.paused = False
        
        # Scoring
        self.score = 0
        self.time_bonus = 0
        self.start_time = 0
        
        # Physics
        self.gravity = 2.0
        
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
        self.level_complete = False
        self.current_mode = mode
        self.start_time = time.time()
        
        # Mode-specific settings
        if mode == GameMode.TIME_ATTACK:
            self.time_limit = 180  # 3 minutes
        elif mode == GameMode.SPEEDRUN:
            self.time_limit = 120  # 2 minutes
            self.gravity = 2.5  # Faster gravity
        else:
            self.time_limit = 0
        
        # Create first level
        self._create_level(1)
        
        # Spawn player
        self.player = Player(5, 10)
        
        # Initialize objects
        self.enemies.clear()
        self.coins.clear()
        self.particles.clear()
        self.camera_x = 0
    
    def _create_level(self, level_num: int):
        """Create a level layout."""
        self.level = []
        self.level_width = 80 + level_num * 20  # Longer levels
        
        # Initialize empty level
        for _ in range(self.height):
            self.level.append([CellType.EMPTY for _ in range(self.level_width)])
        
        # Create ground
        for x in range(self.level_width):
            for y in range(self.height - 3, self.height):
                self.level[y][x] = CellType.GROUND
        
        # Create platforms
        platform_y = self.height - 8
        for i in range(5 + level_num):
            start_x = 10 + i * 15
            length = random.randint(3, 6)
            
            for x in range(start_x, min(start_x + length, self.level_width)):
                if x < self.level_width:
                    self.level[platform_y][x] = CellType.BRICK
                    self.level[platform_y - 1][x] = CellType.QUESTION_BLOCK
        
        # Add some coins
        for i in range(10 + level_num * 5):
            x = random.randint(2, self.level_width - 3)
            y = random.randint(3, self.height - 5)
            
            if self.level[y][x] == CellType.EMPTY:
                self.level[y][x] = CellType.COIN
        
        # Add enemies
        enemy_count = min(level_num + 2, 8)
        for i in range(enemy_count):
            x = random.randint(10, self.level_width - 10)
            y = self.height - 4
            enemy = Enemy(x, y)
            self.enemies.append(enemy)
        
        # Add finish flag
        flag_x = self.level_width - 5
        flag_y = self.height - 4
        self.level[flag_y][flag_x] = CellType.FLAG
        
        # Add pipes at the end
        for y in range(self.height - 6, self.height - 2):
            self.level[y][self.level_width - 3] = CellType.PIPE
            self.level[y][self.level_width - 2] = CellType.PIPE
    
    def _handle_game_input(self, screen):
        """Handle keyboard input."""
        key = screen.getch()
        
        if key == 27:  # ESC
            self.running = False
            return
        elif key in [ord('p'), ord('P')]:
            self.paused = not self.paused
            return
        
        if self.paused or self.game_over or not self.player:
            return
        
        # Player controls
        if key in [curses.KEY_UP, ord('w'), ord('W'), ord(' ')]:
            self.player.jump()
        elif key in [curses.KEY_LEFT, ord('a'), ord('A')]:
            self.player.move_left(0.1)
        elif key in [curses.KEY_RIGHT, ord('d'), ord('D')]:
            self.player.move_right(0.1)
        else:
            self.player.stop_horizontal()
    
    def _update(self, dt: float):
        """Update game state."""
        # Check time limit for timed modes
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                self.game_over = True
                return
        
        # Update player
        if self.player:
            self.player.update(dt, self.gravity)
            self._check_player_collisions()
            
            # Update camera to follow player
            target_camera_x = max(0, self.player.x - self.width // 2)
            self.camera_x = target_camera_x
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(dt)
        
        # Update particles
        self._update_particles(dt)
        
        # Check level completion
        self._check_level_complete()
        
        # Check if player fell off screen
        if self.player and self.player.y > self.height + 5:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.game_over = True
            else:
                # Respawn player
                self.player.x = 5
                self.player.y = 10
                self.player.vx = 0
                self.player.vy = 0
    
    def _check_player_collisions(self):
        """Check player collisions with level and objects."""
        if not self.player:
            return
        
        px = int(self.player.x)
        py = int(self.player.y)
        
        # Check ground collision
        if py + 1 >= self.height or (0 <= py + 1 < len(self.level) and 
            0 <= px < len(self.level[py + 1]) and
            self.level[py + 1][px] in [CellType.GROUND, CellType.BRICK, CellType.QUESTION_BLOCK, CellType.PIPE]):
            if not self.player.on_ground:
                self.player.on_ground = True
        else:
            self.player.on_ground = False
        
        # Check block collisions
        if 0 <= py < len(self.level) and 0 <= px < len(self.level[py]):
            cell = self.level[py][px]
            
            if cell == CellType.COIN:
                self.player.coins += 1
                self.score += 100
                self.level[py][px] = CellType.EMPTY
                self._create_coin_effect(px, py)
            
            elif cell == CellType.QUESTION_BLOCK:
                # Power-up effect
                self.score += 200
                self.level[py][px] = CellType.BRICK
                self._create_powerup_effect(px, py)
            
            elif cell == CellType.FLAG:
                self.level_complete = True
        
        # Check enemy collisions
        player_rect = (self.player.x, self.player.y, self.player.width, self.player.height)
        
        for enemy in self.enemies[:]:
            if enemy.alive:
                enemy_rect = (enemy.x, enemy.y, enemy.width, enemy.height)
                
                if self._rects_collide(player_rect, enemy_rect):
                    if self.player.vy > 0:  # Falling on enemy
                        # Stomp enemy
                        enemy.defeat()
                        self.score += 100
                        self._create_stomp_effect(enemy.x, enemy.y)
                    else:
                        # Hit enemy from side
                        self.player.lives -= 1
                        if self.player.lives <= 0:
                            self.game_over = True
                        else:
                            # Respawn
                            self.player.x = 5
                            self.player.y = 10
    
    def _rects_collide(self, rect1: Tuple, rect2: Tuple) -> bool:
        """Check if two rectangles collide."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)
    
    def _create_coin_effect(self, x: int, y: int):
        """Create coin collection effect."""
        for _ in range(5):
            vx = random.uniform(-2, 2)
            vy = random.uniform(-3, -1)
            self.particles.append({
                'x': x, 'y': y, 'vx': vx, 'vy': vy,
                'lifetime': 0.8, 'char': '○'
            })
    
    def _create_powerup_effect(self, x: int, y: int):
        """Create power-up effect."""
        for _ in range(8):
            vx = random.uniform(-3, 3)
            vy = random.uniform(-2, 1)
            self.particles.append({
                'x': x, 'y': y, 'vx': vx, 'vy': vy,
                'lifetime': 1.0, 'char': '★'
            })
    
    def _create_stomp_effect(self, x: float, y: float):
        """Create enemy stomp effect."""
        for _ in range(6):
            vx = random.uniform(-1, 1)
            vy = random.uniform(-1, 1)
            self.particles.append({
                'x': x, 'y': y, 'vx': vx, 'vy': vy,
                'lifetime': 0.5, 'char': '·'
            })
    
    def _update_particles(self, dt: float):
        """Update particle effects."""
        surviving_particles = []
        
        for particle in self.particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['lifetime'] -= dt
            particle['vy'] += 5 * dt  # Gravity
            
            if particle['lifetime'] > 0:
                surviving_particles.append(particle)
        
        self.particles = surviving_particles
    
    def _check_level_complete(self):
        """Check if level is complete."""
        if self.level_complete and not self.game_over:
            # Calculate time bonus
            elapsed = time.time() - self.start_time
            self.time_bonus = max(0, 300 - int(elapsed)) * 10
            
            # Level complete bonus
            self.score += 1000 + self.time_bonus
            
            # Create celebration effect
            for _ in range(15):
                x = random.uniform(0, self.width)
                y = random.uniform(2, self.height // 2)
                self.particles.append({
                    'x': x, 'y': y, 'vx': random.uniform(-2, 2),
                    'vy': random.uniform(-3, -1), 'lifetime': 2.0,
                    'char': random.choice(['★', '✦', '✧'])
                })
    
    def _render(self, screen):
        """Render the game."""
        screen.clear()
        height, width = screen.getmaxyx()
        
        # Draw title
        title = f"MARIO PLATFORMER - Level {self.level}"
        screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Draw game area
        self._draw_level(screen, 0, 2)
        
        # Draw UI
        self._draw_ui(screen, 2, 2)
        
        # Draw pause overlay if paused
        if self.paused:
            self._draw_pause_overlay(screen)
        
        # Draw level complete overlay
        if self.level_complete:
            self._draw_level_complete_overlay(screen)
        
        # Draw controls hint
        controls_text = "Arrow Keys/WASD: Move | Space/Up: Jump | P: Pause | ESC: Quit"
        screen.addstr(height - 1, (width - len(controls_text)) // 2, controls_text)
        
        screen.refresh()
    
    def _draw_level(self, screen, start_x: int, start_y: int):
        """Draw the level with camera."""
        camera_start_x = int(self.camera_x)
        camera_end_x = camera_start_x + self.width
        
        # Draw visible portion of level
        for y in range(self.height):
            for x in range(self.width):
                level_x = camera_start_x + x
                level_y = y
                
                if (0 <= level_x < self.level_width and 0 <= level_y < len(self.level)):
                    cell = self.level[level_y][level_x]
                    screen_x = start_x + x
                    screen_y = start_y + y
                    
                    if cell == CellType.GROUND:
                        screen.addch(screen_y, screen_x, '▀', curses.color_pair(3) if curses.has_colors() else 0)
                    elif cell == CellType.BRICK:
                        screen.addch(screen_y, screen_x, '▒', curses.color_pair(2) if curses.has_colors() else 0)
                    elif cell == CellType.QUESTION_BLOCK:
                        screen.addch(screen_y, screen_x, '?', curses.color_pair(4) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
                    elif cell == CellType.COIN:
                        screen.addch(screen_y, screen_x, '○', curses.color_pair(5) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
                    elif cell == CellType.PIPE:
                        screen.addch(screen_y, screen_x, '│', curses.color_pair(2) if curses.has_colors() else 0)
                    elif cell == CellType.FLAG:
                        screen.addch(screen_y, screen_x, '🚩', curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
                    # Player will be drawn separately
        
        # Draw player
        if self.player:
            player_screen_x = int(self.player.x - self.camera_x)
            player_screen_y = int(self.player.y)
            
            if 0 <= player_screen_x < self.width:
                player_char = '>' if self.player.facing_right else '<'
                screen.addch(start_y + player_screen_y, start_x + player_screen_x,
                           player_char, curses.color_pair(6) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        # Draw enemies
        for enemy in self.enemies:
            if enemy.alive:
                enemy_screen_x = int(enemy.x - self.camera_x)
                enemy_screen_y = int(enemy.y)
                
                if 0 <= enemy_screen_x < self.width:
                    screen.addch(start_y + enemy_screen_y, start_x + enemy_screen_x, '👾')
        
        # Draw particles
        for particle in self.particles:
            particle_screen_x = int(particle['x'] - self.camera_x)
            particle_screen_y = int(particle['y'])
            
            if 0 <= particle_screen_x < self.width:
                screen.addch(start_y + particle_screen_y, start_x + particle_screen_x, particle['char'])
    
    def _draw_ui(self, screen, x: int, y: int):
        """Draw UI elements."""
        ui_lines = [
            f"Score: {self.score}",
            f"Coins: {self.player.coins if self.player else 0}",
            f"Lives: {'❤️' * (self.player.lives if self.player else 0)}",
            f"Camera: {int(self.camera_x)}"
        ]
        
        if self.time_bonus > 0:
            ui_lines.append(f"Time Bonus: +{self.time_bonus}")
        
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
    
    def _draw_level_complete_overlay(self, screen):
        """Draw level complete overlay."""
        height, width = screen.getmaxyx()
        
        complete_text = [
            "╔" + "═" * 24 + "╗",
            "║" + " " * 24 + "║",
            "║" + "   LEVEL COMPLETE!   " + "║",
            "║" + " " * 24 + "║",
            "║" + f"  Score: {self.score}   " + "║",
            "║" + f"  Time Bonus: +{self.time_bonus}   " + "║",
            "║" + " " * 24 + "║",
            "║" + "  Press any key   " + "║",
            "║" + "   to continue      " + "║",
            "║" + " " * 24 + "║",
            "╚" + "═" * 24 + "╝"
        ]
        
        start_y = (height - len(complete_text)) // 2
        start_x = (width - 26) // 2
        
        for i, line in enumerate(complete_text):
            screen.addstr(start_y + i, start_x, line, curses.A_REVERSE)
    
    def get_controls_help(self) -> str:
        """Return help text for game controls."""
        return """
CONTROLS:
←/A - Move Left
→/D - Move Right
↑/W/Space - Jump
P - Pause/Resume
ESC - Quit Game

OBJECTIVE:
Reach the flag at the end of each level!
Avoid enemies and collect coins for points.

ITEMS:
○ Coin - 100 points
? Power-up Block - 200 points
🚩 Flag - Complete level (1000 + time bonus)

ENEMIES:
👾 Goomba - Defeat by jumping on them (100 points)
- Touching from side costs a life

GAMEPLAY:
- Time bonus: 10 points per second under 5 minutes
- Longer levels with more enemies
- Physics-based jumping and movement

GAME MODES:
Normal: Classic platformer gameplay.
Time Attack: Complete levels quickly for time bonus.
Speedrun: Faster gravity and 2-minute time limit.
Infinite: Play with extended level layouts.

SCORING:
Coin: 100 points
Enemy: 100 points
Power-up: 200 points
Level Complete: 1000 + time bonus
"""