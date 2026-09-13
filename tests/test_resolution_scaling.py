"""Тесты масштабирования и компенсации соотношения сторон при кастомных разрешениях игры."""

import pytest
import numpy as np

from core import vision
from core import config
from core import window as wm


def test_aspect_ratio_correction_calculates_horizontal_distortion_for_nonstandard_aspect_ratios():
    """При нестандартных разрешениях (например 1024x768 вместо эталонного 1152x756)
    соотношение сторон отличается (1.33 против 1.52). Фиксированные пиксельные элементы
    Roblox при растягивании до эталонного пространства 1152x756 искажаются по горизонтали.
    Функция set_aspect_ratio_correction должна точно вычислять коэффициент коррекции,
    а _get_multiscale_pairs — добавлять пары масштабов с компенсацией."""
    # Эталонное разрешение: коэффициент 1.0, никаких дополнительных искажений
    vision.set_aspect_ratio_correction(1.0)
    assert vision.get_aspect_ratio_correction() == 1.0
    pairs_default = vision._get_multiscale_pairs()
    # При 1.0 все пары изотропные (scale_x == scale_y)
    for sx, sy in pairs_default:
        assert sx == sy

    # Разрешение 1024x768:
    # (1152 / 1024) / (756 / 768) = 1.125 / 0.984375 ≈ 1.142857
    expected_corr = (1152 / 1024) / (756 / 768)
    vision.set_aspect_ratio_correction(expected_corr)
    assert abs(vision.get_aspect_ratio_correction() - expected_corr) < 1e-5

    pairs_custom = vision._get_multiscale_pairs()
    # Должна появиться пара масштабов, компенсирующая горизонтальное сжатие шаблона
    has_compensated = any(abs(sx - expected_corr) < 1e-4 and sy == 1.0 for sx, sy in pairs_custom)
    assert has_compensated, "В мультискейл-парах должна присутствовать компенсация соотношения сторон"

    # Сбрасываем обратно
    vision.set_aspect_ratio_correction(1.0)


def test_ref_to_screen_scales_coordinates_accurately_to_target_resolution(monkeypatch):
    """Координаты кликов рассчитываются от эталонного пространства 1152x756.
    При игре в окне 1024x768 клик в центр эталона (576, 378) должен попадать
    ровно в центр реального клиентского окна (512, 384), а не смещаться."""
    # Клиентское окно размером 1024x768 со смещением (100, 200) на экране
    monkeypatch.setattr(wm, "get_client_rect_screen", lambda hwnd: (100, 200, 100 + 1024, 200 + 768))

    ref_center_x, ref_center_y = 576, 378
    screen_x, screen_y = vision.ref_to_screen(1, ref_center_x, ref_center_y)

    assert screen_x == 100 + 512
    assert screen_y == 200 + 384


def test_scaled_templates_supports_2d_aspect_ratio_scaling(monkeypatch):
    """При поиске с компенсацией соотношения сторон шаблоны масштабируются независимо
    по X и Y. Кэш шаблонов должен корректно создавать и сохранять 2D-масштабированные изображения."""
    dummy_template = np.ones((100, 100), dtype=np.uint8)
    monkeypatch.setattr(vision, "load_template_grays", lambda name, template_dir: [(dummy_template, None)])

    # Масштабируем по X в 1.14 раза, по Y оставляем 1.0
    scaled = vision._scaled_templates("test_button", None, 1.14, 1.0)
    assert len(scaled) == 1
    scaled_img, _ = scaled[0]
    # Высота остаётся 100, ширина становится 114
    assert scaled_img.shape == (100, 114)


def test_api_resolution_get_and_set(monkeypatch):
    """Методы Api get_game_resolution и set_game_resolution должны валидировать и
    ограничивать размеры (не меньше 640x480 и не больше 2560x1440), обновлять настройки
    и выставлять коррекцию в vision."""
    from main import Api
    from core import settings as cfg

    api = Api()

    # Проверяем получение текущего разрешения
    res = api.get_game_resolution()
    assert "width" in res and "height" in res

    # Устанавливаем 1024x768
    set_res = api.set_game_resolution(1024, 768)
    assert set_res["success"] is True
    assert set_res["width"] == 1024
    assert set_res["height"] == 768
    assert api.game_width == 1024
    assert api.game_height == 768
    assert cfg.load().get("game_width") == 1024
    assert cfg.load().get("game_height") == 768

    # Проверяем, что в vision обновилась коррекция
    expected_corr = (config.FIXED_WIN_W / 1024) / (config.FIXED_WIN_H / 768)
    assert abs(vision.get_aspect_ratio_correction() - expected_corr) < 1e-4

    # Проверяем clamp слишком маленького разрешения
    set_small = api.set_game_resolution(100, 200)
    assert set_small["width"] == 640
    assert set_small["height"] == 480

    # Возвращаем стандартное разрешение
    api.set_game_resolution(1152, 756)
    assert api.game_width == 1152
    assert api.game_height == 756


def test_click_match_scales_to_custom_resolution(monkeypatch):
    """Проверяет, что click_match масштабирует точку совпадения из эталонного пространства
    1152x756 в реальные координаты экрана окна 1024x768."""
    clicked = []

    class FakeMouse:
        def click(self, x, y):
            clicked.append((x, y))

    monkeypatch.setattr(wm, "get_client_rect_screen", lambda hwnd: (100, 200, 100 + 1024, 200 + 768))

    match = {"cx": 576, "cy": 378}
    vision.click_match(FakeMouse(), hwnd=1, match=match)

    assert len(clicked) == 1
    # 576 * (1024/1152) = 512; 378 * (768/756) = 384
    assert clicked[0] == (100 + 512, 200 + 384)
