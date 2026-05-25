"""HTML builder — takes BriefingData, renders mint-themed HTML."""

from datetime import datetime, timezone
from .providers import BriefingData, WeatherForecast, Schedule, NewsSection, Quote, Event


def _render_quote(q: Quote | None) -> str:
    if not q or not q.text:
        return ""
    src = f" <span style='color:var(--muted2)'>{q.source}</span>" if q.source else ""
    return f'''<div class="quote-block">
  <div class="text">"{q.text}"</div>
  <div class="attr"><span class="author">{q.author}</span>{src}</div>
</div>'''


def _render_weather(wf: WeatherForecast | None) -> str:
    if not wf or not wf.today:
        return ""
    t = wf.today
    today = f'''<div class="weather-card">
  <div class="day">Hoy</div>
  <div class="temp">{t.temp:.0f}°C</div>
  <div class="cond">{t.condition}</div>
  <div class="detail"><span>Hum {t.humidity}%</span><span>Viento {t.wind:.0f}km/h</span></div>
</div>'''
    tmrw = ""
    if wf.tomorrow:
        tm = wf.tomorrow
        tmrw = f'''<div class="weather-card">
  <div class="day">Manana</div>
  <div class="temp">{tm.temp:.0f}°C</div>
  <div class="cond">{tm.condition}</div>
  <div class="detail"><span>Precip {tm.precip_prob}%</span></div>
</div>'''
    return f'''<div class="section">
  <div class="section-header"><span class="accent"></span><span class="title">Clima</span></div>
  <div class="weather-grid">{today}{tmrw}</div>
</div>'''


def _render_schedule(sched: Schedule | None) -> str:
    if not sched:
        return ""
    items_html = ""
    if sched.events:
        for e in sched.events:
            meta = f'<div class="meta">{e.meta}</div>' if e.meta else ""
            items_html += f'''<div class="schedule-item">
  <div class="time">{e.time}</div>
  <div class="body"><div class="title">{e.title}</div>{meta}</div>
</div>'''
    else:
        items_html = '<div class="empty-state">Sin actividades programadas</div>'

    deadlines_html = ""
    for d in sched.deadlines:
        deadlines_html += f'''<div class="deadline-item">
  <span class="dot"></span>
  <span class="label">{d.label}</span>
  <span class="date">{d.date}</span>
  <span class="days">({d.days_left}d)</span>
</div>'''

    return f'''<div class="section">
  <div class="section-header"><span class="accent"></span><span class="title">Agenda</span></div>
  <div class="schedule-card">
    <div class="header-bar"><span class="dot"></span><span class="label">{sched.day_name}</span></div>
    {items_html}
    {deadlines_html}
  </div>
</div>'''


def _render_news(sections: list[NewsSection]) -> str:
    if not sections:
        return ""
    result = ""
    for sec in sections:
        items_html = ""
        for i, item in enumerate(sec.items, 1):
            src = f'<div class="source">{item.source}</div>' if item.source else ""
            items_html += f'''<a class="news-item" href="{item.url}" target="_blank">
  <span class="num">{i}</span>
  <div class="content"><div class="news-title">{item.title}</div>{src}</div>
</a>'''
        result += f'''<div class="section">
  <div class="section-header"><span class="accent"></span><span class="title">{sec.name}</span></div>
  <div class="news-list">{items_html}</div>
</div>'''
    return result


def _render_idea(text: str) -> str:
    if not text:
        return ""
    return f'''<div class="idea-block">
  <div class="label">Idea del dia</div>
  <div class="text">{text}</div>
</div>'''


def _render_wiki(text: str) -> str:
    if not text:
        return ""
    return f'''<div class="wiki-block">
  <div class="label">Wiki</div>
  <div class="text">{text}</div>
</div>'''


def build_html(data: BriefingData) -> str:
    """Render full HTML from BriefingData."""
    with open(__file__.rsplit("/", 1)[0] + "/templates/briefing.html") as f:
        template = f.read()

    replacements = {
        "{{DATE}}": data.date_str,
        "{{GREETING}}": data.greeting,
        "{{DAY_NAME}}": data.day_name,
        "{{QUOTE_HTML}}": _render_quote(data.quote),
        "{{WEATHER_HTML}}": _render_weather(data.weather),
        "{{SCHEDULE_HTML}}": _render_schedule(data.schedule),
        "{{NEWS_HTML}}": _render_news(data.news),
        "{{IDEA_HTML}}": _render_idea(data.content_idea),
        "{{WIKI_HTML}}": _render_wiki(data.wiki_digest),
    }

    result = template
    for key, val in replacements.items():
        result = result.replace(key, val)
    return result
