<div align="center">

<img src="logo.ico" width="96" height="96" alt="Anime Expeditions">

# Anime Expeditions

**Auto-farm macro for Anime Expeditions on Roblox — Version 2.0.0**

<p align="center">
  <b>English</b> • <a href="README.ru.md">Русский</a>
</p>

Vision-driven macro: real-time screen capture and template detection.<br>
Zero process injection, zero memory manipulation.<br>
Roblox embeds directly into the macro interface for fully autonomous farming.

<br>

<a href="https://github.com/Ponchik0/ae/releases/latest">
  <img src="https://img.shields.io/badge/version-2.0.0-c9a227?style=for-the-badge&labelColor=1c1c1c" alt="Version 2.0.0">
</a>
<img src="https://img.shields.io/badge/platform-Windows-c9a227?style=for-the-badge&labelColor=1c1c1c" alt="Windows">
<img src="https://img.shields.io/badge/python-3.10+-c9a227?style=for-the-badge&labelColor=1c1c1c" alt="Python 3.10+">
<a href="LICENSE">
  <img src="https://img.shields.io/badge/license-MIT-c9a227?style=for-the-badge&labelColor=1c1c1c" alt="MIT">
</a>

<br><br>

[Overview](#overview) · [Interface Showcase](#interface-showcase) · [Key Capabilities](#key-capabilities) · [Installation](#installation) · [First Launch](#first-launch) · [Webhooks](#discord-webhooks) · [Documentation](#documentation) · [Credits](#credits)

</div>

---

## Overview

A specialized, feature-complete fork of [Cream's Macro](https://github.com/Cweamy/Anime-Expeditions-Creams-Macro) built for Anime Expeditions on Roblox.

**Core engine credit**: The base computer vision algorithms, stage navigation structure, Roblox window docking mechanisms (`SetParent`), OCR, and packaging were originally architected by [Cweamy](https://github.com/Cweamy). Upstream enhancements are continuously tracked and integrated.

**Version 2.0.0 highlights**:
- **Atmospheric Glass UI**: Complete visual overhaul featuring frosted glass surfaces, centered floating navigation, high-contrast typography, and zero emoji clutter.
- **Modular Dashboard Customization**: Reorderable dashboard slots, granular sub-block toggles, and instant visual layout management.
- **Resolution Preservation & Fullscreen**: Maximizing or resizing the macro window automatically preserves Roblox's calibrated 1152x756 game canvas, accompanied by non-intrusive HUD notifications.
- **Active Automations Hub**: Centralized monitoring and one-click controls for Auto-Shop, Bounty Hunter (Mythic-only rerolls), Auto-Crafting, and Fuel Watchdog.
- **Clean Discord Webhook Telemetry**: Upstream-aligned Discord embeds without emoji spam, featuring live match results, win streaks, session winrate bars, active automations, and OpenCV status cards.
- **High-Precision Input Replay**: TinyTask-style mouse and keyboard recorder operating on `time.perf_counter()`, faithfully preserving in-match idle times.

Legacy AutoHotkey coordinates, thresholds, and operational findings remain documented in [`docs/from_ahk.md`](docs/from_ahk.md).

---

## Interface Showcase

<p align="center">
  <img src="docs/media/glass_home.png" alt="Anime Expeditions v2.0.0 Home Dashboard" width="100%">
  <em>v2.0.0 Home: Embedded Roblox canvas, live task queue, win streak telemetry, active automations, real-time process logs, and session history.</em>
</p>

<p align="center">
  <img src="docs/media/glass_tasks.png" alt="Tasks & Queue Management" width="100%">
  <em>v2.0.0 Tasks: Multi-mode queue builder, universal JSON import/export, and flexible task configuration.</em>
</p>

<p align="center">
  <img src="docs/media/glass_scenarios.png" alt="Scenarios & Macro Builder" width="100%">
  <em>v2.0.0 Scenarios: Visual phase-based macro editor (Pre Start, Battle, Loop A & B) with real-time WASD movement paths and modular palette.</em>
</p>

---

## Key Capabilities

| System | Technical Details |
|:--|:--|
| **Docked Roblox Window** | Roblox embeds directly into the macro window (`core/dock.py`). Keystrokes and mouse inputs remain strictly bounded, allowing other desktop tasks without interference. |
| **Resolution Integrity** | Window maximization preserves the internal 1152x756 game aspect ratio without pixel distortion or coordinate drift. HUD toasts display active resolution state. |
| **Multi-Mode Task Queue** | Story, Expedition, Raid, Tower, Challenge, and Portals. Supports map, stage, difficulty, matchmaking/solo selection, and repeat counters. |
| **Portals Automation** | Opens portals directly from inventory, navigates lobby selection, picks mid-battle offer cards, and chains next portals directly through results. |
| **In-Game Auto Play** | Autonomous toggle for built-in Roblox Auto Play, suppressing redundant camera movement while maintaining persistent run states. |
| **Pre Start Builder** | Structured starter unit routines with placement verification, retry offsets, game settings toggles via hotkeys, and first-repeat execution limits. |
| **Action Recorder (Replay)** | F8 starts/stops recording; F9 toggles the overlay. Preserves exact in-match waiting durations using monotonic absolute clocks. |
| **Active Automations** | Background modules: Auto-Shop hourly sweeps, Bounty Hunter mythic objective rerolls, periodic Auto-Crafting, and Fuel Watchdog monitoring. |
| **Smart Recovery** | Auto-returns to lobby on unexpected UI stalls, missing clicks, or black screens. Relaunches Roblox via `roblox://` deep-links upon disconnects. |
| **Discord Notifications** | Formatted embed telemetry: Victory/Defeat verification, duration, wave count, streak tracking, session winrate bars, and OpenCV status cards. |

<details>
<summary><b>Detailed Automation Systems</b> — click to inspect</summary>

<br>

- **Autonomous Portals Farming**: Operates portal cycles directly from the player inventory. Selects the middle modifier card in-game and transitions into subsequent portals via the completion screen without returning to the lobby.
- **Roblox Window Docking**: Uses Win32 `SetParent` integration. The game canvas is maintained at 1152x756. Minimizing or moving the macro window moves the game container synchronously.
- **Bounty Hunter Automation**: Automatically checks the Event Bounty Board, re-rolls daily objective cards until Mythic rarity is confirmed, and proceeds to map execution.
- **Scheduled Auto-Shop**: Scans the event merchant on schedule, purchasing tickets, trait crystals, stat rolls, and meat supplies according to user quotas.
- **Fuel Watchdog**: Automatically monitors expedition fuel reserves, executes navigation paths between stations, and refills resources at defined intervals.
- **Stall Detection Watchdog**: Monitors action heartbeat. If the client freezes or remains inactive for 25 minutes, the macro terminates Roblox, executes deep-link reconnection, and restores the active task.

</details>

---

## Discord Webhooks

Webhooks provide structured match reporting matching the clean upstream aesthetic without emoji noise:

- **Match Verdict**: Victory, Defeat, or Round Finished with duration, map, stage, difficulty, and wave counters.
- **Session Telemetry**: Total elapsed runtime, session record (W/L), winrate percentage, runs per hour, and Challenge reset countdown.
- **All-Time Metrics**: Total match history, cumulative winrate, and persistent uptime counter.
- **Streak & Performance**: Current consecutive win/loss streak, all-time best streak, and today's local calendar record.
- **Active Automations**: Real-time operational state of Shop, Bounty, Crafting, and Fuel services.
- **Visual Status Card**: Programmatically generated OpenCV BGR card attached alongside the raw screenshot.

---

## Requirements

| Requirement | Specification |
|:--|:--|
| **Operating System** | Windows 10 or Windows 11 (64-bit) |
| **Roblox Client** | Official desktop client running Anime Expeditions |
| **Python** | 3.10 or higher (for source execution) |
| **WebView2 Runtime** | Pre-installed on Windows 10/11 (Edge runtime) |
| **OCR Engines** | RapidOCR / Tesseract OCR (optional, for reward text scanning) |

---

## Installation

### From Source

```bash
git clone https://github.com/Ponchik0/ae.git
cd ae
pip install -r requirements.txt
```

Run application:

```bash
python main.py
```

Optional diagnostic run:

```bash
python main.py --test
```

### Binary Release

Download `Anime Expeditions Macro Setup.exe` from [GitHub Releases](https://github.com/Ponchik0/ae/releases/latest) and execute the installer. Settings and assets are preserved across updates.

---

## First Launch

1. Start Roblox and enter Anime Expeditions — the macro detects and embeds the game canvas automatically.
2. **Tasks**: Configure your target playlist: game mode (Story, Portals, Raid, Expedition), map, stage, and repetitions.
3. **Macro Manager**: Build Pre Start routines: unit placement points, initial settings toggles, and movement paths.
4. **Dashboard**: Select your configured templates, arrange dashboard blocks via Customize Layout, and click **Start**.
5. **Settings**: Adjust hotkeys, Discord webhook URL, private server link, and visual density.

---

## Verification & Testing

The test suite runs headlessly without Roblox or Windows API dependencies:

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
node --check ui/app.js
node --check ui/concept-glass/app.js
node --check ui/i18n.js
```

---

## Documentation

| Guide | Description |
|:--|:--|
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | In-depth operational documentation |
| [`docs/architecture.md`](docs/architecture.md) | Modular engine architecture and data flow |
| [`docs/from_ahk.md`](docs/from_ahk.md) | Legacy AutoHotkey coordinate references and interface quirks |
| [`AGENTS.md`](AGENTS.md) | Development standards, testing rules, and release protocols |

---

## Contributors

[Cweamy](https://github.com/Cweamy) — original engine author ([Cream's Macro | Anime Expeditions](https://github.com/Cweamy/Anime-Expeditions-Creams-Macro), [YouTube](https://www.youtube.com/@Cweamya)). Core vision routines, window docking, OCR, coordinate pipelines, and base macro loops are authored by Cweamy under MIT.

---

## Disclaimer

> This project is an independent automation utility. It is not affiliated with, endorsed by, or associated with Roblox Corporation or Anime Expeditions. Automation tools should be used in compliance with relevant platform terms. All trademarks and game assets belong to their respective copyright holders.

<div align="center">
<br>

Licensed under [MIT](LICENSE) · Fork of [Cweamy/Anime-Expeditions-Creams-Macro](https://github.com/Cweamy/Anime-Expeditions-Creams-Macro)

</div>
