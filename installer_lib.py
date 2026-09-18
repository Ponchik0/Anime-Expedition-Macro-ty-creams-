"""Общая часть установщика и бутстраппера: релизы, безопасная распаковка,
ярлыки и запись в «Установка и удаление программ».

ЗАЧЕМ ОТДЕЛЬНЫМ МОДУЛЕМ. Здесь лежит is_inside — проверка, что распаковываемый
файл не уедет за пределы папки установки. Имена внутри zip это НЕДОВЕРЕННЫЙ
ввод, и запись «..\\..\\Windows\\System32\\...» или «D:\\payload.exe» внутри
архива обязана быть отброшена. Держать такую проверку в двух копиях (в
bootstrap.py и в installer.py) нельзя: копии расходятся, и та, что отстала,
становится дырой. Поэтому одна реализация на всех.

ЗАВИСИМОСТИ ДЕРЖИМ ПУСТЫМИ намеренно. Модуль подключают и установщик, и
бутстраппер — обе сборки должны оставаться маленькими, чтобы их было не жалко
скинуть в Discord. Отсюда только стандартная библиотека плюс requests; ни
core/, ни opencv, ни pywebview сюда тянуть нельзя (core тащит за собой всё
зрение макроса, и установщик распух бы до размеров самого приложения).
"""
import os
import subprocess
import sys
import tempfile
import zipfile
import base64

import requests

APP_NAME = "Anime Expeditions Macro"
RELEASES_REPO = "Ponchik0/Anime-Expedition-Macro-ty-creams-"
RELEASES_PAGE = f"https://github.com/{RELEASES_REPO}/releases/latest"
API_URL = f"https://api.github.com/repos/{RELEASES_REPO}/releases/latest"
# Совпадает с именем из release.yml. Дефисы намеренно: GitHub заменяет пробелы
# в именах вложений на точки, дефисы остаются как есть.
ZIP_ASSET_NAME = "Anime-Expeditions-Macro-Windows.zip"
EXE_NAME = f"{APP_NAME}.exe"

# Ключ в реестре, по которому Windows показывает программу в списке
# установленных. HKCU, а не HKLM: установка идёт в профиль пользователя и прав
# администратора не требует (см. комментарий про LOCALAPPDATA в installer.py).
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\AnimeExpeditionsMacro"

# Что принадлежит ПОЛЬЗОВАТЕЛЮ, а не установщику. Ни обновление, ни удаление
# не трогают это без явного разрешения: тут его настройки, шаблоны,
# записанные маршруты и подменённые эталоны — то, что он делал руками и чего
# никакая переустановка не вернёт.
USER_OWNED = ("settings.json", "Paths", "Templates", "Recordings", "debug")


HEADERS = {"User-Agent": f"{APP_NAME}-Installer"}


def is_inside(root: str, target: str) -> bool:
    """Действительно ли target лежит внутри root.

    Проверяется РАЗРЕШЁННЫЙ путь, а не совпадение по образцу. Проверка вида
    «есть ли двоеточие в первом сегменте» обходится записью «a/b/D:/x.exe»:
    os.path.join начинает путь заново с любого абсолютного сегмента, и файл
    уезжает мимо папки установки. Вопрос «где путь в итоге оказался» так
    обмануть нельзя."""
    root = os.path.realpath(root)
    target = os.path.realpath(target)
    return target == root or target.startswith(root + os.sep)


def latest_tag(timeout: float = 10.0):
    """Последний тег релиза через редирект, а не через API.

    github.com/.../releases/latest отвечает 302 на страницу тега. Так номер
    версии узнаётся, ни разу не потревожив api.github.com, у которого лимит
    60 запросов в час НА IP — а один IP бывает общим на школу или на целого
    провайдера."""
    try:
        resp = requests.head(RELEASES_PAGE, headers=HEADERS, allow_redirects=False, timeout=timeout)
        location = resp.headers.get("Location", "")
        if "/releases/tag/" in location:
            return location.rsplit("/releases/tag/", 1)[-1]
    except Exception:
        pass
    return None


