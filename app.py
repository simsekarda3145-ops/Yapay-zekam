import json
import os
import random
import re
import sys
import time
from html.parser import HTMLParser
import requests

# ------------------------------------------------------------------
# Hafıza dosyası (bot kapatılıp açılsa bile hatırlasın diye)
# ------------------------------------------------------------------
HAFIZA_DOSYASI = os.path.join(os.getcwd(), "kanka_hafiza.json")


def hafizayi_yukle():
    if os.path.exists(HAFIZA_DOSYASI):
        try:
            with open(HAFIZA_DOSYASI, "r", encoding="utf-8") as f:
                veri = json.load(f)
                veri.setdefault("isim", None)
                veri.setdefault("son_kategori", None)
                veri.setdefault("son_cevap", None)
                veri.setdefault("gecmis", [])
                veri.setdefault("tarih_modu", False)
                veri.setdefault("tarih_indeks", 0)
                return veri
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "isim": None,
        "son_kategori": None,
        "son_cevap": None,
        "gecmis": [],
        "tarih_modu": False,
        "tarih_indeks": 0,
    }


def hafizayi_kaydet(baglam):
    try:
        with open(HAFIZA_DOSYASI, "w", encoding="utf-8") as f:
            # Sadece kaydedilebilir/kalıcı alanları yazıyoruz
            json.dump(
                {
                    "isim": baglam.get("isim"),
                    "son_kategori": baglam.get("son_kategori"),
                    "son_cevap": baglam.get("son_cevap"),
                    "gecmis": baglam.get("gecmis", [])[-50:],  # son 50 mesajla sınırlı
                    "tarih_modu": baglam.get("tarih_modu", False),
                    "tarih_indeks": baglam.get("tarih_indeks", 0),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
    except OSError:
        pass  # Kaydedemezsek sohbeti bozmayalım, sessizce geçelim


# ------------------------------------------------------------------
# Chrome Yer İmleri (Bookmarks) entegrasyonu
# ------------------------------------------------------------------
# Chrome, yer imlerini bilgisayarında düz bir JSON dosyasında tutar.
# Bu fonksiyonlar o dosyayı bulup okuyor - hiçbir veri internete
# gönderilmiyor, sadece kendi bilgisayarındaki dosya okunuyor. Bu özellik
# doğal olarak SADECE botu kendi bilgisayarında (Chrome kuruluyken)
# çalıştırdığında işe yarar.
def chrome_yer_imleri_dosyasini_bul():
    ev_dizini = os.path.expanduser("~")

    if sys.platform.startswith("win"):
        olasi_ana_dizinler = [
            os.path.join(ev_dizini, "AppData", "Local", "Google", "Chrome", "User Data"),
            os.path.join(ev_dizini, "AppData", "Local", "Chromium", "User Data"),
        ]
    elif sys.platform == "darwin":
        olasi_ana_dizinler = [
            os.path.join(ev_dizini, "Library", "Application Support", "Google", "Chrome"),
            os.path.join(ev_dizini, "Library", "Application Support", "Chromium"),
        ]
    else:
        olasi_ana_dizinler = [
            os.path.join(ev_dizini, ".config", "google-chrome"),
            os.path.join(ev_dizini, ".config", "chromium"),
        ]

    bulunan_dosyalar = []
    for ana_dizin in olasi_ana_dizinler:
        if not os.path.isdir(ana_dizin):
            continue
        for profil_adi in os.listdir(ana_dizin):
            aday_dosya = os.path.join(ana_dizin, profil_adi, "Bookmarks")
            if os.path.isfile(aday_dosya):
                bulunan_dosyalar.append(aday_dosya)

    if not bulunan_dosyalar:
        return None

    # "Default" profilini varsa öne alalım, genelde asıl kullanılan odur
    bulunan_dosyalar.sort(key=lambda yol: 0 if "Default" in yol else 1)
    return bulunan_dosyalar[0]


def chrome_yer_imlerini_oku():
    """
    Bulunan Bookmarks dosyasını okuyup düz bir liste hâline getirir:
    [{"baslik": ..., "url": ...}, ...]
    Dosya bulunamazsa ya da okunamazsa None döner.
    """
    dosya_yolu = chrome_yer_imleri_dosyasini_bul()
    if not dosya_yolu:
        return None

    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            veri = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    yer_imleri = []

    def klasoru_gez(dugum):
        if dugum.get("type") == "url":
            yer_imleri.append({"baslik": dugum.get("name", "İsimsiz"), "url": dugum.get("url", "")})
        elif dugum.get("type") == "folder":
            for cocuk in dugum.get("children", []):
                klasoru_gez(cocuk)

    for kok_klasor in veri.get("roots", {}).values():
        if isinstance(kok_klasor, dict):
            klasoru_gez(kok_klasor)

    return yer_imleri


YER_IMI_TETIKLEYICILERI = ["yer imlerim", "yer imi", "bookmarklarım", "bookmark", "favorilerim"]
# Arama terimini çıkarırken elenecek "dolgu" kelimeler
YER_IMI_DURAK_KELIMELERI = {
    "yer", "imlerim", "imlerimde", "imlerimi", "imi", "bookmarklarım",
    "bookmarklarımda", "bookmark", "favorilerim", "var", "mı", "mi",
    "ara", "bul", "içinde", "geçen", "göster", "listele", "olan", "kanka",
}


def yer_imi_arama_terimini_cikar(girdi_alt):
    kelimeler = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ0-9]+", girdi_alt)
    kalanlar = [k for k in kelimeler if k not in YER_IMI_DURAK_KELIMELERI]
    return " ".join(kalanlar).strip()


def yer_imlerine_cevap_ver(girdi_alt):
    yer_imleri = chrome_yer_imlerini_oku()

    if yer_imleri is None:
        return (
            "Kanka bilgisayarında Chrome yer imlerini bulamadım. Bu özellik "
            "sadece botu KENDİ bilgisayarında, Chrome kuruluyken çalıştırdığında "
            "işe yarıyor - şu an çalıştığın ortamda Chrome profili yok gibi görünüyor."
        )

    if not yer_imleri:
        return "Kanka Chrome'unu buldum ama hiç yer imin yok gibi görünüyor."

    arama_terimi = yer_imi_arama_terimini_cikar(girdi_alt)

    if arama_terimi:
        eslesenler = [
            y for y in yer_imleri
            if arama_terimi.lower() in y["baslik"].lower() or arama_terimi.lower() in y["url"].lower()
        ]
        if not eslesenler:
            return f"Kanka yer imlerinde '{arama_terimi}' ile ilgili bir şey bulamadım."
        liste = "\n".join(f"- {y['baslik']} ({y['url']})" for y in eslesenler[:10])
        return f"Kanka '{arama_terimi}' ile ilgili {len(eslesenler)} yer imi buldum:\n{liste}"

    liste = "\n".join(f"- {y['baslik']} ({y['url']})" for y in yer_imleri[:15])
    toplam = len(yer_imleri)
    return f"Kanka toplam {toplam} yer imin var, ilk {min(15, toplam)} tanesi:\n{liste}"


# ------------------------------------------------------------------
# Gerçek internet gezinme: kullanıcı bir site/domain yazınca bot oraya
# gerçekten girip içeriği okuyor ve kendi cümleleriyle özetliyor.
# ------------------------------------------------------------------
URL_DESENI = re.compile(
    r"((?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?)",
    re.IGNORECASE,
)


class _MetinCikarici(HTMLParser):
    """HTML içinden sadece görünen metni (script/style hariç) ve başlığı çıkarır."""

    def __init__(self):
        super().__init__()
        self.metin_parcalari = []
        self.gizli_etiket_icinde = False
        self.baslik_metni = ""
        self.baslik_okunuyor = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.gizli_etiket_icinde = True
        if tag == "title":
            self.baslik_okunuyor = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.gizli_etiket_icinde = False
        if tag == "title":
            self.baslik_okunuyor = False

    def handle_data(self, data):
        if self.baslik_okunuyor:
            self.baslik_metni += data
        elif not self.gizli_etiket_icinde:
            temiz = data.strip()
            if temiz:
                self.metin_parcalari.append(temiz)


def web_sayfasi_oku(url):
    """
    Verilen adrese gerçekten bir HTTP isteği atar, HTML'i indirir ve
    içindeki görünen metni çıkarır. (baslik, metin) tuple'ı ya da
    hata durumunda (None, hata_mesaji) döner.
    """
    try:
        yanit = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (KankaBot; kişisel kullanım)"},
        )
        yanit.raise_for_status()
    except requests.RequestException as e:
        return None, f"o siteye giremedim, bir bağlantı sorunu var ({e})"

    icerik_turu = yanit.headers.get("Content-Type", "")
    if "html" not in icerik_turu.lower():
        return None, "o adres bir web sayfası değil gibi görünüyor (HTML değil)"

    cikarici = _MetinCikarici()
    try:
        cikarici.feed(yanit.text)
    except Exception:
        pass

    metin = re.sub(r"\s+", " ", " ".join(cikarici.metin_parcalari)).strip()
    baslik = cikarici.baslik_metni.strip()
    return {"baslik": baslik, "metin": metin}, None


