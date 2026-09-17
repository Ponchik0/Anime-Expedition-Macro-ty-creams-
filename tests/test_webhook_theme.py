"""Тесты оформления вебхуков: отсутствие эмодзи и вывод активных автоматизаций.

Этот тест защищает вебхуки от регрессии:
1. В заголовках и названиях полей не должно быть эмодзи и ии-слопа (чистый Discord-формат).
2. Активные фоновые службы (Shop, Bounty, Crafting, Fuel) должны корректно отображаться блоком Automations.
3. При отсутствии активных служб лишние пустые поля не создаются.
"""
import re
import pytest

from core import stats_report
from core import runner as runner_module
from core import webhook as webhook_module
from core.runner import MacroRunner


# Регулярка для детекции эмодзи и лишних иконок в тексте
_EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]"
)


def _runner_with_stats(monkeypatch, sent, custom_stats=None):
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = runner.logs.append
    stats = {
        "session_wins": 5, "session_losses": 1,
        "all_time_wins": 20, "all_time_losses": 4,
        "session_start": None, "runs_per_hour": "7.5", "time_until_challenge": "15m",
        "version": "2.0.0", "results": [],
    }
    if custom_stats:
        stats.update(custom_stats)
    runner._get_run_stats = lambda: stats

    def send_rich(url, embeds=None, file_attachments=None, content="", silent=False):
        sent.append({"embeds": embeds, "content": content})
        return {"ok": True, "reason": ""}

    monkeypatch.setattr(webhook_module, "send_rich", send_rich)
    monkeypatch.setattr(runner_module, "cv2", None, raising=False)
    return runner


def test_webhook_result_embed_has_no_emojis(monkeypatch):
    """Проверяем, что в заголовке, полях и описании вебхука результата матча нет эмодзи."""
    sent = []
    runner = _runner_with_stats(monkeypatch, sent)
    webhook = {"url": "https://discord.com/api/webhooks/1/t", "enabled": True}
    task = {"mode": "story", "map": "King's Tomb", "stage": "1", "macro": "starter"}

    runner._send_result_webhook(webhook, "win", task, "3m 12s", None, None)

    assert sent, "Уведомление не было отправлено"
    embed = sent[0]["embeds"][0]

    # Проверяем title
    assert not _EMOJI_PATTERN.search(embed.get("title", "")), f"Эмодзи в title: {embed.get('title')}"
    # Проверяем имена полей
    for f in embed.get("fields", []):
        assert not _EMOJI_PATTERN.search(f["name"]), f"Эмодзи в поле {f['name']}"
        # Проверяем значение Result
        if f["name"] == "Match":
            assert "Victory" in f["value"]
            assert not _EMOJI_PATTERN.search(f["value"])


def test_automations_field_appears_when_services_are_active():
    """Когда включены фоновые сервисы, в эмбеде появляется компактное поле Automations."""
    stats = {
        "session_wins": 1, "session_losses": 0,
        "all_time_wins": 1, "all_time_losses": 0,
        "automations": {
            "Shop": "Active",
            "Bounty": "Mythic · 5/10",
            "Crafting": "Every 20",
            "Fuel": "Active",
        }
    }
    fields = stats_report.report_fields("Match", [("Result", "Victory")], stats)
    auto_field = next((f for f in fields if f["name"] == "Automations"), None)

    assert auto_field is not None, "Поле Automations должно отображаться при активных сервисах"
    assert auto_field["inline"] is True
    assert "Shop" in auto_field["value"]
    assert "Bounty" in auto_field["value"]
    assert "Crafting" in auto_field["value"]
    assert "Fuel" in auto_field["value"]


def test_automations_field_omitted_when_no_services_are_active():
    """Если все сервисы выключены, поле Automations не должно мусорить в эмбеде."""
    stats = {
        "session_wins": 1, "session_losses": 0,
        "all_time_wins": 1, "all_time_losses": 0,
        "automations": {}
    }
    fields = stats_report.report_fields("Match", [("Result", "Victory")], stats)
    auto_field = next((f for f in fields if f["name"] == "Automations"), None)

    assert auto_field is None, "Поле Automations не должно отображаться, если сервисы не активны"


def test_status_embed_has_no_emojis():
    """Периодическая сводка статуса не должна содержать эмодзи в заголовке и полях."""
    embed = stats_report.status_embed(
        {"session_wins": 2, "session_losses": 1},
        window_seconds=3600,
        window_wins=2,
        window_losses=1,
        now_rows=[("Статус", "в бою")]
    )

    assert not _EMOJI_PATTERN.search(embed.get("title", "")), f"Эмодзи в title: {embed.get('title')}"
    for f in embed.get("fields", []):
        assert not _EMOJI_PATTERN.search(f["name"]), f"Эмодзи в поле {f['name']}"
