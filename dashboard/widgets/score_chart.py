"""Score trend line chart using plotext — Bloomberg green theme."""

try:
    from textual_plotext import PlotextPlot

    class ScoreChart(PlotextPlot):
        DEFAULT_CSS = """
        ScoreChart {
            height: 100%;
            border: solid #1a3a1a;
            background: #050a05;
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
            plt.canvas_color((5, 10, 5))
            plt.axes_color((5, 10, 5))
            plt.ticks_color((58, 106, 58))

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
            height: 100%;
            border: solid #1a3a1a;
            background: #050a05;
            padding: 0 1;
        }
        """

        def __init__(self):
            super().__init__("[#00ff88 bold]\u25c9 SCORE TREND[/#00ff88 bold]")
            self._scores: list[float] = []

        def add_point(self, step: int, score: float):
            self._scores.append(score)
            blocks = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
            spark = "".join(
                f"[#00ff88]{blocks[min(int(s * 8), 8)]}[/#00ff88]"
                for s in self._scores[-50:]
            )
            self.update(
                f"[#00ff88 bold]\u25c9 SCORE TREND[/#00ff88 bold]\n"
                f"  {spark}\n"
                f"  [#3a6a3a]Samples: {len(self._scores)}[/#3a6a3a]"
            )

        def reset(self):
            self._scores = []
            self.update("[#00ff88 bold]\u25c9 SCORE TREND[/#00ff88 bold]")
