import threading
from unittest.mock import MagicMock

import numpy as np
import pytest

from core import runner as runner_module
from core.runner import MacroRunner


def _runner():
    runner = MacroRunner(MagicMock(), MagicMock(), MagicMock())
    runner._set_status = MagicMock()
    return runner


@pytest.mark.parametrize(
    "task, expected",
    [
        ({"mode": "story", "stage": "Infinite", "infinite_wave_limit": 50}, 50),
        ({"mode": "story", "stage": "Infinite"}, 20),
        ({"mode": "story", "stage": "Infinite", "infinite_wave_limit": "bad"}, 20),
        ({"mode": "story", "stage": "Infinite", "infinite_wave_limit": 0}, 20),
        ({"mode": "story", "stage": "5", "infinite_wave_limit": 50}, None),
        ({"mode": "raid", "stage": "Infinite", "infinite_wave_limit": 50}, None),
        # Event > Infinite & Fishing uses the same wave-limit exit as Story > Infinite.
        ({"mode": "event", "stage": "infinite", "infinite_wave_limit": 40}, 40),
        ({"mode": "event", "stage": "infinite"}, 20),
        ({"mode": "event", "stage": "infinite", "infinite_wave_limit": "bad"}, 20),
        ({"mode": "event", "stage": "infinite", "infinite_wave_limit": 0}, 20),
        # Portal Mode (and any legacy event stage) is not an Infinite run.
        ({"mode": "event", "stage": "portal", "infinite_wave_limit": 40}, None),
        ({"mode": "event", "stage": "1", "infinite_wave_limit": 40}, None),
    ],
)
def test_infinite_wave_limit_only_applies_to_infinite_stages(task, expected):
    assert MacroRunner._infinite_wave_limit(task) == expected


def test_wave_limit_finishes_selected_wave_then_requires_a_confirming_read(monkeypatch):
    runner = _runner()
    readings = iter(((20, None), (21, None), (21, None)))
    left = []
    state = {}

    monkeypatch.setattr(
        runner_module.vision, "capture_window_region_bgr", lambda *_args: object())
    monkeypatch.setattr(runner_module.wave_module, "read_wave", lambda _image: next(readings))
    monkeypatch.setattr(
        runner, "_leave_infinite_at_wave_limit",
        lambda _hwnd, _stop, limit: left.append(limit) or True)

    for _ in range(3):
        state["next_check"] = 0
        result = runner._check_infinite_wave_limit(123, threading.Event(), 20, state)

    assert result == "wave_limit"
    assert left == [20]


def test_finite_wave_badge_cannot_trigger_infinite_exit(monkeypatch):
    runner = _runner()
    state = {}
    left = []

    monkeypatch.setattr(
        runner_module.vision, "capture_window_region_bgr", lambda *_args: object())
    monkeypatch.setattr(runner_module.wave_module, "read_wave", lambda _image: (21, 30))
    monkeypatch.setattr(
        runner, "_leave_infinite_at_wave_limit",
        lambda *_args: left.append(True) or True)

    for _ in range(3):
        state["next_check"] = 0
        assert runner._check_infinite_wave_limit(
            123, threading.Event(), 20, state) is None

    assert left == []


def test_impossible_unlimited_reads_cannot_confirm_the_exit_wave(monkeypatch):
    runner = _runner()
    readings = iter(((1414, None), (46, None), (46, None)))
    left = []
    state = {}

    monkeypatch.setattr(
        runner_module.vision, "capture_window_region_bgr", lambda *_args: object())
    monkeypatch.setattr(runner_module.wave_module, "read_wave", lambda _image: next(readings))
    monkeypatch.setattr(
        runner, "_leave_infinite_at_wave_limit",
        lambda _hwnd, _stop, limit: left.append(limit) or True)

    for _ in range(3):
        state["next_check"] = 0
        result = runner._check_infinite_wave_limit(
            123, threading.Event(), 45, state)

    assert result == "wave_limit"
    assert left == [45]


