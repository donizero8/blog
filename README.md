# Dony’s Notebook

Blog Django + PostgreSQL dalam Docker, dengan editor admin bergaya Medium dan dukungan blok kode.

Profil penulis di sidebar dapat diubah melalui menu **Profil situs** di admin, termasuk foto, headline, bio, lokasi, LinkedIn, dan GitHub. Foto tersimpan persisten di volume Docker `media_data`.

Reading journal tersedia di `/library/`. Buku, status baca, progres, rating, sampul, pelajaran, dan catatan per bab dikelola melalui menu **Buku** di admin.

## Menjalankan

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Buka blog di http://localhost:8000 dan editor di http://localhost:8000/admin/.

Saat membuat tulisan, pilih status **Terbit** agar muncul di halaman depan. Gunakan tombol `</>` atau `Ctrl/⌘ + Enter` untuk membuat blok kode.

## Produksi

Ganti `SECRET_KEY`, set `DEBUG=0`, isi `ALLOWED_HOSTS`, dan gunakan password PostgreSQL yang kuat di `.env`.
