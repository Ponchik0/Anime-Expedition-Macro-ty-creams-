"""Догоняющая расстановка: доставить в бою то, что не встало до старта.

Откуда взялось (debug.log, забег Raid Spirit City Act 3 от 14:33):

  [14:33:52] Place Unit "dps": aligned to a valid tile at offset (4, 0).
  [14:33:53] Place Unit "dps": подсветка на (878, 433) не погасла — клик не прошёл, жму ещё раз (1/2).
  [14:33:53] Place Unit "dps": подсветка на (878, 433) не погасла — клик не прошёл, жму ещё раз (2/2).
  [14:33:54] Place Unit "dps": НЕ ВСТАЛ на (878, 433) (Pre Start) — клик не зарегистрировался.
  [14:33:58] Pre Start: расставлено 5, не встало 1 ("dps").

Клетка нашлась, клик нажат трижды, юнит не встал. Это был ЧЕТВЁРТЫЙ подряд
DPS, то есть тот, на кого стартового баланса уже не осталось. Раньше блок
просто выбрасывался и забег шёл без юнита; теперь он ждёт первых волн и
доставляется, когда деньги накопились.
"""
import threading

import numpy as np
import pytest

from core import ocr
from core import runner_blocks
from core import vision
from core.runner import MacroRunner


class _Mouse:
    """Фальшивая мышь. `placed` -- клетки, на которых уже стоит юнит: по ним
    подсветка погашена, и именно это расстановка читает как «клик прошёл».
    `broke` -- клетки, где клик не проходит (нет денег), сколько ни щёлкай."""

    def __init__(self, placed, broke):
        self.clicks = []
        self.placed = placed
        self.broke = broke

    def move_to(self, x, y):
        pass

    def nudge(self, dx=1, dy=0):
        pass

    def click(self, x=None, y=None, button="left", hold=0.05):
        if x is None:
            return
        self.clicks.append((int(x), int(y)))
        if (int(x), int(y)) not in self.broke:
            self.placed.add((int(x), int(y)))

    def double_click(self, x=None, y=None, **kw):
        pass

    def scroll(self, amount):
        pass

    def drag(self, *a, **kw):
        pass


class _Keyboard:
    def tap(self, vk):
        pass

    def key_down(self, vk):
        pass

    def key_up(self, vk):
        pass


BLOCK_OK = {"type": "place_unit", "hotkey": "1", "params": {"name": "farm", "x": 200, "y": 200}}
BLOCK_BROKE = {"type": "place_unit", "hotkey": "2", "params": {"name": "dps", "x": 400, "y": 300}}


@pytest.fixture
def sim(monkeypatch):
    """MacroRunner на фальшивом поле 1152x756. Всё подсвечено (свободно),
    кроме занятых клеток; клетка из `broke` не занимается никогда."""
    monkeypatch.setattr(runner_blocks.time, "sleep", lambda s: None)
    monkeypatch.setattr(runner_blocks.wm, "get_window_rect_screen", lambda h: (0, 0, 1152, 756))

    placed, broke = set(), {(400, 300)}

    def capture_region(l, t, w, h):
        patch = np.full((h, w, 3), 255, np.uint8)
        for (px, py) in placed:
            if l <= px < l + w and t <= py < t + h:
                patch[:, :] = 0
        return patch

    # Два шва: с версии 0.18 Windows читает содержимое окна, macOS снимает
    # экран (см. _capture_place_search_region). Окно фальшивой игры в (0, 0),
    # поэтому числа одни и те же и подделка у них общая.
    monkeypatch.setattr(ocr, "capture_region", capture_region)
    monkeypatch.setattr(runner_blocks.vision, "capture_window_region_bgr",
                        lambda _hwnd, region: capture_region(*region))
    monkeypatch.setattr(vision, "find_image", lambda *a, **k: None)
    monkeypatch.setattr(vision, "wait_for_image", lambda *a, **k: None)

    runner = MacroRunner(_Mouse(placed, broke), _Keyboard(), lambda msg: None)
    runner.logs = []
    runner._log = runner.logs.append
    runner._reset_placement_tally()
    return runner


def _place(runner, block, pending_ok=True):
    return runner._run_place_unit_block(
        1, threading.Event(), 0, 0, block, index=1, macro_name="m",
        unit_ordinal=1, verify=False, pending_ok=pending_ok)


def test_a_unit_that_lands_is_not_queued(sim):
    assert _place(sim, BLOCK_OK) is True
    assert sim._pending_placements == []


def test_a_unit_that_never_lands_goes_into_the_queue(sim):
    assert _place(sim, BLOCK_BROKE) is False
    assert len(sim._pending_placements) == 1
    assert sim._pending_placements[0]["name"] == "dps"
    assert sim._pending_placements[0]["tries"] == 0


def test_battle_placements_are_never_queued(sim):
    """pending_ok=False -- в бою догонять некуда, бой уже идёт."""
    assert _place(sim, BLOCK_BROKE, pending_ok=False) is False
    assert sim._pending_placements == []