def url_bul(girdi):
    eslesme = URL_DESENI.search(girdi)
    if not eslesme:
        return None
    ham = eslesme.group(0)
    if not ham.lower().startswith("http"):
        ham = "https://" + ham
    return ham


def web_gezinme_cevabi_uret(girdi):
    tam_url = url_bul(girdi)
    if not tam_url:
        return None

    sonuc, hata = web_sayfasi_oku(tam_url)
    if hata:
        return f"Kanka {hata}."

    baslik = sonuc["baslik"] or "(başlık bulunamadı)"
    ozet = sonuc["metin"][:500]
    if len(sonuc["metin"]) > 500:
        ozet += "..."

    if not ozet:
        return f"Kanka {tam_url} adresine girdim ('{baslik}') ama okunabilir bir metin bulamadım."

    return f"Kanka {tam_url} adresine girdim. Başlık: '{baslik}'.\n\nİçerikten bir kesit:\n{ozet}"


# ------------------------------------------------------------------
# Matematik işlem kontrolü
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
# Cevap havuzu
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

# ------------------------------------------------------------------
# Türk Tarihi zaman tüneli (Göktürkler'den Cumhuriyet'e kronoloji)
# ------------------------------------------------------------------
TARIH_KRONOLOJISI = [
    {
        "donem": "Göktürk Kağanlığı (552-744)",
        "bilgi": "Tarihte 'Türk' adını taşıyan bilinen ilk devlet. Bumin Kağan tarafından kuruldu. Orhun Anıtları (Bilge Kağan, Kültigin, Tonyukuk) bu döneme ait.",
    },
    {
        "donem": "Uygur Devleti (744-840)",
        "bilgi": "Göktürkler'in ardından kuruldu. Türk devletleri arasında yerleşik hayata geçen ilk topluluklardan, kendi alfabelerini geliştirdiler.",
    },
    {
        "donem": "Karahanlılar (840-1212)",
        "bilgi": "İslamiyet'i resmî din olarak kabul eden ilk Türk devleti. Satuk Buğra Han döneminde İslam'a geçiş yaşandı.",
    },
    {
        "donem": "Büyük Selçuklu Devleti (1037-1194)",
        "bilgi": "Tuğrul Bey tarafından kuruldu. 1071'deki Malazgirt Zaferi ile Anadolu'nun kapıları Türklere açıldı.",
    },
    {
        "donem": "Anadolu Selçuklu Devleti (1075-1308)",
        "bilgi": "Anadolu'da kurulan ilk büyük Türk devleti, başkenti Konya idi. Moğol baskısıyla zayıflayıp beyliklere bölündü.",
    },
    {
        "donem": "Beylikler Dönemi (1300'ler)",
        "bilgi": "Anadolu Selçuklu'nun dağılmasıyla ortaya çıkan küçük Türk beylikleri dönemi. Bunlardan biri de kuzeybatıdaki küçük Osmanlı Beyliği'ydi.",
    },
    {
        "donem": "Osmanlı Devleti - Kuruluş (1299-1453)",
        "bilgi": "Osman Gazi tarafından kuruldu. 1453'te Fatih Sultan Mehmed İstanbul'u fethederek Bizans'a son verdi.",
    },
    {
        "donem": "Osmanlı Devleti - Yükselme (1453-1579)",
        "bilgi": "Kanuni Sultan Süleyman döneminde sınırlar üç kıtaya (Avrupa, Asya, Afrika) yayıldı, imparatorluk zirvedeydi.",
    },
    {
        "donem": "Osmanlı Devleti - Duraklama (1579-1699)",
        "bilgi": "Avrupa'daki teknolojik ve askeri gelişmelere ayak uydurulamadı, savaşlarda ilk ciddi toprak kayıpları başladı.",
    },
    {
        "donem": "Osmanlı Devleti - Gerileme (1699-1792)",
        "bilgi": "Toprak kayıpları hızlandı, ıslahat girişimleri (III. Selim'in Nizam-ı Cedid'i gibi) yetersiz kaldı.",
    },
    {
        "donem": "Osmanlı Devleti - Dağılma (1792-1922)",
        "bilgi": "Milliyetçilik akımları imparatorluğu içten sardı, I. Dünya Savaşı yenilgisiyle Osmanlı Devleti sona erdi.",
    },
    {
        "donem": "Kurtuluş Savaşı (1919-1922)",
        "bilgi": "Mustafa Kemal Atatürk önderliğinde işgale karşı verilen bağımsızlık mücadelesi. 1922'de zaferle sonuçlandı.",
    },
    {
        "donem": "Türkiye Cumhuriyeti (1923-günümüz)",
        "bilgi": "29 Ekim 1923'te Cumhuriyet ilan edildi, Mustafa Kemal Atatürk ilk cumhurbaşkanı oldu. Modern Türkiye'nin temelleri bu dönemde atıldı.",
    },
]

