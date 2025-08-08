#!/bin/bash

# GPT-OSS:20B Streamlit Chat Startup Script

# Ermittle das Script-Verzeichnis dynamisch
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 GPT-OSS:20B Streamlit Chat starten..."
echo "📁 Arbeitsverzeichnis: $(pwd)"

# Prüfe ob Ollama läuft
echo "📡 Prüfe Ollama-Verbindung..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama ist erreichbar"
else
    echo "❌ Ollama ist nicht erreichbar. Starte Ollama zuerst:"
    echo "   ollama serve"
    exit 1
fi

# Aktiviere virtuelle Umgebung und starte Streamlit
echo "🌟 Starte Streamlit Chat..."

# Prüfe ob virtuelle Umgebung existiert
if [ ! -d ".venv" ]; then
    echo "❌ Virtuelle Umgebung nicht gefunden in $(pwd)"
    echo "   Erstellen Sie zuerst eine virtuelle Umgebung:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Finde einen verfügbaren Port
PORT=8501
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    PORT=$((PORT + 1))
done

echo "📱 Die App wird verfügbar sein unter: http://localhost:$PORT"
echo "🛑 Drücke Ctrl+C zum Beenden"

source .venv/bin/activate
streamlit run app.py --server.port $PORT
