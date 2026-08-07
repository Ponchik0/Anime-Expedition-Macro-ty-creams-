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
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import installer_lib as lib


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
        root.title(f"{lib.APP_NAME} — {'удаление' if uninstall_mode else 'установка'}")
        root.resizable(False, False)

        frame = ttk.Frame(root, padding=16)
        frame.grid(sticky="nsew")

        ttk.Label(frame, text=lib.APP_NAME,
                  style="Head.TLabel").grid(columnspan=3, sticky="w")
        self.subtitle = ttk.Label(frame, style="Dim.TLabel", text=(
            "Удаление приложения и его ярлыков." if uninstall_mode
            else "Куда поставить и что создать. Права администратора не нужны."
        ))
        self.subtitle.grid(columnspan=3, sticky="w", pady=(2, 14))

        # Повторный запуск предлагает ТУ ЖЕ папку, что и прошлая установка —
        # иначе рядом молча появилась бы вторая копия.
        self.path_var = tk.StringVar(
            value=lib.read_install_dir() or lib.default_install_dir())

        ttk.Label(frame, text="Папка:").grid(row=2, column=0, sticky="w")
        entry = ttk.Entry(frame, textvariable=self.path_var, width=46)
        entry.grid(row=2, column=1, sticky="we", padx=(8, 6))
        self.browse_btn = ttk.Button(frame, text="Обзор…", command=self.pick_folder)
        self.browse_btn.grid(row=2, column=2)

        self.desktop_var = tk.BooleanVar(value=True)
        self.startmenu_var = tk.BooleanVar(value=True)
        self.launch_var = tk.BooleanVar(value=True)
        self.keepdata_var = tk.BooleanVar(value=True)

        opts = ttk.Frame(frame)
        opts.grid(row=3, columnspan=3, sticky="w", pady=(12, 0))
        if uninstall_mode:
            entry.state(["disabled"])
            self.browse_btn.state(["disabled"])
            ttk.Checkbutton(opts, variable=self.keepdata_var,
                            text="Сохранить настройки, шаблоны, маршруты и мои эталоны"
                            ).grid(sticky="w")
            ttk.Label(opts, style="Dim.TLabel", wraplength=430, text=(
                "Снимешь галочку — папка будет удалена целиком, вместе с тем, "
                "что ты настраивал руками. Восстановить это неоткуда."
            )).grid(sticky="w", pady=(2, 0))
        else:
            ttk.Checkbutton(opts, variable=self.desktop_var,
                            text="Ярлык на рабочем столе").grid(sticky="w")
            ttk.Checkbutton(opts, variable=self.startmenu_var,
                            text="Ярлык в меню «Пуск»").grid(sticky="w")
            ttk.Checkbutton(opts, variable=self.launch_var,
                            text="Запустить после установки").grid(sticky="w")

        self.bar = ttk.Progressbar(frame, length=430, mode="determinate")
        self.bar.grid(row=4, columnspan=3, sticky="we", pady=(16, 4))
        self.status = ttk.Label(frame, text="", style="Dim.TLabel")
        self.status.grid(row=5, columnspan=3, sticky="w")

        buttons = ttk.Frame(frame)
        buttons.grid(row=6, columnspan=3, sticky="e", pady=(16, 0))
        self.go_btn = ttk.Button(
            buttons, style="Go.TButton",
            text="Удалить" if uninstall_mode else "Установить",
            command=self.start)
        self.go_btn.grid(row=0, column=0, padx=(0, 8))
        self.cancel_btn = ttk.Button(buttons, text="Отмена", command=self.close)
        self.cancel_btn.grid(row=0, column=1)

        frame.columnconfigure(1, weight=1)
        root.protocol("WM_DELETE_WINDOW", self.close)

    # --- вспомогательное ---
    def pick_folder(self):
        chosen = filedialog.askdirectory(title="Куда поставить")
        if chosen:
            self.path_var.set(resolve_install_target(chosen))

    def close(self):
        # Закрыть посреди распаковки значит оставить половину файлов и битую
        # запись в реестре. Пока идёт работа, окно не закрывается.
        if self.busy:
            return
        self.root.destroy()

    def say(self, text):
        self.root.after(0, lambda: self.status.config(text=text))

    def progress(self, done, total):
        def apply():
            if total:
                self.bar.config(mode="determinate", maximum=total, value=done)
                # Мегабайты, а не только полоса. Скачивается 115 МБ, и на
                # медленном канале это минуты: без цифр человек не понимает,
                # идёт ли дело вообще, и закрывает окно на середине.
                self.status.config(
                    text=f"Скачиваю… {done / 1048576:.0f} из {total / 1048576:.0f} МБ")
            else:
                # Сервер не прислал размер — показываем «идёт», а не врём
                # процентами, которых не знаем.
                self.bar.config(mode="indeterminate")
                self.bar.start(12)
                self.status.config(text=f"Скачиваю… {done / 1048576:.0f} МБ")
        self.root.after(0, apply)

    def set_busy(self, busy):
        self.busy = busy
        state = ["disabled"] if busy else ["!disabled"]
        for w in (self.go_btn, self.cancel_btn, self.browse_btn):
            try:
                w.state(state)
            except tk.TclError:
                pass

    # --- запуск ---
    def start(self):
        target = os.path.normpath(self.path_var.get().strip())
        if not target:
            messagebox.showerror(lib.APP_NAME, "Укажи папку.")
            return
        if self.uninstall_mode and not os.path.isdir(target):
            messagebox.showerror(lib.APP_NAME, f"Папка не найдена:\n{target}")
            return
        if self.uninstall_mode and not messagebox.askyesno(
                lib.APP_NAME,
                f"Удалить {lib.APP_NAME} из\n{target}?"
                + ("" if self.keepdata_var.get()
                   else "\n\nНастройки, шаблоны и маршруты будут удалены безвозвратно.")):
            return

        self.set_busy(True)
        # Отдельный поток: в главном крутится tkinter, и скачивание 115 МБ в
        # нём заморозило бы окно намертво — Windows пометила бы его как
        # «не отвечает» ровно тогда, когда всё идёт хорошо.
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
            self.root.after(0, lambda: self._failed(exc))

    def _failed(self, exc):
        self.bar.stop()
        self.set_busy(False)
        self.say("Не получилось.")
        messagebox.showerror(
            lib.APP_NAME,
            f"{'Удаление' if self.uninstall_mode else 'Установка'} не удалась:\n{exc}\n\n"
            "Проверь подключение к интернету и права на папку.")

    def _done_install(self, target, version):
        self.bar.stop()
        self.bar.config(mode="determinate", maximum=1, value=1)
        self.busy = False
        self.say(f"Готово. Установлено в {target}")

        # Сначала сообщение, ПОТОМ запуск. Наоборот было ошибкой: приложение
        # поднимает своё окно поверх, окно установщика уходит под него вместе
        # с ещё не показанным messagebox, и человек видит, что установщик
        # «завис», хотя всё уже готово.
        messagebox.showinfo(
            lib.APP_NAME,
            f"{lib.APP_NAME} {version} установлен.\n\n{target}")

        if self.launch_var.get():
            exe = lib.app_exe_path(target)
            try:
                # cwd обязателен: приложение ищет Assets рядом с собой, и
                # запуск с чужой рабочей папкой оставил бы его без картинок.
                subprocess.Popen([exe], cwd=target)
            except OSError as exc:
                # Молча проглатывать нельзя: галочка стояла, человек ждёт
                # запуска, а вместо него тишина и непонятно, установилось ли.
                messagebox.showwarning(
                    lib.APP_NAME,
                    f"Установлено, но запустить не получилось:\n{exc}\n\n"
                    f"Запусти вручную:\n{exe}")
        self.root.destroy()

    def _done_uninstall(self):
        self.bar.stop()
        self.busy = False
        messagebox.showinfo(lib.APP_NAME, f"{lib.APP_NAME} удалён.")
        self.root.destroy()


