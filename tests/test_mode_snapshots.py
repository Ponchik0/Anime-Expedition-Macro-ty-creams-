"""Снимок по умолчанию для режима: снял кадр один раз — подставляется сам.

Зачем это вообще. Готовых карт в поставке нет и не будет: клик по чужому кадру
промахивается, ракурс камеры у каждого свой (Assets/map/README.txt). Значит
единственный точный путь задать точку — «Снимок из игры», и раньше его
приходилось повторять на КАЖДУЮ точку: свернуть интерфейс, показать игру,
дождаться кадра, снять. На сборке из шести юнитов — шесть одинаковых снимков
одного и того же экрана.

Ключ — режим плюс необязательная карта (у Raid и Event — акт). Сначала ключом
был один только режим: точка задаётся в экранных координатах и зависит от
ракурса камеры, а камеру макрос выставляет одинаково для всего режима (см.
runner._run_prestart). Про камеру это верно, а вывод — нет: камера-то одна, но
ПОЛЕ под ней у каждой карты своё, и на каждую вторую карту приходилось
переснимать поверх единственного слота, теряя предыдущий.

Общий слот на режим остался ключом БЕЗ карты — поэтому все ранее сохранённые
снимки продолжают работать, и он же запасной: нет кадра для этой карты —
подставится общий.
"""
import os

import pytest

from core import maps

PNG = b"\x89PNG\r\n\x1a\n" + b"payload"


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    """Каталог карт в отдельной папке -- иначе тесты писали бы в Assets
    пользователя."""
    monkeypatch.setattr(maps, "MAPS_DIR", str(tmp_path / "map"))
    return tmp_path / "map"


# ── Белый список режимов ──────────────────────────────────────────────────

@pytest.mark.parametrize("mode,folder", [
    ("story", "Story"),
    ("raid", "Raid"),
    ("expedition", "Expedition"),
    ("event", "Event"),
])
def test_every_task_mode_has_a_folder(mode, folder):
    assert maps.category_for_mode(mode) == folder


def test_mode_matching_is_case_and_space_tolerant():
    assert maps.category_for_mode(" Raid ") == "Raid"
    assert maps.category_for_mode("RAID") == "Raid"


@pytest.mark.parametrize("mode", [
    "", None, "challenge", "bounty",
    # Главное: имя режима приходит из интерфейса и попадает в путь на диске.
    "../../Windows", "..\\..\\etc", "a/b",
])
def test_anything_outside_the_whitelist_is_refused(mode):
    assert maps.category_for_mode(mode) == ""
    assert maps.mode_snapshot_path(mode) == ""
    assert maps.has_mode_snapshot(mode) is False
    assert maps.mode_snapshot_data_uri(mode) == ""
    assert maps.delete_mode_snapshot(mode) is False


def test_a_path_traversal_mode_cannot_write_anywhere(catalog):
    with pytest.raises(ValueError):
        maps.save_mode_snapshot("../../evil", PNG)


# ── Сохранение и чтение ───────────────────────────────────────────────────

def test_saving_creates_the_folder_and_the_file(catalog):
    path = maps.save_mode_snapshot("raid", PNG)

    assert os.path.isfile(path)
    assert path == str(catalog / "Raid" / "Snapshot.png")
    assert open(path, "rb").read() == PNG


def test_nothing_exists_before_the_first_save(catalog):
    assert maps.has_mode_snapshot("raid") is False
    assert maps.mode_snapshot_data_uri("raid") == ""


def test_the_snapshot_comes_back_as_a_data_uri(catalog):
    """Интерфейс читает картинки только так -- ни http-сервера, ни доступа к
    file:// у него нет (см. core/maps.map_image_data_uri)."""
    maps.save_mode_snapshot("expedition", PNG)

    uri = maps.mode_snapshot_data_uri("expedition")

    assert uri.startswith("data:image/png;base64,")
    import base64
    assert base64.b64decode(uri.split(",", 1)[1]) == PNG


def test_saving_again_replaces_the_old_frame(catalog):
    """«Снимок по умолчанию» -- ровно один на режим: повторное нажатие значит
    «этот кадр теперь актуальный», а не «положи ещё один»."""
    maps.save_mode_snapshot("story", PNG)
    maps.save_mode_snapshot("story", b"newer frame")

    assert open(maps.mode_snapshot_path("story"), "rb").read() == b"newer frame"
    assert os.listdir(catalog / "Story") == ["Snapshot.png"]


def test_an_empty_frame_is_refused(catalog):
    """Пустые байты означают, что снимка не было -- записать «ничего» под
    видом снимка хуже, чем честно отказаться."""
    with pytest.raises(ValueError):
        maps.save_mode_snapshot("story", b"")
    assert maps.has_mode_snapshot("story") is False


def test_modes_do_not_share_a_snapshot(catalog):
    maps.save_mode_snapshot("raid", b"raid frame")
    maps.save_mode_snapshot("expedition", b"expedition frame")

    assert open(maps.mode_snapshot_path("raid"), "rb").read() == b"raid frame"
    assert open(maps.mode_snapshot_path("expedition"), "rb").read() == b"expedition frame"


