# Morning Briefing para Hermes Agent 🐝

**Tu dosis diaria de clima + agenda + deadlines + noticias + audio, directo a Telegram.**

Un pipeline modular que corre todas las mananas a las 7 AM y te entrega un HTML con diseno oscuro + una burbuja de voz con el resumen.

## Una linea lo instala

```bash
curl -fsSL https://raw.githubusercontent.com/Shugar03/hermes-morning-briefing/main/install.sh | bash
```

## Que trae

| Componente | Provider por defecto | Alternativas |
|---|---|---|
| Clima | Open-Meteo (gratis, sin key) | Cualquier ciudad |
| Agenda | Notion DB | Google Calendar, Obsidian, iCal, Manual |
| Deadlines | Notion DB | Misma fuente que agenda |
| Noticias | Google News RSS | 3 secciones: AI/Tech, Mercados, Global |
| Frase estoica | 40 frases rotativas | — |
| Audio (TTS) | Resumen narrado | Edge/OpenAI TTS |
| Diseno | Oscuro premium | — |

## Modo de uso

```bash
# 1. Instalar
curl -fsSL ... | bash

# 2. Configurar
nano ~/.hermes/morning-briefing.yaml

# 3. Probar
python3 ~/.hermes/scripts/morning-briefing.py

# 4. Crear cron (decile a tu Hermes)
# "crea el cron del morning briefing a las 7 AM"
```

## Arquitectura

```
                       ┌──────────────────┐
                       │   config.yaml    │
                       └────────┬─────────┘
                                │
  ┌──────────┐  ┌──────────┐  ┌▼──────────┐  ┌──────────┐
  │ Weather  │  │ Schedule │  │   main.py │  │  News    │
  │ Provider │  │ Provider │  │ Orq estra │  │ Provider │
  └──────────┘  └──────────┘  └────┬──────┘  └──────────┘
                                   │
                          ┌────────▼────────┐
                          │   builder.py    │
                          │   template.html  │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              ┌─────▼─────┐               ┌──────▼──────┐
              │  HTML doc │               │  Audio TTS  │
              │  Telegram │               │  Telegram   │
              └───────────┘               └─────────────┘
```

## Para desarrolladores

Agregar un provider nuevo = escribir una clase + decorador `@register`:

```python
from src.providers import ScheduleProvider, Schedule, register

class TodoistSchedule(ScheduleProvider):
    def get_events_today(self) -> Schedule:
        # tu logica aca
        ...

register(TodoistSchedule)
```

## Tecnologias

- Python 3.12+
- Solo stdlib + PyYAML
- Open-Meteo API (gratis)
- Google News RSS
- Notion API / Google Calendar API / archivos locales
- Hermes Agent TTS

## Creditos

Creado por [@Shugar03](https://x.com/TheShugarBoy) para [Salta Dev](https://github.com/salta-dev) y la comunidad Hermes Agent.