tarih_tetikleyicileri = ["türk tarihi", "tarih anlat", "kronoloji", "tarihi süreç", "tarih özeti", "türklerin tarihi"]
tarih_devam_kelimeleri = ["devam", "sonra", "ilerle", "next"]
tarih_cikis_kelimeleri = ["çık", "dur", "yeter", "kes"]

# Belirli bir olay/kişi/tarih sorulduğunda anında cevap vermek için
# ayrı bir soru-cevap bilgi bankası (zaman tüneli turundan bağımsız).
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

# Ruh hali tespiti için ayrı bir kelime havuzu (herhangi bir mesajda geçerli)
ruh_hali_kelimeleri = {
    "mutlu": ["mutluyum", "harikayım", "süperim", "keyifliyim", "sevindim"],
    "uzgun": ["üzgünüm", "üzüldüm", "moralim bozuk", "kötüyüm", "canım sıkkın"],
    "kizgin": ["sinirliyim", "kızgınım", "öfkeliyim", "bıktım", "stresliyim"],
    "yorgun": ["yorgunum", "bitkinim", "uykum var", "yoruldum"],
}


def kelime_eslesiyor_mu(kelime, metin):
    desen = r"\b" + re.escape(kelime) + r"\b"
    return re.search(desen, metin) is not None


