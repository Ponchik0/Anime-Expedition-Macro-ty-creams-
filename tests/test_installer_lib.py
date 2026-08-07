"""Установщик: безопасность распаковки и что именно он удаляет.

ПОЧЕМУ ИМЕННО ЭТО. В installer_lib две вещи, ошибка в которых дорого стоит и
незаметна на глаз:

  1. Имена файлов внутри zip — НЕДОВЕРЕННЫЙ ввод. Запись вида
     «..\\..\\Windows\\...» или «D:\\payload.exe» обязана быть отброшена, иначе
     установщик пишет куда угодно на диске.
  2. Удаление. Список того, что сносится при деинсталляции, решает судьбу
     настроек, шаблонов и записанных маршрутов — вещей, которые человек делал
     руками и восстановить не сможет.

Обе проверяются здесь, а не глазами на живой установке: ошибку такого рода
замечают уже после того, как что-то потеряно.
"""
import os
import sys
import zipfile

import pytest

import installer_lib as lib


def _zip(path, entries):
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return str(path)


# ────────────────────────── Куда можно писать ──────────────────────────────

def test_a_normal_release_lands_where_it_should(tmp_path):
    src = _zip(tmp_path / "r.zip", {
        "Anime Expeditions Macro.exe": "exe",
        "Assets/ui/start.png": "png",
        "VERSION": "1.1.3",
    })
    dest = tmp_path / "install"

    written = lib.extract_release(src, str(dest))

    assert written == 3
    assert (dest / "Anime Expeditions Macro.exe").read_text() == "exe"
    assert (dest / "Assets" / "ui" / "start.png").read_text() == "png"


@pytest.mark.parametrize("evil", [
    "../escaped.txt",
    "../../escaped.txt",
    "a/../../escaped.txt",
    "a/b/../../../escaped.txt",
])
def test_entries_climbing_out_of_the_folder_are_dropped(tmp_path, evil):
    """Классический zip-slip: точки в имени уводят запись выше папки."""
    src = _zip(tmp_path / "r.zip", {evil: "payload", "ok.txt": "ok"})
    dest = tmp_path / "install"

    lib.extract_release(src, str(dest))

    assert (dest / "ok.txt").exists(), "обычный файл должен был распаковаться"
    assert not (tmp_path / "escaped.txt").exists(), "запись вырвалась из папки установки"


def test_an_absolute_path_inside_the_archive_is_dropped(tmp_path):
    """Тот случай, который обходит проверку «двоеточие в первом сегменте»:
    os.path.join начинает путь заново с абсолютного сегмента, поэтому
    «a/b/D:/payload.exe» приземлился бы мимо папки установки."""
    src = _zip(tmp_path / "r.zip", {"a/b/D:/payload.exe": "x", "ok.txt": "ok"})
    dest = tmp_path / "install"

    lib.extract_release(src, str(dest))

    assert (dest / "ok.txt").exists()
    assert not any(p.name == "payload.exe" for p in dest.rglob("*"))


def test_is_inside_is_not_fooled_by_a_sibling_with_the_same_prefix(tmp_path):
    """«C:\\app-old» не внутри «C:\\app», хотя строка начинается так же."""
    root = tmp_path / "app"
    root.mkdir()
    (tmp_path / "app-old").mkdir()

    assert lib.is_inside(str(root), str(root / "file.txt"))
    assert not lib.is_inside(str(root), str(tmp_path / "app-old" / "file.txt"))


# ────────────────────── Свои эталоны не перетираются ───────────────────────

def test_a_users_own_reference_image_survives_installation(tmp_path):
    """Assets — папка, куда человек кладёт СВОИ картинки взамен неподошедших.
    Перезаписать её из архива значит выбросить ровно ту правку, ради которой
    папка и существует."""
    dest = tmp_path / "install"
    (dest / "Assets" / "ui").mkdir(parents=True)
    (dest / "Assets" / "ui" / "start.png").write_text("мой кроп", encoding="utf-8")

    src = _zip(tmp_path / "r.zip", {
        "Assets/ui/start.png": "из архива",
        "Assets/ui/new.png": "новая картинка",
    })
    lib.extract_release(src, str(dest))

    assert (dest / "Assets" / "ui" / "start.png").read_text(encoding="utf-8") == "мой кроп"
    assert (dest / "Assets" / "ui" / "new.png").read_text(encoding="utf-8") == "новая картинка", \
        "новые эталоны из релиза добавляться всё же должны"


def test_the_app_itself_is_always_replaced(tmp_path):
    """Обратная сторона: exe — не пользовательский файл, и обновление обязано
    его заменить, иначе установка «прошла», а версия прежняя."""
    dest = tmp_path / "install"
    dest.mkdir()
    (dest / "Anime Expeditions Macro.exe").write_text("старый", encoding="utf-8")

    src = _zip(tmp_path / "r.zip", {"Anime Expeditions Macro.exe": "новый"})
    lib.extract_release(src, str(dest))

    assert (dest / "Anime Expeditions Macro.exe").read_text(encoding="utf-8") == "новый"


