"""
Classic Space Invaders game implementation.
Defend Earth from waves of alien invaders!
"""

import random
import curses
import time
import math
from typing import List, Optional, Tuple
from enum import Enum

from plugins.base_game import BaseGame, GameMode

class InvaderType(Enum):
    """Types of alien invaders."""
    BASIC = "basic"      # Worth 10 points
    MEDIUM = "medium"     # Worth 20 points  
    ELITE = "elite"       # Worth 30 points

class Direction(Enum):
    LEFT = -1
    RIGHT = 1

class Bullet:
    """Represents a bullet."""
    
    def __init__(self, x: float, y: float, dy: float, is_player: bool = True):
        self.x = x
        self.y = y
        self.dy = dy
        self.is_player = is_player
        self.active = True
    
    def update(self, dt: float):
        """Update bullet position."""
        self.y += self.dy * dt * 10
        
        # Deactivate if out of bounds
        if self.y < 0 or self.y > 30:
            self.active = False

class Invader:
    """Represents an alien invader."""
    
    def __init__(self, x: float, y: float, invader_type: InvaderType):
        self.x = x
        self.y = y
        self.type = invader_type
        self.animation_frame = 0
        self.animation_timer = 0
        self.shoot_cooldown = 0
        
        # Set properties based on type
        if invader_type == InvaderType.BASIC:
            self.char = '👾'
            self.points = 10
            self.health = 1
        elif invader_type == InvaderType.MEDIUM:
            self.char = '👽'
            self.points = 20
            self.health = 2
        else:  # ELITE
            self.char = '🛸'
            self.points = 30
            self.health = 3
    
    def update(self, dt: float, shoot_chance: float):
        """Update invader."""
        # Update animation
        self.animation_timer += dt
        if self.animation_timer > 0.5:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
        
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        
        # Randomly shoot
        if self.shoot_cooldown <= 0 and random.random() < shoot_chance:
            self.shoot_cooldown = 2.0  # 2 second cooldown
            return Bullet(self.x, self.y + 1, 1, is_player=False)
        
        return None
    
    def get_display_char(self) -> str:
        """Get current display character."""
        if self.animation_frame == 0:
            return self.char
        else:
            # Alternate character for animation
            if self.type == InvaderType.BASIC:
                return '👾'
            elif self.type == InvaderType.MEDIUM:
                return '👽'
            else:
                return '🛸'

