"""ТЕСТЫ ПЕРЕХОДОВ ЗАДАЧ И ОСТАНОВКИ ПРИ СБОЕ.

1. Ловит TypeError в _tracking_set_status: вызовы self._set_status(..., action=True)
   передавали строку первым позиционным аргументом, из-за чего макрос падал
   с ошибкой `takes 0 positional arguments but 1 was given`.

2. Проверяет опцию `stop_on_failure`: при сбое или исключении в задаче макрос
   должен останавливаться, а не продолжать выполнение следующей задачи.

3. Проверяет действие после завершения задачи (`on_complete_enabled`):
   - 'stop': макрос останавливается после выполнения задачи;
   - 'repeat': повторяет ту же самую задачу;
   - 'jump': переходит к указанной целевой задаче.
"""
import threading
from unittest.mock import MagicMock

import pytest

from core import vision
from core import window as wm
from core.runner import MacroRunner
from main import Api


@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch):
    """Изолирует тесты от вызовов Windows API, захвата экрана MSS и sleep-блокировок."""
    monkeypatch.setattr(vision, "find_image", lambda *a, **k: None)
    monkeypatch.setattr(vision, "close_mss", lambda: None)
    monkeypatch.setattr(wm, "prevent_sleep", lambda: None)
    monkeypatch.setattr(wm, "allow_sleep", lambda: None)
    monkeypatch.setattr(wm, "is_window", lambda hwnd: True)


def _make_runner(status_collector=None):
    cb = status_collector if status_collector is not None else (lambda **kw: None)
    r = MacroRunner(
        MagicMock(), MagicMock(), lambda msg: None,
        set_status=cb, record_result=lambda *a, **k: None,
        get_challenge_settings=lambda: {}, mark_challenge_stage_played=lambda *a, **k: None,
        get_run_stats=lambda: {}, get_crafting_settings=lambda: {}, set_crafting_count=lambda *a, **k: None,
        get_bounty_settings=lambda: {}, set_bounty_remaining=lambda *a, **k: None,
        get_fuel_settings=lambda: {}, mark_fuel_refill_result=lambda *a, **k: None,
        get_hotkeys=lambda: {}, get_auto_shop_settings=lambda: {},
        save_auto_shop_item_state=lambda *a, **k: None, save_auto_shop_shop_state=lambda *a, **k: None
    )
    r._log = lambda *a, **k: None
    return r


def test_tracking_set_status_accepts_positional_string_and_action_true():
    """Ловит баг: TypeError: _tracking_set_status() takes 0 positional arguments but 1 was given.

    При вызовах из порталов и автоигры (например, `self._set_status('Opening...', action=True)`)
    первый аргумент передавался позиционно, а функция принимала только **kw.
    """
    statuses = []
    runner = _make_runner(status_collector=lambda **kw: statuses.append(kw))

    # Вызов с позиционной строкой и action=True (как в порталах)
    runner._set_status("Opening the portal...", action=True)
    assert runner._last_action == "Opening the portal..."
    assert statuses[-1]["action"] == "Opening the portal..."

    # Вызов с позиционной строкой без именованных параметров
    runner._set_status("Just a plain status")
    assert runner._last_action == "Just a plain status"
    assert statuses[-1]["action"] == "Just a plain status"

    # Вызов со словарём позиционно
    runner._set_status({"action": "Dict status", "stage": "2"})
    assert runner._last_action == "Dict status"
    assert statuses[-1]["action"] == "Dict status"
    assert statuses[-1]["stage"] == "2"


def test_api_set_run_status_handles_positional_args_and_russian_stop():
    """Проверяет безопасность _set_run_status в main.Api при позиционных вызовах
    и сброс полей текущей задачи при статусе 'Остановлен...'."""
    api = Api()
    api._run_status["current_task"] = "1 / 2"
    api._run_status["current_repeat"] = "1 / 5"

    api._set_run_status("Остановлен: сбой задачи")
    assert api._run_status["action"] == "Остановлен: сбой задачи"
    assert api._run_status["current_task"] == "-"
    assert api._run_status["current_repeat"] == "-"


def test_stop_on_failure_in_run_task_stops_when_attempts_exhausted(monkeypatch):
    """Ловит баг: задача не смогла выполниться и исчерпала попытки восстановления,
    но макрос молча продолжал выполнение очереди вместо остановки."""
    runner = _make_runner()
    monkeypatch.setattr(runner, "_recover_to_lobby", lambda hwnd, stop_event: True)
    monkeypatch.setattr(runner, "_save_debug_screenshot_unconditional", lambda hwnd, prefix: "")
    monkeypatch.setattr(runner, "_send_event_webhook", lambda *a, **k: None)
    monkeypatch.setattr(runner, "_send_progress_webhook", lambda *a, **k: None)

    # Имитируем провал настройки задачи
    monkeypatch.setattr(runner, "_run_task_setup", lambda *a, **k: False)

    stop = threading.Event()
    task = {"mode": "story", "map": "Namek", "stage": "1", "repeat": 1, "stop_on_failure": True}

    res = runner._run_task(
        12345, stop, task, 1, 1, {}, 1, 1, {}, {}
    )
    assert res is False
    assert "Stopped: task failure" in runner._last_action or "Остановлен: сбой задачи" in runner._last_action


