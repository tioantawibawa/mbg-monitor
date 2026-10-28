import altair as alt
import pandas as pd
import streamlit as st

from src.core import safe_csv
from src.text_analysis import COLORS, LABELS, THEMES, cloud_png, enrich, word_counts

@st.cache_data(show_spinner=False, max_entries=24)
def cached_cloud(items, limit):
    return cloud_png(dict(items), limit)

def render_insights(news):
    data = enrich(news)
    overview, sentiment, words, education = st.tabs([
        'Dampak dalam berita', 'Sentimen & konteks', 'Word cloud', 'Kenali risiko pangan'])
    with overview:
        st.subheader('Apa dampak yang muncul dalam pemberitaan?')
        st.caption('Semua grafik mengikuti filter di sidebar. Unit hitung adalah artikel, bukan korban atau kejadian unik.')
        if not data:
            st.info('Tidak ada artikel pada filter ini. Pilih periode atau wilayah lain.')
        else:
            counts = [{'Tema': theme, 'Artikel': sum(theme in r['themes'] for r in data)} for theme in THEMES]
            frame = pd.DataFrame(counts)
            frame['Persentase'] = frame.Artikel / len(data)
            top = frame.sort_values('Artikel', ascending=False).iloc[0]
            st.write(f"Dari **{len(data):,} artikel** terfilter, **{int(top.Artikel):,}** menyebut istilah dalam tema **{top.Tema.lower()}**. Penyebutan bisa berupa laporan, bantahan, atau langkah pencegahan; baca sumber sebelum menyimpulkan.")
            st.altair_chart(alt.Chart(frame).mark_bar(color='#B45340').encode(
                x=alt.X('Artikel:Q', title='Jumlah artikel yang menyebut tema'),
                y=alt.Y('Tema:N', sort='-x'), tooltip=['Tema', 'Artikel', alt.Tooltip('Persentase:Q', format='.1%')]), width='stretch')
            st.caption('Kategori dapat tumpang tindih. Jumlah lintas tema tidak boleh dijumlahkan sebagai jumlah kasus.')
            months = sorted({r['month'] for r in data})
            monthly = [{'Bulan': month, 'Tema': theme, 'Artikel': sum(r['month'] == month and theme in r['themes'] for r in data)} for month in months for theme in THEMES]
            st.subheader('Perubahan tema dari bulan ke bulan')
            st.altair_chart(alt.Chart(pd.DataFrame(monthly)).mark_rect().encode(
                x=alt.X('Bulan:O', title='Bulan publikasi'), y='Tema:N',
                color=alt.Color('Artikel:Q', scale=alt.Scale(scheme='oranges')),
                tooltip=['Bulan', 'Tema', 'Artikel']), width='stretch')
            st.caption('Sel kosong/0 berarti tidak ada penyebutan yang terdeteksi dalam arsip terfilter, bukan tidak ada dampak di masyarakat. Bulan berjalan belum lengkap.')
            selected_theme = st.selectbox('Telusuri sumber berdasarkan tema', ['Semua tema'] + list(THEMES))
            evidence = [r for r in data if selected_theme == 'Semua tema' or selected_theme in r['themes']]
            st.dataframe(pd.DataFrame([{'Tanggal': r['published_at'][:10], 'Judul': r['clean_title'], 'Penerbit': r['source'], 'Sumber': r['url']} for r in evidence]),
                         hide_index=True, column_config={'Sumber': st.column_config.LinkColumn(display_text='Baca sumber')}, width='stretch')
    with sentiment:
        st.subheader('Nada judul, bukan survei sentimen masyarakat')
        st.warning('Sampel sejak awal disaring dengan kata “keracunan”. Persentase berikut tidak mewakili dukungan/penolakan masyarakat terhadap MBG, seluruh berita MBG, atau dampak bersih program.')
        st.caption('Klasifikasi kamus v1, belum divalidasi pada sampel berlabel manusia. Kata “keracunan” sendiri tidak diberi skor negatif. Negasi, bantahan, dan pencegahan masuk Perlu konteks; tanpa kata pemicu masuk Tidak terklasifikasi, bukan netral.')
        if data:
            frame = pd.DataFrame([{'Nada': label, 'Artikel': sum(r['tone'] == label for r in data)} for label in LABELS])
            frame['Bagian'] = frame.Artikel / len(data)
            st.altair_chart(alt.Chart(frame).mark_bar().encode(
                x=alt.X('Artikel:Q', title='Jumlah artikel'), y=alt.Y('Nada:N', sort=LABELS),
                color=alt.Color('Nada:N', scale=alt.Scale(domain=LABELS, range=COLORS), legend=None),
                tooltip=['Nada', 'Artikel', alt.Tooltip('Bagian:Q', format='.1%')]), width='stretch')
            st.dataframe(frame, hide_index=True, column_config={'Bagian': st.column_config.NumberColumn('Proporsi (0–1)', format='%.3f')})
            trend = pd.DataFrame([{'Bulan': r['month'], 'Nada': r['tone']} for r in data]).groupby(['Bulan', 'Nada']).size().reset_index(name='Artikel')
            st.altair_chart(alt.Chart(trend).mark_bar().encode(
                x=alt.X('Bulan:O', title='Bulan publikasi'), y=alt.Y('Artikel:Q', stack='normalize', title='Proporsi artikel'),
                color=alt.Color('Nada:N', scale=alt.Scale(domain=LABELS, range=COLORS)), tooltip=['Bulan', 'Nada', 'Artikel']), width='stretch')
            st.caption('Tooltip menunjukkan jumlah artikel sebagai dasar persentase. Pergeseran komposisi sumber dapat mengubah grafik tanpa perubahan opini masyarakat.')
            choice = st.selectbox('Audit klasifikasi judul', ['Semua nada'] + LABELS)
            audit = [{'Judul': r['clean_title'], 'Nada': r['tone'], 'Kata pemicu': r['trigger_words'], 'URL': r['url']} for r in data if choice == 'Semua nada' or r['tone'] == choice]
            st.dataframe(pd.DataFrame(audit), hide_index=True, column_config={'URL': st.column_config.LinkColumn(display_text='Buka')}, width='stretch')
            export = [{**r, 'themes': ' | '.join(r['themes'])} for r in data]
            st.download_button('Unduh klasifikasi & kata pemicu', safe_csv(export, list(export[0])), 'mbg-analisis-judul.csv', 'text/csv')
        else:
            st.info('Belum ada judul untuk dianalisis pada filter ini.')
    with words:
        st.subheader('Kata yang menonjol dalam judul')
        st.caption('Ukuran huruf mengikuti jumlah judul yang memuat kata, bukan jumlah korban atau tingkat bahaya. Satu kata dihitung maksimal sekali per judul. Nama penerbit di akhir judul, angka, kata umum, MBG, dan keracunan dikeluarkan.')
        dedupe = st.checkbox('Gabungkan judul identik lintas penerbit untuk word cloud', value=True)
        excluded = st.text_input('Kata tambahan yang ingin disembunyikan', placeholder='Contoh: bgn sppg')
        limit = st.slider('Maksimum kata pada word cloud', 20, 100, 60, step=10)
        frequencies = word_counts(news, excluded, dedupe)
        if frequencies:
            png = cached_cloud(tuple(frequencies.items()), limit)
            st.image(png, caption='Frekuensi kata dalam judul terfilter • warna hanya dekoratif', width='stretch')
            st.download_button('Unduh word cloud PNG', png, 'mbg-wordcloud.png', 'image/png')
            top = pd.DataFrame(list(frequencies.items())[:20], columns=['Kata', 'Jumlah judul'])
            st.altair_chart(alt.Chart(top).mark_bar(color='#0F766E').encode(x='Jumlah judul:Q', y=alt.Y('Kata:N', sort='-x'), tooltip=['Kata', 'Jumlah judul']), width='stretch')
            st.caption('Tabel frekuensi adalah rujukan angka; sebagian kata dapat tidak muat pada gambar. Penggabungan judul di sini tidak mengubah hitungan artikel pada tab lain.')
            st.dataframe(top, hide_index=True)
            st.download_button('Unduh seluruh frekuensi kata', safe_csv([{'kata': k, 'jumlah_judul': v} for k, v in frequencies.items()], ['kata', 'jumlah_judul']), 'mbg-frekuensi-kata.csv', 'text/csv')
        else:
            st.info('Tidak ada kata tersisa. Ubah filter atau daftar kata yang disembunyikan.')
    with education:
        st.subheader('Potensi keracunan: pahami faktor risikonya')
        st.info('Dashboard ini belum dapat menghitung peluang keracunan per porsi, sekolah, atau provinsi. Dibutuhkan kasus terverifikasi, jumlah porsi/penerima yang terpapar, periode yang sama, serta cakupan pelaporan yang sebanding. Banyaknya berita tidak cukup untuk memberi skor aman/berbahaya.')
        st.markdown('''Pangan yang terkontaminasi dapat menyebabkan gangguan kesehatan. Dalam penyelenggaraan makanan massal, pengendalian perlu mencakup bahan baku, pengolahan, penyimpanan, hingga distribusi. Faktor berikut merupakan **rujukan pencegahan**, bukan kesimpulan penyebab setiap insiden MBG.''')
        st.dataframe(pd.DataFrame([
            {'Tahap': 'Bahan & air', 'Faktor yang perlu diperiksa': 'Keamanan bahan baku dan air', 'Pengendalian': 'Gunakan air dan bahan yang aman; jaga ketertelusuran bahan.'},
            {'Tahap': 'Persiapan', 'Faktor yang perlu diperiksa': 'Kebersihan dan kontaminasi silang', 'Pengendalian': 'Jaga kebersihan; pisahkan pangan mentah dan matang.'},
            {'Tahap': 'Memasak', 'Faktor yang perlu diperiksa': 'Pemasakan tidak memadai', 'Pengendalian': 'Masak dengan saksama sesuai prosedur keamanan pangan.'},
            {'Tahap': 'Simpan & distribusi', 'Faktor yang perlu diperiksa': 'Suhu dan waktu tidak terkendali', 'Pengendalian': 'Pantau dan catat suhu/waktu; pertahankan suhu pangan yang aman.'},
            {'Tahap': 'Pengawasan', 'Faktor yang perlu diperiksa': 'Kelemahan prosedur dan penelusuran', 'Pengendalian': 'Tinjau kepatuhan SOP, pemeriksaan, dan dokumentasi distribusi.'},
        ]), hide_index=True, width='stretch')
        st.markdown('Rujukan: [WHO — Five keys to safer food](https://www.who.int/activities/promoting-safe-food-handling), [BPOM — penguatan keamanan pangan MBG](https://www.pom.go.id/berita/rdp-bersama-komisi-ix-dpr-bpom-tekankan-penguatan-keamanan-pangan-dalam-program-mbg). Rujukan umum ini bukan data kejadian 2026.')
        st.subheader('Dampak kesehatan dan kapan mencari bantuan')
        st.write('Gejala dapat meliputi mual, muntah, diare, nyeri perut, dan demam. Sebagian kejadian dapat memerlukan perawatan rumah sakit; gejala saja tidak membuktikan sumber makanan penyebabnya.')
        st.warning('Cari pertolongan medis bila ada diare berdarah, muntah sampai tidak bisa mempertahankan cairan, atau tanda dehidrasi seperti sedikit berkemih dan pusing saat berdiri. Jangan menunggu hasil analisis dashboard untuk mencari bantuan.')
        st.markdown('[CDC — gejala keracunan pangan dan tanda yang memerlukan pertolongan](https://www.cdc.gov/food-safety/signs-symptoms/). Informasi umum; diagnosis dan penentuan penyebab memerlukan tenaga kesehatan/investigasi.')
        with st.expander('Visualisasi lanjutan jika data terverifikasi tersedia'):
            st.markdown('''- **Tren insiden dan jumlah terdampak:** berdasarkan tanggal kejadian; pisahkan dugaan, terkonfirmasi, dan dibantah.
- **Peta tingkat kejadian per 100.000 porsi/penerima:** hanya jika pembilang, penyebut, periode, dan wilayah sebanding; tampilkan kelengkapan pelaporan.
- **Distribusi keparahan:** rawat jalan, rawat inap, dan hasil akhir dengan definisi serta sumber konsisten.
- **Waktu respons:** jeda antara kejadian, laporan, investigasi, dan tindakan korektif jika tanggalnya tersedia.''')
