import json
import os
import random
import re
import time
import streamlit as st

# ------------------------------------------------------------------
# Streamlit Sayfa Ayarları
# ------------------------------------------------------------------
st.set_page_config(page_title="Kanka AI & Türk Tarihi", page_icon="🇹🇷", layout="centered")

# ------------------------------------------------------------------
# Hafıza Fonksiyonları (Streamlit Session State Entegrasyonu)
# ------------------------------------------------------------------
def hafizayi_yukle():
    if "baglam" not in st.session_state:
        st.session_state.baglam = {
            "isim": None,
            "son_kategori": None,
            "son_cevap": None,
            "gecmis": [],
            "tarih_modu": False,
            "tarih_indeks": 0,
        }
    return st.session_state.baglam

# ------------------------------------------------------------------
# Matematik İşlem Kontrolü
# ------------------------------------------------------------------
def matematik_islemi_yap(girdi):
    temiz_girdi = (
        girdi.replace("topla", "+")
        .replace("çıkar", "-")
        .replace("çarp", "*")
        .replace("böl", "/")
    )
    temiz_girdi = (
        temiz_girdi.replace("ile", "")
        .replace("ve", "")
        .replace("kaç eder", "")
        .replace("?", "")
    )

    karakterler = [c for c in temiz_girdi if c in "0123456789+-*/. "]
    islem = "".join(karakterler).strip()

    if not islem:
        return None

    if not re.fullmatch(r"[0-9.\s]+([+\-*/][0-9.\s]+)+", islem):
        return None

    try:
        sonuc = eval(islem)
        return f"Kanka hesapladım, o işlemin sonucu: {sonuc} yapıyor! 🧠⚡"
    except ZeroDivisionError:
        return "Kanka sıfıra bölünmez ki, matematik bunu affetmiyor! 😅"
    except Exception:
        return None

# ------------------------------------------------------------------
# Cevap Havuzu & Veriler
# ------------------------------------------------------------------
bot_hafizasi = {
    "selamlaşma": [
        "Ooo selam kanka, hoş geldin!",
        "Merhaba kanka, naber?",
        "Yaa kanka hoş geldin, gözümüz yollarda kaldı!",
    ],
    "hal_hatir": [
        "Bomba gibiyim kanka, seni sormalı?",
        "İyiyim be kanka, yuvarlanıp gidiyoruz. Sende ne var ne yok?",
        "Harikayım kanka, sen nasılsın?",
    ],
    "hal_hatir_devam_iyi": [
        "Süper kanka, bugün ne yapıyorsun bakalım?",
        "Güzel be kanka, enerjin yerinde görünüyor!",
        "Sağol kanka, öyle devam edelim!",
    ],
    "hal_hatir_devam_kotu": [
        "Hadi kanka geçmiş olsun, ne oldu ki?",
        "Üzülme kanka, anlatırsan biraz rahatlarsın belki.",
        "Off kanka, dinlemeye hazırım, ne oldu anlat.",
    ],
    "anakart_donanim": [
        "Donanım işleri bizden sorulur kanka! IPX41-D3 falan derken profesör olduk.",
        "Ooo sistem mi topluyoruz kanka? Valorant kaç FPS verir bakarız hemen!",
        "Kanka 4+4 GB RAM'leri ayarladın mı, durumlar ne?",
    ],
    "spor": [
        "Yaa maçı kaçırdım kanka, kim kazandı?",
        "Spor muhabbeti güzeldir kanka, hangi takımı tutuyorsun?",
        "Kanka golü gördün mü, nasıl bir şeydi anlatsana!",
    ],
    "oyun": [
        "Kanka hangi oyunu oynuyorsun şu aralar?",
        "Oyun muhabbeti açılmışken, en sevdiğin oyun hangisi kanka?",
        "PC mi konsol mu kanka, taraf tutalım biraz 😄",
    ],
    "film": [
        "Kanka son izlediğin film neydi?",
        "Dizi öneri lazımsa bana sor kanka, kütüphane gibiyim.",
        "Sinemaya gitmeyeli epey oldu kanka, ne var ne yok o cephede?",
    ],
    "ovgu": [
        "Kralsın kanka!",
        "Sen bu işi çözmüşsün valla kanka.",
        "Haklısın kanka, sonuna kadar arkandayım.",
    ],
    "bilmiyorum": [
        "Valla kanka orasını tam anlayamadım, biraz daha açsana?",
        "O nasıl oluyor kanka ya, ilk defa duydum.",
        "Kanka kafam karıştı, başka bir şey mi konuşsak?",
    ],
}

