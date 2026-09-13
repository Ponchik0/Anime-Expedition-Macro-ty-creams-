<div align="center">

<img src="logo.ico" width="96" height="96" alt="Anime Expeditions">

# Anime Expeditions

**Auto-farm macro for Anime Expeditions on Roblox**

<p align="center">
  <b>English</b> • <a href="README.ru.md">Русский</a>
</p>

Works via computer vision: captures the screen and detects images.<br>
No process injection, no memory reading.<br>
Roblox docks directly inside the macro window — full farming automation.

<br>

<a href="https://github.com/Ponchik0/ae/releases/latest">
  <img src="https://img.shields.io/github/v/release/Ponchik0/ae?style=for-the-badge&color=c9a227&labelColor=1c1c1c&label=version" alt="Latest Version">
</a>
<a href="https://github.com/Ponchik0/ae/releases">
  <img src="https://img.shields.io/github/downloads/Ponchik0/ae/total?style=for-the-badge&color=c9a227&labelColor=1c1c1c&label=downloads" alt="Downloads">
</a>
<img src="https://img.shields.io/badge/platform-Windows-c9a227?style=for-the-badge&labelColor=1c1c1c" alt="Windows">
<img src="https://img.shields.io/badge/python-3.10+-c9a227?style=for-the-badge&labelColor=1c1c1c" alt="Python 3.10+">
<a href="LICENSE">
  <img src="https://img.shields.io/badge/license-MIT-c9a227?style=for-the-badge&labelColor=1c1c1c" alt="MIT">
</a>

<br><br>

