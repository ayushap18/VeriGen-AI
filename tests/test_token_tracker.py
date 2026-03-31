from agent.token_tracker import TokenTracker


def test_initial_state():
    t = TokenTracker(cost_per_1m_in=0.15, cost_per_1m_out=0.60)
    assert t.total_in == 0
    assert t.total_out == 0
    assert t.total_cost == 0.0


def test_record_usage():
    t = TokenTracker(cost_per_1m_in=0.15, cost_per_1m_out=0.60)
    t.record(tokens_in=1000, tokens_out=100)
    assert t.total_in == 1000
    assert t.total_out == 100
    assert t.total_cost > 0


def test_accumulates():
    t = TokenTracker(cost_per_1m_in=0.15, cost_per_1m_out=0.60)
    t.record(tokens_in=500, tokens_out=50)
    t.record(tokens_in=500, tokens_out=50)
    assert t.total_in == 1000
    assert t.total_out == 100


def test_cost_calculation():
    t = TokenTracker(cost_per_1m_in=1.0, cost_per_1m_out=1.0)
    t.record(tokens_in=1_000_000, tokens_out=1_000_000)
    assert abs(t.total_cost - 2.0) < 0.001


def test_reset():
    t = TokenTracker(cost_per_1m_in=0.15, cost_per_1m_out=0.60)
    t.record(tokens_in=1000, tokens_out=100)
    t.reset()
    assert t.total_in == 0
    assert t.total_cost == 0.0
