"""Tests for live in-situ walk path recording (Teach-In) during macro runs.

Баг-контроль:
1. Таймер записи должен начинаться строго с момента первого нажатия клавиши
   (WASD), чтобы не копить мертвое время ожидания в начале пути.
2. После отпускания всех клавиш и паузы бездействия (1.8с) запись должна
   завершаться автоматически, при этом сама 1.8-секундная пауза НЕ должна
   попадать в events (чистая обрезка хвоста).
3. Принудительная остановка через finish_live_walk_record() или прерывание макроса
   через stop_event должны отрабатывать без зависаний и утечек клавиш.
4. Исполнитель блока _run_walk_block_tick должен автоматически сохранять записанный
   путь в Paths/, прописывать его имя в сам блок и в файл шаблона на диске,
   после чего бесшовно возвращать управление для выполнения следующих блоков.
"""
import os
import threading
import time
import pytest

from core import paths as walk_paths
from core.runner import MacroRunner
from core import templates as tpl


def test_record_live_path_until_idle_first_key_and_idle_trim(monkeypatch):
    """Проверяет старт таймера с первой клавиши и автоматическую обрезку хвоста бездействия."""
    key_states = [
        # Первые 2 тика: клавиши не нажаты (игрок собирается)
        {"w": False, "a": False, "s": False, "d": False, "i": False, "o": False},
        {"w": False, "a": False, "s": False, "d": False, "i": False, "o": False},
        # Тик 3: зажал W
        {"w": True, "a": False, "s": False, "d": False, "i": False, "o": False},
        # Тик 4: держит W
        {"w": True, "a": False, "s": False, "d": False, "i": False, "o": False},
        # Тик 5: отпустил W
        {"w": False, "a": False, "s": False, "d": False, "i": False, "o": False},
        # Далее тики: все клавиши отпущены, идет проверка idle_seconds
        {"w": False, "a": False, "s": False, "d": False, "i": False, "o": False},
    ]
    state_idx = [0]

    def mock_is_move_key_down(key):
        curr = key_states[min(state_idx[0], len(key_states) - 1)]
        return curr.get(key, False)

    monkeypatch.setattr(walk_paths._input_backend, "is_move_key_down", mock_is_move_key_down)

    fake_time = [100.0]

    def mock_perf_counter():
        return fake_time[0]

    def mock_sleep(d):
        fake_time[0] += 0.05
        state_idx[0] += 1

    monkeypatch.setattr(time, "perf_counter", mock_perf_counter)
    monkeypatch.setattr(time, "sleep", mock_sleep)

    first_key_called = []

    events = walk_paths.record_live_path_until_idle(
        stop_event=None,
        idle_seconds=0.2,  # 4 тика по 0.05с = 0.2с idle
        max_seconds=10.0,
        wait_first_key_timeout=5.0,
        on_first_key=lambda: first_key_called.append(True),
        poll_interval=0.01,
    )

    assert len(first_key_called) == 1, "on_first_key должен быть вызван при первом нажатии"
    assert len(events) == 2, f"Должно быть ровно 2 события (down и up), получено: {events}"
    assert events[0]["key"] == "w" and events[0]["state"] == "down"
    assert events[0]["t"] == 0.0, "Первое событие обязано иметь t=0.0"
    assert events[1]["key"] == "w" and events[1]["state"] == "up"
    # Метка времени отпускания клавиши меньше общего времени, пауза бездействия 0.2с не вошла в events
    assert events[1]["t"] == 0.1


def test_record_live_path_until_idle_honors_stop_event(monkeypatch):
    """Проверяет мгновенную остановку без сохранения мусора при нажатии Stop (stop_event)."""
    monkeypatch.setattr(walk_paths._input_backend, "is_move_key_down", lambda k: False)
    stop_ev = threading.Event()
    stop_ev.set()

    events = walk_paths.record_live_path_until_idle(
        stop_event=stop_ev,
        idle_seconds=1.8,
        poll_interval=0.001,
    )
    assert events == [], "При взведённом stop_event должен возвращаться пустой список"


