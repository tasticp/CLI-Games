"""
ncurses-based menu system for the CLI Games Launcher.
Provides interactive menu navigation with smooth animations and preview support.
"""

import curses
import time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

class MenuAction(Enum):
    """Menu item actions."""
    SELECT = "select"
    BACK = "back"
    EXIT = "exit"
    CUSTOM = "custom"

class MenuItem:
    """Represents a single menu item."""
    
    def __init__(self, text: str, action: MenuAction = MenuAction.SELECT, 
                 data: Any = None, description: str = "", submenu: 'Menu' = None):
        self.text = text
        self.action = action
        self.data = data
        self.description = description
        self.submenu = submenu
        self.selected = False

class Menu:
    """Interactive menu system with ncurses."""
    
    def __init__(self, title: str = "CLI Games Launcher", subtitle: str = ""):
        self.title = title
        self.subtitle = subtitle
        self.items: List[MenuItem] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.animation_time = 0
        self.show_descriptions = True
        self.parent_menu: Optional['Menu'] = None
        
    def add_item(self, item: MenuItem):
        """Add an item to the menu."""
        self.items.append(item)
    
    def add_text(self, text: str, description: str = "", data: Any = None):
        """Add a simple text item that can be selected."""
        item = MenuItem(text, MenuAction.SELECT, data, description)
        self.add_item(item)
    
    def add_submenu(self, text: str, submenu: 'Menu', description: str = ""):
        """Add a submenu item."""
        submenu.parent_menu = self
        item = MenuItem(text, MenuAction.SELECT, submenu, description, submenu)
        self.add_item(item)
    
    def add_back(self):
        """Add a back button (for submenus)."""
        item = MenuItem("Back", MenuAction.BACK)
        self.add_item(item)
    
    def add_exit(self, text: str = "Exit"):
        """Add an exit button."""
        item = MenuItem(text, MenuAction.EXIT)
        self.add_item(item)
    
    def show(self, stdscr, theme: Dict[str, Any] = None) -> Optional[MenuItem]:
        """Display the menu and return selected item."""
        if theme is None:
            theme = {
                'text': curses.COLOR_WHITE,
                'selected': curses.COLOR_CYAN,
                'title': curses.COLOR_YELLOW,
                'border': curses.COLOR_BLUE,
                'description': curses.COLOR_GREEN
            }
        
        # Setup colors if available
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            
            # Define color pairs
            curses.init_pair(1, theme['text'], curses.COLOR_BLACK)
            curses.init_pair(2, theme['selected'], curses.COLOR_BLACK)
            curses.init_pair(3, theme['title'], curses.COLOR_BLACK)
            curses.init_pair(4, theme['border'], curses.COLOR_BLACK)
            curses.init_pair(5, theme['description'], curses.COLOR_BLACK)
        
        # Hide cursor
        curses.curs_set(0)
        stdscr.nodelay(0)  # Blocking input
        
        while True:
            self.draw(stdscr, theme)
            key = stdscr.getch()
            
            # Handle input
            if key == curses.KEY_UP or key == ord('k'):
                self.selected_index = max(0, self.selected_index - 1)
                self._adjust_scroll()
            elif key == curses.KEY_DOWN or key == ord('j'):
                self.selected_index = min(len(self.items) - 1, self.selected_index + 1)
                self._adjust_scroll()
            elif key == curses.KEY_PPAGE:  # Page up
                self.selected_index = max(0, self.selected_index - 5)
                self._adjust_scroll()
            elif key == curses.KEY_NPAGE:  # Page down
                self.selected_index = min(len(self.items) - 1, self.selected_index + 5)
                self._adjust_scroll()
            elif key in [curses.KEY_ENTER, 10, 13]:  # Enter
                if self.items:
                    selected_item = self.items[self.selected_index]
                    
                    # Handle submenu navigation
                    if isinstance(selected_item.data, Menu):
                        result = selected_item.data.show(stdscr, theme)
                        if result is not None:
                            return result
                    else:
                        return selected_item
            elif key == 27:  # ESC
                if self.parent_menu:
                    return MenuItem("Back", MenuAction.BACK)
                else:
                    return MenuItem("Exit", MenuAction.EXIT)
            elif key == ord('q'):
                return MenuItem("Exit", MenuAction.EXIT)
            
            # Update animation
            self.animation_time += 0.1
    
    def draw(self, stdscr, theme: Dict[str, Any]):
        """Draw the menu."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Draw border
        self._draw_border(stdscr, theme)
        
        # Draw title
        if self.title:
            title_lines = self.title.split('\n')
            for i, line in enumerate(title_lines):
                title_y = 2 + i
                if title_y < height - 2:
                    title_text = f" {line} "[:width-4]
                    title_x = (width - len(title_text)) // 2
                    stdscr.addstr(title_y, title_x, title_text, curses.color_pair(3) | curses.A_BOLD)
        
        # Draw subtitle
        if self.subtitle and height > 5:
            subtitle_text = f" {self.subtitle} "[:width-4]
            subtitle_x = (width - len(subtitle_text)) // 2
            stdscr.addstr(4, subtitle_x, subtitle_text, curses.color_pair(5))
        
        # Calculate visible area for menu items
        start_y = 7 if self.title else 3
        max_items = height - start_y - 3
        if max_items < 1:
            max_items = 1
        
        # Draw menu items
        visible_items = self.items[self.scroll_offset:self.scroll_offset + max_items]
        for i, item in enumerate(visible_items):
            y = start_y + i
            if y >= height - 2:
                break
                
            # Determine if this item is selected
            is_selected = (self.scroll_offset + i) == self.selected_index
            
            # Prepare the display text
            prefix = "▶ " if is_selected else "  "
            display_text = f"{prefix}{item.text}"[:width-6]
            
            # Apply colors
            if is_selected:
                attr = curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE
            else:
                attr = curses.color_pair(1)
            
            stdscr.addstr(y, 3, display_text, attr)
            
            # Draw description if available and there's space
            if self.show_descriptions and item.description and height > y + 2:
                desc_lines = item.description.split('\n')
                for j, desc_line in enumerate(desc_lines[:2]):  # Max 2 lines of description
                    if y + j + 1 < height - 2:
                        desc_text = f"    └─ {desc_line}"[:width-8]
                        stdscr.addstr(y + j + 1, 5, desc_text, curses.color_pair(5))
        
        # Draw scroll indicator if needed
        if len(self.items) > max_items:
            scroll_height = max(1, (max_items * max_items) // len(self.items))
            scroll_pos = start_y + (self.selected_index * (max_items - scroll_height)) // max(len(self.items) - max_items, 1)
            
            for y in range(start_y, start_y + max_items):
                if y < height - 2:
                    if scroll_pos <= y < scroll_pos + scroll_height:
                        stdscr.addch(y, width - 2, '█', curses.color_pair(4))
                    else:
                        stdscr.addch(y, width - 2, '░', curses.color_pair(4))
        
        # Draw help text at bottom
        help_text = "↑↓: Navigate | Enter: Select | ESC: Back | Q: Exit"
        if len(help_text) < width - 4:
            help_x = (width - len(help_text)) // 2
            stdscr.addstr(height - 1, help_x, help_text, curses.color_pair(4))
        
        stdscr.refresh()
    
    def _draw_border(self, stdscr, theme: Dict[str, Any]):
        """Draw a decorative border."""
        height, width = stdscr.getmaxyx()
        
        # Top border
        stdscr.addstr(0, 0, "╔" + "═" * (width - 2) + "╗", curses.color_pair(4))
        
        # Side borders
        for y in range(1, height - 1):
            stdscr.addch(y, 0, '║', curses.color_pair(4))
            stdscr.addch(y, width - 1, '║', curses.color_pair(4))
        
        # Bottom border
        stdscr.addstr(height - 1, 0, "╚" + "═" * (width - 2) + "╝", curses.color_pair(4))
    
    def _adjust_scroll(self):
        """Adjust scroll offset to keep selection visible."""
        height = curses.LINES  # Approximate terminal height
        start_y = 7 if self.title else 3
        max_items = height - start_y - 3
        if max_items < 1:
            max_items = 1
        
        # Make sure selected item is visible
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + max_items:
            self.scroll_offset = self.selected_index - max_items + 1
        
        # Ensure scroll offset is within bounds
        self.scroll_offset = max(0, min(self.scroll_offset, len(self.items) - max_items))
    
    def clear(self):
        """Clear all menu items."""
        self.items.clear()
        self.selected_index = 0
        self.scroll_offset = 0