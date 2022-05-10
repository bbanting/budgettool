import os
import logging

from typing import Any, Callable

import colorama
from colorama import Fore, Back, Style


logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")
colorama.init(autoreset=True)


class DisplayError(Exception):
    pass


class LineBuffer:
    """A buffer of lines to print."""
    def __init__(self, name:str, numbered:bool, truncate:bool, offset:int, refresh_func:Callable) -> None:
        # Attributes
        self.name = name
        self.numbered = numbered
        self.truncate = truncate
        self.offset= abs(offset)
        self.refresh_func= refresh_func

        # Sub-buffers & state
        self.body= []
        self.header= []
        self.footer= []

        self._page = 1
        self.printed = False
        self.highlight = 0
        self.message = ""
    
    @property
    def body_space(self) -> int:
        """Return the height in lines of the available space for the body."""
        page_nums = 2
        header_footer = len(self.header) + len(self.footer)
        height = t_height() - self.offset - page_nums - header_footer
        if height < 1: 
            raise DisplayError("Terminal window is too short.")
        return height

    @property
    def page(self) -> int:
        if 0 < self._page <= self.n_pages:
           return self._page
        elif self._page > self.n_pages:
            return self.n_pages

    @property
    def n_pages(self) -> int:
        """Return the total number of pages."""
        lines = self.true_lines()
        pages = lines / self.body_space
        if pages.is_integer():
            pages = int(pages)
        else:
            pages = int(pages + 1)
        return pages if pages else 1

    def change_page(self, page: int) -> None:
        """Change which page to display."""
        if page != self.page:
            self.highlight = 0
        if page < 1:
            return
        self._page = page
    
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

    def select(self, index: int) -> Any:
        """Return an item by line number from the current page."""
        start = -(self.page * self.body_space)
        end = start + self.body_space
        if end > -1: end = None
        items = self.body[start:end][::-1]
        if index > len(items) or index < 1:
            raise DisplayError("Invalid line selection.")

        self.highlight = index
        return items[index-1]

    def true_lines(self) -> int:
        """The number of total effective lines in the body.
        This function is not useful right now but may be in the future.
        """
        if self.truncate:
            return len(self.body)
        width = t_width()
        count = 0
        for line in self.body:
            result = len(str(line)) / width
            if result.is_integer():
                count += int(result)
            count += int(result + 1)
        return count

    def _print_header(self) -> None:
        """Print the header."""
        for line in self.header:
            style = f"{Back.WHITE}{Fore.BLACK}{Style.BRIGHT}"
            lpadding = " " * 3
            line = line[:(t_width()-len(lpadding))]
            rpadding = " " * (t_width() - len(lpadding + line))
            print(f"{style}{lpadding}{line}{rpadding}")

    def _print_filler(self) -> None:
        """Print the space between the last body line and the header."""
        if not self.page == self.n_pages:
            return
        filled_lines = self.true_lines() - (self.body_space * (self.page - 1))
        empty_space = self.body_space - filled_lines
        count = self.body_space
        for _ in range(empty_space):
            num = f"{count:02}" if self.numbered else ""
            print(Style.DIM + num)
            count -= 1

    def _print_footer(self) -> None:
        """Print the footer."""
        for line in self.footer:
            print(line[:t_width()])

    def _print_body(self) -> None:
        """Print the body."""
        index = self.page * self.body_space
        count = self.body_space
        if self.page == self.n_pages:
            count = len(self.body) - ((self.n_pages-1) * self.body_space)
        for line in self.body[-index:]:
            to_print = str(line)
            if self.numbered:
                num = f"{count:02}"
                to_print = f"{Style.DIM}{num} {Style.NORMAL}{to_print}"
            if self.truncate:
                to_print = to_print[:t_width()]
            if count+1 == self.highlight:
                to_print = Fore.CYAN + to_print
            count -= 1
            
            print(to_print)
            if count == 0:
                break
    
    def _get_page_range(self) -> tuple[range, str]:
        """Return the range of pages to be displayed and the markings
        on both ends that denote pages preceding or following."""
        max_pages_displayed = t_width() // 8
        prefix, suffix = "   ", "   "

        if self.n_pages <= max_pages_displayed:
            return range(1, self.n_pages+1), prefix, suffix

        page_sets = self.n_pages / max_pages_displayed
        if page_sets.is_integer():
            page_sets = int(page_sets)
        else:
            page_sets = int(page_sets + 1)
        
        for x in range(1, page_sets+1):
            rng = range(max_pages_displayed*(x-1)+1, max_pages_displayed*x+1)
            if self.page not in rng:
                continue
            if x < page_sets: suffix = ">>|"
            if x > 1: prefix = "|<<"

            return rng, prefix, suffix
        
    def _print_page_numbers(self, div_char:str="-",) -> None:
        """Print the divider bar with page numbers."""
        style = f"{Back.WHITE}{Fore.BLACK}{Style.BRIGHT}"
        div_char = " "
        if self.n_pages < 2:
            print(f"{style}{div_char*t_width()}", end="\n")
            return

        page_range, prefix, suffix = self._get_page_range()

        leading = (t_width() // 2) - (len(page_range)) - (len(prefix+suffix))
        nums = "".join([f" {n} " if n != self.page else f"|{n}|" for n in page_range])
        trailing = t_width()-(leading+len(nums))
        print(f"{style}{div_char*(leading-2)}{prefix} {nums} {suffix}{div_char*(trailing-6)}")

    def _print_message_bar(self) -> None:
        """Print the line below the page numbers."""
        print(self.message)
        self.message = ""

    def print(self) -> None:
        """Print the contents of the buffer to the terminal."""
        self._print_header()
        self._print_filler()
        self._print_body()
        self._print_footer()
        self._print_page_numbers()
        self._print_message_bar()
        self.printed = True


class ScreenController:
    """A class to switch to and from multiple buffers."""
    _active: LineBuffer
    _screens: dict[str, LineBuffer]

    def __init__(self):
        self._screens = {}

    def add(self, name:str, numbered:bool, truncate:bool, offset:int, refresh_func:Callable) -> None:
        """Add a screen to the list."""
        self._screens.update({name: LineBuffer(name, numbered, truncate, offset, refresh_func)})
        if len(self._screens) == 1:
            self._active = self._screens[name]

    def switch_to(self, name:str) -> None:
        """Switch the active screen."""
        if name not in self._screens:
            raise DisplayError("A screen with that name does not exist.")
        self._active = self._screens[name]


def clear_terminal() -> None:
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


def push(*items:Any) -> None:
    """Push an item to body."""
    for item in items:
        get_screen().push(item)

def push_h(*items:Any) -> None:
    """Push an item to header."""
    for item in items:
        get_screen().push(item, target="header")

def push_f(*items:Any) -> None:
    """Push an item to footer."""
    for item in items:
        get_screen().push(item, target="footer")


def message(text:str) -> None:
    get_screen().message = text


def select(index) -> Any:
    """Return an item by line number from the current view in screen."""
    return get_screen().select(index)


def deselect() -> None:
    """Remove the highlight."""
    get_screen().highlight = 0


def change_page(number:int) -> None:
    "Change the page of the active screen."
    get_screen().change_page(number)


def error(error) -> None:
    clear_terminal()
    get_screen().clear()
    message(str(error))


def add_screen(name:str, *, numbered:bool=False, truncate:bool=True, offset:int=0, refresh_func=None) -> None:
    """Public func to add a screen to the controller."""
    controller.add(name, numbered, truncate, offset, refresh_func)


def switch_screen(name:str) -> None:
    """Public func to switch the active screen."""
    for k, v in controller._screens.items():
        if k == name:
            continue
        v.clear()
    controller.switch_to(name)


def get_screen(name:str = None) -> LineBuffer:
    """Get the active screen."""
    if not controller._screens:
        raise DisplayError("No screens have been created.")
    if screen := controller._screens.get(name):
        return screen
    return controller._active


def refresh() -> None:
    """Clear the terminal and print the current state of the screen."""
    if get_screen().refresh_func:
        get_screen().refresh_func()
    clear_terminal()
    get_screen().print()


controller = ScreenController()


if __name__ == "__main__":
    add_screen("main", offset=1, numbered=True)
    add_screen("notmain", offset=1, numbered=False)
    switch_screen("notmain")
    for n in range(80):
        push(f"Old MacDonald had a farm {n+1}")
    change_page(4)
    select(3)
    refresh()
    print("> ")
    