[Features](#features) · [Installation](#installation) · [First Launch](#first-launch) · [Updates](#updates) · [Documentation](#documentation) · [Credits](#credits)

</div>

---

## About

A custom build and feature-rich fork of [Cream's Macro](https://github.com/Cweamy/Anime-Expeditions-Creams-Macro) for Anime Expeditions on Roblox.

**Core engine credit goes to [Cweamy](https://github.com/Cweamy)**: image detection, stage progression, Roblox window docking, OCR, webhooks, and installer packaging were designed by him, with upstream improvements regularly ported over.

**This fork adds**:
- A completely overhauled, clean dark/neutral user interface with bilingual English & Russian support (`ui/i18n.js`).
- Full **Portals mode** automation: lobby inventory entry, continuous chain-farming directly through the chooser without lobby re-entry, and in-round 3-portal offer card selection.
- **In-Game Auto Play** integration: seamless toggle between macro unit placement and native Roblox Auto Play, with camera drag bypass and persistent state preservation across portal runs.
- **Auto Shop Meat**: added Food/Meat auto-purchasing (up to 200 stock) with aligned purchase grids.
- **Action Recorder (Replay Mode)**: TinyTask-style mouse & keyboard recorder/replayer that faithfully preserves in-match wait times using high-precision timers (`time.perf_counter()`).
- **Universal Import & Dynamic Layout**: Accepts any `.json` task/template structure, CREAM share codes, and auto-adapts window layout across any Roblox resolution without button clipping.
- **Fishing & Hotbar Safety**: Multi-rank fishing rod auto-detection (Novice to Grandmaster) and placeable fish unequip protection.
- Auto-reconnect via `roblox://` deep links on disconnects, template verification tool, customizable theme engine, and PDF run reports.

Historical AutoHotkey coordinates, thresholds, and observations are documented in [`docs/from_ahk.md`](docs/from_ahk.md).

## Features

| Feature | Description |
|:--|:--|
| **Docked Roblox Window** | The game embeds directly inside the macro window (`SetParent`). Keystrokes and clicks land accurately even when other windows overlap |
| **Multi-Mode Task Queue** | Story, Expedition, Raid, Tower, Challenge, and Portals. Set map, stage, difficulty, solo/matchmaking, and repeats |
| **Portals Automation** | Opens portals from inventory or chains them directly through the result chooser; picks the middle portal card during matches |
| **In-Game Auto Play** | Let the game play itself when desired — automatically toggles Auto Play and skips unnecessary camera manipulation |
| **Pre Start Builder** | Set up starter units with placement checks, toggle settings via hotkeys, and run "Once" blocks on first repeats only |
| **Action Recorder (Replay)** | F8 starts/stops recording input; F9 opens the recordings overlay. In-match idle time is preserved and accurately replayed |
| **Smart Recovery** | Automatically returns to lobby on stalled matches, failed clicks, or black screens; restarts Roblox on 25m stalls |
| **Discord Notifications** | Result screenshots, generated win/loss status cards, hourly summaries, and PDF reports |
| **Theme Customization** | Six backgrounds, six accent colors, adjustable UI density, and border radius |
| **Custom Templates & Crops** | Missing a specific button crop? Drop your own PNG into `Assets/` without needing to recompile |

<details>
<summary><b>Detailed Automation Features</b> — click to expand</summary>

<br>

- **Embedded Roblox Window**: Game embeds as a native child window. Clicks and inputs stay contained even if you work in another application.
- **Portals Mode**: Full support for Portal farming — opens from inventory, joins lobbies, auto-picks the middle card during the round, and chains into the next portal from the chooser window without extra lobby loads.
- **In-Game Auto Play**: Switch between macro-controlled unit placement and Roblox's built-in Auto Play. Prevents unnecessary camera drags and preserves Auto Play state across portal chains.
- **Task Queue & Repeat Recovery**: Runs a queued sequence of tasks. If a match stalls or a click misses, the macro safely returns to the lobby and restarts rather than breaking an overnight session.
- **Pre Start Unit Placement**: Validates tile availability, retries if a position shifts, adjusts placement offset, and runs one-time setup on the initial repeat.
- **Recorded Movement Paths**: Walk paths recorded on WASD run automatically during Pre Start.
- **Multi-Scale Image Search**: Templates are tested across multiple scale steps, reliably matching even when Windows display scaling differs.
- **Auto Shop**: Automatically sweeps the shop on schedule, buying tickets, traits, and meat.

</details>

<details>
<summary><b>Fork Enhancements</b> — additions created for this build</summary>

<br>

- **Redesigned Interface**: Neutral dark theme, high-contrast palette, dense layout, consistent margins, and responsive hover/focus states.
- **Bilingual Interface**: Seamless EN/RU toggle in the header with persistent language preference. The run log stays in English to avoid breaking unit coordinate parsing.
- **UI Customization**: Six background tones (from OLED black to light dark), six accents, compact/comfortable density, and customizable border radius.
- **Private Server Support**: Deep-link launch directly into your private server without opening extra browser tabs.
- **Action Recorder (Replay Mode)**: TinyTask-style F8/F9 recording. Tracks mouse and keyboard input only while Roblox is active and in focus. Includes full wait time so mid-match idle phases are preserved.
- **Template Checker**: One-click scanner that checks all reference images against your current game screen, highlighting verified, borderline, and missing templates.
- **Task Timers**: Set duration limits on tasks to transition cleanly after the current match ends.
- **Stall & Disconnect Watchdog**: Detects 25-minute stalls or black screens, cleanly relaunches Roblox, and resumes the task queue.
- **Self-Updater**: Checks releases directly against `Ponchik0/ae` and seamlessly updates the executable while preserving custom assets and settings.

</details>

## Requirements

| Requirement | Details |
|:--|:--|
| **Windows 10 or 11** | Primary supported platform |
| **[Roblox](https://www.roblox.com/)** | Anime Expeditions game |
| **Python 3.10+** | For running from source |
| **[WebView2](https://developer.microsoft.com/microsoft-edge/webview2/)** | UI renderer (installed by default on most modern Windows systems) |
| **[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)** / **RapidOCR** | Optional: for reading reward item names and in-depth stats |

## Installation

### From Source

```bash
git clone https://github.com/Ponchik0/ae.git
cd ae
pip install -r requirements.txt
```

Launch:

```bash
python main.py
```

Or double-click `run.bat`.

> [!TIP]
> On a new machine (or RDP), ensure you run `pip install -r requirements.txt` to avoid `ModuleNotFoundError`.

Headless diagnostics:

```bash
python main.py --test
```

### Binary Release

Download `Anime Expeditions Macro Setup.exe` from [Releases](https://github.com/Ponchik0/ae/releases/latest) and run the installer.

## First Launch

1. Start Roblox and enter Anime Expeditions — the macro will automatically detect and dock the game window.
2. **Tasks** — build your queue: game mode (Story, Expedition, Portals, Tower, etc.), stage, difficulty, repeats, and auto-play preference.
3. **Creation (Macro Manager)** — configure your Pre Start routines: unit placements, settings toggles, walk paths, and save as a template.
4. **Dashboard** — assign templates to tasks and press **Start**.
5. **Settings** — configure hotkeys, Discord webhook, private server link, UI theme, and calibrated coordinates.

If an element fails detection, open **Settings → Template Check** to see match scores on your resolution, then capture a custom crop via **Image Manager**.

> [!IMPORTANT]
> When cropping button templates, crop closely around the text without extra background, as background animations in the game can alter matching scores.

## Updates

The macro compares the local `VERSION` file against the latest GitHub Release on startup, or manually when clicking the version badge in the header.

Updating never touches `settings.json`, custom templates, paths, or existing images in `Assets` — only new files are added.

## Documentation

| Document | Purpose |
|:--|:--|
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Comprehensive user manual |
| [`docs/architecture.md`](docs/architecture.md) | Codebase and module architecture overview |
| [`docs/from_ahk.md`](docs/from_ahk.md) | Coordinate references and lessons learned from the legacy AHK macro |
| [`AGENTS.md`](AGENTS.md) | Contributor guidelines, testing standards, and release workflow |

<details>
<summary><b>Project Structure</b></summary>

<br>

```
main.py                 Entry point; pywebview API bridge between UI and Python
core/                   Core engine: vision, runner, blocks, OCR, webhooks, dock
core/replay.py          Player input recorder & playback (Replay mode)
core/joinlink.py        Roblox join links & private server handling
core/template_check.py  Template validation utility
ui/                     Frontend: HTML, CSS, JS
ui/i18n.js              Russian translation dictionary
Assets/ui/              Reference button & UI crops
Assets/portals/         Portal reference crops
Assets/cards/           Upgrade card reference crops
Paths/defaults/         Default movement paths for Pre Start
tests/                  Pytest suite (no GUI / no Windows dependencies)
```

</details>

## Testing

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
node --check ui/app.js
node --check ui/i18n.js
```

## Credits

**Upstream Engine — [Cream's Macro | Anime Expeditions](https://github.com/Cweamy/Anime-Expeditions-Creams-Macro)** by [Cweamy](https://github.com/Cweamy) ([YouTube](https://www.youtube.com/@Cweamya)). The underlying computer vision architecture, stage navigation routines, window docking, OCR, webhooks, and core logic originate from his project (licensed under MIT).

**Fork Contributions** ([@Ponchik0](https://github.com/Ponchik0)):
- Redesigned user interface with custom themes, density controls, and bilingual RU/EN support.
- Portals mode automation and in-game Auto Play integration.
- Precision action recorder (Replay mode) with accurate in-match wait tracking.
- Template checking utility, deep-link rejoining, auto-reconnect recovery, and PDF reporting.
- Shop meat purchasing and community asset expansions.

## Disclaimer

> This is a fan-made automation tool. It is not affiliated with, endorsed by, or associated with Roblox Corporation or the developers of Anime Expeditions. Automating gameplay may violate game or platform terms of service — use at your own discretion. All game trademarks and assets belong to their respective owners.

<div align="center">
<br>

Licensed under [MIT](LICENSE) · Fork of [Cweamy/Anime-Expeditions-Creams-Macro](https://github.com/Cweamy/Anime-Expeditions-Creams-Macro)

</div>
