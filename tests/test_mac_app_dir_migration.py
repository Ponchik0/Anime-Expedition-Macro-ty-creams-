"""Переезд папки данных mac-сборки на новое имя.

ЗАЧЕМ ЭТИ ТЕСТЫ. Сборка переименована с «Creams Macro - Anime Expeditions» на
«Anime Expeditions Macro», и папка данных вслед за ней. Но у того, кто уже
пользовался mac-сборкой, настройки, шаблоны, маршруты и эталоны лежат под
старым именем: сменить строку без переезда значит запустить приложение с
чистого листа. Данные при этом не удаляются, но пропадают из виду — на ощупь
это одно и то же.

Проверить руками нельзя: ветка работает только на macOS и только в собранном
виде. Поэтому логика вынесена в _resolve_mac_app_dir, а проверяется здесь.
"""
import os

import pytest

from core import constants

LEGACY = constants._MAC_APP_DIR_LEGACY
NEW = constants._MAC_APP_DIR


def _make(root, name, filename="settings.json", text="данные"):
    d = root / name
    d.mkdir()
    (d / filename).write_text(text, encoding="utf-8")
    return d


def test_old_folder_moves_over_with_everything_in_it(tmp_path):
    """Главное: пользователь со старой сборки не теряет ничего."""
    _make(tmp_path, LEGACY)

    result = constants._resolve_mac_app_dir(str(tmp_path))

    assert result == str(tmp_path / NEW)
    assert (tmp_path / NEW / "settings.json").read_text(encoding="utf-8") == "данные"
    assert not (tmp_path / LEGACY).exists(), "старая папка должна ПЕРЕЕХАТЬ, а не скопироваться"


def test_fresh_install_just_gets_the_new_name(tmp_path):
    """Нет старой папки — не выдумываем переезд."""
    assert constants._resolve_mac_app_dir(str(tmp_path)) == str(tmp_path / NEW)
    assert not (tmp_path / LEGACY).exists()


def test_the_move_happens_once_and_never_touches_live_data_again(tmp_path):
    """Обе папки на месте — новая уже используется, старая осталась хвостом.

    Тронуть её здесь значило бы затереть настройки, которыми человек
    пользуется прямо сейчас, содержимым, которое он бросил."""
    _make(tmp_path, LEGACY, text="старое")
    _make(tmp_path, NEW, text="актуальное")

    result = constants._resolve_mac_app_dir(str(tmp_path))

    assert result == str(tmp_path / NEW)
    assert (tmp_path / NEW / "settings.json").read_text(encoding="utf-8") == "актуальное"
    assert (tmp_path / LEGACY).exists(), "старую папку не удаляем — это данные пользователя"


def test_a_failed_move_keeps_using_the_folder_that_has_the_data(tmp_path, monkeypatch):
    """Переезд не удался (папка занята, нет прав) — остаёмся на старой.

    Пустое новое место было бы хуже отказа: приложение выглядело бы рабочим и
    молча забыло всё, что человек настроил."""
    _make(tmp_path, LEGACY, text="данные")

    def boom(*_a, **_kw):
        raise OSError("не отдали")

    monkeypatch.setattr(constants.os, "rename", boom)

    result = constants._resolve_mac_app_dir(str(tmp_path))

    assert result == str(tmp_path / LEGACY)
    assert (tmp_path / LEGACY / "settings.json").read_text(encoding="utf-8") == "данные"


def test_a_stray_file_named_like_the_new_folder_does_not_eat_the_move(tmp_path):
    """os.path.exists, а не isdir, на новом пути — намеренно: если там лежит
    ФАЙЛ с таким именем, os.rename на большинстве систем не пройдёт или
    затрёт его. Проверяем, что до rename в этом случае не доходит."""
    _make(tmp_path, LEGACY)
    (tmp_path / NEW).write_text("не папка", encoding="utf-8")

    result = constants._resolve_mac_app_dir(str(tmp_path))

    assert result == str(tmp_path / NEW)
    assert (tmp_path / LEGACY).exists(), "старая папка должна остаться нетронутой"
