"""Проверка версии: чем именно она кончилась.

ГЛАВНОЕ, ЧТО ЗДЕСЬ ПРОВЕРЯЕТСЯ, — что «не смогли проверить» больше не выглядит
как «у тебя последняя версия». Раньше исход был один на всё: {"available":
False}. Под него попадали и свежая версия, и отсутствие сети, и недоступный
репозиторий, и репозиторий без единого релиза, — а интерфейс на всё это отвечал
«You're up to date». Кнопка при этом выглядела рабочей и врала.

Живой случай: GITHUB_REPO указывает на приватный репозиторий. GitHub отвечает
анонимному гостю 404 (а не 403 — чтобы не выдать сам факт его существования),
и проверка молча рапортовала «обновлений нет» вообще всегда.
"""
import pytest
import requests

from core import updater


class _Resp:
    """Ответ requests ровно в том объёме, в каком его читает апдейтер."""

    def __init__(self, status_code=200, location=""):
        self.status_code = status_code
        self.headers = {"Location": location} if location else {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def at_version(monkeypatch):
    def _set(version):
        monkeypatch.setattr(updater, "get_current_version", lambda: version)
    return _set


def _head(monkeypatch, releases=None, repo=None, boom=False):
    """Подменяет requests.head: отдельные ответы на страницу релизов и на сам
    репозиторий — по ним апдейтер и различает два очень разных 404."""
    def head(url, **kw):
        if boom:
            raise requests.RequestException("сеть отвалилась")
        if url.endswith("/releases/latest"):
            return releases if releases is not None else _Resp(404)
        return repo if repo is not None else _Resp(404)

    monkeypatch.setattr(updater.requests, "head", head)


def _no_api(monkeypatch):
    """Метаданные релиза через api.github.com не трогаем: проверяется решение,
    а не разбор чужого JSON."""
    def get(*a, **kw):
        raise requests.RequestException("сюда ходить не надо")
    monkeypatch.setattr(updater.requests, "get", get)


# ── Обновление есть ───────────────────────────────────────────────────────

def test_a_newer_release_is_reported_with_both_versions(monkeypatch, at_version):
    """Ровно то, о чём просили: стою на 1.1.0, вышла 1.2.0 — видно обе."""
    at_version("1.1.0")
    _head(monkeypatch, releases=_Resp(302, "https://github.com/o/r/releases/tag/1.2.0"))
    _no_api(monkeypatch)

    res = updater.check_for_update()

    assert res["available"] is True
    assert res["status"] == updater.CHECK_AVAILABLE
    assert res["version"] == "1.2.0"
    assert res["current_version"] == "1.1.0"


def test_a_v_prefixed_tag_is_understood_too(monkeypatch, at_version):
    """Релизы форка бывают и с «v», и без — на решение это влиять не должно."""
    at_version("1.1.0")
    _head(monkeypatch, releases=_Resp(302, "https://github.com/o/r/releases/tag/v1.2.0"))
    _no_api(monkeypatch)

    assert updater.check_for_update()["available"] is True


@pytest.mark.parametrize("tag", ["1.1.0", "1.0.9", "0.18.0"])
def test_an_older_or_equal_release_is_not_an_update(monkeypatch, at_version, tag):
    """0.18.0 — версия апстрима. Она НИЖЕ нашей 1.1.0, и предлагать «обновиться»
    до неё значило бы откатить форк на чужую сборку."""
    at_version("1.1.0")
    _head(monkeypatch, releases=_Resp(302, f"https://github.com/o/r/releases/tag/{tag}"))

    res = updater.check_for_update()

    assert res["available"] is False
    assert res["status"] == updater.CHECK_UP_TO_DATE
    # Найденный номер кладётся рядом: «у тебя 1.1.0, последняя тоже» — это
    # ответ, а «обновлений нет» — отписка.
    assert res["version"] == tag
    assert res["current_version"] == "1.1.0"


# ── Проверить не вышло, и каждый раз по-своему ────────────────────────────

def test_a_private_repository_is_named_as_such(monkeypatch, at_version):
    """Живой случай. GitHub отвечает 404 и на релизы, и на сам репозиторий."""
    at_version("1.1.0")
    _head(monkeypatch, releases=_Resp(404), repo=_Resp(404))

    res = updater.check_for_update()

    assert res["status"] == updater.CHECK_REPO_UNREACHABLE
    assert res["available"] is False
    assert "приватный" in res["reason"]


def test_a_public_repo_without_releases_is_a_different_answer(monkeypatch, at_version):
    """Репозиторий виден, релизов в нём нет — это не «недоступен», и лечится
    это совсем другим: надо выпустить релиз."""
    at_version("1.1.0")
    _head(monkeypatch, releases=_Resp(404), repo=_Resp(200))

    res = updater.check_for_update()

    assert res["status"] == updater.CHECK_NO_RELEASES
    assert "релиз" in res["reason"]


def test_no_network_is_not_reported_as_being_up_to_date(monkeypatch, at_version):
    """Та самая подмена, из-за которой кнопка выглядела рабочей: запрос не
    ушёл никуда, а ответ был «обновлений нет»."""
    at_version("1.1.0")
    _head(monkeypatch, boom=True)

    res = updater.check_for_update()

    assert res["status"] == updater.CHECK_OFFLINE
    assert res["status"] != updater.CHECK_UP_TO_DATE


def test_disabled_updates_say_so_instead_of_pretending_to_check(monkeypatch, at_version):
    at_version("1.1.0")
    monkeypatch.setattr(updater, "UPDATES_DISABLED", True)

    assert updater.check_for_update()["status"] == updater.CHECK_DISABLED


# ── Общий контракт ────────────────────────────────────────────────────────

@pytest.mark.parametrize("releases,repo,boom", [
    (_Resp(302, "https://github.com/o/r/releases/tag/9.9.9"), None, False),
    (_Resp(302, "https://github.com/o/r/releases/tag/0.0.1"), None, False),
    (_Resp(404), _Resp(404), False),
    (_Resp(404), _Resp(200), False),
    (None, None, True),
])
def test_every_outcome_carries_a_status_and_the_current_version(
        monkeypatch, at_version, releases, repo, boom):
    """Интерфейс разбирает исход по `status`. Ответ без него он прочитал бы как
    «не смогли проверить» — то есть один починенный случай снова стал бы
    неотличим от сломанного."""
    at_version("1.1.0")
    _head(monkeypatch, releases=releases, repo=repo, boom=boom)
    _no_api(monkeypatch)

    res = updater.check_for_update()

    assert res.get("status"), res
    assert res["current_version"] == "1.1.0"


# ── Приватные исходники, публичные релизы ────────────────────────────────
# Исходники могут быть закрыты, и тогда до них не достучится ни один запрос
# отсюда: GitHub требует авторизацию, а токен в приложении достаётся из него за
# минуту, то есть раздаёт доступ всем, у кого есть сборка. Поэтому всё сетевое
# ходит в ОТДЕЛЬНЫЙ публичный репозиторий релизов. Стоит одной ссылке уехать
# обратно на приватный — и обновление молча начнёт получать 404 у всех.

def test_nothing_network_facing_points_at_the_source_repo(monkeypatch, at_version):
    """Каждая ссылка, по которой клиент реально ходит, — из RELEASES_REPO."""
    at_version("1.1.0")
    monkeypatch.setattr(updater, "RELEASES_REPO", "owner/public-releases")
    monkeypatch.setattr(updater, "GITHUB_REPO", "owner/private-source")
    monkeypatch.setattr(updater, "RELEASES_PAGE_URL",
                        "https://github.com/owner/public-releases/releases/latest")
    _head(monkeypatch, releases=_Resp(302, "https://github.com/o/r/releases/tag/1.2.0"))
    _no_api(monkeypatch)

    res = updater.check_for_update()

    for key in ("url", "zip_url", "release_zip_url"):
        assert "public-releases" in res[key], (key, res[key])
        assert "private-source" not in res[key], (key, res[key])


def test_the_module_level_urls_are_built_from_the_releases_repo():
    """Ссылки собираются один раз при импорте — проверяем именно их, а не то,
    что удалось подменить в тесте."""
    assert updater.RELEASES_REPO in updater.RELEASES_PAGE_URL
    assert updater.RELEASES_REPO in updater.RELEASES_LATEST_URL


def test_updating_from_source_refuses_instead_of_quietly_doing_nothing(
        tmp_path, monkeypatch):
    """Если релизы когда-нибудь переедут в отдельный репозиторий, скачивать
    «исходники» станет неоткуда: там будет архив сборки, а не код. Молча
    разложить его README поверх установки и перезапуститься на той же версии —
    худший из возможных исходов: выглядит как успех, а версия не меняется."""
    monkeypatch.setattr(updater, "RELEASES_REPO", "owner/public-releases")

    with pytest.raises(RuntimeError) as exc:
        updater.stage_source_update("https://example.invalid/x.zip",
                                    str(tmp_path), log=lambda *_: None)

    assert "git pull" in str(exc.value)
    assert "owner/public-releases" in str(exc.value)


def test_updating_from_source_is_allowed_while_the_repo_is_one_and_public():
    """Обратная сторона: пока код и релизы в одном репозитории, отказывать не
    за что — обновление из исходников работает, и защита выше молчит."""
    assert updater.RELEASES_REPO == updater.GITHUB_REPO
    updater._refuse_source_update_from_releases_repo()  # не должно бросить


def test_the_repo_is_only_asked_about_when_something_went_wrong(monkeypatch, at_version):
    """Второй запрос -- цена разбора ошибки, и платить её на каждой удачной
    проверке незачем."""
    at_version("1.1.0")
    urls = []

    def head(url, **kw):
        urls.append(url)
        return _Resp(302, "https://github.com/o/r/releases/tag/1.2.0")

    monkeypatch.setattr(updater.requests, "head", head)
    _no_api(monkeypatch)

    updater.check_for_update()

    assert len(urls) == 1 and urls[0].endswith("/releases/latest")
