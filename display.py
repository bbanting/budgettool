import collections
import os
from typing import List, Any

import config

# Widths for display columns
IDW = 8
DATEW = 8
AMOUNTW = 10
TAGSW = 12
NOTEW = None


class DisplayError(Exception):
    pass


class LineBuffer(collections.UserList):
    def __init__(self, numbered=False) -> None:
        super().__init__()
        self.previous_contents = None
        self.numbered = numbered
    
    def push(self, item: Any) -> None:
        self.append(item)

    def real_height(self) -> int:
        width, height = os.get_terminal_size()
        count = 0
        for line in self:
            result = len(str(line)) / width
            if result.is_integer():
                count += int(result)
            count += int(result + 1)
        return count

    def print(self, max_height=None) -> None:
        self.previous_contents = self
        if not self.numbered:
            print("\n".join(self))
        else:
            count = len(self)
            for line in self:
                print(f"{count:<2} {line}")
                count -= 1            
        self.clear()

    def select(self, id: int) -> Any:
        return list(reversed(upper_lines))[id]


def clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def print_divider(char: str = "-") -> None:
    print(char * (os.get_terminal_size()[0] - 1))


def print_empty_space() -> None:
    width, height = os.get_terminal_size()
    upper_height = upper_lines.real_height()
    lower_height = lower_lines.real_height()
    empty_space = height - (lower_height + upper_height + 2)
    if empty_space > 0:
        print("\n" * empty_space)


def refresh() -> None:
    width, height = os.get_terminal_size()
    clear_screen()
    print_empty_space()
    upper_lines.print()
    print_divider()
    lower_lines.print()


upper_lines = LineBuffer(numbered=True)
lower_lines = LineBuffer()

lower_lines.push("Hello terminal")
upper_lines.push("Old MacDonald had a farm")
upper_lines.push("On that farm he had a dog")
upper_lines.push("On that farm he had a pig")
lower_lines.push(upper_lines.select(1))
refresh()
