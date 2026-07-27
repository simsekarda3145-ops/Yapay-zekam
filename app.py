import json
import os
import random
import re
import requests
from html.parser import HTMLParser
import streamlit as st

# Sayfa Ayarları
st.set_page_config(page_title="Kanka AI", page_icon="🤖", layout="centered")

# Streamlit Sohbet Geçmişi Hafızası
if "messages" not in st.session_state:
    st.session_state.messages = []

if "baglam" not in st.session_state:
    st.session_state.baglam = {
        "isim": None,
        "son_kategori": None,
        "son_cevap": None,
        "tarih_modu": False,
        "tarih_indeks": 0,
    }

# ------------------------------------------------------------------
# Cevap Havuzu ve Mantık
# ------------------------------------------------------------------
bot_hafizasi = {
    "selamlaşma": ["Ooo selam kanka, hoş geldin!", "Merhaba kanka, naber?", "Yaa kanka hoş geldin!"],
    "hal_hatir": ["Bomba gibiyim kanka, seni sormalı?", "İyiyim be kanka, yuvarlanıp gidiyoruz. Sende ne var ne yok?"],
    "hal_hatir_devam_iyi": ["Süper kanka, bugün ne yapıyorsun bakalım?", "Güzel be kanka, enerjin yerinde!"],
    "hal_hatir_devam_kotu": ["Hadi kanka geçmiş olsun, ne oldu ki?", "Üzülme kanka, anlatırsan rahatlarsın."],
    "anakart_donanim": ["Donanım işleri bizden sorulur kanka! IPX41-D3 falan derken profesör olduk.", "Ooo sistem mi topluyoruz kanka?"],
    "spor": ["Yaa maçı kaçırdım kanka, kim kazandı?", "Spor muhabbeti güzeldir kanka!"],
    "oyun": ["Kanka hangi oyunu oynuyorsun şu aralar?", "Oyun muhabbeti açılmışken, en sevdiğin oyun ne?"],
    "film": ["Kanka son izlediğin film neydi?", "Dizi önerisi lazımsa bana sor kanka!"],
    "ovgu": ["Kralsın kanka!", "Sen bu işi çözmüşsün valla kanka."],
    "bilmiyorum": ["Valla kanka orasını tam anlayamadım, biraz daha açsana?", "Kafam karıştı kanka, başka bir şey konuşalım mı?"],
}

kategori_kelimeleri = [
    ("selamlaşma", ["selam", "merhaba", "sa", "sea", "hey", "hello"]),
    ("hal_hatir", ["nasılsın", "naber", "ne haber", "nasıl gidiyor", "napıyorsun"]),
    ("anakart_donanim", ["anakart", "ram", "fps", "valorant", "ekran kartı", "pc", "bilgisayar"]),
    ("spor", ["fenerbahçe", "galatasaray", "beşiktaş", "maç", "gol", "futbol"]),
    ("oyun", ["oyun", "steam", "ps5", "xbox", "minecraft", "fortnite", "lol"]),
    ("film", ["film", "dizi", "netflix", "sinema"]),
    ("ovgu", ["iyi", "sağol", "teşekkür", "kralsın", "cansın", "eyvallah"]),
]

def matematik_islemi_yap(girdi):
    temiz = girdi.replace("topla", "+").replace("çıkar", "-").replace("çarp", "*").replace("böl", "/").replace("?", "")
    karakterler = [c for c in temiz if c in "0123456789+-*/. "]
    islem = "".join(karakterler).strip()
    if islem and re.fullmatch(r"[0-9.\s]+([+\-*/][0-9.\s]+)+", islem):
        try:
            return f"Kanka hesapladım, o işlemin sonucu: {eval(islem)} yapıyor! 🧠⚡"
        except ZeroDivisionError:
            return "Kanka sıfıra bölünmez ki! 😅"
    return None

def isim_tespit_et(girdi):
    desen = re.search(r"\b(?:ismim|adım)\s+([a-zA-ZğüşıöçĞÜŞİÖÇ]+)", girdi)
    return desen.group(1).capitalize() if desen else None

def cevap_uret(girdi, baglam):
    girdi_alt = girdi.lower()
    
    isim = isim_tespit_et(girdi_alt)
    if isim:
        baglam["isim"] = isim
        return f"Tanıştığıma sevindim {isim} kanka, artık seni hatırlıyorum!"

    mat_sonuc = matematik_islemi_yap(girdi_alt)
    if mat_sonuc:
        return mat_sonuc

    for kat, kelimeler in kategori_kelimeleri:
        if any(k in girdi_alt for k in kelimeler):
            return random.choice(bot_hafizasi[kat])

    return random.choice(bot_hafizasi["bilmiyorum"])

# ------------------------------------------------------------------
# ARAYÜZ (Streamlit Frontend)
# ------------------------------------------------------------------
st.title("🤖 Kanka AI Chatbot")
st.write("Sana özel yapay zekan hazır kanka! İstediğini sorabilirsin.")

# Eski mesajları ekranda göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcıdan mesaj al
if prompt := st.chat_input("Bir şeyler yaz kanka..."):
    # Kullanıcı mesajını ekrana bas ve hafızaya ekle
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Bot cevabını üret
    cevap = cevap_uret(prompt, st.session_state.baglam)

    # Bot cevabını ekrana bas ve hafızaya ekle
    with st.chat_message("assistant"):
        st.markdown(cevap)
    st.session_state.messages.append({"role": "assistant", "content": cevap})
