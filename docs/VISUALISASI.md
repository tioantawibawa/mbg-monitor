# Panduan visualisasi publik

Pembaruan 29 Oktober 2026. Tujuan: menjelaskan dampak yang diberitakan dan cara memahami risiko keamanan pangan tanpa menyamakan banyaknya berita dengan banyaknya korban atau peluang keracunan.

Tab estimasi korban kini juga tersedia: lihat [metode rekap korban, deduplikasi, dan tanggal berita pertama](ESTIMASI_KORBAN.md).

| Visual | Pertanyaan yang dijawab | Batas pembacaan |
|---|---|---|
| Batang tema dampak | Apa yang disebut dalam judul: keluhan, perawatan, gangguan layanan, mutu, pengawasan, pemulihan? | Satu artikel dapat masuk beberapa tema; bantahan dan pencegahan juga dapat menyebut istilah dampak. |
| Heatmap tema × bulan | Bagaimana perhatian pemberitaan berubah? | Tanggal publikasi, bukan kejadian; intensitas media dan kelengkapan arsip memengaruhi warna. |
| Batang nada judul & komposisi bulanan | Nada apa yang terdeteksi oleh kamus? | Sampel pencarian keracunan, bukan opini publik atau sentimen seluruh program MBG. |
| Word cloud & 20 kata teratas | Kata apa yang paling banyak muncul pada judul? | Frekuensi dokumen, bukan tingkat bahaya; tidak otomatis memahami negasi. |
| Tabel risiko sepanjang rantai pangan | Apa faktor yang perlu dikendalikan? | Edukasi umum, bukan diagnosis sebab insiden tertentu. |

## Metode analisis judul

- Kamus v1 dapat dibaca dan diubah di `src/text_analysis.py`. Analisis dilakukan lokal, tanpa API AI atau biaya token.
- Nama sumber pada akhiran judul dibuang sebelum analisis. Kata cocok pada batas kata/frasa.
- Kata pencarian `keracunan` tidak diberi skor negatif. Kata dampak seperti `dirawat` memicu Negatif/dampak; `sembuh` memicu Pemulihan; keduanya memicu Campuran.
- Negasi, bantahan, dan pencegahan masuk Perlu konteks agar tidak disimpulkan sebagai kejadian negatif secara otomatis. Ini aturan kasar dan bisa melewatkan negasi tidak langsung, kutipan, ironi, atau bentuk kata lain.
- Tidak ada pemicu berarti Tidak terklasifikasi, bukan sentimen netral. Belum ada validasi akurasi terhadap sampel berlabel manusia; tidak ditampilkan probabilitas/confidence palsu.
- Ekspor klasifikasi menyertakan judul, sumber, tema, kategori, dan kata pemicu agar bisa dikoreksi melalui tinjauan.
- Word cloud menghitung satu kata maksimal sekali per judul. Opsi default menggabungkan judul identik lintas penerbit hanya untuk analisis kata. Judul yang sangat mirip tetapi tidak identik tetap terpisah. Kata umum, kata pencarian, dan angka dikeluarkan; daftar tambahan bisa diatur pengguna.
- Warna cloud hanya dekoratif. Ukuran mengikuti frekuensi, dengan pengecilan untuk penempatan; angka pasti tersedia di tabel/CSV. Beberapa kata mungkin tidak muat.

## Yang belum layak ditampilkan sebagai angka risiko

Peta merah/hijau “provinsi berbahaya”, peluang keracunan, dan ranking keselamatan sekolah belum dapat dibuat dari arsip judul. Dibutuhkan register kasus terverifikasi serta penyebut jumlah porsi/penerima terpapar dengan definisi, wilayah, dan periode yang sama. Cakupan pelaporan juga perlu dinilai. Jangan memakai jumlah berita sebagai pembilang untuk insidensi.

Setelah tersedia, rekomendasi berikutnya: tren jumlah kejadian dan terdampak menurut tanggal kejadian; tingkat kejadian per 100.000 porsi/penerima; distribusi rawat jalan/rawat inap; dan jeda respons/investigasi. Jangan menjumlahkan kategori korban yang tumpang tindih atau menganggap data kosong sebagai nol.

## Rujukan edukasi

- [WHO — Five keys to safer food](https://www.who.int/activities/promoting-safe-food-handling)
- [BPOM — penguatan keamanan pangan dalam MBG](https://www.pom.go.id/berita/rdp-bersama-komisi-ix-dpr-bpom-tekankan-penguatan-keamanan-pangan-dalam-program-mbg)
- [CDC — gejala dan kapan mencari pertolongan](https://www.cdc.gov/food-safety/signs-symptoms/)

Rujukan edukasi bukan daftar insiden 2026. Jangan menisbatkan semua gejala atau faktor tersebut kepada seluruh makanan MBG.

## Menjalankan pembaruan

Jika Streamlit masih aktif, refresh browser dan izinkan rerun ketika diminta. Jika perlu restart, Ctrl+C di PowerShell lalu:

```powershell
Set-Location 'C:\Users\tio\Documents\ChatGPT\New project\mbg-monitor'
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m streamlit run app.py
```

Untuk repository yang sudah diinisialisasi dan remote-nya sudah benar:

```powershell
git rev-parse --show-toplevel
# Pastikan hasil berakhir dengan mbg-monitor, bukan folder induknya.
git status --short
git add app.py src requirements.txt README.md docs tests ui_tests assets data .github/workflows/collect.yml VERIFICATION.md
git commit -m 'Add public impact, title tone and word cloud analysis'
git push
```

Jika belum pernah push, ikuti langkah inisialisasi repository pada README terlebih dahulu. File lokal sudah diperbarui; GitHub dan Streamlit Cloud belum diperbarui otomatis oleh sesi ini.
