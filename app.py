from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
import urllib.parse

app = Flask(__name__)
app.secret_key = 'rahasia'

# ================== KONFIGURASI POSTGRESQL ==================

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pendaftaran (
        id SERIAL PRIMARY KEY,
        nama TEXT NOT NULL,
        asal_sekolah TEXT NOT NULL,
        no_hp TEXT NOT NULL,
        status TEXT DEFAULT 'baru'
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS berita (
        id SERIAL PRIMARY KEY,
        judul TEXT NOT NULL,
        isi TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alumni (
        id SERIAL PRIMARY KEY,
        nama TEXT NOT NULL,
        tahun_lulus TEXT NOT NULL,
        pekerjaan TEXT NOT NULL,
        foto TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS galeri (
        id SERIAL PRIMARY KEY,
        judul TEXT NOT NULL,
        gambar TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS guru (
        id SERIAL PRIMARY KEY,
        nip TEXT,
        nama TEXT NOT NULL,
        mapel TEXT NOT NULL,
        kontak TEXT NOT NULL,
        foto TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nama TEXT NOT NULL,
        kelas TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        is_active INTEGER DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nilai (
        id SERIAL PRIMARY KEY,
        nama TEXT NOT NULL,
        mapel TEXT NOT NULL,
        nilai INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ekstrakurikuler (
        id SERIAL PRIMARY KEY,
        nama TEXT NOT NULL,
        deskripsi TEXT NOT NULL,
        gambar TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ================== DECORATOR LOGIN ==================

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Silakan login sebagai admin terlebih dahulu!', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user_logged_in'):
            flash('Silakan login sebagai siswa terlebih dahulu!', 'warning')
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return wrapper

# ================== KONFIG UPLOAD ==================

UPLOAD_GALERI = 'static/uploads/galeri'
UPLOAD_GURU = 'static/uploads/guru'
UPLOAD_ALUMNI = 'static/uploads/alumni'
UPLOAD_EKSTRA = 'static/uploads/ekstra'

for folder in [UPLOAD_GALERI, UPLOAD_GURU, UPLOAD_ALUMNI, UPLOAD_EKSTRA]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================== ROUTE UTAMA ==================

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT id, judul FROM berita ORDER BY id DESC LIMIT 5")
    berita = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('index.html', berita=berita)

@app.route('/berita')
def berita():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM berita")
    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('berita.html', berita=data)

@app.route('/galeri')
def galeri():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM galeri ORDER BY id DESC")
    galeri = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('galeri.html', galeri=galeri)

# ================== PENDAFTARAN ==================

@app.route('/pendaftaran', methods=['GET', 'POST'])
def pendaftaran():
    if request.method == 'POST':
        nama = request.form['nama']
        asal_sekolah = request.form['asal_sekolah']
        no_hp = request.form['no_hp']

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO pendaftaran (nama, asal_sekolah, no_hp)
            VALUES (%s, %s, %s)
        """, (nama, asal_sekolah, no_hp))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('pendaftaran_sukses'))

    return render_template('pendaftaran.html')

@app.route('/pendaftaran/sukses')
def pendaftaran_sukses():
    return render_template('pendaftaran_sukses.html')

# ================== LOGIN ADMIN ==================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau Password admin salah!', 'danger')

    return render_template('admin/login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db()
    cur = conn.cursor()

    tables = [
        "pendaftaran", "berita", "alumni",
        "guru", "users", "nilai",
        "galeri", "ekstrakurikuler"
    ]

    stats = {}

    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        stats[t] = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template('admin/dashboard.html', **stats)

# ================== CRUD GURU ==================

@app.route('/admin/guru')
@admin_required
def admin_guru():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM guru")
    guru = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('admin/kelola_guru.html', guru=guru)

@app.route('/admin/guru/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_guru():
    if request.method == 'POST':
        nip = request.form['nip']
        nama = request.form['nama']
        mapel = request.form['mapel']
        kontak = request.form['kontak']

        foto = request.files.get('foto')
        foto_filename = None

        if foto and allowed_file(foto.filename):
            ext = foto.filename.rsplit('.', 1)[1].lower()
            foto_filename = f"{uuid.uuid4()}.{ext}"
            foto.save(os.path.join(UPLOAD_GURU, foto_filename))

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO guru (nip, nama, mapel, kontak, foto)
            VALUES (%s, %s, %s, %s, %s)
        """, (nip, nama, mapel, kontak, foto_filename))

        conn.commit()
        cur.close()
        conn.close()

        flash('Guru berhasil ditambahkan!')
        return redirect(url_for('admin_guru'))

    return render_template('admin/form_guru.html', aksi='Tambah')

# ================== LOGIN USER ==================

@app.route('/users/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_logged_in'] = True
            session['user_nama'] = user['nama']
            session['user_kelas'] = user['kelas']
            return redirect(url_for('user_dashboard'))
        else:
            flash('Username atau password salah!', 'danger')

    return render_template('users/login.html')

@app.route('/users/dashboard')
@user_required
def user_dashboard():
    return render_template(
        'users/dashboard.html',
        nama=session['user_nama'],
        kelas=session['user_kelas']
    )

@app.route('/users/logout')
def user_logout():
    session.clear()
    return redirect(url_for('user_login'))

# ================== DETAIL BERITA ==================

@app.route('/berita/<int:id>')
def detail_berita(id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM berita WHERE id=%s", (id,))
    berita = cur.fetchone()

    cur.close()
    conn.close()

    if berita:
        return render_template('detail_berita.html', berita=berita)
    return render_template('404.html'), 404

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run()
