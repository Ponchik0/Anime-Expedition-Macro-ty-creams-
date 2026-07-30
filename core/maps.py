"""Serves the map catalog (Assets/map/<Category>/<Map name>.png) to the
Place Unit picker in Creation -- lets a player click a spot on a reference
map image (or a live Roblox snapshot, see main.get_roblox_snapshot) to read
off an X/Y position instead of guessing coordinates blind.

Здесь же живёт СНИМОК ПО УМОЛЧАНИЮ ДЛЯ РЕЖИМА (см. MODE_CATEGORIES ниже):
кадр из игры, снятый один раз, который подставляется в выбор точки сам,
пока ты работаешь со сценарием этого режима.
"""
import base64
import os

from . import constants

MAPS_DIR = os.path.join(constants.ASSETS_DIR, "map")

_IMAGE_EXTS = (".png", ".jpg", ".jpeg")

# ── Снимок по умолчанию для режима ────────────────────────────────────────
# Зачем. Готовых карт в поставке нет и не будет: клик по чужому кадру
# промахивается -- ракурс камеры и положение карты у каждого свои (см.
# Assets/map/README.txt). Значит единственный точный путь -- «Снимок из игры»,
# и раньше его приходилось делать ЗАНОВО на каждую точку: свернуть интерфейс,
# показать игру, дождаться кадра, снять. На сборке из шести юнитов это шесть
# одинаковых снимков одного и того же экрана.
#
# Теперь снимок сохраняется под режим и дальше подставляется сам.
#
# ПОЧЕМУ КЛЮЧ -- РЕЖИМ, А НЕ КАРТА. Точка установки задаётся в экранных
# координатах и зависит от того, куда смотрит камера, а камеру макрос
# выставляет одинаково для всего режима (см. runner._run_prestart: у
# Expedition своя последовательность, у остальных общая). То есть один кадр на
# режим -- ровно та единица, которая переиспользуется.
#
# Папка-категория совпадает с той, что уже используется каталогом
# (Assets/map_bundled/{Story,Raid,Expedition,Event}), поэтому сохранённый
# снимок виден и как обычная карта: его можно выбрать руками или удалить,
# просто стерев файл.
MODE_CATEGORIES = {
    "story": "Story",
    "raid": "Raid",
    "expedition": "Expedition",
    "event": "Event",
}

# Имя файла снимка внутри папки режима. Оно же -- подпись в сетке карт,
# поэтому по-английски и без символов, которые пришлось бы вычищать из пути.
MODE_SNAPSHOT_NAME = "Snapshot"


def list_categories() -> list:
    if not os.path.isdir(MAPS_DIR):
        return []
    return sorted(d for d in os.listdir(MAPS_DIR) if os.path.isdir(os.path.join(MAPS_DIR, d)))


def list_maps(category: str) -> list:
    folder = os.path.join(MAPS_DIR, category)
    if not os.path.isdir(folder):
        return []
    return sorted(
        os.path.splitext(f)[0] for f in os.listdir(folder)
        if f.lower().endswith(_IMAGE_EXTS)
    )


def map_image_data_uri(category: str, name: str) -> str:
    folder = os.path.join(MAPS_DIR, category)
    for ext in _IMAGE_EXTS:
        path = os.path.join(folder, f"{name}{ext}")
        if os.path.isfile(path):
            mime = "image/png" if ext == ".png" else "image/jpeg"
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            return f"data:{mime};base64,{b64}"
    return ""


def category_for_mode(mode: str) -> str:
    """Папка каталога для режима, или "" если режим не тот.

    БЕЛЫЙ СПИСОК, а не «сделай папку с таким именем»: имя режима приходит из
    интерфейса и попадает в путь на диске, поэтому произвольную строку сюда
    пускать нельзя (тот же принцип, что у main._image_manager_root)."""
    return MODE_CATEGORIES.get(str(mode or "").strip().lower(), "")


def mode_snapshot_path(mode: str) -> str:
    """Путь к снимку по умолчанию для режима, или "" если режим не тот.
    Существование файла НЕ проверяется -- это путь, куда писать и откуда
    читать; проверка отдельно, в has_mode_snapshot."""
    category = category_for_mode(mode)
    if not category:
        return ""
    return os.path.join(MAPS_DIR, category, f"{MODE_SNAPSHOT_NAME}.png")


def has_mode_snapshot(mode: str) -> bool:
    path = mode_snapshot_path(mode)
    return bool(path) and os.path.isfile(path)


def save_mode_snapshot(mode: str, png_bytes: bytes) -> str:
    """Кладёт кадр PNG как снимок по умолчанию для режима. Возвращает путь.

    Перезаписывает молча и намеренно: «снимок по умолчанию» -- ровно один на
    режим, и повторное нажатие означает «этот кадр теперь актуальный»
    (пересобрал состав, сменил ракурс). Копии тут были бы мусором."""
    path = mode_snapshot_path(mode)
    if not path:
        raise ValueError(f"unknown mode: {mode!r}")
    if not png_bytes:
        raise ValueError("empty snapshot")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png_bytes)
    return path


def mode_snapshot_data_uri(mode: str) -> str:
    """Снимок по умолчанию как data-URI, или "" если его нет. Тем же способом,
    что и остальные карты: интерфейс читает картинки только так -- ни
    http-сервера, ни доступа к file:// у него нет."""
    if not has_mode_snapshot(mode):
        return ""
    with open(mode_snapshot_path(mode), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def delete_mode_snapshot(mode: str) -> bool:
    """Удаляет снимок по умолчанию. Возвращает, было ли что удалять."""
    if not has_mode_snapshot(mode):
        return False
    os.remove(mode_snapshot_path(mode))
    return True
