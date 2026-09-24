# Hypixel Pit Event Notifier

A lightweight desktop app that tracks upcoming Hypixel **Pit** events and sends
you a desktop notification before they start.

Event data is pulled periodically from the [`BrookeAFK`](https://brookeafk.com/) event feed and shown in a
sortable list, with optional desktop notifications for events you care about.

## Features

- 🕒 Live countdown to every tracked event, refreshed every second
- 🔔 Two-stage notifications: an early "X minutes before" warning and a
  final "starting now" alert, each configurable independently
- ✅ Pick exactly which events (major and minor) you want to track
- 🔄 Automatic background refresh of event data every 30 minutes
- 🖥️ Simple UI — no browser or extra runtime needed

### Tracked events

**Major:** Pizza, Raffle, Squads, Spire, Blockhead, Robbery, Team Deathmatch, Rage Pit, Beast

**Minor:** 2x Rewards, KOTH, KOTL, Dragon Egg, Care Package, Auction, Quick Maths, Giant Cake, All Bounty

## Requirements

- Python 3.8+
- [`requests`](https://pypi.org/project/requests/)
- [`plyer`](https://pypi.org/project/plyer/) (for desktop notifications)
- `tkinter` (bundled with most Python installations; on Linux you may need
  to install it separately, e.g. `sudo apt install python3-tk`)

## Installation

1. Clone or download this repository.
2. Install the dependencies:

   ```bash
   pip install requests plyer
   ```

3. Make sure an icon file exists at `assets/dirtblock.ico` (used for the
   window icon and Windows notification branding).

## Usage

Run the app with:

```bash
python pit_event_notifier.py
```

On launch, the app will:

1. Build its window and event checklist.
2. Immediately fetch the latest event schedule in the background.
3. Refresh that schedule automatically every 30 minutes.

### Selecting events

Use the checkboxes under **Events to Track** to choose which major and minor
events appear in the list and trigger notifications. **Select All** /
**Deselect All** buttons are provided for convenience.

### Notification settings

Under **Notification Settings** you can:

- Toggle notifications on/off entirely
- Set how many minutes before an event you want an early warning
- Set how many minute(s) before an event starts you want a final alert

### Event list

The **Upcoming Events** table shows each tracked event's name, type
(major/minor), and a live countdown, sorted soonest-first. It updates once
per second.


## Building a standalone executable

The script checks for a PyInstaller-style frozen environment
(`sys._MEIPASS`) to locate bundled assets, so it can be packaged with
[PyInstaller](https://pyinstaller.org/):

```bash
pyinstaller --onefile --windowed --add-data "assets;assets" --icon=assets/dirtblock.ico --collect-all plyer pit_event_notifier.py
```

(On macOS/Linux, replace the `;` in `--add-data` with `:`.)
