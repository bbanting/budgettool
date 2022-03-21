import os
import logging
from typing import List, Any, Iterable


logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class DisplayError(Exception):
    pass


class LineBuffer:
    """"""
    def __init__(self, numbered:bool=True, truncate:bool=True, offset:int=0) -> None:
        self.body: Iterable = []
        self.header = []
        self.footer = []
        self.numbered: int = numbered
        self.truncate: bool = truncate
        self.offset: int = abs(offset)
        self.page: int = 1
        self.printed = False
    
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
        if 0 < page <= self.n_pages:
            self.page = page
        if page > self.n_pages:
            self.page = self.n_pages
    
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
        self.page = 1

    def select(self, index: int) -> Any:
        """Return an item by line number from the current page."""
        start = -(self.page * self.body_space)
        end = start + self.body_space
        if end > -1: end = None
        items = self.body[start:end][::-1]
        if index > len(items) or index < 1:
            raise IndexError("Invalid selection.")
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

    def _print_filler(self):
        """Print the space between the last body line and the header."""
        if not self.page == self.n_pages:
            return
        filled_lines = self.true_lines() - (self.body_space * (self.page - 1))
        empty_space = self.body_space - filled_lines
        print("\n" * empty_space, end="")

    def _print_header(self):
        """Print the header."""
        for line in self.header:
            print(line[:t_width()])

    def _print_footer(self):
        """Print the footer."""
        for line in self.footer:
            print(line[:t_width()])
    
    def _get_page_range(self) -> tuple[range, str]:
        """Return the range of pages to be displayed and the markings
        on both ends that denote pages preceding or following."""
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
            if self.page not in rng:
                continue
            if x < page_sets: suffix = ">>|"
            if x > 1: prefix = "|<<"

            return rng, prefix, suffix
        
    def _print_page_numbers(self, div_char:str="-",) -> None:
        """Print the divider bar with page numbers."""
        page_range, prefix, suffix = self._get_page_range()

        leading = (t_width() // 2) - (len(page_range)) - (len(prefix+suffix))
        nums = " ".join([str(n) for n in page_range])
        indicator = [" " for _ in range(len(nums))] or [" "]
        indicator[nums.find(str(self.page))] = "^"
        indicator = "".join(indicator)
        trailing = t_width()-(leading+len(nums))
        print(f"{div_char*(leading-4)}{prefix} {nums} {suffix}{div_char*(trailing-4)}")
        print(" "*(leading), indicator, sep="")

    def _print_body(self) -> None:
        """Print the body."""
        index = self.page * self.body_space

        count = self.body_space
        if self.page == self.n_pages:
            count = len(self.body) - ((self.n_pages-1) * self.body_space)
        for line in self.body[-index:]:
            to_print = str(line)
            if self.numbered:
                to_print = f"{count:<2} {to_print}"
                count -= 1
            if self.truncate:
                to_print = to_print[:t_width()]

            print(to_print)
            if count == 0:
                break

    def print(self) -> None:
        """Print the contents of the buffer to the terminal."""
        self._print_filler()
        self._print_header()
        self._print_body()
        self._print_footer()
        self._print_page_numbers()
        self.printed = True


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


def push(item:Any, target:str="body") -> None:
    """Push an item to 'body', 'header', or 'footer'."""
    if target not in ("body", "header", "footer"):
        raise DisplayError("Invalid push target.")
    buffer.push(item, target=target)


def select(index) -> Any:
    """Return an item by line number from the current view in screen."""
    return buffer.select(index)


def configure(numbered:bool=False, truncate:bool=False, offset:int=0):
    """Public function for modifying current buffer."""
    buffer.__init__(numbered=numbered, truncate=truncate, offset=offset)


def refresh() -> None:
    """Clear the terminal and print the current state of the screen."""
    clear_terminal()
    buffer.print()


buffer = LineBuffer()

if __name__ == "__main__":
    configure(numbered=True, truncate=True, offset=1)
    for n in range(80):
        buffer.push(f"Old MacDonald had a farm {n+1}")
    buffer.change_page(1)
    refresh()
    print(buffer.select(3))
    print("> ")