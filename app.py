from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.core import INCIDENT_FIELDS, PROVINCES, load_incidents, read_json, safe_csv
from src.public_insights import render_insights
from src.estimate_view import render_estimates

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Pantau MBG | Indonesia', page_icon='🇮🇩', layout='wide')
st.caption('PEMANTAUAN PANGAN  /  INDONESIA  /  SEJAK 2026')
st.title('Pantau insiden MBG')
st.write('Pahami dampak yang diberitakan, kenali risiko keamanan pangan, dan telusuri sumber tentang Makan Bergizi Gratis.')
st.info('Berita ≠ insiden. Statistik register ditinjau dan estimasi otomatis dari judul ditampilkan terpisah. Estimasi bukan angka resmi; tanggal publikasi bukan tanggal kejadian.')
articles = read_json(ROOT / 'data/articles.json', [])
health = read_json(ROOT / 'data/health.json', {})
try:
    incidents = load_incidents(ROOT / 'data/incidents.csv')
except (ValueError, KeyError) as exc:
    st.error(f'Register insiden tidak valid: {exc}')
    st.stop()
if health:
    st.caption(f"Pengambilan terakhir: {health.get('finished_at')} · Status: {health.get('status')} · Kueri gagal: {health.get('failed_queries', 0)}")
    if health.get('status') != 'ok':
        st.warning('Pengambilan terakhir tidak lengkap. Data tersimpan tetap ditampilkan; periksa tab Kualitas data.')
    last = health.get('last_success_at')
    if not last or (datetime.now(ZoneInfo('Asia/Jakarta')) - datetime.fromisoformat(last)).total_seconds() > 48 * 3600:
        st.warning('Belum ada pengambilan sukses dalam 48 jam terakhir.')
else:
    st.warning('Scraper belum pernah dijalankan. Jalankan pengumpulan awal melalui PowerShell atau GitHub Actions.')
with st.sidebar:
    st.header('Jelajahi data')
    period = st.date_input('Periode', (date(2026, 1, 1), datetime.now(ZoneInfo('Asia/Jakarta')).date()), min_value=date(2026, 1, 1))
    selected = st.multiselect('Provinsi', PROVINCES + ['Belum diketahui'])
    keyword = st.text_input('Cari judul / kabupaten')
    st.caption('Berita memakai tanggal publikasi; estimasi korban memakai tanggal berita pertama kelompok; register memakai tanggal kejadian. Provinsi berita hanya petunjuk judul, sedangkan estimasi juga memakai kamus nama kota/kabupaten.')
if len(period) != 2:
    st.info('Pilih tanggal awal dan akhir.')
    st.stop()
left, right = period
news = [r for r in articles if left <= date.fromisoformat(r['published_at'][:10]) <= right
        and (not selected or r['province_hint'] in selected)
        and keyword.lower() in r['title'].lower()]
events = [r for r in incidents if left <= date.fromisoformat(r['event_date']) <= right
          and (not selected or r['province'] in selected)
          and keyword.lower() in (r['district'] + ' ' + r['location']).lower()]
active = [r for r in events if r['status'] != 'Dibantah']
a, b, c, d = st.columns(4)
a.metric('Artikel terpantau', len(news))
b.metric('Insiden ditinjau¹', len(active) if incidents else '—')
c.metric('Terkonfirmasi²', sum(r['status'] == 'Terkonfirmasi' for r in active) if incidents else '—')
d.metric('Terdampak dilaporkan¹', sum(int(r['affected']) for r in active if r['affected']) if any(r['affected'] for r in active) else '—')
st.caption('¹ Dugaan + terkonfirmasi, tidak termasuk dibantah. Jumlah terdampak hanya nilai yang tersedia per insiden, bukan orang unik lintas kejadian. ² Berdasarkan bukti otoritas yang dicatat reviewer.')
estimated, public, tab1, tab2, tab3 = st.tabs(['Estimasi korban dari judul', 'Dampak & literasi publik', 'Pemberitaan', 'Register insiden', 'Kualitas data & metodologi'])
with estimated:
    render_estimates(articles, left, right, selected, keyword)