# --------------------------------------------------------------- ОФОРМЛЕНИЕ -
# ЧИСТО НЕЙТРАЛЬНАЯ ШКАЛА: ни одного цветного оттенка, только серые.
# Установщик видят один раз, часто на чужом мониторе с непонятной калибровкой,
# и цветной акцент здесь ничего не сообщает — он только украшает. Роль
# «главного» берёт на себя светлота: самая светлая заливка в окне ровно одна,
# у кнопки «Установить».
#
# КОНТРАСТ ПОСЧИТАН, А НЕ ПОДОБРАН НА ГЛАЗ (WCAG 2.1, отношение яркостей):
#   текст на фоне        17.68:1     приглушённый на фоне      7.04:1
#   текст на карточке    16.16:1     приглушённый на карточке  6.43:1
#   второстепенный       11.35:1     текст в поле ввода       13.87:1
#   текст на кнопке      16.91:1     граница на всех трёх    3.00-3.83:1
# Нормы: 4.5:1 для текста, 3:1 для границ и прочих нетекстовых элементов.
#
# Граница светлее, чем «красиво»: #6d6d6d — минимальное значение, которое
# держит 3:1 на ВСЕХ трёх подложках сразу, включая самую светлую (поле ввода).
# Более тёмная выглядела бы аккуратнее и пропадала бы на плохом мониторе, а
# рамка поля ввода — это единственное, что показывает, куда можно печатать.
BG        = "#0a0a0a"   # окно
BG_CARD   = "#161616"   # кнопки, приподнятые поверхности
BG_FIELD  = "#242424"   # поле ввода, вдавленное
BORDER    = "#6d6d6d"   # границы и рамка фокуса
INK       = "#f2f2f2"   # основной текст
INK_DIM   = "#c4c4c4"   # второстепенный
INK_MUTED = "#9a9a9a"   # подписи
ACCENT    = "#ededed"   # заливка главной кнопки (текст на ней — BG)


