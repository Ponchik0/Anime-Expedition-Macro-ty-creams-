"""Тесты колокольчика диагностики (get_diagnostics, install_windows_ocr).

Колокольчик появляется, когда get_diagnostics возвращает непустой список.
Единственная текущая проверка - доступность Windows OCR. install_windows_ocr
запускает PowerShell с UAC-повышением; в тестах это патчится.

Почему тесты важны: если get_diagnostics вдруг стала бросать исключение
или возвращать неправильный формат, JS не сможет обработать ответ и
колокольчик тихо исчезнет - баг останется невидимым для пользователя.
"""

import sys
import threading
import types


def _make_api(monkeypatch):
    import main
    api = object.__new__(main.Api)
    api._pushed_uis = []
    api._pushed_logs = []

    def _push_ui(name):
        api._pushed_uis.append(name)

    def _push_log(msg):
        api._pushed_logs.append(msg)

    api.push_ui = _push_ui
    api.push_log = _push_log
    return api


def test_get_diagnostics_returns_ocr_issue_when_ocr_unavailable(monkeypatch):
    """get_diagnostics включает windows_ocr_missing когда Windows OCR недоступен.

    Ловит регрессию: если метод сломается или перестанет возвращать issues,
    колокольчик не появится и пользователь не узнает о проблеме.
    """
    fake_ocr_windows = types.ModuleType("core.ocr_windows")
    fake_ocr_windows.is_available = lambda: False
    fake_ocr_windows.unavailable_reason = lambda: "no installed language packs"
    monkeypatch.setitem(sys.modules, "core.ocr_windows", fake_ocr_windows)

    api = _make_api(monkeypatch)
    result = api.get_diagnostics()

    assert result["ok"] is True
    assert isinstance(result["issues"], list)
    ids = [i["id"] for i in result["issues"]]
    assert "windows_ocr_missing" in ids

    issue = next(i for i in result["issues"] if i["id"] == "windows_ocr_missing")
    assert issue["action"] == "install_windows_ocr"
    assert issue["action_label"] == "Install"
    assert "title" in issue
    assert "detail" in issue


def test_get_diagnostics_empty_when_ocr_available(monkeypatch):
    """get_diagnostics возвращает пустой список когда Windows OCR работает.

    Ловит ложные срабатывания: колокольчик не должен появляться у пользователей
    с установленным языковым пакетом.
    """
    fake_ocr_windows = types.ModuleType("core.ocr_windows")
    fake_ocr_windows.is_available = lambda: True
    fake_ocr_windows.unavailable_reason = lambda: ""
    monkeypatch.setitem(sys.modules, "core.ocr_windows", fake_ocr_windows)

    # Убедимся, что симуляция выключена
    from core import settings as cfg
    monkeypatch.setattr(cfg, "load", lambda: {"simulate_missing_ocr": False})

    api = _make_api(monkeypatch)
    result = api.get_diagnostics()

    assert result["ok"] is True
    assert result["issues"] == []


def test_get_diagnostics_simulate_missing_ocr(monkeypatch):
    """get_diagnostics показывает проблему если включена симуляция, даже при рабочем OCR.

    Ловит регрессию режима предварительного просмотра для разработчика/пользователя.
    """
    fake_ocr_windows = types.ModuleType("core.ocr_windows")
    fake_ocr_windows.is_available = lambda: True
    monkeypatch.setitem(sys.modules, "core.ocr_windows", fake_ocr_windows)

    from core import settings as cfg
    monkeypatch.setattr(cfg, "load", lambda: {"simulate_missing_ocr": True})

    api = _make_api(monkeypatch)
    result = api.get_diagnostics()

    assert result["ok"] is True
    ids = [i["id"] for i in result["issues"]]
    assert "windows_ocr_missing" in ids


def test_install_windows_ocr_success(monkeypatch):
    """install_windows_ocr запускает поток, ждет процесс и сигналит windowsOcrInstallDone."""
    if sys.platform == "darwin":
        import pytest
        pytest.skip("install_windows_ocr не поддерживается на macOS")

    import ctypes
    from ctypes import wintypes
    import time

    fired_uis = []
    api = _make_api(monkeypatch)
    api.push_ui = lambda name: fired_uis.append(name)

    from core import settings as cfg
    monkeypatch.setattr(cfg, "load", lambda: {})
    monkeypatch.setattr(cfg, "update", lambda patch: None)

    class FakeShell32:
        def ShellExecuteExW(self, p_info):
            # p_info это byref объект, его внутренняя структура доступна через _obj
            p_info._obj.hProcess = 9999
            return 1

    class FakeKernel32:
        def WaitForSingleObject(self, handle, timeout):
            return 0  # WAIT_OBJECT_0

        def GetExitCodeProcess(self, handle, p_code):
            p_code._obj.value = 0  # Код 0 (успех)
            return 1

        def CloseHandle(self, handle):
            return 1

        def GetLastError(self):
            return 0

    monkeypatch.setattr(ctypes.windll, "shell32", FakeShell32(), raising=False)
    monkeypatch.setattr(ctypes.windll, "kernel32", FakeKernel32(), raising=False)

    fake_ocr = types.ModuleType("core.ocr_windows")
    fake_ocr.reset_cache = lambda: None
    fake_ocr.is_available = lambda: True
    monkeypatch.setitem(sys.modules, "core.ocr_windows", fake_ocr)

    res = api.install_windows_ocr()
    assert res["ok"] is True

    # Ждем завершения фонового потока
    deadline = time.monotonic() + 2.0
    while "windowsOcrInstallDone" not in fired_uis and time.monotonic() < deadline:
        time.sleep(0.05)

    assert "windowsOcrInstallDone" in fired_uis