def test_the_queue_waits_before_the_first_attempt(sim, monkeypatch):
    """Сразу после старта боя лезть нельзя: деньги ещё не накопились, и
    попытка сгорела бы впустую."""
    _place(sim, BLOCK_BROKE)
    now = 1000.0
    monkeypatch.setattr(runner_blocks.time, "time", lambda: now)
    sim._pending_placements_battle_start = now  # бой только что начался

    sim._retry_pending_placements(1, threading.Event())

    assert sim._pending_placements[0]["tries"] == 0, "полез догонять раньше времени"


def test_a_pending_unit_is_delivered_once_the_tile_takes_it(sim, monkeypatch):
    """Деньги накопились -- клик проходит, и юнит уходит из очереди."""
    _place(sim, BLOCK_BROKE)
    clock = {"t": 1000.0}
    monkeypatch.setattr(runner_blocks.time, "time", lambda: clock["t"])
    sim._pending_placements_battle_start = clock["t"]
    clock["t"] += runner_blocks.PLACE_PENDING_FIRST_WAIT_S + 1
    sim._mouse.broke.clear()  # накопились

    sim._retry_pending_placements(1, threading.Event())

    assert sim._pending_placements == [], "юнит встал, но остался в очереди"
    assert any("Догнал" in m for m in sim.logs)


def test_the_queue_gives_up_after_the_try_cap(sim, monkeypatch):
    """Не встал и с последнего подхода -- убираем, иначе очередь будет
    дёргать игру до конца боя."""
    _place(sim, BLOCK_BROKE)
    clock = {"t": 1000.0}
    monkeypatch.setattr(runner_blocks.time, "time", lambda: clock["t"])
    sim._pending_placements_battle_start = clock["t"]
    clock["t"] += runner_blocks.PLACE_PENDING_FIRST_WAIT_S + 1

    for _ in range(runner_blocks.PLACE_PENDING_MAX_TRIES):
        sim._retry_pending_placements(1, threading.Event())
        clock["t"] += runner_blocks.PLACE_PENDING_RETRY_S + 1

    assert sim._pending_placements == []
    assert any("больше не пытаюсь" in m for m in sim.logs)


def test_attempts_are_spaced_out(sim, monkeypatch):
    """Второй подход не раньше PLACE_PENDING_RETRY_S: смысл паузы в том, что
    за неё капают деньги."""
    _place(sim, BLOCK_BROKE)
    clock = {"t": 1000.0}
    monkeypatch.setattr(runner_blocks.time, "time", lambda: clock["t"])
    sim._pending_placements_battle_start = clock["t"]
    clock["t"] += runner_blocks.PLACE_PENDING_FIRST_WAIT_S + 1

    sim._retry_pending_placements(1, threading.Event())
    assert sim._pending_placements[0]["tries"] == 1
    sim._retry_pending_placements(1, threading.Event())  # тот же миг
    assert sim._pending_placements[0]["tries"] == 1, "подходы идут без паузы"

    clock["t"] += runner_blocks.PLACE_PENDING_RETRY_S + 1
    sim._retry_pending_placements(1, threading.Event())
    assert sim._pending_placements[0]["tries"] == 2


def test_the_whole_thing_expires_late_into_the_battle(sim, monkeypatch):
    """Волны ушли далеко -- догонять уже бессмысленно, очередь сворачивается
    с честной подсказкой в журнал."""
    _place(sim, BLOCK_BROKE)
    clock = {"t": 1000.0}
    monkeypatch.setattr(runner_blocks.time, "time", lambda: clock["t"])
    sim._pending_placements_battle_start = clock["t"]
    clock["t"] += runner_blocks.PLACE_PENDING_DEADLINE_S + 1

    sim._retry_pending_placements(1, threading.Event())

    assert sim._pending_placements == []
    assert any("время вышло" in m for m in sim.logs)


def test_nothing_happens_before_the_battle_starts(sim):
    """_pending_placements_battle_start ещё None -- значит Pre Start не
    закончился, и трогать игру нельзя."""
    _place(sim, BLOCK_BROKE)
    sim._pending_placements_battle_start = None

    sim._retry_pending_placements(1, threading.Event())

    assert sim._pending_placements[0]["tries"] == 0


def test_an_empty_queue_costs_nothing(sim, monkeypatch):
    """Вызов стоит в цикле опроса боя, то есть срабатывает раз в секунду в
    каждом забеге -- он обязан выходить сразу, ничего не снимая с экрана."""
    calls = []
    # Оба пути захвата: пустая очередь не должна трогать экран ни на одной
    # платформе (см. _capture_place_search_region).
    monkeypatch.setattr(ocr, "capture_region", lambda *a: calls.append(a))
    monkeypatch.setattr(runner_blocks.vision, "capture_window_region_bgr",
                        lambda *a: calls.append(a))

    sim._retry_pending_placements(1, threading.Event())

    assert calls == []
