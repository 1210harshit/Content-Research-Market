"""Tests for source policy decisions and source skipping."""

from __future__ import annotations

from course_market_intelligence.source_policy import evaluate, is_mode_allowed


def test_linkedin_blocks_public_scraping():
    res = evaluate("linkedin.com", "public_metadata")
    assert res.allowed is False
    assert "public_metadata" in res.blocked_modes


def test_linkedin_allows_manual_csv():
    assert is_mode_allowed("linkedin.com", "manual_csv") is True


def test_youtube_requires_api_not_scraping():
    assert is_mode_allowed("youtube.com", "youtube_data_api") is True
    assert is_mode_allowed("youtube.com", "public_metadata") is False


def test_google_search_api_allowed_scraping_blocked():
    assert is_mode_allowed("google.com", "search_api") is True
    assert is_mode_allowed("google.com", "public_metadata") is False


def test_udemy_affiliate_api_allowed():
    assert is_mode_allowed("udemy.com", "affiliate_api") is True


def test_unknown_domain_defaults_least_privilege():
    res = evaluate("some-random-site.example", "official_api")
    # official_api not in defaults -> blocked
    assert res.allowed is False
    assert is_mode_allowed("some-random-site.example", "search_api") is True


def test_subdomain_matches_parent_policy():
    assert is_mode_allowed("api.udemy.com", "affiliate_api") is True


def test_safe_next_step_present_when_blocked():
    res = evaluate("linkedin.com", "public_metadata")
    assert res.safe_next_step
