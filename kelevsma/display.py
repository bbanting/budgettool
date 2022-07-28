"""Module to handle displaying output in terminal."""
from __future__ import annotations
from fileinput import filename

import os
import logging
import collections
import time
from dataclasses import dataclass
from typing import Any, Callable

import colorama
from colorama import Fore, Back, Style


colorama.init(autoreset=True)


class DisplayError(Exception):
    pass


@dataclass(slots=True)
class Line:
    """Represents a single line to be printed. Holds a reference to the
    original object the text is derived from."""
    ref_obj: Any
    text: str

    def __str__(self) -> str:
        return self.text


class LineGroup(collections.UserList):
    """A group of lines for printing."""

    def __init__(self, number:bool=False, trunc:bool=False, bold:bool=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.number = number
        self.trunc = trunc
        self.bold = bold
    
    def prepare_lines(self) -> list[Line]:
        """Return a list of lines that won't overflow."""
        lines = []
        width = t_width()
        if self.number:
            width -= 3

        # For truncated line output
        if self.trunc:
            lines.extend([Line(obj, str(obj)[:width]) for obj in self])
            return lines

        # For full output
        for obj in self:
            src_string = str(obj)
            first_line = True
            obj_lines = []
            while src_string:
                if first_line:
                    obj_lines.append(Line(obj, src_string[:width]))
                    src_string = src_string[width:]
                    first_line = False
                    continue
                obj_lines.append(Line(obj, f"    {src_string[:width-4]}"))
                src_string = src_string[width-4:]
            for l in obj_lines[::-1]:
                lines.append(l)

        return lines
        
    def print(self) -> list[str]:
        """Return all lines for printing if any exist."""
        lines = self.prepare_lines()
        normal_style = f"{Back.RESET}{Fore.RESET}{Style.NORMAL}"
        style = Style.BRIGHT if self.bold else normal_style
        return [f"{style}{l}{normal_style}" for l in lines]


class BodyLines(LineGroup):
    """A special LineGroup for the screen body."""
    def __init__(self, parent:Screen, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parent_screen = parent
        self._page = 1
        self.selected = None

    @property
    def space(self) -> int:
        return self.parent_screen.body_space

    @property
    def page(self) -> int:
        """Get the current page."""
        n_pages = self.n_pages
        if 0 < self._page <= n_pages:
           return self._page
        elif self._page > n_pages:
            return n_pages

    @property
    def n_pages(self) -> int:
        """Return the total number of pages."""
        pages = len(self) / self.space
        if pages.is_integer():
            pages = int(pages)
        else:
            pages = int(pages + 1)
        return pages if pages else 1

    def get_current_range(self) -> tuple[int]:
        """Return the start and end indices of the current page."""
        start = -(self.page * self.space)
        if self.parent_screen.reverse_body_order:
            start = 0 + ((self.page-1) * self.space)
        end = start + self.space if start + self.space else None
        return (start, end)

    def change_page(self, page: int) -> None:
        """Change which page to display."""
        if page != self.page:
            self.selected = 0
        if page < 1:
            return
        self._page = page

    def select(self, index: int) -> Any:
        """Return an item by line number from the current page."""
        start, end = self.get_current_range()
        items = list(self)[start:end][::-1]
        if index > len(items) or index < 1:
            raise DisplayError("Invalid line selection.")

        self.selected = items[index-1]
        return self.selected

    def print(self) -> list[str]:
        """Return all lines for printing if any exist."""
        lines = []
        start, end = self.get_current_range()
        raw_lines: list[Line] = list(reversed(self.prepare_lines()[start:end]))

        # Append lines
        # Prepend numbers and highlight if selected
        count = 1
        for line in raw_lines:
            to_print = line
            if self.number:
                to_print = f"{Style.DIM}{count:02} {Style.NORMAL}{to_print}"
            if line.ref_obj is self.selected:
                to_print = f"{Fore.CYAN}{to_print}{Fore.RESET}"
            lines.append(to_print)
            count += 1
        
        if self.parent_screen.reverse_body_order:
            lines = lines[::-1]

        # Append empty space
        while count <= self.space:
            lines.append(f"{Style.DIM}{count:02}" if self.number else "")
            count += 1
        
        return [str(l) for l in lines]


class Screen:
    """A buffer of lines to print."""
    def __init__(self, name:str, *, min_width:int=50, min_body_height:int=5, 
    numbered:bool=False, truncate:bool=False, refresh_func:Callable=None, 
    reversed:bool=False, clear:bool=False) -> None:
        # Attributes
        self.name = name
        self.min_body_height = min_body_height
        self.min_width = min_width
        self.offset = 3 # Page nums, message line, input line
        self.refresh_func = refresh_func
        self.reverse_body_order = reversed
        self.clear_on_refresh = clear

        # Sub-buffers & state
        self.body = BodyLines(self, trunc=truncate, number=numbered)
        self.header = LineGroup(trunc=True, bold=True)
        self.footer = LineGroup()
        self.message = ""
        self.printed = False
    
    @property
    def body_space(self) -> int:
        """Return the height in lines of the available space for the body."""
        return t_height() - sum((self.offset, len(self.header), len(self.footer)))

    @property
    def selected(self) -> Any:
        return self.body.selected

    def check_window_size(self) -> bool:
        """Check if the terminal is big enough. Print message if not and 
        return False. Otherwise return True.
        """
        high_enough = t_height() >= sum((3, len(self.header), len(self.footer), self.min_body_height))
        wide_enough = t_width() >= self.min_width
        dimensions = [("height", high_enough), ("width", wide_enough)]

        for dim, enough in dimensions:
            if enough:
                continue
            clear_terminal()
            print("\n" * (t_height()-1), end="")
            print(f"Please increase the window {dim}.", end="")
            return False
        return True
        
    def push(self, item:Any, target:str="body") -> None:
        """Append an item to one of the sub-buffers."""
        if self.printed:
            self.printed = False
            self.clear()
        getattr(self, target).append(item)

    def clear(self):
        """Clear all sub-buffers."""
        self.body.clear()
        self.header.clear()
        self.footer.clear()
        
    def _print_page_numbers(self) -> list[str]:
        """Return the divider bar with page numbers for printing."""
        style = f"{Back.WHITE}{Fore.BLACK}{Style.BRIGHT}"
        div_char = " "

        nums = f"{self.body.page} / {self.body.n_pages}"
        free_space = t_width() - len(nums)
        leading = free_space // 2
        trailing = free_space // 2 + (free_space % 2)
        
        return [f"{style}{div_char*leading}{nums}{div_char*trailing}"]

    def _print_message_bar(self) -> list[str]:
        """Return the line below the page numbers for printing."""
        style = f"{Back.RESET}{Fore.WHITE}{Style.NORMAL}"
        msg = f"{style}{self.message}{' ' * (t_width() - len(self.message))}"
        self.message = ""
        return [msg]

    def print(self) -> None:
        """Print the contents of the screen to the terminal."""
        # Check the height before printing
        if not self.check_window_size():
            return

        # Combine into one string and print
        else:
            lines = ["\n"]
            lines.extend(self.header.print())
            lines.extend(self.body.print())
            lines.extend(self.footer.print())
            lines.extend(self._print_page_numbers())
            lines.extend(self._print_message_bar())
            lines.extend(["> "])

            print("\n".join(lines), end="")
            self.printed = True


class ScreenController:
    """A class to switch to and from multiple buffers."""
    _active: Screen
    _screens: dict[str, Screen]

    def __init__(self):
        self._screens = {}

    def add(self, screen:Screen) -> None:
        """Add a screen to the list."""
        self._screens.update({screen.name: screen})
        if len(self._screens) == 1:
            self._active = screen

    def switch_to(self, screen:Screen) -> None:
        """Switch the active screen."""
        self._active = screen

    def get_screen(self, name:str="") -> Screen:
        """Get the active screen."""
        if not self._screens:
            raise DisplayError("No screens have been created.")
        if not name:
            return self._active
        if screen := self._screens.get(name):
            return screen
        else:
            raise DisplayError(f"A screen with the name '{name}' does not exist.")

    def refresh(self) -> None:
        """Clear the terminal and print the current state of the screen."""
        if self._active.refresh_func and self._active.selected is None:
            self._active.refresh_func()
        clear_terminal()
        self._active.print()    


def clear_terminal() -> None:
    if not controller.get_screen().clear_on_refresh:
        return
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def t_width() -> int:
    """Return current terminal width in lines."""
    return os.get_terminal_size()[0]


def t_height() -> int:
    """Return current terminal height in lines."""
    return os.get_terminal_size()[1]


def window_checker() -> None:
    """Check if the terminal window size has changed, refresh if so."""
    width, height = os.get_terminal_size()
    while True:
        time.sleep(0.5)
        new_width, new_height = os.get_terminal_size()
        if (width, height) == (new_width, new_height):
            continue
        width, height = new_width, new_height
        clear_terminal()
        controller.get_screen().print()


def add_screen(screen:Screen) -> None:
    """Public func to add a screen to the controller."""
    if screen.name not in controller._screens:
        controller.add(screen)


def push(*items:Any) -> None:
    """Push an item to body."""
    for item in items:
        controller.get_screen().push(item)

def push_h(*items:Any) -> None:
    """Push an item to header."""
    for item in items:
        controller.get_screen().push(item, target="header")

def push_f(*items:Any) -> None:
    """Push an item to footer."""
    for item in items:
        controller.get_screen().push(item, target="footer")


def select(index) -> Any:
    """Return an item by line number from the current view in screen."""
    return controller.get_screen().body.select(index)

def deselect() -> None:
    """Remove the selection."""
    controller.get_screen().body.selected = None
    

def message(text:str) -> None:
    """Set the message on the current screen. For giving info or errors
    that won't corrupt the output.
    """
    controller.get_screen().message = text

def error(error) -> None:
    """Clears all output and sets the message."""
    clear_terminal()
    controller.get_screen().clear()
    message(str(error))


def change_page(number:int) -> None:
    "Change the page of the active screen."
    controller.get_screen().body.change_page(number)


def refresh() -> None:
    """Call the controller's refresh method."""
    controller.refresh()


controller = ScreenController()
