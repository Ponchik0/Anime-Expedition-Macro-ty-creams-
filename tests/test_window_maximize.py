"""ТЕСТЫ РАЗВЕРТЫВАНИЯ И ВОССТАНОВЛЕНИЯ ОКНА МАКРОСА.

Пользователь может захотеть развернуть макрос на весь экран монитора, чтобы
окно не было ограничено фиксированными размерами 1600x960. Для этого используются
нативные Win32-вызовы ShowWindow с SW_MAXIMIZE (3) и SW_RESTORE (9), а также IsZoomed.

Настоящие вызовы Windows подменены через monkeypatch: тесты должны идти и на CI,
где нет графического интерфейса.
"""
import sys
import pytest

from core import window as wm


def test_is_zoomed_reads_window_state(monkeypatch):
    """Ловит баг, когда макрос не может определить, развернуто ли окно на весь экран,
    и повторно пытается развернуть уже развернутое окно вместо восстановления."""
    if sys.platform != "win32":
        pytest.skip("Win32-only test")

    import core.window_win as win_mod

    state = {"zoomed": 0}

    class FakeUser32:
        def IsZoomed(self, hwnd):
            return state["zoomed"]

    monkeypatch.setattr(win_mod, "user32", FakeUser32())

    assert wm.is_zoomed(12345) is False

    state["zoomed"] = 1
    assert wm.is_zoomed(12345) is True


def test_maximize_window_issues_sw_maximize(monkeypatch):
    """Проверяет, что maximize_window вызывает ShowWindow с точным кодом SW_MAXIMIZE = 3,
    а не другим случайным кодом, ломающим состояние окна."""
    if sys.platform != "win32":
        pytest.skip("Win32-only test")

    import core.window_win as win_mod

    calls = []

    class FakeUser32:
        def ShowWindow(self, hwnd, cmd):
            calls.append((hwnd, cmd))

    monkeypatch.setattr(win_mod, "user32", FakeUser32())

    wm.maximize_window(55555)
    assert calls == [(55555, 3)]


def test_restore_window_issues_sw_restore(monkeypatch):
    """Проверяет, что restore_window вызывает ShowWindow с точным кодом SW_RESTORE = 9,
    чтобы окно вернулось к нормальным 1600x960."""
    if sys.platform != "win32":
        pytest.skip("Win32-only test")

    import core.window_win as win_mod

    calls = []

    class FakeUser32:
        def ShowWindow(self, hwnd, cmd):
            calls.append((hwnd, cmd))

    monkeypatch.setattr(win_mod, "user32", FakeUser32())

    wm.restore_window(77777)
    assert calls == [(77777, 9)]


def test_api_toggle_maximize_window_toggles_between_maximize_and_restore(monkeypatch):
    """Проверяет мост JS Api.toggle_maximize_window():
    - если окно нормальное -> разворачивает (SW_MAXIMIZE) и возвращает True
    - если окно уже развернуто -> восстанавливает (SW_RESTORE) и возвращает False."""
    from main import Api

    api = Api.__new__(Api)
    api.gui_hwnd = 10101
    api._window = None

    state = {"zoomed": False, "last_cmd": None}

    def fake_is_zoomed(hwnd):
        return state["zoomed"]

    def fake_maximize(hwnd):
        state["zoomed"] = True
        state["last_cmd"] = 3

    def fake_restore(hwnd):
        state["zoomed"] = False
        state["last_cmd"] = 9

    monkeypatch.setattr(wm, "is_zoomed", fake_is_zoomed)
    monkeypatch.setattr(wm, "maximize_window", fake_maximize)
    monkeypatch.setattr(wm, "restore_window", fake_restore)
    monkeypatch.setattr(sys, "platform", "win32")

    # 1. Окно в обычном состоянии -> разворачиваем
    res1 = api.toggle_maximize_window()
    assert res1 is True
    assert state["zoomed"] is True
    assert state["last_cmd"] == 3

    # 2. Окно развернуто -> восстанавливаем
    res2 = api.toggle_maximize_window()
    assert res2 is False
    assert state["zoomed"] is False
    assert state["last_cmd"] == 9


def test_api_toggle_maximize_preserves_game_resolution_and_redocks(monkeypatch):
    """Ловит баг, когда при развертывании окна макроса на весь экран или восстановлении
    разрешение и клиентский размер встроенного окна Roblox сбрасываются к дефолтным
    или окно искажается из-за изменения родительского окна."""
    from main import Api
    import main as main_mod

    api = Api.__new__(Api)
    api.gui_hwnd = 10101
    api.game_hwnd = 20202
    api.game_width = 1024
    api.game_height = 768
    api._window = None

    state = {"zoomed": False}
    dock_calls = []
    resize_calls = []

    class FakeDocker:
        def dock(self, game_hwnd, gui_hwnd, x, y, width, height):
            dock_calls.append((game_hwnd, gui_hwnd, x, y, width, height))

    class FakeRobloxWM:
        def __init__(self, title):
            self.hwnd = None
        def resize_client_to(self, w, h):
            resize_calls.append((self.hwnd, w, h))

    api.docker = FakeDocker()

    monkeypatch.setattr(wm, "is_zoomed", lambda hwnd: state["zoomed"])
    monkeypatch.setattr(wm, "maximize_window", lambda hwnd: state.update(zoomed=True))
    monkeypatch.setattr(wm, "restore_window", lambda hwnd: state.update(zoomed=False))
    monkeypatch.setattr(wm, "is_window", lambda hwnd: True)
    monkeypatch.setattr(main_mod, "WindowManager", FakeRobloxWM)
    monkeypatch.setattr(sys, "platform", "win32")

    # Вызываем переключение
    is_max = api.toggle_maximize_window()
    assert is_max is True
    assert resize_calls == [(20202, 1024, 768)]
    assert dock_calls == [(20202, 10101, 0, 44, 1024, 768)]

