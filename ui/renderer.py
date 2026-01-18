"""
ASCII art rendering and display system for the CLI Games Launcher.
Provides fonts, sprites, animations, and visual effects.
"""

import time
import math
from typing import Dict, List, Tuple, Optional
from enum import Enum

class FontStyle(Enum):
    """Available ASCII font styles."""
    STANDARD = "standard"
    BLOCK = "block"
    BANNER = "banner"
    SLANT = "slant"
    SMALL = "small"

class ASCIIRenderer:
    """Renders ASCII art, text, and animations."""
    
    def __init__(self):
        self.fonts = self._load_fonts()
        self.sprites = self._load_sprites()
        self.animations = {}
        self.particles = []
    
    def _load_fonts(self) -> Dict[str, Dict[str, List[str]]]:
        """Load ASCII font definitions."""
        return {
            "standard": self._create_standard_font(),
            "block": self._create_block_font(),
            "banner": self._create_banner_font(),
            "small": self._create_small_font()
        }
    
    def _create_standard_font(self) -> Dict[str, List[str]]:
        """Create standard ASCII font."""
        return {
            'A': [
                "  ▄▄▄   ",
                " ▐█ █▌  ",
                "▐█▄▄█▄▌ ",
                "▐█  █▌  ",
                " ▀  ▀   "
            ],
            'B': [
                "▄▄▄▄▄   ",
                "▐█ █▌   ",
                "▐▀▀▀▀▄▄ ",
                "▐█   █▌ ",
                " ▀▀▀▀▀  "
            ],
            'C': [
                " ▄▄▄▄▄  ",
                "▐█      ",
                "▐█      ",
                "▐█      ",
                " ▀▀▀▀▀  "
            ],
            'D': [
                "▄▄▄▄▄   ",
                "▐█ █▌   ",
                "▐█  █▌  ",
                "▐█ █▌   ",
                " ▀▀▀▀   "
            ],
            'E': [
                "▄▄▄▄▄▄▄ ",
                "▐█      ",
                "▐▀▀▀▀▀▀ ",
                "▐█      ",
                " ▀▀▀▀▀▀ "
            ],
            'F': [
                "▄▄▄▄▄▄▄ ",
                "▐█      ",
                "▐▀▀▀▀▀▀ ",
                "▐█      ",
                "▀       "
            ],
            'G': [
                " ▄▄▄▄▄  ",
                "▐█      ",
                "▐█  ▄▄▄▌",
                "▐█ █▌ █▌",
                " ▀▀▀▀▀  "
            ],
            'H': [
                "▄▄   ▄▄ ",
                "▐█   █▌ ",
                "▐█████▌ ",
                "▐█   █▌ ",
                "▀    ▀  "
            ],
            'I': [
                "▄▄▄▄▄▄▄",
                "   █   ",
                "   █   ",
                "   █   ",
                " ▀▀▀▀▀ "
            ],
            'L': [
                "▄       ",
                "▐█      ",
                "▐█      ",
                "▐█████▌ ",
                " ▀▀▀▀▀ "
            ],
            'M': [
                "▄▄    ▄▄ ",
                "▐██  ██▌ ",
                "▐█ █ ██▌ ",
                "▐█  ▐█▌  ",
                "▀    ▀   "
            ],
            'N': [
                "▄▄   ▄▄ ",
                "▐██▄ ▐█▌ ",
                "▐█ ████▌ ",
                "▐█▌  ███ ",
                "▀    ▀  "
            ],
            'O': [
                " ▄▄▄▄▄  ",
                "▐█   █▌ ",
                "▐█   █▌ ",
                "▐█   █▌ ",
                " ▀▀▀▀▀  "
            ],
            'P': [
                "▄▄▄▄▄   ",
                "▐█ █▌   ",
                "▐▀▀▀▀▄▄ ",
                "▐█      ",
                " ▀      "
            ],
            'R': [
                "▄▄▄▄▄   ",
                "▐█ █▌   ",
                "▐▀▀▀▀▄▄ ",
                "▐█   █▌ ",
                " ▀▀▀▀▀  "
            ],
            'S': [
                " ▄▄▄▄▄  ",
                "▐█      ",
                " ▀▀▀▀▀▄ ",
                "      █▌",
                " ▀▀▀▀▀  "
            ],
            'T': [
                "▄▄▄▄▄▄▄",
                "   █   ",
                "   █   ",
                "   █   ",
                "   ▀   "
            ],
            'U': [
                "▄▄   ▄▄ ",
                "▐█   █▌ ",
                "▐█   █▌ ",
                "▐█   █▌ ",
                " ▀▀▀▀▀  "
            ],
            'V': [
                "▄▄   ▄▄ ",
                "▐█   █▌ ",
                "▐█   █▌ ",
                " ▐█ █▌  ",
                "  ▀▀   "
            ],
            'W': [
                "▄▄    ▄▄ ",
                "▐█    █▌ ",
                "▐█ █ ██▌ ",
                "▐██  ██▌ ",
                "▀    ▀  "
            ],
            'Y': [
                "▄▄   ▄▄ ",
                "▐█   █▌ ",
                " ▐█ █▌  ",
                "   █   ",
                "   ▀   "
            ],
            ' ': [
                "       ",
                "       ",
                "       ",
                "       ",
                "       "
            ],
            '!': [
                "   ▄   ",
                "   █   ",
                "   █   ",
                "       ",
                "   ▀   "
            ],
            '?': [
                " ▄▄▄▄▄ ",
                "▐█    █▌",
                "    █  ",
                "   ▄   ",
                "   ▀   "
            ],
            '0': [
                " ▄▄▄▄▄ ",
                "▐█ █ █▌",
                "▐█ █ █▌",
                "▐█ █ █▌",
                " ▀▀▀▀▀ "
            ],
            '1': [
                "  ▄▄  ",
                " ▐█ █▌",
                "   █ ",
                "   █ ",
                " ▀▀▀▀"
            ],
            '2': [
                " ▄▄▄▄▄ ",
                "▐█    █▌",
                "   ▄▄▄▌",
                "▐█    ",
                " ▀▀▀▀▀▀"
            ],
            '3': [
                " ▄▄▄▄▄ ",
                "▐█    █▌",
                "   ███ ",
                "▐█    █▌",
                " ▀▀▀▀▀ "
            ],
            '4': [
                "▄▄   ▄▄",
                "▐█   █▌",
                "▐█████▌",
                "    █ ",
                "    ▀ "
            ],
            '5': [
                "▄▄▄▄▄▄▄",
                "▐█     ",
                "▀▀▀▀▀▄▄",
                "     █▌",
                "▀▀▀▀▀▀ "
            ],
            '6': [
                " ▄▄▄▄▄  ",
                "▐█      ",
                "▐████▄▄ ",
                "▐█   █▌ ",
                " ▀▀▀▀▀  "
            ],
            '7': [
                "▄▄▄▄▄▄▄▄",
                "      █▌",
                "    █  ",
                "   █   ",
                "  ▀    "
            ],
            '8': [
                " ▄▄▄▄▄  ",
                "▐█   █▌ ",
                " ▀▀▀▀▀▄ ",
                "▐█   █▌ ",
                " ▀▀▀▀▀  "
            ],
            '9': [
                " ▄▄▄▄▄  ",
                "▐█   █▌ ",
                " ▀████▀ ",
                "      █▌",
                " ▀▀▀▀▀  "
            ]
        }
    
    def _create_block_font(self) -> Dict[str, List[str]]:
        """Create block ASCII font."""
        return {
            'A': [
                "█████╗ ",
                "██╔═██╗",
                "██████╔╝",
                "██╔══██╗",
                "██║  ██║",
                "╚═╝  ╚═╝"
            ],
            'C': [
                " ██████╗",
                "██╔════╝",
                "██║     ",
                "██║     ",
                "╚██████╗",
                " ╚═════╝"
            ],
            # ... (simplified for brevity)
        }
    
    def _create_banner_font(self) -> Dict[str, List[str]]:
        """Create banner ASCII font."""
        return {
            'A': [
                " __  __ ",
                "|  \\/  |",
                "| \\  / |",
                "| |\\/| |",
                "| |  | |",
                "|_|  |_|"
            ],
            # ... (simplified for brevity)
        }
    
    def _create_small_font(self) -> Dict[str, List[str]]:
        """Create small ASCII font."""
        return {
            'A': ["▄█▄", "█▄█", "█▄█"],
            'B': ["▄█ ", "██ ", "▄█▄"],
            'C': ["▄█▄", "█  ", "▀▀▀"],
            # ... (simplified for brevity)
        }
    
    def _load_sprites(self) -> Dict[str, List[str]]:
        """Load sprite definitions."""
        return {
            'heart': [
                "  ♥♥   ",
                " ♥  ♥  ",
                "♥    ♥ ",
                " ♥  ♥  ",
                "  ♥♥   "
            ],
            'star': [
                "    ★    ",
                "   ★★★   ",
                "  ★★★★★  ",
                " ★★★★★★★ ",
                "  ★★★★★  ",
                "   ★★★   ",
                "    ★    "
            ],
            'explosion': [
                "    *    ",
                "   ***   ",
                "  *****  ",
                " *** *** ",
                "***** ***",
                " *** *** ",
                "  *****  ",
                "   ***   ",
                "    *    "
            ],
            'coin': [
                "  █████  ",
                " ██▄▄██ ",
                "██  █ ██",
                "██  █ ██",
                " ██▀▀██ ",
                "  █████  "
            ],
            'trophy': [
                "    ▄▄   ",
                "   ████  ",
                "  ██████ ",
                " ████████",
                "    ██   ",
                "   ████  ",
                "████████ "
            ],
            'ghost': [
                "  ▄▄▄▄▄  ",
                " ██   ██ ",
                "███████ ",
                "█████████",
                "███   ███",
                "██ ██ ██",
                "██   ██",
                "██   ██"
            ],
            'mushroom': [
                "   ▄▄▄▄▄   ",
                "  ███████  ",
                " ████████ ",
                "███████████",
                "   ████   ",
                "  ███████  ",
                " ████████ ",
                "    ██    "
            ]
        }
    
    def render_text(self, text: str, font: FontStyle = FontStyle.STANDARD) -> List[str]:
        """Render text using ASCII font."""
        font_name = font.value
        if font_name not in self.fonts:
            font_name = "standard"
        
        font_data = self.fonts[font_name]
        
        # Convert to uppercase for font lookup
        text = text.upper()
        
        # Determine character width and height
        if font_data:
            sample_char = next(iter(font_data.values()))
            char_height = len(sample_char)
            char_width = len(sample_char[0]) if sample_char else 5
        else:
            char_height = 5
            char_width = 7
        
        # Build each line of the output
        result = []
        for line in range(char_height):
            text_line = ""
            for char in text:
                if char in font_data:
                    text_line += font_data[char][line]
                else:
                    # Use space for missing characters
                    text_line += " " * char_width
            result.append(text_line)
        
        return result
    
    def render_sprite(self, sprite_name: str, x: int = 0, y: int = 0, 
                     scale: float = 1.0) -> Optional[List[Tuple[int, int, str]]]:
        """Render a sprite with position and scaling."""
        if sprite_name not in self.sprites:
            return None
        
        sprite = self.sprites[sprite_name]
        result = []
        
        for sy, line in enumerate(sprite):
            for sx, char in enumerate(line):
                if char != ' ':
                    # Apply scaling
                    scaled_x = int(x + sx * scale)
                    scaled_y = int(y + sy * scale)
                    result.append((scaled_x, scaled_y, char))
        
        return result
    
    def create_animation(self, name: str, frames: List[List[str]], 
                        frame_delay: float = 0.1, loop: bool = True) -> bool:
        """Create a new animation."""
        self.animations[name] = {
            'frames': frames,
            'frame_delay': frame_delay,
            'loop': loop,
            'current_frame': 0,
            'last_update': 0,
            'playing': False
        }
        return True
    
    def play_animation(self, name: str) -> bool:
        """Start playing an animation."""
        if name in self.animations:
            self.animations[name]['playing'] = True
            self.animations[name]['last_update'] = time.time()
            return True
        return False
    
    def stop_animation(self, name: str) -> bool:
        """Stop playing an animation."""
        if name in self.animations:
            self.animations[name]['playing'] = False
            self.animations[name]['current_frame'] = 0
            return True
        return False
    
    def get_animation_frame(self, name: str) -> Optional[List[str]]:
        """Get the current frame of an animation."""
        if name not in self.animations:
            return None
        
        anim = self.animations[name]
        
        if not anim['playing']:
            return anim['frames'][0] if anim['frames'] else None
        
        # Update frame based on time
        current_time = time.time()
        if current_time - anim['last_update'] >= anim['frame_delay']:
            anim['current_frame'] += 1
            
            if anim['current_frame'] >= len(anim['frames']):
                if anim['loop']:
                    anim['current_frame'] = 0
                else:
                    anim['playing'] = False
                    anim['current_frame'] = len(anim['frames']) - 1
            
            anim['last_update'] = current_time
        
        return anim['frames'][anim['current_frame']]
    
    def add_particle(self, x: int, y: int, char: str, 
                    dx: float = 0, dy: float = 0, 
                    lifetime: float = 1.0, color: Optional[str] = None):
        """Add a particle effect."""
        particle = {
            'x': float(x),
            'y': float(y),
            'dx': dx,
            'dy': dy,
            'char': char,
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'color': color
        }
        self.particles.append(particle)
    
    def update_particles(self, dt: float):
        """Update all particles."""
        surviving_particles = []
        
        for particle in self.particles:
            # Update position
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            
            # Update lifetime
            particle['lifetime'] -= dt
            
            # Apply gravity (optional)
            particle['dy'] += 100 * dt  # Gravity effect
            
            if particle['lifetime'] > 0:
                surviving_particles.append(particle)
        
        self.particles = surviving_particles
    
    def get_particles(self) -> List[Tuple[int, int, str, float]]:
        """Get all current particles with opacity."""
        result = []
        for particle in self.particles:
            opacity = particle['lifetime'] / particle['max_lifetime']
            x = int(particle['x'])
            y = int(particle['y'])
            result.append((x, y, particle['char'], opacity))
        return result
    
    def create_box(self, width: int, height: int, 
                  style: str = "double") -> List[str]:
        """Create a decorative box."""
        styles = {
            "single": {
                "corner_tl": "┌", "corner_tr": "┐", 
                "corner_bl": "└", "corner_br": "┘",
                "horizontal": "─", "vertical": "│"
            },
            "double": {
                "corner_tl": "╔", "corner_tr": "╗",
                "corner_bl": "╚", "corner_br": "╝", 
                "horizontal": "═", "vertical": "║"
            },
            "rounded": {
                "corner_tl": "╭", "corner_tr": "╮",
                "corner_bl": "╰", "corner_br": "╯",
                "horizontal": "─", "vertical": "│"
            }
        }
        
        if style not in styles:
            style = "double"
        
        s = styles[style]
        box = []
        
        # Top line
        top_line = s["corner_tl"] + s["horizontal"] * (width - 2) + s["corner_tr"]
        box.append(top_line)
        
        # Middle lines
        middle_line = s["vertical"] + " " * (width - 2) + s["vertical"]
        for _ in range(height - 2):
            box.append(middle_line)
        
        # Bottom line
        bottom_line = s["corner_bl"] + s["horizontal"] * (width - 2) + s["corner_br"]
        box.append(bottom_line)
        
        return box
    
    def create_progress_bar(self, current: int, maximum: int, 
                           width: int = 20, style: str = "█") -> str:
        """Create a progress bar."""
        if maximum <= 0:
            percentage = 0
        else:
            percentage = min(1.0, current / maximum)
        
        filled_width = int(width * percentage)
        empty_width = width - filled_width
        
        bar = style * filled_width + "░" * empty_width
        percentage_text = f" {percentage * 100:.0f}%"
        
        return f"[{bar}]{percentage_text}"
    
    def create_explosion_effect(self, x: int, y: int, size: int = 5):
        """Create an explosion particle effect."""
        for i in range(size * 10):
            angle = (i / (size * 10)) * 2 * math.pi
            speed = random.uniform(50, 200)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            chars = ["*", "+", "✦", "✧", "·"]
            char = random.choice(chars)
            
            self.add_particle(x, y, char, dx, dy, lifetime=1.0)
    
    def create_text_effect(self, text: str, x: int, y: int, 
                          effect: str = "wave"):
        """Create special text effects."""
        if effect == "wave":
            for i, char in enumerate(text):
                if char != ' ':
                    offset_y = int(math.sin(i * 0.5) * 2)
                    self.add_particle(x + i, y + offset_y, char, dx=0, dy=0, lifetime=2.0)
        
        elif effect == "spiral":
            for i, char in enumerate(text):
                if char != ' ':
                    angle = i * 0.5
                    radius = 5
                    px = x + int(math.cos(angle) * radius)
                    py = y + int(math.sin(angle) * radius)
                    self.add_particle(px, py, char, dx=0, dy=0, lifetime=2.0)
        
        elif effect == "typewriter":
            for i, char in enumerate(text):
                if char != ' ':
                    delay = i * 0.1
                    self.add_particle(x + i, y, char, dx=0, dy=0, lifetime=3.0)
    
    def get_available_fonts(self) -> List[str]:
        """Get list of available font names."""
        return list(self.fonts.keys())
    
    def get_available_sprites(self) -> List[str]:
        """Get list of available sprite names."""
        return list(self.sprites.keys())