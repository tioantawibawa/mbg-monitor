# Rekap estimasi korban dari judul

Pembaruan 29 Oktober 2026. Buka tab **Estimasi korban dari judul** pada dashboard. Semua hasil merupakan estimasi otomatis dari arsip judul, termasuk laporan dugaan, dan memerlukan tinjauan sebelum diperlakukan sebagai angka kejadian/korban terverifikasi.

## Yang dihitung

1. Ambil angka eksplisit yang merujuk orang: `120 siswa`, `432 orang`, `395 korban`, atau klausa jumlah korban. Pemisah ribuan seperti `1.242` dibaca sebagai 1242. Nomor sekolah, tahun, jumlah dapur, porsi, dan jumlah kasus tidak otomatis dianggap jumlah orang.
2. Simpan seluruh angka terdeteksi bersama judul, lokasi, tanggal publikasi WIB, dan sumber. Angka perkiraan/batas seperti “hampir 400”/“51 ribu”, pasien masih dirawat, korban pulih/meninggal, serta penerima layanan ditahan dari kandidat total.
3. Judul yang menyebut tahun sebelum 2026 atau rekap nasional/lintas periode tidak ditambahkan ke kelompok kejadian. Beberapa angka total dalam judul ditahan bila hubungannya tidak jelas. Penjumlahan hanya untuk konstruksi terpisah yang eksplisit seperti `75 siswa dan 5 guru`.
4. Nama kota/kabupaten dan beberapa lokalitas dipetakan melalui kamus pada `src/geography.py`. Kamus belum lengkap. Nama kota/kabupaten yang sama dapat menjadi satu kunci, misalnya kota dan kabupaten Bogor; pemetaan ini bukan kode administrasi resmi. Lokasi ganda/tidak dikenal tidak dialokasikan otomatis ke provinsi. Alias lokalitas tanpa kabupaten dapat diinferensikan dari judul lain yang menyebut keduanya dalam jendela waktu; alasannya dicatat.
5. Judul pada wilayah/lokalitas sama digabung menggunakan jendela 14 hari secara default. Pilihan 3/7/14/30 hari tersedia untuk melihat sensitivitas. Lokalitas yang berbeda seperti Cisarua dan Dramaga dipisahkan. Berita kabupaten yang cocok dengan beberapa lokalitas ditahan. Subwilayah bertingkat yang sudah dikenali, seperti Pondok Kelapa di Duren Sawit, dinormalisasi agar tidak menjadi dua kelompok.
6. Berita lanjutan hasil uji/penyebab/biaya perawatan dapat ditautkan sampai 60 hari bila hanya satu kelompok asal cocok. Berita tersebut tidak membentuk kelompok kejadian baru. Aturan tidak selalu menangkap semua bentuk berita retrospektif.
7. **Satu kelompok memakai satu angka total tertinggi dari judul yang lolos**, bukan penjumlahan antarartikel. Ini pilihan proksi untuk menghindari penjumlahan pembaruan, bukan bukti bahwa angka tertinggi benar. Kelompok dengan bantahan/koreksi jumlah atau kejadian ditahan; bantahan khusus kabar kematian tidak membatalkan jumlah terdampak nonfatal.

Peringatan ekstraksi: hanya angka dalam digit yang didukung saat ini; kata bilangan seperti “tiga”, “belasan”, atau “ratusan” tidak ditafsirkan menjadi angka pasti. Ekstraksi berbasis aturan dapat salah membaca konteks. Audit seluruh judul tetap dapat dibuka dengan menonaktifkan filter “Hanya judul yang memiliki angka orang terdeteksi”.

## Tanggal dan filter

- Tanggal kelompok adalah tanggal publikasi WIB paling awal dari artikel anggota yang tersedia di arsip, termasuk judul awal tanpa angka. Bukan tanggal mulai scraper, tanggal artikel sumber angka, atau tanggal kejadian.
- Angka dari pembaruan berikutnya ditempatkan kembali pada tanggal pertama kelompok. Grafik merupakan rekonstruksi menggunakan arsip terkini, bukan deret jumlah yang diketahui pada setiap hari historis. Kolom `count_source_date` menunjukkan tanggal publikasi angka pilihan.
- Kelompok dibangun menggunakan seluruh arsip sebelum filter. Filter tanggal memilih tanggal pertama kelompok; filter tidak mengubah kelompok atau menggandakan berita yang sama.
- Audit artikel memakai tanggal publikasi masing-masing judul. Jumlah artikel audit pada periode tertentu bisa berbeda dari jumlah anggota kelompok yang tanggal pertamanya masuk filter.
- Minggu dimulai Senin. Kumulatif dimulai dari nol pada awal filter dan mencakup provinsi terpilih. Interval pertama/terakhir dapat parsial. Nilai 0 berarti tidak ada tambahan estimasi yang dihitung pada interval tersebut, bukan tidak ada kejadian di Indonesia.

