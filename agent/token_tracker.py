"""Tracks token usage and cost across LLM calls."""


class TokenTracker:
    def __init__(self, cost_per_1m_in: float = 0.15, cost_per_1m_out: float = 0.60):
        self.cost_per_1m_in = cost_per_1m_in
        self.cost_per_1m_out = cost_per_1m_out
        self.total_in = 0
        self.total_out = 0
        self.total_cost = 0.0

    def record(self, tokens_in: int, tokens_out: int):
        self.total_in += tokens_in
        self.total_out += tokens_out
        cost_in = (tokens_in / 1_000_000) * self.cost_per_1m_in
        cost_out = (tokens_out / 1_000_000) * self.cost_per_1m_out
        self.total_cost += cost_in + cost_out

    def reset(self):
        self.total_in = 0
        self.total_out = 0
        self.total_cost = 0.0
