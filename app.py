import os
import time
import urllib.parse
import random
import asyncio
import base64
from io import BytesIO

import requests
import streamlit as st
from PIL import Image
from google import genai
import edge_tts


# ==================================================
# SAYFA AYARLARI
# ==================================================

st.set_page_config(
    page_title="Şimşek Zeka ⚡",
    page_icon="⚡",
    layout="centered"
)


# ==================================================
# CSS
# ==================================================

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


# ==================================================
# BAŞLIK
# ==================================================

st.title("⚡ Şimşek Zeka - Işık Hızında Yapay Zeka")
st.caption("Şimşek Zeka AI Altyapısı ile Güçlendirildi 🚀")


# ==================================================
# SES SİSTEMİ
# ==================================================

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
            '<audio controls autoplay '
            'style="width:100%;" '
            f'src="data:audio/mp3;base64,{b64_audio}">'
            '</audio>'
        )

    except Exception:
        return None


# ==================================================
# GÖRSEL OLUŞTURMA
# ==================================================

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


# ==================================================
# GEMINI BAĞLANTISI
# ==================================================

api_key = (
    st.secrets.get("GEMINI_API_KEY")
    or os.getenv("GEMINI_API_KEY")
)

if api_key:

    client = genai.Client(
        api_key=api_key
    )

else:

    client = None


# ==================================================
# GEMINI MODEL LİSTESİ
# ==================================================

GEMINI_MODELLERI = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]


# ==================================================
# SOHBET GEÇMİŞİ OLUŞTURMA
# ==================================================

def sohbet_gecmisini_hazirla():

    if "messages" not in st.session_state:
        return ""

    gecmis = []

    # Son 12 mesajı kullan
    son_mesajlar = st.session_state.messages[-12:]

    for mesaj in son_mesajlar:

        if mesaj.get("type") == "image":
            continue

        role = mesaj.get("role")
        content = mesaj.get("content")

        if not isinstance(content, str):
            continue

        if role == "user":
            gecmis.append(
                f"Kullanıcı: {content}"
            )

        elif role == "assistant":
            gecmis.append(
                f"Şimşek Zeka: {content}"
            )

    return "\n".join(gecmis)


# ==================================================
# GEMINI CEVAP SİSTEMİ
# ==================================================

def gemini_cevap_al(
    kullanici_icerigi,
    fotograf=None
):

    if not client:

        return (
            "Gemini API Key bulunamadı kanka! ⚠️\n\n"
            "Streamlit Secrets bölümünde "
            "`GEMINI_API_KEY` olduğundan emin ol."
        )


    # ----------------------------------------------
    # ŞİMŞEK ZEKA KARAKTERİ
    # ----------------------------------------------

    sistem = """
Senin adın Şimşek Zeka ⚡.

Seni Arda Şimşek geliştirdi.

Kullanıcıyla Türkçe konuş.
Samimi ve doğal ol.
Gerektiğinde kullanıcıya "kanka" diye hitap et.
Sorulara doğru ve anlaşılır cevap ver.
Gereksiz yere çok uzun cevaplar verme.

Fotoğraf gönderildiyse fotoğrafı dikkatlice incele
ve yalnızca görüntüden çıkarılabilecek bilgiler üzerinden
cevap ver.
"""


    # ----------------------------------------------
    # SOHBET GEÇMİŞİ
    # ----------------------------------------------

    gecmis = sohbet_gecmisini_hazirla()


    # ----------------------------------------------
    # NORMAL METİN
    # ----------------------------------------------

    if fotograf is None:

        tam_prompt = f"""
{sistem}

Önceki sohbet:
{gecmis}

Kullanıcının yeni mesajı:
{kullanici_icerigi}
"""

        icerik = tam_prompt


    # ----------------------------------------------
    # FOTOĞRAF
    # ----------------------------------------------

    else:

        tam_prompt = f"""
{sistem}

Kullanıcının fotoğrafla ilgili sorusu:
{kullanici_icerigi}
"""

        icerik = [
            fotograf,
            tam_prompt
        ]


    son_hata = ""


    # ----------------------------------------------
    # MODELLERİ DENE
    # ----------------------------------------------

    for model_adi in GEMINI_MODELLERI:

        # Her model için en fazla 2 deneme
        for deneme in range(2):

            try:

                response = client.models.generate_content(
                    model=model_adi,
                    contents=icerik
                )


                if response and response.text:

                    return response.text.strip()


                son_hata = (
                    f"{model_adi}: Gemini boş cevap döndürdü."
                )


            except Exception as e:

                hata = str(e)
                hata_lower = hata.lower()

                son_hata = (
                    f"{model_adi}: "
                    f"{type(e).__name__}: "
                    f"{hata}"
                )


                # ----------------------------------
                # GEÇİCİ HATALAR
                # ----------------------------------

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

                gecici_mi = any(
                    kelime in hata_lower
                    for kelime in gecici_hatalar
                )


                if gecici_mi:

                    if deneme == 0:

                        time.sleep(2)

                        continue


                # ----------------------------------
                # MODEL BULUNAMADI
                # ----------------------------------

                model_hatasi = (
                    "404" in hata_lower
                    or "not found" in hata_lower
                    or "does not exist" in hata_lower
                )

                if model_hatasi:

                    # Bu modeli bırak,
                    # sıradaki modele geç.
                    break


                # ----------------------------------
                # YETKİ / API KEY
                # ----------------------------------

                if (
                    "403" in hata_lower
                    or "permission" in hata_lower
                    or "api key" in hata_lower
                    or "authentication" in hata_lower
                ):

                    return (
                        "Gemini API erişiminde sorun var kanka. ⚠️\n\n"
                        f"Teknik hata:\n{son_hata}"
                    )


                # ----------------------------------
                # DİĞER HATALAR
                # ----------------------------------

                break


    # ==================================================
    # HİÇBİR MODEL ÇALIŞMAZSA
    # ==================================================

    return (
        "Gemini'ye şu anda bağlanamadım kanka. ⚡\n\n"
        "Denediğim modeller:\n"
        + "\n".join(
            f"• {model}"
            for model in GEMINI_MODELLERI
        )
        + "\n\n"
        f"Son teknik hata:\n{son_hata}"
    )


