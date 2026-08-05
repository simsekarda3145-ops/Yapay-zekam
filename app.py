import os
import urllib.parse
import streamlit as st
from groq import Groq
from PIL import Image
from gtts import gTTS
import base64
import requests
from io import BytesIO
from streamlit_mic_recorder import speech_to_text

# Sayfa Ayarları
st.set_page_config(page_title="Şimşek Zeka ⚡", page_icon="⚡", layout="centered")

# CSS Tasarımı (Karanlık Tema)
st.markdown("""
    <style>
    .stApp { 
        background-color: #0e1117 !important; 
        color: #ffffff !important; 
    }
    h1, h2, h3, p, span, label, div {
        color: #ffffff !important;
    }
    .stChatMessage {
        background-color: #1a1f2c !important;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #2d3748;
    }
    .stChatMessage p {
        color: #f0f2f5 !important;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        height: 2.8em; 
        background-color: #1f2937 !important; 
        color: #ffffff !important; 
        border: 1px solid #374151 !important; 
        font-weight: bold; 
    }
    .stButton>button:hover { 
        background-color: #eab308 !important; 
        color: #000000 !important; 
        border-color: #eab308 !important; 
    }
    .stChatInputContainer input {
        color: #ffffff !important;
        background-color: #1a1f2c !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Groq & Voice AI Altyapısı ile Güçlendirildi 🚀")

# Ses Oluşturma Fonksiyonu
def metni_sese_cevir(text):
    try:
        tts = gTTS(text=text, lang='tr')
        tts.save("response.mp3")
        with open("response.mp3", "rb") as f:
            audio_bytes = f.read()
        b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64_audio}">'
    except Exception:
        return None

# Görsel İndirme Fonksiyonu
def gorsel_indir_ve_getir(prompt_text):
    try:
        encoded_text = urllib.parse.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{encoded_text}?width=1024&height=1024&nologo=true"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        return None
    except Exception:
        return None

# Groq API Bağlantısı
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben Şimşek Zeka ⚡ '+ ' butonuna basarak foto yükleyebilir veya sesli konuşabilirsin!"}
    ]

# Eski Mesajları Göster
for message in st.session_state
