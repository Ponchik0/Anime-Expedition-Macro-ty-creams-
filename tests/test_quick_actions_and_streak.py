"""ТЕСТЫ: АВТО-РЕСТАРТ, VIP РЕДЖОИН И ВИНСТРИК.

Проверяет новые элементы карточки управления:
1. Подсчёт серии побед (Win Streak) и лучшего результата в сессии / за всё время.
2. Переключение режима Auto-Restart Loop и его сохранение в настройках.
3. Запуск перезахода в VIP-лобби через vip_lobby_rejoin.
4. Регистрацию горячих клавиш auto_restart_loop (F6) и vip_rejoin (F10).

Все тесты изолированы, не обращаются к Windows API и безопасно идут на CI.
"""
import threading
import time
import pytest

import main
from core import settings as cfg


def test_win_streak_calculates_consecutive_wins_and_best_record(monkeypatch, tmp_path):
    """Счётчик серии побед сбрасывается при поражении, а рекорд сохраняется.

    БАГ: Без раздельного отслеживания текущего стрика и рекорда сессия
    теряла максимальную серию при первом же поражении, и на табло отображался 0,
    хотя до этого могло быть 10+ побед подряд.
    """
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(settings_file))

    api = main.Api()
    # Исходно стрик 0
    st = api.get_status()
    assert st["win_streak"] == 0
    assert st["best_streak"] == 0

    # 3 победы подряд
    api._record_match_result("win", "Summer", "1:30")
    api._record_match_result("win", "Summer", "1:25")
    api._record_match_result("win", "Summer", "1:28")

    st = api.get_status()
    assert st["win_streak"] == 3
    assert st["best_streak"] == 3

    # Поражение: текущий стрик обнуляется, рекорд остаётся 3
    api._record_match_result("loss", "Summer", "0:45")
    st = api.get_status()
    assert st["win_streak"] == 0
    assert st["best_streak"] == 3

    # Ещё 1 победа: стрик 1, рекорд всё ещё 3
    api._record_match_result("win", "Summer", "1:20")
    st = api.get_status()
    assert st["win_streak"] == 1
    assert st["best_streak"] == 3

    # Очистка истории: сбрасывает и историю, и винстрик
    api.clear_run_history()
    st = api.get_status()
    assert st["win_streak"] == 0
    assert st["best_streak"] == 0
    api.stopping.set()


def test_auto_restart_loop_toggle_and_persistence(monkeypatch, tmp_path):
    """Флаг Auto-Restart Loop переключается атомарно и сохраняется в settings.json.

    БАГ: Если переключатель не обновляет settings.json через cfg.update,
    то при фоновом сохранении других параметров (например, координат)
    значение авто-рестарта затиралось.
    """
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(settings_file))

    api = main.Api()
    # По умолчанию выключен
    st = api.get_status()
    assert st["auto_restart_loop"] is False

    # Первое переключение -> True
    res1 = api.toggle_auto_restart_loop()
    assert res1["ok"] is True
    assert res1["enabled"] is True
    assert api.get_status()["auto_restart_loop"] is True
    assert cfg.load().get("auto_restart_loop") is True

    # Второе переключение -> False
    res2 = api.toggle_auto_restart_loop()
    assert res2["ok"] is True
    assert res2["enabled"] is False
    assert api.get_status()["auto_restart_loop"] is False
    assert cfg.load().get("auto_restart_loop") is False
    api.stopping.set()


def test_vip_lobby_rejoin_triggers_rejoin_or_launch(monkeypatch, tmp_path):
    """vip_lobby_rejoin вызывает force_rejoin при живом окне или launch_roblox при закрытом.

    БАГ: Если игра вылетела (окна нет), старый force_rejoin тихо падал
    с ошибкой no_roblox вместо того, чтобы открыть клиент заново.
    """
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(settings_file))

    api = main.Api()
    launched = []
    rejoined = []

    monkeypatch.setattr(api, "launch_roblox", lambda: (launched.append(True), {"ok": True})[1])
    monkeypatch.setattr(api.runner, "debug_force_rejoin", lambda hwnd, getter: (rejoined.append(hwnd), True)[1])
    monkeypatch.setattr(main.wm, "is_window", lambda hwnd: hwnd == 12345)

    # 1. Окна игры нет -> должен вызвать launch_roblox
    api.game_hwnd = None
    res_launch = api.vip_lobby_rejoin()
    assert res_launch["ok"] is True
    assert len(launched) == 1
    assert len(rejoined) == 0

    # 2. Окно игры есть -> должен вызвать debug_force_rejoin
    api.game_hwnd = 12345
    res_rejoin = api.vip_lobby_rejoin()
    assert res_rejoin["ok"] is True
    assert len(rejoined) == 1
    assert rejoined[0] == 12345
    api.stopping.set()


