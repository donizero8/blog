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

Konfigurasi production menggunakan volume lokal Docker `media_data`. Volume ini
dipasang read-write pada Django dan read-only pada Nginx, sehingga foto profil,
sampul buku, dan gambar artikel tetap ada setelah rebuild container.

Di Droplet, salin konfigurasi environment dan isi dengan domain serta secret yang
kuat:

```bash
cp .env.production.example .env
nano .env
docker compose -f compose.prod.yaml config --quiet
docker compose -f compose.prod.yaml up --build -d
```

Container Nginx hanya membuka `127.0.0.1:8080`. Salin konfigurasi host, ganti
`example.com`, lalu aktifkan:

```bash
sudo cp deploy/nginx-host.conf.example /etc/nginx/sites-available/donys-notebook
sudo nano /etc/nginx/sites-available/donys-notebook
sudo ln -s /etc/nginx/sites-available/donys-notebook /etc/nginx/sites-enabled/donys-notebook
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d example.com -d www.example.com
```

Production memaksa HTTPS dan memulai HSTS selama satu jam
(`SECURE_HSTS_SECONDS=3600`). Pastikan HTTP, HTTPS, admin, dan upload media bekerja
normal sebelum menaikkan nilainya, misalnya ke `86400` lalu `31536000`. Jangan
aktifkan `SECURE_HSTS_INCLUDE_SUBDOMAINS` atau `SECURE_HSTS_PRELOAD` sebelum semua
subdomain dipastikan selalu mendukung HTTPS.

Gunakan perintah production ini untuk operasi berikutnya:

```bash
docker compose -f compose.prod.yaml ps
docker compose -f compose.prod.yaml logs --tail=100 web
docker compose -f compose.prod.yaml exec web python manage.py createsuperuser
```

Jangan menjalankan `docker compose down -v`, karena opsi `-v` menghapus volume
database dan media. Cadangkan kedua volume secara rutin sebelum upgrade besar.
