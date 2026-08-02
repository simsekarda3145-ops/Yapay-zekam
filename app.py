import streamlit as st

st.set_page_config(page_title="Yapay Zeka Asistanı", page_icon="🤖")

# Chat geçmişini başlat
if "messages" not in st.messages:
    st.session_state.messages = [
        {"role": "assistant", "content": "Naber kanka! Ben süper hızlı yapay zeka asistanınım. Ne konuşmak istersin?"}
    ]

# Hızlı Butonlar
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🎭 Fıkra Anlat"):
        st.session_state.messages.append({"role": "user", "content": "Bana komik, kısa bir fıkra anlat kanka!"})
with col2:
    if st.button("🎮 Oyun Öner"):
        st.session_state.messages.append({"role": "user", "content": "Bana oynayacak güzel bir oyun öner kanka!"})
with col3:
    if st.button("🧠 İlginç Bilgi"):
        st.session_state.messages.append({"role": "user", "content": "Bana hiç duymadığım ilginç bir bilgi ver kanka!"})

# Mesajları Ekrana Yazdır
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Kullanıcı Girişi
if prompt := st.chat_input("Bir şeyler yaz kanka..."):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Yapay Zeka Cevabı (Pekmez Kontrolü Burada)
    with st.chat_message("assistant"):
        if "pekmez" in prompt.lower():
            response = "İşte aradığın pekmez görseli kanka!"
            st.write(response)
            try:
                st.image("pekmez.jpg")
            except:
                st.error("pekmez.jpg dosyası bulunamadı!")
        else:
            # Buraya kendi sohbet cevabını ekleyebilirsin
            response = f"Kanka, dediklerini aldım! ('{prompt}' hakkında konuşuyoruz)"
            st.write(response)
            
        st.session_state.messages.append({"role": "assistant", "content": response})
