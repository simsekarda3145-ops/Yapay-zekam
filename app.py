import streamlit as st
import requests
import io
import urllib.parse
from PIL import Image

# Sayfa başlığı
st.title("Yapay Zeka Görsel Oluşturucu")

# Kullanıcıdan girdi alma
user_prompt = st.text_input("Ne çizmek istersin?", "")

if st.button("Görsel Oluştur"):
    if user_prompt:
        
        # 1. KONTROL: Pekmez yazıldıysa yüklediğin fotoğrafı gösterir
        if "pekmez" in user_prompt.lower():
            try:
                image = Image.open("pekmez.jpg")
                st.image(image, caption="Pekmez Görseli")
            except FileNotFoundError:
                st.error("pekmez.jpg dosyası bulunamadı! GitHub'a 'pekmez.jpg' adıyla yüklediğinden emin ol.")
        
        # 2. KONTROL: Başka bir şey yazıldıysa Yapay Zeka resim çizer
        else:
            with st.spinner("Yapay zeka görseli çiziyor..."):
                try:
                    # Hızlı ve ücretsiz yapay zeka servisi
                    encoded_prompt = urllib.parse.quote(user_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        ai_image = Image.open(io.BytesIO(response.content))
                        st.image(ai_image, caption=f"Çizilen: {user_prompt}")
                    else:
                        st.error("Resim oluşturulurken bir hata oluştu, tekrar dene.")
                except Exception as e:
                    st.error("Bir bağlantı hatası oluştu.")