def kok_eslesiyor_mu(kok, metin):
    desen = r"\b" + re.escape(kok)
    return re.search(desen, metin) is not None


def esnek_eslesiyor_mu(kelime, metin):
    """
    Kısa kelimeler (sa, ve, iyi gibi) için TAM kelime sınırı arar
    (yanlış eşleşmeleri önlemek için), 4+ harfli kelimeler için ise
    Türkçe ek durumlarını (oyunu, filmi, maçtan gibi) yakalamak adına
    sadece kelimenin başlangıcını arar.
    """
    if len(kelime) <= 3:
        return kelime_eslesiyor_mu(kelime, metin)
    return kok_eslesiyor_mu(kelime, metin)


def levenshtein_mesafesi(a, b):
    """İki kelime arasında kaç harf ekleme/silme/değiştirme gerektiğini hesaplar."""
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
    """
    Kullanıcı yazım hatası yapmış olabilir (ör. 'nasılsn', 'slam',
    'valornt'). Levenshtein mesafesi ile metindeki her kelimenin hedef
    kelimeden kaç harf farklı olduğuna bakıyoruz. Kısa kelimelerde 1
    harflik, uzun kelimelerde 2 harflik farka izin veriyoruz - aksi
    halde 'steam' ile 'selam' gibi alakasız ama harf dizilimi benzeyen
    kelimeler yanlışlıkla eşleşebiliyor (bunu test ederken yakaladık).

    Çok kelimeli ifadeler (ör. 'ne haber') için bunu uygulamıyoruz,
    çünkü kelime kelime karşılaştırmak yanıltıcı olur; onlar için
    esnek_eslesiyor_mu yeterli.
    """
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
    """
    Önce hızlı/kesin kontrolü dener (esnek_eslesiyor_mu). Bulamazsa ve
    kelime yeterince uzunsa (kısa kelimelerde yanlış pozitif riski
    yüksek olduğu için 4+ harf şartı koyduk), yazım hatalarını tolere
    eden bulanık eşleşmeyi dener.
    """
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


