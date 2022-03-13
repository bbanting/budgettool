import os
import logging
from typing import List, Any

import config

logging.basicConfig(level=logging.DEBUG)

# Widths for display columns
IDW = 8
DATEW = 8
AMOUNTW = 10
TAGSW = 12
NOTEW = None

terminal_size = os.get_terminal_size()


class DisplayError(Exception):
    pass


class LineBuffer:
    def __init__(self, numbered:bool=False, truncate:bool=False, offset:int=0) -> None:
        self.lines = []
        self.previous_lines = None
        self.numbered = numbered
        self.truncate = truncate
        self.offset = abs(offset)
        self._page = 1
    
    @property
    def page_height(self) -> int:
        return os.get_terminal_size()[1] - self.offset

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
            self._page - page   
    
    def push(self, item: Any) -> None:
        self.lines.append(item)

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
        if terminal_size_changed(terminal_size):
            self._page = 1
        start = (self._page-1) * self.page_height
        end = self._page * self.page_height

        if not self.numbered:
            print("\n".join(reversed(self.lines[start:end])))
        else:
            count = self._page * self.page_height
            if self._page == self.pages: # Last page
                count = self._true_lines()
            for line in reversed(self.lines[start:end]):
                print(f"{count:<2} {line}")
                count -= 1
       
        # self.previous_contents = self
        self.lines.clear()

    def select(self, id: int) -> Any:
        return self.lines[::-1][id]


def clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def print_divider(char: str="-") -> None:
    print(char * (os.get_terminal_size()[0] - 1))


def terminal_size_changed(old_size) -> bool:
    if old_size != (new_size := os.get_terminal_size()):
        old_size = new_size
        return True
    return False


def refresh() -> None:
    width, height = terminal_size

    clear_screen()
    screen._print_filler()
    screen._print()
    print_divider()


screen = LineBuffer(numbered=True, offset=2)

for n in range(30):
    screen.push(f"Old MacDonald had a farm {n}")
refresh()
print("> ")
