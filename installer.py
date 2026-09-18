"""Установщик Anime Expeditions Macro: выбор папки, ярлыки, удаление.

ЗАЧЕМ ОН НУЖЕН. bootstrap.py ставит приложение РЯДОМ С СОБОЙ: запустил из
«Загрузок» — оно там и живёт, вперемешку со всем, что человек когда-либо
скачивал. Обновиться оно потом сможет, а вот найти его, сделать ярлык или
удалить — уже забота пользователя. Этот установщик закрывает всё три:
кладёт приложение в понятное место, заводит ярлыки и регистрируется в
«Установка и удаление программ», откуда его можно снести как любую программу.

ИНТЕРФЕЙС НА TKINTER, а не на pywebview, которым сделан сам макрос. pywebview
тянет за собой WebView2 и вес, сопоставимый с приложением; tkinter входит в
стандартную библиотеку, и установщик остаётся маленьким — таким, какой не
жалко скинуть в Discord. Для четырёх полей и полосы прогресса этого хватает
с запасом.

РЕЖИМЫ:
    installer.exe               обычная установка
    installer.exe --uninstall   удаление (так его зовёт Windows)

ПРАВА АДМИНИСТРАТОРА НЕ ТРЕБУЮТСЯ и требоваться не должны — почему именно,
расписано у default_install_dir в installer_lib.py.
"""
import ctypes
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import installer_lib as lib

# --------------------------------------------------------------- ЦВЕТОВАЯ ПАЛИТРА -
# Cyber-Glass Onyx (тёмный графит, неоновый фиолетовый акцент, мягкие границы).
# Все контрасты выверены по WCAG AA/AAA для отличной читаемости на любом мониторе.
BG = "#0c0d14"              # Основной фон окна
HEADER_BG = "#10121d"       # Фон шапки
CARD_BG = "#131624"         # Фон стеклянной карточки
CARD_BORDER = "#23283c"     # Тонкая граница карточки
INPUT_BG = "#191c2e"        # Фон поля ввода
INPUT_BORDER = "#2f3652"    # Рамка поля ввода
INPUT_BORDER_FOCUS = "#7c6cf0" # Рамка при фокусе

TEXT_HEAD = "#ffffff"       # Заголовки
TEXT_MAIN = "#e3e6f3"       # Основной текст
TEXT_MUTED = "#868da4"      # Приглушённый текст / подписи
TEXT_DIM = "#5e647b"        # Второстепенный текст

ACCENT = "#7c6cf0"          # Неоновый фиолетовый акцент
ACCENT_HOVER = "#8f80fa"    # Акцент при наведении
ACCENT_ACTIVE = "#6b5be2"   # Акцент при нажатии
ACCENT_FG = "#ffffff"       # Текст на акцентной кнопке

BUTTON_SEC_BG = "#1e2236"   # Второстепенная кнопка
BUTTON_SEC_HOVER = "#2a304a"
BUTTON_SEC_BORDER = "#333b5c"
BUTTON_SEC_FG = "#ccd2e5"

BADGE_BG = "#221c3e"        # Подложка бейджа версии
BADGE_BORDER = "#493b82"
BADGE_FG = "#b8abff"

SUCCESS_COLOR = "#4ade80"   # Зелёный статус
ERROR_COLOR = "#f87171"     # Красный статус


def enable_dpi_awareness():
    """Включает попиксельную чёткость на мониторах с масштабированием (125%, 150%, 200%).
    Без этого Tkinter мылит шрифты и растягивает пиксели."""
    try:
        # Per-monitor DPI aware v2 (Windows 10 1703+)
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            # Per-monitor DPI aware (Windows 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def set_dark_titlebar(root):
    """Окрашивает стандартную белую рамку окна Windows 10/11 в тёмный цвет.
    Использует DWMWA_USE_IMMERSIVE_DARK_MODE."""
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if not hwnd:
            hwnd = root.winfo_id()
        for attr in (20, 19):  # 20 для Win11/Win10 20H1+, 19 для Win10 1809
            val = ctypes.c_int(1)
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)
            )
            if res == 0:
                break
    except Exception:
        pass