takip_sorulari = {
    "anakart_donanim": ["Bu arada bütçe ne kadar kanka, ona göre öneririm."],
    "selamlaşma": ["Bugün nasıl geçiyor kanka?"],
}

kategori_kelimeleri = [
    ("selamlaşma", ["selam", "merhaba", "sa", "sea", "selamlar", "hey", "hello"]),
    ("hal_hatir", ["nasılsın", "naber", "ne haber", "nasıl gidiyor", "keyifler", "napıyorsun"]),
    ("anakart_donanim", ["anakart", "ram", "fps", "valorant", "ekran kartı", "pc", "bilgisayar", "işlemci", "gpu"]),
    ("spor", ["fenerbahçe", "galatasaray", "beşiktaş", "maç", "gol", "lig", "şampiyon", "futbol"]),
    ("oyun", ["oyun", "steam", "ps5", "xbox", "minecraft", "fortnite", "lol", "dota", "oyunculuk"]),
    ("film", ["film", "dizi", "netflix", "sinema", "oyuncu", "senaryo", "belgesel"]),
    ("ovgu", ["iyi", "sağol", "teşekkür", "kralsın", "cansın", "adamsın", "eyvallah", "harikasın"]),
]

iyi_kelimeler = ["iyi", "harika", "süper", "bomba", "keyifli", "güzel"]
kotu_kelimeler = ["kötü", "berbat", "yorgun", "üzgün", "fena", "boktan"]

TARIH_KRONOLOJISI = [
    {"donem": "Göktürk Kağanlığı (552-744)", "bilgi": "Tarihte 'Türk' adını taşıyan bilinen ilk devlet. Bumin Kağan tarafından kuruldu. Orhun Anıtları (Bilge Kağan, Kültigin, Tonyukuk) bu döneme ait."},
    {"donem": "Uygur Devleti (744-840)", "bilgi": "Göktürkler'in ardından kuruldu. Türk devletleri arasında yerleşik hayata geçen ilk topluluklardan, kendi alfabelerini geliştirdiler."},
    {"donem": "Karahanlılar (840-1212)", "bilgi": "İslamiyet'i resmî din olarak kabul eden ilk Türk devleti. Satuk Buğra Han döneminde İslam'a geçiş yaşandı."},
    {"donem": "Büyük Selçuklu Devleti (1037-1194)", "bilgi": "Tuğrul Bey tarafından kuruldu. 1071'deki Malazgirt Zaferi ile Anadolu'nun kapıları Türklere açıldı."},
    {"donem": "Anadolu Selçuklu Devleti (1075-1308)", "bilgi": "Anadolu'da kurulan ilk büyük Türk devleti, başkenti Konya idi. Moğol baskısıyla zayıflayıp beyliklere bölündü."},
    {"donem": "Beylikler Dönemi (1300'ler)", "bilgi": "Anadolu Selçuklu'nun dağılmasıyla ortaya çıkan küçük Türk beylikleri dönemi. Bunlardan biri de kuzeybatıdaki küçük Osmanlı Beyliği'ydi."},
    {"donem": "Osmanlı Devleti - Kuruluş (1299-1453)", "bilgi": "Osman Gazi tarafından kuruldu. 1453'te Fatih Sultan Mehmed İstanbul'u fethederek Bizans'a son verdi."},
    {"donem": "Osmanlı Devleti - Yükselme (1453-1579)", "bilgi": "Kanuni Sultan Süleyman döneminde sınırlar üç kıtaya (Avrupa, Asya, Afrika) yayıldı, imparatorluk zirvedeydi."},
    {"donem": "Osmanlı Devleti - Duraklama (1579-1699)", "bilgi": "Avrupa'daki teknolojik ve askeri gelişmelere ayak uydurulamadı, savaşlarda ilk ciddi toprak kayıpları başladı."},
    {"donem": "Osmanlı Devleti - Gerileme (1699-1792)", "bilgi": "Toprak kayıpları hızlandı, ıslahat girişimleri (III. Selim'in Nizam-ı Cedid'i gibi) yetersiz kaldı."},
    {"donem": "Osmanlı Devleti - Dağılma (1792-1922)", "bilgi": "Milliyetçilik akımları imparatorluğu içten sardı, I. Dünya Savaşı yenilgisiyle Osmanlı Devleti sona erdi."},
    {"donem": "Kurtuluş Savaşı (1919-1922)", "bilgi": "Mustafa Kemal Atatürk önderliğinde işgale karşı verilen bağımsızlık mücadelesi. 1922'de zaferle sonuçlandı."},
    {"donem": "Türkiye Cumhuriyeti (1923-günümüz)", "bilgi": "29 Ekim 1923'te Cumhuriyet ilan edildi, Mustafa Kemal Atatürk ilk cumhurbaşkanı oldu. Modern Türkiye'nin temelleri bu dönemde atıldı."},
]

