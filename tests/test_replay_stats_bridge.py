"""МОСТ «ПОВТОР → СТАТИСТИКА»: история, счётчики, табло, очистка.

Забег, отыгранный повтором, должен попадать туда же, куда и забег автомата:
в историю, в счётчики сессии и всех времён, в табло на Панели. Отличать его от
автомата надо по одному полю в строке истории (`source`), а не по догадке из
названия карты.

Настоящих Windows-вызовов здесь нет: тест про то, что происходит с числами.
"""
import types

import pytest

import main
from core import settings as cfg


@pytest.fixture
def api(tmp_path, monkeypatch):
    """Api с настройками во временном файле и без единого потока."""
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    a = main.Api.__new__(main.Api)                 # без __init__: он поднимает окно и потоки
    a._session_wins = 0
    a._session_losses = 0
    a._run_status = {"action": "Idle", "mode": "-", "macro": "-",
                     "current_task": "-", "current_repeat": "-", "map": "-"}
    a.push_log = lambda m: None
    a.session_start = 0.0
    return a


def _history():
    return cfg.load().get("run_history", [])


def test_a_replay_win_lands_in_history_marked_as_replay(api):
    api._record_match_result("win", "Запись «забег»", "3m 1s", source="replay")

    rows = _history()
    assert len(rows) == 1
    assert rows[0]["result"] == "win"
    assert rows[0]["source"] == "replay"
    assert rows[0]["map"] == "Запись «забег»"


def test_the_auto_run_stays_the_default_source(api):
    """Автомат зовёт _record_match_result без source — и это по-прежнему
    «auto», иначе старый вызов молча помечал бы забеги неправильно."""
    api._record_match_result("loss", "Marjenta", "2m 0s")
    assert _history()[0]["source"] == "auto"


def test_replay_results_count_in_both_session_and_all_time(api):
    """Повтор считается ровно как автомат: отдельной статистики у него нет —
    иначе табло на Панели показывало бы одно, а история другое."""
    api._record_match_result("win", "Запись «забег»", "1m", source="replay")
    api._record_match_result("win", "Marjenta", "1m")
    api._record_match_result("loss", "Запись «забег»", "1m", source="replay")

    assert (api._session_wins, api._session_losses) == (2, 1)
    data = cfg.load()
    assert data["all_time_wins"] == 2
    assert data["all_time_losses"] == 1


def test_old_history_without_source_reads_as_auto(api):
    """Забеги, записанные до появления поля, — автоматические: режима повтора
    тогда просто не было. Панель не должна спотыкаться об их отсутствие."""
    cfg.update({"run_history": [{"result": "win", "map": "Marjenta",
                                  "duration": "1m", "at": 1_700_000_000.0}]})
    api.get_challenge_settings = lambda: {}
    api.docker = types.SimpleNamespace(docked=False)
    rows = api.get_status()["run_history"]
    assert rows[0]["source"] == "auto"


# ── Очистка ───────────────────────────────────────────────────────────────

def test_clearing_wipes_history_and_both_counters(api):
    """Одной кнопкой — и журнал, и счётчики. Обнулить журнал, оставив «312
    побед за всё время», значит получить табло, которое не сходится ни с чем
    на экране."""
    api._record_match_result("win", "Marjenta", "1m")
    api._record_match_result("loss", "Marjenta", "1m", source="replay")

    assert api.clear_run_history()["ok"]

    assert _history() == []
    assert (api._session_wins, api._session_losses) == (0, 0)
    data = cfg.load()
    assert data["all_time_wins"] == 0 and data["all_time_losses"] == 0


# ── Табло на Панели ───────────────────────────────────────────────────────

def _player(**kw):
    base = {"running": True, "countdown_ms": 0.0, "state": "running", "index": 5,
            "total": 100, "name": "забег", "loop_num": 2}
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_the_status_says_what_the_start_button_will_do(api):
    """Значок над «Стартом» на Панели рисуется по этому полю. Без него режим
    переключался только на экране «Запись» и в окне записей — и выбранная
    когда-то запись молча запускалась вместо сценария."""
    api.get_challenge_settings = lambda: {}
    api.docker = types.SimpleNamespace(docked=False)

    assert api.get_status()["run_mode"] == "auto", "по умолчанию — автомат"

    cfg.update({"run_mode": "replay"})
    assert api.get_status()["run_mode"] == "replay"

    # Мусор в файле настроек не должен превращаться в третий режим.
    cfg.update({"run_mode": "чепуха"})
    assert api.get_status()["run_mode"] == "auto"


def test_the_history_records_what_the_run_actually_was(api):
    """Challenge ходит под mode="story" — в истории он был неотличим от
    обычной Story-задачи, то есть половина строк выглядела одинаково."""
    from core.runner import MacroRunner

    assert MacroRunner._run_kind({"mode": "expedition"}) == "Expedition"
    assert MacroRunner._run_kind({"mode": "story"}) == "Story"
    assert MacroRunner._run_kind({"mode": "story", "is_challenge": True}) == "Challenge"
    assert MacroRunner._run_kind(
        {"mode": "story", "is_challenge": True, "is_daily_challenge": True}) == "Daily Challenge"
    assert MacroRunner._run_kind({}) == ""

    api._record_match_result("win", "Marjenta", "3m", kind="Expedition")
    assert _history()[0]["kind"] == "Expedition"


