#!/bin/bash
#
# Morning Briefing — One-command installer for Hermes Agent
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Shugar03/hermes-morning-briefing/main/install.sh | bash
#
set -e

REPO="https://github.com/Shugar03/hermes-morning-briefing"
INSTALL_DIR="${HERMES_HOME:-$HOME/.hermes}/morning-briefing"
SKILL_DIR="${HERMES_HOME:-$HOME/.hermes}/skills/autonomous/morning-briefing"
SCRIPT_DIR="${HERMES_HOME:-$HOME/.hermes}/scripts"
CONFIG_DIR="${HERMES_HOME:-$HOME/.hermes}"
CONFIG_FILE="$CONFIG_DIR/morning-briefing.yaml"

AVAILABLE_TOPICS=(
  "AI & Tecnologia"
  "Mercados & Finanzas"
  "Politica & Global"
  "Ciencia & Salud"
  "Startups & Negocios"
  "Desarrollo & Tech"
)

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║         Morning Briefing Installer       ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ── 1. Install code ──
if [ -d "$INSTALL_DIR" ]; then
    echo "  [1/4] Updating existing installation..."
    cd "$INSTALL_DIR" && git pull 2>/dev/null || true
elif [ -d "$(dirname "$0")/src" ]; then
    echo "  [1/4] Installing from local checkout..."
    mkdir -p "$INSTALL_DIR"
    cp -r "$(dirname "$0")/src" "$INSTALL_DIR/"
    cp "$(dirname "$0")/skill/SKILL.md" "$INSTALL_DIR/"
    cp "$(dirname "$0")/README.md" "$INSTALL_DIR/"
else
    echo "  [1/4] Cloning repo..."
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi

# ── 2. Install Hermes skill ──
mkdir -p "$SKILL_DIR"
cp "$INSTALL_DIR/skill/SKILL.md" "$SKILL_DIR/SKILL.md" 2>/dev/null || \
    cp "$INSTALL_DIR/SKILL.md" "$SKILL_DIR/SKILL.md" 2>/dev/null || true
echo "  [2/4] Skill installed"

# ── 3. Install script wrapper ──
mkdir -p "$SCRIPT_DIR"
WRAPPER="$SCRIPT_DIR/morning-briefing.py"
cat > "$WRAPPER" << PYEOF
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '$INSTALL_DIR')
from src.main import main, load_config
cfg_path = '$CONFIG_DIR/morning-briefing.yaml'
cfg = load_config(cfg_path)
html_path = main(cfg)
print(f"HTML saved to {html_path}")
print(f"AUDIO_SCRIPT: {cfg.get('output_audio', '/tmp/morning-briefing-voice.txt')}")
PYEOF
chmod +x "$WRAPPER"
echo "  [3/4] Script installed"

# ── 4. Interactive setup ──
echo ""
echo "  [4/4] Let's configure your briefing!"
echo "  ─────────────────────────────────────"
echo ""

# ── 4a. City ──
read -r -p "  Your city [Salta]: " CITY
CITY="${CITY:-Salta}"

# ── 4b. News topics ──
echo ""
echo "  Pick your news topics (space-separated numbers):"
echo ""
for i in "${!AVAILABLE_TOPICS[@]}"; do
    n=$((i + 1))
    echo "    [$n] ${AVAILABLE_TOPICS[$i]}"
done
echo ""
read -r -p "  Topics [1 2 3]: " TOPIC_INPUT
TOPIC_INPUT="${TOPIC_INPUT:-1 2 3}"

SELECTED_TOPICS=()
for num in $TOPIC_INPUT; do
    idx=$((num - 1))
    if [ "$idx" -ge 0 ] && [ "$idx" -lt "${#AVAILABLE_TOPICS[@]}" ]; then
        SELECTED_TOPICS+=("${AVAILABLE_TOPICS[$idx]}")
    fi
done

# ── 4c. Schedule provider ──
echo ""
echo "  Pick your calendar:"
echo ""
echo "    [1] Notion         ← needs DB ID + API key"
echo "    [2] Google Calendar ← needs OAuth setup (one-time)"
echo "    [3] iCal / ICS     ← needs public calendar URL"
echo "    [4] Obsidian       ← reads markdown from vault"
echo "    [5] Manual         ← edit a simple JSON file"
echo "    [6] Skip           ← no agenda, just weather + news"
echo ""
read -r -p "  Calendar [6]: " SCHEDULE_CHOICE
SCHEDULE_CHOICE="${SCHEDULE_CHOICE:-6}"

# ── 4d. Audio ──
echo ""
read -r -p "  Enable audio briefing? (TTS voice message) [y/N]: " AUDIO_ENABLED
AUDIO_ENABLED="${AUDIO_ENABLED:-n}"

