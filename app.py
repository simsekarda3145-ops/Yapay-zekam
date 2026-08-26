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

# Sayfa Ayarları
st.set_page_config(page_title="Şimşek Zeka ⚡", page_icon="⚡", layout="centered")

# --- KUSURSUZ EN ALTA SABİTLEME VE + BUTONU HİZALAMA CSS ---
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
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 12px;
        border: 1px solid #2d3748;
    }
    .stChatMessage p {
        color: #f0f2f5 !important;
    }
    
    /* İçerik alttaki sabit çubuğun altında kalmasın diye alt boşluk */
    .main .block-container {
        padding-bottom: 160px !important;
    }

    /* Streamlit Chat Input Alanını En Alta ("Manage app" çubuğunun hemen üzerine) Sabitleme */
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 50px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 92% !important;
        max-width: 700px !important;
        z-index: 99999 !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 24px !important;
        box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.7) !important;
        padding: 4px 8px 4px 45px !important;
    }

    /* stChatInput içindeki metin alanı */
    .stChatInputContainer textarea {
        background: transparent !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* + Butonunu tam chat inputun sol içine kilitleyen CSS */
    button[aria-label="➕"] {
        position: fixed !important;
        bottom: 57px !important;
        left: calc(50% - 325px) !important;
        z-index: 100000 !important;
        background: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        font-size: 18px !important;
        box-shadow: none !important;
    }
    @media (max-width: 768px) {
        button[aria-label="➕"] {
            left: 28px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Groq & Vision AI Altyapısı ile Güçlendirildi 🚀")

# --- DOĞAL VE AKICI MICROSOFT EDGE SES FONKSİYONU ---
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

# Görsel İndirme Fonksiyonu
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

# Görseli Base64'e Dönüştürme
def resim_to_base64(image_file):
    buffered = BytesIO()
    image_file.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Groq API Bağlantısı
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben Şimşek Zeka ⚡ Alttaki '+' butonuna basarak araçları açabilirsin!"}
    ]

# --- + BUTONU VE ARAÇLAR MENÜSÜ ---
with st.popover("➕", help="Araçlar Menüsü"):
    st.markdown("### 🛠️ Şimşek Zeka Araçları")
    st.write("📷 **Fotoğraf Yükle & Analiz Et:**")
    yuklenen_dosya = st.file_uploader("Bir görsel seç veya çek", type=["jpg", "jpeg", "png"])
    
    yuklenen_gorsel_objesi = None
    if yuklenen_dosya:
        yuklenen_gorsel_objesi = Image.open(yuklenen_dosya)
        st.image(yuklenen_gorsel_objesi, caption="Yüklenen Fotoğraf", use_container_width=True)
        st.success("Görsel yüklendi kanka!")

    st.divider()
    if st.button("🎭 Bana Komik Bir Fıkra Anlat"):
        st.session_state.fikra_isteği = "Bana komik bir fıkra anlat kanka!"

# Eski Mesajları Göster
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

# Sohbet Girdisi (En altta "Manage app" çubuğunun hemen üzerinde sabit)
chat_input_text = st.chat_input("Şimşek Zeka'ya sor veya '...çiz' de...")

if "fikra_isteği" in st.session_state and st.session_state.fikra_isteği:
    prompt = st.session_state.fikra_isteği
    st.session_state.fikra_isteği = None
else:
    prompt = chat_input_text

if prompt or ('yuklenen_gorsel_objesi' in locals() and yuklenen_gorsel_objesi is not None):
    girdi_metni = prompt if prompt else "Bu fotoğrafta ne görüyorsun kanka, detaylıca anlatır mısın?"
    
    st.chat_message("user").markdown(girdi_metni)
    st.session_state.messages.append({"role": "user", "content": girdi_metni})

    prompt_lower = girdi_metni.lower()
    gorsel_kelimeleri = ["çiz", "resim", "görsel", "fotoğrafı", "tasarla", "draw", "picture"]
    is_image_request = any(kelime in prompt_lower for kelime in gorsel_kelimeleri)

    active_image = yuklenen_gorsel_objesi if ('yuklenen_gorsel_objesi' in locals() and yuklenen_gorsel_objesi is not None) else None

    with st.chat_message("assistant"):
        # 1. FOTOĞRAF ANALİZ ETME
        if active_image is not None:
            with st.spinner("Şimşek Zeka fotoğrafı inceliyor... 👁️⚡"):
                if client:
                    try:
                        base64_image = resim_to_base64(active_image)
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": f"Sen Şimşek Zeka'sın. Seni Arda Şimşek geliştirdi. Kullanıcıya 'kanka' diye hitap et. Fotoğrafla ilgili şu soruya cevap ver: {girdi_metni}"},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}",
                                            },
                                        },
                                    ],
                                }
                            ],
                        )
                        cevap = response.choices[0].message.content
                    except Exception as e:
                        cevap = f"Görseli incelerken bir sorun oluştu kanka: {e}"
                else:
                    cevap = "Kanka Groq API key eksik olduğu için fotoğrafı okuyamıyorum!"

                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap, "type": "text"})

        # 2. Pekmez Kontrolü
        elif "pekmez" in prompt_lower:
            try:
                img = Image.open("CutPaste_2026-05-26_22-53-22-862.jpg")
                st.image(img, caption="İşte senin pekmez görselin kanka! 🍇", use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": img, "type": "image"})
            except FileNotFoundError:
                hata_msg = "Kanka dosya bulunamadı, GitHub ana dizininde 'CutPaste_2026-05-26_22-53-22-862.jpg' olduğundan emin ol!"
                st.error(hata_msg)
                st.session_state.messages.append({"role": "assistant", "content": hata_msg, "type": "text"})

        # 3. Resim Çizdirme
        elif is_image_request:
            with st.spinner("Şimşek Zeka resmini çiziyor... 🎨⚡"):
                img_data = gorsel_indir_ve_getir(girdi_metni)
                if img_data:
                    st.image(img_data, caption=f"İşte senin için çizdiğim: {girdi_metni}", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": img_data, "type": "image"})
                else:
                    st.error("Kanka resim servisi şu an yoğun, tekrar dene!")

        # 4. Normal Metin Sohbeti
        else:
            with st.spinner("Şimşek Zeka düşünüyor... ⚡🧠"):
                if client:
                    try:
                        temiz_gecmis = [
                            {"role": m["role"], "content": str(m["content"])} 
                            for m in st.session_state.messages if m.get("type") != "image"
                        ]
                        
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
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
                    cevap = "Kanka Groq API key henüz eklenmemiş!"

                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap, "type": "text"})

                if st.button("🔊 Sesli Dinle", key=f"listen_new_{len(st.session_state.messages)}"):
                    audio_html = metni_sese_cevir(cevap)
                    if audio_html:
                        st.components.v1.html(audio_html, height=0)
