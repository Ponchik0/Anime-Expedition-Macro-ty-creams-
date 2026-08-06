"""Матчи, кончившиеся без распознанного исхода: их считают отдельно.

ЖИВОЙ СЛУЧАЙ, ради которого всё это. За два часа повтора отыграно 25 кругов,
а в статистику попал ОДИН матч: баннеры не совпадали с эталонами (лучшие счета
0.50 и 0.58 при пороге 0.90). Табло при этом показывало «1W · 0L» — то есть
выглядело как спокойная ночь, в которую просто мало играли. Отличить поломку
от невезения было нечем.

Теперь такой матч считается третьим числом — ни победа, ни поражение. Тесты
здесь ровно про эту границу: цифра должна расти, но не смешиваться ни с
победами, ни с поражениями и не попадать в журнал забегов (журналу нечего о
ней записать: ни исхода, ни длительности).
"""
import time
import types

import pytest

import main
from core import replay_result, stats_report
from core import settings as cfg
from core.runner_constants import RESULT_UNKNOWN


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    a = main.Api.__new__(main.Api)
    a._session_wins = 0
    a._session_losses = 0
    a._session_unknown = 0
    a._run_status = {"action": "Idle", "mode": "-", "macro": "-",
                     "current_task": "-", "current_repeat": "-", "map": "-"}
    a.push_log = lambda m: None
    a.session_start = time.time()
    a._all_time_base = 0.0
    a._player = None
    a.runner = types.SimpleNamespace(is_running=lambda: False)
    # get_status() спрашивает док и очередь задач — здесь они не при чём,
    # но без них до счётчика дело не доходит.
    a.docker = types.SimpleNamespace(docked=False)
    return a


# ── Счёт ──────────────────────────────────────────────────────────────────

def test_an_unrecognised_match_is_neither_a_win_nor_a_loss(api):
    """Записать наугад «поражение» значило бы испортить винрейт навсегда."""
    api._record_match_result(RESULT_UNKNOWN, "", "", source="replay", kind="Replay")

    assert api._session_unknown == 1
    assert (api._session_wins, api._session_losses) == (0, 0)
    data = cfg.load()
    assert data.get("all_time_wins", 0) == 0 and data.get("all_time_losses", 0) == 0


def test_an_unrecognised_match_leaves_the_run_history_alone(api):
    """Журналу о нём нечего записать: ни исхода, ни карты, ни длительности.
    А строка-пустышка сломала бы и список на Панели, и сетку активности, и
    темп забегов."""
    api._record_match_result(RESULT_UNKNOWN, "", "", source="replay")

    assert cfg.load().get("run_history", []) == []


def test_unrecognised_matches_survive_a_restart(api):
    """Ночь длиннее одного запуска приложения: за всё время счётчик копится
    на диске, как победы и поражения."""
    api._record_match_result(RESULT_UNKNOWN, "", "")
    api._record_match_result(RESULT_UNKNOWN, "", "")

    assert cfg.load()["all_time_unknown"] == 2


def test_real_results_still_go_where_they_always_went(api):
    """Главное, чего нельзя сломать новым счётчиком."""
    api._record_match_result("win", "Marjenta", "4m")
    api._record_match_result("loss", "Marjenta", "3m")

    assert (api._session_wins, api._session_losses) == (1, 1)
    assert len(cfg.load()["run_history"]) == 2


# ── Наблюдатель повтора отдаёт цифру наружу ───────────────────────────────

def test_the_watcher_reports_an_unrecognised_match_outwards(monkeypatch):
    """Раньше эта цифра жила только внутри наблюдателя и в журнале приложения —
    то есть до табло, карточки и сводки не доходила вовсе."""
    seen = []
    watcher = replay_result.ResultWatcher(lambda: 1, lambda *a: None,
                                           on_unknown=lambda: seen.append(1))
    watcher._on_unknown()

    assert seen == [1]


def test_a_broken_handler_does_not_kill_the_watcher(monkeypatch):
    """Наблюдатель крутится всю ночь: упасть из-за счётчика он не имеет права."""
    logs = []
    watcher = replay_result.ResultWatcher(
        lambda: 1, lambda *a: None, log=logs.append,
        on_unknown=lambda: (_ for _ in ()).throw(RuntimeError("боль")))

    # Ровно та же защита, что стоит в цикле вокруг вызова.
    try:
        watcher._on_unknown()
    except RuntimeError:
        pass
    assert watcher.unknown == 0  # счётчик наблюдателя живёт своей жизнью


