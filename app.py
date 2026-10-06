import os
import time
import urllib.parse
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import base64
import requests
from io import BytesIO
import random
import asyncio
import edge_tts

# --------------------------------------------------
# SAYFA AYARLARI
# --------------------------------------------------

st.set_page_config(
    page_title="Şimşek Zeka ⚡",
    page_icon="⚡",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background-color: #0e1117 !important;
    color: #ffffff !important;
}

h1, h2, h3, p, span, label, div {
    color: #ffffff !important;
}

.stChatMessage {
    background-color: #1a1f2c !important;
    border-radius: 16px;
    padding: 12px 16px;
    margin-bottom: 12px;
    border: 1px solid #2d3748;
}

.main .block-container {
    padding-bottom: 200px !important;
}

div[data-testid="stPopover"] {
    position: fixed !important;
    bottom: 125px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: auto !important;
    max-width: 220px !important;
    z-index: 99999 !important;
}

div[data-testid="stPopover"] > button {
    width: 100% !important;
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 20px !important;
    color: #00f2fe !important;
    font-weight: bold !important;
    padding: 4px 12px !important;
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Şimşek Zeka AI Altyapısı ile Güçlendirildi 🚀")


# --------------------------------------------------
# SES SİSTEMİ
# --------------------------------------------------

async def generate_edge_tts(text):
    voice = "tr-TR-AhmetNeural"

    communicate = edge_tts.Communicate(
        text,
        voice
    )

    audio_data = b""

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]

    return audio_data


def metni_sese_cevir(text):
    try:
        metin_kisa = text[:300]

        audio_bytes = asyncio.run(
            generate_edge_tts(metin_kisa)
        )

        b64_audio = base64.b64encode(
            audio_bytes
        ).decode("utf-8")

        return (
            f'<audio autoplay="true" '
            f'src="data:audio/mp3;base64,{b64_audio}">'
        )

    except Exception:
        return None


# --------------------------------------------------
# GÖRSEL OLUŞTURMA
# --------------------------------------------------

def gorsel_indir_ve_getir(prompt_text):

    try:
        seed_num = random.randint(1, 1000000)

        encoded_text = urllib.parse.quote(
            prompt_text
        )

        url = (
            "https://image.pollinations.ai/prompt/"
            f"{encoded_text}"
            "?width=1024"
            "&height=1024"
            "&nologo=true"
            f"&seed={seed_num}"
        )

        response = requests.get(
            url,
            timeout=15
        )

        if response.status_code == 200:
            return Image.open(
                BytesIO(response.content)
            )

        return None

    except Exception:
        return None


# --------------------------------------------------
# GEMINI BAĞLANTISI
# --------------------------------------------------

api_key = (
    st.secrets.get("GEMINI_API_KEY")
    or os.getenv("GEMINI_API_KEY")
)

client = (
    genai.Client(api_key=api_key)
    if api_key
    else None
)


# --------------------------------------------------
# GEMINI CEVAP SİSTEMİ
# --------------------------------------------------

def gemini_cevap_al(contents_data):

    if not client:
        return "Gemini API Key bulunamadı kanka! ⚠️"

    # Güncel ve güvenilir model sıralaması
    denenecek_modeller = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite"
    ]

    for model_adi in denenecek_modeller:

        for deneme in range(2):

            try:

                response = client.models.generate_content(
                    model=model_adi,
                    contents=contents_data
                )

                if response and response.text:
                    return response.text

            except Exception as e:

                hata = str(e).lower()

                # Geçici sunucu / kota problemleri
                gecici_hata = (
                    "503",
                    "unavailable",
                    "429",
                    "timeout",
                    "deadline",
                    "resource exhausted"
                )

                if any(
                    kelime in hata
                    for kelime in gecici_hata
                ):

                    if deneme == 0:
                        time.sleep(1)
                        continue

                # Model bulunamadıysa
                if (
                    "not found" in hata
                    or "404" in hata
                ):
                    break

                break

    return (
        "Şu an yapay zekâ sunucularına "
        "bağlanamadım kanka. ⚡\n\n"
        "Birkaç saniye sonra tekrar dener misin?"
    )


# --------------------------------------------------
# MESAJ GEÇMİŞİ
# --------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Naber kanka! Ben Şimşek Zeka ⚡ "
                "Buradayım, fotoğraflarını da "
                "inceleyebilirim!"
            )
        }
    ]


# --------------------------------------------------
# ESKİ MESAJLARI GÖSTER
# --------------------------------------------------

for i, message in enumerate(
    st.session_state.messages
):

    with st.chat_message(message["role"]):

        if message.get("type") == "image":

            if (
                isinstance(
                    message["content"],
                    str
                )
                and os.path.exists(
                    message["content"]
                )
            ):

                st.image(
                    message["content"],
                    caption="Özel Görsel 🍯⚡",
                    use_container_width=True
                )

            else:

                st.image(
                    message["content"],
                    caption="Şimşek Zeka Çizimi 🎨⚡",
                    use_container_width=True
                )

        else:

            st.markdown(
                message["content"]
            )

            if (
                message["role"] == "assistant"
                and isinstance(
                    message["content"],
                    str
                )
            ):

                if st.button(
                    "🔊 Sesli Dinle",
                    key=f"listen_{i}"
                ):

                    audio_html = metni_sese_cevir(
                        message["content"]
                    )

                    if audio_html:
                        st.components.v1.html(
                            audio_html,
                            height=0
                        )