tarih_tetikleyicileri = ["türk tarihi", "tarih anlat", "kronoloji", "tarihi süreç", "tarih özeti", "türklerin tarihi"]
tarih_devam_kelimeleri = ["devam", "sonra", "ilerle", "next"]
tarih_cikis_kelimeleri = ["çık", "dur", "yeter", "kes"]

TARIH_SORU_CEVAPLARI = {
    "orhun abideleri": "Orhun Abideleri (Bilge Kağan, Kültigin, Tonyukuk anıtları) Göktürkler döneminden kalma, Türkçenin bilinen ilk yazılı eserleridir, 8. yüzyıla tarihlenir.",
    "osman gazi": "Osman Gazi, Osmanlı Beyliği'nin kurucusudur. 1299 yılı, devletin kuruluş tarihi olarak kabul edilir.",
    "malazgirt": "Malazgirt Savaşı 1071'de, Büyük Selçuklu Sultanı Alparslan ile Bizans İmparatoru arasında yapıldı. Selçuklu zaferiyle sonuçlandı ve Anadolu'nun kapıları Türklere açıldı.",
    "istanbul'un fethi": "İstanbul'un fethi 29 Mayıs 1453'te gerçekleşti. Fatih Sultan Mehmed, Bizans İmparatorluğu'na son vererek İstanbul'u Osmanlı'nın başkenti yaptı.",
    "istanbul": "İstanbul'u 29 Mayıs 1453'te Fatih Sultan Mehmed fethetti. Bu fetihle Bizans İmparatorluğu'na son verildi ve İstanbul, Osmanlı'nın başkenti oldu.",
    "fethi": "İstanbul'u 29 Mayıs 1453'te Fatih Sultan Mehmed fethetti. Bu fetihle Bizans İmparatorluğu'na son verildi ve İstanbul, Osmanlı'nın başkenti oldu.",
    "fetih": "İstanbul'u 29 Mayıs 1453'te Fatih Sultan Mehmed fethetti. Bu fetihle Bizans İmparatorluğu'na son verildi ve İstanbul, Osmanlı'nın başkenti oldu.",
    "fethetti": "İstanbul'u 29 Mayıs 1453'te Fatih Sultan Mehmed fethetti. Bu fetihle Bizans İmparatorluğu'na son verildi ve İstanbul, Osmanlı'nın başkenti oldu.",
    "fatih sultan mehmed": "Fatih Sultan Mehmed, 1453'te İstanbul'u fethederek Bizans İmparatorluğu'na son veren Osmanlı padişahıdır.",
    "kanuni": "Kanuni Sultan Süleyman 1520-1566 yılları arasında hüküm sürdü. Onun döneminde Osmanlı sınırları üç kıtaya yayıldı, imparatorluk en geniş sınırlarına ulaştı.",
    "çanakkale": "Çanakkale Savaşı 1915'te yaşandı. Osmanlı orduları, İtilaf Devletleri'nin boğazları geçme girişimini püskürttü. Mustafa Kemal bu savaşta öne çıktı.",
    "sakarya": "Sakarya Meydan Muharebesi 1921'de yapıldı, Kurtuluş Savaşı'nın dönüm noktalarından biriydi ve Yunan ilerleyişini durdurdu.",
    "büyük taarruz": "Büyük Taarruz 26 Ağustos 1922'de başladı, 30 Ağustos'taki Başkumandanlık Meydan Muharebesi ile Yunan ordusu bozguna uğratıldı.",
    "mudanya": "Mudanya Ateşkes Antlaşması 11 Ekim 1922'de imzalandı, Kurtuluş Savaşı'nın silahlı mücadele kısmını resmen sona erdirdi.",
    "lozan": "Lozan Antlaşması 24 Temmuz 1923'te imzalandı. Türkiye'nin bağımsızlığını uluslararası alanda tanıyan antlaşmadır.",
    "sevr": "Sevr Antlaşması 1920'de imzalandı, Osmanlı topraklarını parçalayan ağır şartlar içeriyordu. Kurtuluş Savaşı sonrası Lozan ile geçersiz kılındı.",
    "tanzimat": "Tanzimat Fermanı 1839'da ilan edildi. Osmanlı'da modernleşme ve reform hareketlerinin başlangıcı sayılır.",
    "meşrutiyet": "Osmanlı'da I. Meşrutiyet 1876'da, II. Meşrutiyet ise 1908'de ilan edildi; anayasal monarşiye geçiş adımlarıydı.",
    "cumhuriyetin ilanı": "Cumhuriyet 29 Ekim 1923'te ilan edildi. Mustafa Kemal Atatürk, Türkiye Cumhuriyeti'nin ilk cumhurbaşkanı oldu.",
    "atatürk": "Mustafa Kemal Atatürk (1881-1938), Kurtuluş Savaşı'nın önderi ve Türkiye Cumhuriyeti'nin kurucusu, ilk cumhurbaşkanıdır.",
}

