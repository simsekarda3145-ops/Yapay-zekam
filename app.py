import streamlit as st
from PIL import Image
import requests
import io
import urllib.parse

st.set_page_config(page_title="AI Görsel Oluşturucu", page_icon="🎨")

st.title("🎨 Yapay Zeka Görsel Oluşturucu")

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
        
        # KONTROL 2: Başka Bir Şey Yazıldıysa Yapay Zekaya Çizdir (Pollinations AI)
        else:
            with st.spinner("Yapay zeka görseli çiziyor..."):
                try:
                    # Metni URL formatına çevirip hızlı yapay zeka servisine gönderiyoruz
                    encoded_prompt = urllib.parse.quote(user_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        ai_image = Image.open(io.BytesIO(response.content))
                        st.image(ai_image, caption=f"Yapay Zeka Çizimi: {user_prompt}")
                    else:
                        st.error("Görsel oluşturulamadı, lütfen tekrar dene.")
                except Exception as e:
                    st.error("Bir hata oluştu, lütfen tekrar dene.")