# ── Build config ──
echo ""
echo "  Generating config..."

# News sections YAML
NEWS_YAML=""
for topic in "${SELECTED_TOPICS[@]}"; do
    NEWS_YAML+="    - \"$topic\"\n"
done
# Remove trailing newline
NEWS_YAML="${NEWS_YAML%"${NEWS_YAML##*[![:space:]]}"}"

# Schedule YAML based on choice
case "$SCHEDULE_CHOICE" in
    1) SCHEDULE_YAML="provider: notion-schedule
  notion_key: \"\${NOTION_API_KEY}\"
  db_id: \"\${NOTION_SCHEDULE_DB_ID}\""
       SCHEDULE_NOTE="  # Get your Notion DB ID from your database URL"
       ;;
    2) SCHEDULE_YAML="provider: google-calendar
  credentials_file: \"\${GOOGLE_CREDENTIALS}\""
       SCHEDULE_NOTE="  # Run 'google-oauth setup' after install"
       ;;
    3) SCHEDULE_YAML="provider: ical
  ics_url: \"https://.../basic.ics\""
       SCHEDULE_NOTE="  # Replace with your public ICS feed URL"
       ;;
    4) SCHEDULE_YAML="provider: obsidian
  vault_path: \"~/vault/daily\""
       SCHEDULE_NOTE="  # Path to your Obsidian daily notes folder"
       ;;
    5) SCHEDULE_YAML="provider: manual
  json_path: \"~/.hermes/morning-briefing-schedule.json\""
       SCHEDULE_NOTE="  # Edit the JSON file with your events"
       ;;
    *) SCHEDULE_YAML=""
       SCHEDULE_NOTE=""
       ;;
esac

if [ -z "$SCHEDULE_YAML" ]; then
    SCHEDULE_BLOCK=""
else
    SCHEDULE_BLOCK="schedule:
  $SCHEDULE_YAML
  $SCHEDULE_NOTE"
fi

# Audio YAML
if [[ "$AUDIO_ENABLED" =~ ^[yYsS]$ ]]; then
    AUDIO_BLOCK="audio:
  provider: briefing-audio
  lang: es"
else
    AUDIO_BLOCK=""
fi

cat > "$CONFIG_FILE" << CONFIGEOF
# Morning Briefing — Configuration
# Generated by install.sh on $(date +%Y-%m-%d)
# Edit this file anytime to change your setup

weather:
  provider: open-meteo-weather
  lat: $( [ "$CITY" = "Salta" ] && echo "-24.78" || echo "-34.61" )
  lon: $( [ "$CITY" = "Salta" ] && echo "-65.41" || echo "-58.38" )
  city: $CITY

news:
  provider: google-news-rss
  max_per_section: 5

news_sections:
$NEWS_YAML

$SCHEDULE_BLOCK
$AUDIO_BLOCK

output_html: /tmp/morning-briefing.html
output_audio: /tmp/morning-briefing-voice.txt
CONFIGEOF

echo "  Config saved → $CONFIG_FILE"
echo ""

# ── Summary ──
echo "  ╔══════════════════════════════╗"
echo "  ║  Ready! Your briefing will   ║"
echo "  ║  include:                    ║"
echo "  ║                              ║"
echo "  ║  City: $CITY"
echo "  ║  News: ${SELECTED_TOPICS[*]}"

if [ -n "$SCHEDULE_YAML" ]; then
    echo "  ║  Calendar: configured ✓"
else
    echo "  ║  Calendar: skipped"
fi

if [ -n "$AUDIO_BLOCK" ]; then
    echo "  ║  Audio: enabled ✓"
else
    echo "  ║  Audio: disabled"
fi

echo "  ║                              ║"
echo "  ╚══════════════════════════════╝"
echo ""
echo "  Next steps:"
echo ""

if [ "$SCHEDULE_CHOICE" = "1" ]; then
    echo "    1. Set your Notion env vars:"
    echo "       echo 'export NOTION_API_KEY=ntn_...' >> ~/.bashrc"
    echo "       echo 'export NOTION_SCHEDULE_DB_ID=...' >> ~/.bashrc"
elif [ "$SCHEDULE_CHOICE" = "2" ]; then
    echo "    1. Set up Google Calendar OAuth"
elif [ "$SCHEDULE_CHOICE" = "5" ]; then
    echo "    1. Create ~/.hermes/morning-briefing-schedule.json"
fi

echo "    2. Test: python3 $WRAPPER"
echo "    3. Create cron: tell your Hermes Agent:"
echo "       'crea el cron del morning briefing a las 7 AM'"
echo ""
