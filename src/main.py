#!/usr/bin/env python3
"""
Morning Briefing Orchestrator.

Usage:
    python3 main.py [--config config.yaml]

Generates:
    /tmp/morning-briefing.html       — HTML newsletter
    /tmp/morning-briefing-voice.txt  — TTS script (for Audio Briefing)

Config:
    See config.yaml in repo root.
"""

import os
import sys
import re
import yaml
from datetime import datetime, timezone

from .providers import (
    BriefingData, BriefingData as BD,
    Quote, WeatherForecast, Schedule, NewsSection,
    get, available,
)
from .builder import build_html


DAY_NAMES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
GREETINGS = [
    "Buenos dias",
    "Que tengas un gran dia",
    "Arrancando el dia con todo",
    "Buen dia",
    "Dale que es hoy",
]


def load_config(path: str | None = None) -> dict:
    if path and os.path.exists(path):
        with open(path) as f:
            raw = f.read()
        # Resolve ${VAR} and $VAR patterns
        def _resolve_env(m):
            var = m.group(1) or m.group(2)
            return os.environ.get(var, "")
        raw = re.sub(r'\$\{(\w+)\}|\$(\w+)', _resolve_env, raw)
        return yaml.safe_load(raw) or {}

    # Default config
    return {
        "weather": {"provider": "open-meteo-weather", "lat": -24.78, "lon": -65.41, "city": "Salta"},
        "news": {"provider": "google-news-rss", "feeds": {}, "max_per_section": 5},
        "quote": {"provider": "stoic-quotes"},
        "schedule": {
            "provider": "notion-schedule",
            "notion_key": os.environ.get("NOTION_API_KEY", ""),
            "db_id": os.environ.get("NOTION_SCHEDULE_DB_ID", ""),
            "ds_id": os.environ.get("NOTION_DEADLINES_DB_ID", ""),
        },
        "audio": {"provider": "briefing-audio", "lang": "es"},
        "news_sections": ["AI & Tecnologia", "Mercados & Finanzas", "Politica & Global"],
        "output_html": "/tmp/morning-briefing.html",
        "output_audio": "/tmp/morning-briefing-voice.txt",
    }


def main(config: dict | None = None):
    if config is None:
        config = load_config()

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%d %b %Y")
    day_name = DAY_NAMES[now.weekday()]
    greeting = GREETINGS[now.day % len(GREETINGS)]

    data = BriefingData(
        date_str=date_str,
        day_name=day_name,
        greeting=greeting,
    )

    # ── Quote ──
    q_provider = config.get("quote", {}).get("provider", "stoic-quotes")
    try:
        q = get("quote", q_provider)
        data.quote = q.get_daily_quote()
    except Exception as e:
        print(f"[warn] Quote provider '{q_provider}': {e}", file=sys.stderr)

    # ── Weather ──
    w_cfg = config.get("weather", {})
    w_provider = w_cfg.get("provider", "open-meteo-weather")
    try:
        w = get("weather", w_provider, lat=w_cfg.get("lat", -24.78), lon=w_cfg.get("lon", -65.41))
        data.weather = w.get_forecast()
    except Exception as e:
        print(f"[warn] Weather provider '{w_provider}': {e}", file=sys.stderr)

    # ── Schedule ──
    s_cfg = config.get("schedule", {})
    s_provider = s_cfg.get("provider", "")
    if s_provider and s_cfg.get("notion_key"):
        # Accept both db_id (notion-schedule) and page_id (notion-page)
        has_db_id = bool(s_cfg.get("db_id"))
        has_page_id = bool(s_cfg.get("page_id"))
        if has_db_id or has_page_id:
            try:
                kwargs = {"notion_key": s_cfg["notion_key"], "ds_id": s_cfg.get("ds_id", "")}
                if has_page_id:
                    kwargs["page_id"] = s_cfg["page_id"]
                if has_db_id:
                    kwargs["db_id"] = s_cfg["db_id"]
                if s_cfg.get("properties"):
                    kwargs["properties"] = s_cfg["properties"]
                s = get("schedule", s_provider, **kwargs)
                data.schedule = s.get_events_today()
            except Exception as e:
                print(f"[warn] Schedule provider '{s_provider}': {e}", file=sys.stderr)

    # ── News ──
    n_cfg = config.get("news", {})
    n_provider = n_cfg.get("provider", "google-news-rss")
    try:
        n = get("news", n_provider, feeds=n_cfg.get("feeds"), max_per_section=n_cfg.get("max_per_section", 5))
        sections = n_cfg.get("feeds", list) if isinstance(n_cfg.get("feeds"), list) else None
        data.news = n.get_headlines(sections or config.get("news_sections"))
    except Exception as e:
        print(f"[warn] News provider '{n_provider}': {e}", file=sys.stderr)

    # ── Content idea (optional, from env var) ──
    data.content_idea = config.get("content_idea", os.environ.get("MORNING_IDEA", ""))

    # ── Wiki digest (optional, from file) ──
    wiki_path = os.path.expanduser(config.get("wiki_path", "~/.hermes/wiki/log.md"))
    try:
        with open(wiki_path) as f:
            lines = f.readlines()
            if lines:
                last = [l for l in lines if l.strip()][-3:]
                data.wiki_digest = " ".join(l.strip() for l in last)
    except Exception:
        pass

    # ── Build HTML ──
    html = build_html(data)
    html_path = config.get("output_html", "/tmp/morning-briefing.html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"HTML saved to {html_path} ({len(html)} bytes)")

    # ── Build Audio Script ──
    a_provider = config.get("audio", {}).get("provider", "briefing-audio")
    try:
        a = get("audio", a_provider)
        script = a.generate_script(data)
        audio_path = config.get("output_audio", "/tmp/morning-briefing-voice.txt")
        with open(audio_path, "w") as f:
            f.write(script)
        print(f"Audio script saved to {audio_path} ({len(script)} chars)")
    except Exception as e:
        print(f"[warn] Audio provider '{a_provider}': {e}", file=sys.stderr)

    return html_path


if __name__ == "__main__":
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else None
    cfg = load_config(cfg_path)
    main(cfg)
