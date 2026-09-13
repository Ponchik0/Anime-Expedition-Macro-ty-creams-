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