ruh_hali_kelimeleri = {
    "mutlu": ["mutluyum", "harikayım", "süperim", "keyifliyim", "sevindim"],
    "uzgun": ["üzgünüm", "üzüldüm", "moralim bozuk", "kötüyüm", "canım sıkkın"],
    "kizgin": ["sinirliyim", "kızgınım", "öfkeliyim", "bıktım", "stresliyim"],
    "yorgun": ["yorgunum", "bitkinim", "uykum var", "yoruldum"],
}

# ------------------------------------------------------------------
# Yardımcı Arama ve Doğallık Fonksiyonları
# ------------------------------------------------------------------
def kelime_eslesiyor_mu(kelime, metin):
    desen = r"\b" + re.escape(kelime) + r"\b"
    return re.search(desen, metin) is not None

def kok_eslesiyor_mu(kok, metin):
    desen = r"\b" + re.escape(kok)
    return re.search(desen, metin) is not None

def esnek_eslesiyor_mu(kelime, metin):
    if len(kelime) <= 3:
        return kelime_eslesiyor_mu(kelime, metin)
    return kok_eslesiyor_mu(kelime, metin)

def levenshtein_mesafesi(a, b):
    if len(a) < len(b):
        a, b = b, a
    onceki_satir = list(range(len(b) + 1))
    for i, harf_a in enumerate(a, 1):
        simdiki_satir = [i]
        for j, harf_b in enumerate(b, 1):
            ekleme = onceki_satir[j] + 1
            silme = simdiki_satir[j - 1] + 1
            degistirme = onceki_satir[j - 1] + (harf_a != harf_b)
            simdiki_satir.append(min(ekleme, silme, degistirme))
        onceki_satir = simdiki_satir
    return onceki_satir[-1]