# ------------------------------------------------------------------
# İnsansı doğallık: dolgu kelimeleri ve ufak "yazım hataları"
# ------------------------------------------------------------------
DOLGU_KELIMELERI = ["Yani, ", "Hmm, ", "Valla, ", "Aslında, ", "İşte, ", "Şey, "]

# Neredeyse her kategoriye eklenebilecek genel, doğal takip cümleleri.
# Bunlar her seferinde rastgele seçildiği için cevaplar kalıba girmiyor.
genel_ek_yorumlar = [
    "Neyse, sen anlat bakalım.",
    "Bu arada bugün nasıl geçti sence?",
    "Söz sırası sende kanka.",
    "Hadi devam et, dinliyorum.",
    "Sen ne düşünüyorsun bu konuda?",
]


def turkce_kucuk_harf(karakter):
    """
    Python'ın varsayılan .lower() metodu Türkçe 'İ' harfini yanlış
    küçültüyor (i̇ gibi bozuk çıkıyor). Bunu elle düzeltiyoruz.
    """
    ozel_durumlar = {"İ": "i", "I": "ı"}
    return ozel_durumlar.get(karakter, karakter.lower())


def dogal_dolgu_ekle(cevap):
    """Cevabın başına bazen doğal bir konuşma dolgusu ekler."""
    if random.random() < 0.3:
        dolgu = random.choice(DOLGU_KELIMELERI)
        return dolgu + turkce_kucuk_harf(cevap[0]) + cevap[1:]
    return cevap


def yazim_hatasi_ekle(cevap):
    """
    Bazen (düşük ihtimalle) cevaptaki bir kelimede insansı bir yazım hatası
    yapıp hemen ardından kendini düzeltir. Tıpkı hızlı yazan biri gibi:
    'yarnın... yarın demek istedim'
    """
    if random.random() >= 0.12:
        return cevap

    kelimeler = cevap.split(" ")
    aday_indeksler = [i for i, k in enumerate(kelimeler) if len(re.sub(r"[^\wğüşıöçĞÜŞİÖÇ]", "", k)) >= 4]
    if not aday_indeksler:
        return cevap

    i = random.choice(aday_indeksler)
    orijinal_kelime = kelimeler[i]
    harfler = list(orijinal_kelime)
    # Kelimenin ortasından iki harfi yer değiştiriyoruz (klasik hızlı yazma hatası)
    j = random.randint(1, len(harfler) - 2)
    harfler[j], harfler[j + 1] = harfler[j + 1], harfler[j]
    hatali_kelime = "".join(harfler)

    hatali_kelimeler = kelimeler.copy()
    hatali_kelimeler[i] = hatali_kelime
    hatali_cevap = " ".join(hatali_kelimeler)

    return f"{hatali_cevap}* {orijinal_kelime} demek istedim"


def insanilastir(cevap, kategori):
    """
    Matematik sonucu ve isim tanıma gibi hassas/kesin bilgi içeren
    cevaplara dokunmuyoruz (yanlış anlaşılmasınlar diye). Diğer sohbet
    cevaplarına doğallık katıyoruz.
    """
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
    """
    Kullanıcı belirli bir tarihi olay/kişi/dönemden bahsettiğinde
    (ör. 'malazgirt ne zaman', 'atatürk kimdir'), zaman tüneli turunu
    başlatmadan direkt ve kısa bir cevap veriyoruz. Birden fazla anahtar
    eşleşirse ilk bulunanı döndürüyoruz.
    """
    for anahtar, cevap in TARIH_SORU_CEVAPLARI.items():
        if akilli_eslesiyor_mu(anahtar, girdi_alt):
            onsoz = random.choice(TARIH_CEVAP_ONSOZLERI)
            return onsoz + cevap
    return None


