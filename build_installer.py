"""Сборка exe установщика (см. installer.py) через PyInstaller.

ЗАЧЕМ ОТДЕЛЬНАЯ СБОРКА. Установщик обязан быть маленьким: его скачивают
первым и часто пересылают друг другу. Поэтому он тянет только tkinter из
стандартной библиотеки и requests — ни OpenCV, ни numpy, ни pywebview, ни
mss, которыми живёт само приложение. Собирать его тем же скриптом, что и
приложение, значило бы получить второй файл на 88 МБ вместо нескольких.

ОДИН ФАЙЛ НА ДВА РЕЖИМА. Отдельного uninstall.exe не собираем: это ТОТ ЖЕ
самый файл, просто запущенный с ключом --uninstall. При установке
installer.py копирует себя в папку приложения под именем uninstall.exe и
прописывает в реестр строку удаления с этим ключом (см. do_install).
Собирать два почти одинаковых exe не только лишняя работа, но и лишний
источник расхождений: обновишь один — забудешь другой.

    py -3.12 -m pip install pyinstaller
    py -3.12 build_installer.py

Итог: dist/Anime Expeditions Macro Setup.exe
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
# Без апострофов и прочего, что PyInstaller пишет прямо в .spec как
# незаэкранированный литерал Python — та же причина, что у EXE_NAME в
# build_pyinstaller.py.
EXE_NAME = "Anime Expeditions Macro Setup"

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    # --windowed: у установщика есть своё окно, и чёрная консоль за ним
    # выглядела бы так, будто что-то пошло не так.
    "--windowed",
    "--noconfirm",
    f"--name={EXE_NAME}",
    f"--icon={os.path.join(ROOT, 'logo.ico')}",
    "--distpath=dist",
    "--workpath=build",
    # installer_lib лежит рядом и подхватится сам, но пусть будет явно:
    # молча потерянный модуль обнаружится только при запуске готового exe.
    "--hidden-import=installer_lib",
    # Тяжёлое приложение сюда попасть не должно. PyInstaller умеет затащить
    # лишнее по цепочке импортов, а установщик, распухший до размеров
    # приложения, теряет весь смысл.
    "--exclude-module=cv2",
    "--exclude-module=numpy",
    "--exclude-module=webview",
    "--exclude-module=mss",
    "--exclude-module=PIL",
    os.path.join(ROOT, "installer.py"),
]

print("Собираю установщик через PyInstaller...")
if subprocess.run(cmd, cwd=ROOT).returncode != 0:
    print("\nСБОРКА НЕ УДАЛАСЬ")
    sys.exit(1)

out = os.path.join(ROOT, "dist", f"{EXE_NAME}.exe")
size = os.path.getsize(out) / 1048576 if os.path.isfile(out) else 0
print(f"\nГотово: dist/{EXE_NAME}.exe ({size:.1f} МБ)")
print("Он же становится uninstall.exe в папке установки — см. installer.do_install.")