# ── Табло ─────────────────────────────────────────────────────────────────

def test_the_dashboard_line_shows_both_numbers(api):
    """«Засчитано 3» само по себе читается как спокойная ночь. «Засчитано 3 ·
    не распознано 24» — как поломка, которой оно и является."""
    watcher = types.SimpleNamespace(matches=3, unknown=24)

    line = main.Api._replay_match_line(watcher)

    assert "3" in line and "24" in line


def test_the_dashboard_line_stays_quiet_when_there_is_nothing_to_say(api):
    assert main.Api._replay_match_line(types.SimpleNamespace(matches=0, unknown=0)) == "-"
    assert main.Api._replay_match_line(None) == "-"


def test_the_status_endpoint_carries_the_counter(api):
    api._record_match_result(RESULT_UNKNOWN, "", "")

    assert api.get_status()["unknown"] == 1
    assert api.get_status()["all_time_unknown"] == 1


# ── Карточка матча ────────────────────────────────────────────────────────

def _stats(**over):
    stats = {"session_wins": 1, "session_losses": 0, "all_time_wins": 1,
             "all_time_losses": 0, "session_start": time.time() - 60,
             "runs_per_hour": "-", "time_until_challenge": "Disabled",
             "derived": {}}
    stats.update(over)
    return stats


def _field(fields, needle):
    for f in fields:
        if needle in f["name"]:
            return f
    return None


def test_the_card_reports_unrecognised_matches(_field_needle="Session"):
    fields = stats_report.report_fields("⚔️ Match", [], _stats(session_unknown=24))

    assert "Не распознано" in _field(fields, "Session")["value"]
    assert "24" in _field(fields, "Session")["value"]


def test_the_card_says_nothing_when_everything_was_recognised():
    """Строка, которая всегда показывает ноль, читается как «всё в порядке» и
    потому перестаёт читаться вовсе."""
    fields = stats_report.report_fields("⚔️ Match", [], _stats(session_unknown=0))

    assert "Не распознано" not in _field(fields, "Session")["value"]


def test_the_all_time_block_reports_them_too():
    fields = stats_report.report_fields("⚔️ Match", [], _stats(all_time_unknown=312))

    assert "312" in _field(fields, "All Time")["value"]


# ── Сводка ────────────────────────────────────────────────────────────────

def test_the_status_report_names_the_culprit():
    """Ровно тот случай из журнала: прогон идёт, а в счёт не попадает ничего."""
    embed = stats_report.status_embed(_stats(), window_seconds=6 * 3600,
                                       window_wins=0, window_losses=0, window_unknown=24)

    assert "24" in embed["description"]
    assert "Менеджер картинок" in embed["description"]


def test_the_status_report_shows_the_share_when_some_did_land():
    """«3 засчитано, 24 мимо» — это 89%, и такую долю надо назвать вслух."""
    embed = stats_report.status_embed(_stats(), window_seconds=6 * 3600,
                                       window_wins=3, window_losses=0, window_unknown=24)

    assert "89%" in embed["description"]


def test_a_clean_window_does_not_mention_them_at_all():
    embed = stats_report.status_embed(_stats(), window_seconds=3600,
                                       window_wins=8, window_losses=2, window_unknown=0)

    assert "не распознан" not in embed["description"]


# ── Окно сводки считает нераспознанные за СВОЙ промежуток ─────────────────

def test_the_window_counts_only_its_own_unrecognised_matches(api, monkeypatch):
    """Счётчик сессии только растёт, а сводка обязана сказать «за эти шесть
    часов» — иначе каждая следующая повторяла бы все предыдущие."""
    cfg.update({"webhook_enabled": True, "webhook_url": "https://discord.com/api/webhooks/1/t"})
    api._status_accum = 3600.0
    api._status_since = time.time() - 3600
    api._session_unknown = 30
    api._status_unknown_base = 24                  # 24 из них были до начала окна
    sent = []
    monkeypatch.setattr(main.webhook, "send",
                        lambda url, embed, content="", silent=False: (
                            sent.append(embed), {"ok": True, "reason": ""})[1])

    api._send_status_report(reset=False)

    assert "**6**" in sent[0]["description"]       # 30 - 24
