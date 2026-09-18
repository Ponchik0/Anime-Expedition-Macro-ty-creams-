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


def download(url: str, dest_path: str, on_progress=None,
             timeout=(10.0, 45.0), max_retries: int = 5) -> None:
    """Качает файл с поддержкой докачки (HTTP Range) и повторных попыток.

    При обрыве связи на 100 из 160 МБ не начинает скачивание с нуля, а
    докачивает оставшийся хвост. Это предотвращает сбои на нестабильных
    сетях и медленных соединениях."""
    import time
    done = 0
    total = 0

    for attempt in range(max_retries):
        try:
            req_headers = dict(HEADERS)
            mode = "wb"
            if os.path.isfile(dest_path):
                done = os.path.getsize(dest_path)
                if done > 0:
                    req_headers["Range"] = f"bytes={done}-"
                    mode = "ab"

            with requests.get(url, headers=req_headers, stream=True, timeout=timeout) as r:
                if r.status_code == 416:
                    # Диапазон не удовлетворяется — файл уже скачан целиком
                    break
                if r.status_code == 206:
                    cr = r.headers.get("Content-Range", "")
                    if "/" in cr:
                        try:
                            total = int(cr.rsplit("/", 1)[-1])
                        except ValueError:
                            pass
                elif r.status_code == 200:
                    # Сервер вернул файл с начала (не поддерживает Range или мы запросили с 0)
                    done = 0
                    mode = "wb"
                    total = int(r.headers.get("content-length") or 0)
                else:
                    r.raise_for_status()

                with open(dest_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=128 * 1024):
                        if not chunk:
                            continue
                        f.write(chunk)
                        done += len(chunk)
                        if on_progress:
                            on_progress(done, total)

                # Успешно дочитали весь поток
                if total == 0 or done >= total:
                    break
        except (requests.exceptions.RequestException, OSError):
            if attempt >= max_retries - 1:
                raise
            time.sleep(1.5)


def extract_release(zip_path: str, dest_dir: str, on_progress=None) -> int:
    """Раскладывает архив сборки в dest_dir. Возвращает число записанных файлов.

    Два правила, и оба важны:
      • всё, что уезжает за пределы dest_dir, пропускается молча (см. is_inside);
      • файлы внутри Assets/ пишутся ТОЛЬКО ЕСЛИ ИХ ЕЩЁ НЕТ. Это папка, куда
        человек кладёт свои эталоны взамен неподошедших; перезаписать её
        содержимым из архива значит выбросить ровно ту правку, ради которой
        папка и существует. Ту же политику применяет core/updater.py.
    """
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Corrupted or invalid ZIP archive: {zip_path}")

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


def _is_valid_release_archive(fpath: str) -> bool:
    """Проверяет, что файл является настоящим архивом релиза, а не исходным кодом или битым файлом."""
    try:
        if not os.path.isfile(fpath) or os.path.getsize(fpath) < 10 * 1024 * 1024:
            return False
        if not zipfile.is_zipfile(fpath):
            return False
        with zipfile.ZipFile(fpath) as zf:
            names = [os.path.basename(n).lower() for n in zf.namelist()]
            return EXE_NAME.lower() in names
    except Exception:
        return False


def find_local_archive() -> str | None:
    """Ищет готовый zip-архив сборки рядом с установщиком или в папке Загрузок.
    Позволяет установить приложение даже если GitHub недоступен или заблокирован."""
    search_dirs = []
    try:
        argv_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        if os.path.isdir(argv_dir):
            search_dirs.append(argv_dir)
    except Exception:
        pass

    cwd = os.getcwd()
    if os.path.isdir(cwd) and cwd not in search_dirs:
        search_dirs.append(cwd)

    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.isdir(downloads) and downloads not in search_dirs:
        search_dirs.append(downloads)

    for d in search_dirs:
        # Сначала проверяем точное имя ZIP_ASSET_NAME в текущей папке
        exact = os.path.join(d, ZIP_ASSET_NAME)
        if _is_valid_release_archive(exact):
            return exact

        # Затем ищем любые подходящие zip-архивы в этой папке
        dir_candidates = []
        try:
            for fname in os.listdir(d):
                if not fname.lower().endswith(".zip"):
                    continue
                fl = fname.lower()
                if ("anime" in fl or "macro" in fl or "expedition" in fl) and "setup" not in fl:
                    fpath = os.path.join(d, fname)
                    if _is_valid_release_archive(fpath):
                        dir_candidates.append(fpath)
        except OSError:
            pass

        if dir_candidates:
            dir_candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return dir_candidates[0]

    return None


def install_release(dest_dir: str, on_status=None, on_progress=None) -> str:
    """Скачивает и раскладывает сборку в dest_dir. Возвращает тег версии.
    Если рядом с установщиком или в Загрузках уже лежит готовый zip-архив,
    используется он напрямую без повторного скачивания."""
    def say(text):
        if on_status:
            on_status(text)

    os.makedirs(dest_dir, exist_ok=True)
    tag = latest_tag() or ""

    local_zip = find_local_archive()
    if local_zip:
        say(f"Installing from local package ({os.path.basename(local_zip)})…")
        extract_release(local_zip, dest_dir, on_progress=on_progress)
        return tag or "v2.0.0"

    say("Checking for latest release…")
    url = zip_asset_url()

    fd, tmp_zip = tempfile.mkstemp(suffix=".zip", prefix="aem_")
    os.close(fd)
    try:
        say("Downloading package…")
        download(url, tmp_zip, on_progress=on_progress)
        say("Extracting files…")
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


