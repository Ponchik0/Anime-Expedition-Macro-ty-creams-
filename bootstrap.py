"""
Tiny bootstrapper for Anime Expeditions Macro.

Downloads the real app from GitHub Releases on first run (or when a newer
version is out) and launches it. Built as its own separate, much smaller
exe (see build_bootstrap.py) -- the full app is 40+ MB because of
OpenCV/numpy/pywebview, which this script never imports, so the
bootstrapper itself ends up small enough to share directly (e.g. on
Discord) instead of the full download.

Downloads the release ZIP (exe + the loose, user-editable Assets/ folder
side by side -- see release.yml's packaging step), not just the exe:
Assets stopped being bundled inside the exe (so users can open/replace/add
the macro's reference images without a rebuild -- see core/constants.py's
ASSETS_DIR), which means a bare exe alone can't find any of its reference
images. The exe is always replaced on update; Assets files are extracted
ADD-ONLY (never overwriting one already on disk) so an update can't wipe
out images the user has replaced or added -- same policy core/updater.py's
merge_assets_update applies for in-app updates.

    py -3.12 bootstrap.py
"""
import os
import sys
import ctypes
import subprocess

import installer_lib as lib

APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

# ВСЁ ОБЩЕЕ ЖИВЁТ В installer_lib. Здесь раньше лежали свои копии: адрес
# репозитория, имя архива, разбор редиректа, поиск вложения, распаковка и
# проверка _is_inside. Последняя — защита от того, что запись из архива
# уедет за пределы папки (zip-slip), и держать её в двух файлах было
# опаснее всего: копии расходятся, и отставшая становится дырой.
# Теперь и установщик, и бутстраппер зовут одну реализацию.
VERSION_FILE = os.path.join(APP_DIR, ".bootstrap_version")


def find_local_exe() -> str:
    """Путь до установленного приложения рядом с бутстраппером."""
    return lib.app_exe_path(APP_DIR)


MB_OK = 0x40
MB_ERROR = 0x10


def _msg(text: str, icon: int = MB_OK):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, "Anime Expeditions Macro", icon)
    except Exception:
        pass


def _download_and_extract() -> bool:
    """Скачивает архив релиза и раскладывает его рядом с бутстраппером.

    Правила распаковки (exe перезаписывается, файлы в Assets добавляются, но
    не перетираются, всё, что уезжает за пределы папки, отбрасывается) живут
    в installer_lib.extract_release — одни и те же для установщика и для
    бутстраппера."""
    try:
        lib.install_release(APP_DIR)
        return os.path.isfile(find_local_exe())
    except Exception:
        return False


def _local_version() -> str:
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _save_local_version(tag: str):
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(tag)
    except OSError:
        pass


def ensure_app() -> bool:
    """Make sure the real exe (and its Assets folder) is present and up to
    date. Returns True if it's ready to launch, False if there's nothing
    usable at all."""
    latest = lib.latest_tag()
    have_exe = os.path.isfile(find_local_exe())
    # The Assets check matters for installs made by an OLD bootstrapper
    # (which only ever downloaded the bare exe): same tag, but no Assets
    # folder on disk -- re-extracting the zip fills it in without touching
    # the exe's version bookkeeping.
    have_assets = os.path.isdir(os.path.join(APP_DIR, "Assets", "ui"))

    if have_exe and have_assets and (not latest or latest == _local_version()):
        return True  # already up to date (or offline -- just use what we have)

    ok = _download_and_extract()
    if ok and latest:
        _save_local_version(latest)
    return ok or have_exe


def main():
    if not ensure_app():
        _msg(
            "Couldn't download Anime Expeditions Macro. Check your internet connection "
            "and try again.",
            MB_ERROR,
        )
        sys.exit(1)

    subprocess.Popen([find_local_exe()], cwd=APP_DIR)


if __name__ == "__main__":
    main()