with public:
    render_insights(news)
with tab1:
    if news:
        frame = pd.DataFrame(news)
        trend = pd.to_datetime(frame['published_at'], utc=True).dt.tz_convert('Asia/Jakarta').dt.date.value_counts().sort_index()
        st.subheader('Intensitas pemberitaan harian')
        st.bar_chart(trend.rename('Artikel'), color='#0D9488')
        st.dataframe(frame[['published_at', 'title', 'source', 'province_hint', 'url']], hide_index=True,
                     column_config={'url': st.column_config.LinkColumn('Sumber', display_text='Buka berita')}, width='stretch')
        st.download_button('Unduh berita terfilter', safe_csv(news, list(news[0])), 'mbg-berita.csv', 'text/csv')
    else:
        st.info('Belum ada artikel pada filter ini. Ketiadaan berita bukan bukti tidak adanya kasus.')
with tab2:
    st.caption('Satu baris = satu kejadian. Pembaruan jumlah korban mengganti angka pada incident_id yang sama.')
    if events:
        frame = pd.DataFrame(events)
        st.subheader('Sebaran insiden ditinjau per provinsi')
        if active:
            st.bar_chart(pd.Series([r['province'] for r in active]).value_counts().rename('Insiden'))
        st.dataframe(frame, hide_index=True, width='stretch')
        st.download_button('Unduh register terfilter', safe_csv(events, INCIDENT_FIELDS), 'mbg-insiden.csv', 'text/csv')
    else:
        st.info('Belum ada insiden yang ditinjau pada filter ini. Tinjau sumber dan isi data/incidents.csv untuk menghasilkan statistik kasus.')
with tab3:
    capped = [q for q in health.get('queries', []) if q.get('possibly_capped') and not q.get('subdivided')]
    if capped:
        st.warning(f'{len(capped)} kueri berpotensi terpotong oleh batas feed. Cakupan belum lengkap; lakukan pencarian regional atau sumber tambahan.')
    st.markdown('''**Cakupan:** pencarian nasional dan opsi pencarian 38 provinsi melalui Google News RSS. Hanya judul, sumber, tautan, dan tanggal publikasi disimpan; isi lengkap artikel tidak disalin.

**Batasan:** indeks dapat tidak lengkap, feed dapat dibatasi, berita lama dapat tidak muncul. Artikel tahun 2026 mungkin membahas kejadian 2025. Semua artikel masuk sebagai kandidat belum ditinjau. Tidak ada klaim cakupan seluruh kasus Indonesia.

**Deduplikasi:** judul yang dinormalisasi + penerbit mencegah pengulangan artikel. Berita dari media berbeda tetap terpisah. Reviewer menggabungkan artikel terkait dalam satu incident_id berdasarkan tanggal, lokasi, dan kejadian.

**Tinjauan insiden:** catat tanggal kejadian sejak 1 Januari 2026, provinsi, kabupaten, lokasi, sumber, bukti, reviewer, dan tanggal tinjau. Status Terkonfirmasi memerlukan pernyataan otoritas yang relevan; judul tanpa kata “diduga” tidak cukup. Angka tidak tersedia dibiarkan kosong. Klaim yang dibantah tetap tersimpan tetapi dikeluarkan dari KPI.

**Pembaruan:** GitHub Actions menjalankan pengumpulan harian; dashboard membaca snapshot yang di-commit ke repositori. Kegagalan tidak menghapus data sebelumnya. Penjadwalan dan publikasi baru aktif setelah repositori di-push dan aplikasi di-deploy.''')
    st.write(f'Petunjuk provinsi belum diketahui: {sum(r["province_hint"] == "Belum diketahui" for r in articles)} dari {len(articles)} artikel.')
    if health:
        st.json({k: v for k, v in health.items() if k != 'queries'})
        st.dataframe(pd.DataFrame(health.get('queries', [])), hide_index=True)
