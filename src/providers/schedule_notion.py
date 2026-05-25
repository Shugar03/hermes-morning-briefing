"""Notion schedule provider.

Reads today's events and deadlines from a Notion database.
Supports both regular databases and multi-source (data_source) databases.
Auto-detects which endpoint to use.

Property names are configurable via `properties` in the YAML config.
Defaults to the Cronograma Completo schema (Sherman's Study Hub).
"""

from datetime import datetime, timezone
from . import ScheduleProvider, Schedule, Event, Deadline, register


DAY_NAMES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
DEADLINE_DAYS_WARNING = 12

# Default property names (Cronograma Completo schema)
DEFAULT_PROPS = {
    "title": "Nombre",
    "time": "Hora Inicio",
    "time_end": "Hora Fin",
    "date": "Fecha",
    "professor": "Profesor",
    "location": "Ubicacion",
    "status": "",          # no status filter needed
}


class NotionSchedule(ScheduleProvider):
    def __init__(self, notion_key: str, db_id: str, ds_id: str | None = None,
                 properties: dict | None = None):
        self.notion_key = notion_key
        self.db_id = db_id
        self.ds_id = ds_id or db_id
        self.p = {**DEFAULT_PROPS, **(properties or {})}
        self._use_data_source = None  # auto-detect on first query

    def is_available(self) -> bool:
        return bool(self.notion_key) and bool(self.db_id)

    def _query(self, payload: dict, db_id: str | None = None) -> list[dict]:
        """Query Notion, auto-detecting regular DB vs data_source endpoint."""
        import json, urllib.request

        target_id = db_id or self.db_id
        headers = {
            "Authorization": f"Bearer {self.notion_key}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json",
        }

        # Try data_source endpoint if we know it's multi-source
        if self._use_data_source is True:
            url = f"https://api.notion.com/v1/data_sources/{target_id}/query"
        elif self._use_data_source is False:
            url = f"https://api.notion.com/v1/databases/{target_id}/query"
        else:
            # Auto-detect: try database first, fallback to data_source
            url = f"https://api.notion.com/v1/databases/{target_id}/query"
            data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    self._use_data_source = False
                    return json.loads(resp.read()).get("results", [])
            except urllib.error.HTTPError as e:
                err = json.loads(e.read().decode())
                # Multi-source databases return 400 with invalid_request_url
                if e.code == 400:
                    self._use_data_source = True
                    url = f"https://api.notion.com/v1/data_sources/{target_id}/query"
                else:
                    raise

        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("results", [])

    def _get_title(self, props: dict) -> str:
        # Prefer "title" type over "rich_text" (legacy compat)
        for val in props.values():
            if isinstance(val, dict) and val.get("type") == "title":
                els = val.get("title", [])
                return "".join(e.get("plain_text", "") for e in els)
        for val in props.values():
            if isinstance(val, dict) and val.get("type") == "rich_text":
                els = val.get("rich_text", [])
                return "".join(e.get("plain_text", "") for e in els)
        return ""

    def _get_text(self, props: dict, key: str) -> str:
        if not key:
            return ""
        v = props.get(key, {})
        if isinstance(v, dict):
            rt = v.get("rich_text", []) or v.get("text", [])
            return "".join(e.get("plain_text", "") for e in rt)
        return ""

    def _get_select(self, props: dict, key: str) -> str:
        if not key:
            return ""
        v = props.get(key, {})
        if isinstance(v, dict):
            sel = v.get("select") or v.get("status") or {}
            return (sel.get("name", "") or "") if isinstance(sel, dict) else ""
        return ""

    def _get_date_str(self, props: dict, key: str) -> str:
        """Extract date string from a date property."""
        if not key:
            return ""
        v = props.get(key, {})
        if isinstance(v, dict):
            d = v.get("date") or {}
            return d.get("start", "") if isinstance(d, dict) else ""
        return ""

    def get_events_today(self) -> Schedule:
        today = datetime.now(timezone.utc)
        # Adjust to Argentina time (UTC-3) for correct day
        local_now = today.replace(hour=(today.hour - 3) % 24) if today.hour >= 3 else today
        day_name = DAY_NAMES[local_now.weekday()]
        today_str = today.strftime("%Y-%m-%d")

        events: list[Event] = []
        deadlines: list[Deadline] = []

        # ── Query: today's events ──
        payload = {
            "filter": {
                "and": [
                    {"property": self.p["date"], "date": {"equals": today_str}},
                ]
            },
            "sorts": [{"property": self.p["time"], "direction": "ascending"}],
        }

        # Add status filter if configured
        if self.p.get("status"):
            payload["filter"]["and"].append(
                {"property": self.p["status"], "status": {"does_not_equal": "Completado"}}
            )

        try:
            results = self._query(payload)
        except Exception as e:
            print(f"[warn] Schedule query failed: {e}", file=__import__("sys").stderr)
            results = []

        for r in results:
            props = r.get("properties", {})
            title = self._get_title(props)
            if not title:
                continue

            time_str = self._get_text(props, self.p["time"]) or ""
            prof = self._get_text(props, self.p.get("professor", ""))
            ubic = self._get_text(props, self.p.get("location", ""))
            meta_parts = [p for p in [prof, ubic] if p]
            meta = " | ".join(meta_parts) if meta_parts else ""

            events.append(Event(time=time_str, title=title, meta=meta))

        # ── Deadlines: upcoming events (next 12 days) ──
        if self.ds_id:
            try:
                dl_payload = {
                    "filter": {
                        "and": [
                            {"property": self.p["date"], "date": {"on_or_after": today_str}},
                        ]
                    },
                    "sorts": [{"property": self.p["date"], "direction": "ascending"}],
                }

                if self.p.get("status"):
                    dl_payload["filter"]["and"].append(
                        {"property": self.p["status"], "status": {"does_not_equal": "Completado"}}
                    )

                dl_results = self._query(dl_payload, self.ds_id)
                seen = set()
                for r in dl_results:
                    props = r.get("properties", {})
                    title = self._get_title(props)
                    date_str = self._get_date_str(props, self.p["date"])
                    if not title or not date_str:
                        continue

                    # Deduplicate by title + date
                    dedup_key = f"{title}::{date_str[:10]}"
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)

                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        days = (dt - today).days
                    except Exception:
                        continue

                    if 0 <= days <= DEADLINE_DAYS_WARNING:
                        deadlines.append(Deadline(
                            label=title,
                            date=dt.strftime("%d/%m"),
                            days_left=days,
                        ))
            except Exception as e:
                print(f"[warn] Schedule deadlines query failed: {e}",
                      file=__import__("sys").stderr)

        return Schedule(
            day_name=day_name,
            events=events,
            deadlines=deadlines,
        )


register(NotionSchedule)