def _create_shortcut_com(link_path: str, target: str, workdir: str = "",
                         icon: str = "", description: str = "") -> bool:
    """Создаёт .lnk напрямую через интерфейсы Windows COM (IShellLinkW, IPersistFile)
    через стандартный ctypes без запуска внешних процессов и без временных файлов.
    Работает во всех версиях Windows, не блокируется ASR/Defender и не зависит
    от системной кодовой страницы ANSI при кириллических путях."""
    try:
        import ctypes
        from ctypes import wintypes

        class _GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8),
            ]
            def __init__(self, d1, d2, d3, d4):
                super().__init__(d1, d2, d3, (wintypes.BYTE * 8)(*d4))

        CLSID_ShellLink = _GUID(0x00021401, 0, 0, (0xC0, 0, 0, 0, 0, 0, 0, 0x46))
        IID_IShellLinkW = _GUID(0x000214F9, 0, 0, (0xC0, 0, 0, 0, 0, 0, 0, 0x46))
        IID_IPersistFile = _GUID(0x0000010B, 0, 0, (0xC0, 0, 0, 0, 0, 0, 0, 0x46))
        CLSCTX_INPROC_SERVER = 1

        class _IShellLinkW(ctypes.Structure):
            _fields_ = [("lpVtbl", ctypes.c_void_p)]

        ole32 = ctypes.oledll.ole32
        ole32.CoInitialize(None)
        try:
            p_sl = ctypes.POINTER(_IShellLinkW)()
            hr = ole32.CoCreateInstance(
                ctypes.byref(CLSID_ShellLink), None, CLSCTX_INPROC_SERVER,
                ctypes.byref(IID_IShellLinkW), ctypes.byref(p_sl)
            )
            if hr != 0 or not p_sl:
                return False

            vtbl = ctypes.cast(p_sl.contents.lpVtbl, ctypes.POINTER(ctypes.c_void_p))

            # IShellLinkW Vtbl indices: 7: SetDescription, 9: SetWorkingDirectory, 17: SetIconLocation, 20: SetPath
            proto_SetPath = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.LPCWSTR)(vtbl[20])
            proto_SetPath(p_sl, target)

            if workdir or os.path.dirname(target):
                proto_SetWorkingDirectory = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.LPCWSTR)(vtbl[9])
                proto_SetWorkingDirectory(p_sl, workdir or os.path.dirname(target))

            if description:
                proto_SetDescription = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.LPCWSTR)(vtbl[7])
                proto_SetDescription(p_sl, description)

            if icon or target:
                proto_SetIconLocation = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.LPCWSTR, ctypes.c_int)(vtbl[17])
                proto_SetIconLocation(p_sl, icon or target, 0)

            # QueryInterface for IPersistFile (index 0)
            p_pf = ctypes.c_void_p()
            proto_QI = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p))(vtbl[0])
            hr_qi = proto_QI(p_sl, ctypes.byref(IID_IPersistFile), ctypes.byref(p_pf))
            if hr_qi == 0 and p_pf.value:
                pf_vtbl = ctypes.cast(p_pf, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))
                # IPersistFile::Save is index 6
                proto_Save = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.LPCWSTR, wintypes.BOOL)(pf_vtbl.contents[6])
                proto_Save(p_pf, link_path, True)
                ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(pf_vtbl.contents[2])(p_pf)

            ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(vtbl[2])(p_sl)
        finally:
            ole32.CoUninitialize()
    except Exception:
        pass

    return os.path.isfile(link_path)


def create_shortcut(link_path: str, target: str, workdir: str = "",
                    icon: str = "", description: str = "") -> bool:
    """Создаёт .lnk. Возвращает True, если файл появился.

    Неудача здесь НЕ должна валить установку: приложение уже разложено и
    работает, отсутствие ярлыка — неудобство, а не поломка."""
    link_dir = os.path.dirname(os.path.abspath(link_path))
    os.makedirs(link_dir, exist_ok=True)

    # 1. Быстрый и прямой способ через in-process Windows COM (ctypes)
    try:
        if _create_shortcut_com(link_path, target, workdir, icon, description):
            return True
    except Exception:
        pass

    # 2. Попытка через VBScript + cscript (нативно для Windows)
    script = _VBS.format(
        link=_vbs_str(link_path),
        target=_vbs_str(target),
        workdir=_vbs_str(workdir or os.path.dirname(target)),
        icon=_vbs_str(icon or target),
        desc=_vbs_str(description or APP_NAME),
    )
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
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
            val, _ = winreg.QueryValueEx(k, "Desktop")
            if val:
                expanded = os.path.expandvars(val)
                if os.path.isdir(expanded):
                    return expanded
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Desktop")


def start_menu_dir() -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
            val, _ = winreg.QueryValueEx(k, "Programs")
            if val:
                expanded = os.path.expandvars(val)
                if os.path.isdir(expanded):
                    return expanded
    except Exception:
        pass
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