# ── Слот на карту/акт ─────────────────────────────────────────────────────
# Сначала слот был ОДИН на режим, и рассуждение было такое: точка задаётся в
# экранных координатах и зависит от ракурса камеры, а камеру макрос выставляет
# одинаково для всего режима. Про камеру верно, а вывод — нет: камера-то одна,
# но ПОЛЕ под ней у каждой карты своё, и на каждую вторую карту приходилось
# переснимать поверх единственного слота, теряя предыдущий.

def test_each_map_keeps_its_own_snapshot(catalog):
    maps.save_mode_snapshot("story", b"rose", "Rose Kingdom")
    maps.save_mode_snapshot("story", b"school", "School Grounds")

    assert open(maps.mode_snapshot_path("story", "Rose Kingdom"), "rb").read() == b"rose"
    assert open(maps.mode_snapshot_path("story", "School Grounds"), "rb").read() == b"school"


def test_a_map_without_its_own_snapshot_falls_back_to_the_mode(catalog):
    """Запасной вариант — главное здесь. Требовать снимок под КАЖДУЮ карту
    значило бы вернуть ровно ту возню, ради устранения которой снимок по
    умолчанию и заводился."""
    maps.save_mode_snapshot("story", b"general")

    assert maps.resolve_mode_snapshot("story", "Rose Kingdom") == maps.mode_snapshot_path("story")
    assert maps.has_mode_snapshot("story", "Rose Kingdom") is False   # своего нет
    assert maps.mode_snapshot_data_uri("story", "Rose Kingdom")       # но общий подставится

    maps.save_mode_snapshot("story", b"own", "Rose Kingdom")
    assert maps.resolve_mode_snapshot("story", "Rose Kingdom") == \
        maps.mode_snapshot_path("story", "Rose Kingdom")


def test_the_mode_wide_slot_keeps_its_old_filename(catalog):
    """Снимки, сохранённые до появления карт, обязаны продолжать работать:
    общий слот — это по-прежнему ключ БЕЗ варианта и то же имя файла."""
    assert os.path.basename(maps.mode_snapshot_path("raid")) == f"{maps.MODE_SNAPSHOT_NAME}.png"


@pytest.mark.parametrize("nasty", [
    "../../evil", "..\\..\\evil", "a/b", "a\\b", "con:", "....",
])
def test_a_map_name_can_never_escape_the_folder(catalog, nasty):
    """Имя карты приходит из интерфейса и попадает в путь на диске. Опасное
    выбрасывается ЦЕЛИКОМ, а не заменяется подчёркиваниями: из подчёркиваний
    собралось бы другое существующее имя."""
    path = maps.mode_snapshot_path("story", nasty)
    assert os.path.dirname(os.path.abspath(path)) == os.path.abspath(str(catalog / "Story"))
    assert ".." not in os.path.basename(path)


def test_a_real_map_name_with_an_apostrophe_survives(catalog):
    """King's Tomb — настоящее имя карты. Вычистить апостроф значило бы свалить
    две разные карты в один слот."""
    assert maps.snapshot_variant("King's Tomb") == "King's Tomb"
    maps.save_mode_snapshot("story", b"tomb", "King's Tomb")
    assert maps.has_mode_snapshot("story", "King's Tomb")
    assert not maps.has_mode_snapshot("story", "Kings Tomb")


# ── Удаление ──────────────────────────────────────────────────────────────

def test_deleting_reports_whether_there_was_anything(catalog):
    assert maps.delete_mode_snapshot("raid") is False   # нечего удалять

    maps.save_mode_snapshot("raid", PNG)
    assert maps.delete_mode_snapshot("raid") is True
    assert maps.has_mode_snapshot("raid") is False


def test_deleting_a_map_snapshot_leaves_the_mode_one_alone(catalog):
    """Кнопка «убрать» на карте не должна стирать общий кадр режима — он
    чужой, и на нём держатся все остальные карты."""
    maps.save_mode_snapshot("story", b"general")
    maps.save_mode_snapshot("story", b"own", "Rose Kingdom")

    assert maps.delete_mode_snapshot("story", "Rose Kingdom") is True
    assert maps.has_mode_snapshot("story") is True
    assert maps.resolve_mode_snapshot("story", "Rose Kingdom") == maps.mode_snapshot_path("story")

    # На карте без своего снимка удалять уже нечего — и общий не трогаем.
    assert maps.delete_mode_snapshot("story", "Rose Kingdom") is False
    assert maps.has_mode_snapshot("story") is True


# ── Связь с обычным каталогом карт ────────────────────────────────────────

def test_the_snapshot_shows_up_as_an_ordinary_map(catalog):
    """Снимок кладётся в тот же каталог, что и карты, поэтому его видно
    вкладкой и карточкой: можно выбрать руками или удалить, стерев файл."""
    maps.save_mode_snapshot("raid", PNG)

    assert "Raid" in maps.list_categories()
    assert maps.list_maps("Raid") == [maps.MODE_SNAPSHOT_NAME]
    assert maps.map_image_data_uri("Raid", maps.MODE_SNAPSHOT_NAME).startswith("data:image/png;base64,")
