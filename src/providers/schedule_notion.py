"""Notion schedule provider.

Reads today's events and deadlines from a Notion database.
Requires NOTION_API_KEY env var and a Notion DB ID in config.

Property names (day, status, order, time, professor, location, date)
are configurable via `properties` in the YAML config and default to
Spanish names for Sherman's Study Hub schema.
"""

from datetime import datetime, timezone
from . import ScheduleProvider, Schedule, Event, Deadline, register


DAY_NAMES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
DEADLINE_DAYS_WARNING = 12

# Default property names (Spanish / Sherman Study Hub)
DEFAULT_PROPS = {
    "day": "Dia",
    "status": "Estado",
    "order": "Orden",
    "time": "Horario",
    "professor": "Profesor",
    "location": "Ubicacion",
    "date": "Fecha",
}


class NotionSchedule(ScheduleProvider):
    def __init__(self, notion_key: str, db_id: str, ds_id: str | None = None,
                 properties: dict | None = None):
        self.notion_key = notion_key
        self.db_id = db_id
        self.ds_id = ds_id or db_id
        self.p = {**DEFAULT_PROPS, **(properties or {})}

    def is_available(self) -> bool:
        return bool(self.notion_key) and bool(self.db_id)

    def _notion_query(self, db_id: str, payload: dict) -> list[dict]:
        import json, urllib.request
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        headers = {
            "Authorization": f"Bearer {self.notion_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("results", [])

    def _get_title(self, props: dict) -> str:
        for val in props.values():
            if isinstance(val, dict) and val.get("type") == "title":
                els = val.get("title", [])
                return "".join(e.get("plain_text", "") for e in els)
            if isinstance(val, dict) and val.get("type") == "rich_text":
                els = val.get("rich_text", [])
                return "".join(e.get("plain_text", "") for e in els)
        return ""

    def _get_select(self, props: dict, key: str) -> str:
        v = props.get(key, {})
        if isinstance(v, dict):
            sel = v.get("select") or v.get("status") or {}
            return (sel.get("name", "") or "") if isinstance(sel, dict) else ""
        return ""

    def _get_text(self, props: dict, key: str) -> str:
        v = props.get(key, {})
        if isinstance(v, dict):
            rt = v.get("rich_text", []) or v.get("text", [])
            return "".join(e.get("plain_text", "") for e in rt)
        return ""

    def get_events_today(self) -> Schedule:
        today = datetime.now(timezone.utc)
        day_name = DAY_NAMES[today.weekday()]
        today_str = today.strftime("%Y-%m-%d")
        today_weekday = today.weekday()

        events: list[Event] = []
        deadlines: list[Deadline] = []

        # ── Query 1: Daily schedule ──
        payload = {
            "filter": {
                "and": [
                    {"property": self.p["day"], "select": {"equals": day_name}},
                    {"property": self.p["status"], "status": {"does_not_equal": "Completado"}},
                ]
            },
            "sorts": [{"property": self.p["order"], "direction": "ascending"}],
        }
        results = self._notion_query(self.db_id, payload)
        for r in results:
            props = r.get("properties", {})
            title = self._get_title(props)
            if not title:
                continue
            time_str = self._get_select(props, self.p["time"]) or ""
            prof = self._get_text(props, self.p["professor"])
            ubic = self._get_text(props, self.p["location"])
            meta_parts = [p for p in [prof, ubic] if p]
            meta = " | ".join(meta_parts) if meta_parts else ""
            events.append(Event(time=time_str, title=title, meta=meta))

        # ── Query 2: Deadlines ──
        if self.ds_id:
            try:
                dl_payload = {
                    "filter": {
                        "and": [
                            {"property": self.p["status"], "status": {"does_not_equal": "Completado"}},
                            {"property": self.p["date"], "date": {"on_or_after": today_str}},
                        ]
                    },
                    "sorts": [{"property": self.p["date"], "direction": "ascending"}],
                }
                dl_results = self._notion_query(self.ds_id, dl_payload)
                for r in dl_results:
                    props = r.get("properties", {})
                    title = self._get_title(props)
                    date_prop = props.get(self.p["date"], {}).get("date", {})
                    if not title or not date_prop:
                        continue
                    date_str = date_prop.get("start", "")
                    if not date_str:
                        continue
                    try:
                        dt = datetime.fromisoformat(date_str)
                        days = (dt - today).days
                    except Exception:
                        continue
                    if 0 <= days <= DEADLINE_DAYS_WARNING:
                        deadlines.append(Deadline(
                            label=title,
                            date=dt.strftime("%d/%m"),
                            days_left=days,
                        ))
            except Exception:
                pass

        return Schedule(
            day_name=day_name,
            events=events,
            deadlines=deadlines,
        )


register(NotionSchedule)