def test_confirmed_later_wave_substitutes_after_target_wave_was_seen(monkeypatch):
    runner = _runner()
    state = {}
    left = []
    readings = iter(((45, None), (47, None), (47, None)))

    monkeypatch.setattr(
        runner_module.vision, "capture_window_region_bgr", lambda *_args: object())
    monkeypatch.setattr(
        runner_module.wave_module, "read_wave", lambda _image: next(readings))
    monkeypatch.setattr(
        runner, "_leave_infinite_at_wave_limit",
        lambda _hwnd, _stop, limit: left.append(limit) or True)

    for _ in range(3):
        state["next_check"] = 0
        result = runner._check_infinite_wave_limit(
            123, threading.Event(), 45, state)

    assert result == "wave_limit"
    assert left == [45]


def test_later_wave_cannot_exit_without_observing_target_wave(monkeypatch):
    runner = _runner()
    state = {}
    left = []

    monkeypatch.setattr(
        runner_module.vision, "capture_window_region_bgr", lambda *_args: object())
    monkeypatch.setattr(runner_module.wave_module, "read_wave", lambda _image: (55, None))
    monkeypatch.setattr(
        runner, "_leave_infinite_at_wave_limit",
        lambda *_args: left.append(True) or True)

    for _ in range(3):
        state["next_check"] = 0
        assert runner._check_infinite_wave_limit(
            123, threading.Event(), 45, state) is None

    assert left == []


def test_infinite_limit_is_checked_before_battle_blocks():
    runner = _runner()
    runner._check_infinite_wave_limit = MagicMock(return_value="wave_limit")
    runner._run_battle_blocks_tick = MagicMock()

    result = runner._wait_for_match_result(
        123,
        threading.Event(),
        battle_blocks=[{"type": "upgrade_unit"}],
        task={
            "mode": "story",
            "stage": "Infinite",
            "infinite_wave_limit": 45,
        },
    )

    assert result == "wave_limit"
    runner._run_battle_blocks_tick.assert_not_called()


def test_failed_leave_reports_failure_to_match_loop(monkeypatch):
    runner = _runner()
    state = {"confirmations": 1, "confirmation_wave": 11}

    monkeypatch.setattr(
        runner_module.vision, "capture_window_region_bgr", lambda *_args: object())
    monkeypatch.setattr(runner_module.wave_module, "read_wave", lambda _image: (11, None))
    monkeypatch.setattr(runner, "_leave_infinite_at_wave_limit", lambda *_args: False)

    assert runner._check_infinite_wave_limit(
        123, threading.Event(), 10, state) == "failed"


def test_infinite_wave_limit_uses_restart_game_when_repeats_remain(monkeypatch):
    """Ловит баг, когда макрос посреди цепочки повторов выходил в лобби
    через Leave Stage вместо нажатия Restart Game в настройках, из-за чего
    терялось время и возникали ложные ошибки возврата в лобби."""
    runner = _runner()
    runner._is_last_repeat = False

    clicks = []
    # После первого клика restart_btn пропадает — симулируем флагом.
    call_count = {"n": 0}

    def fake_find_image(_hwnd, name, **_kwargs):
        if name in ("restart_btn", "restart_icon"):
            # Первые два вызова: возвращаем кнопку (до клика).
            # После клика — None, retry-цикл понимает «сработало».
            if call_count["n"] < 2:
                return {"x": 500, "y": 300, "cx": 550, "cy": 320, "score": 0.95}
            return None
        return None

    def fake_ref_to_screen(_hwnd, cx, cy):
        return (cx + 100, cy + 50)   # любое смещение, главное не падать

    def fake_move_to(sx, sy):
        pass   # hover — просто не падаем

    def fake_click(sx, sy):
        clicks.append((sx, sy))
        call_count["n"] += 1

    monkeypatch.setattr(runner_module.vision, "find_image", fake_find_image)
    monkeypatch.setattr(runner_module.vision, "ref_to_screen", fake_ref_to_screen)
    runner._mouse.move_to = fake_move_to
    runner._mouse.click = fake_click

    res = runner._leave_infinite_at_wave_limit(123, threading.Event(), 30)
    assert res == "restarted"
    assert len(clicks) >= 1


