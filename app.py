import os
import sys
import uuid
from datetime import datetime
from functools import wraps

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
)

# ============================================================
# Konfigurasi LocalStack / AWS lokal
# ============================================================
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LOCALSTACK_ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
BOOKS_TABLE = os.getenv("BOOKS_TABLE", "eperpus_books")
MEMBERS_TABLE = os.getenv("MEMBERS_TABLE", "eperpus_members")
LOANS_TABLE = os.getenv("LOANS_TABLE", "eperpus_loans")
S3_BUCKET = os.getenv("S3_BUCKET", "eperpus-buku-local")
SQS_QUEUE = os.getenv("SQS_QUEUE", "eperpus-aktivitas")
FAVORITES_TABLE = os.getenv("FAVORITES_TABLE", "eperpus_favorites")

# Konfigurasi Upload Lokal (Untuk Keamanan Data di Windows)
UPLOAD_FOLDER = os.path.join("static", "uploads", "covers")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Kredensial dummy untuk LocalStack. Jangan pakai untuk AWS asli.
AWS_KWARGS = {
    "endpoint_url": LOCALSTACK_ENDPOINT,
    "region_name": AWS_REGION,
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
}

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "eperpus-local-secret")

# ============================================================
# Client AWS lokal
# ============================================================
dynamodb = boto3.resource("dynamodb", **AWS_KWARGS)
dynamodb_client = boto3.client("dynamodb", **AWS_KWARGS)
s3 = boto3.client("s3", **AWS_KWARGS)
sqs = boto3.client("sqs", **AWS_KWARGS)


def now_text():
    return datetime.now().strftime("%d-%m-%Y %H:%M")


def today_text():
    return datetime.now().strftime("%d-%m-%Y")


def make_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def localstack_available():
    try:
        dynamodb_client.list_tables()
        return True
    except EndpointConnectionError:
        return False
    except Exception:
        return False


def table_exists(name):
    try:
        existing = dynamodb_client.list_tables()["TableNames"]
        return name in existing
    except Exception:
        return False


