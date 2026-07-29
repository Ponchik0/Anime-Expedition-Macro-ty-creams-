"""Куда заходить в Roblox: на приватный сервер игрока или в общее лобби.

В движке ссылка была зашита константой (REJOIN_DEEPLINK в
core/runner_constants.py) — макрос всегда попадал в ПУБЛИЧНУЮ игру, и
задать свой сервер было негде.

Здесь ровно одна развилка:
    поле «Приватный сервер» заполнено -> идём по этой ссылке;
    пусто                             -> прежняя зашитая ссылка, как было.

Отдельный модуль, а не функция в runner_constants: тот модуль — набор
голых констант, и тянуть в него чтение настроек значит завязать константы
на файл настроек. Здесь же читается settings.json, поэтому место своё.

Ссылка никуда не отправляется и лежит только в settings.json на диске
игрока (а settings.json в .gitignore).
"""
from __future__ import annotations

import re

from core import settings as cfg

# Ссылка приватного сервера Roblox бывает двух видов:
#   https://www.roblox.com/games/<id>/...?privateServerLinkCode=XXXX
#   roblox://experiences/start?placeId=<id>&linkCode=XXXX
# Проверяем мягко: задача — отсечь явный мусор (пустая строка, «привет»),
# а не изображать валидатор URL. Ошибётся человек в коде сервера — это
# видно сразу по тому, куда его закинуло.
_HTTP = re.compile(r"^https?://(www\.)?roblox\.com/", re.I)
_PROTO = re.compile(r"^roblox://", re.I)


def normalize(link: str) -> str:
    return (link or "").strip()


def looks_valid(link: str) -> bool:
    link = normalize(link)
    if not link:
        return False
    return bool(_HTTP.match(link) or _PROTO.match(link))


def describe(link: str) -> dict:
    """Состояние для интерфейса: что показать под полем ввода."""
    link = normalize(link)
    if not link:
        return {"state": "empty",
                "text": "Не задан — макрос заходит в общее лобби."}
    if not looks_valid(link):
        return {"state": "bad",
                "text": "Не похоже на ссылку Roblox. Нужна https://www.roblox.com/… "
                        "или roblox://…"}
    return {"state": "ok",
            "text": "Ссылка принята — макрос будет заходить на этот сервер."}


def get_join_link() -> str:
    """Ссылка, по которой открывать игру.

    Пусто или мусор в настройке -> прежнее поведение движка (общее лобби).
    Мусор намеренно НЕ роняет запуск: лучше зайти в публичную игру, чем не
    зайти никуда, — макрос всё равно доберётся до боя через меню.
    """
    from core.runner_constants import REJOIN_DEEPLINK
    link = normalize(cfg.load().get("private_server_link", ""))
    return link if looks_valid(link) else REJOIN_DEEPLINK


def is_private() -> bool:
    return looks_valid(cfg.load().get("private_server_link", ""))