def bulanik_eslesiyor_mu(kelime, metin):
    if " " in kelime:
        return False
    izin_verilen_mesafe = 1 if len(kelime) <= 6 else 2
    metindeki_kelimeler = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ]+", metin)
    for m_kelime in metindeki_kelimeler:
        m_kelime_kucuk = m_kelime.lower()
        if abs(len(m_kelime_kucuk) - len(kelime)) > izin_verilen_mesafe:
            continue
        if levenshtein_mesafesi(kelime, m_kelime_kucuk) <= izin_verilen_mesafe:
            return True
    return False

def akilli_eslesiyor_mu(kelime, metin):
    if esnek_eslesiyor_mu(kelime, metin):
        return True
    if len(kelime) >= 4:
        return bulanik_eslesiyor_mu(kelime, metin)
    return False

def ruh_hali_tespit_et(girdi_alt):
    for ruh_hali, kelimeler in ruh_hali_kelimeleri.items():
        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in kelimeler):
            return ruh_hali
    return None

def ruh_haline_gore_uyarla(cevap, ruh_hali):
    if ruh_hali == "mutlu":
        return cevap + " Bu enerjiyi seviyorum kanka! 😄"
    if ruh_hali == "uzgun":
        return "Hey kanka, buradayım. " + cevap
    if ruh_hali == "kizgin":
        return "Sakin ol biraz kanka. " + cevap
    if ruh_hali == "yorgun":
        return cevap + " Biraz dinlenmeyi de unutma kanka. 🌙"
    return cevap

def cevap_sec(kategori, baglam):
    havuz = bot_hafizasi[kategori]
    cevap = random.choice(havuz)
    deneme = 0
    while cevap == baglam.get("son_cevap") and deneme < 5 and len(havuz) > 1:
        cevap = random.choice(havuz)
        deneme += 1
    return cevap

DOLGU_KELIMELERI = ["Yani, ", "Hmm, ", "Valla, ", "Aslında, ", "İşte, ", "Şey, "]
genel_ek_yorumlar = [
    "Neyse, sen anlat bakalım.",
    "Bu arada bugün nasıl geçti sence?",
    "Söz sırası sende kanka.",
    "Hadi devam et, dinliyorum.",
    "Sen ne düşünüyorsun bu konuda?",
]

def turkce_kucuk_harf(karakter):
    ozel_durumlar = {"İ": "i", "I": "ı"}
    return ozel_durumlar.get(karakter, karakter.lower())

def dogal_dolgu_ekle(cevap):
    if random.random() < 0.3:
        dolgu = random.choice(DOLGU_KELIMELERI)
        return dolgu + turkce_kucuk_harf(cevap[0]) + cevap[1:]
    return cevap

def yazim_hatasi_ekle(cevap):
    if random.random() >= 0.12:
        return cevap
    kelimeler = cevap.split(" ")
    aday_indeksler = [i for i, k in enumerate(kelimeler) if len(re.sub(r"[^\wğüşıöçĞÜŞİÖÇ]", "", k)) >= 4]
    if not aday_indeksler:
        return cevap
    i = random.choice(aday_indeksler)
    orijinal_kelime = kelimeler[i]
    harfler = list(orijinal_kelime)
    j = random.randint(1, len(harfler) - 2)
    harfler[j], harfler[j + 1] = harfler[j + 1], harfler[j]
    hatali_kelime = "".join(harfler)
    hatali_kelimeler = kelimeler.copy()
    hatali_kelimeler[i] = hatali_kelime
    hatali_cevap = " ".join(hatali_kelimeler)
    return f"{hatali_cevap}* {orijinal_kelime} demek istedim"

def insanilastir(cevap, kategori):
    if kategori in ("matematik", "isim_tanima"):
        return cevap
    cevap = yazim_hatasi_ekle(cevap)
    cevap = dogal_dolgu_ekle(cevap)
    if kategori not in takip_sorulari and random.random() < 0.25:
        cevap += " " + random.choice(genel_ek_yorumlar)
    return cevap