def test_old_history_without_a_kind_still_reads(api):
    """Забеги, записанные до появления поля, метки не получают: врать о них
    нечем, а падать интерфейс из-за этого не должен."""
    cfg.update({"run_history": [{"result": "win", "map": "Marjenta",
                                  "duration": "1m", "at": 1_700_000_000.0}]})
    api.get_challenge_settings = lambda: {}
    api.docker = types.SimpleNamespace(docked=False)
    assert api.get_status()["run_history"][0]["kind"] == ""


def test_the_pdf_gets_the_kind_in_russian(api):
    """Отчёт открывают ОТДЕЛЬНО от приложения, и словарь i18n перевести
    подписи там уже не сможет — в файл они обязаны попасть готовыми."""
    assert main.RUN_KIND_RU["Daily Challenge"] == "Дневной челлендж"
    assert main.RUN_KIND_RU["Replay"] == "Повтор"
    assert main.RUN_KIND_RU["Expedition"] == "Expedition"   # имя режима из игры не переводим


def test_the_start_preview_names_the_first_task_and_its_scenario(api):
    """Блок над «Стартом» отвечает на вопрос «что будет, если нажать».

    Играется ОЧЕРЕДЬ ЗАДАЧ сверху вниз, а сценарий указан внутри каждой
    задачи — не «верхний сценарий из списка». Раньше узнать это можно было,
    только обойдя три-четыре экрана."""
    p = main.Api._start_preview({
        "run_mode": "auto",
        "tasks": [{"map": "Marjenta", "stage": 12, "difficulty": "Hard", "macro": "Мой сценарий"},
                  {"map": "Spirit City"}],
    })
    assert p["what"] == "Marjenta · 12 · Hard"
    assert p["detail"] == "Мой сценарий"
    assert p["queue"] == 2
    assert not p["warn"]


def test_the_start_preview_warns_about_an_empty_queue(api):
    p = main.Api._start_preview({"run_mode": "auto", "tasks": []})
    assert p["warn"] == "Task queue is empty"


def test_the_start_preview_names_the_recording_in_replay_mode(api):
    p = main.Api._start_preview({"run_mode": "replay", "replay_file": "забег", "replay_loops": 0})
    assert p["what"] == "«забег»"
    assert p["detail"] == "endless loops"

    empty = main.Api._start_preview({"run_mode": "replay", "replay_file": ""})
    assert empty["warn"] == "No recording picked yet"


def test_the_start_preview_lists_only_the_enabled_extras(api):
    """Надстройки работают ПОВЕРХ режима, а не вместо него — Challenge не
    отменяет очередь задач, он в неё вклинивается. Показываем только
    включённые: пять всегда-видимых значков читаются хуже двух ярких."""
    p = main.Api._start_preview({
        "run_mode": "auto", "tasks": [{"map": "Marjenta"}],
        "challenge": {"enabled": True},
        "crafting": {"enabled": False},
        "bounty": {"enabled": True},
        "auto_shop": {"enabled": False},
        "fuel_refill": {"enabled": True},
    })
    assert p["extras"] == ["Challenge", "Bounty", "Fuel"]

    quiet = main.Api._start_preview({"run_mode": "auto", "tasks": [{"map": "Marjenta"}]})
    assert quiet["extras"] == []


def test_the_daily_challenge_alone_counts_as_enabled(api):
    """У Challenge два выключателя — обычный и дневной. Включён любой —
    значок обязан быть."""
    p = main.Api._start_preview({
        "run_mode": "auto", "tasks": [{"map": "Marjenta"}],
        "challenge": {"enabled": False, "daily": {"enabled": True}},
    })
    assert p["extras"] == ["Challenge"]


def test_the_dashboard_shows_the_countdown_before_the_first_action(api):
    api._player = _player(countdown_ms=1400.0)
    st = api._replay_status()
    assert "1.4" in st["action"], st["action"]
    assert st["mode"] == "Повтор"
    assert st["macro"] == "забег"


def test_the_dashboard_shows_progress_while_playing(api):
    api._player = _player()
    cfg.update({"replay_loops": 3})
    st = api._replay_status()
    assert "5/100" in st["action"]
    assert st["current_repeat"] == "2/3"


def test_endless_loops_read_as_infinity(api):
    api._player = _player()
    cfg.update({"replay_loops": 0})
    assert api._replay_status()["current_repeat"] == "2/∞"


def test_a_finished_replay_clears_the_dashboard_itself(api):
    """Повтор может кончиться САМ, отыграв заданное число кругов. Кнопка «Стоп»
    табло сбрасывает, а тихое окончание раньше не сбрасывало — и на Панели
    висело «Играю запись» от прогона, которого уже нет."""
    api._run_status = {"action": "Играю запись — действие 5/100", "mode": "Повтор",
                       "macro": "забег", "current_task": "забег",
                       "current_repeat": "2/3", "map": "-"}
    api._player = _player(running=False)

    assert api._replay_status() == {}
    assert api._run_status["action"] == "Idle"
    assert api._run_status["mode"] == "-"


def test_the_dashboard_is_untouched_when_the_auto_run_is_going(api):
    """Автомат ведёт своё табло сам — повтор не должен в него лезть."""
    api._run_status = {"action": "Battle in progress...", "mode": "story",
                       "macro": "Мой сценарий", "current_task": "Marjenta",
                       "current_repeat": "1/5", "map": "Marjenta"}
    api._player = _player(running=False)

    assert api._replay_status() == {}
    assert api._run_status["action"] == "Battle in progress..."
