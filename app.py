import random
import re
import streamlit as st

# Sayfa Ayarları (Koyu Tema & Başlık)
st.set_page_config(
    page_title="Kanka AI Pro",
    page_icon="🤖",
    layout="centered"
)

# Özel CSS ile Şık Tasarım
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #1f2937;
        color: #ffffff;
        border: 1px solid #374151;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Kanka AI - Akıllı Asistan")
st.caption("Kendi Özel Konuşma & Öneri Motoru ile Çalışıyor 🚀")

# Hafıza Tarafı
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben senin akıllı asistanınım. Ne konuşalım bugün?"}
    ]

# Bilgi ve Cevap Havuzları
fikralar = [
    "Temel bir gün uçağa binmiş, yanındaki adama 'Nereye gidiyorsun?' demiş. Adam 'İstanbul'a' demiş. Temel de 'Aaa ne tesadüf, ben de uçağa gidiyorum!' demiş. 😄",
    "İki domates yolda yürüyormuş, biri diğerine 'Dikkat et araba geliyor!' derken... Salça olmuşlar! 🍅😂",
    "Öğretmen Ali'ye sormuş: 'Oğlum 4 kere 5 kaç eder?' Ali: '20 eder öğretmenim.' Öğretmen: 'Aferin Ali, al sana 20 puan.' Ali: 'Hocam bilseydim 4 kere 10 derdim!' 🤣"
]

oyunlar = [
    "🎮 **The Witcher 3:** Hikayesi ve dünyasıyla efsanedir, oynamadıysan kesin bak kanka!",
    "🎮 **Valorant / CS2:** Arkadaşlarla girmelik, rekabetçi seviyorsan tam senlik.",
    "🎮 **Minecraft:** Kafa dinlemelik, bir şeyler inşa etmelik zamansız klasiktir kanka.",
    "🎮 **Red Dead Redemption 2:** Grafikleri ve detayları seni bilgisayar başına kilitler!"
]

ilginç_bilgiler = [
    "🧠 **Biliyor muydun?** Ahtapotların 3 tane kalbi ve mavi kanı vardır!",
    "🧠 **Şaşırtıcı Bilgi:** Muzlar teknik olarak birer meyve değil, devasa otsu bitkilerin meyvesidir!",
    "🧠 **Uzay Bilgisi:** Venüs'te bir gün, bir yıldan daha uzun sürer!"
]

bot_hafizasi = {
    "selamlaşma": ["Ooo selam kanka, hoş geldin!", "Merhaba kanka, naber?", "Yaa kanka hoş geldin!"],
    "hal_hatir": ["Bomba gibiyim kanka, seni sormalı?", "İyiyim be kanka, yuvarlanıp gidiyoruz. Sende ne var ne yok?"],
    "anakart_donanim": ["Donanım işleri bizden sorulur kanka!", "Ooo sistem mi topluyoruz kanka? Ekran kartı ne alıyoruz?"],
    "spor": ["Yaa maçı kaçırdım kanka, kim kazandı?", "Spor muhabbeti güzeldir kanka, hangi takımı tutuyorsun?"],
    "ovgu": ["Kralsın kanka!", "Sen bu işi çözmüşsün valla kanka."],
    "bilmiyorum": ["Valla kanka orasını tam anlayamadım, biraz daha açsana?", "Kafam karıştı kanka, başka bir şey mi konuşsak?"]
}

def matematik_islemi_yap(girdi):
    temiz = girdi.replace("topla", "+").replace("çıkar", "-").replace("çarp", "*").replace("böl", "/").replace("?", "")
    karakterler = [c for c in temiz if c in "0123456789+-*/. "]
    islem = "".join(karakterler).strip()
    if islem and re.fullmatch(r"[0-9.\s]+([+\-*/][0-9.\s]+)+", islem):
        try:
            return f"Kanka hesapladım, sonucun: {eval(islem)} yapıyor! 🧠⚡"
        except ZeroDivisionError:
            return "Kanka sıfıra bölünmez ki! 😅"
    return None

def cevap_uret(girdi):
    girdi_alt = girdi.lower()

    if "fıkra" in girdi_alt:
        return random.choice(fikralar)
    if "oyun" in girdi_alt:
        return random.choice(oyunlar)
    if "bilgi" in girdi_alt or "ilginç" in girdi_alt:
        return random.choice(ilginç_bilgiler)

    mat_sonuc = matematik_islemi_yap(girdi_alt)
    if mat_sonuc:
        return mat_sonuc

    if any(k in girdi_alt for k in ["selam", "merhaba", "sa", "hey"]):
        return random.choice(bot_hafizasi["selamlaşma"])
    if any(k in girdi_alt for k in ["nasılsın", "naber", "ne haber"]):
        return random.choice(bot_hafizasi["hal_hatir"])
    if any(k in girdi_alt for k in ["pc", "ram", "ekran kartı", "fps"]):
        return random.choice(bot_hafizasi["anakart_donanim"])
    if any(k in girdi_alt for k in ["maç", "gol", "futbol", "takım"]):
        return random.choice(bot_hafizasi["spor"])

    return random.choice(bot_hafizasi["bilmiyorum"])

# Hızlı Butonlar
st.write("💡 **Hızlı İpuçları:**")
col1, col2, col3 = st.columns(3)

hizli_mesaj = None
with col1:
    if st.button("🎭 Fıkra Anlat"):
        hizli_mesaj = "Bana bir fıkra anlat kanka"
with col2:
    if st.button("🎮 Oyun Öner"):
        hizli_mesaj = "Bana güzel bir oyun öner kanka"
with col3:
    if st.button("🧠 İlginç Bilgi"):
        hizli_mesaj = "Bana ilginç bir bilgi ver kanka"

# Mesaj Geçmişini Ekrana Bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcı Mesaj Girişi
prompt = st.chat_input("Bir şeyler yaz kanka...") or hizli_mesaj

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    cevap = cevap_uret(prompt)

    with st.chat_message("assistant"):
        st.markdown(cevap)
    st.session_state.messages.append({"role": "assistant", "content": cevap})
