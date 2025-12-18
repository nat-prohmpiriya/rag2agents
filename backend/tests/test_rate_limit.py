"""Tests for rate limiting functionality."""

from unittest.mock import MagicMock

from app.core.rate_limit import RateLimits, get_client_ip


class TestGetClientIP:
    """Test client IP extraction."""

    def test_direct_connection(self):
        """Test IP from direct connection."""
        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_forwarded_for_single(self):
        """Test IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "10.0.0.1"}
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_forwarded_for_chain(self):
        """Test IP from X-Forwarded-For header with proxy chain."""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "10.0.0.1, 10.0.0.2, 10.0.0.3"}
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        # Should return the first (original client) IP
        assert ip == "10.0.0.1"

    def test_real_ip_header(self):
        """Test IP from X-Real-IP header."""
        request = MagicMock()
        request.headers = {"x-real-ip": "10.0.0.5"}
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        assert ip == "10.0.0.5"

    def test_forwarded_for_takes_precedence(self):
        """Test that X-Forwarded-For takes precedence over X-Real-IP."""
        request = MagicMock()
        request.headers = {
            "x-forwarded-for": "10.0.0.1",
            "x-real-ip": "10.0.0.5",
        }
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        assert ip == "10.0.0.1"


class TestRateLimits:
    """Test rate limit configurations."""

    def test_auth_limits_are_strict(self):
        """Test that auth endpoints have stricter limits."""
        # Parse rate limit strings
        login_limit = int(RateLimits.AUTH_LOGIN.split("/")[0])
        register_limit = int(RateLimits.AUTH_REGISTER.split("/")[0])
        default_limit = int(RateLimits.API_DEFAULT.split("/")[0])

        # Auth limits should be stricter than default
        assert login_limit < default_limit
        assert register_limit < default_limit
        assert register_limit <= login_limit  # Register should be same or stricter

    def test_limit_format(self):
        """Test that all limits have valid format."""
        limits = [
            RateLimits.AUTH_LOGIN,
            RateLimits.AUTH_REGISTER,
            RateLimits.AUTH_REFRESH,
            RateLimits.AUTH_FORGOT_PASSWORD,
            RateLimits.API_DEFAULT,
            RateLimits.API_CHAT,
            RateLimits.API_UPLOAD,
        ]

        for limit in limits:
            # Should be in format "N/period"
            parts = limit.split("/")
            assert len(parts) == 2
            assert parts[0].isdigit()
            assert parts[1] in ["second", "minute", "hour", "day"]