## Empat tampilan

| Tampilan | Isi |
|---|---|
| Per provinsi | Grafik dan tabel subtotal estimasi; 38 provinsi ditampilkan, dengan 0 jika belum ada kelompok yang dihitung |
| Deret waktu | Harian/mingguan/bulanan, kurva kumulatif, tabel dan CSV |
| Kelompok & duplikasi | Sumber angka, tanggal pertama, variasi angka, jumlah artikel digabung, dan kelompok ditahan |
| Audit setiap judul | Angka yang diekstrak, kandidat total, identitas kelompok, keputusan, alasan penggabungan/penahanan, dan tautan sumber |

Artikel tidak dihapus dari arsip. “Drop redundant” hanya menghilangkan penjumlahan berulang pada subtotal. Kelompok otomatis bisa menyatukan dua kejadian berbeda pada satu wilayah atau memisahkan satu kejadian yang sama; belum ada validasi akurasi deduplikasi terhadap register berlabel manusia. Kelompok tidak mengidentifikasi orang unik antarinsiden. Subtotal bisa kurang atau lebih dari jumlah sebenarnya dan tidak dianggap batas bawah statistik.

## Snapshot lokal dan otomatisasi

Dashboard menghitung dari `data/articles.json` terbaru. Untuk membangun ulang file hasil:

```powershell
Set-Location 'C:\Users\tio\Documents\ChatGPT\New project\mbg-monitor'
& .\.venv\Scripts\python.exe -m src.rebuild_estimates
```

File hasil:

- `data/victim_estimates.json`: kelompok, audit seluruh judul, dan ringkasan metode.
- `data/victims_by_province.csv`: subtotal untuk 38 provinsi.
- `data/victims_timeseries.csv`: estimasi harian dan kumulatif sejak 1 Januari 2026 sampai tanggal publikasi terakhir dalam arsip. Hari tanpa kelompok ditambahkan sebagai 0.

GitHub Actions sudah diperbarui untuk membangun ulang snapshot setelah pengambilan harian. Alur ini baru berjalan pada GitHub setelah perubahan di-push.

## Hasil uji lokal pada arsip saat pembaruan

- 2.153 artikel sumber; 728 judul memiliki angka orang terdeteksi.
- Default 14 hari: 94 kelompok masuk subtotal, 7 kelompok ditahan.
- 333 artikel angka tambahan pada kelompok yang dihitung tidak dijumlahkan ulang.
- Subtotal mesin: **13.243 orang yang dilaporkan dalam judul**. Ini hasil aturan saat ini, bukan jumlah korban nasional terverifikasi. Nilainya dapat berubah jika arsip, kamus, atau jendela berubah.
- Total per provinsi sama dengan total penambahan harian dan nilai kumulatif terakhir.

## Melihat dan mengunggah pembaruan

Refresh browser Streamlit. Jika perlu restart, tekan Ctrl+C pada PowerShell, lalu:

```powershell
Set-Location 'C:\Users\tio\Documents\ChatGPT\New project\mbg-monitor'
& .\.venv\Scripts\python.exe -m streamlit run app.py
```

Untuk repository Git yang sudah diinisialisasi pada folder proyek ini dan remote-nya sudah benar:

```powershell
git rev-parse --show-toplevel
# Pastikan hasil berakhir dengan mbg-monitor.
git status --short
git add app.py src tests ui_tests data .github/workflows/collect.yml README.md docs VERIFICATION.md
git commit -m 'Add deduplicated title victim estimates by province and first report date'
git push
```

Jika belum diinisialisasi/push, ikuti langkah repository baru pada README. Perubahan sesi ini hanya lokal; tidak ada push atau deployment eksternal yang dilakukan.
