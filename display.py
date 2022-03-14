import os
import logging
from typing import List, Any, Iterable

import config

logging.basicConfig(level=logging.DEBUG)

# Widths for display columns
IDW = 8
DATEW = 8
AMOUNTW = 10
TAGSW = 12
NOTEW = None


class DisplayError(Exception):
    pass


class LineBuffer:
    """"""
    def __init__(self, numbered:bool=False, truncate:bool=False, offset:int=0, divider: str="") -> None:
        self.lines: Iterable = []
        self.numbered: int = numbered
        self.truncate: bool = truncate
        self.offset: int = abs(offset)
        self._page: int = 1
        self.divider = divider
    
    @property
    def page_height(self) -> int:
        return t_height() - self.offset

    @property
    def pages(self) -> int:
        lines = self._true_lines() - 1
        pages = lines / self.page_height
        if pages.is_integer():
            pages = int(pages)
        else:
            pages = int(pages + 1)
        return pages

    def change_page(self, page: int) -> None:
        if 0 < page <= self.pages:
            self._page = page
        if page > self.pages:
            self._page = self.pages

    def is_last_page(self) -> bool:
        if self._page == self.pages:
            return True
        return False
    
    def push(self, item: Any) -> None:
        self.lines.append(item)

    def replace_lines(self, new_lines: List, reset_page=True) -> None:
        if not hasattr(new_lines, "__iter__"):
            raise DisplayError("new_lines must be an iterable.")
        self.lines = new_lines
        if reset_page:
            self._page = 1

    def clear(self, container_type=list):
        self.lines = container_type()

    def _true_lines(self) -> int:
        """The number of effective lines, ignoring pagination."""
        width, height = os.get_terminal_size()
        count = 0
        for line in self.lines:
            result = len(str(line)) / width
            if result.is_integer():
                count += int(result)
            count += int(result + 1)
        return count

    def _print_filler(self):
        if not self._page == self.pages:
            return
        filled_lines = self._true_lines() - (self.page_height * (self._page - 1))
        empty_space = self.page_height - filled_lines
        print("\n" * empty_space, end="")

    def _print(self, min_lines=0) -> None:
        """Print the contents of the buffer to the """
        self._print_filler()

        start = (self._page-1) * self.page_height
        end = self._page * self.page_height

        count = self._page * self.page_height
        if self.is_last_page():
            count = len(self.lines)
        for line in reversed(self.lines[start:end]):
            to_print = str(line)
            if self.numbered:
                to_print = f"{count:<2} {to_print}"
                count -= 1
            if self.truncate:
                to_print = to_print[:t_width()]
            print(to_print)
        
        self._print_page_numbers()
        if self.divider:
             _print_divider(self.divider)
    
    def _print_page_numbers(self):
        pos = (t_width() // 2) - (self.pages // 2)
        nums = " ".join([str(n) for n in range(1, self.pages+1)])
        indicator = [" " for _ in range(self.pages)]
        indicator[self._page-1] = "^"
        indicator = " ".join(indicator)
        print(" "*pos, nums)
        print(" "*pos, indicator)

    def select(self, id: int) -> Any:
        return self.lines[::-1][id]


def clear_terminal() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def _print_divider(char: str="-") -> None:
    print(char * (t_width()), end="\n")


def terminal_size_changed(old_size) -> bool:
    if old_size != (new_size := os.get_terminal_size()):
        old_size = new_size
        return True
    return False


def t_width():
    return os.get_terminal_size()[0]


def t_height():
    return os.get_terminal_size()[1]


def make_screen(numbered:bool=False, truncate:bool=False, offset:int=0, divider: str=""):
    """Public function for creating and initializing the screen."""
    global _screen
    _screen = LineBuffer(numbered=numbered, truncate=truncate, offset=offset, divider=divider)


def refresh() -> None:
    """Clear the terminal and print the current state of the screen."""
    if _screen is None:
        raise DisplayError("Screen not initialized.")
    clear_terminal()
    _screen._print()
    # screen.clear()


_screen = None

make_screen(numbered=True, truncate=True, offset=4, divider="-")
for n in range(30):
    _screen.push(f"Old MacDonald had a farm {n}")
_screen.change_page(5)
refresh()

print("> ")