def apply_theme(root):
    """Тёмная тема поверх ttk.

    Берём 'clam', а не родную 'vista': vista рисует контролы средствами
    Windows и попросту игнорирует заданные цвета — получилось бы тёмное окно
    со светлыми серыми кнопками посередине. clam рисует сам и слушается.
    """
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        return  # чужая система без clam — оставляем как есть, лишь бы работало

    root.configure(bg=BG)
    style.configure(".", background=BG, foreground=INK,
                    font=("Segoe UI", 9), borderwidth=0)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=INK)
    style.configure("Dim.TLabel", foreground=INK_MUTED)
    style.configure("Head.TLabel", foreground=INK, font=("Segoe UI", 14, "bold"))

    style.configure("TEntry", fieldbackground=BG_FIELD, foreground=INK,
                    insertcolor=INK, bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, padding=5)
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure("TButton", background=BG_CARD, foreground=INK_DIM,
                    bordercolor=BORDER, lightcolor=BG_CARD, darkcolor=BG_CARD,
                    padding=(12, 6), relief="flat")
    style.map("TButton",
              background=[("active", BG_FIELD), ("disabled", BG)],
              foreground=[("active", INK), ("disabled", "#6d6d6d")])

    # Главная кнопка — единственная акцентная во всём окне. Второй акцент
    # рядом означал бы «оба главные», то есть ни одного.
    style.configure("Go.TButton", background=ACCENT, foreground=BG,
                    lightcolor=ACCENT, darkcolor=ACCENT, bordercolor=ACCENT,
                    font=("Segoe UI", 9, "bold"))
    style.map("Go.TButton",
              background=[("active", "#ffffff"), ("disabled", BG_CARD)],
              foreground=[("disabled", "#6d6d6d")])

    style.configure("TCheckbutton", background=BG, foreground=INK_DIM,
                    indicatorbackground=BG_FIELD, indicatorforeground=ACCENT,
                    focuscolor=BG)
    style.map("TCheckbutton",
              foreground=[("active", INK)],
              indicatorbackground=[("selected", ACCENT), ("active", BG_FIELD)])

    style.configure("Horizontal.TProgressbar", background=ACCENT,
                    troughcolor=BG_FIELD, bordercolor=BG_FIELD,
                    lightcolor=ACCENT, darkcolor=ACCENT, thickness=6)


def main():
    uninstall = "--uninstall" in sys.argv[1:]
    root = tk.Tk()
    apply_theme(root)
    InstallerWindow(root, uninstall)
    root.mainloop()


if __name__ == "__main__":
    main()
