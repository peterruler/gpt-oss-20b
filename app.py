import streamlit as st
import ollama
import os
from dotenv import load_dotenv
import time
from typing import List, Dict

# Lade Umgebungsvariablen
load_dotenv()

# Konfiguration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")

# Ollama Client initialisieren
client = ollama.Client(host=OLLAMA_HOST)

# Streamlit Konfiguration
st.set_page_config(
    page_title="GPT-OSS:20B Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session():
    """Initialisiere Session State."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'model_available' not in st.session_state:
        st.session_state.model_available = check_model_availability()
    if 'chat_stats' not in st.session_state:
        st.session_state.chat_stats = {
            'total_messages': 0,
            'total_chars': 0,
            'session_start': time.time()
        }

def check_model_availability() -> bool:
    """Prüfe ob das Modell verfügbar ist."""
    try:
        models = client.list()
        available_models = [model['name'] for model in models['models']]
        return OLLAMA_MODEL in available_models
    except Exception as e:
        st.error(f"❌ Fehler beim Verbinden mit Ollama: {e}")
        return False

def get_model_info():
    """Hole Modell-Informationen."""
    try:
        model_info = client.show(OLLAMA_MODEL)
        return model_info
    except Exception:
        return None

def stream_response(messages: List[Dict]) -> str:
    """Generiere Streaming-Antwort von Ollama."""
    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            stream=True,
            options={
                "temperature": st.session_state.get('temperature', 0.7),
                "top_p": 0.9,
                "top_k": 40
            }
        )
        
        full_response = ""
        placeholder = st.empty()
        
        for chunk in response:
            if 'message' in chunk and 'content' in chunk['message']:
                chunk_content = chunk['message']['content']
                full_response += chunk_content
                placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
        return full_response
        
    except Exception as e:
        st.error(f"❌ Fehler beim Generieren der Antwort: {e}")
        return ""

def main():
    """Haupt-UI."""
    initialize_session()
    
    # Header
    st.title("🤖 GPT-OSS:20B Chat")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Einstellungen")
        
        # Modell-Status
        if st.session_state.model_available:
            st.success(f"✅ **{OLLAMA_MODEL}** verfügbar")
            
            # Modell-Info
            if st.button("ℹ️ Modell Info"):
                model_info = get_model_info()
                if model_info:
                    size_gb = model_info.get('size', 0) / (1024**3)
                    st.info(f"""
                    **Modell:** {OLLAMA_MODEL}
                    **Größe:** {size_gb:.1f} GB
                    **Host:** {OLLAMA_HOST}
                    """)
        else:
            st.error(f"❌ **{OLLAMA_MODEL}** nicht verfügbar")
            if st.button("🔄 Modell laden"):
                with st.spinner(f"Lade {OLLAMA_MODEL}..."):
                    try:
                        client.pull(OLLAMA_MODEL)
                        st.session_state.model_available = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Laden: {e}")
        
        # Parameter
        st.subheader("🎛️ Parameter")
        temperature = st.slider("Temperatur", 0.0, 2.0, 0.7, 0.1)
        st.session_state['temperature'] = temperature
        
        # Chat-Aktionen
        st.subheader("💬 Chat-Aktionen")
        if st.button("🗑️ Chat löschen"):
            st.session_state.messages = []
            st.session_state.chat_stats = {
                'total_messages': 0,
                'total_chars': 0,
                'session_start': time.time()
            }
            st.rerun()
        
        # Chat-Statistiken
        st.subheader("📊 Statistiken")
        stats = st.session_state.chat_stats
        duration = time.time() - stats['session_start']
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        st.metric("Nachrichten", stats['total_messages'])
        st.metric("Zeichen", f"{stats['total_chars']:,}")
        st.metric("Dauer", f"{minutes}m {seconds}s")
    
    # Haupt-Chat-Bereich
    if not st.session_state.model_available:
        st.warning(f"""
        ⚠️ **Modell {OLLAMA_MODEL} nicht verfügbar**
        
        **Schritte zur Lösung:**
        1. Stellen Sie sicher, dass Ollama läuft: `ollama serve`
        2. Laden Sie das Modell: `ollama pull {OLLAMA_MODEL}`
        3. Klicken Sie auf "🔄 Modell laden" in der Sidebar
        """)
        return
    
    # Chat-Verlauf anzeigen
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat-Input
    if prompt := st.chat_input("Ihre Nachricht..."):
        # Benutzer-Nachricht hinzufügen
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Benutzer-Nachricht anzeigen
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI-Antwort generieren
        with st.chat_message("assistant"):
            with st.spinner("Denke nach..."):
                # System-Prompt hinzufügen
                messages_for_api = [
                    {"role": "system", "content": "Du bist ein hilfsbereit AI-Assistent. Antworte höflich und informativ auf Deutsch."}
                ]
                messages_for_api.extend(st.session_state.messages)
                
                response = stream_response(messages_for_api)
                
                if response:
                    # Antwort zur Session hinzufügen
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Statistiken aktualisieren
                    st.session_state.chat_stats['total_messages'] += 1
                    st.session_state.chat_stats['total_chars'] += len(prompt) + len(response)

if __name__ == "__main__":
    main()
