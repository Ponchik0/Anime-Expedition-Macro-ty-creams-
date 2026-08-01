"""ПАУЗА ПЕРЕД ПЕРВЫМ ДЕЙСТВИЕМ ПОВТОРА.

Между «нажал Играть» и «игра на экране» проходит заметное время: окно списка
закрывается, экран уезжает на Панель, окно Roblox возвращают из спрятанного
состояния и оно ловит фокус. Расписание стартовало в тот же миг, и первые
события круга уходили в никуда — а это ровно те события, которыми расставляют
юнитов.

Здесь проверяется, что пауза: (1) действительно задерживает ПЕРВОЕ действие,
(2) не сдвигает расписание внутри круга, (3) не повторяется на втором круге,
(4) прерывается «Стопом» и замирает на паузе.
"""
import time

import pytest

from core import replay


class _Inp:
    """Вместо core._input_win: запоминает, когда пришло каждое нажатие."""

    def __init__(self):
        self.downs = []

    def move_abs(self, x, y):
        pass

    def button_down(self, b):
        self.downs.append(time.perf_counter())

    def button_up(self, b):
        pass

    def key_down(self, vk):
        pass

    def key_up(self, vk):
        pass


@pytest.fixture
def inp(monkeypatch):
    fake = _Inp()
    monkeypatch.setattr(replay, "_inp", fake)
    monkeypatch.setattr(replay, "_timer_precision", lambda on: None)
    monkeypatch.setattr(replay, "_game_focused", lambda hwnd: True)
    monkeypatch.setattr(replay, "_client_xy", lambda hwnd: (0, 0))
    return fake


EVENTS = [{"t": 0.0, "kind": "down", "code": "left", "x": 0, "y": 0},
          {"t": 60.0, "kind": "up", "code": "left", "x": 0, "y": 0}]


def _drain(p, seconds=3.0):
    deadline = time.perf_counter() + seconds
    while p.running and time.perf_counter() < deadline:
        time.sleep(0.01)
    p.stop()


def test_the_first_action_waits_out_the_delay(inp):
    p = replay.Player(lambda: 0)
    t0 = time.perf_counter()
    assert p.start(EVENTS, "забег", loops=1, require_focus=False, start_delay_ms=300.0)
    _drain(p)

    assert inp.downs, "запись должна была отыграться"
    waited = (inp.downs[0] - t0) * 1000.0
    assert waited >= 250, f"первое действие пошло через {waited:.0f} мс вместо ~300"


def test_no_delay_means_no_wait(inp):
    """Ноль — это по-прежнему «начинай сразу»: старое поведение не должно
    зависеть от того, что у паузы появилась возможность."""
    p = replay.Player(lambda: 0)
    t0 = time.perf_counter()
    assert p.start(EVENTS, "забег", loops=1, require_focus=False, start_delay_ms=0.0)
    _drain(p)

    assert inp.downs
    assert (inp.downs[0] - t0) * 1000.0 < 150


def test_the_delay_does_not_stretch_the_recording(inp):
    """Пауза идёт ДО того, как засечено начало расписания.

    Иначе она съела бы начало записи вместо того, чтобы его уберечь: первые
    60 мс круга просто не отыгрались бы."""
    p = replay.Player(lambda: 0)
    assert p.start(EVENTS, "забег", loops=1, require_focus=False,
                   duration_ms=60.0, start_delay_ms=300.0)
    _drain(p)
    # Оба события на месте: и «нажал», и «отпустил» через 60 мс.
    assert p.index == len(EVENTS)


def test_the_delay_happens_once_not_every_loop(inp):
    """Между кругами паузы быть не должно: игра там уже на экране, а лишнее
    ожидание сдвигало бы круг относительно матча."""
    p = replay.Player(lambda: 0)
    assert p.start(EVENTS, "забег", loops=2, require_focus=False,
                   duration_ms=200.0, start_delay_ms=300.0)
    _drain(p)

    assert len(inp.downs) == 2, f"должно быть два круга, а не {len(inp.downs)}"
    gap = (inp.downs[1] - inp.downs[0]) * 1000.0
    # Круг длится 200 мс. Если бы пауза повторялась, разрыв был бы ~500.
    assert gap < 400, f"между кругами затесалась пауза: {gap:.0f} мс"


def test_stop_during_the_countdown_plays_nothing(inp):
    """«Стоп» во время отсчёта обязан сработать сразу и НЕ отыграть запись."""
    p = replay.Player(lambda: 0)
    assert p.start(EVENTS, "забег", loops=0, require_focus=False, start_delay_ms=3000.0)
    time.sleep(0.15)
    assert p.countdown_ms > 0, "отсчёт должен идти"
    t0 = time.perf_counter()
    p.stop()
    assert (time.perf_counter() - t0) < 1.0, "стоп не должен ждать конца отсчёта"
    assert not inp.downs, "во время отсчёта в игру не должно уйти ни одного нажатия"
    assert p.countdown_ms == 0.0


def test_pause_freezes_the_countdown(inp):
    """На паузе отсчёт стоит: снял паузу — досчитали остаток, а не начали
    играть немедленно."""
    p = replay.Player(lambda: 0)
    assert p.start(EVENTS, "забег", loops=1, require_focus=False, start_delay_ms=600.0)
    time.sleep(0.1)
    p.toggle_pause()
    frozen = p.countdown_ms
    time.sleep(0.4)
    assert abs(p.countdown_ms - frozen) < 1e-6, "отсчёт обязан стоять на паузе"
    assert not inp.downs
    p.toggle_pause()
    _drain(p)
    assert inp.downs, "после снятия паузы запись должна доиграть"
