# Panduan Penggunaan E-Perpus Digital (Premium Edition)

Aplikasi Perpustakaan Digital modern berbasis Python Flask dengan integrasi Cloud Lokal menggunakan LocalStack (DynamoDB, S3, SQS).

## 1. Persiapan Sistem

Pastikan perangkat Anda sudah terinstal:
*   **Python 3.10+**
*   **Docker Desktop** (Wajib untuk LocalStack)

## 2. Instalasi & Menjalankan Aplikasi

1.  Buka terminal di folder project.
2.  Jalankan infrastruktur Cloud Lokal:
    ```bash
    docker compose up -d
    ```
3.  Siapkan Virtual Environment & Dependencies:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```
4.  Jalankan aplikasi:
    ```bash
    python app.py
    ```
5.  Akses aplikasi melalui browser: `http://localhost:8000`

## 3. Akses Masuk (Kredensial)

Sistem menggunakan database DynamoDB yang dinamis. Password tidak lagi dikunci di kode program.

*   **Administrator**:
    *   Username: `admin`
    *   Password: `admin123` (Disarankan segera diubah melalui menu Profil)
*   **Member**:
    *   Silakan klik **"Daftar Member Baru"** di halaman login untuk membuat akun sendiri dengan password kustom.
    *   *Catatan: Akun demo 'member' lama telah dihapus untuk keamanan.*

## 4. Fitur Utama & Teknologi

### A. Tampilan Premium Indigo
*   **Sidebar & Glassmorphism**: Navigasi modern dengan efek transparansi.
*   **Responsive Grid**: Layout katalog yang menyesuaikan ukuran layar secara otomatis.
*   **Dashboard Statistik**: Ringkasan jumlah buku, anggota, dan transaksi dalam bentuk kartu visual.

### B. Manajemen Katalog & Foto Sampul
*   **Format 2:3**: Kartu buku dioptimalkan untuk rasio sampul buku standar (lebih profesional).
*   **Penyimpanan Permanen**: Foto sampul disimpan secara fisik di folder `static/uploads/covers/` sehingga **tidak akan hilang** meskipun Docker dimatikan.
*   **Simulasi Cloud**: Sistem tetap mensinkronisasikan foto ke **S3 LocalStack** sebagai backup cloud.

### C. Manajemen Profil & Keamanan
*   **Edit Profil Lengkap**: Pengguna dapat mengubah Nama, Alamat, Telepon, dan Email secara mandiri.
*   **Ganti Password**: Fitur keamanan untuk memperbarui kata sandi langsung ke DynamoDB.
*   **Master Data Anggota**: Administrator dapat mengelola seluruh data anggota melalui panel kontrol.

### D. Fitur Favorit & Pesan (SQS)
*   **Favorit**: Member dapat menandai buku yang disukai untuk diakses cepat nanti.
*   **Aktivitas SQS**: Setiap log masuk dan aktivitas penting dikirim ke antrean SQS sebagai simulasi pesan sistem.

## 5. Tips Persistensi Data (Docker)

Agar data Anda tetap aman saat komputer dimatikan:
1.  **Stop Container**: Gunakan `docker compose stop` untuk mematikan sementara tanpa menghapus database.
2.  **Named Volume**: Proyek ini menggunakan Docker Named Volume (`eperpus_data`) yang menjamin data DynamoDB Anda tetap tersimpan meskipun Anda menjalankan `docker compose down`.
3.  **Local Backup**: File foto sampul Anda aman di folder `static/uploads/`, pastikan folder ini tidak dihapus secara manual.

---
*Dikembangkan oleh Tim E-Perpus Digital - 2026*
