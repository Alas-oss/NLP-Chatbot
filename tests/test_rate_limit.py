import pytest

from rate_limit import SlidingWindowLimiter


class FakeClock:
    """A controllable clock: .now advances only when the test tells it to."""
    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_allows_up_to_the_limit():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is True


def test_blocks_once_over_the_limit():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False   # third within the window is blocked


def test_a_blocked_call_does_not_count_as_an_event():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    assert limiter.allow() is False
    assert limiter.allow() is False   # still blocked, not "used up" by the previous check


def test_old_events_expire_out_of_the_window():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10, clock=clock)
    assert limiter.allow() is True
    assert limiter.allow() is False
    clock.advance(10.001)   # just past the window
    assert limiter.allow() is True


def test_sliding_not_fixed_bucket_prevents_boundary_burst():
    # If this were a fixed-bucket counter keyed by whole seconds, 2 events at
    # t=9.9 and 2 more at t=10.1 could both fit their own "bucket". A sliding
    # window must still see all 4 within a 10s window as too many.
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=10, clock=clock)
    clock.advance(9.9)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is True
    clock.advance(0.2)   # t=10.1, still within 10s of the first two events
    assert limiter.allow() is False


def test_retry_after_is_zero_when_not_limited():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_events=5, window_seconds=60, clock=clock)
    assert limiter.retry_after() == 0.0


def test_retry_after_counts_down_to_the_oldest_event_expiring():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10, clock=clock)
    limiter.allow()
    clock.advance(4)
    assert limiter.retry_after() == pytest.approx(6.0)
    clock.advance(6)
    assert limiter.retry_after() == 0.0


def test_invalid_construction_rejected():
    with pytest.raises(ValueError):
        SlidingWindowLimiter(max_events=0, window_seconds=10)
    with pytest.raises(ValueError):
        SlidingWindowLimiter(max_events=5, window_seconds=0)