def test_record_live_path_until_idle_manual_finish(monkeypatch):
    """Проверяет досрочное завершение записи по вызову finish_live_walk_record() (кнопка Стоп в HUD)."""
    fake_time = [100.0]
    monkeypatch.setattr(time, "perf_counter", lambda: fake_time[0])

    def mock_sleep(d):
        fake_time[0] += 0.05
        # Через 2 тика нажимаем кнопку Стоп
        if fake_time[0] >= 100.1:
            walk_paths.finish_live_walk_record()

    monkeypatch.setattr(time, "sleep", mock_sleep)
    monkeypatch.setattr(walk_paths._input_backend, "is_move_key_down", lambda k: k == "w")

    events = walk_paths.record_live_path_until_idle(
        stop_event=None,
        idle_seconds=5.0,
        poll_interval=0.01,
    )
    assert len(events) >= 1
    assert events[0]["key"] == "w" and events[0]["state"] == "down"
    # При выходе из цикла зажатая W должна быть корректно завершена up-событием
    assert events[-1]["key"] == "w" and events[-1]["state"] == "up"


def test_runner_walk_block_live_recording_prestart(tmp_path, monkeypatch):
    """Проверяет прогон блока Walk в Pre Start: запись, сохранение пути, обновление шаблона и продолжение."""
    logs = []
    statuses = []
    pushed_ui = []

    runner = MacroRunner(
        mouse=None,
        keyboard=None,
        log=lambda msg: logs.append(msg),
        set_status=lambda **kw: statuses.append(kw),
        push_ui=lambda call, data=None: pushed_ui.append((call, data)),
    )
    monkeypatch.setattr(runner, "_checkpoint", lambda stop_ev: False)

    # Изолируем папки Templates и Paths во временную директорию
    tpl_dir = tmp_path / "Templates"
    paths_dir = tmp_path / "Paths"
    tpl_dir.mkdir()
    paths_dir.mkdir()
    monkeypatch.setattr(tpl, "TEMPLATES_DIR", str(tpl_dir))
    monkeypatch.setattr(walk_paths, "PATHS_DIR", str(paths_dir))

    macro_name = "test_macro"
    initial_blocks = {
        "prestart": [
            {"type": "walk", "params": {"path": ""}, "recordOnReach": True, "id": "walk_1"},
            {"type": "place_unit", "params": {"name": "farm", "x": 100, "y": 200}, "hotkey": "5"},
        ],
        "battle": [],
    }
    tpl.save_template(macro_name, initial_blocks)

    # Мокаем record_live_path_until_idle, возвращая фиктивные события
    fake_events = [
        {"t": 0.0, "key": "w", "state": "down"},
        {"t": 1.2, "key": "w", "state": "up"},
    ]
    monkeypatch.setattr(walk_paths, "record_live_path_until_idle", lambda **kw: fake_events)

    stop_event = threading.Event()
    block_to_run = initial_blocks["prestart"][0]

    # Запускаем выполнение блока Walk
    runner._run_walk_block_tick(
        stop_event=stop_event,
        block=block_to_run,
        block_num=1,
        phase_label="Pre Start",
        macro_name=macro_name,
        hwnd=0,
    )

    # 1. Проверяем, что блок в памяти обновился
    saved_path_name = block_to_run.get("pathName")
    assert saved_path_name == "test_macro_pre_start_walk_1"
    assert block_to_run["recordOnReach"] is False
    assert block_to_run["params"]["recordOnReach"] is False
    assert block_to_run["params"]["path"] == saved_path_name

    # 2. Проверяем, что файл пути реально записан в Paths/
    saved_path_file = paths_dir / f"{saved_path_name}.json"
    assert saved_path_file.is_file(), f"Файл {saved_path_file} обязан существовать"

    # 3. Проверяем, что файл шаблона сценария на диске обновился
    reloaded_tpl = tpl.load_template(macro_name)
    saved_walk_block = reloaded_tpl["blocks"]["prestart"][0]
    assert saved_walk_block["pathName"] == saved_path_name
    assert saved_walk_block["recordOnReach"] is False

    # 4. Проверяем, что были отправлены UI уведомления onLiveWalkRecordStart и onLiveWalkRecordDone
    call_names = [call for call, data in pushed_ui]
    assert "onLiveWalkRecordStart" in call_names
    assert "onLiveWalkRecordDone" in call_names

    # 5. Проверяем сообщения в журнале логов
    log_text = " ".join(logs)
    assert "starting live movement recording" in log_text
    assert "saved as" in log_text
    assert "walk recorded & saved. Resuming scenario execution" in log_text


