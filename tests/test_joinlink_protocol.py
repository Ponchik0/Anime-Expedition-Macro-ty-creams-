"""Tests for core/joinlink.py to_roblox_protocol and link normalization.

Catches regressions where web URLs (https://www.roblox.com/...) were passed to
os.startfile directly, causing Windows to open a browser window that steals focus
and breaks macro execution.
"""
from core import joinlink


def test_to_roblox_protocol_standard_game():
    """https:// game links must be converted to roblox:// experiences start URI."""
    url = "https://www.roblox.com/games/84515722934860/Anime-Expeditions"
    assert joinlink.to_roblox_protocol(url) == "roblox://experiences/start?placeId=84515722934860"


def test_to_roblox_protocol_private_server():
    """https:// private server links must include linkCode in the roblox:// URI."""
    url = "https://www.roblox.com/games/84515722934860/Anime-Expeditions?privateServerLinkCode=123456789"
    assert joinlink.to_roblox_protocol(url) == "roblox://experiences/start?placeId=84515722934860&linkCode=123456789"


def test_to_roblox_protocol_share_link():
    """https:// share links must be converted to roblox:// navigation share_links URI."""
    url = "https://www.roblox.com/share?code=abcdef&type=Server"
    assert joinlink.to_roblox_protocol(url) == "roblox://navigation/share_links?code=abcdef&type=Server"


def test_to_roblox_protocol_preserves_roblox_uri():
    """Existing roblox:// protocol URIs should be returned as-is."""
    uri = "roblox://experiences/start?placeId=84515722934860&linkCode=999"
    assert joinlink.to_roblox_protocol(uri) == uri


def test_get_join_link_converts_http_settings(monkeypatch):
    """get_join_link must always return a roblox:// protocol URI."""
    monkeypatch.setattr(
        joinlink.cfg, "load",
        lambda: {"private_server_link": "https://www.roblox.com/games/84515722934860/Game?privateServerLinkCode=abc"})
    assert joinlink.get_join_link() == "roblox://experiences/start?placeId=84515722934860&linkCode=abc"
