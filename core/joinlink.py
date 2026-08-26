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
from urllib.parse import parse_qs, urlparse

_HTTP = re.compile(r"^https?://(www\.)?roblox\.com/", re.I)
_PROTO = re.compile(r"^roblox://", re.I)


def normalize(link: str) -> str:
    return (link or "").strip()


def looks_valid(link: str) -> bool:
    link = normalize(link)
    if not link:
        return False
    return bool(_HTTP.match(link) or _PROTO.match(link))


def to_roblox_protocol(link: str) -> str:
    """Преобразует веб-ссылку https://www.roblox.com/... в прямой протокол roblox://.

    ПОЧЕМУ ЭТО КРИТИЧНО: если открывать https:// ссылку через os.startfile / браузер,
    Windows открывает окно браузера (Edge/Chrome), которое перекрывает макрос,
    ворует фокус и ломает всё управление. Протокол roblox:// запускает Roblox Player
    напрямую, без единого окна браузера.
    """
    link = normalize(link)
    if not link:
        from core.runner_constants import REJOIN_DEEPLINK
        return REJOIN_DEEPLINK
    if link.lower().startswith("roblox://"):
        return link
    try:
        parsed = urlparse(link)
        qs = parse_qs(parsed.query)
        match_games = re.search(r"/games/(\d+)", parsed.path)
        if match_games:
            place_id = match_games.group(1)
            link_code = (qs.get("privateServerLinkCode") or qs.get("linkCode") or [None])[0]
            if link_code:
                return f"roblox://experiences/start?placeId={place_id}&linkCode={link_code}"
            return f"roblox://experiences/start?placeId={place_id}"
        if "share" in parsed.path:
            code = (qs.get("code") or [None])[0]
            share_type = (qs.get("type") or ["Server"])[0]
            if code:
                return f"roblox://navigation/share_links?code={code}&type={share_type}"
    except Exception:
        pass
    return link


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
    Всегда возвращает URI протокола roblox://, чтобы не открывать браузер.
    """
    from core.runner_constants import REJOIN_DEEPLINK
    link = normalize(cfg.load().get("private_server_link", ""))
    if looks_valid(link):
        return to_roblox_protocol(link)
    return REJOIN_DEEPLINK


def is_private() -> bool:
    return looks_valid(cfg.load().get("private_server_link", ""))

