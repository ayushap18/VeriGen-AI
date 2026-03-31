"""Live dashboard screen — Bloomberg/Grafana-style real-time panels."""

import time
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Footer
from textual.binding import Binding

from agent.core import AgentConfig, run_agent
from agent.events import StepResult, TaskStart, TaskEnd, RunComplete
from agent.token_tracker import TokenTracker
from dashboard.providers import PROVIDERS, get_pricing
from dashboard.config import VeriGenConfig
from dashboard.widgets.score_panel import ScorePanel
from dashboard.widgets.token_panel import TokenPanel
from dashboard.widgets.task_progress import TaskProgress
from dashboard.widgets.action_feed import ActionFeed
from dashboard.widgets.error_chart import ErrorChart
from dashboard.widgets.score_chart import ScoreChart
from dashboard.widgets.system_info import SystemInfo


class RunScreen(Screen):
    CSS = """
    Screen { background: #0a0a0f; }
    #header {
        dock: top; height: 1;
        background: #1a1a2e; color: #00d4ff; text-style: bold;
        padding: 0 1;
    }
    #metrics-row { height: 5; }
    #chart-row { height: 12; }
    #feed-row { height: 10; }
    #bottom-row { height: auto; }
    """

    BINDINGS = [
        Binding("q", "quit_run", "Quit"),
        Binding("p", "toggle_pause", "Pause/Resume"),
    ]

    def __init__(self, config: VeriGenConfig):
        super().__init__()
        self.config = config
        self.provider_info = PROVIDERS.get(config.provider, {})
        self.pricing = get_pricing(config.provider, config.model)
        self.tracker = TokenTracker(
            cost_per_1m_in=self.pricing["cost_per_1m_in"],
            cost_per_1m_out=self.pricing["cost_per_1m_out"],
        )
        self._paused = False
        self._start_time = time.time()
        self._step_counter = 0
        self._run_result: RunComplete | None = None

    def compose(self) -> ComposeResult:
        yield Static(
            f" VERIGEN-AI  \u2502  {self.config.model}  \u2502  \u25b6 RUNNING",
            id="header"
        )

        with Horizontal(id="metrics-row"):
            yield ScorePanel()
            yield TokenPanel()

        with Horizontal(id="chart-row"):
            yield ScoreChart()
            yield TaskProgress()

        with Horizontal(id="feed-row"):
            yield ActionFeed()

        with Horizontal(id="bottom-row"):
            yield ErrorChart()
            yield SystemInfo()

        yield Footer()

    def on_mount(self):
        system = self.query_one(SystemInfo)
        system.set_info(
            provider=self.provider_info.get("label", self.config.provider),
            model=self.config.model,
            env_url=self.config.env_url
        )

        task_ids = [
            "fix_dates_and_nulls", "dedup_and_normalize",
            "full_pipeline_clean",
            f"generated_{self.config.difficulty}_{self.config.generated_rows}r"
        ]
        self.query_one(TaskProgress).set_tasks(task_ids)

        self.run_worker(self._run_agent, thread=True)
        self.set_interval(1.0, self._tick)

    def _tick(self):
        elapsed = time.time() - self._start_time
        system = self.query_one(SystemInfo)
        system.update_stats(elapsed=elapsed)

        header = self.query_one("#header", Static)
        m, s = divmod(int(elapsed), 60)
        status = "\u23f8 PAUSED" if self._paused else "\u25b6 RUNNING"
        header.update(
            f" VERIGEN-AI  \u2502  {self.config.model}  \u2502  {status}  \u2502  {m}:{s:02d}"
        )

    def _run_agent(self):
        agent_config = AgentConfig(
            api_key=self.config.api_key,
            base_url=self.provider_info.get("base_url", ""),
            model=self.config.model,
            env_url=self.config.env_url,
            gen_rows=self.config.generated_rows,
            gen_difficulty=self.config.difficulty,
        )

        for event in run_agent(agent_config, self.tracker):
            while self._paused:
                time.sleep(0.2)

            if isinstance(event, TaskStart):
                self.call_from_thread(self._handle_task_start, event)
            elif isinstance(event, StepResult):
                self.call_from_thread(self._handle_step, event)
            elif isinstance(event, TaskEnd):
                self.call_from_thread(self._handle_task_end, event)
            elif isinstance(event, RunComplete):
                self._run_result = event
                self.call_from_thread(self._handle_run_complete, event)

    def _handle_task_start(self, event: TaskStart):
        feed = self.query_one(ActionFeed)
        feed.log_message(
            f"--- {event.task_id} ({event.num_rows} rows, {event.max_steps} steps) ---",
            color="#00d4ff"
        )
        self.query_one(TaskProgress).set_active(event.task_id)
        self.query_one(ScorePanel).reset()
        self.query_one(ScoreChart).reset()
        self._step_counter = 0

    def _handle_step(self, event: StepResult):
        self._step_counter += 1

        self.query_one(ScorePanel).update_score(event.score, event.delta)
        self.query_one(TokenPanel).update_tokens(
            self.tracker.total_in, self.tracker.total_out, self.tracker.total_cost
        )
        self.query_one(ScoreChart).add_point(self._step_counter, event.score)
        self.query_one(ActionFeed).log_step(
            step=event.step, action_type=event.action_type,
            target=event.target, score=event.score,
            delta=event.delta, undone=event.undone
        )
        self.query_one(TaskProgress).set_score(event.task_id, event.score)

    def _handle_task_end(self, event: TaskEnd):
        self.query_one(TaskProgress).set_score(event.task_id, event.final_score)
        self.query_one(ErrorChart).update_errors(event.remaining_errors)
        feed = self.query_one(ActionFeed)
        feed.log_message(
            f"  Final: {event.final_score:.4f} in {event.steps_taken} steps",
            color="#00ff88"
        )

    def _handle_run_complete(self, event: RunComplete):
        self.app.run_result = event
        self.app.push_screen("summary")

    def action_quit_run(self):
        self.app.exit()

    def action_toggle_pause(self):
        self._paused = not self._paused
