import os
import urllib.parse
import streamlit as st
from groq import Groq
from PIL import Image
import base64
import requests
from io import BytesIO
from streamlit_mic_recorder import speech_to_text
import random
import asyncio
import edge_tts
from pypdf import PdfReader
import docx
from duckduckgo_search import DDGS

# Sayfa Ayarları
st.set_page_config(page_title="Şimşek Zeka ⚡", page_icon="⚡", layout="centered")

# --- GELİŞMİŞ CSS VE EN ALTA SABİTLEME ---
st.markdown("""
    <style>
    /* Arka Plan ve Yazı Rengi */
    .stApp { 
        background-color: #0e1117 !important; 
        color: #ffffff !important; 
    }
    h1, h2, h3, p, span, label, div {
        color: #ffffff !important;
    }

    /* Chat Balonları */
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

    /* EN ALT BAR (HAP TASARIMI VE ALT ALANA SABİTLEME) */
    div[data-testid="stHorizontalBlock"]:has(button[aria-label="➕"]) {
        background-color: #1e2430 !important;
        border: 1px solid #374151 !important;
        border-radius: 30px !important;
        padding: 4px 12px !important;
        display: flex !important;
        align-items: center !important;
        position: fixed !important;
        bottom: 20px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 90% !important;
        max-width: 700px !important;
        z-index: 9999 !important;
    }

    /* '+' Butonu Tasarımı */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        font-size: 20px !important;
        padding: 0px !important;
        height: auto !important;
        width: 38px !important;
        box-shadow: none !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
        color: #ffffff !important;
    }

    /* Chat Input Temizleme */
    .stChatInputContainer {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    .stChatInputContainer textarea {
        background: transparent !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
        padding-left: 5px !important;
    }

    /* Chat alanının alt çubuk arkasında kalmaması için alt boşluk */
    .main .block-container {
        padding-bottom: 120px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Groq, Vision AI, Belge Analizi & Canlı İnternet Arama 🚀")

# --- DOĞAL MİKROSOFT EDGE SES FONKSİYONU ---
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

# Belge (PDF, DOCX, TXT) Okuma Fonksiyonu
def belge_oku(uploaded_file):
    try:
        dosya_adi = uploaded_file.name.lower()
        if dosya_adi.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif dosya_adi.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif dosya_adi.endswith(".txt"):
            return uploaded_file.read().decode("utf-8")
    except Exception as e:
        return f"Belge okunurken hata oluştu: {e}"
    return ""

# Canlı İnternet Arama Fonksiyonu
def internette_ara(sorgu):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(sorgu, max_results=3))
            if results:
                arama_özeti = ""
                for r in results:
                    arama_özeti += f"Başlık: {r['title']}\nÖzet: {r['body']}\n\n"
                return arama_özeti
    except Exception:
        return None
    return None

# Groq API Bağlantısı
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben Şimşek Zeka ⚡ '+ ' butonuna basarak foto/belge yükleyebilir, internet araması yapabilir veya sesli konuşabilirsin!"}
    ]

# Eski Mesajları ve Dinleme Butonlarını Göster
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

# --- EKRANIN EN ALTINA SABİTLENMİŞ YAZMA ALANI VE '+' MENÜSÜ ---
ekran_mesaji = None
yuklenen_gorsel_objesi = None
yuklenen_belge_metni = None
web_search_aktif = False

col_plus, col_input = st.columns([1, 8])

with col_plus:
    with st.popover("➕", help="Araçlar & Dosya Yükleme"):
        st.markdown("### 🛠️ Şimşek Araçlar")
        
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

        # 2. Canlı İnternet Arama Switch
        st.write("🌐 **İnternet Arama:**")
        web_search_aktif = st.toggle("Canlı İnternet Arama Özelliği", value=False)

        st.divider()

        # 3. Görsel / Belge Yükleme
        st.write("📁 **Fotoğraf veya Belge Yükle:**")
        yuklenen_dosya = st.file_uploader("Dosya seçin (Görsel, PDF, Word, TXT)", type=["jpg", "jpeg", "png", "pdf", "docx", "txt"])
        
        if yuklenen_dosya:
            dosya_uzantisi = yuklenen_dosya.name.split(".")[-1].lower()
            if dosya_uzantisi in ["jpg", "jpeg", "png"]:
                yuklenen_gorsel_objesi = Image.open(yuklenen_dosya)
                st.image(yuklenen_gorsel_objesi, caption="Yüklenen Fotoğraf", use_container_width=True)
                st.success("Görsel yüklendi kanka!")
            elif dosya_uzantisi in ["pdf", "docx", "txt"]:
                yuklenen_belge_metni = belge_oku(yuklenen_dosya)
                st.success(f"📄 {yuklenen_dosya.name} belgesi okundu!")

        st.divider()
        
        # 4. Hızlı Kısayollar
        if st.button("🎭 Fıkra Anlat"):
            ekran_mesaji = "Bana komik bir fıkra anlat kanka!"

with col_input:
    prompt_input = st.chat_input("Şimşek Zeka'ya sor veya '...çiz' de...")

prompt = prompt_input or ekran_mesaji

if prompt or yuklenen_gorsel_objesi or yuklenen_belge_metni:
    girdi_metni = prompt if prompt else "Bu dosyayı benim için detaylıca inceler misin kanka?"
    
    st.chat_message("user").markdown(girdi_metni)
    st.session_state.messages.append({"role": "user", "content": girdi_metni})

    prompt_lower = girdi_metni.lower()
    gorsel_kelimeleri = ["çiz", "resim", "görsel", "fotoğrafı", "tasarla", "draw", "picture"]
    is_image_request = any(kelime in prompt_lower for kelime in gorsel_kelimeleri)

    with st.chat_message("assistant"):
        # 1. FOTOĞRAF ANALİZ ETME
        if yuklenen_gorsel_objesi is not None:
            with st.spinner("Şimşek Zeka fotoğrafı inceliyor... 👁️⚡"):
                if client:
                    try:
                        base64_image = resim_to_base64(yuklenen_gorsel_objesi)
                        response = client.chat.completions.create(
                            model="llama-3.2-11b-vision-preview",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": f"Sen Şimşek Zeka'sın. Seni Arda Şimşek geliştirdi. Kullanıcıya 'kanka' diye hitap et. Fotoğrafla ilgili şu soruya cevap ver: {girdi_metni}"},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
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

        # 2. PDF / WORD / TXT BELGE ANALİZİ
        elif yuklenen_belge_metni is not None:
            with st.spinner("Şimşek Zeka belgeyi okuyor ve analiz ediyor... 📄⚡"):
                if client:
                    try:
                        metin_ozeti = yuklenen_belge_metni[:6000]
                        sistem_mesaji = f"Kullanıcı sana bir belge yükledi. Belge içeriği şöyle:\n\n{metin_ozeti}\n\nKullanıcının sorusu: {girdi_metni}. Belgeye dayanarak samimi bir dille cevap ver kanka."
                        
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Sen Şimşek Zeka'sın. Seni Arda Şimşek geliştirdi. Kullanıcıya 'kanka' diye hitap et."},
                                {"role": "user", "content": sistem_mesaji}
                            ],
                        )
                        cevap = response.choices[0].message.content
                    except Exception as e:
                        cevap = f"Belgeyi analiz ederken bir hata oluştu kanka: {e}"
                else:
                    cevap = "Kanka Groq API key eksik!"

                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap, "type": "text"})

        # 3. Pekmez Kontrolü
        elif "pekmez" in prompt_lower:
            try:
                img = Image.open("CutPaste_2026-05-26_22-53-22-862.jpg")
                st.image(img, caption="İşte senin pekmez görselin kanka! 🍇", use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": img, "type": "image"})
            except FileNotFoundError:
                hata_msg = "Kanka dosya bulunamadı, GitHub ana dizininde 'CutPaste_2026-05-26_22-53-22-862.jpg' olduğundan emin ol!"
                st.error(hata_msg)
                st.session_state.messages.append({"role": "assistant", "content": hata_msg, "type": "text"})

        # 4. Resim Çizdirme
        elif is_image_request:
            with st.spinner("Şimşek Zeka resmini çiziyor... 🎨⚡"):
                img_data = gorsel_indir_ve_getir(girdi_metni)
                if img_data:
                    st.image(img_data, caption=f"İşte senin için çizdiğim: {girdi_metni}", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": img_data, "type": "image"})
                else:
                    st.error("Kanka resim servisi şu an yoğun, tekrar dene!")

        # 5. Normal Metin Sohbeti VEYA Canlı İnternet Arama
        else:
            with st.spinner("Şimşek Zeka düşünüyor... ⚡🧠"):
                if client:
                    try:
                        ek_bilgi = ""
                        if web_search_aktif:
                            arama_sonucu = internette_ara(girdi_metni)
                            if arama_sonucu:
                                ek_bilgi = f"\n\n[İnternet Arama Sonuçları]:\n{arama_sonucu}\nBu bilgileri kullanarak kullanıcıya güncel cevap ver."

                        temiz_gecmis = [
                            {"role": m["role"], "content": str(m["content"])} 
                            for m in st.session_state.messages if m.get("type") != "image"
                        ]
                        
                        if ek_bilgi:
                            temiz_gecmis[-1]["content"] += ek_bilgi

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
                    cevap = "Kanka Groq API key henüz eklenmemiş!"

                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap, "type": "text"})

                if st.button("🔊 Sesli Dinle", key=f"listen_new_{len(st.session_state.messages)}"):
                    audio_html = metni_sese_cevir(cevap)
                    if audio_html:
                        st.components.v1.html(audio_html, height=0)