def cevap_uret(girdi, baglam):
    girdi_alt = girdi.lower()
    ruh_hali = ruh_hali_tespit_et(girdi_alt)

    # ADIM -1: Tarih zaman tüneli modundaysak, önce buna bakıyoruz
    if baglam.get("tarih_modu"):
        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in tarih_devam_kelimeleri):
            yeni_indeks = baglam.get("tarih_indeks", 0) + 1
            if yeni_indeks < len(TARIH_KRONOLOJISI):
                baglam["tarih_indeks"] = yeni_indeks
                donem = TARIH_KRONOLOJISI[yeni_indeks]
                cevap = (
                    f"📜 {donem['donem']}\n{donem['bilgi']}\n\n"
                    "(Devam etmek için 'devam' yaz, çıkmak için 'çık' yaz kanka.)"
                )
            else:
                baglam["tarih_modu"] = False
                baglam["tarih_indeks"] = 0  # tur bitti, bir dahaki sefere baştan başlasın
                cevap = (
                    "İşte kanka, Göktürkler'den Cumhuriyet'e koca bir yolculuk yaptık! "
                    "Türk tarihi turu burada bitti. 🇹🇷"
                )
            baglam["son_kategori"] = "tarih"
            baglam["son_cevap"] = cevap
            return cevap

        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in tarih_cikis_kelimeleri):
            baglam["tarih_modu"] = False
            cevap = "Tamam kanka, tarih turunu burada bırakıyoruz. İstersen sonra 'türk tarihi' yaz, kaldığımız yerden devam ederiz."
            baglam["son_kategori"] = "tarih_cikis"
            baglam["son_cevap"] = cevap
            return cevap

        # Ne devam ne çıkış dedi -> modu sessizce kapatıp mesajı normal işliyoruz
        baglam["tarih_modu"] = False

    # ADIM 0: İsim paylaşımı
    isim = isim_tespit_et(girdi_alt)
    if isim:
        baglam["isim"] = isim
        baglam["son_kategori"] = "isim_tanima"
        cevap = f"Tanıştığımıza sevindim {isim} kanka, artık seni hatırlıyorum!"
        baglam["son_cevap"] = cevap
        return cevap

    # ADIM 1: Matematik isteği
    matematik_sonucu = matematik_islemi_yap(girdi_alt)
    if matematik_sonucu:
        baglam["son_kategori"] = "matematik"
        baglam["son_cevap"] = matematik_sonucu
        return matematik_sonucu

    # ADIM 1.3: Mesajda bir web adresi/domain var mı? -> gerçekten oraya girip oku
    web_cevabi = web_gezinme_cevabi_uret(girdi)
    if web_cevabi:
        baglam["son_kategori"] = "web_gezinme"
        baglam["son_cevap"] = web_cevabi
        return web_cevabi

    # ADIM 1.4: Chrome yer imleri sorgusu
    if any(akilli_eslesiyor_mu(k, girdi_alt) for k in YER_IMI_TETIKLEYICILERI):
        cevap = yer_imlerine_cevap_ver(girdi_alt)
        baglam["son_kategori"] = "yer_imleri"
        baglam["son_cevap"] = cevap
        return cevap

    # ADIM 1.5: Belirli bir tarihi olay/kişi soruldu mu? -> anında direkt cevap
    tarih_cevabi = tarih_sorusu_cevapla(girdi_alt)
    if tarih_cevabi:
        baglam["son_kategori"] = "tarih_soru"
        baglam["son_cevap"] = tarih_cevabi
        return tarih_cevabi

    # ADIM 1.6: Türk tarihi turu başlatma isteği
    if any(akilli_eslesiyor_mu(k, girdi_alt) for k in tarih_tetikleyicileri):
        baglam["tarih_modu"] = True
        mevcut_indeks = baglam.get("tarih_indeks", 0)

        # Daha önce yarıda bırakılmış bir tur varsa (turu bitirmeden 'çık'
        # demişse), kaldığı yerden devam ediyoruz. Turu tamamen bitirmişse
        # ya da hiç başlamamışsa baştan alıyoruz.
        if 0 < mevcut_indeks < len(TARIH_KRONOLOJISI):
            donem = TARIH_KRONOLOJISI[mevcut_indeks]
            cevap = (
                f"Kaldığımız yerden devam ediyoruz kanka! 🇹🇷\n\n"
                f"📜 {donem['donem']}\n{donem['bilgi']}\n\n"
                "(Devam etmek için 'devam' yaz, istediğin an 'çık' diyebilirsin.)"
            )
        else:
            baglam["tarih_indeks"] = 0
            ilk_donem = TARIH_KRONOLOJISI[0]
            cevap = (
                "Hadi kanka, Türk tarihini Göktürkler'den başlayıp Cumhuriyet'e kadar birlikte gezelim! 🇹🇷\n\n"
                f"📜 {ilk_donem['donem']}\n{ilk_donem['bilgi']}\n\n"
                "(Devam etmek için 'devam' yaz, istediğin an 'çık' diyebilirsin.)"
            )
        baglam["son_kategori"] = "tarih"
        baglam["son_cevap"] = cevap
        return cevap

    # ADIM 2: Bağlama duyarlı "nasılsın" takibi
    if baglam.get("son_kategori") == "hal_hatir":
        # Not: burada bilerek kok_eslesiyor_mu kullanıyoruz (akilli_eslesiyor_mu
        # değil) çünkü 'iyi' gibi 3 harfli kelimeler akilli_eslesiyor_mu'da
        # güvenlik amaçlı sıkı sınır kontrolüne takılıyor ve 'iyiyim' gibi
        # çekimli hallerini yakalayamıyor. Bu kontrol zaten dar bir bağlamda
        # (son mesaj 'nasılsın' olduğunda) çalıştığı için yanlış pozitif riski düşük.
        if any(kok_eslesiyor_mu(k, girdi_alt) for k in iyi_kelimeler):
            cevap = cevap_sec("hal_hatir_devam_iyi", baglam)
            cevap = ruh_haline_gore_uyarla(cevap, ruh_hali)
            cevap = insanilastir(cevap, "hal_hatir_devam_iyi")
            baglam["son_kategori"] = "hal_hatir_devam"
            baglam["son_cevap"] = cevap
            return cevap
        if any(kok_eslesiyor_mu(k, girdi_alt) for k in kotu_kelimeler):
            cevap = cevap_sec("hal_hatir_devam_kotu", baglam)
            cevap = ruh_haline_gore_uyarla(cevap, ruh_hali)
            cevap = insanilastir(cevap, "hal_hatir_devam_kotu")
            baglam["son_kategori"] = "hal_hatir_devam"
            baglam["son_cevap"] = cevap
            return cevap

    # ADIM 3: Çoklu niyet taraması -> mesajda birden fazla konu geçebilir
    eslesen_kategoriler = [
        kategori
        for kategori, kelimeler in kategori_kelimeleri
        if any(akilli_eslesiyor_mu(k, girdi_alt) for k in kelimeler)
    ]

    if len(eslesen_kategoriler) >= 2:
        # En fazla 2 konuya birden cevap veriyoruz, mesaj çok uzamasın
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
# Ana Çalışma Döngüsü
# ------------------------------------------------------------------
def main():
    print("=============================================")
    print("=== FULL SÜRÜM HESAP+SOHBET KANKA AI AÇILDI ===")
    print("=============================================")

    baglam = hafizayi_yukle()

    if baglam.get("isim"):
        print(f"Kanka Bot: Tekrar hoş geldin {baglam['isim']} kanka, seni hatırlıyorum!\n")
    else:
        print("Kanka Bot: Hafıza ve matematik beyni yüklendi. Çıkış için 'çıkış' yaz kanka.\n")

    while True:
        kullanici_girdisi = input("Sen: ")

        if kullanici_girdisi.lower() in ["çıkış", "quit", "exit", "kapat", "baybay"]:
            isim = baglam.get("isim")
            if isim:
                print(f"Kanka Bot: Eyvallah {isim} kanka, hafta sonu görüşürüz. Kendine iyi bak!")
            else:
                print("Kanka Bot: Eyvallah kanka, hafta sonu görüşürüz. Kendine iyi bak!")
            hafizayi_kaydet(baglam)
            break

        if not kullanici_girdisi.strip():
            print("Kanka Bot: Boş gönderme kanka, bir şeyler yaz hadi.")
            continue

        print("Kanka Bot yazıyor...", end="\r")
        time.sleep(random.uniform(0.6, 1.3))

        cevap = cevap_uret(kullanici_girdisi, baglam)
        print(f"Kanka Bot: {cevap}")
        print("-" * 40)

        baglam.setdefault("gecmis", []).append({"kullanici": kullanici_girdisi, "bot": cevap})
        hafizayi_kaydet(baglam)


if __name__ == "__main__":
    main()
