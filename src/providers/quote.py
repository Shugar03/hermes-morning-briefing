"""Stoic quote provider (local, no API needed)."""

from datetime import datetime, timezone
from . import QuoteProvider, Quote, register


QUOTES: list[Quote] = [
    Quote("La felicidad de tu vida depende de la calidad de tus pensamientos.", "Marco Aurelio", "Meditaciones"),
    Quote("Tienes poder sobre tu mente, no sobre eventos externos. Date cuenta de esto y encontraras la fuerza.", "Marco Aurelio", "Meditaciones"),
    Quote("Muy poco es necesario para hacer una vida feliz; todo esta en tu poder.", "Marco Aurelio", "Meditaciones"),
    Quote("No te preocupes por lo que otros dicen de ti. Lo que importa es lo que tu piensas de ti mismo.", "Marco Aurelio", "Meditaciones"),
    Quote("El alma se tine del color de sus pensamientos.", "Marco Aurelio", "Meditaciones"),
    Quote("Si no es correcto, no lo hagas. Si no es verdadero, no lo digas.", "Marco Aurelio", "Meditaciones"),
    Quote("Que nada te perturbe. Nada te espante. Todo pasa. Dios no cambia.", "Tomas Kempis", "Imitacion de Cristo"),
    Quote("El hombre que no espera necesitar algo nunca lo poseera.", "Seneca", "Cartas a Lucilio"),
    Quote("No es que tengamos poco tiempo, es que desperdiciamos mucho.", "Seneca", "Sobre la brevedad de la vida"),
    Quote("La vida es larga si sabes vivirla.", "Seneca", "Sobre la brevedad de la vida"),
    Quote("No hay viento favorable para el que no sabe a donde va.", "Seneca", "Cartas a Lucilio"),
    Quote("Somos mas valientes de lo que creemos y mas temerosos de lo que imaginamos.", "Seneca", "Cartas a Lucilio"),
    Quote("Comienza ya a ser lo que quieres ser.", "Seneca", "Cartas a Lucilio"),
    Quote("No te digo que sea facil. Te digo que vale la pena.", "Gary Vaynerchuk", ""),
    Quote("Lo que obstaculiza, instruye.", "Epicteto", "Manual"),
    Quote("No son las cosas las que nos perturban, sino los juicios que hacemos sobre ellas.", "Epicteto", "Enquiridion"),
    Quote("El hombre no es lo que cree ser. Es lo que hace.", "Epicteto", "Discusiones"),
    Quote("Si quieres mejorar, contentate con parecer ignorante.", "Epicteto", "Manual"),
    Quote("Solo se que no se nada.", "Socrates", ""),
    Quote("Una vida sin examinar no merece ser vivida.", "Socrates", ""),
    Quote("Se el cambio que quieres ver en el mundo.", "Mahatma Gandhi", ""),
    Quote("La calma viene de dentro. No la busques fuera.", "Buda", ""),
    Quote("Lo que piensas, te conviertes.", "Buda", ""),
    Quote("El verdadero viaje de descubrimiento consiste en buscar nuevos paisajes, no en mirar nuevos lugares.", "Marcel Proust", ""),
    Quote("La mente es todo. Te conviertes en lo que piensas.", "Buda", ""),
    Quote("Quien tiene un porque para vivir puede soportar casi cualquier como.", "Friedrich Nietzsche", "Ecce Homo"),
    Quote("Lo que no me mata, me fortalece.", "Friedrich Nietzsche", "Mas alla del bien y del mal"),
    Quote("La vida se puede entender hacia atras, pero hay que vivirla hacia adelante.", "Soren Kierkegaard", ""),
    Quote("El que pregunta es tonto por un momento. El que no pregunta es tonto para siempre.", "Confucio", ""),
    Quote("Vive como si fueras a morir manana. Aprende como si fueras a vivir siempre.", "Mahatma Gandhi", ""),
]


class StoicQuotes(QuoteProvider):
    def __init__(self, quotes: list[Quote] | None = None):
        self.quotes = quotes or QUOTES

    def is_available(self) -> bool:
        return bool(self.quotes)

    def get_daily_quote(self) -> Quote:
        # Deterministic: same quote for the same UTC day
        idx = datetime.now(timezone.utc).toordinal() % len(self.quotes)
        return self.quotes[idx]


register(StoicQuotes)
