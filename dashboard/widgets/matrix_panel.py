"""Matrix-style cascading rain animation — full real-time effect."""

import random
from textual.widgets import Static


class MatrixPanel(Static):
    DEFAULT_CSS = """
    MatrixPanel {
        height: 8;
        background: #020502;
        padding: 0;
        border: solid #1a3a1a;
        overflow: hidden;
    }
    """

    def __init__(self):
        super().__init__("[#0a4a0a]SYSTEM ACTIVE[/#0a4a0a]")
        self._width = 30
        self._height = 6
        self._chars = "0123456789ABCDEF<>{}[]|/\\@#$%&*=+~^"
        self._columns: list[list[str]] = []
        self._drops: list[int] = []
        self._init_rain()

    def _init_rain(self):
        self._columns = []
        self._drops = []
        for _ in range(self._width):
            col = [" "] * self._height
            self._columns.append(col)
            self._drops.append(random.randint(-self._height, 0))

    def tick(self):
        # Advance each rain drop
        for i in range(self._width):
            self._drops[i] += 1
            drop_pos = self._drops[i]

            # Reset drop when it falls off screen
            if drop_pos - 4 > self._height:
                self._drops[i] = random.randint(-4, 0)
                self._columns[i] = [" "] * self._height
                continue

            # Place characters at and behind the drop head
            for row in range(self._height):
                dist = drop_pos - row
                if dist == 0:
                    self._columns[i][row] = random.choice(self._chars)
                elif 0 < dist <= 3:
                    if random.random() < 0.7:
                        self._columns[i][row] = random.choice(self._chars)
                elif dist > 3:
                    if random.random() < 0.15:
                        self._columns[i][row] = " "

        # Render
        lines = []
        for row in range(self._height):
            parts = []
            for col in range(self._width):
                ch = self._columns[col][row]
                if ch == " ":
                    parts.append(" ")
                    continue
                drop_pos = self._drops[col]
                dist = drop_pos - row
                if dist == 0:
                    parts.append(f"[#ffffff bold]{ch}[/#ffffff bold]")
                elif dist == 1:
                    parts.append(f"[#00ff88 bold]{ch}[/#00ff88 bold]")
                elif dist <= 3:
                    parts.append(f"[#00cc66]{ch}[/#00cc66]")
                elif dist <= 5:
                    parts.append(f"[#0a8a2a]{ch}[/#0a8a2a]")
                else:
                    parts.append(f"[#0a4a0a]{ch}[/#0a4a0a]")
            lines.append("".join(parts))
        self.update("\n".join(lines))
