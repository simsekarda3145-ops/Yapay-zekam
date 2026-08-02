import streamlit as st
from PIL import Image

st.set_page_config(page_title="Yapay Zeka Asistanı", page_icon="🤖")

# Sohbet geçmişini başlat (Hata burada düzeltildi: st.session_state kullanıldı)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben süper hızlı yapay zeka asistanınım. Ne konuşmak istersin?"}
    ]

# Ekranın üstündeki hızlı butonlar
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🎭 Fıkra Anlat"):
        st.session_state.messages.append({"role": "user", "content": "Bana komik, kısa bir fıkra anlat kanka!"})
        st.session_state.messages.append({"role": "assistant", "content": "Kanka, dinle! Bir adam doktora gider ve diyor ki: 'Doktor bey, uykum çok sık geliyor, ne yapayım?' Doktor da diyor ki: 'Uyumak için bir çare bulunamaz, ama ben size bir reçete yazıcam, uyanmanız için!' Howahaha, güldün mü kanka?"})

with col2:
    if st.button("🎮 Oyun Öner"):
        st.session_state.messages.append({"role": "user", "content": "Bana oynayacak güzel bir oyun öner kanka!"})
        st.session_state.messages.append({"role": "assistant", "content": "Kanka kesinlikle Red Dead Redemption 2 veya Witcher 3 oynamalısın, hikayeleri efsanedir!"})

with col3:
    if st.button("🧠 İlginç Bilgi"):
        st.session_state.messages.append({"role": "user", "content": "Bana hiç duymadığım ilginç bir bilgi ver kanka!"})
        st.session_state.messages.append({"role": "assistant", "content": "Kanka biliyor muydun? Ahtapotların tam 3 tane kalbi vardır!"})

# Sohbet geçmişini ekrana basma
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "image" in message:
            st.image(message["image"])

# Alt taraftaki mesaj yazma kutusu
if prompt := st.chat_input("Bir şeyler yaz kanka..."):
    # Kullanıcının yazdığını ekrana ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Cevap oluşturma (Pekmez kontrolü)
    with st.chat_message("assistant"):
        if "pekmez" in prompt.lower():
            res = "İşte aradığın pekmez kanka!"
            st.write(res)
            try:
                img = Image.open("pekmez.jpg")
                st.image(img)
                st.session_state.messages.append({"role": "assistant", "content": res, "image": img})
            except FileNotFoundError:
                st.error("pekmez.jpg bulunamadı! Lütfen GitHub'a bu isimle yükle.")
        else:
            res = f"Anladım kanka! '{prompt}' hakkında konuşuyoruz. Başka ne öğrenmek istersin?"
            st.write(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