# ──────────────────────────── Что сносит удаление ──────────────────────────

def test_uninstall_keeps_what_the_user_made(tmp_path):
    """Значение по умолчанию: настройки, шаблоны, маршруты и записи остаются.
    Человек, удаляющий приложение, чтобы поставить заново, не ожидает
    потерять собранные сценарии."""
    d = tmp_path / "install"
    d.mkdir()
    for name in ("settings.json", "VERSION", "Anime Expeditions Macro.exe"):
        (d / name).write_text("x")
    for name in ("Paths", "Templates", "Assets"):
        (d / name).mkdir()

    doomed = {os.path.basename(p) for p in lib.removable_entries(str(d), keep_user_data=True)}

    assert "settings.json" not in doomed
    assert "Paths" not in doomed
    assert "Templates" not in doomed
    assert "VERSION" in doomed
    assert "Anime Expeditions Macro.exe" in doomed


def test_uninstall_can_wipe_everything_when_explicitly_asked(tmp_path):
    d = tmp_path / "install"
    d.mkdir()
    (d / "settings.json").write_text("x")
    (d / "VERSION").write_text("x")

    doomed = {os.path.basename(p) for p in lib.removable_entries(str(d), keep_user_data=False)}

    assert doomed == {"settings.json", "VERSION"}


def test_uninstalling_a_folder_that_is_gone_does_not_explode(tmp_path):
    assert lib.removable_entries(str(tmp_path / "нет-такой"), keep_user_data=True) == []


# ────────────────────────────── Поиск приложения ───────────────────────────

def test_the_app_is_found_by_its_known_name(tmp_path):
    (tmp_path / lib.EXE_NAME).write_text("x")
    assert lib.app_exe_path(str(tmp_path)) == str(tmp_path / lib.EXE_NAME)


def test_a_renamed_build_is_still_found(tmp_path):
    """Имя сборки уже менялось однажды и поменяется снова. Единственный .exe
    рядом — это оно, как бы его ни звали."""
    (tmp_path / "Что-то другое.exe").write_text("x")
    assert lib.app_exe_path(str(tmp_path)) == str(tmp_path / "Что-то другое.exe")


def test_an_empty_folder_still_reports_where_the_app_will_land(tmp_path):
    """До установки exe нет, но вызывающему нужен путь «куда оно приедет»."""
    assert lib.app_exe_path(str(tmp_path)) == str(tmp_path / lib.EXE_NAME)


# ──────────────────── Установка целиком: ярлыки, копия, реестр ─────────────
# Проверяется do_install из installer.py, но БЕЗ скачивания и без записи в
# настоящий реестр и на настоящий рабочий стол: всё внешнее подменено на
# временные папки. Иначе тест либо тянул бы 115 МБ, либо гадил в систему.