# ==================================================
# MESAJ GEÇMİŞİ
# ==================================================

if "messages" not in st.session_state:

    st.session_state.messages = [

        {
            "role": "assistant",
            "content": (
                "Naber kanka! Ben Şimşek Zeka ⚡ "
                "Buradayım. Bana istediğini sorabilir, "
                "fotoğraf gönderebilir veya çizim yaptırabilirsin!"
            )
        }

    ]


# ==================================================
# ESKİ MESAJLARI GÖSTER
# ==================================================

for i, message in enumerate(
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):

        # ------------------------------------------
        # GÖRSEL MESAJ
        # ------------------------------------------

        if message.get("type") == "image":

            content = message.get("content")


            # Dosya yoluysa
            if (
                isinstance(content, str)
                and os.path.exists(content)
            ):

                st.image(
                    content,
                    caption="Özel Görsel 🍯⚡",
                    use_container_width=True
                )


            # PIL görseliyse
            elif content is not None:

                st.image(
                    content,
                    caption="Şimşek Zeka Çizimi 🎨⚡",
                    use_container_width=True
                )


        # ------------------------------------------
        # METİN MESAJI
        # ------------------------------------------

        else:

            content = message.get(
                "content",
                ""
            )

            st.markdown(content)


            # Ses butonu
            if (
                message["role"] == "assistant"
                and isinstance(
                    content,
                    str
                )
                and content.strip()
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
                            height=55
                        )


# ==================================================
# ARAÇLAR
# ==================================================

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
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )


    if yuklenen_dosya:

        try:

            # .copy() önemli:
            # uploaded_file kapanırsa görüntü bozulmasın.
            yuklenen_gorsel_objesi = Image.open(
                yuklenen_dosya
            ).copy()

            st.image(
                yuklenen_gorsel_objesi,
                caption="Yüklenen Fotoğraf",
                use_container_width=True
            )

            st.success(
                "Görsel yüklendi kanka! ⚡"
            )

        except Exception:

            st.error(
                "Bu görseli açamadım kanka."
            )


    st.divider()


    if st.button(
        "🎭 Bana Komik Bir Fıkra Anlat"
    ):

        st.session_state.fikra_istegi = (
            "Bana komik bir fıkra anlat kanka!"
        )


# ==================================================
# CHAT INPUT
# ==================================================

prompt = st.chat_input(
    "Şimşek Zeka'ya sor veya '...çiz' de..."
)


# Fıkra isteği
if (
    "fikra_istegi"
    in st.session_state
    and st.session_state.fikra_istegi
):

    prompt = st.session_state.fikra_istegi

    st.session_state.fikra_istegi = None


# ==================================================
# MESAJ İŞLEME
# ==================================================

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


    # ----------------------------------------------
    # KULLANICI MESAJI
    # ----------------------------------------------

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


    # ----------------------------------------------
    # GÖRSEL İSTEĞİ Mİ?
    # ----------------------------------------------

    is_image_request = any(
        kelime in prompt_lower
        for kelime in [
            "çiz",
            "resim çiz",
            "görsel oluştur",
            "görsel yap",
            "tasarla",
            "resim yap"
        ]
    )


    with st.chat_message(
        "assistant"
    ):


        # ==================================================
        # 1. FOTOĞRAF ANALİZİ
        # ==================================================

        if yuklenen_gorsel_objesi is not None:

            with st.spinner(
                "Şimşek Zeka fotoğrafı inceliyor... 👁️⚡"
            ):

                cevap = gemini_cevap_al(
                    girdi_metni,
                    fotograf=yuklenen_gorsel_objesi
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


        # ==================================================
        # 2. PEKMEZ
        # ==================================================

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


        # ==================================================
        # 3. GÖRSEL OLUŞTURMA
        # ==================================================

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
                            "İşte çizim 🎨⚡"
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
                        "Resim servisi şu an yoğun kanka! "
                        "Birkaç saniye sonra tekrar dene."
                    )


        # ==================================================
        # 4. NORMAL GEMINI SOHBETİ
        # ==================================================

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
