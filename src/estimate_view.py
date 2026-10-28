import json
from collections import Counter

import altair as alt
import pandas as pd
import streamlit as st

from src.core import PROVINCES, safe_csv
from src.victim_estimates import aggregate, build_estimates, filter_clusters

@st.cache_data(show_spinner=False, max_entries=8)
def cached_estimates(articles, window_days):
    return build_estimates(articles, window_days)

def render_estimates(articles, left, right, provinces, keyword):
    st.subheader('Estimasi korban dari angka pada judul berita')
    st.caption('Rekap otomatis ini terpisah dari register insiden hasil tinjauan. “Korban” berarti jumlah orang yang dilaporkan terdampak dalam judul, termasuk dugaan; bukan angka resmi atau orang unik yang sudah diverifikasi.')
    window = st.selectbox('Jendela penggabungan berita tentang kejadian yang sama', [14, 7, 3, 30], format_func=lambda n: f'{n} hari', key='estimate_window')
    bundle = cached_estimates(articles, window)
    selected = filter_clusters(bundle['clusters'], left.isoformat(), right.isoformat(), provinces, keyword)
    included = [r for r in selected if r['included']]
    held = [r for r in selected if not r['included']]
    province_totals, daily = aggregate(selected)
    total = sum(province_totals.values())
    a, b, c, d = st.columns(4)
    a.metric('Subtotal estimasi dari judul', f'{total:,}')
    b.metric('Kelompok kejadian dihitung', len(included))
    c.metric('Artikel angka digabung¹', sum(r['numeric_article_count'] - 1 for r in included))
    d.metric('Kelompok ditahan', len(held))
    st.caption('¹ Artikel angka tambahan dalam kelompok yang sama tidak dijumlahkan lagi. Subtotal hanya mencakup kelompok yang lolos aturan, bukan total korban nasional. Nol berarti tidak ada kelompok yang lolos pada filter ini.')
    st.info('Satu kelompok menggunakan angka total tertinggi yang disebut judul, bukan penjumlahan antarberita. Angka itu ditempatkan pada tanggal publikasi paling awal yang ditemukan untuk kelompok tersebut, termasuk judul awal tanpa angka. Ini rekonstruksi memakai arsip terbaru, bukan jumlah yang sudah diketahui pada hari itu.')
    st.warning('Pengelompokan memakai nama wilayah/lokalitas dan jarak tanggal, sehingga masih bisa menggabungkan kejadian berbeda atau memisahkan kejadian sama. Angka tertinggi bisa berlebihan; kelompok dengan bantahan/koreksi ditahan dari subtotal. Perubahan jendela memperlihatkan sensitivitas hasil, bukan rentang kepercayaan statistik.')
    region_tab, time_tab, group_tab, audit_tab = st.tabs(['Per provinsi', 'Deret waktu', 'Kelompok & duplikasi', 'Audit setiap judul'])
    with region_tab:
        region_frame = pd.DataFrame([{'Provinsi': p, 'Estimasi korban': province_totals.get(p, 0),
                                      'Kelompok': sum(r['province'] == p for r in included)}
                                     for p in PROVINCES if not provinces or p in provinces],
                                    columns=['Provinsi', 'Estimasi korban', 'Kelompok'])
        if included:
            st.altair_chart(alt.Chart(region_frame[region_frame['Estimasi korban'] > 0]).mark_bar(color='#B45340').encode(
                x=alt.X('Estimasi korban:Q', title='Subtotal estimasi orang dari judul'), y=alt.Y('Provinsi:N', sort='-x'),
                tooltip=['Provinsi', 'Estimasi korban', 'Kelompok']), width='stretch')
        else:
            st.info('Belum ada kelompok yang lolos pada filter ini. Lihat audit untuk lokasi yang belum diketahui atau angka yang ditahan.')
        st.dataframe(region_frame, hide_index=True, width='stretch')
        st.caption('Provinsi dengan 0 belum memiliki kelompok yang dihitung; bukan bukti tidak ada korban. Judul tanpa lokasi jelas tidak dialokasikan secara paksa. Nama kota/kabupaten ditautkan ke provinsi melalui kamus wilayah yang belum lengkap.')
        st.download_button('Unduh estimasi per provinsi', safe_csv(region_frame.to_dict('records'), list(region_frame.columns)), 'mbg-estimasi-provinsi.csv', 'text/csv')
    with time_tab:
        frequency = st.radio('Interval waktu', ['Harian', 'Mingguan', 'Bulanan'], horizontal=True)
        if included:
            # Continuous index: no accepted first reports on a day means 0 additions to this estimate.
            series = pd.Series(daily, dtype='int64')
            series.index = pd.to_datetime(series.index)
            series = series.reindex(pd.date_range(left, right), fill_value=0)
            if frequency != 'Harian':
                series = series.resample('W-MON' if frequency == 'Mingguan' else 'MS', label='left', closed='left').sum()
            frame = series.rename('Estimasi korban').rename_axis('Tanggal').reset_index()
            frame['Kumulatif periode filter'] = frame['Estimasi korban'].cumsum()
            st.altair_chart(alt.Chart(frame).mark_bar(color='#C06B43').encode(
                x=alt.X('Tanggal:T', title='Tanggal publikasi pertama / awal interval'), y='Estimasi korban:Q',
                tooltip=[alt.Tooltip('Tanggal:T', format='%d %b %Y'), 'Estimasi korban']), width='stretch')
            st.altair_chart(alt.Chart(frame).mark_line(color='#0F766E').encode(
                x='Tanggal:T', y='Kumulatif periode filter:Q',
                tooltip=[alt.Tooltip('Tanggal:T', format='%d %b %Y'), 'Kumulatif periode filter']), width='stretch')
            st.caption('Minggu dimulai Senin. Kumulatif dimulai dari nol pada awal filter; interval pertama/terakhir dapat parsial. Sumbu memakai tanggal berita pertama, bukan tanggal kejadian. Jumlah antarinterval sama dengan subtotal provinsi.')
            st.dataframe(frame, hide_index=True)
            export = frame.copy()
            export['Tanggal'] = export['Tanggal'].dt.strftime('%Y-%m-%d')
            st.download_button('Unduh deret waktu estimasi', safe_csv(export.to_dict('records'), list(export.columns)), 'mbg-estimasi-timeseries.csv', 'text/csv')
        else:
            st.info('Tidak ada kelompok yang dapat dibuatkan deret waktu pada filter ini.')
    with group_tab:
        st.caption('Kolom min_reported_total dan estimated_victims menunjukkan variasi angka antarjudul dalam satu kelompok; bukan batas bawah/atas statistik. Tanggal count_source_date menunjukkan kapan angka pilihan diberitakan.')
        fields = ['cluster_id', 'first_report_date', 'province', 'district', 'locality', 'min_reported_total',
                  'estimated_victims', 'count_source_date', 'article_count', 'numeric_article_count', 'status',
                  'representative_title', 'representative_url']
        frame = pd.DataFrame(selected, columns=fields)
        st.dataframe(frame, hide_index=True, column_config={'representative_url': st.column_config.LinkColumn('Sumber angka', display_text='Baca')}, width='stretch')
        if selected:
            st.download_button('Unduh kelompok termasuk yang ditahan', safe_csv(selected, list(selected[0])), 'mbg-estimasi-kelompok.csv', 'text/csv')
    with audit_tab:
        st.caption('Audit memakai tanggal publikasi tiap artikel. Grafik memakai tanggal pertama kelompok. Filter tanggal karenanya dapat menghasilkan jumlah artikel audit yang berbeda dari artikel anggota kelompok.')
        audit = [r for r in bundle['audit'] if left.isoformat() <= r['published_date'] <= right.isoformat()
                 and (not provinces or (r['province'] or 'Belum diketahui') in provinces)
                 and keyword.lower() in r['title'].lower()]
        only_counts = st.checkbox('Hanya judul yang memiliki angka orang terdeteksi', value=True)
        if only_counts:
            audit = [r for r in audit if r['extracted_counts']]
        st.write(f'{len(audit):,} judul dalam audit terfilter.')
        decisions = Counter(r['decision'] for r in audit)
        st.write(dict(decisions))
        audit_export = [{**r, 'extracted_counts': json.dumps(r['extracted_counts'], ensure_ascii=False)} for r in audit]
        if audit_export:
            fields = ['published_date', 'title', 'province', 'district', 'candidate_count', 'extracted_counts',
                      'cluster_id', 'decision', 'exclusion_reason', 'dedupe_reason', 'location_reason', 'url']
            st.dataframe(pd.DataFrame(audit_export)[fields], hide_index=True, column_config={'url': st.column_config.LinkColumn(display_text='Baca sumber')}, width='stretch')
            st.download_button('Unduh audit judul dan alasan penggabungan', safe_csv(audit_export, list(audit_export[0])), 'mbg-audit-angka-korban.csv', 'text/csv')
        else:
            st.info('Tidak ada judul pada filter audit ini.')
    with st.expander('Aturan ekstraksi dan deduplikasi'):
        st.markdown('''1. Angka eksplisit yang melekat pada orang/siswa/guru/korban atau klausa jumlah korban diekstrak. Nomor sekolah, tahun, jumlah dapur, persentase, dan jumlah kasus tidak dianggap orang. Angka perkiraan seperti “hampir 400” atau “51 ribu” ditahan.
2. Angka pasien masih dirawat, korban pulih/meninggal, dan penerima layanan dipisahkan dari total. Dua kelompok orang hanya dijumlahkan bila judul menyatakan penambahan jelas, misalnya “75 siswa dan 5 guru”.
3. Rekap nasional/lintas periode dan judul yang menyebut tahun sebelum 2026 dikeluarkan. Lokasi ganda atau tidak dikenal ditahan.
4. Berita pada wilayah/lokalitas sama dalam jendela pilihan digabung. Berita tingkat kabupaten yang cocok ke beberapa lokalitas ditahan. Berita hasil lab/penyebab/biaya perawatan dapat ditautkan hingga 60 hari hanya bila satu kelompok asal cocok; tidak membuat kejadian baru.
5. Satu angka tertinggi dipilih untuk satu kelompok. Kelompok yang memiliki bantahan/koreksi terhadap jumlah atau kejadian ditahan dari subtotal. Bantahan khusus kabar kematian tidak membatalkan jumlah terdampak nonfatal. Semua artikel tetap tersedia; “drop redundant” hanya dilakukan pada perhitungan.
6. Kelompok dibangun dari seluruh arsip sebelum filter diterapkan. Filter waktu memilih tanggal berita pertama kelompok. Angka dapat direvisi bila arsip bertambah; ini bukan pelacakan historis angka yang diketahui saat itu.''')
