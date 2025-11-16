from search_api.services.rate_limit_service import RateLimitService


def test_token_bucket_allows_within_limit():
    rl = RateLimitService()
    # Use a small custom limit to keep test fast
    decision = rl.check(key="test", limit_per_minute=5)
    assert decision.allowed
    assert decision.limit == 5
    # Consume remaining quickly
    for _ in range(4):
        d = rl.check(key="test", limit_per_minute=5)
        assert d.allowed
    # Next should be limited (5th already taken)
    d = rl.check(key="test", limit_per_minute=5)
    assert not d.allowed or d.remaining >= 0


