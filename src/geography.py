"""Curated title aliases, intentionally incomplete; unknown locations stay unknown.

District labels may combine a city/regency with the same name. They are grouping
keys, not official administrative codes. Province is the reporting dimension.
"""
import re
from src.core import PROVINCES

DISTRICTS = {
    'Aceh': 'Bireuen|Bireun;Bener Meriah;Aceh Selatan;Aceh Utara;Aceh Timur;Banda Aceh',
    'Sumatera Utara': 'Karo|Berastagi;Dairi|Sidikalang;Humbang Hasundutan|Humbahas;Deli Serdang;Medan;Simalungun;Tapanuli Utara;Toba',
    'Sumatera Barat': 'Agam;Pariaman;Padang;Padang Pariaman;Tanah Datar;Pasaman;Lima Puluh Kota',
    'Riau': 'Pekanbaru;Siak;Kampar;Bengkalis',
    'Kepulauan Riau': 'Kepulauan Anambas|Anambas;Batam;Bintan;Tanjungpinang;Karimun;Natuna',
    'Jambi': 'Kota Jambi;Muaro Jambi;Bungo',
    'Sumatera Selatan': 'Palembang;Ogan Ilir;Banyuasin;Ogan Komering Ilir',
    'Bengkulu': 'Kota Bengkulu;Bengkulu Utara',
    'Lampung': 'Tanggamus|Talang Padang;Bandar Lampung;Lampung Utara;Lampung Selatan;Lampung Timur;Pringsewu;Pesawaran;Metro',
    'Kepulauan Bangka Belitung': 'Bangka;Belitung;Pangkalpinang',
    'DKI Jakarta': 'Jakarta Timur|Jaktim|Cakung|Duren Sawit|Pondok Kelapa;Jakarta Selatan|Jaksel;Jakarta Utara|Jakut;Jakarta Barat|Jakbar;Jakarta Pusat|Jakpus',
    'Banten': 'Serang|Padarincang;Cilegon;Tangerang Selatan|Tangsel;Tangerang;Pandeglang;Lebak',
    'Jawa Barat': 'Bogor|Dramaga;Cirebon;Indramayu|Anjatan;Sukabumi|Gunungguruh;Cianjur;Garut;Cimahi;Bandung Barat;Bandung;Tasikmalaya;Subang;Sumedang;Majalengka;Bekasi;Depok;Purwakarta;Karawang;Kuningan;Ciamis;Pangandaran',
    'Jawa Tengah': 'Grobogan|Gubug;Kudus;Pati;Semarang;Magelang|Candimulyo;Klaten|Kalikotes;Purworejo;Wonogiri|Jatisrono;Rembang|Lasem;Tegal;Pemalang;Pekalongan|Kedungwuni;Boyolali;Sragen;Sukoharjo;Karanganyar;Banyumas;Banjarnegara;Kebumen;Demak;Blora;Jepara;Brebes;Temanggung;Wonosobo;Surakarta|Solo',
    'DI Yogyakarta': 'Bantul;Sleman;Kulon Progo;Gunungkidul;Kota Yogyakarta',
    'Jawa Timur': 'Mojokerto|Mojoanyar|Mojosari;Tulungagung|Boyolangu;Kediri;Malang;Surabaya;Sidoarjo;Jember|Kaliwates;Bangkalan;Ngawi;Jombang;Pasuruan|Pandaan;Probolinggo;Gresik;Lamongan;Tuban;Bojonegoro;Nganjuk;Madiun;Magetan;Ponorogo;Blitar;Banyuwangi;Bondowoso;Situbondo;Lumajang;Sampang;Pamekasan;Sumenep;Trenggalek;Pacitan;Batu',
    'Bali': 'Denpasar;Badung;Gianyar;Buleleng;Tabanan;Klungkung;Karangasem;Bangli;Jembrana',
    'Nusa Tenggara Barat': 'Lombok Barat|Lingsar;Lombok Timur;Lombok Tengah;Lombok Utara;Mataram;Bima;Sumbawa;Dompu',
    'Nusa Tenggara Timur': 'Timor Tengah Utara|TTU|Insana;Kupang;Timor Tengah Selatan|TTS;Belu;Ende;Sikka;Manggarai;Manggarai Barat;Manggarai Timur',
    'Kalimantan Barat': 'Ketapang;Singkawang;Pontianak;Sambas;Sanggau;Kubu Raya;Sintang',
    'Kalimantan Tengah': 'Palangka Raya;Kotawaringin Timur;Kotawaringin Barat',
    'Kalimantan Selatan': 'Banjarmasin;Banjarbaru;Tanah Laut',
    'Kalimantan Timur': 'Samarinda;Balikpapan;Kutai Kartanegara;Bontang',
    'Kalimantan Utara': 'Tarakan;Bulungan;Nunukan',
    'Sulawesi Utara': 'Tomohon;Manado;Bitung;Minahasa',
    'Gorontalo': 'Kota Gorontalo',
    'Sulawesi Tengah': 'Palu;Donggala;Parigi Moutong;Poso',
    'Sulawesi Barat': 'Majene;Polewali Mandar|Polman;Mamuju',
    'Sulawesi Selatan': 'Tana Toraja;Toraja Utara;Makassar;Gowa;Maros;Bone',
    'Sulawesi Tenggara': 'Kendari;Kolaka|Watubangga;Baubau;Konawe;Konawe Selatan;Konawe Utara',
    'Maluku': 'Ambon;Maluku Tengah;Tual',
    'Maluku Utara': 'Ternate;Tidore',
    'Papua': 'Jayapura|Sentani',
    'Papua Barat': 'Manokwari;Fakfak',
    'Papua Barat Daya': 'Sorong;Raja Ampat',
    'Papua Tengah': 'Nabire;Mimika|Timika',
    'Papua Pegunungan': 'Jayawijaya|Wamena',
    'Papua Selatan': 'Merauke',
}
# Within-district locality evidence avoids merging nearby simultaneous outbreaks.
LOCALITIES = {
    'Bogor': ['dramaga', 'cisarua', 'cibinong'],
    'Grobogan': ['gubug', 'pulongrambe'],
    'Klaten': ['tulung', 'kalikotes'],
    'Magelang': ['candimulyo'],
    'Mojokerto': ['mojoanyar', 'mojosari'],
    'Kediri': ['kras'],
    'Tanggamus': ['kedaloman', 'talang padang'],
    'Jakarta Timur': ['cakung', 'pondok kelapa', 'duren sawit'],
    'Cirebon': ['kalijaga'],
    'Surabaya': ['tembok dukuh'],
}

