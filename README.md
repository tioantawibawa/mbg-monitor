# Pantau MBG — Indonesia sejak 2026

Dashboard Streamlit berbahasa Indonesia untuk pemantauan berita keracunan terkait Makan Bergizi Gratis (MBG). Pengumpulan metadata RSS otomatis berjalan harian melalui GitHub Actions pukul **07.17 WIB (00.17 UTC)**. Tanpa API key dan tanpa layanan AI berbayar. Penggunaan GitHub Actions mengikuti kuota akun/repository.

## Apa yang tersedia

- Tab **Estimasi korban dari judul**: ekstraksi angka orang, penggabungan berita berulang, rekap 38 provinsi, deret waktu harian/mingguan/bulanan dan kumulatif berdasarkan berita pertama, serta audit alasan setiap angka dihitung/ditahan. [Metode dan penggunaan](docs/ESTIMASI_KORBAN.md).
- Tab **Dampak & literasi publik**: grafik tema dampak, heatmap bulanan, nada judul, word cloud dengan unduhan PNG, serta panduan risiko pangan berbasis WHO/BPOM/CDC.
- Grafik intensitas berita, filter tanggal/provinsi/kata kunci, tautan sumber, unduhan CSV.
- Pengumpulan nasional dan pencarian tambahan untuk 38 provinsi; histori memakai jendela mingguan sejak 1 Januari 2026.
- Deduplikasi artikel, retry, timeout, penyimpanan atomik, serta data lama dipertahankan jika sumber gagal.
- Register insiden dengan dugaan/terkonfirmasi/dibantah untuk statistik hasil tinjauan. Estimasi otomatis dari judul disajikan terpisah.
- Log kueri, peringatan feed berpotensi dibatasi, status parsial/gagal, dan peringatan data basi >48 jam.
- Tes pipeline dan smoke test Streamlit. Dataset produksi tidak berisi contoh fiktif.

**Batas penting:** ini pemantauan berita, bukan sensus kasus atau angka resmi. RSS dapat melewatkan kejadian, membatasi hasil, atau menampilkan artikel 2026 tentang kejadian 2025. Nama provinsi pada judul hanya petunjuk, bukan verifikasi lokasi. Pencarian provinsi tidak berarti seluruh kejadian provinsi tersebut ditemukan. Register insiden awal kosong sampai ditinjau manusia. Dengan demikian, scraping otomatis berjalan, tetapi verifikasi kasus dan jumlah korban memerlukan tinjauan.

## 1. Jalankan lokal di PowerShell

Prasyarat: Python 3.12 dan Git sudah terpasang. Buka PowerShell:

```powershell
Set-Location 'C:\Users\tio\Documents\ChatGPT\New project\mbg-monitor'
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -m unittest discover -s ui_tests -v
& .\.venv\Scripts\python.exe -m streamlit run app.py
```

Jika `py` tidak ditemukan, gunakan path Python yang valid. Pada komputer sesi pembuatan ini tersedia:

```powershell
& 'C:\Users\tio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
```

Tidak perlu menjalankan Activate.ps1 atau mengubah ExecutionPolicy. Buka alamat localhost yang ditampilkan Streamlit. Hentikan dengan Ctrl+C.

## 2. Ambil data historis dan harian

```powershell
# Nasional, jendela mingguan sejak 1 Januari 2026 hingga hari ini WIB.
& .\.venv\Scripts\python.exe -m src.collect --backfill

# Harian: ulangi tujuh hari terakhir + hari ini, nasional dan 38 provinsi.
& .\.venv\Scripts\python.exe -m src.collect --regional

# Pendalaman histori per bulan (lebih banyak permintaan dan lebih lama).
& .\.venv\Scripts\python.exe -m src.collect --start 2026-01-01 --end 2026-01-31 --regional
```

`--end` inklusif; semua tanggal menggunakan Asia/Jakarta. Proses bisa memakan beberapa menit. Jangan jalankan dua collector lokal bersamaan. Pengambilan ulang aman terhadap duplikasi artikel, tetapi tidak menjamin seluruh arsip berhasil ditemukan. Periksa `data/health.json` dan tab Kualitas data. `possibly_capped: true` berarti feed >=100 item: collector otomatis membagi rentang hingga satu hari (`subdivided: true`). Jika satu hari tetap terpotong, gunakan pencarian regional atau sumber tambahan. `status: partial/failed` menghasilkan exit code 1 dan tetap menyimpan hasil yang berhasil. `data/runs.json` menyimpan 90 run terbaru. Kegagalan tidak menghapus arsip sebelumnya.

## 3. Push sendiri ke GitHub

Di GitHub, buat repository kosong bernama `mbg-monitor` (jangan centang README/.gitignore/license agar tidak konflik). Untuk tutorial ini gunakan branch `main`. Folder proyek ini berada di dalam workspace lain: pastikan `git init` dilakukan **di folder mbg-monitor**.

```powershell
Set-Location 'C:\Users\tio\Documents\ChatGPT\New project\mbg-monitor'
git init -b main
git rev-parse --show-toplevel
# Pastikan hasil berakhir dengan /mbg-monitor, lalu lanjut.
git add .
git status --short
# Periksa daftar; .venv, secrets.toml, dan .env tidak boleh masuk.
git commit -m 'Initial MBG monitoring dashboard'
git remote add origin https://github.com/USERNAME/mbg-monitor.git
git push -u origin main
```

Ganti `USERNAME` dengan username GitHub Tio. Autentikasi lewat Git Credential Manager/browser saat diminta; jangan menaruh token di kode atau URL remote. Jika Git belum memiliki identitas:

```powershell
git config user.name 'Tio Anta Wibawa'
git config user.email 'EMAIL_GITHUB_ANDA'
```

Lalu ulangi commit/push yang sebelumnya gagal. Jika `origin` sudah ada, periksa `git remote -v` sebelum menggunakan `git remote set-url origin https://github.com/USERNAME/mbg-monitor.git`.

## 4. Aktifkan pengumpulan harian

1. Pastikan `.github/workflows/collect.yml` sudah berada di default branch `main`.
2. GitHub → repository → Settings → Actions → General → Workflow permissions → **Read and write permissions**, jika pengaturan organisasi mengizinkan. Workflow hanya memerlukan `contents: write` untuk menyimpan snapshot data.
3. Actions → **Daily MBG collection** → Run workflow. Centang `backfill` untuk pengambilan historis awal; tanpa centang untuk nasional + 38 provinsi pada periode terbaru.
4. Pastikan run sukses, ada commit `data: refresh MBG news and collection health`, dan `data/health.json` berstatus `ok`. Run gagal tetap mencoba menyimpan log kegagalan.
5. Jadwal berikutnya sekitar 07.17 WIB. GitHub dapat menunda jadwal ketika sibuk; repository publik yang tidak aktif dapat mengalami penonaktifan schedule setelah 60 hari. Cek Actions bila dashboard memberi peringatan basi.

Workflow mengasumsikan push langsung ke `main` diperbolehkan. Jika branch protection melarang bot push, sesuaikan kebijakan repository atau ubah alur menjadi PR. Tidak ada bypass otomatis. Konflik saat pull/rebase membuat job gagal agar data tidak ditimpa; selesaikan konflik lalu jalankan ulang.

## 5. Deploy ke Streamlit Community Cloud

1. Buka https://share.streamlit.io dan hubungkan akun GitHub.
2. Pilih **Create app** → repository `USERNAME/mbg-monitor`, branch `main`, main file `app.py`.
3. Pada Advanced settings, pilih Python 3.12 bila tersedia. Tidak perlu secrets/API key.
4. Deploy dan tunggu instalasi `requirements.txt` selesai.
5. Buka aplikasi, cocokkan waktu pengambilan terakhir dengan `data/health.json` di GitHub.

Streamlit mengikuti perubahan repository. Collector berjalan di GitHub Actions, bukan pada rerun pengunjung Streamlit, sehingga refresh halaman tidak menimbulkan scraping berulang. Jika data belum terlihat setelah commit, periksa status deployment dan lakukan reboot dari pengelola app.

## 6. Meninjau dan memperbarui insiden

Edit `data/incidents.csv` secara lokal. Satu baris mewakili satu kejadian, bukan satu artikel. Gabungkan sumber lanjutan pada incident_id yang sama; pisahkan kejadian di tanggal/lokasi berbeda setelah meninjau buktinya.

| Kolom | Aturan |
|---|---|
| incident_id | ID unik stabil, misalnya tanggal-kabupaten-lokasi |
| event_date | Tanggal kejadian YYYY-MM-DD, minimal 2026-01-01 |
| province | Nama resmi dari `PROVINCES` dalam src/core.py |
| district, location | Kabupaten/kota dan sekolah/SPPG/lokasi yang disebut sumber |
| status | Dugaan, Terkonfirmasi, atau Dibantah |
| affected | Angka terakhir yang didukung sumber; kosong jika tidak diketahui |
| source_urls | URL artikel/pernyataan, pisahkan beberapa URL dengan tanda `|` |
| evidence | Ringkasan bukti, otoritas, tanggal pernyataan, alasan perubahan angka/status |
| reviewer, reviewed_at | Nama peninjau dan tanggal tinjau YYYY-MM-DD |

Gunakan Terkonfirmasi hanya bila ada pernyataan otoritas yang relevan mengenai kejadian/hubungan dengan MBG. Tidak adanya kata “diduga” pada judul tidak cukup. Jangan menggabungkan jumlah “dirawat” dengan seluruh “terdampak”; pilih definisi konsisten dan jelaskan di evidence. Pembaruan jumlah mengganti nilai lama, bukan ditambahkan. Jangan masukkan identitas anak atau data pribadi korban.

Sebelum mengubah data lokal setelah bot bekerja:

```powershell
git pull --rebase origin main
# Edit data/incidents.csv, lalu:
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
git add data/incidents.csv
git commit -m 'data: review MBG incidents'
git push
```

Riwayat Git menyimpan perubahan tinjauan. Dashboard publik tidak memiliki form penulisan agar perubahan data hanya melalui repository.

## Struktur

```text
app.py                      Dashboard Streamlit
src/core.py                 Validasi, deduplikasi, ekspor
src/collect.py              Collector RSS + CLI
data/articles.json          Arsip metadata berita
data/incidents.csv          Register kejadian hasil tinjauan
data/health.json             Status pengambilan terakhir (dibuat collector)
data/runs.json               Riwayat run (dibuat collector)
tests/                      Pengujian pipeline tanpa jaringan
ui_tests/                   Smoke test dashboard
.github/workflows/          Jadwal pengambilan dan CI
```

## Referensi deployment

- Streamlit: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Dependencies: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- GitHub schedule: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

RSS Google News digunakan sebagai kanal penemuan publik, bukan API dengan jaminan kelengkapan/SLA. Atribusi penerbit dan link disimpan; hindari menyalin isi lengkap artikel atau melewati paywall. Sesuaikan sumber jika ketentuan/akses layanan berubah.
