"""Live dashboard screen — Bloomberg Terminal style, all panels."""

import time
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Input, Static
from textual.binding import Binding

from agent.core import AgentConfig, run_agent
from agent.events import StepResult, TaskStart, TaskEnd, RunComplete
from agent.token_tracker import TokenTracker
from dashboard.providers import PROVIDERS, get_pricing
from dashboard.config import VeriGenConfig
from dashboard.widgets.status_bar import StatusBar
from dashboard.widgets.ticker_bar import TickerBar
from dashboard.widgets.score_panel import ScorePanel
from dashboard.widgets.token_panel import TokenPanel
from dashboard.widgets.task_progress import TaskProgress
from dashboard.widgets.action_feed import ActionFeed
from dashboard.widgets.error_chart import ErrorChart
from dashboard.widgets.score_chart import ScoreChart
from dashboard.widgets.system_info import SystemInfo
from dashboard.widgets.agent_chat import AgentChat
from dashboard.widgets.task_history import TaskHistory
from dashboard.widgets.perf_monitor import PerfMonitor
from dashboard.widgets.matrix_panel import MatrixPanel
from dashboard.widgets.pie_chart import PieChart
from dashboard.widgets.action_summary import ActionSummary


class RunScreen(Screen):
    CSS = """
    Screen { background: #020502; }

    /* === MAIN SPLIT === */
    #main-body { height: 1fr; }
    #left-col { width: 3fr; }
    #right-col { width: 2fr; border-left: solid #1a3a1a; }

    /* === LEFT COLUMN ROWS === */
    #metrics-row { height: 8; }
    ScorePanel { width: 1fr; }
    TokenPanel { width: 1fr; }
    SystemInfo { width: 1fr; }

    #mid-section { height: 1fr; min-height: 14; }
    ScoreChart { width: 1fr; }
    ActionFeed { width: 1fr; }

    #bottom-section { height: auto; min-height: 14; max-height: 24; }
    #bottom-left-col { width: 1fr; }
    TaskProgress { height: auto; }
    ActionSummary { height: 1fr; min-height: 6; }
    #bottom-right-col { width: 1fr; }
    ErrorChart { height: auto; max-height: 10; }
    PieChart { height: auto; max-height: 10; }
    TaskHistory { height: auto; max-height: 10; }

    /* === RIGHT COLUMN === */
    AgentChat { height: 1fr; min-height: 10; }
    #chat-input {
        height: 3;
        border: solid #1a3a1a;
        background: #0a1a0a;
        color: #00ff88;
    }
    #chat-input:focus { border: solid #00ff88; }
    #right-panels { height: auto; min-height: 16; max-height: 22; }
    PerfMonitor { height: auto; min-height: 12; }
    MatrixPanel { height: 8; }
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
        self._tasks_done = 0
        self._total_tasks = 4
        self._current_score = 0.0
        self._run_result: RunComplete | None = None
        # Track task IDs the agent actually reports
        self._reported_tasks: set[str] = set()

    def compose(self) -> ComposeResult:
        yield StatusBar()

        with Horizontal(id="main-body"):
            # LEFT: Main dashboard
            with Vertical(id="left-col"):
                with Horizontal(id="metrics-row"):
                    yield ScorePanel()
                    yield TokenPanel()
                    yield SystemInfo()

                with Horizontal(id="mid-section"):
                    yield ScoreChart()
                    yield ActionFeed()

                with Horizontal(id="bottom-section"):
                    with Vertical(id="bottom-left-col"):
                        yield TaskProgress()
                        yield ActionSummary()
                    with Vertical(id="bottom-right-col"):
                        yield ErrorChart()
                        yield PieChart()
                        yield TaskHistory()

            # RIGHT: Agent chat + monitors
            with Vertical(id="right-col"):
                yield AgentChat()
                yield Input(
                    placeholder="Ask the agent... (Enter to send)",
                    id="chat-input"
                )
                with Vertical(id="right-panels"):
                    yield PerfMonitor()
                    yield MatrixPanel()

        yield TickerBar()
        yield Footer()

    def on_mount(self):
        task_ids = self._get_task_ids()
        self._total_tasks = len(task_ids)

        self.query_one(StatusBar).set_config(
            model=self.config.model,
            provider=self.provider_info.get("label", self.config.provider),
            total_tasks=self._total_tasks,
        )

        self.query_one(SystemInfo).set_info(
            provider=self.provider_info.get("label", self.config.provider),
            model=self.config.model,
            env_url=self.config.env_url
        )

        self.query_one(TaskProgress).set_tasks(task_ids)

        self.query_one(TickerBar).set_items([
            "\u25b2 VERIGEN-AI",
            f"MODEL: {self.config.model}",
            "STATUS: ONLINE",
            f"TASKS: 0/{self._total_tasks}",
            "SCORE: 0.0000",
        ])

        if self.config.csv_path:
            self.query_one(AgentChat).log_decision(
                f"CSV loaded: {self.config.csv_path}"
            )

        self.run_worker(self._run_agent, thread=True)
        # High-frequency real-time updates
        self.set_interval(1.0, self._tick)
        self.set_interval(0.5, self._perf_tick)
        self.set_interval(0.3, self._matrix_tick)
        self.set_interval(0.5, self._ticker_tick)

    def _get_task_ids(self) -> list[str]:
        """Return task IDs matching what the agent core will actually run."""
        return [
            "fix_dates_and_nulls", "dedup_and_normalize",
            "full_pipeline_clean",
            f"generated_{self.config.difficulty}_{self.config.generated_rows}r"
        ]

    def _tick(self):
        elapsed = time.time() - self._start_time
        self.query_one(SystemInfo).update_stats(elapsed=elapsed)
        self.query_one(StatusBar).update_stats(
            elapsed=elapsed,
            tokens=self.tracker.total_in + self.tracker.total_out,
            cost=self.tracker.total_cost,
            status="PAUSED" if self._paused else "RUNNING",
        )

    def _perf_tick(self):
        try:
            self.query_one(PerfMonitor).tick()
        except Exception:
            pass

    def _matrix_tick(self):
        try:
            self.query_one(MatrixPanel).tick()
        except Exception:
            pass

    def _ticker_tick(self):
        try:
            self.query_one(TickerBar).scroll_tick()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            msg = event.value.strip()
            if not msg:
                return
            event.input.value = ""
            self.query_one(AgentChat).log_user_msg(msg)
            self.run_worker(
                lambda: self._handle_chat_message(msg),
                thread=True
            )

    def _handle_chat_message(self, msg: str):
        from openai import OpenAI
        try:
            client = OpenAI(
                base_url=self.provider_info.get("base_url", ""),
                api_key=self.config.api_key,
            )
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": (
                        "You are VeriGen-AI, a data cleaning agent. "
                        "Answer questions about data cleaning, your progress, "
                        "strategies, or data topics. Keep answers concise (2-3 sentences)."
                    )},
                    {"role": "user", "content": msg}
                ],
                max_tokens=256,
                temperature=0.3
            )
            reply = response.choices[0].message.content.strip()
            tokens_in = getattr(response.usage, "prompt_tokens", 0)
            tokens_out = getattr(response.usage, "completion_tokens", 0)
            self.tracker.record(tokens_in, tokens_out)
            self.app.call_from_thread(
                lambda: self.query_one(AgentChat).log_agent_reply(reply)
            )
        except Exception as e:
            self.app.call_from_thread(
                lambda: self.query_one(AgentChat).log_error(f"Chat error: {e}")
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
                self.app.call_from_thread(self._handle_task_start, event)
            elif isinstance(event, StepResult):
                self.app.call_from_thread(self._handle_step, event)
            elif isinstance(event, TaskEnd):
                self.app.call_from_thread(self._handle_task_end, event)
            elif isinstance(event, RunComplete):
                self._run_result = event
                self.app.call_from_thread(self._handle_run_complete, event)

    def _handle_task_start(self, event: TaskStart):
        # If agent reports a task ID we don't have in the queue, add it
        if event.task_id not in self._reported_tasks:
            self._reported_tasks.add(event.task_id)
            tp = self.query_one(TaskProgress)
            if event.task_id not in tp._tasks:
                tp._tasks.append(event.task_id)
                tp._rebuild()

        self.query_one(ActionFeed).log_message(
            f"\u2550\u2550\u2550 {event.task_id} "
            f"({event.num_rows}r \u00d7 {event.num_columns}c, "
            f"{event.max_steps} steps) \u2550\u2550\u2550",
            color="#00ff88"
        )

        self.query_one(AgentChat).log_task_start(
            event.task_id, event.num_rows,
            event.num_columns, event.column_types
        )

        self.query_one(TaskProgress).set_active(event.task_id)
        self.query_one(ScorePanel).reset()
        self.query_one(ScoreChart).reset()
        self.query_one(ActionSummary).reset()
        self._step_counter = 0
        self._current_score = 0.0
        self.query_one(StatusBar).update_stats(score=0.0)

    def _handle_step(self, event: StepResult):
        self._step_counter += 1
        self._current_score = event.score

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
        self.query_one(ActionSummary).record_action(
            event.action_type, event.delta, event.undone
        )

        self.query_one(AgentChat).log_thinking(
            event.task_id, event.step, event.action_type,
            event.target, event.new_value
        )
        self.query_one(AgentChat).log_score_change(event.score, event.delta)
        if event.undone:
            self.query_one(AgentChat).log_error(
                "Action undone \u2014 score dropped, reverting"
            )

        self.query_one(StatusBar).update_stats(
            score=event.score,
            tokens=self.tracker.total_in + self.tracker.total_out,
            cost=self.tracker.total_cost,
        )

        delta_arrow = "\u25b2" if event.delta >= 0 else "\u25bc"
        self.query_one(TickerBar).set_items([
            f"\u25c8 {event.task_id}",
            f"STEP {event.step}",
            f"{delta_arrow} SCORE: {event.score:.4f} ({'+' if event.delta >= 0 else ''}{event.delta:.4f})",
            f"TOKENS: {self.tracker.total_in + self.tracker.total_out:,}",
            f"COST: ${self.tracker.total_cost:.4f}",
            f"TASKS: {self._tasks_done}/{self._total_tasks}",
            f"TPS: {(self.tracker.total_in + self.tracker.total_out) / max(1, time.time() - self._start_time):.1f}",
        ])

    def _handle_task_end(self, event: TaskEnd):
        self._tasks_done += 1
        self.query_one(TaskProgress).set_score(event.task_id, event.final_score)
        self.query_one(ErrorChart).update_errors(event.remaining_errors)
        self.query_one(PieChart).update_data(event.remaining_errors or {})

        self.query_one(ActionFeed).log_message(
            f"  \u2713 Final: {event.final_score:.4f} in {event.steps_taken} steps",
            color="#00ff88"
        )
        self.query_one(AgentChat).log_success(
            f"Task complete: {event.final_score:.4f} in {event.steps_taken} steps"
        )

        errors_left = sum(event.remaining_errors.values()) if event.remaining_errors else 0
        self.query_one(TaskHistory).add_result(
            event.task_id, event.final_score, event.steps_taken, errors_left
        )

        self.query_one(StatusBar).update_stats(
            tasks_done=self._tasks_done, score=event.final_score,
        )

    def _handle_run_complete(self, event: RunComplete):
        self.app.run_result = event
        self.app.push_screen("summary")

    def action_quit_run(self):
        self.app.exit()

    def action_toggle_pause(self):
        self._paused = not self._paused
