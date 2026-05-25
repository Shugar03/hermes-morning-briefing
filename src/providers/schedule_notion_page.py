"""Notion Page Schedule provider.

Reads today's schedule from a Notion page with bulleted list items
(e.g. "Vista Semanal" page in Study Hub).
Parses format: "HH:MM - HH:MM  |  Title  -- Meta"
"""

import json
import re
from datetime import datetime, timezone
from . import ScheduleProvider, Schedule, Event, Deadline, register

DAY_NAMES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
TODAY_SPANISH = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


class NotionPageSchedule(ScheduleProvider):
    """Schedule provider that reads from a Notion page with bulleted schedule items."""

    def __init__(self, notion_key: str, page_id: str, ds_id: str | None = None):
        self.notion_key = notion_key
        self.page_id = page_id
        self.ds_id = ds_id or page_id

    def is_available(self) -> bool:
        return bool(self.notion_key) and bool(self.page_id)

    def _get_page_blocks(self) -> list[dict]:
        import urllib.request
        url = f"https://api.notion.com/v1/blocks/{self.page_id}/children?page_size=100"
        headers = {
            "Authorization": f"Bearer {self.notion_key}",
            "Notion-Version": "2022-06-28",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("results", [])

    def get_events_today(self) -> Schedule:
        today_idx = datetime.now(timezone.utc).weekday()
        today_name = DAY_NAMES[today_idx]
        today_spanish = TODAY_SPANISH[today_idx]

        blocks = self._get_page_blocks()
        events = []
        current_day = None
        in_today_section = False

        for block in blocks:
            btype = block.get("type", "")
            bt = block.get(btype, {})
            texts = bt.get("rich_text", []) if isinstance(bt, dict) else []
            if not texts:
                continue
            text = "".join(t.get("text", {}).get("content", "") for t in texts if t.get("text")).strip()
            if not text:
                continue

            if btype == "heading_2":
                # Day headers: "MARTES", "MIERCOLES", etc.
                day_header = text.strip().lower()
                current_day = day_header
                in_today_section = day_header == today_spanish
                continue

            if btype == "bulleted_list_item" and in_today_section:
                # Parse "HH:MM - HH:MM  |  Title  -- Meta"
                match = re.match(
                    r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*\|\s*(.+?)(?:\s*--\s*(.*))?$",
                    text,
                )
                if match:
                    time_str = match.group(1)
                    title = match.group(3).strip()
                    meta = match.group(4).strip() if match.group(4) else ""
                    events.append(Event(time=time_str, title=title, meta=meta))
                else:
                    # Fallback: treat the whole text as an event title with no time
                    events.append(Event(time="", title=text.strip(), meta=""))

        return Schedule(events=events, deadlines=[], day_name=today_name)


register(NotionPageSchedule)
