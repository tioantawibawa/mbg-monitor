# Pemeriksaan lokal — 29 Oktober 2026 WIB

## Pembaruan estimasi korban dari judul

- Ekstraksi angka orang, pemisahan subkelompok/penerima layanan, pengecualian rekap lintas periode, deduplikasi berbasis wilayah/lokalitas/waktu, serta penautan berita lanjutan ditambahkan.
- 33 tes pipeline/analisis/estimasi lulus. Pengujian mencakup angka pembaruan, judul pertama tanpa angka, lokasi berbeda dalam kabupaten sama, berita hasil lab terlambat, nomor sekolah, bantahan jumlah, bantahan kematian, dan rekonsiliasi provinsi/deret waktu.
- 5 tes aplikasi/gambar lulus: data aktual, kondisi kosong, interval mingguan/bulanan, filter lokasi belum diketahui, KPI register, dan PNG. Total terbaru **38 tes lulus**. AppTest memeriksa komponen tanpa screenshot browser.
- Snapshot aktual dibangun ulang: 728 judul dengan angka orang terdeteksi, 94 kelompok dihitung, 7 ditahan, subtotal aturan 13.243 orang dilaporkan. Ini hasil mesin dari judul, belum ditinjau sebagai jumlah korban terverifikasi.
- 333 artikel angka tambahan pada kelompok yang dihitung digabung tanpa menambah subtotal.
- Dashboard memakai seluruh arsip sebelum filter; pengelompokan di-cache per arsip/jendela. Snapshot hasil dibangun ulang melalui workflow harian setelah perubahan di-push.
- Tidak ada perubahan pada register insiden hasil tinjauan dan tidak ada push/deployment eksternal.

## Pembaruan analisis publik

- Pada pembaruan analisis publik sebelumnya: 17 tes pipeline/analisis teks dan 4 tes aplikasi/gambar lulus (21 tes).
- Pengujian mencakup negasi/pencegahan, kategori campuran/pemulihan, batas kata, penghapusan nama sumber, frekuensi per judul, deduplikasi lintas penerbit, dan PNG deterministik.
- Aplikasi diuji dengan dataset aktual, data kosong, filter pencarian, dan register sintetis khusus tes untuk memastikan insiden dibantah tidak masuk KPI.
- Contoh word cloud dibuat dari arsip aktual di `assets/wordcloud-preview.png`; tidak dipakai sebagai pengganti gambar dinamis di dashboard.
- Klasifikasi kamus belum divalidasi terhadap label manusia. Hasil bukan opini publik maupun estimasi risiko keracunan.
- Tidak ada push GitHub atau deployment eksternal pada pembaruan ini.

## Pemeriksaan versi awal

- 11 tes pipeline lulus: relevansi, periode, RSS tidak valid, deduplikasi, petunjuk provinsi, kontinuitas rentang, pemecahan feed terpotong, data tetap tersimpan saat gagal, validasi register, dan ekspor CSV.
- 3 tes Streamlit AppTest lulus: aplikasi dengan dataset aktual, kondisi kosong, dan KPI yang mengeluarkan insiden dibantah. Filter kata kunci juga diuji. Ini pengujian komponen, bukan pemeriksaan screenshot browser.
- `pip check`: tidak ada dependensi rusak.
- Pengambilan historis nasional aktual: 2.153 artikel kandidat dari 510 label penerbit, rentang permintaan 1 Januari–29 Oktober 2026. Seluruh 92 kueri berhasil merespons RSS.
- Sebelas kueri harian masih mencapai batas >=100 item. Cakupan arsip belum lengkap meski status koneksi `ok`; dashboard menampilkan peringatan ini. Pencarian regional/sumber tambahan dapat memperluas cakupan.
- Register insiden belum diisi. Tidak ada total kasus atau korban yang dinyatakan terverifikasi.
- Pencarian harian regional 38 provinsi sudah diimplementasikan, tetapi run regional penuh belum diuji terhadap jaringan pada sesi ini.
- GitHub belum dibuat/di-push, jadwal GitHub Actions belum aktif, dan Streamlit Cloud belum di-deploy. Tahapan tersebut dilakukan pengguna mengikuti README.
- Percobaan pengambilan pertama terkena pembatasan socket lingkungan lokal. Pengambilan ulang dengan akses jaringan yang diizinkan berhasil; riwayat kegagalan tetap tercatat dalam data/runs.json.
