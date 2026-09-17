"""ТЕСТЫ БЕЗОПАСНОГО ОТКРЫТИЯ ВНЕШНИХ ССЫЛОК ИЗ ИНТЕРФЕЙСА (Api.open_url).

Из интерфейса (Help screen, ссылки на форк, гайд Creams, YouTube) вызывается
метод Api.open_url(url). Тесты проверяют, что открываются только безопасные
http/https протоколы и отсекаются любые попытки запуска опасных URI-схем.
"""
import pytest
from main import Api


def test_open_url_opens_valid_http_and_https_links(monkeypatch):
    """Ловит баг, когда клик по ссылке на репозиторий или YouTube-гайд
    в веб-интерфейсе не передаётся в браузер по умолчанию."""
    opened = []

    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda u: opened.append(u))

    api = Api.__new__(Api)

    # HTTPS ссылка
    res_https = api.open_url("https://github.com/Ponchik0/ae")
    assert res_https == {"ok": True}
    assert opened == ["https://github.com/Ponchik0/ae"]

    # HTTP ссылка
    res_http = api.open_url("http://example.com")
    assert res_http == {"ok": True}
    assert opened == ["https://github.com/Ponchik0/ae", "http://example.com"]


def test_open_url_rejects_unsafe_schemes_and_malformed_inputs(monkeypatch):
    """Ловит уязвимость и баг, если из интерфейса попытаются передать
    произвольные локальные схемы (file://, cmd:, javascript:) или некорректный ввод."""
    opened = []

    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda u: opened.append(u))

    api = Api.__new__(Api)

    # Опасные схемы не должны вызывать webbrowser.open
    assert api.open_url("file:///C:/Windows/notepad.exe") == {"ok": False, "error": "Only HTTP/HTTPS allowed"}
    assert api.open_url("javascript:alert(1)") == {"ok": False, "error": "Only HTTP/HTTPS allowed"}
    assert api.open_url("cmd:echo 1") == {"ok": False, "error": "Only HTTP/HTTPS allowed"}
    assert api.open_url("") == {"ok": False, "error": "Invalid URL"}
    assert api.open_url(None) == {"ok": False, "error": "Invalid URL"}
    assert api.open_url(12345) == {"ok": False, "error": "Invalid URL"}

    assert opened == []
