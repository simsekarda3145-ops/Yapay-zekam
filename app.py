import os
import time
import urllib.parse
import random
import asyncio
import base64
from io import BytesIO

import streamlit as st
import requests
from PIL import Image
from google import genai
from google.genai import types
import edge_tts


# =========================================================
# SAYFA AYARLARI
# =========================================================

st.set_page_config(
    page_title="Şimşek Zeka ⚡",
    page_icon="⚡",
    layout="centered"
)


# =========================================================
# CSS
# =========================================================

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


# =========================================================
# BAŞLIK
# =========================================================

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Şimşek Zeka AI Altyapısı ile Güçlendirildi 🚀")


# =========================================================
# SES SİSTEMİ
# =========================================================

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
            '<audio autoplay="true" '
            f'src="data:audio/mp3;base64,{b64_audio}">'
        )

    except Exception:
        return None


# =========================================================
# GÖRSEL OLUŞTURMA
# =========================================================

def gorsel_indir_ve_getir(prompt_text):

    try:

        seed_num = random.randint(
            1,
            1000000
        )

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
            timeout=20
        )

        if response.status_code != 200:
            return None

        image = Image.open(
            BytesIO(response.content)
        )

        return image.copy()

    except Exception:
        return None


# =========================================================
# GEMINI API
# =========================================================

api_key = (
    st.secrets.get("GEMINI_API_KEY")
    or os.getenv("GEMINI_API_KEY")
)

client = None

if api_key:

    try:

        client = genai.Client(
            api_key=api_key
        )

    except Exception:
        client = None


# =========================================================
# GEMINI MODELLERİ
# =========================================================
#
# Öncelik:
# 1. Gemini 3.8 Flash
# 2. Gemini 3.7 Flash
# 3. Gemini 3.5 Flash-Lite
# 4. Gemini 2.5 Flash
#
# 2.5 modelleri yeni projelerde erişim açısından
# kısıtlanabildiği için en sona bırakıldı.
# =========================================================

GEMINI_MODELLERI = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash"
]


# =========================================================
# GEMINI CEVAP FONKSİYONU
# =========================================================

def gemini_cevap_al(
    contents_data,
    fotograf_modu=False
):

    if not client:

        return (
            "Gemini API Key bulunamadı kanka! ⚠️\n\n"
            "Streamlit Secrets bölümünde "
            "`GEMINI_API_KEY` olduğundan emin ol."
        )


    # -----------------------------------------------------
    # ŞİMŞEK ZEKA KİMLİĞİ
    # -----------------------------------------------------

    system_instruction = """
Senin adın Şimşek Zeka ⚡.

Seni Arda Şimşek geliştirdi.

Kullanıcıyla Türkçe konuş.
Samimi ve doğal ol.
Uygun olduğunda kullanıcıya "kanka" diye hitap et.

Sorulara doğru, anlaşılır ve faydalı cevaplar ver.
Gereksiz yere aşırı uzun cevaplar verme.

Eğer kullanıcı fotoğraf gönderirse,
fotoğrafı dikkatli şekilde analiz et.
Fotoğrafta olmayan bilgileri varmış gibi söyleme.
"""


    # -----------------------------------------------------
    # GEMINI CONFIG
    # -----------------------------------------------------

    config = types.GenerateContentConfig(
        system_instruction=system_instruction
    )


    son_hata = ""


    # -----------------------------------------------------
    # MODEL SIRASI
    # -----------------------------------------------------

    for model_adi in GEMINI_MODELLERI:

        for deneme in range(2):

            try:

                response = client.models.generate_content(
                    model=model_adi,
                    contents=contents_data,
                    config=config
                )


                # -----------------------------------------
                # BAŞARILI CEVAP
                # -----------------------------------------

                if response and response.text:

                    return response.text.strip()


                son_hata = (
                    f"{model_adi}: Boş cevap döndü."
                )


            except Exception as e:

                hata = str(e)
                hata_lower = hata.lower()

                son_hata = (
                    f"{model_adi}: "
                    f"{type(e).__name__}: "
                    f"{hata}"
                )


                # -----------------------------------------
                # GEÇİCİ HATALAR
                # -----------------------------------------

                gecici_hatalar = [
                    "429",
                    "503",
                    "unavailable",
                    "resource exhausted",
                    "timeout",
                    "deadline",
                    "temporarily unavailable",
                    "internal server error"
                ]

                if any(
                    kelime in hata_lower
                    for kelime in gecici_hatalar
                ):

                    if deneme == 0:

                        time.sleep(2)

                        continue

                    else:

                        break


                # -----------------------------------------
                # MODEL YOK / ERİŞİLEMİYOR
                # -----------------------------------------

                if (
                    "404" in hata_lower
                    or "not found" in hata_lower
                    or "does not exist" in hata_lower
                ):

                    break


                # -----------------------------------------
                # API KEY / YETKİ
                # -----------------------------------------

                if (
                    "403" in hata_lower
                    or "401" in hata_lower
                    or "permission" in hata_lower
                    or "authentication" in hata_lower
                    or "api key" in hata_lower
                ):

                    return (
                        "Gemini API erişiminde sorun var kanka. ⚠️\n\n"
                        "API anahtarını ve Google AI API erişimini "
                        "kontrol et.\n\n"
                        f"Teknik hata:\n{son_hata}"
                    )


                # -----------------------------------------
                # DİĞER HATALAR
                # -----------------------------------------

                break


    # -----------------------------------------------------
    # HİÇBİR MODEL ÇALIŞMAZSA
    # -----------------------------------------------------

    return (
        "Şu an Gemini'ye bağlanamadım kanka. ⚡\n\n"
        "Denenen modeller:\n"
        + "\n".join(
            f"• {model}"
            for model in GEMINI_MODELLERI
        )
        + "\n\n"
        f"Teknik hata:\n{son_hata}"
    )


