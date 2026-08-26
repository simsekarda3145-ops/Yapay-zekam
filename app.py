import os
import urllib.parse
import streamlit as st
from groq import Groq
from PIL import Image
import base64
import requests
from io import BytesIO
import random
import asyncio
import edge_tts

st.set_page_config(page_title="Şimşek Zeka ⚡", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    h1, h2, h3, p, span, label, div { color: #ffffff !important; }
    .stChatMessage {
        background-color: #1a1f2c !important;
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 12px;
        border: 1px solid #2d3748;
    }
    .main .block-container { padding-bottom: 150px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Groq & Vision AI Altyapısı ile Güçlendirildi 🚀")

async def generate_edge_tts(text):
    voice = "tr-TR-AhmetNeural"
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def metni_sese_cevir(text):
    try:
        metin_kisa = text[:300] if len(text) > 300 else text
        audio_bytes = asyncio.run(generate_edge_tts(metin_kisa))
        b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64_audio}">'
    except Exception:
        return None

def gorsel_indir_ve_getir(prompt_text):
    try:
        seed_num = random.randint(1, 1000000)
        encoded_text = urllib.parse.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{encoded_text}?width=1024&height=1024&nologo=true&seed={seed_num}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        return None
    except Exception:
        return None

def resim_to_base64(image_file):
    buffered = BytesIO()
    image_file.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben Şimşek Zeka ⚡ Araçlar butonuna basarak fotoğraf yükleyebilirsin!"}
    ]

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Şimşek Zeka Çizimi 🎨⚡", use_container_width=True)
        else:
            st.markdown(message["content"])
            if message["role"] == "assistant" and isinstance(message["content"], str):
                if st.button("🔊 Sesli Dinle", key=f"listen_{i}"):
                    audio_html = metni_sese_cevir(message["content"])
                    if audio_html:
                        st.components.v1.html(audio_html, height=0)

# Araçlar Menüsü (Alt Input'un Hemen Üstü)
yuklenen_gorsel_objesi = None
with st.popover("➕ Araçlar Menüsü", help="Fotoğraf Yükle veya Hızlı Komut Ver"):
    st.markdown("### 🛠️ Şimşek Zeka Araçları")
    yuklenen_dosya = st.file_uploader("Bir görsel seç veya çek", type=["jpg", "jpeg", "png"])
    if yuklenen_dosya:
        yuklenen_gorsel_objesi = Image.open(yuklenen_dosya)
        st.image(yuklenen_gorsel_objesi, caption="Yüklenen Fotoğraf", use_container_width=True)
        st.success("Görsel yüklendi kanka!")
    
    st.divider()
    if st.button("🎭 Bana Komik Bir Fıkra Anlat"):
        st.session_state.fikra_isteği = "Bana komik bir fıkra anlat kanka!"

# Standart Chat Input (Telefon Klavesindeki Enter %100 Çalışır)
prompt = st.chat_input("Şimşek Zeka'ya sor veya '...çiz' de...")

if "fikra_isteği" in st.session_state and st.session_state.fikra_isteği:
    prompt = st.session_state.fikra_isteği
    st.session_state.fikra_isteği = None

if prompt or yuklenen_gorsel_objesi is not None:
    girdi_metni = prompt if prompt else "Bu fotoğrafta ne görüyorsun kanka?"
    
    st.chat_message("user").markdown(girdi_metni)
    st.session_state.messages.append({"role": "user", "content": girdi_metni})

    prompt_lower = girdi_metni.lower()
    is_image_request = any(k in prompt_lower for k in ["çiz", "resim", "görsel", "tasarla"])

    with st.chat_message("assistant"):
        if yuklenen_gorsel_objesi is not None:
            with st.spinner("Şimşek Zeka fotoğrafı inceliyor... 👁️⚡"):
                if client:
                    try:
                        base64_image = resim_to_base64(yuklenen_gorsel_objesi)
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=[{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": f"Fotoğrafla ilgili şu soruya cevap ver: {girdi_metni}"},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            }]
                        )
                        cevap = response.choices[0].message.content
                    except Exception as e:
                        cevap = f"Hata oluştu kanka: {e}"
                else:
                    cevap = "API Key eksik kanka!"
                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap, "type": "text"})

        elif is_image_request:
            with st.spinner("Şimşek Zeka resmini çiziyor... 🎨⚡"):
                img_data = gorsel_indir_ve_getir(girdi_metni)
                if img_data:
                    st.image(img_data, caption=f"İşte çizim: {girdi_metni}", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": img_data, "type": "image"})
                else:
                    st.error("Resim servisi yoğun kanka!")

        else:
            with st.spinner("Şimşek Zeka düşünüyor... ⚡🧠"):
                if client:
                    try:
                        temiz_gecmis = [{"role": m["role"], "content": str(m["content"])} for m in st.session_state.messages if m.get("type") != "image"]
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=[
                                {"role": "system", "content": "Senin adın Şimşek Zeka. Seni Arda Şimşek geliştirdi. Kullanıcıya 'kanka' diye hitap et."},
                                *temiz_gecmis
                            ]
                        )
                        cevap = response.choices[0].message.content
                    except Exception as e:
                        cevap = f"Hata: {e}"
                else:
                    cevap = "API Key eksik kanka!"
                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap, "type": "text"})
