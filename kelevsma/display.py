"""Module to handle displaying output in terminal."""
from __future__ import annotations

import os
import logging
import collections
import time
from dataclasses import dataclass
from typing import Any, Callable

import colorama
from colorama import Fore, Back, Style


logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")
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
    
    def append(self, obj:Any) -> None:
        """Append an object as a Line. If not truncated, split into
        multiple Line objects as necessary.
        """
        width = t_width()
        if self.number:
            width -= 3

        # For truncated line output
        if self.trunc:
            self.data.append(Line(obj, str(obj)[:width]))
            return

        # For full output
        src_string = str(obj)
        lines = []
        first_line = True
        while src_string:
            if first_line:
                lines.append(Line(obj, src_string[:width]))
                src_string = src_string[width:]
                first_line = False
                continue
            lines.append(Line(obj, f"    {src_string[:width-4]}"))
            src_string = src_string[width-4:]
        for l in lines[::-1]:
            self.data.append(l)

    def print(self) -> list:
        """Return all lines for printing if any exist."""
        style = Style.BRIGHT if self.bold else f"{Back.RESET}{Fore.WHITE}{Style.NORMAL}"
        return [f"{style}{l}" for l in self]


class BodyLines(LineGroup):
    """A special LineGroup for the screen body."""
    def __init__(self, parent:Screen, number:bool=True, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parent_screen = parent
        self.number = number
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

        self.selected = items[index-1].ref_obj
        return self.selected

    def print(self) -> list:
        """Return all lines for printing if any exist."""
        lines = []
        start, end = self.get_current_range()
        raw_lines = list(reversed(self.data[start:end]))

        # Append lines
        # Prepend numbers and highlight if selected
        count = 1
        for line in raw_lines:
            to_print = line
            if self.number:
                to_print = f"{Style.DIM}{count:02} {Style.NORMAL}{to_print}"
            if line.ref_obj is self.selected:
                to_print = f"{Fore.CYAN}{to_print}"
            
            lines.append(to_print)
            count += 1

        # Append empty space
        while count <= self.space:
            lines.append(f"{Style.DIM}{count:02}" if self.number else "")
            count += 1
        
        return [str(l) for l in lines]


class Screen:
    """A buffer of lines to print."""
    def __init__(self, name:str, min_body_height:int, numbered:bool, 
    truncate:bool, refresh_func:Callable) -> None:
        # Attributes
        self.name = name
        self.min_body_height = min_body_height
        self.offset = 3 # Page nums, message line, input line
        self.refresh_func = refresh_func

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

    def check_height(self) -> bool:
        """Check to see that the terminal window is tall enough."""
        if t_height() > sum((2, len(self.header), len(self.footer), self.min_body_height)):
            return True
        return False
    
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
    
    def _get_page_range(self) -> tuple[range, str]:
        """Return the range of pages to be displayed and the markings
        on both ends that denote pages preceding or following."""
        max_pages_displayed = t_width() // 8
        prefix, suffix = "   ", "   "

        if self.body.n_pages <= max_pages_displayed:
            return range(1, self.body.n_pages+1), prefix, suffix

        page_sets = self.body.n_pages / max_pages_displayed
        if page_sets.is_integer():
            page_sets = int(page_sets)
        else:
            page_sets = int(page_sets + 1)
        
        for x in range(1, page_sets+1):
            rng = range(max_pages_displayed*(x-1)+1, max_pages_displayed*x+1)
            if self.body.page not in rng:
                continue
            if x < page_sets: suffix = ">>|"
            if x > 1: prefix = "|<<"

            return rng, prefix, suffix
        
    def _print_page_numbers(self) -> list:
        """Return the divider bar with page numbers for printing."""
        style = f"{Back.WHITE}{Fore.BLACK}{Style.BRIGHT}"
        norm = f"{Back.BLACK}{Fore.WHITE}{Style.NORMAL}"
        div_char = " "
        if self.body.n_pages < 2:
            return [f"{style}{div_char*t_width()}"]

        page_range, prefix, suffix = self._get_page_range()

        leading = (t_width() // 2) - (len(page_range)) - (len(prefix+suffix))
        nums = "".join([f" {n} " if n != self.body.page else f"|{n}|" for n in page_range])
        trailing = t_width()-(leading+len(nums))
        
        return [f"{style}{div_char*(leading-2)}{prefix} {nums} {suffix}{div_char*(trailing-6)}"]

    def _print_message_bar(self) -> list:
        """Return the line below the page numbers for printing."""
        style = f"{Back.RESET}{Fore.WHITE}{Style.NORMAL}"
        msg = f"{style}{self.message}{' ' * (t_width() - len(self.message))}"
        self.message = ""
        return [msg]

    def print(self) -> None:
        """Print the contents of the screen to the terminal."""
        # Check the height before printing
        if not self.check_height():
            print("Please increase the height of the terminal window.", end="")
            return
        # Print
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
        screen.clear()
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
        if self._active.refresh_func:
            self._active.refresh_func()
        clear_terminal()
        self._active.print()    


def clear_terminal() -> None:
    # if os.name == "nt":
    #     os.system("cls")
    # else:
    #     os.system("clear")
    pass


def t_width() -> int:
    """Return current terminal width in lines."""
    return os.get_terminal_size()[0]


def t_height() -> int:
    """Return current terminal height in lines."""
    return os.get_terminal_size()[1]


def height_checker() -> None:
    """Check if the screen size has changed, refresh if so."""
    height = t_height()
    while True:
        new_height = t_height()
        if height == new_height:
            continue
        height = new_height
        clear_terminal()
        controller.get_screen().print()
        time.sleep(0.5)


def add_screen(name:str, *, min_body_height:int=1, numbered:bool=False, 
            truncate:bool=False, refresh_func=None) -> None:
    """Public func to add a screen to the controller."""
    if name not in controller._screens:
        screen = Screen(name, min_body_height, numbered, truncate, refresh_func)
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
    controller.get_screen().selected = None
    

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