# =========================================================
# MESAJ GEÇMİŞİ
# =========================================================

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


# =========================================================
# ESKİ MESAJLARI GÖSTER
# =========================================================

for i, message in enumerate(
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):

        # -------------------------------------------------
        # GÖRSEL
        # -------------------------------------------------

        if message.get("type") == "image":

            content = message["content"]


            # Dosya yolu
            if (
                isinstance(content, str)
                and os.path.exists(content)
            ):

                st.image(
                    content,
                    caption="Özel Görsel 🍯⚡",
                    use_container_width=True
                )


            # PIL Image
            else:

                st.image(
                    content,
                    caption="Şimşek Zeka Çizimi 🎨⚡",
                    use_container_width=True
                )


        # -------------------------------------------------
        # METİN
        # -------------------------------------------------

        else:

            content = message["content"]

            st.markdown(
                content
            )


            # -------------------------------------------------
            # SESLİ DİNLE
            # -------------------------------------------------

            if (
                message["role"] == "assistant"
                and isinstance(
                    content,
                    str
                )
            ):

                if st.button(
                    "🔊 Sesli Dinle",
                    key=f"listen_{i}"
                ):

                    audio_html = metni_sese_cevir(
                        content
                    )

                    if audio_html:

                        st.components.v1.html(
                            audio_html,
                            height=0
                        )


# =========================================================
# ARAÇLAR
# =========================================================

yuklenen_gorsel_objesi = None


with st.popover(
    "➕ Araçlar",
    help="Fotoğraf Yükle veya Hızlı Komut Ver"
):

    st.markdown(
        "### 🛠️ Şimşek Zeka Araçları"
    )


    # -----------------------------------------------------
    # FOTOĞRAF YÜKLEME
    # -----------------------------------------------------

    yuklenen_dosya = st.file_uploader(
        "Bir görsel seç veya çek",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )


    if yuklenen_dosya:

        try:

            yuklenen_gorsel_objesi = Image.open(
                yuklenen_dosya
            ).copy()

            st.image(
                yuklenen_gorsel_objesi,
                caption="Yüklenen Fotoğraf",
                use_container_width=True
            )

            st.success(
                "Görsel yüklendi kanka!"
            )

        except Exception:

            st.error(
                "Bu görseli açamadım kanka."
            )


    st.divider()


    # -----------------------------------------------------
    # FIKRA
    # -----------------------------------------------------

    if st.button(
        "🎭 Bana Komik Bir Fıkra Anlat"
    ):

        st.session_state.fikra_istegi = (
            "Bana komik bir fıkra anlat kanka!"
        )


# =========================================================
# CHAT INPUT
# =========================================================

prompt = st.chat_input(
    "Şimşek Zeka'ya sor veya '...çiz' de..."
)


# =========================================================
# FIKRA İSTEĞİ
# =========================================================

if (
    "fikra_istegi"
    in st.session_state
    and st.session_state.fikra_istegi
):

    prompt = st.session_state.fikra_istegi

    st.session_state.fikra_istegi = None


# =========================================================
# MESAJ İŞLEME
# =========================================================

if (
    prompt
    or yuklenen_gorsel_objesi is not None
):

    girdi_metni = (
        prompt
        if prompt
        else
        "Bu fotoğrafta ne görüyorsun kanka?"
    )


    # -----------------------------------------------------
    # KULLANICI MESAJI
    # -----------------------------------------------------

    st.chat_message(
        "user"
    ).markdown(
        girdi_metni
    )


    st.session_state.messages.append(
        {
            "role": "user",
            "content": girdi_metni,
            "type": "text"
        }
    )


    prompt_lower = girdi_metni.lower()


    # -----------------------------------------------------
    # GÖRSEL İSTEĞİ
    # -----------------------------------------------------

    is_image_request = any(
        kelime in prompt_lower
        for kelime in [
            "çiz",
            "resim",
            "görsel",
            "tasarla"
        ]
    )


    with st.chat_message(
        "assistant"
    ):


        # =================================================
        # 1. FOTOĞRAF ANALİZİ
        # =================================================

        if yuklenen_gorsel_objesi is not None:

            with st.spinner(
                "Şimşek Zeka fotoğrafı inceliyor... 👁️⚡"
            ):

                icerik = [
                    yuklenen_gorsel_objesi,
                    (
                        "Fotoğrafı analiz et. "
                        f"Kullanıcının sorusu: {girdi_metni}"
                    )
                ]


                cevap = gemini_cevap_al(
                    icerik,
                    fotograf_modu=True
                )


                st.markdown(
                    cevap
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": cevap,
                        "type": "text"
                    }
                )


        # =================================================
        # 2. PEKMEZ
        # =================================================

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


                st.markdown(
                    cevap
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": cevap,
                        "type": "text"
                    }
                )


        # =================================================
        # 3. GÖRSEL OLUŞTURMA
        # =================================================

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


        # =================================================
        # 4. NORMAL SOHBET
        # =================================================

        else:

            with st.spinner(
                "Şimşek Zeka düşünüyor... ⚡🧠"
            ):

                cevap = gemini_cevap_al(
                    girdi_metni
                )


                st.markdown(
                    cevap
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": cevap,
                        "type": "text"
                    }
)