def test_infinite_wave_limit_falls_back_to_leave_stage_when_restart_click_ignored(monkeypatch):
    """Ловит баг, когда кнопка Restart найдена (score 1.00), но клик игнорируется
    игрой — кнопка остаётся видна все 3 попытки. Раньше код возвращал 'restarted'
    и стартовал следующий цикл, пока настройки ещё открыты."""
    runner = _runner()
    runner._is_last_repeat = False

    clicks = []

    def fake_find_image(_hwnd, name, **_kwargs):
        # Кнопка ВСЕГДА видна — симулируем игнорирование клика
        if name in ("restart_btn", "restart_icon"):
            return {"x": 500, "y": 300, "cx": 550, "cy": 320, "score": 1.0}
        return None

    def fake_ref_to_screen(_hwnd, cx, cy):
        return (cx + 100, cy + 50)

    def fake_move_to(sx, sy):
        pass

    def fake_click(sx, sy):
        clicks.append((sx, sy))

    left = []
    monkeypatch.setattr(runner_module.vision, "find_image", fake_find_image)
    monkeypatch.setattr(runner_module.vision, "ref_to_screen", fake_ref_to_screen)
    runner._mouse.move_to = fake_move_to
    runner._mouse.click = fake_click
    monkeypatch.setattr(
        runner, "_click_and_verify_gone",
        lambda _hwnd, _stop, name, *_args, **_kwargs: left.append(name) or True
    )
    monkeypatch.setattr(runner, "_click_return_to_lobby_if_found", lambda *_args: True)

    res = runner._leave_infinite_at_wave_limit(123, threading.Event(), 30)
    # Не должен вернуть "restarted" если кнопка не приняла клик
    assert res != "restarted"
    assert "leave_stage" in left, "при провале restart должен уходить через leave_stage"


def test_infinite_wave_limit_leaves_to_lobby_on_last_repeat(monkeypatch):
    """Ловит баг, когда на последнем повторе макрос ошибочно перезапускал
    раунд вместо выхода в лобби, оставляя игрока внутри матча после
    завершения очереди задач."""
    runner = _runner()
    runner._is_last_repeat = True

    left = []
    monkeypatch.setattr(
        runner, "_click_and_verify_gone",
        lambda _hwnd, _stop, name, *_args, **_kwargs: left.append(name) or True
    )
    monkeypatch.setattr(runner, "_click_return_to_lobby_if_found", lambda *_args: True)

    res = runner._leave_infinite_at_wave_limit(123, threading.Event(), 30)
    assert res == "wave_limit"
    assert "leave_stage" in left


def test_no_hotbar_interaction_during_infinite_match():
    """Проверяет, что макрос НЕ запускает циклическое прожатие слотов 2-6 (рыба-бустеры).

    ПОЧЕМУ ЭТО ВАЖНО: часть пойманных рыб требует применения/установки на юнита.
    Любые автоматические клики или прожатия хотбара активируют режим прицеливания/размещения,
    блокируя дальнейшее управление и ломая прогон.
    """
    runner = _runner()
    assert not hasattr(runner, "_trigger_wave10_hotbar_keys")
    assert not hasattr(runner, "_try_use_fish_hotbar_items")


def test_is_fishing_task():
    """Проверяет точное определение заданий рыбалки (Summer Event Infinite, Inf Summer)."""
    runner = _runner()
    assert runner._is_fishing_task({"mode": "event", "event_kind": "infinite"}) is True
    assert runner._is_fishing_task({"macro": "Inf Summer"}) is True
    assert runner._is_fishing_task({"macro": "summer fishing"}) is True
    assert runner._is_fishing_task({"stage": "Summer Infinite"}) is True
    assert runner._is_fishing_task({"mode": "story", "macro": "Autoplay"}) is False


