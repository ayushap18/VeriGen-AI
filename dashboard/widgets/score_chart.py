"""Score trend line chart using plotext."""

try:
    from textual_plotext import PlotextPlot

    class ScoreChart(PlotextPlot):
        DEFAULT_CSS = """
        ScoreChart {
            height: 12;
            border: solid #2a2a4a;
            background: #0f0f1a;
        }
        """

        def __init__(self):
            super().__init__()
            self._scores: list[float] = []
            self._steps: list[int] = []

        def on_mount(self):
            self._draw()

        def add_point(self, step: int, score: float):
            self._steps.append(step)
            self._scores.append(score)
            self._draw()

        def reset(self):
            self._scores = []
            self._steps = []
            self._draw()

        def _draw(self):
            plt = self.plt
            plt.clear_data()
            plt.clear_figure()
            plt.theme("dark")
            plt.canvas_color((10, 10, 26))
            plt.axes_color((10, 10, 26))
            plt.ticks_color((102, 102, 170))

            if self._scores:
                plt.plot(self._steps, self._scores, color=(0, 255, 136), marker="braille")
                plt.ylim(0, 1.05)
            plt.title("Score Trend")
            plt.xlabel("Step")
            plt.ylabel("Score")
            self.refresh()

except ImportError:
    from textual.widgets import Static

    class ScoreChart(Static):  # type: ignore[no-redef]
        DEFAULT_CSS = """
        ScoreChart {
            height: 12;
            border: solid #2a2a4a;
            background: #0f0f1a;
            padding: 0 1;
        }
        """

        def __init__(self):
            super().__init__("Score chart requires textual-plotext")
            self._scores: list[float] = []

        def add_point(self, step: int, score: float):
            self._scores.append(score)
            blocks = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
            spark = "".join(blocks[min(int(s * 8), 8)] for s in self._scores[-40:])
            self.update(f"SCORE TREND\n{spark}")

        def reset(self):
            self._scores = []
            self.update("Score Trend")
