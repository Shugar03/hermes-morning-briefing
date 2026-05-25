---
name: morning-briefing
description: Daily morning briefing for Hermes Agent — weather, agenda, deadlines, news, content idea, and audio summary. Runs every morning and delivers to Telegram.
version: 1.0.0
author: Shugar
license: MIT
metadata:
  hermes:
    tags: [morning-briefing, daily, newsletter, modular]
    related_skills: []
---

# Morning Briefing — Skill for Hermes Agent

## Description

This skill generates a daily HTML briefing with:
- Weather forecast (Open-Meteo, no API key)
- Daily stoic quote
- Agenda from your calendar (Notion / Google Calendar / Obsidian / iCal / Manual)
- Active deadlines
- Tech, market, and global news (Google News RSS)
- Optional: content idea + wiki digest
- **Audio summary** via TTS

## Cron Setup

This skill is designed to run as a scheduled cron job. After installation:

```bash
# Test manually first
python3 ~/.hermes/scripts/morning-briefing.py
```

Then ask your Hermes Agent:

> *"Crea el cron del morning briefing a las 7 AM usando el skill morning-briefing"*

## What the Cron Does

1. Runs `python3 ~/.hermes/scripts/morning-briefing.py`
2. Script generates `/tmp/morning-briefing.html`
3. Agent reads the audio script from `/tmp/morning-briefing-voice.txt`
4. Agent sends the HTML as a document to Telegram
5. Agent calls `text_to_speech()` with the audio script
6. Telegram delivers both the HTML and a voice bubble

## Architecture

```
src/
├── main.py                  # Orchestrator
├── builder.py               # → HTML (mint design)
├── templates/
│   └── briefing.html        # taste-skill designed template
└── providers/
    ├── __init__.py          # Base + factory
    ├── schedule_notion.py   # Notion backend
    ├── weather.py           # Open-Meteo
    ├── news.py              # Google News RSS
    ├── quote.py             # Stoic quotes
    └── audio.py             # TTS script generator
```

## Adding a New Provider

Each schedule backend implements the same interface:

```python
from src.providers import ScheduleProvider, Schedule, register

class MyCalendar(ScheduleProvider):
    name = "schedule"
    def is_available(self): ...
    def get_events_today(self) -> Schedule: ...

register(MyCalendar)
```

Then set `schedule.provider: my-calendar` in config.yaml.

## Config

Edit `~/.hermes/morning-briefing.yaml` to choose your backends.

## Verification Checklist

- [ ] `python3 ~/.hermes/scripts/morning-briefing.py` exits 0
- [ ] `/tmp/morning-briefing.html` exists
- [ ] `/tmp/morning-briefing-voice.txt` exists
- [ ] HTML renders correctly in browser
- [ ] Cron job delivers to Telegram
- [ ] Audio bubble arrives in Telegram