# ------------------------------------------------------------------- ЛОГИКА -
def resolve_install_target(chosen: str) -> str:
    """Выбранная в диалоге папка — это РОДИТЕЛЬ, внутри неё заводится своя.

    Выбрал «D:\\Игры» — ставим в «D:\\Игры\\Anime Expeditions Macro», а не
    вываливаем exe, Assets, Paths и Templates прямо в «D:\\Игры» вперемешку со
    всем, что там уже лежит. Своя папка нужна и для удаления: каталог сносится
    целиком, не разбирая, что в нём чьё.

    Если выбранная папка УЖЕ называется как приложение (ткнул в существующую
    установку), имя второй раз не дописываем — иначе выйдет
    «…\\Anime Expeditions Macro\\Anime Expeditions Macro»."""
    chosen = os.path.normpath(chosen.strip())
    if os.path.basename(chosen).lower() == lib.APP_NAME.lower():
        return chosen
    return os.path.join(chosen, lib.APP_NAME)


def do_install(target_dir: str, desktop: bool, start_menu: bool,
               on_status, on_progress) -> str:
    """Ставит приложение и возвращает установленную версию.

    Порядок намеренный: сначала файлы, потом ярлыки, потом запись в реестр.
    Ярлык на ещё не скачанное приложение вёл бы в пустоту, а строка в списке
    установленных программ, за которой ничего нет, — худшее из трёх."""
    version = lib.install_release(target_dir, on_status=on_status,
                                  on_progress=on_progress)
    exe = lib.app_exe_path(target_dir)

    on_status("Создаю ярлыки…")
    if desktop:
        lib.create_shortcut(
            os.path.join(lib.desktop_dir(), f"{lib.APP_NAME}.lnk"), exe, target_dir)
    if start_menu:
        lib.create_shortcut(
            os.path.join(lib.start_menu_dir(), f"{lib.APP_NAME}.lnk"), exe, target_dir)

    # Копия установщика кладётся рядом с приложением: именно её потом
    # запускает Windows при удалении. Без копии UninstallString указывал бы на
    # файл в «Загрузках», который человек давно стёр, и кнопка «Удалить» в
    # списке программ просто не работала бы.
    on_status("Регистрирую в списке программ…")
    uninstaller = os.path.join(target_dir, "uninstall.exe")
    placed = False
    me = os.path.abspath(sys.argv[0])
    # .exe — потому что при запуске из исходников sys.argv[0] это
    # installer.py, и копировать скрипт под именем uninstall.exe бессмысленно:
    # Windows его не запустит.
    if me.lower().endswith(".exe") and lib.is_inside(target_dir, uninstaller):
        try:
            shutil.copy2(me, uninstaller)
            placed = True
        except OSError:
            placed = False

    # Запись делается ТОЛЬКО с рабочим деинсталлятором. Строка в «Установка и
    # удаление программ», у которой кнопка «Удалить» ведёт в никуда, хуже, чем
    # отсутствие строки: человек нажимает, ничего не происходит, и починить он
    # это не может. При запуске из исходников (разработка) сюда и не доходим.
    if placed:
        lib.register_uninstall(target_dir, version, uninstaller)
    return version


