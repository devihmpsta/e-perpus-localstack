# LAPORAN MANUAL PENGGUNAAN APLIKASI E-PERPUS DIGITAL
**Mata Kuliah: Cloud Computing B**

---

## IDENTITAS MAHASISWA
*   **Nama**          : Devi Himawan Puspita
*   **NIM**           : 32602400013
*   **Tautan GitHub** : [https://github.com/devihmpsta/e-perpus-localstack](https://github.com/devihmpsta/e-perpus-localstack)

---

## 1. PENDAHULUAN
Aplikasi **E-Perpus Digital** adalah platform manajemen perpustakaan modern yang mengintegrasikan framework **Python Flask** dengan infrastruktur cloud lokal menggunakan **LocalStack**. Proyek ini mensimulasikan penggunaan layanan AWS (Amazon Web Services) seperti **DynamoDB** (Database), **S3** (Object Storage), dan **SQS** (Messaging) dalam lingkungan pengembangan lokal.

### Arsitektur Teknologi:
*   **Backend**: Flask (Python)
*   **Cloud Emulator**: LocalStack (Docker-based)
*   **Database**: DynamoDB (Persistensi data anggota dan buku)
*   **Storage**: S3 & Local Storage (Penyimpanan foto sampul permanen)
*   **UI/UX**: Premium Indigo Theme dengan konsep Glassmorphism.

---

## 2. PANDUAN INSTALASI (UNTUK DOSEN/PENGGUNA LAIN)
Gunakan langkah-langkah berikut untuk menjalankan aplikasi ini di perangkat lain.

### A. Persiapan Awal
Pastikan perangkat sudah terpasang:
1.  **Docker Desktop** (Sudah dalam kondisi berjalan).
2.  **Python 3.10** atau versi yang lebih baru.
3.  **Git** (Untuk melakukan cloning).

### B. Langkah-Langkah Menjalankan
Buka terminal (CMD/PowerShell/Terminal) dan jalankan perintah berikut secara berurutan:

1.  **Clone Repository**:
    ```bash
    git clone https://github.com/devihmpsta/e-perpus-localstack.git
    cd e-perpus-localstack
    ```

2.  **Jalankan Infrastruktur Cloud (Docker)**:
    ```bash
    docker compose up -d
    ```
    *Tunggu hingga status container LocalStack menjadi 'Running' di Docker Desktop.*

3.  **Konfigurasi Environment Python**:
    ```bash
    python -m venv .venv
    # Untuk Windows:
    .venv\Scripts\activate
    # Untuk Linux/Mac:
    source .venv/bin/activate
    
    pip install -r requirements.txt
    ```

4.  **Menjalankan Aplikasi**:
    ```bash
    python app.py
    ```

Akses aplikasi melalui browser di alamat: **`http://localhost:8000`**

---

## 3. PANDUAN PENGGUNAAN APLIKASI

### A. Akses Login
Aplikasi memiliki dua level akses dengan kredensial sebagai berikut:
*   **Administrator**:
    *   Username: `admin`
    *   Password: `admin123`
*   **Member**:
    *   Pengguna baru dapat melakukan registrasi mandiri melalui menu **"Daftar Member Baru"** di halaman utama untuk membuat akun dengan password kustom.

### B. Fitur Utama
1.  **Dashboard Statistik**: Menampilkan jumlah buku, anggota, dan transaksi aktif secara real-time.
2.  **Manajemen Katalog**: Admin dapat menambah/mengedit buku. Pastikan mengunggah foto sampul untuk visualisasi kartu buku yang profesional (Rasio 2:3).
3.  **Sistem Peminjaman & Pengembalian**: Alur transaksi lengkap yang mencatat kondisi buku dan tanggal peminjaman.
4.  **Edit Profil & Keamanan**: Setiap pengguna dapat memperbarui data diri (Email, Telepon, Alamat) dan mengganti kata sandi secara mandiri.

### C. Persistensi Data (PENTING)
*   **Foto Sampul**: Disimpan di folder `static/uploads/covers/` agar tetap ada meskipun Docker dimatikan.
*   **Database**: Data di DynamoDB tersimpan di dalam *Docker Named Volume* (`eperpus_data`), sehingga data pendaftaran anggota dan buku tidak akan hilang saat container di-*restart*.

---

## 4. TROUBLESHOOTING
*   **Gagal Terhubung ke LocalStack**: Pastikan Docker Desktop sudah aktif sebelum menjalankan `python app.py`.
*   **Gambar Tidak Muncul**: Pastikan Anda telah menjalankan `docker compose up -d` agar layanan S3 aktif di latar belakang.
*   **Port 8000 Terpakai**: Jika port 8000 digunakan aplikasi lain, ubah nomor port pada baris terakhir file `app.py`.

---
*Semarang, 2026 - Devi Himawan Puspita*