def test_stop_on_failure_stops_macro_on_guarded_phase_error(monkeypatch):
    """Проверяет, что при возникновении исключения в задаче и флаге stop_on_failure=True
    макрос прекращает выполнение очереди и переходит в статус ошибки."""
    runner = _make_runner()
    stop = threading.Event()

    task1 = {"id": "t1", "mode": "story", "map": "Map1", "stop_on_failure": True}
    task2 = {"id": "t2", "mode": "story", "map": "Map2"}

    ran_tasks = []

    def fake_run_task(hwnd, stop_event, task, *a, **k):
        ran_tasks.append(task["id"])
        if task["id"] == "t1":
            raise RuntimeError("Boom in task 1")
        return True

    monkeypatch.setattr(runner, "_run_task", fake_run_task)
    monkeypatch.setattr(runner, "_recover_to_lobby", lambda *a, **k: True)
    monkeypatch.setattr(wm, "is_window", lambda hwnd: True)

    runner._run(lambda: 12345, lambda: [task1, task2], stop, scroll_power=1, coords={}, scroll_nudges=1, default_walk_paths={}, webhook={})

    assert ran_tasks == ["t1"]
    assert "Stopped: task error" in runner._last_action or "Остановлен: ошибка в задаче" in runner._last_action


def test_on_complete_action_stop_halts_macro(monkeypatch):
    """Проверяет действие after completion: 'stop'.
    Макрос должен остановиться после окончания задачи и не запускать следующую."""
    runner = _make_runner()
    stop = threading.Event()

    task1 = {
        "id": "t1", "mode": "story", "map": "Map1",
        "on_complete_enabled": True, "on_complete_action": "stop"
    }
    task2 = {"id": "t2", "mode": "story", "map": "Map2"}

    ran_tasks = []

    def fake_run_task(hwnd, stop_event, task, *a, **k):
        ran_tasks.append(task["id"])
        return True

    monkeypatch.setattr(runner, "_run_task", fake_run_task)
    monkeypatch.setattr(wm, "is_window", lambda hwnd: True)

    runner._run(lambda: 12345, lambda: [task1, task2], stop, scroll_power=1, coords={}, scroll_nudges=1, default_walk_paths={}, webhook={})

    assert ran_tasks == ["t1"]
    assert runner._last_action == "Idle"


def test_on_complete_action_jump_switches_to_target_task(monkeypatch):
    """Проверяет действие after completion: 'jump'.
    После выполнения t1 макрос переходит к t3, минуя t2."""
    runner = _make_runner()
    stop = threading.Event()

    task1 = {
        "id": "t1", "mode": "story", "map": "Map1",
        "on_complete_enabled": True, "on_complete_action": "jump", "on_complete_target": "t3"
    }
    task2 = {"id": "t2", "mode": "story", "map": "Map2"}
    task3 = {
        "id": "t3", "mode": "story", "map": "Map3",
        "on_complete_enabled": True, "on_complete_action": "stop"
    }

    ran_tasks = []

    def fake_run_task(hwnd, stop_event, task, *a, **k):
        ran_tasks.append(task["id"])
        return True

    monkeypatch.setattr(runner, "_run_task", fake_run_task)
    monkeypatch.setattr(wm, "is_window", lambda hwnd: True)

    runner._run(lambda: 12345, lambda: [task1, task2, task3], stop, scroll_power=1, coords={}, scroll_nudges=1, default_walk_paths={}, webhook={})

    assert ran_tasks == ["t1", "t3"]


def test_on_complete_action_repeat_repeats_current_task(monkeypatch):
    """Проверяет действие after completion: 'repeat'.
    Задача t1 зацикливается и выполняется повторно."""
    runner = _make_runner()
    stop = threading.Event()

    task1 = {
        "id": "t1", "mode": "story", "map": "Map1",
        "on_complete_enabled": True, "on_complete_action": "repeat"
    }
    task2 = {"id": "t2", "mode": "story", "map": "Map2"}

    runs = 0

    def fake_run_task(hwnd, stop_event, task, *a, **k):
        nonlocal runs
        runs += 1
        if runs >= 3:
            stop_event.set()
        return True

    monkeypatch.setattr(runner, "_run_task", fake_run_task)
    monkeypatch.setattr(wm, "is_window", lambda hwnd: True)

    runner._run(lambda: 12345, lambda: [task1, task2], stop, scroll_power=1, coords={}, scroll_nudges=1, default_walk_paths={}, webhook={})

    assert runs == 3


def test_timer_expired_when_disabled_returns_false():
    """Проверяет, что при timer_next_enabled=False таймер не прерывает задачу
    и не переходит автоматически к следующей, даже если время вышло."""
    import time
    runner = _make_runner()
    runner._task_started_at = time.time() - 600  # 10 минут назад

    # Переход выключен
    task = {"timer_minutes": 5, "timer_next_enabled": False, "timer_next": "next"}
    assert runner._timer_expired(task) is False
    assert runner._timer_jump_to is None


def test_timer_expired_when_enabled_transitions_to_next_or_target():
    """Проверяет переход по таймеру при timer_next_enabled=True:
    1) timer_next='next' -> переход к следующей по очереди (_timer_jump_to is None);
    2) timer_next='custom_id' -> прыжок к указанной задаче (_timer_jump_to == 'custom_id')."""
    import time
    runner = _make_runner()
    runner._task_started_at = time.time() - 600  # 10 минут назад

    # Включён переход к следующей по очереди
    task_next = {"timer_minutes": 5, "timer_next_enabled": True, "timer_next": "next"}
    assert runner._timer_expired(task_next) is True
    assert runner._timer_jump_to is None
    assert runner._last_action in ("Task timer expired -- switching", "Таймер задачи вышел — перехожу")

    # Включён переход к конкретной целевой задаче
    task_jump = {"timer_minutes": 5, "timer_next_enabled": True, "timer_next": "target_id_42"}
    assert runner._timer_expired(task_jump) is True
    assert runner._timer_jump_to == "target_id_42"

