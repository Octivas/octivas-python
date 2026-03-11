"""Tests for the RateLimitError credit-limit properties."""

from octivas.exceptions import RateLimitError


class TestRateLimitErrorCreditInfo:
    """RateLimitError should expose credits_used and credits_limit from the body."""

    def test_parses_credits_from_detail_dict(self):
        err = RateLimitError(
            "Credit limit exceeded",
            status_code=429,
            body={
                "detail": {
                    "error": "Credit limit exceeded",
                    "credits_used": 1000,
                    "credits_limit": 1000,
                }
            },
        )
        assert err.credits_used == 1000
        assert err.credits_limit == 1000

    def test_parses_credits_from_flat_body(self):
        err = RateLimitError(
            "Credit limit exceeded",
            status_code=429,
            body={
                "credits_used": 500,
                "credits_limit": 1000,
            },
        )
        assert err.credits_used == 500
        assert err.credits_limit == 1000

    def test_returns_none_when_no_credit_info(self):
        err = RateLimitError(
            "Rate limited",
            status_code=429,
            body={"error": "Too many requests"},
        )
        assert err.credits_used is None
        assert err.credits_limit is None

    def test_returns_none_when_body_is_none(self):
        err = RateLimitError("Rate limited", status_code=429, body=None)
        assert err.credits_used is None
        assert err.credits_limit is None

    def test_returns_none_when_no_body_kwarg(self):
        err = RateLimitError("Rate limited")
        assert err.credits_used is None
        assert err.credits_limit is None

    def test_credits_coerced_to_int(self):
        err = RateLimitError(
            "Credit limit exceeded",
            status_code=429,
            body={"detail": {"credits_used": "42", "credits_limit": "100"}},
        )
        assert err.credits_used == 42
        assert err.credits_limit == 100
        assert isinstance(err.credits_used, int)
        assert isinstance(err.credits_limit, int)