def test_hotkey_defaults_include_auto_restart_and_vip_rejoin():
    """Действия auto_restart_loop и vip_rejoin зарегистрированы в HOTKEY_DEFAULTS и LABELS.

    БАГ: Если действие отсутствует в HOTKEY_DEFAULTS, привязка в интерфейсе
    не могла восстановиться при сбросе настроек или падении settings.json.
    """
    assert "auto_restart_loop" in main.HOTKEY_DEFAULTS
    assert main.HOTKEY_DEFAULTS["auto_restart_loop"] == "alt+f5"
    assert "auto_restart_loop" in main.HOTKEY_LABELS

    assert "vip_rejoin" in main.HOTKEY_DEFAULTS
    assert main.HOTKEY_DEFAULTS["vip_rejoin"] == "alt+f6"
    assert "vip_rejoin" in main.HOTKEY_LABELS


def test_skip_current_task_idle_rotation_and_running_dispatch(monkeypatch, tmp_path):
    """Пропуск задачи перемещает первую задачу в конец списка в режиме ожидания (IDLE),
    а во время работы передаёт запрос раннеру на безопасный переход к следующей задаче.

    БАГ: Без кнопки Skip и обработчика в API пользователю приходилось
    полностью останавливать макрос (Stop F2), вручную пересортировывать задачи
    в настройках и заново запускать макрос, что сбрасывало таймер и прерывало цикл.
    """
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(settings_file))

    api = main.Api()

    # 1. Очередь пуста или содержит 1 задачу -> no_tasks_to_skip
    api.save_tasks([])
    assert api.skip_current_task()["ok"] is False

    api.save_tasks([{"name": "Task 1", "map": "Summer"}])
    assert api.skip_current_task()["ok"] is False

    # 2. Несколько задач в IDLE: первая перемещается в конец
    tasks = [
        {"name": "Task 1", "map": "Summer"},
        {"name": "Task 2", "map": "Windmill Village"},
        {"name": "Task 3", "map": "Regular Challenge"},
    ]
    api.save_tasks(tasks)
    res = api.skip_current_task()
    assert res["ok"] is True
    assert res["running"] is False
    current_tasks = api.get_tasks()
    assert len(current_tasks) == 3
    assert current_tasks[0]["name"] == "Task 2"
    assert current_tasks[1]["name"] == "Task 3"
    assert current_tasks[2]["name"] == "Task 1"

    # 3. Во время работы макроса: раннер получает запрос на пропуск
    monkeypatch.setattr(api.runner, "is_running", lambda: True)
    assert api.runner._skip_task_requested is False
    res_run = api.skip_current_task()
    assert res_run["ok"] is True
    assert res_run["running"] is True
    assert api.runner._skip_task_requested is True
    api.stopping.set()


def test_automations_status_reported_in_get_status(monkeypatch, tmp_path):
    """Статус фоновых автоматизаций (Shop, Bounty, Crafting, Fuel) отдаётся в get_status.

    БАГ: Ранее состояние фоновых сервисов макроса (скупка в магазине торговца,
    авто-баунти, крафт и контроль топлива) было спрятано в глубине настроек,
    и на главной панели не было видно, активны ли они и когда сработают.
    """
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(settings_file))

    api = main.Api()
    st = api.get_status()
    assert "automations" in st
    auto = st["automations"]
    assert "shop" in auto and "bounty" in auto and "crafting" in auto and "fuel" in auto

    # По умолчанию все выключены
    assert auto["shop"]["enabled"] is False
    assert auto["bounty"]["enabled"] is False
    assert auto["crafting"]["enabled"] is False
    assert auto["fuel"]["enabled"] is False

    # Включаем Auto-Shop
    api.set_auto_shop_enabled(True)
    st_shop = api.get_status()
    assert st_shop["automations"]["shop"]["enabled"] is True
    assert st_shop["automations"]["shop"]["status"] == "Active"

    # Включаем Баунти через настройки
    cfg.update({"bounty": {"enabled": True, "mythic_only": True, "remaining": 7}})
    st_bounty = api.get_status()
    assert st_bounty["automations"]["bounty"]["enabled"] is True
    assert "Mythic" in st_bounty["automations"]["bounty"]["status"]
    assert "7/10" in st_bounty["automations"]["bounty"]["status"]
    api.stopping.set()

