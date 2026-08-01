"""Запись и повтор при ВСТРОЕННОМ окне игры.

Что сломалось и почему это не заметили. В обычном режиме окно Roblox не
отдельное: оно вставлено внутрь окна макроса через SetParent (core/dock.py).
Обе проверки в replay спрашивали Windows «какое окно верхнего уровня?» и обе
получали ответ «окно макроса» — потому что для встроенной игры это правда:

  * запись считала любой клик в игру кликом по своей кнопке и выбрасывала
    его. В файле оставались одни клавиши: 28 событий, все — цифры;
  * повтор с галкой «только при активном окне» ждал, когда встроенное окно
    станет активным, а оно верхнего уровня не бывает никогда.

В режиме «вырез» (game_cutout) игра остаётся отдельным окном, и там всё
работало — оттуда и «вроде работает, но мышь не пишется».

Настоящие вызовы Windows тут подменены: тест должен идти и на CI, где нет ни
Roblox, ни курсора.
"""
import pytest

from core import replay

GUI = 1001         # окно макроса
GAME = 2002        # окно игры (в обычном режиме — потомок GUI)
GAME_INNER = 2003  # внутренняя поверхность Roblox, её и вернёт WindowFromPoint
OTHER = 3003       # чужое окно


@pytest.fixture
def docked(monkeypatch):
    """Игра встроена в окно макроса: корень для всего внутри — GUI."""
    monkeypatch.setattr(replay, "_is_child",
                        lambda parent, child: parent == GAME and child == GAME_INNER)
    monkeypatch.setattr(replay, "_root_of",
                        lambda h: GUI if h in (GUI, GAME, GAME_INNER) else h)


def test_click_in_embedded_game_is_recorded(docked, monkeypatch):
    # Курсор в игре. Корень — наше окно, но это ввод в игру, а не в макрос.
    monkeypatch.setattr(replay, "_window_at_cursor", lambda: GAME_INNER)
    assert replay._cursor_over_gui(GUI, GAME) is False


def test_click_on_own_button_is_not_recorded(docked, monkeypatch):
    # Курсор на самой панели макроса — вот это в запись попадать не должно.
    monkeypatch.setattr(replay, "_window_at_cursor", lambda: GUI)
    assert replay._cursor_over_gui(GUI, GAME) is True


def test_click_in_third_party_window_is_recorded(docked, monkeypatch):
    monkeypatch.setattr(replay, "_window_at_cursor", lambda: OTHER)
    assert replay._cursor_over_gui(GUI, OTHER) is False


def test_cutout_mode_still_distinguishes_windows(monkeypatch):
    """Режим «вырез»: игра — отдельное окно верхнего уровня."""
    monkeypatch.setattr(replay, "_is_child", lambda parent, child: False)
    monkeypatch.setattr(replay, "_root_of", lambda h: h)

    monkeypatch.setattr(replay, "_window_at_cursor", lambda: GAME)
    assert replay._cursor_over_gui(GUI, GAME) is False
    monkeypatch.setattr(replay, "_window_at_cursor", lambda: GUI)
    assert replay._cursor_over_gui(GUI, GAME) is True


def test_no_gui_window_records_everything(monkeypatch):
    """Окна макроса ещё нет — глушить нечего, пишем всё."""
    monkeypatch.setattr(replay, "_window_at_cursor", lambda: GAME)
    assert replay._cursor_over_gui(0, GAME) is False


def test_focus_check_accepts_embedded_game(docked, monkeypatch):
    """Активно окно макроса, игра внутри него — повтор должен идти."""
    monkeypatch.setattr(replay.wm, "is_foreground", lambda h: h == GUI)
    assert replay._game_focused(GAME) is True


def test_focus_check_rejects_other_window(docked, monkeypatch):
    """Сверху чужое окно — повтор ждёт, как и обещает галка."""
    monkeypatch.setattr(replay.wm, "is_foreground", lambda h: h == OTHER)
    assert replay._game_focused(GAME) is False


def test_focus_check_accepts_standalone_game(monkeypatch):
    """Режим «вырез»: игра сама себе окно верхнего уровня."""
    monkeypatch.setattr(replay, "_root_of", lambda h: h)
    monkeypatch.setattr(replay.wm, "is_foreground", lambda h: h == GAME)
    assert replay._game_focused(GAME) is True
