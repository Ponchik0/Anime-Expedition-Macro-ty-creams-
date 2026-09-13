import json
import os
import sys
import types
import main


def test_import_tasks_file_reads_utf8_bom_without_crashing(monkeypatch, tmp_path):
    """Проверяет, что импорт файлов с UTF-8 BOM (стандартное сохранение в Блокноте Windows)
    не падает с ошибкой JSONDecodeError: Unexpected UTF-8 BOM.
    """
    file_with_bom = tmp_path / "bom_template.json"
    payload = {"kind": "anime-expeditions-templates", "templates": {"Farm 1": {"blocks": []}}}
    raw_bytes = b"\xef\xbb\xbf" + json.dumps(payload).encode("utf-8")
    file_with_bom.write_bytes(raw_bytes)

    monkeypatch.setitem(
        sys.modules, "webview",
        types.SimpleNamespace(FileDialog=types.SimpleNamespace(SAVE=2, OPEN=1)))

    class Window:
        def create_file_dialog(self, dialog_type, **kwargs):
            return [str(file_with_bom)]

    api = main.Api()
    api._window = Window()

    res = api.import_tasks_file("templates")
    assert res["ok"] is True
    assert res["data"] == payload
    assert res["filename"] == "bom_template.json"


def test_import_tasks_file_decodes_cream_share_codes_from_file(monkeypatch, tmp_path):
    """Проверяет, что если пользователь выбрал файл, в котором сохранён сырой CREAM-код
    вместо обычного JSON, импорт не падает, а декодирует код через core.share.
    """
    from core import share
    sample_blocks = [{"type": "place_unit", "params": {"x": 100, "y": 200}}]
    code = share.encode_template_code({"name": "My Shared Macro", "blocks": sample_blocks})
    share_file = tmp_path / "shared_code.txt"
    share_file.write_text(code, encoding="utf-8")

    monkeypatch.setitem(
        sys.modules, "webview",
        types.SimpleNamespace(FileDialog=types.SimpleNamespace(SAVE=2, OPEN=1)))

    class Window:
        def create_file_dialog(self, dialog_type, **kwargs):
            return [str(share_file)]

    api = main.Api()
    api._window = Window()

    res = api.import_tasks_file("templates")
    assert res["ok"] is True
    assert res["data"]["ok"] is True
    assert "My Shared Macro" in res["data"]["templates"]
    assert res["filename"] == "shared_code.txt"


def test_get_log_history_returns_full_newline_delimited_log_buffer():
    """Проверяет, что get_log_history возвращает весь буфер логов для кнопки
    «Скопировать логи» (Copy Logs), объединённый переносами строк.
    """
    api = main.Api()
    api._log_history = ["[Macro] Line 1", "[Macro] Line 2", "[Vision] Found target"]
    history = api.get_log_history()
    assert history == "[Macro] Line 1\n[Macro] Line 2\n[Vision] Found target"


def test_start_macro_preflight_blockers_return_descriptive_error_message(monkeypatch):
    """Проверяет, что при сбое предстартовых проверок start_macro возвращает
    понятное человеческое описание причины и необходимого действия, а не просто
    сухой технический код 'preflight_blocker', который пугал новых пользователей.
    """
    api = main.Api()
    mock_preflight = {
        "ok": False,
        "has_blocker": True,
        "checks": [
            {
                "id": "roblox_running",
                "ok": False,
                "blocker": True,
                "message": "Roblox is not running.",
                "action": "Launch Roblox first."
            }
        ],
        "warnings": []
    }
    monkeypatch.setattr(api, "run_preflight_check", lambda: mock_preflight)

    result = api.start_macro()
    assert result["ok"] is False
    assert result["reason"] == "preflight_blocker"
    assert "Roblox is not running. (Launch Roblox first.)" in result["message"]


def test_click_found_image_forces_shuffle_click_for_event_buttons(monkeypatch):
    """Проверяет, что клик по кнопке Event в лобби ('nav_event' / 'nav_events')
    принудительно активирует shuffle=True. Без реальных микродвижений мыши
    движок интерфейса Roblox в лобби при масштабировании разрешения не активирует кнопку.
    """
    from core.runner import MacroRunner
    import core.vision as vision

    calls = []

    class DummyMouse:
        def click(self, x, y):
            calls.append(("click", x, y))

        def shuffle_click(self, x, y):
            calls.append(("shuffle_click", x, y))

    r = MacroRunner(DummyMouse(), None, lambda msg: None)

    match_dict = {"cx": 520, "cy": 320, "score": 0.95}
    monkeypatch.setattr(vision, "wait_for_image", lambda *args, **kwargs: match_dict)
    monkeypatch.setattr(vision, "ref_to_screen", lambda hwnd, cx, cy: (cx, cy))

    # Для обычной кнопки без shuffle (shuffle=False)
    calls.clear()
    r._click_found_image(12345, "nav_settings", timeout=1.0, shuffle=False)
    assert calls == [("click", 520, 320)]

    # Для nav_event принудительно должен вызываться shuffle_click даже если shuffle=False передан
    calls.clear()
    r._click_found_image(12345, "nav_event", timeout=1.0, shuffle=False)
    assert calls == [("shuffle_click", 520, 320)]

    # Для nav_events аналогично
    calls.clear()
    r._click_found_image(12345, "nav_events", timeout=1.0, shuffle=False)
    assert calls == [("shuffle_click", 520, 320)]
