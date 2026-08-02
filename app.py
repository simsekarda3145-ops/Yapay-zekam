import os
import urllib.parse
import streamlit as st
from groq import Groq
from PIL import Image

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
st.caption("Groq & Pollinations AI Altyapısı ile Güçlendirildi 🚀")

# Görsel Üretim Fonksiyonu
def gorsel_olustur(prompt_text):
    encoded_text = urllib.parse.quote(prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_text}?width=1024&height=1024&nologo=true"
    return image_url

# Groq API Bağlantısı
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if api_key:
    client = Groq(api_key=api_key)
else:
    client = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben Şimşek Zeka ⚡ Sohbet edebilir, sorularını yanıtlayabilir ya da 'Uzayda kedi çiz' dersen sana özel resim çizebilirim!"}
    ]

# Hızlı Butonlar
st.write("💡 **Hızlı İpuçları:**")
col1, col2, col3 = st.columns(3)
hizli_mesaj = None

with col1:
    if st.button("🎭 Fıkra Anlat"):
        hizli_mesaj = "Bana komik, kısa bir fıkra anlat kanka!"
with col2:
    if st.button("🎨 Resim Çizdir"):
        hizli_mesaj = "Siberpunk şehirde uçan kırmızı bir araba çiz"
with col3:
    if st.button("🧠 İlginç Bilgi"):
        hizli_mesaj = "Beni şaşırtacak çok ilginç ve az bilinen bir bilgi ver kanka!"

# Eski Mesajları Göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Şimşek Zeka Çizimi 🎨⚡", use_container_width=True)
        else:
            st.markdown(message["content"])

# Kullanıcı Girdisi
prompt = st.chat_input("Soru sor veya '...çiz' de...") or hizli_mesaj

if prompt:
    # Kullanıcının mesajını ekrana bas ve hafızaya al
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower()
    
    # Görsel İsteği mi Kontrol Et
    gorsel_kelimeleri = ["çiz", "resim", "görsel", "fotoğrafı", "tasarla", "draw", "picture"]
    is_image_request = any(kelime in prompt_lower for kelime in gorsel_kelimeleri)

    with st.chat_message("assistant"):
        # 1. ÖZEL KONTROL: Pekmez yazıldıysa yüklenen görseli göster
        if "pekmez" in prompt_lower:
            try:
                img = Image.open("pekmez.jpg")
                st.image(img, caption="İşte senin pekmez görselin kanka! 🍇", use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": "pekmez.jpg", "type": "image"})
            except FileNotFoundError:
                hata_msg = "Kanka 'pekmez.jpg' dosyasını GitHub'a yüklediğinden emin ol, dosya bulunamadı!"
                st.error(hata_msg)
                st.session_state.messages.append({"role": "assistant", "content": hata_msg, "type": "text"})

        # 2. YAPAY ZEKA İLE RESİM ÇİZME (Görsel Kelimesi Geçiyorsa)
        elif is_image_request:
            with st.spinner("Şimşek Zeka resmini çiziyor... 🎨⚡"):
                resim_linki = gorsel_olustur(prompt)
                st.image(resim_linki, caption=f"İşte senin için çizdiğim: {prompt}", use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": resim_linki, "type": "image"})
                
        # 3. NORMAL SOHBET (Groq API Cevabı)
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
                                {"role": "system", "content": "Senin adın Şimşek Zeka. Sen samimi, eğlenceli ve kullanıcıya her zaman 'kanka' diye hitap eden çok zeki, ışık hızında ve yardımsever bir yapay zeka asistanısın."},
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
