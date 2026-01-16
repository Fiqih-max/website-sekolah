from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
import os
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "rahasia")

# ================= DATABASE =================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# ================= INIT DB =================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nama TEXT NOT NULL,
        kelas TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS berita (
        id SERIAL PRIMARY KEY,
        judul TEXT NOT NULL,
        isi TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS galeri (
        id SERIAL PRIMARY KEY,
        judul TEXT,
        gambar TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pendaftaran (
        id SERIAL PRIMARY KEY,
        nama TEXT,
        asal_sekolah TEXT,
        no_hp TEXT,
        status TEXT DEFAULT 'baru'
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ================= AUTH DECORATOR =================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Silakan login admin", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

# ================= ROUTE UMUM =================
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, judul FROM berita ORDER BY id DESC LIMIT 5")
    berita = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", berita=berita)

@app.route("/berita")
def berita():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM berita ORDER BY id DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("berita.html", berita=data)

@app.route("/berita/<int:id>")
def detail_berita(id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM berita WHERE id=%s", (id,))
    berita = cur.fetchone()
    cur.close()
    conn.close()
    if not berita:
        return render_template("404.html"), 404
    return render_template("detail_berita.html", berita=berita)

# ================= ADMIN LOGIN =================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Login admin gagal", "danger")
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM berita")
    total_berita = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM galeri")
    total_galeri = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM pendaftaran")
    total_pendaftar = cur.fetchone()[0]
    cur.close()
    conn.close()
    return render_template(
        "admin/dashboard.html",
        total_berita=total_berita,
        total_galeri=total_galeri,
        total_pendaftar=total_pendaftar
    )

# ================= ADMIN BERITA =================
@app.route("/admin/berita")
@admin_required
def admin_berita():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM berita ORDER BY id DESC")
    berita = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin/kelola_berita.html", berita=berita)

@app.route("/admin/berita/tambah", methods=["GET", "POST"])
@admin_required
def tambah_berita():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO berita (judul, isi) VALUES (%s, %s)",
            (request.form["judul"], request.form["isi"])
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("admin_berita"))
    return render_template("admin/form_berita.html", aksi="Tambah")

# ================= ADMIN GALERI =================
UPLOAD_GALERI = "static/uploads/galeri"
os.makedirs(UPLOAD_GALERI, exist_ok=True)

@app.route("/admin/galeri")
@admin_required
def admin_galeri():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM galeri ORDER BY id DESC")
    galeri = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin/kelola_galeri.html", galeri=galeri)

@app.route("/admin/galeri/tambah", methods=["GET", "POST"])
@admin_required
def tambah_galeri():
    if request.method == "POST":
        gambar = request.files["gambar"]
        ext = gambar.filename.rsplit(".", 1)[1]
        filename = f"{uuid.uuid4()}.{ext}"
        gambar.save(os.path.join(UPLOAD_GALERI, filename))

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO galeri (judul, gambar) VALUES (%s, %s)",
            (request.form["judul"], filename)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("admin_galeri"))

    return render_template("admin/form_galeri.html", aksi="Tambah")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
