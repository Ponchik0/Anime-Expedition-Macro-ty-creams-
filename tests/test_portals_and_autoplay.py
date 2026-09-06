"""Тесты для механики Portals, Autoplay и сопутствующих расширений блоков/детекта.

Проверяет:
1. Поиск средней карточки порталов (_find_middle_portal_card):
   - Меньше 3 карточек -> None (ждём полного появления).
   - 3 и более карточек -> выбор средней по оси X (полю cx).
2. Разрешение координат порталов (_portal_task_point):
   - Корректные координаты из задачи для слота лобби/выбора.
   - Возврат None при отсутствии или некорректных значениях.
3. Переключение автоплея (_settle_autoplay_for_match):
   - Включение автоплея при auto_play='autoplay'.
   - Выключение автоплея при auto_play='macro'.
   - Пропуск переключения при переходе из chooser в порталах (состояние сохраняется).
4. Счётчик в блоках детекта (_eval_counter / _counter_limit):
   - Чтение лимита из задачи через limit_from_task.
   - Фолбэк на собственный limit блока при отсутствии поля в задаче.
   - Бесконечный цикл при limit <= 0.
   - Ограничение проходов: ровно N раз True (THEN), затем False (ELSE).
5. Расширения блоков (BlockOps):
   - Пропуск блоков в _run_prestart_blocks при совпадении режима задачи с skip_modes.
   - Разрешение координат клика по coord_key из конфигурации runner._coords в _run_click_block.
"""
import threading
from unittest.mock import MagicMock, patch
import pytest

from core import detect
from core.runner_blocks import BlockOps
from core.runner import MacroRunner


class DummyBlockRunner(BlockOps):
    def __init__(self, task=None, coords=None):
        self.logs = []
        self._task = task or {}
        self._coords = coords or {}
        self._mouse = MagicMock()
        self.stop_requested = False
        self.pause_requested = False

    def _log(self, msg):
        self.logs.append(msg)

    def _checkpoint(self, stop_event=None):
        return False

    def _release_quick_place_shift(self):
        pass


# ---------------------------------------------------------------------------
# 1. Поиск средней карточки порталов
# ---------------------------------------------------------------------------

@patch("core.vision.find_image_all")
def test_find_middle_portal_card_requires_at_least_three_cards(mock_find):
    """Ловит баг клика по неполному набору карточек выбора портала.

    Если на экране отрисовались ещё не все 3 карточки (например, анимация
    появления показала только 1 или 2), кликать нельзя — координаты средней
    карточки будут неверными, и макрос выберет не тот портал.
    """
    runner = MacroRunner.__new__(MacroRunner)
    mock_find.return_value = []
    assert runner._find_middle_portal_card(12345) is None

    mock_find.return_value = [{"cx": 200, "cy": 300}]
    assert runner._find_middle_portal_card(12345) is None

    mock_find.return_value = [{"cx": 200, "cy": 300}, {"cx": 600, "cy": 300}]
    assert runner._find_middle_portal_card(12345) is None


@patch("core.vision.find_image_all")
def test_find_middle_portal_card_picks_median_by_x(mock_find):
    """Проверяет выбор именно центрального портала из трех предложенных по оси X.

    Карточки могут прийти в любом порядке от детектора (например, правая, левая,
    средняя). Функция обязана отсортировать их по X (cx) и взять среднюю.
    """
    runner = MacroRunner.__new__(MacroRunner)
    left = {"cx": 250, "cy": 400, "score": 0.9}
    mid = {"cx": 500, "cy": 400, "score": 0.95}
    right = {"cx": 750, "cy": 400, "score": 0.92}

    mock_find.return_value = [right, left, mid]
    chosen = runner._find_middle_portal_card(12345)
    assert chosen is not None
    assert chosen["cx"] == 500
    assert chosen["_cards"] == [left, mid, right]


# ---------------------------------------------------------------------------
# 2. Разрешение координат порталов
# ---------------------------------------------------------------------------

def test_portal_task_point_reads_from_task_or_returns_none():
    """Проверяет чтение координат слота портала из параметров задачи.

    В порталах координаты слота уникальны для каждого типа задачи (lobby/chooser)
    и хранятся в задаче. Если координаты не заданы или испорчены, возвращается None.
    """
    # Валидные числа
    task_int = {"portal_lobby_x": 450, "portal_lobby_y": 320}
    assert MacroRunner._portal_task_point(task_int, "lobby") == (450, 320)

    # Строковые значения
    task_str = {"portal_chooser_x": "550", "portal_chooser_y": "380"}
    assert MacroRunner._portal_task_point(task_str, "chooser") == (550, 380)

    # Отсутствующие ключи
    empty_task = {}
    assert MacroRunner._portal_task_point(empty_task, "lobby") is None

    # Некорректные значения
    junk_task = {"portal_lobby_x": "invalid", "portal_lobby_y": 100}
    assert MacroRunner._portal_task_point(junk_task, "lobby") is None


# ---------------------------------------------------------------------------
# 3. Переключение автоплея
# ---------------------------------------------------------------------------

def test_settle_autoplay_turns_on_when_requested():
    """Проверяет включение Autoplay перед боем, если в задаче auto_play='autoplay'."""
    runner = MacroRunner.__new__(MacroRunner)
    runner._ensure_autoplay = MagicMock()
    stop_event = threading.Event()

    task = {"auto_play": "autoplay"}
    runner._settle_autoplay_for_match(12345, stop_event, task)

    runner._ensure_autoplay.assert_called_once_with(12345, stop_event, True)


