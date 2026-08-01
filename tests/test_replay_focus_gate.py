"""Запись идёт ТОЛЬКО пока окно Roblox видно и активно.

Зачем. Рекордер читает физическое состояние клавиш (GetAsyncKeyState) — он
видит их независимо от того, какое окно в фокусе. Без этой заслонки в запись
попадало всё подряд: переписка в браузере, пароль, набранный в другом окне,
возня в настройках самого макроса. При повторе это вываливается в Roblox как
нажатия.

Заодно проверяется, что время отлучки НЕ идёт в запись. Расписание у записи
абсолютное (см. шапку core/replay.py), и без поправки часов минута, проведённая
в браузере, превращалась бы при повторе в минуту, когда макрос просто стоит.

Настоящие вызовы Windows подменены: тест должен идти и на CI, где нет ни
Roblox, ни курсора.
"""
import time

import pytest

from core import replay

GAME = 2002
GUI = 1001
VK_W = ord("W")

SETTLE = 0.12          # с запасом больше и опроса (4 мс), и паузы простоя (50 мс)


class _FakeInput:
    """Вместо core._input_win: физическое состояние клавиш задаёт тест."""

    def __init__(self):
        self.down = set()

    def is_key_down(self, vk):
        return vk in self.down


@pytest.fixture
def rig(monkeypatch):
    """Рекордер с подменённым вводом и управляемым «игра активна»."""
    fake = _FakeInput()
    active = {"on": False}
    monkeypatch.setattr(replay, "_inp", fake)
    monkeypatch.setattr(replay, "_timer_precision", lambda on: None)
    monkeypatch.setattr(replay, "game_active", lambda hwnd: active["on"])
    monkeypatch.setattr(replay, "_cursor_over_gui", lambda gui, game: False)
    monkeypatch.setattr(replay, "_client_xy", lambda hwnd: (10, 20))
    monkeypatch.setattr(replay.wm, "get_window_rect_screen", lambda hwnd: (0, 0, 1152, 756))

    rec = replay.Recorder(lambda: GAME, lambda: GUI)
    yield rec, fake, active
    if rec.running:
        rec.stop()


def _kinds(events, kind):
    return [e for e in events if e["kind"] == kind]


# ── Заслонка ──────────────────────────────────────────────────────────────

def test_input_outside_the_game_is_not_recorded(rig):
    rec, fake, active = rig
    rec.start()
    time.sleep(SETTLE)
    assert rec.waiting is True, "вне игры рекордер обязан ждать, а не писать"

    fake.down.add(VK_W)          # нажали W, сидя в другом окне
    time.sleep(SETTLE)
    assert rec.count == 0

    events = rec.stop()
    assert events == []


def test_input_inside_the_game_is_recorded(rig):
    rec, fake, active = rig
    active["on"] = True
    rec.start()
    time.sleep(SETTLE)
    assert rec.waiting is False

    fake.down.add(VK_W)
    time.sleep(SETTLE)
    fake.down.discard(VK_W)
    time.sleep(SETTLE)

    events = rec.stop()
    assert [e["code"] for e in _kinds(events, "down")] == ["W"]
    assert [e["code"] for e in _kinds(events, "up")] == ["W"]


# ── Часы стоят, пока ты вне игры ──────────────────────────────────────────

def test_time_spent_outside_the_game_does_not_land_in_the_recording(rig):
    rec, fake, active = rig
    rec.start()
    time.sleep(0.4)              # заметная отлучка ДО первого действия
    active["on"] = True
    time.sleep(SETTLE)
    fake.down.add(VK_W)
    time.sleep(SETTLE)

    events = rec.stop()
    downs = _kinds(events, "down")
    assert downs, "нажатие после возвращения в игру должно записаться"
    # Без заморозки часов тут стояло бы больше 400 мс, и повтор начинался бы
    # с почти полусекундной паузы, которой в игре не было.
    assert downs[0]["t"] < 250, f"в запись утекло время вне игры: {downs[0]['t']} мс"


def test_keys_held_when_the_game_loses_focus_are_released_in_the_recording(rig):
    """Иначе в файле остаётся «нажал» без пары, и при повторе клавиша
    залипает в игре до конца круга."""
    rec, fake, active = rig
    active["on"] = True
    rec.start()
    time.sleep(SETTLE)
    fake.down.add(VK_W)          # зажали W и переключились из игры
    time.sleep(SETTLE)
    active["on"] = False
    time.sleep(SETTLE)

    events = rec.stop()
    ups = _kinds(events, "up")
    assert [e["code"] for e in ups] == ["W"], "ровно одно «отпустил», без дубля на остановке"
    # 0,0 -- это «не двигай курсор, просто отпусти» (см. Player._play).
    assert (ups[0]["x"], ups[0]["y"]) == (0, 0)


def test_waiting_flag_follows_the_game_window(rig):
    rec, fake, active = rig
    active["on"] = True
    rec.start()
    time.sleep(SETTLE)
    assert rec.waiting is False
    active["on"] = False
    time.sleep(SETTLE)
    assert rec.waiting is True
    active["on"] = True
    time.sleep(SETTLE)
    assert rec.waiting is False
    rec.stop()
    assert rec.waiting is False


# ── Из чего складывается «игра активна» ───────────────────────────────────

def test_game_active_needs_the_window_to_be_visible(monkeypatch):
    """Окно спрятано -- значит, человек на другом экране макроса, а не в игре.

    Именно этим случай отличается от «свернули Roblox»: в обычном режиме игра
    встроена в наше окно, фокус остаётся на нём, и одной проверки фокуса
    хватило бы, чтобы считать возню в настройках игрой."""
    monkeypatch.setattr(replay, "_game_focused", lambda hwnd: True)
    monkeypatch.setattr(replay.wm, "is_window_visible", lambda hwnd: False)
    assert replay.game_active(GAME) is False

    monkeypatch.setattr(replay.wm, "is_window_visible", lambda hwnd: True)
    assert replay.game_active(GAME) is True


def test_game_active_needs_focus_too(monkeypatch):
    monkeypatch.setattr(replay.wm, "is_window_visible", lambda hwnd: True)
    monkeypatch.setattr(replay, "_game_focused", lambda hwnd: False)
    assert replay.game_active(GAME) is False


def test_no_game_window_means_not_active():
    assert replay.game_active(0) is False
