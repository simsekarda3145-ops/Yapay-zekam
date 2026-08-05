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
import random # Rastgele sayı için ekledik

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

# Geliştirilmiş Görsel İndirme Fonksiyonu (Daha Kararlı)
def gorsel_indir_ve_getir(prompt_text):
    try:
        # Her istek için rastgele bir seed (tohum) oluşturarak servisin bloklama ihtimalini düşürüyoruz.
        seed_num = random.randint(1, 1000000)
        encoded_text = urllib.parse.quote(prompt_text)
        # URL'e rastgele tohum numarasını (&seed=...) olarak ekledik
        url = f"https://image.pollinations.ai/prompt/{encoded_text}?width=1024&height=1024&nologo=true&seed={seed_num}"
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
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Şimşek Zeka Çizimi 🎨⚡", use_container_width=True)
        else:
            st.markdown(message["content"])

# --- GEMINI USULÜ '+' MENÜSÜ ---
ekran_mesaji = None

col_plus, col_input = st.columns([1, 6])

with col_plus:
    with st.popover("➕", help="Araçlar ve Özellikler"):
        st.markdown("### 🛠️ Araçlar")
        
        # 1. Sesli Dinleme
        st.write("🎙️ **Sesli Konuş:**")
        sesli_girdi = speech_to_text(
            language='tr', 
            start_prompt="🎙️ Mikrofona Bas", 
            stop_prompt="⏹️ Durdur", 
            just_once=True,
            key='STT_POP'
        )
        if sesli_girdi:
            ekran_mesaji = sesli_girdi
            
        st.divider()

        # 2. Görsel Yükleme / Kamera
        st.write("📷 **Fotoğraf Yükle:**")
        yuklenen_dosya = st.file_uploader("Bir görsel seç veya çek", type=["jpg", "jpeg", "png"])
        if yuklenen_dosya:
            img = Image.open(yuklenen_dosya)
            st.image(img, caption="Yüklenen Fotoğraf", use_container_width=True)
            st.success("Görsel yüklendi kanka!")

        st.divider()

        # 3. Sesli Yanıt Aç/Kapa
        sesli_cevap_aktif = st.toggle("🔊 Sesli Cevap Verilsin mi?", value=True)

        st.divider()
        
        # 4. Hızlı Kısayollar
        if st.button("🎭 Fıkra Anlat"):
            ekran_mesaji = "Bana komik bir fıkra anlat kanka!"

# Normal Chat Girişi
with col_input:
    prompt_input = st.chat_input("Şimşek Zeka'ya sor veya '...çiz' de...")

prompt = prompt_input or ekran_mesaji

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower()
    gorsel_kelimeleri = ["çiz", "resim", "görsel", "fotoğrafı", "tasarla", "draw", "picture"]
    is_image_request = any(kelime in prompt_lower for kelime in gorsel_kelimeleri)

    with st.chat_message("assistant"):
        # 1. Pekmez Kontrolü (Yazınca Otomatik Çalışır)
        if "pekmez" in prompt_lower:
            try:
                img = Image.open("CutPaste_2026-05-26_22-53-22-862.jpg")
                st.image(img, caption="İşte senin pekmez görselin kanka! 🍇", use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": img, "type": "image"})
            except FileNotFoundError:
                hata_msg = "Kanka dosya bulunamadı, GitHub ana dizininde 'CutPaste_2026-05-26_22-53-22-862.jpg' olduğundan emin ol!"
                st.error(hata_msg)
                st.session_state.messages.append({"role": "assistant", "content": hata_msg, "type": "text"})

        # 2. Resim Çizdirme (Yeni Geliştirilmiş Fonksiyonu Kullanıyoruz)
        elif is_image_request:
            with st.spinner("Şimşek Zeka resmini çiziyor... 🎨⚡"):
                img_data = gorsel_indir_ve_getir(prompt)
                if img_data:
                    st.image(img_data, caption=f"İşte senin için çizdiğim: {prompt}", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": img_data, "type": "image"})
                else:
                    # Hata mesajını biraz daha samimi hale getirdik
                    st.error("Kanka resim servisi şu an çok yoğun, tıkandı kaldı! 😫 Birkaç saniye sonra tekrar deneyelim.")

        # 3. Normal Sohbet
        else:
            with st.spinner("Şimşek Zeka düşünüyor... ⚡🧠"):
                if client:
                    try:
                        temiz_gecmis = [
                            {"role": m["role"], "content": str(m["content"])} 
                            for m in st.session_state.messages if m.get("type") != "image"
                        ]
                        
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "Senin adın Şimşek Zeka. Seni Arda Şimşek geliştirdi ve oluşturdu. Seni kim yaptı, kim tasarladı, geliştiricin kim gibi sorular sorulduğunda gururla seni Arda Şimşek'in yaptığını söyle. Sen samimi, eğlenceli ve kullanıcıya her zaman 'kanka' diye hitap eden çok zeki, ışık hızında ve yardımsever bir yapay zeka asistanısın."
                                },
                                *temiz_gecmis
                            ],
                        )
                        cevap = response.choices[0].message.content
                    except Exception as e:
                        cevap = f"Ufak bir aksilik oldu kanka: {e}"
                else:
                    cevap = "Kanka Groq API key henüz eklenmemiş. Secrets kısmına 'GROQ_API_KEY' ekleyince zekam tam devreye girecek!"

                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap, "type": "text"})

                if 'sesli_cevap_aktif' in locals() and sesli_cevap_aktif and cevap:
                    audio_html = metni_sese_cevir(cevap)
                    if audio_html:
                        st.components.v1.html(audio_html, height=0)