class PlayerShip:
    """Represents the player's ship."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.health = 3
        self.shoot_cooldown = 0
        self.speed = 0.5
    
    def update(self, dt: float):
        """Update player ship."""
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
    
    def move_left(self, dt: float, max_x: float):
        """Move ship left."""
        self.x = max(1, self.x - self.speed * dt * 10)
    
    def move_right(self, dt: float, max_x: float):
        """Move ship right."""
        self.x = min(max_x - 1, self.x + self.speed * dt * 10)
    
    def can_shoot(self) -> bool:
        """Check if player can shoot."""
        return self.shoot_cooldown <= 0
    
    def shoot(self) -> Bullet:
        """Shoot a bullet."""
        if self.can_shoot():
            self.shoot_cooldown = 0.3  # Rapid fire
            return Bullet(self.x, self.y - 1, -1, is_player=True)
        return None

class Particle:
    """Represents a visual effect."""
    
    def __init__(self, x: float, y: float, dx: float, dy: float, 
                 char: str, lifetime: float, color: Optional[int] = None):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.char = char
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
    
    def update(self, dt: float) -> bool:
        """Update particle. Returns False if expired."""
        self.x += self.dx * dt
        self.y += self.dy * dt
        self.lifetime -= dt
        
        # Apply gravity to some particles
        if self.char in ['*', '·']:
            self.dy += 50 * dt
        
        return self.lifetime > 0

class SpaceInvadersGame(BaseGame):
    """Classic Space Invaders game implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "Space Invaders"
        self.description = "Defend Earth from waves of alien invaders"
        self.genre = "Shooter"
        self.author = "CLI Games Team"
        self.version = "1.0.0"
        self.controls = {
            "Arrow Keys": "Move ship left/right",
            "Space": "Fire weapons",
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
        self.height = 25
        self.paused = False
        self.game_over = False
        
        # Game objects
        self.player_ship = None
        self.invaders: List[Invader] = []
        self.bullets: List[Bullet] = []
        self.particles: List[Particle] = []
        self.barriers: List[List[bool]] = []  # Barrier protection
        
        # Game state
        self.wave = 1
        self.invader_direction = Direction.RIGHT
        self.invader_drop_timer = 0
        self.wave_clear = False
        self.wave_clear_timer = 0
        
        # Scoring
        self.score = 0
        self.high_score = 0
        self.lives = 3
        
        # Timing
        self.last_update = 0
        self.game_start_time = 0
        
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
        self.wave = 1
        self.lives = 3
        self.current_mode = mode
        self.game_start_time = time.time()
        
        # Mode-specific settings
        if mode == GameMode.TIME_ATTACK:
            self.time_limit = 300  # 5 minutes
            self.start_time = time.time()
        elif mode == GameMode.SPEEDRUN:
            self.wave_bonus_multiplier = 2.0  # Double points for waves
            self.time_limit = 240  # 4 minutes
            self.start_time = time.time()
        else:
            self.wave_bonus_multiplier = 1.0
        
        # Create player ship
        self.player_ship = PlayerShip(self.width // 2, self.height - 3)
        
        # Initialize game objects
        self.invaders.clear()
        self.bullets.clear()
        self.particles.clear()
        
        # Create barriers
        self._create_barriers()
        
        # Spawn first wave
        self._spawn_wave(self.wave)
    
    def _create_barriers(self):
        """Create protective barriers."""
        self.barriers.clear()
        barrier_count = 4
        barrier_width = 5
        barrier_height = 3
        
        # Create empty barrier grid
        for _ in range(barrier_count):
            self.barriers.append([[False for _ in range(barrier_width)] 
                             for _ in range(barrier_height)])
        
        # Position barriers
        barrier_spacing = (self.width - barrier_count * barrier_width) // (barrier_count + 1)
        
        for i in range(barrier_count):
            x = barrier_spacing + i * (barrier_width + barrier_spacing)
            y = self.height - 8
    
    def _spawn_wave(self, wave_number: int):
        """Spawn a wave of invaders."""
        self.invaders.clear()
        
        # Calculate wave composition
        base_rows = min(5, 2 + wave_number // 2)
        invaders_per_row = 8
        
        # Determine invader types based on wave
        for row in range(base_rows):
            if row == 0:  # Top row - elite
                invader_type = InvaderType.ELITE
            elif row <= 2:  # Middle rows - medium
                invader_type = InvaderType.MEDIUM
            else:  # Bottom rows - basic
                invader_type = InvaderType.BASIC
            
            for col in range(invaders_per_row):
                x = 6 + col * 3
                y = 3 + row * 2
                self.invaders.append(Invader(x, y, invader_type))
        
        self.wave_clear = False
        self.wave_clear_timer = 0
    
    def _handle_game_input(self, screen):
        """Handle keyboard input."""
        key = screen.getch()
        
        if key == 27:  # ESC
            self.running = False
            return
        elif key in [ord('p'), ord('P')]:
            self.paused = not self.paused
            return
        
        if self.paused or self.game_over or not self.player_ship:
            return
        
        # Player controls
        if key in [curses.KEY_LEFT, ord('a'), ord('A')]:
            self.player_ship.move_left(0.1, self.width)
        elif key in [curses.KEY_RIGHT, ord('d'), ord('D')]:
            self.player_ship.move_right(0.1, self.width)
        elif key in [ord(' '), curses.KEY_ENTER]:  # Space or Enter to shoot
            bullet = self.player_ship.shoot()
            if bullet:
                self.bullets.append(bullet)
    
    def _update(self, dt: float):
        """Update game state."""
        # Check time limit for timed modes
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                self.game_over = True
                return
        
        # Update player ship
        if self.player_ship:
            self.player_ship.update(dt)
        
        # Update invaders
        new_bullets = []
        shoot_chance = 0.001 + (self.wave - 1) * 0.0002  # Increase shooting with waves
        
        for invader in self.invaders:
            bullet = invader.update(dt, shoot_chance)
            if bullet:
                new_bullets.append(bullet)
        
        self.bullets.extend(new_bullets)
        
        # Move invaders
        self._move_invaders(dt)
        
        # Update bullets
        self.bullets = [bullet for bullet in self.bullets if bullet.active]
        for bullet in self.bullets:
            bullet.update(dt)
        
        # Update particles
        self.particles = [particle for particle in self.particles 
                        if particle.update(dt)]
        
        # Check collisions
        self._check_collisions()
        
        # Check wave clear
        if not self.invaders and not self.wave_clear:
            self.wave_clear = True
            self.wave_clear_timer = 2.0  # 2 second celebration
            
            # Wave completion bonus
            wave_bonus = 1000 * self.wave * self.wave_bonus_multiplier
            self.score += int(wave_bonus)
            
            # Create celebration effect
            for _ in range(20):
                x = random.uniform(5, self.width - 5)
                y = random.uniform(5, self.height // 2)
                self.particles.append(
                    Particle(x, y, random.uniform(-2, 2), random.uniform(-3, -1),
                           random.choice(['★', '✦', '✧']), 1.5)
                )
        
        # Handle wave clear timer
        if self.wave_clear and self.wave_clear_timer > 0:
            self.wave_clear_timer -= dt
            if self.wave_clear_timer <= 0:
                self.wave += 1
                self._spawn_wave(self.wave)
    
    def _move_invaders(self, dt: float):
        """Move invaders in formation."""
        if not self.invaders:
            return
        
        # Move horizontally
        move_speed = 0.05 + (self.wave - 1) * 0.01
        
        for invader in self.invaders:
            invader.x += self.invader_direction.value * move_speed
        
        # Check if need to change direction
        should_drop = False
        for invader in self.invaders:
            if invader.x <= 2 or invader.x >= self.width - 3:
                should_drop = True
                break
        
        if should_drop:
            # Change direction
            self.invader_direction = Direction.RIGHT if self.invader_direction == Direction.LEFT else Direction.LEFT
            
            # Drop down
            for invader in self.invaders:
                invader.y += 1
            
            # Check if invaders reached player
            for invader in self.invaders:
                if invader.y >= self.height - 5:
                    self._end_game()
                    return
    
    def _check_collisions(self):
        """Check all collisions."""
        # Bullet-invader collisions
        for bullet in self.bullets[:]:
            if bullet.is_player:  # Player bullets
                for invader in self.invaders[:]:
                    if (abs(bullet.x - invader.x) < 1 and 
                        abs(bullet.y - invader.y) < 1):
                        # Hit invader
                        invader.health -= 1
                        bullet.active = False
                        
                        if invader.health <= 0:
                            # Destroy invader
                            self.invaders.remove(invader)
                            self.score += invader.points
                            
                            # Create explosion effect
                            for _ in range(8):
                                self.particles.append(
                                    Particle(invader.x, invader.y,
                                           random.uniform(-3, 3), random.uniform(-3, 3),
                                           random.choice(['*', '+', '·']), 0.8)
                                )
        
        # Bullet-player collisions
        for bullet in self.bullets[:]:
            if not bullet.is_player:  # Enemy bullets
                if (self.player_ship and 
                    abs(bullet.x - self.player_ship.x) < 1 and 
                    abs(bullet.y - self.player_ship.y) < 1):
                    # Hit player
                    self.lives -= 1
                    bullet.active = False
                    
                    # Create damage effect
                    for _ in range(6):
                        self.particles.append(
                            Particle(self.player_ship.x, self.player_ship.y,
                                   random.uniform(-2, 2), random.uniform(-2, 2),
                                   random.choice(['!', '💥', '⚡']), 0.6)
                        )
                    
                    if self.lives <= 0:
                        self._end_game()
    
    def _end_game(self):
        """End the game."""
        self.game_over = True
        
        # Calculate final score with bonuses
        final_score = self.score
        
        # Speedrun bonus
        if self.current_mode == GameMode.SPEEDRUN:
            elapsed = time.time() - self.game_start_time
            if elapsed < 120:  # Under 2 minutes
                final_score += 2000
        
        self.score = final_score
    
    def _render(self, screen):
        """Render the game."""
        screen.clear()
        height, width = screen.getmaxyx()
        
        # Draw title
        title = f"SPACE INVADERS - Wave {self.wave}"
        screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Calculate game area position (centered)
        game_x = (width - self.width) // 2
        game_y = (height - self.height) // 2 + 1
        
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
        controls_text = "Arrow Keys/A/D: Move | Space: Shoot | P: Pause | ESC: Quit"
        screen.addstr(height - 1, (width - len(controls_text)) // 2, controls_text)
        
        screen.refresh()
    
    def _draw_game_area(self, screen, x: int, y: int):
        """Draw the game area border."""
        # Draw borders
        for i in range(self.width):
            screen.addch(y - 1, x + i, '─')
            screen.addch(y + self.height, x + i, '─')
        
        for i in range(self.height):
            screen.addch(y + i, x - 1, '│')
            screen.addch(y + i, x + self.width, '│')
        
        # Draw corners
        screen.addch(y - 1, x - 1, '┌')
        screen.addch(y - 1, x + self.width, '┐')
        screen.addch(y + self.height, x - 1, '└')
        screen.addch(y + self.height, x + self.width, '┘')
        
        # Draw star field background
        for i in range(20):
            star_x = (i * 7) % self.width
            star_y = (i * 3) % self.height
            if random.random() < 0.3:  # 30% star density
                screen.addch(y + star_y, x + star_x, random.choice(['·', '+', '✦']))
    
    def _draw_game_objects(self, screen, x: int, y: int):
        """Draw all game objects."""
        # Draw invaders
        for invader in self.invaders:
            if 0 <= invader.x < self.width and 0 <= invader.y < self.height:
                char = invader.get_display_char()
                screen.addch(y + int(invader.y), x + int(invader.x), char)
        
        # Draw player ship
        if self.player_ship and 0 <= self.player_ship.x < self.width:
            ship_char = '▲' if self.player_ship.health > 1 else '△'
            screen.addch(y + int(self.player_ship.y), x + int(self.player_ship.x),
                       ship_char, curses.color_pair(3) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        
        # Draw bullets
        for bullet in self.bullets:
            if 0 <= bullet.x < self.width and 0 <= bullet.y < self.height:
                if bullet.is_player:
                    char = '|'
                    attr = curses.color_pair(4) if curses.has_colors() else 0
                else:
                    char = '↓'
                    attr = curses.color_pair(5) if curses.has_colors() else 0
                
                screen.addch(y + int(bullet.y), x + int(bullet.x), char, attr)
        
        # Draw particles
        for particle in self.particles:
            if 0 <= particle.x < self.width and 0 <= particle.y < self.height:
                opacity = particle.lifetime / particle.max_lifetime
                if opacity > 0.5:
                    screen.addch(y + int(particle.y), x + int(particle.x), particle.char)
    
    def _draw_ui(self, screen, x: int, y: int):
        """Draw UI elements."""
        # Score and stats
        info_lines = [
            f"Score: {self.score}",
            f"Wave: {self.wave}",
            f"Lives: {'♥' * self.lives}",
            f"Invaders: {len(self.invaders)}"
        ]
        
        if hasattr(self, 'time_limit') and self.time_limit > 0:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            info_lines.append(f"Time: {remaining:.1f}s")
        
        for i, line in enumerate(info_lines):
            screen.addstr(y + i, x, line)
        
        # Wave clear celebration
        if self.wave_clear and self.wave_clear_timer > 0:
            wave_text = "WAVE COMPLETE!"
            bonus = int(1000 * self.wave * self.wave_bonus_multiplier)
            bonus_text = f"Bonus: +{bonus}"
            screen.addstr(y + 10, x + 5, wave_text, curses.A_BLINK)
            screen.addstr(y + 11, x + 5, bonus_text, curses.A_BOLD)
    
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
Space - Fire Weapon
P - Pause/Resume
ESC - Quit Game

OBJECTIVE:
Destroy all alien invaders before they reach Earth!
Survive as many waves as possible.

INVADERS:
👾 Basic - 10 points
👽 Medium - 20 points  
🛸 Elite - 30 points

GAMEPLAY:
- Invaders move faster with each wave
- They shoot more frequently in later waves
- Earn bonus points for completing waves

GAME MODES:
Normal: Classic Space Invaders gameplay.
Time Attack: Score as much as possible in 5 minutes!
Speedrun: Complete waves quickly for double points.
Infinite: Endless waves with increasing difficulty.

SCORING:
Invader Kills: 10-30 points (by type)
Wave Completion: 1000 × wave number points
Speedrun Bonus: 2000 points for finishing under 2 minutes
"""