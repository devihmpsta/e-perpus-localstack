# Panduan Upload Project ke GitHub

## 1. Buat Repository di GitHub

1. Buka https://github.com
2. Login ke akun GitHub.
3. Klik tombol **New repository**.
4. Isi nama repository, contoh:

```text
e-perpus-python-localstack
```

5. Pilih **Public** agar dosen atau teman bisa melihat kode.
6. Jangan centang README karena project sudah memiliki README.
7. Klik **Create repository**.

## 2. Upload dari Komputer

Buka terminal di folder project:

```bash
cd e-perpus-python-localstack
```

Jalankan perintah berikut:

```bash
git init
git add .
git commit -m "Initial commit aplikasi E-Perpus Python LocalStack"
git branch -M main
git remote add origin https://github.com/devihmpsta/e-perpus-python-localstack.git
git push -u origin main
```

Ganti `USERNAME` dengan username GitHub Anda.

Contoh:

```bash
git remote add origin https://github.com/devihmpsta/e-perpus-python-localstack.git
```

## 3. Jika Setelah Edit Ingin Push Lagi

Setelah ada perubahan file, jalankan:

```bash
git status
git add .
git commit -m "Update tampilan dan fitur aplikasi"
git push
```

Jika `git status` menampilkan `modified`, artinya ada file yang berubah dan perlu di-commit.

## 4. Panduan Agar Orang Lain Bisa Menjalankan

Orang lain cukup clone repository:

```bash
git clone https://github.com/devihmpsta/e-perpus-python-localstack.git
cd e-perpus-python-localstack
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
localstack start -d
python app.py
```

Lalu buka browser:

```text
http://localhost:8000
```
