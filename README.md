# E-Perpus Digital

Sistem manajemen perpustakaan modern berbasis Python Flask yang diintegrasikan dengan LocalStack untuk simulasi infrastruktur Cloud AWS (DynamoDB, S3, dan SQS).

## Gambaran Umum

Aplikasi ini dirancang dengan antarmuka Indigo yang responsif, mendukung manajemen katalog buku, keanggotaan, dan transaksi peminjaman secara digital. Data disimpan secara persisten menggunakan emulator LocalStack, memastikan lingkungan pengembangan yang serupa dengan arsitektur cloud aslinya.

## Fitur Utama

*   Sistem Otentikasi: Login Administrator dan Member dengan fitur pembaruan kata sandi mandiri.
*   Katalog Visual: Manajemen buku dengan sampul rasio 2:3 yang disimpan secara permanen di direktori lokal dan S3.
*   Infrastruktur Cloud: Penggunaan DynamoDB untuk basis data, S3 untuk penyimpanan objek, dan SQS untuk antrean aktivitas.
*   Manajemen Profil: Pembaruan informasi akun secara lengkap bagi setiap pengguna.

## Panduan Instalasi

1.  Persiapan Infrastruktur:
    Jalankan LocalStack menggunakan Docker:
    ```bash
    docker compose up -d
    ```

2.  Konfigurasi Lingkungan:
    Instal dependensi yang diperlukan:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Untuk Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  Menjalankan Aplikasi:
    ```bash
    python app.py
    ```

Akses aplikasi melalui: `http://localhost:8000`

## Akses Pengguna

*   Administrator: `admin` / `admin123`
*   Member: Silakan daftar melalui formulir registrasi yang tersedia di halaman login.

## Struktur Direktori

*   `app.py`: Logika inti aplikasi dan integrasi cloud.
*   `static/uploads/covers/`: Lokasi penyimpanan permanen foto sampul buku.
*   `templates/`: Kumpulan template antarmuka aplikasi.
*   `docker-compose.yml`: Konfigurasi layanan LocalStack.

---
E-Perpus Digital - 2026
