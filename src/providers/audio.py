"""Audio script generator: turns BriefingData into a spoken-word summary."""

from . import AudioProvider, BriefingData, register


class BriefingAudio(AudioProvider):
    """Generates a natural-language script for TTS."""

    def __init__(self, lang: str = "es"):
        self.lang = lang

    def is_available(self) -> bool:
        return True

    def generate_script(self, data: BriefingData) -> str:
        parts: list[str] = []

        greeting = data.greeting or "Buenos dias"
        parts.append(f"{greeting}. Hoy es {data.date_str}.")

        # Weather
        if data.weather and data.weather.today:
            w = data.weather.today
            parts.append(
                f"En cuanto al clima, actualmente hay {w.temp:.0f} grados, "
                f"{w.condition.lower()}, con {w.humidity} porciento de humedad "
                f"y viento de {w.wind:.0f} kilometros por hora."
            )

        # Schedule
        if data.schedule and data.schedule.events:
            parts.append("Tu agenda de hoy:")
            for e in data.schedule.events:
                meta = f", {e.meta}" if e.meta else ""
                parts.append(f"  A las {e.time}: {e.title}{meta}.")
            if data.schedule.deadlines:
                parts.append("Tienes pendientes importantes:")
                for d in data.schedule.deadlines:
                    parts.append(f"  {d.label} para el {d.date}, quedan {d.days_left} dias.")

        # News
        if data.news:
            for section in data.news:
                parts.append(f"En {section.name.lower()}:")
                for item in section.items[:3]:
                    src = f" segun {item.source}" if item.source else ""
                    parts.append(f"  {item.title}{src}.")

        # Content idea
        if data.content_idea:
            parts.append(f"Idea del dia: {data.content_idea}")

        # Wrap
        parts.append("Que tengas un excelente dia.")

        return "\n".join(parts)


register(BriefingAudio)
