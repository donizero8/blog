# Dony’s Notebook

Blog Django + PostgreSQL dalam Docker, dengan editor admin bergaya Medium dan dukungan blok kode.

Profil penulis di sidebar dapat diubah melalui menu **Profil situs** di admin, termasuk foto, headline, bio, lokasi, LinkedIn, dan GitHub. Foto tersimpan persisten di volume Docker `media_data`.

Reading journal tersedia di `/library/`. Buku, status baca, progres, rating, sampul, pelajaran, dan catatan per bab dikelola melalui menu **Buku** di admin.

Di form Buku, sampul dapat diunggah manual atau diambil dari URL HTTPS gambar. Gambar dari URL divalidasi, diperkecil, lalu disimpan ke media lokal saat buku disimpan. Tidak diperlukan Google Books API key.

## Menjalankan

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Buka blog di http://localhost:8000 dan editor di http://localhost:8000/admin/.

Saat membuat tulisan, pilih status **Terbit** agar muncul di halaman depan. Gunakan tombol `</>` atau `Ctrl/⌘ + Enter` untuk membuat blok kode.

## Metadata SEO

Halaman detail tulisan dan buku memiliki meta description otomatis (maksimal 160 karakter)
dan canonical ke `SITE_URL` (default `https://donysnotebook.page`). Isi `SITE_URL` dengan
asal URL publik lengkap, tanpa path, query, atau fragmen. Canonical tidak mengikuti host
permintaan maupun parameter pelacakan.

Deskripsi tulisan memakai ringkasan, lalu teks isi, lalu judul. Deskripsi buku memakai
pemikiran, lalu pelajaran, lalu judul dan penulis. HTML dibuang dan spasi dirapikan;
catatan buku, termasuk catatan privat, tidak dipakai untuk metadata. Tidak diperlukan
migrasi database. Rebuild container setelah perubahan kode atau `SITE_URL`.

Sitemap XML otomatis tersedia di `/sitemap.xml`: beranda, perpustakaan, timeline
bacaan, tulisan berstatus Terbit, dan halaman detail buku. Draf, pencarian,
URL admin, URL lama yang redirect, dan catatan privat tidak dicantumkan.
URL menggunakan `SITE_URL`, sama dengan canonical. `lastmod` tulisan memakai
waktu pembaruan; buku tidak mengirim `lastmod` karena catatan bisa berubah terpisah.
`/robots.txt` mencantumkan alamat sitemap dan meminta crawler melewati `/admin/`.
Setelah deploy, kirim `https://donysnotebook.page/sitemap.xml` melalui Google Search Console.

Pada admin Post, pilihan Bahasa mengatur `lang` halaman detail: Indonesia (`id`)
atau Inggris (`en`). Post baru default Indonesia; migrasi mempertahankan Inggris
untuk post lama. Ini tidak menerjemahkan isi maupun label antarmuka.
Mengedit judul memperbarui slug; koreksi manual setelahnya tetap digunakan sampai
judul diubah lagi. Slug lama dicatat sejak fitur ini dipasang dan mengarahkan ke
URL terbaru dengan 301, hanya ketika post terbit. Slug milik post lain, termasuk
riwayatnya, tidak dapat digunakan ulang. Perubahan slug historis sebelum migrasi
tidak dapat dipulihkan otomatis. Gunakan penyimpanan model/form, bukan QuerySet.update
atau bulk_create, saat mengubah judul/slug agar riwayat URL tetap tercatat.
