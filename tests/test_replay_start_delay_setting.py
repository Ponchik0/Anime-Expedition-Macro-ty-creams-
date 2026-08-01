"""НАСТРОЙКА ПАУЗЫ ПЕРЕД СТАРТОМ ПОВТОРА.

Сколько именно ждать, зависит от машины: где-то окно Roblox выныривает за
двести миллисекунд, где-то за полторы секунды. Поэтому число настраиваемое, а
не зашитое, — но настройка обязана переживать мусор в файле настроек и не
превращаться в «макрос не работает» от забытой большой цифры.
"""
import pytest

import main
from core import replay
from core import settings as cfg


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    return main.Api.__new__(main.Api)              # без __init__: он поднимает окно и потоки


def test_the_default_comes_from_the_code_not_the_settings_file(api):
    """Свежая установка: настройки пустые — берём константу из core/replay."""
    assert api._replay_start_delay_sec() == replay.START_DELAY_MS / 1000.0


def test_a_saved_value_is_used(api):
    assert api.set_replay_option("replay_start_delay", "3.5")["ok"]
    assert api._replay_start_delay_sec() == 3.5


def test_zero_is_a_legitimate_value(api):
    """Ноль — это «начинать сразу», то есть прежнее поведение. Он не должен
    молча подменяться значением по умолчанию."""
    assert api.set_replay_option("replay_start_delay", 0)["ok"]
    assert api._replay_start_delay_sec() == 0.0


def test_an_empty_field_reads_as_zero(api):
    """Стёр поле — это «убрал паузу», а не «сломал настройку»."""
    assert api.set_replay_option("replay_start_delay", "")["ok"]
    assert api._replay_start_delay_sec() == 0.0


def test_absurd_values_are_clamped(api):
    """Верхняя граница — минута: больше это уже не «дать игре появиться», а
    забытая настройка, из-за которой макрос выглядит сломанным."""
    api.set_replay_option("replay_start_delay", 9999)
    assert api._replay_start_delay_sec() == 60.0
    api.set_replay_option("replay_start_delay", -5)
    assert api._replay_start_delay_sec() == 0.0


def test_garbage_in_the_settings_file_falls_back_to_the_default(api):
    """Файл настроек правят руками, и там может оказаться что угодно. Повтор
    обязан завестись, а не упасть на приведении типа."""
    cfg.update({"replay_start_delay": "две секунды"})
    assert api._replay_start_delay_sec() == replay.START_DELAY_MS / 1000.0


def test_garbage_from_the_ui_is_refused_not_saved(api):
    """А вот из интерфейса мусор принимать нельзя: молча записать его значит
    получить неверную настройку, о которой человек не узнает."""
    api.set_replay_option("replay_start_delay", 4)
    assert not api.set_replay_option("replay_start_delay", "abc")["ok"]
    assert api._replay_start_delay_sec() == 4.0, "прежнее значение должно уцелеть"


def test_an_unknown_option_is_still_refused(api):
    assert not api.set_replay_option("replay_whatever", 1)["ok"]


def test_the_ui_is_told_the_current_delay(api):
    """Окно записей рисует поле по этому же ответу — без него оно всегда
    показывало бы значение по умолчанию, чем бы настройка ни была."""
    api.set_replay_option("replay_start_delay", 1.5)
    assert api.get_run_mode()["start_delay"] == 1.5
