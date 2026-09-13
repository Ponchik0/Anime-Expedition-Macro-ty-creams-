import threading
from unittest.mock import MagicMock
import numpy as np
import pytest

from core import runner as runner_module
from core import wave as wave_module
from core.runner import MacroRunner


def _runner():
    runner = MacroRunner.__new__(MacroRunner)
    runner._mouse = MagicMock()
    runner._keyboard = MagicMock()
    runner._log = MagicMock()
    runner._debug_save = lambda *_args: None
    return runner


def test_find_start_game_button_adjusts_cy_for_large_prompt_modal(monkeypatch):
    """Ловит баг, когда совпадение с шаблоном модального окна start_game_prompt
    (диалог 'Start Game?') кликало в геометрический центр модалки (в аватар или текст),
    вместо зеленой кнопки старта в нижней части окна.
    """
    runner = _runner()
    # Модальное окно высотой 140px, начинающееся с y=200
    modal_match = {"x": 400, "y": 200, "w": 280, "h": 140, "cx": 540, "cy": 270, "score": 0.85}

    def fake_find_image(_hwnd, name, **_kwargs):
        if name == "start_game_prompt":
            return dict(modal_match)
        return None

    monkeypatch.setattr(runner_module.vision, "find_image", fake_find_image)
    name, match = runner._find_start_game_button(123)

    assert name == "start_game_prompt"
    assert match is not None
    # cy должен быть смещен к нижней границе модалки: 200 + 140 - 20 = 320
    assert match["cy"] == 320


def test_find_start_game_button_falls_back_to_green_color_blob(monkeypatch):
    """Ловит баг, когда при изменении скинов, шейдеров или разрешения эталонные
    картинки nav_start_game не находились, и макрос ошибочно решал, что раунд уже
    начался, оставляя модальное окно висеть на экране и блокировать игру.
    """
    runner = _runner()
    monkeypatch.setattr(runner_module.vision, "find_image", lambda *_a, **_kw: None)

    # Имитируем захват кадра с зеленой прямоугольной кнопкой по центру
    fake_bgr = np.zeros((450, 552, 3), dtype=np.uint8)
    # Рисуем зеленый прямоугольник кнопки: G=200, R=50, B=50
    fake_bgr[50:80, 100:300, 1] = 200
    fake_bgr[50:80, 100:300, 2] = 50
    fake_bgr[50:80, 100:300, 0] = 50

    monkeypatch.setattr(runner_module.vision, "capture_game_bgr", lambda _hwnd, _reg: fake_bgr)
    name, match = runner._find_start_game_button(123)

    assert name == "start_game_green_btn"
    assert match is not None
    assert match["score"] == 1.0
    # Координаты должны быть в пространстве 1152x756 с учетом смещения rx=300, ry=150
    assert match["x"] == 400
    assert match["y"] == 200
    assert match["w"] == 200
    assert match["h"] == 30


def test_read_wave_returns_none_gracefully_when_no_ocr_available(monkeypatch):
    """Ловит баг, когда при отсутствии Tesseract в сборке без WinRT
    read_wave выбрасывал необработанное исключение TesseractNotAvailable,
    ломая цикл проверки волн.
    """
    monkeypatch.setattr(wave_module.ocr_windows, "is_available", lambda: False)

    def fake_get_pytesseract():
        raise RuntimeError("Tesseract not installed")

    monkeypatch.setattr(wave_module, "get_pytesseract", fake_get_pytesseract)

    fake_region = np.zeros((100, 100, 3), dtype=np.uint8)
    curr, max_w = wave_module.read_wave(fake_region)
    assert curr is None
    assert max_w is None
