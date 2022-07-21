"""A module for custom screens."""
from colorama import Back, Fore, Style

from kelevsma.display import BodyLines, Screen, Line, t_width
from util import dollar_str


class TargetGraphBody(BodyLines):
    """Replaces Screen body to print targets in graph format."""
    def prepare_lines(self) -> list[Line]:
        """Prepare the lines for the graph."""
        # FIX: Width of 145 causes glitch
        width = int(t_width() * .75)
        if odd_width := (width % 2):
            width -= 1
        margin = (t_width() - width) // 2
        max_bar_len = width // 2
        extreme = max([abs(t.current_total) for t in self])

        # Loop through targets and format them as Lines
        lines = []
        for t in self:
            total = t.current_total
            total_str = dollar_str(total)
            ratio = (abs(total) / extreme) if total else 0
            bar_len = int(max_bar_len * ratio) if int(max_bar_len * ratio) else 1
            style = Back.RED if t.failing() else Back.GREEN

            if total < 0:
                name = f"{t.name} {Style.DIM}({dollar_str(t.goal)}){Style.NORMAL}"
                lpadding = " " * (max_bar_len-bar_len)
                if len(total_str) <= bar_len:
                    bar = f"{style}{total_str}{' ' * (bar_len-len(total_str))}{Back.RESET}"
                elif len(total_str) <= len(lpadding):
                    bar = f"{total_str}{style}{' ' * (bar_len)}{Back.RESET}"
                    lpadding = " " * (max_bar_len-bar_len-len(total_str))
                else:
                    bar = f"{style}{' ' * bar_len}{Back.RESET}"
                rpadding = " " * (max_bar_len - len(name) + len(Style.DIM + Style.NORMAL))
                lhalf = f"{lpadding}{bar}"
                rhalf = f"{name}{rpadding}"
            elif total > 0:
                name = f"{Style.DIM}({dollar_str(t.goal)}){Style.NORMAL} {t.name}"
                lpadding = " " * (max_bar_len - len(name) + len(Style.DIM + Style.NORMAL))
                rpadding = " " * (max_bar_len-bar_len)
                if len(total_str) <= bar_len:
                    bar = f"{style}{' ' * (bar_len-len(total_str))}{total_str}{Back.RESET}"
                elif len(total_str) <= len(rpadding):
                    bar = f"{style}{' ' * (bar_len)}{Back.RESET}{total_str}"
                    rpadding = " " * (max_bar_len-bar_len-len(total_str))
                lhalf = f"{lpadding}{name}"
                rhalf = f"{bar}{rpadding}"
            else:
                name = f"{t.name} {Style.DIM}({dollar_str(t.goal)}){Style.NORMAL}"
                lhalf = " " * max_bar_len
                rhalf = name + (" " * (max_bar_len - len(name)))

            lines.append(Line(t, f"{' ' * margin}{lhalf}{rhalf}{' ' * odd_width}"))
        
        return lines

    def print(self) -> list[str]:
        """Return all lines for printing if any exist."""
        lines = self.prepare_lines()
        to_print = [l.text for l in lines]
        to_print.append("\n" * (self.space - len(self) - 1))
        
        return to_print


class GraphScreen(Screen):
    """A screen with a graph for the body."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.body = TargetGraphBody(self)
