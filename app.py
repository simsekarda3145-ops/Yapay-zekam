import streamlit as st
from PIL import Image

# === SENİN ORİJİNAL KODLARIN BURADAN BAŞLIYOR ===
st.title("Yapay Zeka Görsel Oluşturucu")

user_prompt = st.text_input("Ne çizmek istersin?")

if st.button("Görsel Oluştur"):
    if user_prompt:
        
        # === SADECE BU 4 SATIR KONTROLÜ EKLENDİ ===
        if "pekmez" in user_prompt.lower():
            image = Image.open("pekmez.jpg")
            st.image(image)
        else:
            # === BURASI SENİN MEVCUT YAPAY ZEKA ÇAĞRI KODUN ===
            # Eskiden yapay zekadan resmi nasıl çekiyorsan o kodun buraya gelecek:
            pass 