def test_is_fishing_rod_equipped_vision_and_ocr(monkeypatch):
    """Проверяет железобетонную детекцию удочки: как через шаблоны, так и через OCR (Grandmaster / Novice)."""
    runner = _runner()

    # 1. Проверка по шаблону
    monkeypatch.setattr(runner_module.vision, "find_image", lambda *_args, **_kwargs: {"score": 0.92})
    assert runner._is_fishing_rod_equipped(123) is True

    # 2. Проверка по OCR при несовпадении шаблонов (например, ранг Grandmaster максимального уровня)
    monkeypatch.setattr(runner_module.vision, "find_image", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner_module.vision, "capture_window_region_bgr", lambda *_args, **_kwargs: np.zeros((50, 200, 3), dtype=np.uint8))
    monkeypatch.setattr(runner_module.ocr_windows, "is_available", lambda: True)
    monkeypatch.setattr(runner_module.ocr_windows, "ocr_lines", lambda *_args, **_kwargs: [{"text": "Grandmaster"}])
    assert runner._is_fishing_rod_equipped(123) is True

    # 3. Проверка по OCR для других уровней (Novice, Veteran, Fishing EXP)
    monkeypatch.setattr(runner_module.ocr_windows, "ocr_lines", lambda *_args, **_kwargs: [{"text": "500 / 1000 Fishing EXP"}])
    assert runner._is_fishing_rod_equipped(123) is True

    # 4. Если на экране пустота / лобби — возвращает False
    monkeypatch.setattr(runner_module.ocr_windows, "ocr_lines", lambda *_args, **_kwargs: [{"text": "Wave 15"}])
    assert runner._is_fishing_rod_equipped(123) is False


def test_ensure_fishing_rod_equipped_protects_held_rod(monkeypatch):
    """Проверяет, что если удочка уже в руках, макрос НЕ жмет слот 1 (чтобы не убрать удочку в Roblox)."""
    runner = _runner()
    keys_tapped = []
    clicks = []
    runner._keyboard.tap = lambda vk, **_kwargs: keys_tapped.append(vk)
    runner._mouse.click = lambda x, y: clicks.append((x, y))

    # Удочка уже экипирована
    monkeypatch.setattr(runner, "_is_fishing_rod_equipped", lambda _hwnd: True)

    ok = runner._ensure_fishing_rod_equipped(123)
    assert ok is True
    assert len(keys_tapped) == 0
    assert len(clicks) == 0


def test_ensure_fishing_rod_equipped_equips_when_missing(monkeypatch):
    """Проверяет, что если удочки в руках нет, макрос экипирует слот 1 и проверяет появление HUD."""
    runner = _runner()
    keys_tapped = []
    clicks = []
    runner._keyboard.tap = lambda vk, **_kwargs: keys_tapped.append(chr(vk))
    runner._mouse.click = lambda x, y: clicks.append((x, y))
    monkeypatch.setattr(runner_module.wm, "activate_window", lambda _hwnd: None)
    monkeypatch.setattr(runner_module.vision, "ref_to_screen", lambda _hwnd, x, y: (x, y))

    # Сначала удочки нет, после первого нажатия '1' HUD появляется
    state = {"equipped": False}
    def fake_is_equipped(_hwnd):
        return state["equipped"]
    def fake_tap(vk, **_kwargs):
        keys_tapped.append(chr(vk))
        state["equipped"] = True

    monkeypatch.setattr(runner, "_is_fishing_rod_equipped", fake_is_equipped)
    runner._keyboard.tap = fake_tap

    ok = runner._ensure_fishing_rod_equipped(123)
    assert ok is True
    assert "1" in keys_tapped
    assert len(clicks) == 0  # Кликом не спамил, так как клавиша '1' сразу активировала удочку


def test_click_block_skips_slot1_when_rod_already_held(monkeypatch):
    """Проверяет, что блок клика (74, 670) пропускается, если удочка уже в руках."""
    runner = _runner()
    clicks = []
    runner._mouse.click = lambda x, y: clicks.append((x, y))
    monkeypatch.setattr(runner_module.wm, "get_window_rect_screen", lambda _hwnd: (0, 0, 1152, 756))
    monkeypatch.setattr(runner, "_is_fishing_rod_equipped", lambda _hwnd: True)

    block = {"type": "click", "params": {"x": 74, "y": 670}}
    runner._run_click_block(123, threading.Event(), block, block_num=1, phase_label="Pre Start")

    # Клик должен быть пропущен, так как удочка уже в руках!
    assert len(clicks) == 0