# --------------------------------------------------
# ARAÇLAR
# --------------------------------------------------

yuklenen_gorsel_objesi = None

with st.popover(
    "➕ Araçlar",
    help="Fotoğraf Yükle veya Hızlı Komut Ver"
):

    st.markdown(
        "### 🛠️ Şimşek Zeka Araçları"
    )

    yuklenen_dosya = st.file_uploader(
        "Bir görsel seç veya çek",
        type=["jpg", "jpeg", "png"]
    )

    if yuklenen_dosya:

        yuklenen_gorsel_objesi = Image.open(
            yuklenen_dosya
        )

        st.image(
            yuklenen_gorsel_objesi,
            caption="Yüklenen Fotoğraf",
            use_container_width=True
        )

        st.success(
            "Görsel yüklendi kanka!"
        )

    st.divider()

    if st.button(
        "🎭 Bana Komik Bir Fıkra Anlat"
    ):

        st.session_state.fikra_istegi = (
            "Bana komik bir fıkra anlat kanka!"
        )


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

prompt = st.chat_input(
    "Şimşek Zeka'ya sor veya '...çiz' de..."
)


if (
    "fikra_istegi"
    in st.session_state
    and st.session_state.fikra_istegi
):

    prompt = st.session_state.fikra_istegi

    st.session_state.fikra_istegi = None


# --------------------------------------------------
# MESAJ İŞLEME
# --------------------------------------------------

if (
    prompt
    or yuklenen_gorsel_objesi is not None
):

    girdi_metni = (
        prompt
        if prompt
        else "Bu fotoğrafta ne görüyorsun kanka?"
    )

    st.chat_message(
        "user"
    ).markdown(
        girdi_metni
    )

    st.session_state.messages.append(
        {
            "role": "user",
            "content": girdi_metni
        }
    )

    prompt_lower = girdi_metni.lower()

    is_image_request = any(
        kelime in prompt_lower
        for kelime in [
            "çiz",
            "resim",
            "görsel",
            "tasarla"
        ]
    )


    with st.chat_message("assistant"):

        # --------------------------------------------------
        # 1. FOTOĞRAF ANALİZİ
        # --------------------------------------------------

        if yuklenen_gorsel_objesi is not None:

            with st.spinner(
                "Şimşek Zeka fotoğrafı inceliyor... 👁️⚡"
            ):

                icerik = [
                    yuklenen_gorsel_objesi,
                    (
                        "Senin adın Şimşek Zeka. "
                        "Kullanıcıya samimi şekilde "
                        "'kanka' diye hitap et. "
                        f"Fotoğrafla ilgili soru: {girdi_metni}"
                    )
                ]

                cevap = gemini_cevap_al(
                    icerik
                )

                st.markdown(cevap)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": cevap,
                        "type": "text"
                    }
                )


        # --------------------------------------------------
        # 2. PEKMEZ
        # --------------------------------------------------

        elif "pekmez" in prompt_lower:

            pekmez_dosyasi = "pekmez.jpg"

            if os.path.exists(
                pekmez_dosyasi
            ):

                st.image(
                    pekmez_dosyasi,
                    caption="Özel Pekmez Görseli 🍯⚡",
                    use_container_width=True
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": pekmez_dosyasi,
                        "type": "image"
                    }
                )

            else:

                cevap = (
                    "Kanka 'pekmez' dedin ama "
                    f"`{pekmez_dosyasi}` dosyasını bulamadım."
                )

                st.markdown(cevap)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": cevap,
                        "type": "text"
                    }
                )


        # --------------------------------------------------
        # 3. GÖRSEL OLUŞTURMA
        # --------------------------------------------------

        elif is_image_request:

            with st.spinner(
                "Şimşek Zeka resmini çiziyor... 🎨⚡"
            ):

                img_data = (
                    gorsel_indir_ve_getir(
                        girdi_metni
                    )
                )

                if img_data:

                    st.image(
                        img_data,
                        caption=(
                            f"İşte çizim: "
                            f"{girdi_metni}"
                        ),
                        use_container_width=True
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": img_data,
                            "type": "image"
                        }
                    )

                else:

                    st.error(
                        "Resim servisi şu an yoğun kanka!"
                    )


        # --------------------------------------------------
        # 4. NORMAL SOHBET
        # --------------------------------------------------

        else:

            with st.spinner(
                "Şimşek Zeka düşünüyor... ⚡🧠"
            ):

                system_instruction = (
                    "Senin adın Şimşek Zeka. "
                    "Seni Arda Şimşek geliştirdi. "
                    "Kullanıcıya samimi bir şekilde "
                    "'kanka' diye hitap et."
                )

                prompt_full = (
                    f"{system_instruction}\n\n"
                    f"Kullanıcı: {girdi_metni}"
                )

                cevap = gemini_cevap_al(
                    prompt_full
                )

                st.markdown(cevap)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": cevap,
                        "type": "text"
                    }
                )