def hit(text, phrase):
    return bool(re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text, re.I))

def locate(title):
    text = title.lower()
    # Remove administrative labels found inside a longer one (Padang Pariaman).
    hits = []
    for province, groups in DISTRICTS.items():
        for group in groups.split(';'):
            aliases = group.split('|')
            for alias in aliases:
                if hit(text, alias):
                    hits.append((alias.lower(), aliases[0], province))
    hits = [x for x in hits if not any(x[0] != y[0] and x[0] in y[0] for y in hits)]
    locations = sorted({(district, province) for _, district, province in hits})
    if len(locations) == 1:
        district, province = locations[0]
        explicit = [p for p in PROVINCES if hit(text, p)]
        explicit = [p for p in explicit if not any(p != q and p in q for q in explicit)]
        if any(p != province for p in explicit):
            return '', '', '', 'Lokasi/provinsi ganda atau bertentangan'
        areas = [area for area in LOCALITIES.get(district, []) if hit(text, area)]
        if district == 'Jakarta Timur' and 'duren sawit' in areas:
            areas = list(set(areas) - {'duren sawit'} | {'pondok kelapa'})
        return province, district, '|'.join(sorted(areas)), 'Kamus nama wilayah pada judul'
    if len(locations) > 1:
        return '', '', '', 'Beberapa wilayah disebut; jangan membagi korban secara otomatis'
    provinces = [p for p in PROVINCES if hit(text, p)]
    provinces = [p for p in provinces if not any(p != q and p in q for q in provinces)]
    return (provinces[0] if len(provinces) == 1 else ''), '', '', 'Kabupaten/lokasi belum terpetakan'