def do_uninstall(install_dir: str, keep_user_data: bool, on_status) -> None:
    """Снимает ярлыки, запись в реестре и файлы приложения.

    Собственный exe удалить нельзя, пока он запущен, поэтому uninstall.exe
    остаётся и стирается отложенной командой уже после выхода."""
    on_status("Убираю ярлыки…")
    for path in (os.path.join(lib.desktop_dir(), f"{lib.APP_NAME}.lnk"),
                 os.path.join(lib.start_menu_dir(), f"{lib.APP_NAME}.lnk")):
        try:
            os.remove(path)
        except OSError:
            pass

    on_status("Удаляю файлы…")
    me = os.path.abspath(sys.argv[0])
    for entry in lib.removable_entries(install_dir, keep_user_data):
        if os.path.abspath(entry).lower() == me.lower():
            continue  # себя удалим после выхода
        try:
            if os.path.isdir(entry):
                shutil.rmtree(entry, ignore_errors=True)
            else:
                os.remove(entry)
        except OSError:
            pass

    lib.unregister_uninstall()

    # Отложенное самоудаление: ждём пару секунд, чтобы процесс успел выйти и
    # отпустить файл, и убираем uninstall.exe, а следом пустую папку. Если в
    # ней остались данные пользователя (keep_user_data), rmdir не сработает и
    # папка останется — это правильно, там его файлы.
    if me.lower().endswith(".exe") and lib.is_inside(install_dir, me):
        try:
            subprocess.Popen(
                ["cmd", "/c", "ping -n 3 127.0.0.1 >nul & "
                 f'del /f /q "{me}" & rmdir "{install_dir}"'],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError:
            pass


# --------------------------------------------------------------- ИНТЕРФЕЙС -
class InstallerWindow:
    def __init__(self, root, uninstall_mode: bool):
        self.root = root
        self.uninstall_mode = uninstall_mode
        self.busy = False
        self.installed_version = "v2.0.0"
        self.target_installed_dir = ""

        mode_title = "Удаление" if uninstall_mode else "Установка"
        root.title(f"{lib.APP_NAME} • {mode_title}")
        root.configure(bg=BG)
        root.resizable(False, False)

        # Центрируем окно на экране
        width, height = 540, 530
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 2 - 20)
        root.geometry(f"{width}x{height}+{x}+{y}")

        # Иконка приложения
        try:
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            ico = os.path.join(base_dir, "logo.ico")
            if os.path.isfile(ico):
                root.iconbitmap(ico)
        except Exception:
            pass

        self.main_container = tk.Frame(root, bg=BG)
        self.main_container.pack(fill="both", expand=True)

        self._build_header()
        self._build_config_view()

        root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_header(self):
        """Верхняя брендовая плашка в стиле Cyber-Glass."""
        header_frame = tk.Frame(self.main_container, bg=HEADER_BG, height=82)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        top_box = tk.Frame(header_frame, bg=HEADER_BG)
        top_box.pack(fill="both", expand=True, padx=22, pady=14)

        # Иконка-эмблема
        icon_canvas = tk.Canvas(top_box, width=44, height=44, bg=HEADER_BG,
                                highlightthickness=0)
        icon_canvas.pack(side="left", padx=(0, 14))

        icon_canvas.create_polygon(22, 2, 42, 22, 22, 42, 2, 22,
                                   fill="#1c1f33", outline=ACCENT, width=2)
        icon_canvas.create_text(22, 22, text="AE", fill="#ffffff",
                                font=("Segoe UI Variable Display", 11, "bold"))

        text_box = tk.Frame(top_box, bg=HEADER_BG)
        text_box.pack(side="left", fill="y", expand=True)

        title_row = tk.Frame(text_box, bg=HEADER_BG)
        title_row.pack(anchor="w")

        title_lbl = tk.Label(title_row, text=lib.APP_NAME.upper(),
                             font=("Segoe UI Variable Display", 12, "bold"),
                             fg=TEXT_HEAD, bg=HEADER_BG)
        title_lbl.pack(side="left")

        badge_text = "UNINSTALL" if self.uninstall_mode else "v2.0.0"
        badge_lbl = tk.Label(title_row, text=f" {badge_text} ",
                             font=("Segoe UI Variable Text", 8, "bold"),
                             fg=BADGE_FG, bg=BADGE_BG,
                             relief="solid", bd=1)
        badge_lbl.configure(highlightbackground=BADGE_BORDER, highlightthickness=1)
        badge_lbl.pack(side="left", padx=(10, 0))

        sub_text = ("Деинсталляция компонентов приложения и ярлыков"
                    if self.uninstall_mode
                    else "Cyber-Glass Edition • Автоматическая установка и настройка")
        sub_lbl = tk.Label(text_box, text=sub_text,
                           font=("Segoe UI Variable Text", 9),
                           fg=TEXT_MUTED, bg=HEADER_BG)
        sub_lbl.pack(anchor="w", pady=(3, 0))

        sep = tk.Frame(self.main_container, bg=CARD_BORDER, height=1)
        sep.pack(fill="x", side="top")

    def _build_config_view(self):
        """Основной экран параметров установки/удаления."""
        self.view_frame = tk.Frame(self.main_container, bg=BG)
        self.view_frame.pack(fill="both", expand=True, padx=20, pady=16)

        # ── КАРТОЧКА 1: Папка назначения ──
        path_card = tk.Frame(self.view_frame, bg=CARD_BG,
                             highlightbackground=CARD_BORDER, highlightthickness=1)
        path_card.pack(fill="x", pady=(0, 14))

        p_inner = tk.Frame(path_card, bg=CARD_BG)
        p_inner.pack(fill="x", padx=16, pady=14)

        p_head = tk.Label(p_inner, text="ПАПКА УСТАНОВКИ",
                          font=("Segoe UI Variable Text", 8, "bold"),
                          fg=TEXT_MUTED, bg=CARD_BG)
        p_head.pack(anchor="w", pady=(0, 8))

        row_box = tk.Frame(p_inner, bg=CARD_BG)
        row_box.pack(fill="x")

        self.path_var = tk.StringVar(
            value=lib.read_install_dir() or lib.default_install_dir())

        self.entry = tk.Entry(row_box, textvariable=self.path_var,
                              font=("Segoe UI Variable Text", 9),
                              bg=INPUT_BG, fg=TEXT_MAIN,
                              insertbackground=TEXT_HEAD,
                              relief="solid", bd=1,
                              highlightthickness=1,
                              highlightbackground=INPUT_BORDER,
                              highlightcolor=INPUT_BORDER_FOCUS)
        self.entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        self.browse_btn = tk.Button(row_box, text="Обзор…",
                                    font=("Segoe UI Variable Text", 9),
                                    bg=BUTTON_SEC_BG, fg=BUTTON_SEC_FG,
                                    activebackground=BUTTON_SEC_HOVER,
                                    activeforeground=TEXT_HEAD,
                                    relief="solid", bd=1,
                                    highlightthickness=1,
                                    highlightbackground=BUTTON_SEC_BORDER,
                                    cursor="hand2", padx=12, ipady=4,
                                    command=self.pick_folder)
        self.browse_btn.pack(side="right")

        info_text = ("Текущая директория установки приложения."
                     if self.uninstall_mode
                     else "✓ Права администратора не требуются  •  Установка в профиль пользователя")
        p_hint = tk.Label(p_inner, text=info_text,
                          font=("Segoe UI Variable Text", 8),
                          fg=TEXT_DIM, bg=CARD_BG)
        p_hint.pack(anchor="w", pady=(8, 0))

        # ── КАРТОЧКА 2: Опции / Ярлыки ──
        opts_card = tk.Frame(self.view_frame, bg=CARD_BG,
                             highlightbackground=CARD_BORDER, highlightthickness=1)
        opts_card.pack(fill="x", pady=(0, 14))

        o_inner = tk.Frame(opts_card, bg=CARD_BG)
        o_inner.pack(fill="x", padx=16, pady=14)

        o_head = tk.Label(o_inner, text="ПАРАМЕТРЫ",
                          font=("Segoe UI Variable Text", 8, "bold"),
                          fg=TEXT_MUTED, bg=CARD_BG)
        o_head.pack(anchor="w", pady=(0, 10))

        self.desktop_var = tk.BooleanVar(value=True)
        self.startmenu_var = tk.BooleanVar(value=True)
        self.launch_var = tk.BooleanVar(value=True)
        self.keepdata_var = tk.BooleanVar(value=True)

        if self.uninstall_mode:
            self.entry.config(state="disabled")
            self.browse_btn.config(state="disabled")
            self._add_check(o_inner, self.keepdata_var,
                            "Сохранить настройки, шаблоны и эталоны (рекомендуется)")
            warn_lbl = tk.Label(o_inner,
                                text="Если снять эту галочку, папка будет удалена полностью со всеми вашими записями.",
                                font=("Segoe UI Variable Text", 8),
                                fg=ERROR_COLOR, bg=CARD_BG, wraplength=460, justify="left")
            warn_lbl.pack(anchor="w", padx=26, pady=(3, 0))
        else:
            self._add_check(o_inner, self.desktop_var, "Создать ярлык на рабочем столе")
            self._add_check(o_inner, self.startmenu_var, "Добавить ярлык в меню «Пуск»")
            self._add_check(o_inner, self.launch_var, "Запустить Anime Expeditions Macro сразу после установки")

        # ── БЛОК ПРОГРЕССА И СТАТУСА ──
        self.progress_box = tk.Frame(self.view_frame, bg=BG)
        self.progress_box.pack(fill="x", pady=(0, 12))

        self.bar = ttk.Progressbar(self.progress_box, length=490, mode="determinate")
        self.bar.pack(fill="x", pady=(0, 6))

        init_status = ("Нажмите «Установить» для начала загрузки и распаковки."
                       if not self.uninstall_mode
                       else "Нажмите «Удалить» для деинсталляции.")
        self.status_lbl = tk.Label(self.progress_box, text=init_status,
                                   font=("Segoe UI Variable Text", 8),
                                   fg=TEXT_MUTED, bg=BG)
        self.status_lbl.pack(anchor="w")

        # ── ПОДВАЛ С КНОПКАМИ ДЕЙСТВИЯ ──
        self.footer = tk.Frame(self.view_frame, bg=BG)
        self.footer.pack(fill="x", side="bottom")

        btn_text = "Удалить" if self.uninstall_mode else "Установить"
        btn_bg = ERROR_COLOR if self.uninstall_mode else ACCENT
        btn_hover = "#ef4444" if self.uninstall_mode else ACCENT_HOVER

        self.go_btn = tk.Button(self.footer, text=btn_text,
                                font=("Segoe UI Variable Text", 9, "bold"),
                                bg=btn_bg, fg=ACCENT_FG,
                                activebackground=btn_hover,
                                activeforeground=ACCENT_FG,
                                relief="flat", bd=0,
                                cursor="hand2", padx=24, ipady=8,
                                command=self.start)
        self.go_btn.pack(side="right")

        self.cancel_btn = tk.Button(self.footer, text="Отмена",
                                    font=("Segoe UI Variable Text", 9),
                                    bg=BUTTON_SEC_BG, fg=BUTTON_SEC_FG,
                                    activebackground=BUTTON_SEC_HOVER,
                                    activeforeground=TEXT_HEAD,
                                    relief="solid", bd=1,
                                    highlightthickness=1,
                                    highlightbackground=BUTTON_SEC_BORDER,
                                    cursor="hand2", padx=18, ipady=7,
                                    command=self.close)
        self.cancel_btn.pack(side="right", padx=(0, 10))

    def _add_check(self, parent, var, text):
        """Создает стилизованный чекбокс в стиле Cyber-Glass."""
        chk = tk.Checkbutton(parent, text=text, variable=var,
                             font=("Segoe UI Variable Text", 9),
                             fg=TEXT_MAIN, bg=CARD_BG,
                             activebackground=CARD_BG,
                             activeforeground=TEXT_HEAD,
                             selectcolor=INPUT_BG,
                             cursor="hand2", bd=0, highlightthickness=0)
        chk.pack(anchor="w", pady=3)
        return chk

    def pick_folder(self):
        chosen = filedialog.askdirectory(title="Куда поставить Anime Expeditions Macro")
        if chosen:
            self.path_var.set(resolve_install_target(chosen))

    def close(self):
        if self.busy:
            return
        self.root.destroy()

    def say(self, text):
        self.root.after(0, lambda: self.status_lbl.config(text=text, fg=TEXT_MUTED))

    def progress(self, done, total):
        def apply():
            if total:
                self.bar.config(mode="determinate", maximum=total, value=done)
                pct = int((done / total) * 100)
                mb_done = done / 1048576
                mb_total = total / 1048576
                self.status_lbl.config(
                    text=f"Скачивание… {mb_done:.1f} из {mb_total:.1f} МБ ({pct}%)",
                    fg=TEXT_MAIN)
            else:
                self.bar.config(mode="indeterminate")
                self.bar.start(12)
                mb_done = done / 1048576
                self.status_lbl.config(
                    text=f"Скачивание… {mb_done:.1f} МБ", fg=TEXT_MAIN)
        self.root.after(0, apply)

    def set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for w in (self.go_btn, self.cancel_btn, self.browse_btn, self.entry):
            try:
                w.config(state=state)
            except Exception:
                pass

    def start(self):
        target = os.path.normpath(self.path_var.get().strip())
        if not target:
            self.say("Пожалуйста, укажите папку для установки.")
            return
        if self.uninstall_mode and not os.path.isdir(target):
            self.say(f"Папка не найдена: {target}")
            return

        self.set_busy(True)
        threading.Thread(target=self._work, args=(target,), daemon=True).start()

    def _work(self, target):
        try:
            if self.uninstall_mode:
                do_uninstall(target, self.keepdata_var.get(), self.say)
                self.root.after(0, self._done_uninstall)
            else:
                version = do_install(target, self.desktop_var.get(),
                                     self.startmenu_var.get(), self.say, self.progress)
                self.root.after(0, lambda: self._done_install(target, version))
        except Exception as exc:
            self.root.after(0, lambda e=exc: self._failed(e))

    def _done_install(self, target, version):
        """Отображает стильный экран завершения установки прямо в окне (без нативных попапов)."""
        self.bar.stop()
        self.bar.config(mode="determinate", maximum=1, value=1)
        self.busy = False
        self.installed_version = version or "v2.0.0"
        self.target_installed_dir = target

        self.view_frame.destroy()

        done_frame = tk.Frame(self.main_container, bg=BG)
        done_frame.pack(fill="both", expand=True, padx=24, pady=24)

        icon_box = tk.Canvas(done_frame, width=54, height=54, bg=BG, highlightthickness=0)
        icon_box.pack(pady=(16, 12))
        icon_box.create_oval(3, 3, 51, 51, fill="#122a1e", outline=SUCCESS_COLOR, width=2)
        icon_box.create_text(27, 27, text="✓", fill=SUCCESS_COLOR,
                             font=("Segoe UI Variable Display", 20, "bold"))

        h1 = tk.Label(done_frame, text="Установка успешно завершена!",
                      font=("Segoe UI Variable Display", 14, "bold"),
                      fg=TEXT_HEAD, bg=BG)
        h1.pack(pady=(0, 6))

        h2 = tk.Label(done_frame,
                      text=f"{lib.APP_NAME} {self.installed_version} готов к использованию.",
                      font=("Segoe UI Variable Text", 10),
                      fg=TEXT_MUTED, bg=BG)
        h2.pack(pady=(0, 20))

        res_card = tk.Frame(done_frame, bg=CARD_BG,
                            highlightbackground=CARD_BORDER, highlightthickness=1)
        res_card.pack(fill="x", pady=(0, 24))

        rc_inner = tk.Frame(res_card, bg=CARD_BG)
        rc_inner.pack(fill="x", padx=16, pady=12)

        rc_lbl = tk.Label(rc_inner, text="РАСПОЛОЖЕНИЕ ПРИЛОЖЕНИЯ",
                          font=("Segoe UI Variable Text", 8, "bold"),
                          fg=TEXT_MUTED, bg=CARD_BG)
        rc_lbl.pack(anchor="w", pady=(0, 4))

        rc_path = tk.Label(rc_inner, text=target,
                           font=("Consolas", 9),
                           fg=TEXT_MAIN, bg=CARD_BG, wraplength=450, justify="left")
        rc_path.pack(anchor="w")

        btn_box = tk.Frame(done_frame, bg=BG)
        btn_box.pack(fill="x", side="bottom")

        launch_btn = tk.Button(btn_box, text="Запустить сейчас",
                               font=("Segoe UI Variable Text", 9, "bold"),
                               bg=ACCENT, fg=ACCENT_FG,
                               activebackground=ACCENT_HOVER,
                               activeforeground=ACCENT_FG,
                               relief="flat", bd=0,
                               cursor="hand2", padx=22, ipady=8,
                               command=self._launch_and_exit)
        launch_btn.pack(side="right")

        close_btn = tk.Button(btn_box, text="Закрыть",
                              font=("Segoe UI Variable Text", 9),
                              bg=BUTTON_SEC_BG, fg=BUTTON_SEC_FG,
                              activebackground=BUTTON_SEC_HOVER,
                              activeforeground=TEXT_HEAD,
                              relief="solid", bd=1,
                              highlightthickness=1,
                              highlightbackground=BUTTON_SEC_BORDER,
                              cursor="hand2", padx=18, ipady=7,
                              command=self.root.destroy)
        close_btn.pack(side="right", padx=(0, 10))

        if self.launch_var.get():
            self._launch_app(target)

    def _done_uninstall(self):
        """Отображает стильный экран завершения деинсталляции."""
        self.bar.stop()
        self.busy = False

        self.view_frame.destroy()

        done_frame = tk.Frame(self.main_container, bg=BG)
        done_frame.pack(fill="both", expand=True, padx=24, pady=36)

        icon_box = tk.Canvas(done_frame, width=54, height=54, bg=BG, highlightthickness=0)
        icon_box.pack(pady=(16, 12))
        icon_box.create_oval(3, 3, 51, 51, fill="#122a1e", outline=SUCCESS_COLOR, width=2)
        icon_box.create_text(27, 27, text="✓", fill=SUCCESS_COLOR,
                             font=("Segoe UI Variable Display", 20, "bold"))

        h1 = tk.Label(done_frame, text=f"{lib.APP_NAME} успешно удалён",
                      font=("Segoe UI Variable Display", 14, "bold"),
                      fg=TEXT_HEAD, bg=BG)
        h1.pack(pady=(0, 6))

        h2 = tk.Label(done_frame,
                      text="Все ярлыки и регистрационные данные удалены из системы.",
                      font=("Segoe UI Variable Text", 10),
                      fg=TEXT_MUTED, bg=BG)
        h2.pack(pady=(0, 30))

        close_btn = tk.Button(done_frame, text="Закрыть",
                              font=("Segoe UI Variable Text", 9, "bold"),
                              bg=BUTTON_SEC_BG, fg=BUTTON_SEC_FG,
                              activebackground=BUTTON_SEC_HOVER,
                              activeforeground=TEXT_HEAD,
                              relief="solid", bd=1,
                              highlightthickness=1,
                              highlightbackground=BUTTON_SEC_BORDER,
                              cursor="hand2", padx=28, ipady=8,
                              command=self.root.destroy)
        close_btn.pack()

    def _failed(self, exc):
        """Отображает ошибку установки с подсказкой и возможностью повторить."""
        self.bar.stop()
        self.set_busy(False)
        self.status_lbl.config(text=f"Ошибка: {exc}", fg=ERROR_COLOR)

        messagebox.showerror(
            lib.APP_NAME,
            f"{'Удаление' if self.uninstall_mode else 'Установка'} не удалась:\n\n{exc}\n\n"
            "Проверьте подключение к интернету или права доступа к выбранной папке."
        )

    def _launch_and_exit(self):
        self._launch_app(self.target_installed_dir)
        self.root.destroy()

    def _launch_app(self, target_dir):
        exe = lib.app_exe_path(target_dir)
        try:
            subprocess.Popen([exe], cwd=target_dir)
        except OSError:
            pass


# --------------------------------------------------------------- ОФОРМЛЕНИЕ -
def apply_theme(root):
    """Настраивает визуальные стили ttk под тему Cyber-Glass."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG, foreground=TEXT_MAIN,
                    font=("Segoe UI Variable Text", 9), borderwidth=0)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT_MAIN)

    style.configure("Horizontal.TProgressbar",
                    background=ACCENT,
                    troughcolor=INPUT_BG,
                    bordercolor=CARD_BORDER,
                    lightcolor=ACCENT,
                    darkcolor=ACCENT,
                    thickness=8)


def main():
    enable_dpi_awareness()
    uninstall = "--uninstall" in sys.argv[1:]
    root = tk.Tk()
    set_dark_titlebar(root)
    apply_theme(root)
    InstallerWindow(root, uninstall)
    root.mainloop()


if __name__ == "__main__":
    main()
