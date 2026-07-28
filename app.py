import streamlit as st
from google import genai

# Sayfa Konfigürasyonu (Koyu Tema ve Başlık)
st.set_page_config(
    page_title="Kanka AI Pro",
    page_icon="🤖",
    layout="centered"
)

# Özel CSS ile Tasarımı Şıklaştırma
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        background-color: #262730;
        color: #ffffff;
        border: 1px solid #4f535a;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #ff4b4b;
        color: white;
        border-color: #ff4b4b;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Kanka AI - Süper Akıllı Asistan")
st.caption("Google Gemini Yapay Zeka Beyni ile Güçlendirildi 🚀")

# Gemini API İstemcisi
# Not: Tam performans için Streamlit Secrets'a 'GEMINI_API_KEY' ekleyebilirsin.
try:
    client = genai.Client()
except Exception:
    client = None

# Sohbet Geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben senin süper akıllı yapay zeka asistanınım. Ne sormak istersin?"}
    ]

# Hızlı Sorular / Butonlar
st.write("💡 **Hızlı İpuçları:**")
col1, col2, col3 = st.columns(3)

hizli_mesaj = None
with col1:
    if st.button("🎭 Fıkra Anlat"):
        hizli_mesaj = "Bana komik, kısa bir fıkra anlat kanka!"
with col2:
    if st.button("🎮 Oyun Önerisi"):
        hizli_mesaj = "Şu an oynayabileceğimi düşündüğün harika bir PC/Konsol oyunu önerir misin?"
with col3:
    if st.button("🧠 İLGİNÇ BİLGİ"):
        hizli_mesaj = "Beni şaşırtacak çok ilginç ve az bilinen bir bilgi ver kanka!"

# Eski Mesajları Listele
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcı Girdisi (Arama kutusu veya Buton tıklaması)
prompt = st.chat_input("Bir şeyler yaz kanka...") or hizli_mesaj

if prompt:
    # Kullanıcı mesajını ekrana ekle
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Yapay Zeka Cevabı Üret
    with st.chat_message("assistant"):
        with st.spinner("Düşünüyorum kanka... 🧠"):
            if client:
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"Sen samimi, eğlenceli ve 'kanka' diye hitap eden bir yapay zeka asistanısın. Kullanıcının sorusu: {prompt}",
                    )
                    cevap = response.text
                except Exception as e:
                    cevap = f"Ufak bir aksilik oldu kanka: {e}"
            else:
                cevap = "Kanka Gemini API anahtarın henüz tanımlı değil. Streamlit Cloud ayarlarından GEMINI_API_KEY ekleyince gerçek yapay zeka beyni devreye girecek!"

            st.markdown(cevap)
            st.session_state.messages.append({"role": "assistant", "content": cevap})
