"""Serves the map catalog (Assets/map/<Category>/<Map name>.png) to the
Place Unit picker in Creation -- lets a player click a spot on a reference
map image (or a live Roblox snapshot, see main.get_roblox_snapshot) to read
off an X/Y position instead of guessing coordinates blind.

Здесь же живёт СНИМОК ПО УМОЛЧАНИЮ (см. MODE_CATEGORIES ниже): кадр из игры,
снятый один раз, который подставляется в выбор точки сам. Слот на каждую карту
(у Raid и Event -- на акт) плюс общий слот на режим, который служит запасным.
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
# КЛЮЧ -- РЕЖИМ ПЛЮС НЕОБЯЗАТЕЛЬНАЯ КАРТА/АКТ.
#
# Сначала ключом был ОДИН ТОЛЬКО режим, и рассуждение было такое: точка
# установки задаётся в экранных координатах и зависит от того, куда смотрит
# камера, а камеру макрос выставляет одинаково для всего режима (см.
# runner._run_prestart). Про камеру это верно, а вывод -- нет: камера-то одна,
# но ПОЛЕ под ней у каждой карты своё. Снимок Rose Kingdom для School Grounds
# бесполезен ровно так же, как чужой кадр, и на каждую вторую карту приходилось
# переснимать поверх единственного слота, теряя предыдущий.
#
# Теперь слот на каждую карту (или акт -- у Raid и Event это они), плюс общий
# слот на режим. Общий остаётся ключом БЕЗ варианта, поэтому все ранее
# сохранённые снимки продолжают работать как были, и он же -- запасной: нет
# кадра для этой карты, подставится общий для режима.
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


def snapshot_variant(variant: str) -> str:
    """Безопасное имя карты/акта для файла, или "" -- «общий снимок режима».

    Имя приходит из интерфейса и попадает в путь на диске, поэтому пропускаем
    только буквы, цифры, пробел, дефис и апостроф (последний нужен: карта так
    и называется -- King's Tomb). Всё прочее выбрасываем целиком, а не
    заменяем: «..» и разделители пути обязаны исчезнуть, а не превратиться в
    подчёркивания, из которых потом соберётся другое имя. Тот же принцип, что
    у белого списка режимов в category_for_mode."""
    cleaned = "".join(
        ch for ch in str(variant or "").strip()
        if ch.isalnum() or ch in " -'"
    ).strip()
    return cleaned[:60]


def mode_snapshot_path(mode: str, variant: str = "") -> str:
    """Путь к снимку для режима (и карты/акта), или "" если режим не тот.
    Существование файла НЕ проверяется -- это путь, куда писать и откуда
    читать; проверка отдельно, в has_mode_snapshot."""
    category = category_for_mode(mode)
    if not category:
        return ""
    safe = snapshot_variant(variant)
    # Без варианта -- ровно прежнее имя файла: снимки, сохранённые до
    # появления карт, обязаны продолжать работать.
    name = f"{MODE_SNAPSHOT_NAME} - {safe}" if safe else MODE_SNAPSHOT_NAME
    return os.path.join(MAPS_DIR, category, f"{name}.png")


def has_mode_snapshot(mode: str, variant: str = "") -> bool:
    """Есть ли снимок ИМЕННО для этой карты (или общий, если variant пуст).
    Без запасного варианта -- на этот вопрос отвечает resolve_mode_snapshot."""
    path = mode_snapshot_path(mode, variant)
    return bool(path) and os.path.isfile(path)


def resolve_mode_snapshot(mode: str, variant: str = "") -> str:
    """Какой файл реально подставится: снимок этой карты, иначе общий для
    режима, иначе "".

    Запасной вариант -- главное здесь. Карт много, и требовать снимок под
    каждую значило бы вернуть ровно ту возню, ради устранения которой снимок
    по умолчанию и заводился: на новой карте подставится общий кадр режима, и
    только если он не подходит, имеет смысл снять свой."""
    if variant and has_mode_snapshot(mode, variant):
        return mode_snapshot_path(mode, variant)
    if has_mode_snapshot(mode):
        return mode_snapshot_path(mode)
    return ""


def save_mode_snapshot(mode: str, png_bytes: bytes, variant: str = "") -> str:
    """Кладёт кадр PNG как снимок по умолчанию. Возвращает путь.

    Перезаписывает молча и намеренно: снимок -- ровно один на слот, и
    повторное нажатие означает «этот кадр теперь актуальный» (пересобрал
    состав, сменил ракурс). Копии тут были бы мусором."""
    path = mode_snapshot_path(mode, variant)
    if not path:
        raise ValueError(f"unknown mode: {mode!r}")
    if not png_bytes:
        raise ValueError("empty snapshot")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png_bytes)
    return path


def mode_snapshot_data_uri(mode: str, variant: str = "") -> str:
    """Снимок как data-URI, или "" если его нет. Тем же способом, что и
    остальные карты: интерфейс читает картинки только так -- ни http-сервера,
    ни доступа к file:// у него нет."""
    path = resolve_mode_snapshot(mode, variant)
    if not path:
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def delete_mode_snapshot(mode: str, variant: str = "") -> bool:
    """Удаляет снимок ИМЕННО этого слота. Возвращает, было ли что удалять.

    Именно этого, а не «того, что подставился»: иначе кнопка «убрать» на
    карте без своего снимка стирала бы общий кадр режима, то есть чужой."""
    if not has_mode_snapshot(mode, variant):
        return False
    os.remove(mode_snapshot_path(mode, variant))
    return True
