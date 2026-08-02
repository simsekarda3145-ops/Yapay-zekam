import streamlit as st
from PIL import Image

st.title("Yapay Zeka Görsel Oluşturucu")

# Kullanıcıdan metin alma
user_prompt = st.text_input("Ne çizmek istersin?", "")

if st.button("Görsel Oluştur"):
    if user_prompt:
        # KONTROL: Eğer "pekmez" yazıldıysa direkt senin yüklediğin fotoğrafı göster
        if "pekmez" in user_prompt.lower():
            try:
                image = Image.open("pekmez.jpg")
                st.image(image, caption="Özel Pekmez Görseli")
            except FileNotFoundError:
                st.error("pekmez.jpg dosyası bulunamadı! Lütfen GitHub'a bu isimle resmi yükleyin.")
        else:
            # Burası normal yapay zeka kodlarının çalışacağı yer
            st.info("Yapay zeka görseli oluşturuluyor...")
            # Mevcut yapay zeka resim üretme kodların buraya gelecek
