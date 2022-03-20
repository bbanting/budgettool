import os
import logging
from typing import List, Any, Iterable

import config

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")

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
        self.used = False
    
    @property
    def body_height(self) -> int:
        page_nums = 2
        header_footer = len(self.header) + len(self.footer)
        height = t_height() - self.offset - page_nums - header_footer
        if height < 1: 
            raise DisplayError("Terminal window is too short.")
        return height

    @property
    def n_pages(self) -> int:
        lines = self._true_lines()
        pages = lines / self.body_height
        if pages.is_integer():
            pages = int(pages)
        else:
            pages = int(pages + 1)
        return pages if pages else 1

    def change_page(self, page: int) -> None:
        if 0 < page <= self.n_pages:
            self._page = page
        if page > self.n_pages:
            self._page = self.n_pages

    def is_last_page(self) -> bool:
        if self._page == self.n_pages:
            return True
        return False
    
    def add_line(self, item: Any) -> None:
        if self.used:
            self.used = False
            self.clear()
        self.body.append(item)

    def add_header(self, item: Any) -> None:
        if self.used:
            self.used = False
            self.clear()
        self.header.append(item)

    def add_footer(self, item: Any) -> None:
        if self.used:
            self.used = False
            self.clear()
        self.footer.append(item)

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
        # if not self._page == self.pages:
        #     return
        filled_lines = self._true_lines() - (self.body_height * (self._page - 1))
        empty_space = self.body_height - filled_lines
        print("\n" * empty_space, end="")

    def _print_header(self):
        for line in self.header:
            print(line[:t_width()])

    def _print_footer(self):
        for line in self.footer:
            print(line[:t_width()])
    
    def _get_page_range(self) -> tuple[range, str]:
        max_pages_displayed = t_width() // 8
        prefix, suffix = "|||", "|||"

        if self.n_pages <= max_pages_displayed:
            return range(1, self.n_pages+1), prefix, suffix

        page_sets = self.n_pages / max_pages_displayed
        if page_sets.is_integer():
            page_sets = int(page_sets)
        else:
            page_sets = int(page_sets + 1)
        
        for x in range(1, page_sets+1):
            rng = range(max_pages_displayed*(x-1)+1, max_pages_displayed*x+1)
            if self._page not in rng:
                continue
            if x < page_sets: suffix = ">>|"
            if x > 1: prefix = "|<<"

            return rng, prefix, suffix
        

    def _print_page_numbers(self, div_char:str="-",):
        page_range, prefix, suffix = self._get_page_range()

        leading = (t_width() // 2) - (len(page_range)) - (len(prefix+suffix))
        nums = " ".join([str(n) for n in page_range])
        indicator = [" " for _ in range(len(nums))] or [" "]
        indicator[nums.find(str(self._page))] = "^"
        indicator = "".join(indicator)
        trailing = t_width()-(leading+len(nums))
        print(f"{div_char*(leading-4)}{prefix} {nums} {suffix}{div_char*(trailing-4)}")
        print(" "*(leading), indicator, sep="")

    def print(self, min_items=4) -> None:
        """Print the contents of the buffer to the """
        self._print_filler()
        self._print_header()
        self.body = self.body[::-1]
        start = (self._page-1) * self.body_height
        end = self._page * self.body_height

        count = self.body_height
        if self.is_last_page():
            count = len(self.body) - ((self.n_pages-1) * self.body_height)
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
        self.used = True

    def select(self, index: int) -> Any:
        start = (self._page-1) * self.body_height
        end = self._page * self.body_height
        items = self.body[start:end]
        if index > len(items) or index < 1:
            raise IndexError("Invalid selection.")
        return items[index-1]


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
    clear_terminal()
    screen.print()


screen = LineBuffer()

if __name__ == "__main__":
    configure_screen(numbered=True, truncate=True, offset=1)
    for n in range(80):
        screen.add_line(f"Old MacDonald had a farm {n+1}")
    screen.change_page(38)
    refresh()
    print(screen.select(1))
    print("> ")