def test_runner_walk_block_live_recording_battle(tmp_path, monkeypatch):
    """Проверяет прогон блока Walk в фазе Battle: запись, сохранение и обновление в секции battle."""
    logs = []
    statuses = []
    pushed_ui = []

    runner = MacroRunner(
        mouse=None,
        keyboard=None,
        log=lambda msg: logs.append(msg),
        set_status=lambda **kw: statuses.append(kw),
        push_ui=lambda call, data=None: pushed_ui.append((call, data)),
    )
    monkeypatch.setattr(runner, "_checkpoint", lambda stop_ev: False)

    tpl_dir = tmp_path / "Templates"
    paths_dir = tmp_path / "Paths"
    tpl_dir.mkdir()
    paths_dir.mkdir()
    monkeypatch.setattr(tpl, "TEMPLATES_DIR", str(tpl_dir))
    monkeypatch.setattr(walk_paths, "PATHS_DIR", str(paths_dir))

    macro_name = "battle_macro"
    initial_blocks = {
        "prestart": [],
        "battle": [
            {"type": "walk", "params": {"path": ""}, "recordOnReach": True, "id": "walk_battle_1"},
        ],
    }
    tpl.save_template(macro_name, initial_blocks)

    fake_events = [
        {"t": 0.0, "key": "s", "state": "down"},
        {"t": 0.8, "key": "s", "state": "up"},
    ]
    monkeypatch.setattr(walk_paths, "record_live_path_until_idle", lambda **kw: fake_events)

    stop_event = threading.Event()
    block_to_run = initial_blocks["battle"][0]

    runner._run_walk_block_tick(
        stop_event=stop_event,
        block=block_to_run,
        block_num=1,
        phase_label="Battle",
        macro_name=macro_name,
        hwnd=0,
    )

    saved_path_name = block_to_run.get("pathName")
    assert saved_path_name == "battle_macro_battle_walk_1"
    assert block_to_run["recordOnReach"] is False

    reloaded_tpl = tpl.load_template(macro_name)
    assert reloaded_tpl["blocks"]["battle"][0]["pathName"] == saved_path_name
    assert reloaded_tpl["blocks"]["battle"][0]["recordOnReach"] is False


def test_runner_walk_block_replay_when_already_recorded(monkeypatch):
    """Проверяет, что если блок уже содержит путь и recordOnReach=False, запускается обычный replay_events."""
    replayed = []
    monkeypatch.setattr(walk_paths, "load_path", lambda name: {"name": name, "events": [{"t": 0.0, "key": "w", "state": "down"}]})
    monkeypatch.setattr(walk_paths, "replay_events", lambda ev, kb, stop_ev, sprint=False: replayed.append((ev, sprint)))

    runner = MacroRunner(
        mouse=None,
        keyboard=None,
        log=lambda msg: None,
        set_status=lambda **kw: None,
    )

    block = {"type": "walk", "params": {"path": "my_path"}, "recordOnReach": False, "sprint": True}
    runner._run_walk_block_tick(
        stop_event=threading.Event(),
        block=block,
        block_num=1,
        phase_label="Battle",
    )

    assert len(replayed) == 1
    assert replayed[0][1] is True, "Спринт должен быть передан в replay_events"


def test_start_macro_cancels_abandoned_path_recording(monkeypatch):
    """Ловит баг, когда пользователь нажал «Record WASD» в модале, но не закончил запись
    и запустил макрос — без отмены зависшая запись перехватывала ввод и висела на экране.
    """
    from main import Api
    from core import paths

    api = Api()
    monkeypatch.setattr(api, "run_preflight_check", lambda: {"has_blocker": False, "checks": []})
    monkeypatch.setattr(api.runner, "start", lambda *a, **kw: {"ok": True})

    cancelled = []
    monkeypatch.setattr(paths, "is_recording", lambda: True)
    monkeypatch.setattr(paths, "cancel_recording", lambda: cancelled.append(True))

    res = api.start_macro()
    assert res.get("ok") is True
    assert len(cancelled) == 1, "Зависшая запись пути обязана быть отменена перед стартом макроса"