def create_table_if_not_exists(name, key_name):
    if table_exists(name):
        return
    print(f"Membuat tabel DynamoDB: {name}")
    dynamodb_client.create_table(
        TableName=name,
        AttributeDefinitions=[{"AttributeName": key_name, "AttributeType": "S"}],
        KeySchema=[{"AttributeName": key_name, "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    waiter = dynamodb_client.get_waiter("table_exists")
    waiter.wait(TableName=name)


def create_bucket_if_not_exists(bucket):
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        print(f"Membuat bucket S3: {bucket}")
        s3.create_bucket(Bucket=bucket)


def get_queue_url():
    try:
        return sqs.get_queue_url(QueueName=SQS_QUEUE)["QueueUrl"]
    except ClientError:
        print(f"Membuat queue SQS: {SQS_QUEUE}")
        return sqs.create_queue(QueueName=SQS_QUEUE)["QueueUrl"]


def send_activity(message):
    try:
        sqs.send_message(QueueUrl=get_queue_url(), MessageBody=message)
    except Exception as exc:
        print("Gagal mengirim aktivitas ke SQS:", exc)


def table(name):
    return dynamodb.Table(name)


def scan_table(table_name):
    result = table(table_name).scan()
    items = result.get("Items", [])
    while "LastEvaluatedKey" in result:
        result = table(table_name).scan(ExclusiveStartKey=result["LastEvaluatedKey"])
        items.extend(result.get("Items", []))
    return items


def put_s3_text(key, content):
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )


def seed_data():
    books = scan_table(BOOKS_TABLE)
    if not books:
        sample_books = [
            {
                "book_id": "BK-001",
                "title": "Python untuk Pemula",
                "author": "Tim E-Perpus",
                "publisher": "Perpustakaan LTE CS",
                "year": "2024",
                "stock": 5,
                "description": "Buku pengantar pemrograman Python untuk latihan aplikasi lokal.",
                "s3_key": "books/python-untuk-pemula.txt",
                "created_at": now_text(),
            },
            {
                "book_id": "BK-002",
                "title": "Cloud Computing Dasar",
                "author": "Admin Perpus",
                "publisher": "LocalStack Press",
                "year": "2025",
                "stock": 4,
                "description": "Materi dasar cloud computing, emulator cloud, dan LocalStack.",
                "s3_key": "books/cloud-computing-dasar.txt",
                "created_at": now_text(),
            },
            {
                "book_id": "BK-003",
                "title": "Basis Data Digital",
                "author": "LTE CS Team",
                "publisher": "E-Perpus",
                "year": "2023",
                "stock": 3,
                "description": "Pengenalan penyimpanan metadata buku dan transaksi peminjaman.",
                "s3_key": "books/basis-data-digital.txt",
                "created_at": now_text(),
            },
        ]
        for book in sample_books:
            table(BOOKS_TABLE).put_item(Item=book)
            put_s3_text(book["s3_key"], f"File contoh untuk buku: {book['title']}\n")

    # Pastikan minimal ada 1 Admin di database
    try:
        all_members = scan_table(MEMBERS_TABLE)
        has_admin = any(m.get("username") == "admin" for m in all_members)
        if not has_admin:
            print("Membuat akun Administrator default di DynamoDB...")
            admin_user = {
                "member_id": "ADMIN-001",
                "name": "Administrator",
                "username": "admin",
                "password": "admin123",
                "email": "admin@eperpus.local",
                "phone": "-",
                "address": "System",
                "role": "Administrator",
                "created_at": now_text(),
            }
            table(MEMBERS_TABLE).put_item(Item=admin_user)
            
        # Hapus akun demo 'member' lama agar tidak bisa login lagi
        for m in all_members:
            if m.get("username") == "member":
                print(f"Menghapus akun demo: {m['username']}")
                table(MEMBERS_TABLE).delete_item(Key={"member_id": m["member_id"]})
    except Exception as e:
        print(f"Gagal inisialisasi akun: {e}")


def init_localstack_resources():
    if not localstack_available():
        print("\nERROR: LocalStack belum berjalan.")
        print("Jalankan salah satu perintah berikut terlebih dahulu:")
        print("  localstack start -d")
        print("atau")
        print("  docker compose up -d")
        print("\nSetelah itu jalankan lagi: python app.py\n")
        sys.exit(1)

    create_table_if_not_exists(BOOKS_TABLE, "book_id")
    create_table_if_not_exists(MEMBERS_TABLE, "member_id")
    create_table_if_not_exists(LOANS_TABLE, "loan_id")
    # Tabel favorit: PK=member_id, SK=book_id
    if not table_exists(FAVORITES_TABLE):
        print(f"Membuat tabel DynamoDB: {FAVORITES_TABLE}")
        dynamodb_client.create_table(
            TableName=FAVORITES_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "member_id", "AttributeType": "S"},
                {"AttributeName": "book_id", "AttributeType": "S"}
            ],
            KeySchema=[
                {"AttributeName": "member_id", "KeyType": "HASH"},
                {"AttributeName": "book_id", "KeyType": "RANGE"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    create_bucket_if_not_exists(S3_BUCKET)
    get_queue_url()

    # Cek apakah database benar-benar kosong (tidak ada buku DAN tidak ada anggota selain admin)
    all_books = get_books()
    all_members = get_members()
    
    # Hanya seed jika benar-benar tidak ada data
    if not all_books and len(all_members) <= 1:
        print("Database kosong, melakukan seeding data awal...")
        seed_data()
    else:
        print(f"Data ditemukan ({len(all_books)} buku, {len(all_members)} anggota). Melewati seeding.")
    
    print("LocalStack siap: S3, DynamoDB, dan SQS sudah tersedia.")


# ============================================================
# Helper aplikasi
# ============================================================
def get_books():
    return sorted(scan_table(BOOKS_TABLE), key=lambda x: x.get("title", ""))


def get_members():
    return sorted(scan_table(MEMBERS_TABLE), key=lambda x: x.get("name", ""))


def get_loans():
    return sorted(scan_table(LOANS_TABLE), key=lambda x: x.get("borrowed_at", ""), reverse=True)


def get_active_loans():
    return [loan for loan in get_loans() if loan.get("status") == "Dipinjam"]


def require_login(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_globals():
    # Hitung pesan di SQS secara real-time
    unread_count = 0
    try:
        queue_url = get_queue_url()
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url, 
            AttributeNames=['ApproximateNumberOfMessages']
        )
        unread_count = int(attrs.get('Attributes', {}).get('ApproximateNumberOfMessages', 0))
    except Exception:
        unread_count = 0

    return {
        "current_user": session.get("name", "Administrator"),
        "current_role": session.get("role", "Administrator"),
        "today": today_text(),
        "app_name": "E - Perpus",
        "unread_count": unread_count,
    }


# ============================================================
# Routes
# ============================================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Cari user di DynamoDB (Admin maupun Member) - Case Insensitive untuk username
        user_match = None
        username_lower = username.lower()
        for u in get_members():
            if u.get("username", "").lower() == username_lower:
                user_match = u
                break
        
        if user_match and user_match.get("password") == password:
            session.clear()
            role = user_match.get("role", "Member")
            session.update({
                "logged_in": True,
                "username": username,
                "name": user_match.get("name"),
                "role": role,
                "member_id": user_match.get("member_id"),
            })
            send_activity(f"{role} {user_match.get('name')} login ke E-Perpus")
            return redirect(url_for("dashboard"))

        flash("Username atau kata sandi salah.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not username:
            flash("Nama dan username wajib diisi.", "warning")
            return redirect(url_for("register"))

        if any(m.get("username") == username for m in get_members()):
            flash("Username sudah digunakan.", "danger")
            return redirect(url_for("register"))

        password = request.form.get("password", "123456").strip()
        
        member = {
            "member_id": make_id("AG"),
            "name": name,
            "username": username,
            "password": password,
            "email": email or "-",
            "phone": phone or "-",
            "address": address or "-",
            "role": "Member",
            "created_at": now_text(),
        }
        table(MEMBERS_TABLE).put_item(Item=member)
        send_activity(f"Member baru mendaftar: {name}")
        flash("Pendaftaran berhasil. Silakan login dengan kata sandi Anda.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/dashboard")
@require_login
def dashboard():
    books = get_books()
    members = get_members()
    loans = get_loans()
    returned = [x for x in loans if x.get("status") == "Dikembalikan"]
    active = [x for x in loans if x.get("status") == "Dipinjam"]
    stats = {
        "anggota": len(members),
        "buku": len(books),
        "peminjaman": len(active),
        "pengembalian": len(returned),
    }
    # Ambil 6 buku terbaru untuk preview katalog
    books = get_books()
    
    return render_template(
        "dashboard.html", 
        stats=stats, 
        recent_loans=loans[:5],
        latest_books=books[:6]
    )


@app.route("/peminjaman", methods=["GET", "POST"])
@require_login
def peminjaman():
    books = get_books()
    members = get_members()

    if request.method == "POST":
        member_id = request.form.get("member_id")
        book_id = request.form.get("book_id")
        condition_borrow = request.form.get("condition_borrow")
        borrow_date = request.form.get("borrow_date") or today_text()

        member = next((x for x in members if x.get("member_id") == member_id), None)
        book = next((x for x in books if x.get("book_id") == book_id), None)
        if not member or not book:
            flash("Anggota atau buku tidak valid.", "danger")
            return redirect(url_for("peminjaman"))
        if int(book.get("stock", 0)) <= 0:
            flash("Stok buku sedang kosong.", "warning")
            return redirect(url_for("peminjaman"))

        loan = {
            "loan_id": make_id("PM"),
            "member_id": member["member_id"],
            "member_name": member["name"],
            "book_id": book["book_id"],
            "book_title": book["title"],
            "borrowed_at": borrow_date,
            "condition_borrow": condition_borrow,
            "status": "Dipinjam",
            "created_at": now_text(),
        }
        table(LOANS_TABLE).put_item(Item=loan)
        book["stock"] = int(book.get("stock", 0)) - 1
        table(BOOKS_TABLE).put_item(Item=book)
        send_activity(f"Peminjaman buku: {member['name']} meminjam {book['title']}")
        flash("Data peminjaman berhasil disimpan.", "success")
        return redirect(url_for("peminjaman"))

    selected_member_id = session.get("member_id") if session.get("role") == "Member" else None
    loans = get_loans()
    return render_template(
        "peminjaman.html",
        books=books,
        members=members,
        loans=loans,
        selected_member_id=selected_member_id,
    )


@app.route("/pengembalian", methods=["GET", "POST"])
@require_login
def pengembalian():
    all_active = get_active_loans()
    # Filter jika member, hanya tampilkan pinjaman miliknya
    if session.get("role") == "Member":
        active_loans = [x for x in all_active if x.get("member_id") == session.get("member_id")]
    else:
        active_loans = all_active

    if request.method == "POST":
        loan_id = request.form.get("loan_id")
        condition_return = request.form.get("condition_return")
        loan = next((x for x in active_loans if x.get("loan_id") == loan_id), None)
        if not loan:
            flash("Data peminjaman tidak ditemukan atau sudah dikembalikan.", "danger")
            return redirect(url_for("pengembalian"))

        loan["status"] = "Dikembalikan"
        loan["returned_at"] = today_text()
        loan["condition_return"] = condition_return
        table(LOANS_TABLE).put_item(Item=loan)

        # Tambahkan stok buku kembali
        try:
            response = table(BOOKS_TABLE).get_item(Key={"book_id": loan["book_id"]})
            book = response.get("Item")
            if book:
                book["stock"] = int(book.get("stock", 0)) + 1
                table(BOOKS_TABLE).put_item(Item=book)
        except Exception as exc:
            print("Gagal update stok:", exc)

        send_activity(f"Pengembalian buku: {loan['member_name']} mengembalikan {loan['book_title']}")
        flash("Pengembalian buku berhasil diproses.", "success")
        return redirect(url_for("pengembalian"))

    return render_template("pengembalian.html", active_loans=active_loans, loans=get_loans())


@app.route("/katalog")
@require_login
def katalog():
    return render_template("katalog.html", books=get_books())


@app.route("/katalog/<book_id>")
@require_login
def detail_buku_katalog(book_id):
    try:
        response = table(BOOKS_TABLE).get_item(Key={"book_id": book_id})
        book = response.get("Item")
        if not book:
            flash("Buku tidak ditemukan.", "danger")
            return redirect(url_for("katalog"))
        return render_template("detail_buku.html", book=book)
    except Exception as exc:
        flash(f"Gagal mengambil detail buku: {exc}", "danger")
        return redirect(url_for("katalog"))


@app.route("/buku", methods=["GET", "POST"])
@require_login
def buku():
    if session.get("role") != "Administrator":
        flash("Halaman ini hanya untuk administrator.", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        publisher = request.form.get("publisher", "").strip()
        year = request.form.get("year", "").strip()
        stock = request.form.get("stock", "1").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("Judul buku wajib diisi.", "warning")
            return redirect(url_for("buku"))

        book_id = make_id("BK")
        s3_key = f"books/{book_id}.txt"
        cover_url = None

        # Handle Cover Upload
        if "cover" in request.files:
            file = request.files["cover"]
            if file and file.filename:
                ext = file.filename.split(".")[-1]
                cover_key = f"{book_id}.{ext}"
                local_path = os.path.join(UPLOAD_FOLDER, cover_key)
                
                try:
                    # Simpan ke folder project (PERMANEN)
                    file.save(local_path)
                    cover_url = url_for('static', filename=f'uploads/covers/{cover_key}')
                    
                    # Tetap upload ke S3 sebagai backup simulasi (Opsional)
                    file.seek(0) # Reset pointer file setelah save lokal
                    s3.upload_fileobj(
                        file, 
                        S3_BUCKET, 
                        f"covers/{cover_key}", 
                        ExtraArgs={"ACL": "public-read", "ContentType": file.content_type or "image/jpeg"}
                    )
                except Exception as e:
                    print(f"Gagal simpan sampul: {e}")

        book = {
            "book_id": book_id,
            "title": title,
            "author": author or "-",
            "publisher": publisher or "-",
            "year": year or "-",
            "stock": int(stock or 1),
            "description": description or "-",
            "cover_url": cover_url,
            "s3_key": s3_key,
            "created_at": now_text(),
        }
        table(BOOKS_TABLE).put_item(Item=book)
        put_s3_text(s3_key, f"File contoh untuk buku: {title}\nDeskripsi: {description}\n")
        send_activity(f"Admin menambah buku: {title}")
        flash("Buku berhasil ditambahkan dengan sampul.", "success")
        return redirect(url_for("buku"))
    return render_template("buku.html", books=get_books())


@app.route("/buku/edit/<book_id>", methods=["GET", "POST"])
@require_login
def edit_buku(book_id):
    if session.get("role") != "Administrator":
        flash("Halaman ini hanya untuk administrator.", "warning")
        return redirect(url_for("dashboard"))

    try:
        response = table(BOOKS_TABLE).get_item(Key={"book_id": book_id})
        book = response.get("Item")
        if not book:
            flash("Buku tidak ditemukan.", "danger")
            return redirect(url_for("buku"))
    except Exception as exc:
        flash(f"Gagal mengambil data buku: {exc}", "danger")
        return redirect(url_for("buku"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        publisher = request.form.get("publisher", "").strip()
        year = request.form.get("year", "").strip()
        stock = request.form.get("stock", "1").strip()
        description = request.form.get("description", "").strip()

        if not title:
            flash("Judul buku wajib diisi.", "warning")
            return redirect(url_for("edit_buku", book_id=book_id))

        cover_url = book.get("cover_url")
        # Handle New Cover Upload
        if "cover" in request.files:
            file = request.files["cover"]
            if file and file.filename:
                ext = file.filename.split(".")[-1]
                cover_key = f"{book_id}.{ext}"
                local_path = os.path.join(UPLOAD_FOLDER, cover_key)
                
                try:
                    # Simpan ke folder project (PERMANEN)
                    file.save(local_path)
                    cover_url = url_for('static', filename=f'uploads/covers/{cover_key}')
                    
                    # Update S3 backup (Opsional)
                    file.seek(0)
                    s3.upload_fileobj(
                        file, 
                        S3_BUCKET, 
                        f"covers/{cover_key}", 
                        ExtraArgs={"ACL": "public-read", "ContentType": file.content_type or "image/jpeg"}
                    )
                except Exception as e:
                    print(f"Gagal update sampul: {e}")

        book.update({
            "title": title,
            "author": author or "-",
            "publisher": publisher or "-",
            "year": year or "-",
            "stock": int(stock or 0),
            "description": description or "-",
            "cover_url": cover_url,
            "updated_at": now_text(),
        })
        
        try:
            table(BOOKS_TABLE).put_item(Item=book)
            send_activity(f"Admin mengedit buku: {title}")
            flash("Data buku dan sampul berhasil diperbarui.", "success")
            return redirect(url_for("buku"))
        except Exception as exc:
            flash(f"Gagal memperbarui data buku: {exc}", "danger")

    return render_template("edit_buku.html", book=book)


@app.route("/buku/delete/<book_id>", methods=["POST"])
@require_login
def delete_buku(book_id):
    if session.get("role") != "Administrator":
        flash("Halaman ini hanya untuk administrator.", "warning")
        return redirect(url_for("dashboard"))

    try:
        table(BOOKS_TABLE).delete_item(Key={"book_id": book_id})
        send_activity(f"Admin menghapus buku ID: {book_id}")
        flash("Buku berhasil dihapus dari koleksi.", "success")
    except Exception as exc:
        flash(f"Gagal menghapus buku: {exc}", "danger")

    return redirect(url_for("buku"))


@app.route("/anggota", methods=["GET", "POST"])
@require_login
def anggota():
    if session.get("role") != "Administrator":
        flash("Halaman ini hanya untuk administrator.", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        if not name or not username:
            flash("Nama dan username wajib diisi.", "warning")
            return redirect(url_for("anggota"))
        member = {
            "member_id": make_id("AG"),
            "name": name,
            "username": username,
            "email": email or "-",
            "phone": phone or "-",
            "address": address or "-",
            "created_at": now_text(),
        }
        table(MEMBERS_TABLE).put_item(Item=member)
        send_activity(f"Admin menambah anggota: {name}")
        flash("Anggota berhasil ditambahkan.", "success")
        return redirect(url_for("anggota"))
    return render_template("anggota.html", members=get_members())


@app.route("/anggota/edit/<member_id>", methods=["GET", "POST"])
@require_login
def edit_anggota(member_id):
    if session.get("role") != "Administrator":
        flash("Halaman ini hanya untuk administrator.", "warning")
        return redirect(url_for("dashboard"))

    try:
        response = table(MEMBERS_TABLE).get_item(Key={"member_id": member_id})
        member = response.get("Item")
        if not member:
            flash("Anggota tidak ditemukan.", "danger")
            return redirect(url_for("anggota"))
    except Exception as exc:
        flash(f"Gagal mengambil data anggota: {exc}", "danger")
        return redirect(url_for("anggota"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not username:
            flash("Nama dan username wajib diisi.", "warning")
            return redirect(url_for("edit_anggota", member_id=member_id))

        member.update({
            "name": name,
            "username": username,
            "email": email or "-",
            "phone": phone or "-",
            "address": address or "-",
            "updated_at": now_text(),
        })
        
        try:
            table(MEMBERS_TABLE).put_item(Item=member)
            send_activity(f"Admin mengedit anggota: {name}")
            flash("Data anggota berhasil diperbarui.", "success")
            return redirect(url_for("anggota"))
        except Exception as exc:
            flash(f"Gagal memperbarui data anggota: {exc}", "danger")

    return render_template("edit_anggota.html", member=member)


@app.route("/anggota/delete/<member_id>", methods=["POST"])
@require_login
def delete_anggota(member_id):
    if session.get("role") != "Administrator":
        flash("Halaman ini hanya untuk administrator.", "warning")
        return redirect(url_for("dashboard"))

    try:
        table(MEMBERS_TABLE).delete_item(Key={"member_id": member_id})
        send_activity(f"Admin menghapus anggota ID: {member_id}")
        flash("Anggota berhasil dihapus dari sistem.", "success")
    except Exception as exc:
        flash(f"Gagal menghapus anggota: {exc}", "danger")

    return redirect(url_for("anggota"))


@app.route("/laporan")
@require_login
def laporan():
    return render_template("laporan.html", loans=get_loans())


@app.route("/pesan")
@require_login
def pesan():
    queue_url = get_queue_url()
    try:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=1,
            VisibilityTimeout=2,
            AttributeNames=['All']
        )
        messages = response.get("Messages", [])
    except Exception:
        messages = []
    return render_template("pesan.html", messages=messages)


@app.route("/favorit")
@require_login
def favorit():
    member_id = session.get("member_id", "ADMIN") # Admin juga bisa punya favorit
    try:
        # Scan atau query tabel favorit
        result = table(FAVORITES_TABLE).query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("member_id").eq(member_id)
        )
        fav_items = result.get("Items", [])
        
        # Ambil detail buku untuk setiap favorit
        books = []
        for item in fav_items:
            b_res = table(BOOKS_TABLE).get_item(Key={"book_id": item["book_id"]})
            if "Item" in b_res:
                books.append(b_res["Item"])
        
        return render_template("favorit.html", books=books)
    except Exception as exc:
        flash(f"Gagal mengambil daftar favorit: {exc}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/favorit/tambah/<book_id>")
@require_login
def tambah_favorit(book_id):
    member_id = session.get("member_id", "ADMIN")
    try:
        table(FAVORITES_TABLE).put_item(Item={
            "member_id": member_id,
            "book_id": book_id,
            "added_at": now_text()
        })
        flash("Buku telah ditambahkan ke favorit Anda.", "success")
    except Exception as exc:
        flash(f"Gagal menambah favorit: {exc}", "danger")
    return redirect(url_for("favorit"))


@app.route("/favorit/hapus/<book_id>")
@require_login
def hapus_favorit(book_id):
    member_id = session.get("member_id", "ADMIN")
    try:
        table(FAVORITES_TABLE).delete_item(Key={
            "member_id": member_id,
            "book_id": book_id
        })
        flash("Buku dihapus dari favorit.", "success")
    except Exception as exc:
        flash(f"Gagal menghapus favorit: {exc}", "danger")
    return redirect(url_for("favorit"))


@app.route("/pesan/hapus/<path:receipt_handle>", methods=["POST"])
@require_login
def hapus_pesan(receipt_handle):
    try:
        sqs.delete_message(QueueUrl=get_queue_url(), ReceiptHandle=receipt_handle)
        flash("Pesan berhasil dihapus.", "success")
    except Exception as exc:
        flash(f"Gagal menghapus pesan: {exc}", "danger")
    return redirect(url_for("pesan"))


@app.route("/pesan/baca-semua", methods=["POST"])
@require_login
def baca_semua_pesan():
    try:
        queue_url = get_queue_url()
        # Cara termudah 'tandai baca semua' di SQS adalah purge (hapus semua)
        sqs.purge_queue(QueueUrl=queue_url)
        flash("Semua pesan telah ditandai sebagai dibaca (dihapus dari antrean).", "success")
    except Exception as exc:
        # Purge hanya bisa sekali setiap 60 detik
        flash("Antrean sedang diproses atau baru saja dibersihkan. Mohon tunggu sebentar.", "warning")
    return redirect(url_for("pesan"))


@app.route("/profil/edit", methods=["GET", "POST"])
@require_login
def edit_profil():
    username = session.get("username")
    
    # Ambil data user saat ini
    user_match = None
    try:
        all_members = get_members()
        user_match = next((m for m in all_members if m.get("username") == username), None)
    except Exception:
        pass

    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        new_email = request.form.get("email", "").strip()
        new_phone = request.form.get("phone", "").strip()
        new_address = request.form.get("address", "").strip()
        
        if not new_name:
            flash("Nama wajib diisi.", "warning")
            return redirect(url_for("edit_profil"))

        if user_match:
            try:
                user_match.update({
                    "name": new_name,
                    "email": new_email or "-",
                    "phone": new_phone or "-",
                    "address": new_address or "-",
                    "updated_at": now_text()
                })
                table(MEMBERS_TABLE).put_item(Item=user_match)
                session["name"] = new_name # Update nama di session agar navbar berubah
                flash("Profil berhasil diperbarui.", "success")
            except Exception as e:
                flash(f"Gagal memperbarui profil: {e}", "danger")
        else:
            # Fallback jika user tidak ada di DB (misal session lama)
            session["name"] = new_name
            flash("Profil diperbarui di sesi, namun gagal menyimpan ke database.", "warning")
            
        return redirect(url_for("profil"))
        
    return render_template("edit_profil.html", user=user_match)


@app.route("/profil/password", methods=["GET", "POST"])
@require_login
def ganti_password():
    if request.method == "POST":
        current_pass = request.form.get("current_password")
        new_pass = request.form.get("new_password")
        confirm_pass = request.form.get("confirm_password")
        
        member_id = session.get("member_id")
        # Jika admin lama tidak punya member_id, cari berdasarkan username
        username = session.get("username")
        
        # Ambil user dari DynamoDB
        user_match = None
        for u in get_members():
            if u.get("username") == username:
                user_match = u
                break
        
        if not user_match:
            flash("Data pengguna tidak ditemukan.", "danger")
            return redirect(url_for("profil"))
            
        if user_match.get("password") != current_pass:
            flash("Kata sandi lama salah.", "danger")
            return redirect(url_for("ganti_password"))
            
        if new_pass != confirm_pass:
            flash("Konfirmasi kata sandi baru tidak cocok.", "danger")
            return redirect(url_for("ganti_password"))
            
        # Update Password
        user_match["password"] = new_pass
        table(MEMBERS_TABLE).put_item(Item=user_match)
        
        send_activity(f"User {username} mengubah kata sandi")
        flash("Kata sandi berhasil diperbarui.", "success")
        return redirect(url_for("profil"))
    return render_template("ganti_password.html")


@app.route("/profil")
@require_login
def profil():
    return render_template("profil.html")


@app.route("/identitas")
@require_login
def identitas():
    return render_template("identitas.html")


@app.route("/logout")
def logout():
    send_activity(f"{session.get('name', 'User')} logout dari E-Perpus")
    session.clear()
    flash("Anda berhasil keluar.", "success")
    return redirect(url_for("login"))


@app.route("/s3/<path:key>")
def proxy_s3(key):
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return Response(
            obj["Body"].read(),
            mimetype=obj.get("ContentType", "image/jpeg")
        )
    except Exception as e:
        print(f"S3 Proxy Error: {e}")
        return "Not Found", 404


# Inisialisasi resource saat startup
init_localstack_resources()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
