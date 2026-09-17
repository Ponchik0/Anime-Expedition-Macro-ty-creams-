import threading
import time
from unittest.mock import MagicMock

from core import runner as runner_module
from core import vision


def _runner():
    r = runner_module.MacroRunner.__new__(runner_module.MacroRunner)
    r._log = MagicMock()
    r._set_status = MagicMock()
    r._checkpoint = MagicMock(return_value=False)
    r._dismiss_lobby_overlay = MagicMock(return_value=False)
    r._attempt_rejoin = MagicMock(return_value=False)
    r._current_task = {}
    return r


def test_ensure_lobby_dismisses_overlay_and_finds_anchor_fallback(monkeypatch):
    """Проверяет, что при сжатом или нестандартном окне (1024x672), когда Play
    не находится с порогом 0.90, макрос закрывает оверлеи и находит лобби по
    альтернативным якорям с порогом 0.78, предотвращая зависание и ложный реконнект.
    """
    runner = _runner()
    dismissed = []
    runner._dismiss_lobby_overlay = lambda _h: dismissed.append(True) or True

    monkeypatch.setattr(vision, 'wait_for_image_any', lambda *_a, **_kw: (None, None))

    def fake_find_image(_hwnd, name, threshold=vision.DEFAULT_THRESHOLD, **_kw):
        if name == 'nav_event' and threshold <= 0.78:
            return {'x': 100, 'y': 100, 'cx': 120, 'cy': 120, 'score': 0.82}
        return None

    monkeypatch.setattr(vision, 'find_image', fake_find_image)

    stop_event = threading.Event()
    assert runner._ensure_lobby(12345, stop_event) is True
    assert len(dismissed) >= 1
    assert runner._attempt_rejoin.called is False


def test_lobby_overlay_dismiss_uses_generic_close_templates(monkeypatch):
    """Проверяет, что автозакрытие баннеров в лобби реально работает: отдельной
    вырезки update_log_close на диске нет, поэтому закрытие обязано находиться
    по общим шаблонам (click_anywhere_to_close / nav_closeui). Если список
    сузить до несуществующего имени, find_image_any бросит TemplateNotFound и
    баннер обновления так и останется висеть над Play.
    """
    from core import runner_constants as rc

    assert 'click_anywhere_to_close' in rc.LOBBY_OVERLAY_CLOSE_IMAGE_NAMES
    assert 'nav_closeui' in rc.LOBBY_OVERLAY_CLOSE_IMAGE_NAMES

    runner = _runner()
    # _runner() подменяет метод моком: снимаем подмену, тестируем настоящий код.
    del runner._dismiss_lobby_overlay
    runner._mouse = MagicMock()
    clicked = []

    def fake_find_image_any(_hwnd, names, **_kw):
        assert 'click_anywhere_to_close' in names
        return ({'x': 10, 'y': 10, 'cx': 20, 'cy': 20, 'score': 0.91}, 'click_anywhere_to_close')

    monkeypatch.setattr(vision, 'find_image_any', fake_find_image_any)
    monkeypatch.setattr(vision, 'click_match', lambda _mouse, _hwnd, _m: clicked.append(True))
    monkeypatch.setattr(runner_module.time, 'sleep', lambda _s: None)

    assert runner._dismiss_lobby_overlay(12345) is True
    assert clicked == [True]


def test_lobby_overlay_dismiss_quiet_without_templates(monkeypatch):
    """Если ни одного шаблона-закрывашки нет на диске, проверка лобби не должна
    падать: find_image_any бросает TemplateNotFound, и оверлей просто пропускается.
    """
    runner = _runner()

    def raise_missing(_hwnd, _names, **_kw):
        raise vision.TemplateNotFound('update_log_close')

    monkeypatch.setattr(vision, 'find_image_any', raise_missing)
    assert runner._dismiss_lobby_overlay(12345) is False


def test_infinite_wave_limit_triggers_time_fallback_when_ocr_unavailable(monkeypatch):
    """Проверяет, что если OCR в Windows не установлен (no installed language packs)
    и волна не распознается, макрос не зависает навсегда, а по истечении
    расчетного таймера волны (fallback_timeout) делает рестарт матча.
    """
    runner = _runner()
    runner._exit_infinite_wave_limit = MagicMock(return_value='restarted')

    monkeypatch.setattr(runner_module.vision, 'capture_window_region_bgr', lambda *_a: object())
    monkeypatch.setattr(runner_module.wave_module, 'read_wave', lambda _img: (None, None))

    state = {'start_time': time.time() - 500, 'next_check': 0}
    stop_event = threading.Event()

    result = runner._check_infinite_wave_limit(12345, stop_event, limit=30, state=state)
    assert result == 'restarted'
    runner._exit_infinite_wave_limit.assert_called_once_with(12345, stop_event, 30)