def zip_asset_url(timeout: float = 15.0) -> str:
    """Ссылка на архив сборки. Если API недоступен или упёрся в лимит —
    собираем адрес сами: имя вложения задано release.yml и не меняется, так
    что построенная ссылка ничем не хуже полученной."""
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            assets = resp.json().get("assets", [])
            for asset in assets:
                if asset.get("name", "").lower() == ZIP_ASSET_NAME.lower():
                    return asset["browser_download_url"]
            # Если точного совпадения нет, ищем любой zip для Windows
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".zip") and ("windows" in name or "macro" in name):
                    return asset["browser_download_url"]
    except Exception:
        pass
    return f"https://github.com/{RELEASES_REPO}/releases/latest/download/{ZIP_ASSET_NAME}"


def download(url: str, dest_path: str, on_progress=None, timeout: float = 120.0) -> None:
    """Качает файл, по дороге сообщая (получено, всего).

    total = 0, если сервер не прислал Content-Length: это не повод падать,
    вызывающий просто покажет неопределённый индикатор вместо процентов."""
    with requests.get(url, headers=HEADERS, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        done = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if on_progress:
                    on_progress(done, total)


def extract_release(zip_path: str, dest_dir: str, on_progress=None) -> int:
    """Раскладывает архив сборки в dest_dir. Возвращает число записанных файлов.

    Два правила, и оба важны:
      • всё, что уезжает за пределы dest_dir, пропускается молча (см. is_inside);
      • файлы внутри Assets/ пишутся ТОЛЬКО ЕСЛИ ИХ ЕЩЁ НЕТ. Это папка, куда
        человек кладёт свои эталоны взамен неподошедших; перезаписать её
        содержимым из архива значит выбросить ровно ту правку, ради которой
        папка и существует. Ту же политику применяет core/updater.py.
    """
    written = 0
    with zipfile.ZipFile(zip_path) as zf:
        entries = [i for i in zf.infolist() if not i.is_dir()]
        for n, info in enumerate(entries, 1):
            parts = info.filename.replace("\\", "/").split("/")
            # Точки уводят путь выше папки (zip-slip), а двоеточие — признак буквы
            # диска в Windows (например, a/b/D:/payload.exe) или NTFS-потока, из-за
            # которого os.path.join либо переключает диск, либо приземляет файл мимо.
            if not parts or any(p in ("", ".", "..") or ":" in p for p in parts):
                continue
            dest = os.path.join(dest_dir, *parts)
            if not is_inside(dest_dir, dest):
                continue
            if parts[0].lower() == "assets" and os.path.exists(dest):
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as out:
                out.write(src.read())
            written += 1
            if on_progress:
                on_progress(n, len(entries))
    return written


def install_release(dest_dir: str, on_status=None, on_progress=None) -> str:
    """Скачивает и раскладывает сборку в dest_dir. Возвращает тег версии.
    Если рядом с установщиком уже лежит готовый zip-архив, используется
    он напрямую без скачивания."""
    def say(text):
        if on_status:
            on_status(text)

    os.makedirs(dest_dir, exist_ok=True)
    tag = latest_tag() or ""

    # Проверяем локальный zip рядом с exe установщика (офлайн/ручная загрузка)
    try:
        installer_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        local_zip = os.path.join(installer_dir, ZIP_ASSET_NAME)
        if os.path.isfile(local_zip) and os.path.getsize(local_zip) > 1024 * 1024:
            say("Установка из локального архива…")
            extract_release(local_zip, dest_dir, on_progress=on_progress)
            return tag or "v2.0.0"
    except Exception:
        pass

    say("Ищу последнюю версию…")
    url = zip_asset_url()

    fd, tmp_zip = tempfile.mkstemp(suffix=".zip", prefix="aem_")
    os.close(fd)
    try:
        say("Скачиваю…")
        download(url, tmp_zip, on_progress=on_progress)
        say("Распаковываю…")
        extract_release(tmp_zip, dest_dir, on_progress=on_progress)
    finally:
        try:
            os.remove(tmp_zip)
        except OSError:
            pass
    return tag


def app_exe_path(install_dir: str) -> str:
    """Путь до exe приложения. Имя НЕ прибито намертво: сначала известное, а
    если его нет — единственный .exe рядом, кроме самого установщика. Так
    будущее переименование сборки не превращает установщик в тыкву (ровно на
    этом уже спотыкались, см. историю bootstrap.py)."""
    hinted = os.path.join(install_dir, EXE_NAME)
    if os.path.isfile(hinted):
        return hinted
    try:
        me = os.path.basename(os.path.abspath(sys.argv[0])).lower()
        found = [f for f in os.listdir(install_dir)
                 if f.lower().endswith(".exe") and f.lower() != me]
    except OSError:
        found = []
    if len(found) == 1:
        return os.path.join(install_dir, found[0])
    return hinted


# ------------------------------------------------------------------ ЯРЛЫКИ --
# Через VBScript, а не через pywin32. Ярлык Windows это COM-объект
# WScript.Shell, и «правильный» путь потребовал бы зависимости, которая одна
# весит больше всего установщика. cscript есть в любой Windows, скрипт живёт
# несколько миллисекунд во временной папке и удаляется.
_VBS = '''Set s = CreateObject("WScript.Shell")
Set l = s.CreateShortcut({link})
l.TargetPath = {target}
l.WorkingDirectory = {workdir}
l.IconLocation = {icon}
l.Description = {desc}
l.Save
'''


def _vbs_str(value: str) -> str:
    """Строковый литерал VBScript. Кавычка внутри удваивается — иначе путь
    вида C:\\Папка "Игры"\\ разорвал бы скрипт."""
    return '"' + str(value).replace('"', '""') + '"'


def create_shortcut(link_path: str, target: str, workdir: str = "",
                    icon: str = "", description: str = "") -> bool:
    """Создаёт .lnk. Возвращает True, если файл появился.

    Неудача здесь НЕ должна валить установку: приложение уже разложено и
    работает, отсутствие ярлыка — неудобство, а не поломка."""
    script = _VBS.format(
        link=_vbs_str(link_path),
        target=_vbs_str(target),
        workdir=_vbs_str(workdir or os.path.dirname(target)),
        icon=_vbs_str(icon or target),
        desc=_vbs_str(description or APP_NAME),
    )
    link_dir = os.path.dirname(os.path.abspath(link_path))
    os.makedirs(link_dir, exist_ok=True)
    try:
        fd, path = tempfile.mkstemp(suffix=".vbs", prefix="aem_lnk_")
    except Exception:
        fd, path = tempfile.mkstemp(suffix=".vbs", prefix="aem_lnk_", dir=link_dir)
    try:
        # UTF-16, а НЕ utf-8-sig. Windows Script Host понимает либо ANSI, либо
        # UTF-16LE с BOM; на BOM от UTF-8 он падает сразу на первом символе
        # («недопустимый знак» в позиции 1,1) и ярлык не создаётся вообще.
        # Ошибка была не видна, потому что cscript зовётся с capture_output и
        # его stderr никуда не шёл. ANSI тоже не годится: в пути к папке
        # пользователя бывает кириллица, а в описании она есть всегда.
        with os.fdopen(fd, "w", encoding="utf-16") as f:
            f.write(script)
        subprocess.run(["cscript", "//nologo", path], timeout=30,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                       capture_output=True)
    except Exception:
        pass
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

    # Fallback на PowerShell, если cscript заблокирован политиками безопасности или ASR.
    # Команду кодируем в base64 UTF-16LE (-EncodedCommand), чтобы кириллические пути
    # и пробелы не ломались в консоли независимо от текущей кодовой страницы Windows.
    if not os.path.isfile(link_path):
        try:
            escaped_link = link_path.replace("'", "''")
            escaped_target = target.replace("'", "''")
            escaped_workdir = (workdir or os.path.dirname(target)).replace("'", "''")
            escaped_icon = (icon or target).replace("'", "''")
            escaped_desc = (description or APP_NAME).replace("'", "''")
            ps_script = (
                f"$ws = New-Object -ComObject WScript.Shell; "
                f"$s = $ws.CreateShortcut('{escaped_link}'); "
                f"$s.TargetPath = '{escaped_target}'; "
                f"$s.WorkingDirectory = '{escaped_workdir}'; "
                f"$s.IconLocation = '{escaped_icon}'; "
                f"$s.Description = '{escaped_desc}'; "
                f"$s.Save()"
            )
            encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                capture_output=True,
            )
        except Exception:
            pass

    return os.path.isfile(link_path)


