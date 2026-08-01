"""ПОВТОР ПЕРЕЖИВАЕТ ПЕРЕЗАПУСК ROBLOX.

Окно игры плеер спрашивал ОДИН РАЗ, на старте круга. Roblox посреди ночного
прогона перезапускается — сам, от вылета, или его перезапускает сторож, — и
hwnd старого окна после этого мёртв. Повтор до самого «Стоп» слал нажатия в
никуда: снаружи это «макрос работает, а в игре ничего не происходит».
Рекордер hwnd переспрашивал каждый тик, плеер — нет, и вот эта разница и была
дырой.

Теперь плеер спрашивает окно каждый тик и, увидев новое, отпускает всё
зажатое, пересчитывает масштаб под его размер и начинает круг заново.
"""
import time

import pytest

from core import replay


class _Inp:
    def __init__(self):
        self.downs = []
        self.ups = []
        self.moves = []

    def move_abs(self, x, y):
        self.moves.append((x, y))

    def button_down(self, b):
        self.downs.append(b)

    def button_up(self, b):
        self.ups.append(b)

    def key_down(self, vk):
        self.downs.append(vk)

    def key_up(self, vk):
        self.ups.append(vk)


@pytest.fixture
def rig(monkeypatch):
    """Окно игры задаёт тест: game["hwnd"] можно менять на ходу."""
    fake = _Inp()
    game = {"hwnd": 1001}
    sizes = {1001: (0, 0, 1152, 756), 2002: (0, 0, 576, 378)}
    monkeypatch.setattr(replay, "_inp", fake)
    monkeypatch.setattr(replay, "_timer_precision", lambda on: None)
    monkeypatch.setattr(replay, "_game_focused", lambda hwnd: True)
    monkeypatch.setattr(replay.wm, "get_window_rect_screen",
                        lambda hwnd: sizes.get(hwnd, (0, 0, 1152, 756)))
    return fake, game


EVENTS = [{"t": 0.0, "kind": "down", "code": "left", "x": 100, "y": 200},
          {"t": 400.0, "kind": "up", "code": "left", "x": 100, "y": 200}]


def _drain(p, seconds=3.0):
    deadline = time.perf_counter() + seconds
    while p.running and time.perf_counter() < deadline:
        time.sleep(0.01)
    p.stop()


def test_a_vanished_window_freezes_the_schedule(rig):
    """Окна нет — не жмём. Без hwnd клиентские координаты записи некуда
    пересчитывать, и клики ушли бы по тем же числам на рабочий стол."""
    fake, game = rig
    p = replay.Player(lambda: game["hwnd"])
    assert p.start(EVENTS, "забег", loops=0, require_focus=False, duration_ms=400.0)
    time.sleep(0.1)
    assert fake.downs, "пока окно есть, запись играет"
    played = len(fake.downs)

    game["hwnd"] = 0                   # Roblox закрылся
    time.sleep(0.6)                    # больше круга (400 мс)
    assert len(fake.downs) == played, "без окна игры не должно уйти ни одного нажатия"

    p.stop()


def test_the_run_resumes_on_the_new_window(rig):
    """Roblox поднялся заново — повтор обязан продолжить в новом окне, а не
    ждать до конца прогона."""
    fake, game = rig
    p = replay.Player(lambda: game["hwnd"])
    assert p.start(EVENTS, "забег", loops=0, require_focus=False, duration_ms=400.0)
    time.sleep(0.1)
    game["hwnd"] = 0
    time.sleep(0.2)
    played = len(fake.downs)

    game["hwnd"] = 2002                # Roblox открылся заново, окно другое
    time.sleep(0.3)
    assert len(fake.downs) > played, "в новом окне запись должна пойти дальше"

    p.stop()


def test_the_new_window_gets_its_own_scale(rig):
    """У нового окна свой размер, и координаты обязаны пересчитаться под него.
    Иначе после перезапуска Roblox все клики бьют мимо."""
    fake, game = rig
    p = replay.Player(lambda: game["hwnd"])
    assert p.start(EVENTS, "забег", loops=0, require_focus=False,
                   base_w=1152, base_h=756, duration_ms=300.0)
    time.sleep(0.15)
    first = list(fake.moves)
    assert first, "должно быть хоть одно движение курсора"
    # Окно 1152×756 при базе 1152×756 — масштаб 1:1, координаты как в записи.
    assert first[0] == (100, 200)

    fake.moves.clear()
    game["hwnd"] = 2002                # вдвое меньше по обеим сторонам
    time.sleep(0.4)
    p.stop()

    assert fake.moves, "в новом окне тоже должно быть движение"
    assert fake.moves[0] == (50, 100), f"масштаб не пересчитался: {fake.moves[0]}"


def test_everything_held_is_released_when_the_window_changes(rig):
    """Зажатое относилось к СТАРОМУ окну. Не отпустить — и клавиша повиснет
    нажатой в системе до конца прогона."""
    fake, game = rig
    long_hold = [{"t": 0.0, "kind": "down", "code": "left", "x": 10, "y": 10},
                 {"t": 5000.0, "kind": "up", "code": "left", "x": 10, "y": 10}]
    p = replay.Player(lambda: game["hwnd"])
    assert p.start(long_hold, "забег", loops=1, require_focus=False, duration_ms=5000.0)
    time.sleep(0.15)
    assert fake.downs and not fake.ups, "кнопка должна быть зажата"

    game["hwnd"] = 2002
    time.sleep(0.15)
    assert fake.ups, "при смене окна всё зажатое обязано отпуститься"

    p.stop()


def test_a_run_without_any_window_still_plays(rig):
    """Запуск вообще без окна игры (так устроены остальные тесты) не должен
    замирать: замирать надо, когда окно БЫЛО и пропало."""
    fake, game = rig
    game["hwnd"] = 0
    p = replay.Player(lambda: game["hwnd"])
    assert p.start(EVENTS, "забег", loops=1, require_focus=False, duration_ms=400.0)
    _drain(p)
    assert fake.downs, "без окна с самого начала запись всё равно должна отыграться"