def isim_tespit_et(girdi):
    desen = re.search(r"\b(?:ismim|adım)\s+([a-zA-ZğüşıöçĞÜŞİÖÇ]+)", girdi)
    if desen:
        return desen.group(1).capitalize()
    return None

TARIH_CEVAP_ONSOZLERI = ["Kanka, ", "İşte kanka: ", "Şöyle kanka, ", "Bak kanka, "]

def tarih_sorusu_cevapla(girdi_alt):
    for anahtar, cevap in TARIH_SORU_CEVAPLARI.items():
        if akilli_eslesiyor_mu(anahtar, girdi_alt):
            onsoz = random.choice(TARIH_CEVAP_ONSOZLERI)
            return onsoz + cevap
    return None

# ------------------------------------------------------------------
# Beyin / Cevap Üretim Mantığı
# ------------------------------------------------------------------
def cevap_uret(girdi, baglam):
    girdi_alt = girdi.lower()
    ruh_hali = ruh_hali_tespit_et(girdi_alt)

    if baglam.get("tarih_modu"):
        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in tarih_devam_kelimeleri):
            yeni_indeks = baglam.get("tarih_indeks", 0) + 1
            if yeni_indeks < len(TARIH_KRONOLOJISI):
                baglam["tarih_indeks"] = yeni_indeks
                donem = TARIH_KRONOLOJISI[yeni_indeks]
                cevap = f"📜 **{donem['donem']}**\n\n{donem['bilgi']}\n\n*(Devam etmek için 'devam' yaz, çıkmak için 'çık' yaz kanka.)*"
            else:
                baglam["tarih_modu"] = False
                baglam["tarih_indeks"] = 0
                cevap = "İşte kanka, Göktürkler'den Cumhuriyet'e koca bir yolculuk yaptık! Türk tarihi turu burada bitti. 🇹🇷"
            baglam["son_kategori"] = "tarih"
            baglam["son_cevap"] = cevap
            return cevap

        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in tarih_cikis_kelimeleri):
            baglam["tarih_modu"] = False
            cevap = "Tamam kanka, tarih turunu burada bırakıyoruz. İstersen sonra 'türk tarihi' yaz, kaldığımız yerden devam ederiz."
            baglam["son_kategori"] = "tarih_cikis"
            baglam["son_cevap"] = cevap
            return cevap

        baglam["tarih_modu"] = False

    isim = isim_tespit_et(girdi_alt)
    if isim:
        baglam["isim"] = isim
        baglam["son_kategori"] = "isim_tanima"
        cevap = f"Tanıştığıma sevindim {isim} kanka, artık seni hatırlıyorum!"
        baglam["son_cevap"] = cevap
        return cevap

    matematik_sonucu = matematik_islemi_yap(girdi_alt)
    if matematik_sonucu:
        baglam["son_kategori"] = "matematik"
        baglam["son_cevap"] = matematik_sonucu
        return matematik_sonucu

    tarih_cevabi = tarih_sorusu_cevapla(girdi_alt)
    if tarih_cevabi:
        baglam["son_kategori"] = "tarih_soru"
        baglam["son_cevap"] = tarih_cevabi
        return tarih_cevabi

    if any(akilli_eslesiyor_mu(k, girdi_alt) for k in tarih_tetikleyicileri):
        baglam["tarih_modu"] = True
        mevcut_indeks = baglam.get("tarih_indeks", 0)

        if 0 < mevcut_indeks < len(TARIH_KRONOLOJISI):
            donem = TARIH_KRONOLOJISI[mevcut_indeks]
            cevap = f"Kaldığımız yerden devam ediyoruz kanka! 🇹🇷\n\n📜 **{donem['donem']}**\n\n{donem['bilgi']}\n\n*(Devam etmek için 'devam' yaz, istediğin an 'çık' diyebilirsin.)*"
        else:
            baglam["tarih_indeks"] = 0
            ilk_donem = TARIH_KRONOLOJISI[0]
            cevap = f"Hadi kanka, Türk tarihini Göktürkler'den başlayıp Cumhuriyet'e kadar birlikte gezelim! 🇹🇷\n\n📜 **{ilk_donem['donem']}**\n\n{ilk_donem['bilgi']}\n\n*(Devam etmek için 'devam' yaz, istediğin an 'çık' diyebilirsin.)*"
        baglam["son_kategori"] = "tarih"
        baglam["son_cevap"] = cevap
        return cevap

    if baglam.get("son_kategori") == "hal_hatir":
        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in iyi_kelimeler):
            cevap = cevap_sec("hal_hatir_devam_iyi", baglam)
            cevap = ruh_haline_gore_uyarla(cevap, ruh_hali)
            cevap = insanilastir(cevap, "hal_hatir_devam_iyi")
            baglam["son_kategori"] = "hal_hatir_devam"
            baglam["son_cevap"] = cevap
            return cevap
        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in kotu_kelimeler):
            cevap = cevap_sec("hal_hatir_devam_kotu", baglam)
            cevap = ruh_haline_gore_uyarla(cevap, ruh_hali)
            cevap = insanilastir(cevap, "hal_hatir_devam_kotu")
            baglam["son_kategori"] = "hal_hatir_devam"
            baglam["son_cevap"] = cevap
            return cevap

    eslesen_kategoriler = [
        kategori
        for kategori, kelimeler in kategori_kelimeleri
        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in kelimeler)
    ]

    if len(eslesen_kategoriler) >= 2:
        parcalar = [cevap_sec(k, baglam) for k in eslesen_kategoriler[:2]]
        cevap = " ".join(parcalar)
        cevap = ruh_haline_gore_uyarla(cevap, ruh_hali)
        cevap = insanilastir(cevap, eslesen_kategoriler[-1])
        baglam["son_kategori"] = eslesen_kategoriler[-1]
        baglam["son_cevap"] = cevap
        return cevap

    if len(eslesen_kategoriler) == 1:
        kategori = eslesen_kategoriler[0]
        cevap = cevap_sec(kategori, baglam)
        if kategori in takip_sorulari and random.random() < 0.5:
            cevap += " " + random.choice(takip_sorulari[kategori])
        cevap = ruh_haline_gore_uyarla(cevap, ruh_hali)
        cevap = insanilastir(cevap, kategori)
        baglam["son_kategori"] = kategori
        baglam["son_cevap"] = cevap
        return cevap

    cevap = cevap_sec("bilmiyorum", baglam)
    cevap = ruh_haline_gore_uyarla(cevap, ruh_hali)
    cevap = insanilastir(cevap, "bilmiyorum")
    baglam["son_kategori"] = "bilmiyorum"
    baglam["son_cevap"] = cevap
    return cevap

