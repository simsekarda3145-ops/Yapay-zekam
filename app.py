import streamlit as st
from PIL import Image
import requests
import io

st.title("Yapay Zeka Görsel Oluşturucu")

# Hugging Face ücretsiz görsel üretme API adresi
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

def ai_resim_ureti(prompt):
    payload = {"inputs": prompt}
    response = requests.post(API_URL, json=payload)
    if response.status_code == 200:
        image_bytes = response.content
        return Image.open(io.BytesIO(image_bytes))
    else:
        return None

user_prompt = st.text_input("Ne çizmek istersin?", "")

if st.button("Görsel Oluştur"):
    if user_prompt:
        # KONTROL 1: Pekmez Yazıldıysa Özel Fotoğrafı Göster
        if "pekmez" in user_prompt.lower():
            try:
                image = Image.open("pekmez.jpg")
                st.image(image, caption="Özel Pekmez Görseli")
            except FileNotFoundError:
                st.error("pekmez.jpg dosyası bulunamadı! Lütfen GitHub'a bu isimle resmi yükleyin.")
        
        # KONTROL 2: Başka Bir Şey Yazıldıysa Yapay Zekaya Çizdir
        else:
            with st.spinner("Yapay zeka görseli çiziyor, lütfen bekle..."):
                ai_image = ai_resim_ureti(user_prompt)
                if ai_image:
                    st.image(ai_image, caption=f"Çizilen: {user_prompt}")
                else:
                    st.error("Yapay zeka şu an yoğun, lütfen birkaç saniye sonra tekrar dene!")
