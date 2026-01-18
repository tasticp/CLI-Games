# CLI Games - Modular Terminal Game Launcher

A comprehensive terminal-based game launcher with support for a vast library of games, featuring:

## 🎮 Features

- **Modular Plugin System**: Easy to add new games
- **Multiple Game Modes**: Time attack, speedrun, infinite, multiplayer
- **Leaderboard System**: Local and global high scores
- **Cross-Platform**: Windows, macOS, Linux support
- **Retro & Modern Games**: Classic and contemporary game adaptations
- **ASCII Art Graphics**: Rich visual experience in terminal

## 🚀 Quick Start

### Requirements
- Python 3.7+
- curses library (usually included with Python)

### Installation
```bash
git clone <repository-url>
cd CLI-Games
python main.py
```

## 🎯 Game Categories

- **Retro Classics**: Mario, Pac-Man, Space Invaders
- **Modern Retro**: Retro-styled versions of modern games  
- **Puzzle Games**: Sudoku, Crosswords, Word games
- **Action Games**: Maze games, Snake, Tetris variants
- **Rhythm Games**: CLI-based rhythm challenges

## 🛠️ Development

### Adding Games
Create a new plugin in the `plugins/` directory:

```python
from plugins.base_game import BaseGame

class MyGame(BaseGame):
    def __init__(self):
        super().__init__()
        self.name = "My Game"
        self.genre = "Puzzle"
        
    def run(self, screen):
        # Your game logic here
        pass
```

### Project Structure
```
cli-games/
├── main.py                 # Entry point
├── core/                   # Core framework
├── ui/                     # User interface
├── plugins/                # Game plugins
├── assets/                 # Fonts, sprites, sounds
└── config/                 # Configuration files
```

## 🎮 Controls

- **Arrow Keys**: Navigate menus
- **Enter**: Select
- **Esc**: Back/Exit
- **Game-specific**: See individual game help

## 🏆 Leaderboards

- Local high scores stored automatically
- Optional online leaderboard integration
- Friend competitions and achievements

## 🌟 Contributing

Contributions welcome! Please read the contributing guidelines before submitting pull requests.

## 📄 License

MIT License - see LICENSE file for details