def test_settle_autoplay_turns_off_when_macro():
    """Проверяет отключение Autoplay, если в задаче auto_play='macro'."""
    runner = MacroRunner.__new__(MacroRunner)
    runner._ensure_autoplay = MagicMock()
    stop_event = threading.Event()

    task = {"auto_play": "macro"}
    runner._settle_autoplay_for_match(12345, stop_event, task)

    runner._ensure_autoplay.assert_called_once_with(12345, stop_event, False)


def test_settle_autoplay_skips_when_came_from_chooser():
    """Пропускает переключение автоплея в цепочке порталов (состояние игры сохраняется)."""
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._ensure_autoplay = MagicMock()
    runner._portal_entered_from = "chooser"
    stop_event = threading.Event()

    task = {"mode": "portals", "auto_play": "autoplay"}
    result = runner._settle_autoplay_for_match(12345, stop_event, task)

    assert result is True
    runner._ensure_autoplay.assert_not_called()
    assert any("Came straight from the portal chooser" in log for log in runner.logs)


# ---------------------------------------------------------------------------
# 4. Счётчик в блоках детекта (limit_from_task)
# ---------------------------------------------------------------------------

def test_counter_detect_limit_from_task():
    """Проверяет получение лимита повторов из задачи (limit_from_task).

    В порталах шаблон один для любого количества повторов. Лимит забирается из
    поля задачи (например, extract_after). Первые N раз блок возвращает True
    (ветка THEN продолжать прогон), на N+1 раз — False (ветка ELSE выйти в лобби).
    """
    class DummyCtx:
        def __init__(self, task):
            self.task = task
            self.counters = {}

    ctx = DummyCtx({"extract_after": 2})
    block = {"counter_id": "portal_counter", "limit_from_task": "extract_after", "limit": 99}

    assert detect._eval_counter(ctx, block) is True
    assert detect._eval_counter(ctx, block) is True
    assert detect._eval_counter(ctx, block) is False


def test_counter_detect_fallback_to_own_limit():
    """Проверяет фолбэк на limit блока при отсутствии поля задачи."""
    class DummyCtx:
        def __init__(self, task):
            self.task = task
            self.counters = {}

    ctx = DummyCtx({})
    block = {"counter_id": "test_c", "limit_from_task": "extract_after", "limit": 1}

    assert detect._eval_counter(ctx, block) is True
    assert detect._eval_counter(ctx, block) is False


def test_counter_detect_infinite_when_zero_or_missing_limit():
    """Проверяет бесконечный цикл, если лимит не задан или равен 0."""
    class DummyCtx:
        def __init__(self, task):
            self.task = task
            self.counters = {}

    ctx = DummyCtx({})
    block = {"counter_id": "infinite_c"}

    for _ in range(10):
        assert detect._eval_counter(ctx, block) is True


# ---------------------------------------------------------------------------
# 5. Расширения блоков (BlockOps: skip_modes и coord_key)
# ---------------------------------------------------------------------------

def test_block_ops_skips_when_mode_in_skip_modes():
    """Проверяет пропуск блока в бою, если текущий режим задачи входит в skip_modes."""
    runner = DummyBlockRunner()
    runner._current_task = {"mode": "portals"}
    runner._battle_block_index = 0
    runner._battle_block_state = {}

    block = {
        "type": "click",
        "skip_modes": ["portals", "tower"],
        "params": {"x": 100, "y": 100},
    }
    stop_event = threading.Event()

    runner._run_click_block = MagicMock()
    runner._run_battle_blocks_tick(hwnd=999, stop_event=stop_event, battle_blocks=[block], first_repeat=True)

    # Блок пропущен: индекс увеличен, клик не вызывался
    assert runner._battle_block_index == 1
    runner._run_click_block.assert_not_called()


def test_block_ops_executes_when_mode_not_in_skip_modes():
    """Проверяет исполнение блока в бою, если текущий режим задачи не в skip_modes."""
    runner = DummyBlockRunner()
    runner._current_task = {"mode": "story"}
    runner._battle_block_index = 0
    runner._battle_block_state = {}

    block = {
        "type": "click",
        "skip_modes": ["portals"],
        "params": {"x": 100, "y": 100},
    }
    stop_event = threading.Event()

    runner._run_click_block = MagicMock()
    runner._run_battle_blocks_tick(hwnd=999, stop_event=stop_event, battle_blocks=[block], first_repeat=True)

    runner._run_click_block.assert_called_once_with(999, stop_event, block, 1)


@patch("core.runner_blocks.wm.get_window_rect_screen", return_value=(10, 20, 1000, 800))
def test_block_ops_click_resolves_coord_key(mock_rect):
    """Проверяет клик по именованному ключу coord_key из настроек Macro Coordinates."""
    coords = {"portal_exit_x": 456, "portal_exit_y": 789}
    runner = DummyBlockRunner(coords=coords)
    stop_event = threading.Event()

    block = {
        "type": "click",
        "params": {"coord_key": "portal_exit"},
    }

    runner._run_click_block(hwnd=999, stop_event=stop_event, block=block, block_num=1)

    runner._mouse.click.assert_called_once_with(10 + 456, 20 + 789)
    assert any("clicking (456, 789)" in log for log in runner.logs)


def test_block_ops_click_skips_when_coord_key_not_configured():
    """Проверяет пропуск клика, если coord_key не настроен в конфигурации."""
    runner = DummyBlockRunner(coords={})
    stop_event = threading.Event()

    block = {
        "type": "click",
        "params": {"coord_key": "portal_exit"},
    }

    runner._run_click_block(hwnd=999, stop_event=stop_event, block=block, block_num=1)

    runner._mouse.click.assert_not_called()
    assert any("coord_key 'portal_exit' not set" in log for log in runner.logs)