def _fake_release(dest_dir, tag="v9.9.9"):
    """Подмена install_release: кладёт минимальную «сборку» и возвращает тег."""
    os.makedirs(os.path.join(dest_dir, "Assets", "ui"), exist_ok=True)
    with open(os.path.join(dest_dir, lib.EXE_NAME), "w", encoding="utf-8") as f:
        f.write("exe")
    return tag


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Рабочий стол, меню «Пуск» и реестр — во временную папку."""
    import installer

    desktop = tmp_path / "Desktop"
    startmenu = tmp_path / "StartMenu"
    desktop.mkdir()
    startmenu.mkdir()
    made = []

    monkeypatch.setattr(lib, "desktop_dir", lambda: str(desktop))
    monkeypatch.setattr(lib, "start_menu_dir", lambda: str(startmenu))
    monkeypatch.setattr(lib, "install_release",
                        lambda d, on_status=None, on_progress=None: _fake_release(d))
    # Ярлыки не создаём по-настоящему (для этого нужен cscript и живая
    # Windows) — записываем факт вызова: проверяем решение, а не COM.
    def fake_shortcut(link, target, workdir="", icon="", description=""):
        made.append((link, target))
        open(link, "w").close()
        return True
    monkeypatch.setattr(lib, "create_shortcut", fake_shortcut)
    monkeypatch.setattr(lib, "register_uninstall",
                        lambda d, v, u: made.append(("registry", u)) or True)
    return installer, made


def test_install_lays_out_files_and_both_shortcuts(sandbox, tmp_path):
    installer, made = sandbox
    target = str(tmp_path / "install")

    version = installer.do_install(target, desktop=True, start_menu=True,
                                   on_status=lambda *_: None, on_progress=lambda *_: None)

    assert version == "v9.9.9"
    assert os.path.isfile(os.path.join(target, lib.EXE_NAME))
    links = [os.path.basename(l) for l, _ in made if l != "registry"]
    assert links.count(f"{lib.APP_NAME}.lnk") == 2, "ждём ярлык и на столе, и в «Пуске»"


def test_unchecked_shortcuts_are_not_created(sandbox, tmp_path):
    """Галочки должны что-то значить: снял — ярлыка нет."""
    installer, made = sandbox
    target = str(tmp_path / "install")

    installer.do_install(target, desktop=False, start_menu=False,
                         on_status=lambda *_: None, on_progress=lambda *_: None)

    assert [m for m in made if m[0] != "registry"] == []


def test_no_registry_entry_without_a_working_uninstaller(sandbox, tmp_path, monkeypatch):
    """Запуск из исходников: uninstall.exe положить не из чего.

    Строка в «Установка и удаление программ» с кнопкой «Удалить», ведущей в
    никуда, хуже отсутствия строки — нажимаешь, ничего не происходит."""
    installer, made = sandbox
    monkeypatch.setattr(installer.sys, "argv", ["installer.py"])
    target = str(tmp_path / "install")

    installer.do_install(target, desktop=False, start_menu=False,
                         on_status=lambda *_: None, on_progress=lambda *_: None)

    assert not any(m[0] == "registry" for m in made)
    assert not os.path.exists(os.path.join(target, "uninstall.exe"))


# ─────────────────── Выбранная папка = родитель, не цель ──────────────────

def test_choosing_a_folder_creates_its_own_subfolder_inside():
    r"""Выбрал D:\Игры — ставим в D:\Игры\<имя>, а не вываливаем файлы
    приложения прямо туда, вперемешку со всем, что там уже лежит."""
    import installer
    got = installer.resolve_install_target(r"D:\Игры")
    assert got == os.path.join(r"D:\Игры", lib.APP_NAME)


def test_picking_an_existing_install_does_not_nest_the_name_twice():
    """Ткнул в уже существующую установку — второй раз имя не дописываем."""
    import installer
    existing = os.path.join(r"D:\Игры", lib.APP_NAME)
    assert installer.resolve_install_target(existing) == existing


def test_the_name_check_ignores_letter_case():
    import installer
    weird = os.path.join(r"D:\x", lib.APP_NAME.upper())
    assert installer.resolve_install_target(weird) == weird


# ───────────────── Ярлык создаётся ПО-НАСТОЯЩЕМУ, без заглушек ─────────────
# Этот тест существует из-за конкретной ошибки. create_shortcut писала
# временный .vbs в кодировке utf-8-sig, а Windows Script Host на BOM от UTF-8
# падает сразу («недопустимый знак» в позиции 1,1) — ярлыки не создавались
# ВООБЩЕ, ни один. Заметно это не было по двум причинам: cscript зовётся с
# capture_output, так что его ошибка никуда не шла, а тесты выше подменяют
# create_shortcut заглушкой и проверяют лишь РЕШЕНИЕ (звать или не звать).
#
# Поэтому здесь единственный тест, который реально запускает cscript. Цель —
# sys.executable: настоящий подписанный файл. С файлом-пустышкой Windows
# Defender блокирует сохранение ярлыка, и тест падал бы не по делу.

@pytest.mark.skipif(os.name != "nt", reason="ярлыки Windows и cscript есть только в Windows")
def test_a_shortcut_is_really_created_and_points_at_its_target(tmp_path):
    import shutil as _shutil
    import subprocess

    app_dir = tmp_path / lib.APP_NAME
    app_dir.mkdir()
    exe = app_dir / lib.EXE_NAME
    _shutil.copy2(sys.executable, exe)
    # Кириллица в пути намеренно: у большинства пользователей рабочий стол
    # называется по-русски, а ANSI-кодировка на таком пути и ломается.
    desktop = tmp_path / "Рабочий стол"
    desktop.mkdir()
    link = desktop / f"{lib.APP_NAME}.lnk"

    assert lib.create_shortcut(str(link), str(exe), str(app_dir),
                               description=lib.APP_NAME), "cscript не создал ярлык"
    assert link.is_file()

    reader = tmp_path / "read.vbs"
    reader.write_text(
        'Set s = CreateObject("WScript.Shell")\n'
        f'WScript.Echo s.CreateShortcut("{link}").TargetPath\n',
        encoding="utf-16")
    got = subprocess.run(["cscript", "//nologo", str(reader)],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    assert os.path.normcase(got) == os.path.normcase(str(exe)), \
        "ярлык создан, но ведёт не туда"


@pytest.mark.skipif(os.name != "nt", reason="реестр Windows")
def test_the_uninstall_entry_round_trips_through_the_registry(tmp_path):
    """Пишем, читаем обратно, стираем. Без этого «программа установлена» —
    утверждение на веру: запись могла не создаться, и в списке программ её
    просто нет."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / lib.EXE_NAME).write_bytes(b"MZ")
    try:
        assert lib.register_uninstall(str(app_dir), "v1.1.3",
                                      str(app_dir / "uninstall.exe"))
        assert lib.read_install_dir() == str(app_dir)
    finally:
        lib.unregister_uninstall()
    assert lib.read_install_dir() is None
