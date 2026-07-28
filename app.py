import os
import streamlit as st
from groq import Groq

# Sayfa Ayarları
st.set_page_config(page_title="Şimşek Zeka ⚡", page_icon="⚡", layout="centered")

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
        background-color: #eab308 !important; 
        color: #000000 !important; 
        border-color: #eab308 !important; 
    }

    /* Mesaj Giriş Kutusu (Chat Input) */
    .stChatInputContainer input {
        color: #ffffff !important;
        background-color: #1a1f2c !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Groq & Llama 3 Altyapısı ile Güçlendirildi 🚀")

# Groq API Bağlantısı
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if api_key:
    client = Groq(api_key=api_key)
else:
    client = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben Şimşek Zeka ⚡ Süper hızlı ve zeki asistanınım. Bugün ne yapmak istersin?"}
    ]

# Hızlı Butonlar
st.write("💡 **Hızlı İpuçları:**")
col1, col2, col3 = st.columns(3)
hizli_mesaj = None

with col1:
    if st.button("🎭 Fıkra Anlat"):
        hizli_mesaj = "Bana komik, kısa bir fıkra anlat kanka!"
with col2:
    if st.button("🎮 Oyun Öner"):
        hizli_mesaj = "Şu an oynayabileceğim harika bir PC/Konsol oyunu önerir misin?"
with col3:
    if st.button("🧠 İlginç Bilgi"):
        hizli_mesaj = "Beni şaşırtacak çok ilginç ve az bilinen bir bilgi ver kanka!"

# Eski Mesajları Göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcı Girdisi
prompt = st.chat_input("Şimşek Zeka'ya bir şeyler sor kanka...") or hizli_mesaj

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Şimşek Zeka düşünüyor... ⚡🧠"):
            if client:
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Senin adın Şimşek Zeka. Sen samimi, eğlenceli ve kullanıcıya her zaman 'kanka' diye hitap eden çok zeki, ışık hızında ve yardımsever bir yapay zeka asistanısın."},
                            *st.session_state.messages
                        ],
                    )
                    cevap = response.choices[0].message.content
                except Exception as e:
                    cevap = f"Ufak bir aksilik oldu kanka: {e}"
            else:
                cevap = "Kanka Groq API key henüz eklenmemiş. Secrets kısmına 'GROQ_API_KEY' ekleyince zekam tam devreye girecek!"

            st.markdown(cevap)
            st.session_state.messages.append({"role": "assistant", "content": cevap})
