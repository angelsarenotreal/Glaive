# Glaive — Minimalist In-Game League of Legends Scouting Overlay

**Glaive** is a high-performance, minimal, monochrome in-game companion and player scouting overlay for League of Legends. Built natively with Python and PyQt6, it delivers rich real-time player data with zero in-game frame drops and zero ping impact.

---

## Key Features

- **Minimalist Monochrome Glassmorphism**: Clean obsidian and slate aesthetic (`#0a0c10`) with subtle contrast badges for distraction-free gameplay.
- **Zero FPS & Micro-Stutter Impact**: Unlike Overwolf and Electron apps that consume 500MB–1.2GB of RAM and trigger periodic garbage collection lag, Glaive runs at **~35 MB RAM** and **0.0% idle CPU**.
- **Zero Ping Impact**: Game state is queried once via Riot's local API and official Web API upon match start, then cached in-memory. Zero network requests are sent during active gameplay.
- **No Focus Stealing (`WS_EX_NOACTIVATE`)**: Toggling or clicking the overlay never steals input focus away from `League of Legends.exe`.
- **100% Vanguard Safe**: Reads only the official local Riot Live Client Data API (`https://127.0.0.1:2999`) and official Riot Web API. Zero memory hooking, zero DLL injection.
- **Global Hotkey**: Press **`Ctrl + X`** (configurable) anytime in-game to instantly show or hide the overlay.
- **Rich Player Intelligence**:
  - Solo/Duo rank, LP, and seasonal win rate.
  - Current champion win rate and games played.
  - Tactical badges: `OTP`, `Main Champ`, `Hot Streak (3W+)`, `Cold Streak (3L+)`, `First Time`, `High KDA`, `High Deaths`.
  - Recent 5-match form history.
  - Team average rank and win rate comparisons.

---

## Quick Start

### 1. Requirements
- Windows 10/11
- Python 3.10+ (Tested on Python 3.14)
- League of Legends display mode set to **Borderless Windowed** (Options -> Video -> Window Mode -> Borderless).

### 2. Run the Application

To run live with automatic match detection:
```bash
python src/main.py
```

To preview and test the overlay immediately with realistic 10-player data:
```bash
python src/main.py --mock
```

---

## Configuration & API Key

1. Get a free Riot Developer API key at [developer.riotgames.com](https://developer.riotgames.com/).
2. In Glaive, click **⚙ Settings** in the top-right corner of the overlay.
3. Paste your API key, select your platform region (e.g., `EUW`, `NA`, `KR`), and adjust your preferred opacity or hotkey.
4. Settings are automatically saved to `config.json`.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + X` | Toggle Overlay Show / Hide |
| `Esc` | Hide Overlay |
| `Drag Header` | Reposition Overlay Window |

---

## Project Structure

```
Glaive/
├── src/
│   ├── analytics.py       # Badges, streak detection & KDA calculators
│   ├── config.py          # App settings & platform routing
│   ├── game_poller.py     # Port 2999 local live client listener
│   ├── hotkey_listener.py # Global Windows hotkey hook (Ctrl+X)
│   ├── mock_data.py       # 10-player test lobby generator
│   ├── riot_api.py        # Riot Web API client (PUUID, League, Match-V5)
│   ├── main.py            # Application entrypoint
│   └── ui/
│       ├── overlay_window.py   # Frameless transparent overlay
│       ├── player_card.py      # Individual player stats card
│       ├── settings_dialog.py  # Configuration modal
│       └── theme.py            # Monochrome design tokens & QSS
├── tests/
│   ├── test_analytics.py  # Unit tests for analytics & badges
│   └── test_config.py     # Unit tests for configuration
└── requirements.txt
```
