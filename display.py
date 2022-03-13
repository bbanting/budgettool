import os
from typing import List, Any

import config

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
    def __init__(self, numbered=False, truncate=False) -> None:
        self.lines = []
        self.previous_lines = None
        self.numbered = numbered
        self.truncate = truncate
    
    def pages(self) -> int:
        self.true_height(*os.get_terminal_size())
    
    def push(self, item: Any) -> None:
        self.lines.append(item)

    def true_height(self, width, height) -> int:
        """The number of effective lines, ignoring pagination."""
        count = 0
        for line in self.lines:
            result = len(str(line)) / width
            if result.is_integer():
                count += int(result)
            count += int(result + 1)
        return count if count < (height-2) else (height-2)

    def print(self, max_lines, min_lines=0, page=1) -> None:
        if terminal_size_changed(terminal_size):
            page = 1
        start = (page-1) * max_lines
        end = page * max_lines

        if not self.numbered:
            print("\n".join(reversed(self.lines[start:end])))
        else:
            count = page * self.true_height(*terminal_size)
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


def print_empty_space(width, height) -> None:
    upper_height = screen.true_height(width, height)
    # 2 is for the divider and the input line
    empty_space = height - (upper_height + 2)
    print("\n" * empty_space, end="")


def terminal_size_changed(old_size) -> bool:
    if old_size != (new_size := os.get_terminal_size()):
        old_size = new_size
        return True
    return False


def refresh() -> None:
    width, height = terminal_size

    clear_screen()
    print_empty_space(width, height)
    screen.print(max_lines=height-2, page=1)
    print_divider()


screen = LineBuffer(numbered=True)

for n in range(25):
    screen.push(f"Old MacDonald had a farm {n}")
refresh()
print("> ")
