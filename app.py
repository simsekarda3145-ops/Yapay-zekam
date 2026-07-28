import os
import streamlit as st
from groq import Groq

# Sayfa Ayarları
st.set_page_config(page_title="Kanka AI Pro (Groq)", page_icon="🤖", layout="centered")

# Tasarım ve Renk Düzeltmeleri (CSS)
st.markdown("""
    <style>
    /* Ana Sayfa Arka Planı */
    .stApp { 
        background-color: #0e1117 !important; 
        color: #ffffff !important; 
    }
    
    /* Genel Yazı Renkleri */
    h1, h2, h3, p, span, label, div {
        color: #ffffff !important;
    }

    /* Sohbet Mesaj Kutuları */
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

    /* Buton Tasarımları */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        height: 3em; 
        background-color: #1f2937 !important; 
        color: #ffffff !important; 
        border: 1px solid #374151 !important; 
        font-weight: bold; 
    }
    .stButton>button:hover { 
        background-color: #3b82f6 !important; 
        color: #ffffff !important; 
        border-color: #3b82f6 !important; 
    }

    /* Mesaj Giriş Kutusu (Chat Input) */
    .stChatInputContainer input {
        color: #ffffff !important;
        background-color: #1a1f2c !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Kanka AI - Işık Hızında Yapay Zeka")
st.caption("Groq & Llama 3 Altyapısı ile Güçlendirildi 🚀")

# Groq API Bağlantısı
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