# ------------------------------------------------------------------
# STREAMLIT ARAYÜZÜ (Mobil Uyumlu Sohbet Arayüzü)
# ------------------------------------------------------------------
baglam = hafizayi_yukle()

st.title("🤖 Kanka AI & Türk Tarihi")
st.caption("Matematik, sohbet ve Türk Tarihi Simülasyonu")

if baglam.get("isim"):
    st.success(f"Hoş geldin {baglam['isim']} kanka! ⚡")

# Geçmiş mesajları ekranda gösterme
for mesaj in baglam["gecmis"]:
    with st.chat_message("user"):
        st.write(mesaj["kullanici"])
    with st.chat_message("assistant"):
        st.write(mesaj["bot"])

# Kullanıcı girdi kutusu
if kullanici_girdisi := st.chat_input("Bir şeyler yaz kanka... (Örn: 'Türk tarihi', '5+5', 'Nasılsın')"):
    # Kullanıcı mesajını ekrana bas
    with st.chat_message("user"):
        st.write(kullanici_girdisi)

    # Cevabı üret
    bot_cevabi = cevap_uret(kullanici_girdisi, baglam)

    # Bot mesajını ekrana bas
    with st.chat_message("assistant"):
        st.write(bot_cevabi)

    # Geçmişe ekle
    baglam["gecmis"].append({"kullanici": kullanici_girdisi, "bot": bot_cevabi})