def desktop_dir() -> str:
    return os.path.join(os.path.expanduser("~"), "Desktop")


def start_menu_dir() -> str:
    return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                        "Microsoft", "Windows", "Start Menu", "Programs")


def default_install_dir() -> str:
    """%LOCALAPPDATA%\\<APP_NAME>.

    Не Program Files, и это не лень. Приложение обновляет САМО СЕБЯ, подменяя
    exe на месте (core/updater.py). В Program Files такая подмена требует прав
    администратора, то есть каждое обновление упиралось бы в запрос UAC — а
    оно происходит в фоне, когда спрашивать некого. В профиле пользователя
    обновление проходит молча и работает.
    """
    base = os.environ.get("LOCALAPPDATA") or os.path.join(
        os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(base, APP_NAME)


# ------------------------------------------ ЗАПИСЬ В СПИСОК УСТАНОВЛЕННЫХ --
def register_uninstall(install_dir: str, version: str, uninstaller: str) -> bool:
    """Показывает программу в «Установка и удаление программ».

    Без этой записи установщик, который раскладывает файлы и делает ярлыки,
    выглядит для системы как распаковщик: удалять придётся руками, а человек
    не обязан знать, где именно лежат файлы."""
    try:
        import winreg
    except ImportError:
        return False
    try:
        size_kb = 0
        for root, _dirs, files in os.walk(install_dir):
            for name in files:
                try:
                    size_kb += os.path.getsize(os.path.join(root, name)) // 1024
                except OSError:
                    pass
        exe = app_exe_path(install_dir)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
            values = {
                "DisplayName": APP_NAME,
                "DisplayVersion": version.lstrip("v") or "",
                "Publisher": "Ponchik0",
                "InstallLocation": install_dir,
                "DisplayIcon": exe,
                "UninstallString": f'"{uninstaller}" --uninstall',
                "URLInfoAbout": f"https://github.com/{RELEASES_REPO}",
            }
            for name, value in values.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            # NoModify/NoRepair: у установщика нет режимов «изменить» и
            # «восстановить», и предлагать их в интерфейсе Windows значило бы
            # обещать кнопки, которые ничего не делают.
            for name in ("NoModify", "NoRepair"):
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, size_kb)
        return True
    except OSError:
        return False


def unregister_uninstall() -> bool:
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
        return True
    except Exception:
        return False


def read_install_dir():
    """Куда установлено по записи в реестре, если установка уже была. Нужно,
    чтобы повторный запуск установщика предлагал ту же папку, а не заводил
    вторую копию рядом."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
            value, _ = winreg.QueryValueEx(key, "InstallLocation")
            return value or None
    except Exception:
        return None


def removable_entries(install_dir: str, keep_user_data: bool):
    """Что удалять при деинсталляции.

    keep_user_data=True — настройки, шаблоны, маршруты, записи и правки
    эталонов остаются. Это значение по умолчанию: человек, удаляющий
    приложение, чтобы поставить заново, не ожидает потерять собранные
    сценарии, а восстановить их неоткуда."""
    try:
        names = os.listdir(install_dir)
    except OSError:
        return []
    if not keep_user_data:
        return [os.path.join(install_dir, n) for n in names]
    keep = {n.lower() for n in USER_OWNED}
    return [os.path.join(install_dir, n) for n in names if n.lower() not in keep]
