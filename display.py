import os
import logging
from typing import List, Any, Iterable

import config

logging.basicConfig(level=logging.DEBUG, filename="log.txt", filemode="w", encoding="utf-8")

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
    def __init__(self, numbered:bool=False, truncate:bool=False, offset:int=0) -> None:
        self.body: Iterable = []
        self.header = []
        self.footer = []
        self.numbered: int = numbered
        self.truncate: bool = truncate
        self.offset: int = abs(offset)
        self._page: int = 1
    
    @property
    def page_height(self) -> int:
        return t_height() - self.offset - len(self.header) - len(self.footer)

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
    
    def add_line(self, item: Any) -> None:
        self.body.append(item)

    def add_header(self, item: Any) -> None:
        self.header.append(item)

    def add_footer(self, item: Any) -> None:
        self.footer.append(item)

    def replace_lines(self, new_lines: List, reset_page=True) -> None:
        if not hasattr(new_lines, "__iter__"):
            raise DisplayError("new_lines must be an iterable.")
        self.body = new_lines
        if reset_page:
            self._page = 1

    def clear(self):
        self.body.clear()
        self.header.clear()
        self.footer.clear()

    def _true_lines(self) -> int:
        """The number of effective lines, ignoring pagination."""
        width, height = os.get_terminal_size()
        count = 0
        for line in self.body:
            result = len(str(line)) / width
            if result.is_integer():
                count += int(result)
            count += int(result + 1)
        return count

    def _print_filler(self):
        # print("hi")
        # if not self._page == self.pages:
        #     return
        filled_lines = self._true_lines() - (self.page_height * (self._page - 1))
        empty_space = self.page_height - filled_lines
        # if self.header:
        #     empty_space -= len(self.header)
        print("\n" * empty_space, end="")

    def _print_header(self):
        for line in self.header:
            print(line)

    def _print_footer(self):
        for line in self.footer:
            print(line)
    
    def _print_page_numbers(self, div_char: str="-"):
        if not self.body:
            print("\n")
            return
        leading = (t_width() // 2) - (self.pages // 2)
        nums = " ".join([str(n) for n in range(1, self.pages+1)])
        indicator = [" " for _ in range(self.pages)]
        indicator[self._page-1] = "^"
        indicator = " ".join(indicator)
        trailing = t_width()-(leading+len(nums))
        print(f"{div_char*(leading-3)}// {nums} //{div_char*(trailing-3)}")
        print(" "*leading, indicator, sep="")

    def print(self, min_items=4) -> None:
        """Print the contents of the buffer to the """
        self._print_filler()
        self._print_header()
        self.body = self.body[::-1]
        start = (self._page-1) * self.page_height
        end = self._page * self.page_height

        count = self.page_height
        if self.is_last_page():
            count = len(self.body) - ((self.pages-1) * self.page_height)
        for line in reversed(self.body[start:end]):
            to_print = str(line)
            if self.numbered:
                to_print = f"{count:<2} {to_print}"
                count -= 1
            if self.truncate:
                to_print = to_print[:t_width()]
            print(to_print)
        
        self._print_footer()
        self._print_page_numbers()

    def select(self, index: int) -> Any:
        if index < 1:
            return
        return self.body[::-1][index-1]


def clear_terminal() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def terminal_size_changed(old_size) -> bool:
    if old_size != (new_size := os.get_terminal_size()):
        old_size = new_size
        return True
    return False


def t_width():
    return os.get_terminal_size()[0]


def t_height():
    return os.get_terminal_size()[1]


def configure_screen(numbered:bool=False, truncate:bool=False, offset:int=0):
    """Public function for creating and initializing the screen."""
    screen.__init__(numbered=numbered, truncate=truncate, offset=offset)


def refresh() -> None:
    """Clear the terminal and print the current state of the screen."""
    # screen.clear()
    clear_terminal()
    screen.print()


screen = LineBuffer()

# configure_screen(numbered=True, truncate=True, offset=4)
# for n in range(30):
#     screen.add_line(f"Old MacDonald had a farm {n+1}")
# screen.change_page(3)
# refresh()
# print(screen.select(3))
# print("> ")