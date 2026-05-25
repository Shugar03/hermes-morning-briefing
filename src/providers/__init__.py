"""Provider system for Morning Briefing.

Each provider implements a base interface and is registered via the factory.
Adding a new backend (e.g. Todoist, Linear) == writing one class + registering it.
"""

import importlib
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


# ── Data Contracts ──────────────────────────────────────────────────────────

@dataclass
class Event:
    """A single calendar/agenda event."""
    time: str              # "10:00"
    title: str             # "Analisis Matematico"
    meta: str = ""         # "Prof. Garcia | Aula 12"

@dataclass
class Deadline:
    label: str
    date: str
    days_left: int

@dataclass
class Schedule:
    day_name: str
    events: list[Event] = field(default_factory=list)
    deadlines: list[Deadline] = field(default_factory=list)

@dataclass
class Weather:
    temp: float
    condition: str          # "Despejado", "Lluvia ligera", etc.
    humidity: int | None = 0
    wind: float | None = 0
    precip_prob: int = 0

@dataclass
class WeatherForecast:
    today: Weather
    tomorrow: Optional[Weather] = None

@dataclass
class NewsItem:
    title: str
    url: str
    source: str = ""

@dataclass
class NewsSection:
    name: str
    items: list[NewsItem]

@dataclass
class Quote:
    text: str
    author: str
    source: str = ""

@dataclass
class BriefingData:
    """Everything the HTML builder needs."""
    date_str: str
    greeting: str
    day_name: str
    quote: Optional[Quote] = None
    weather: Optional[WeatherForecast] = None
    schedule: Optional[Schedule] = None
    news: list[NewsSection] = field(default_factory=list)
    content_idea: str = ""
    wiki_digest: str = ""


# ── Base Provider Interface ─────────────────────────────────────────────────

class Provider(ABC):
    """Every module (weather, news, schedule, etc.) extends this."""
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Can this provider operate with current config?"""
        ...


class ScheduleProvider(Provider):
    name = "schedule"

    @abstractmethod
    def get_events_today(self) -> Schedule:
        ...


class WeatherProvider(Provider):
    name = "weather"

    @abstractmethod
    def get_forecast(self) -> WeatherForecast:
        ...


class NewsProvider(Provider):
    name = "news"

    @abstractmethod
    def get_headlines(self, sections: list[str]) -> list[NewsSection]:
        ...


class QuoteProvider(Provider):
    name = "quote"

    @abstractmethod
    def get_daily_quote(self) -> Quote:
        ...


class AudioProvider(Provider):
    """Generates a spoken-word summary from BriefingData."""
    name = "audio"

    @abstractmethod
    def generate_script(self, data: BriefingData) -> str:
        ...


# ── Registry ──

import re

_providers: dict[str, dict[str, type[Provider]]] = {}

def _class_to_key(name: str) -> str:
    """Convert CamelCase to kebab-case: OpenMeteoWeather → open-meteo-weather."""
    s = re.sub(r'(?<=[a-z])(?=[A-Z])', '-', name).lower()
    # Remove trailing 'provider' / 'schedule' etc if present
    for suffix in ['provider', 'schedule']:
        if s.endswith(f'-{suffix}'):
            s = s[:-(len(suffix)+1)]
    return s

def register(provider_class: type[Provider]) -> type[Provider]:
    """Decorator: register a provider implementation."""
    kind = provider_class.name
    key = _class_to_key(provider_class.__name__)
    _providers.setdefault(kind, {})[key] = provider_class
    return provider_class

def available(kind: str) -> list[str]:
    """List registered provider keys for a kind (e.g. 'schedule')."""
    return list(_providers.get(kind, {}).keys())

def get(kind: str, key: str, **kwargs) -> Provider:
    """Instantiate a provider by kind + key."""
    cls = _providers.get(kind, {}).get(key)
    if not cls:
        raise ValueError(f"No provider registered: {kind}/{key}. "
                         f"Available {kind}: {available(kind)}")
    return cls(**kwargs)


# ── Auto-discover all provider modules in this package ──

for _importer, _modname, _ispkg in pkgutil.iter_modules(__path__):
    if not _modname.startswith("_") and _modname != "schedule_":
        importlib.import_module(f".{_modname}", __name__)
