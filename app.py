from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import urllib.parse

app = Flask(__name__)
app.secret_key = 'rahasia'

DB_PATH = 'database/sma.db'

# ================== FUNGSI DATABASE ==================

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


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


# ================== FOLDER UPLOAD ==================

UPLOAD_FOLDERS = [
    'static/uploads/galeri',
    'static/uploads/guru',
    'static/uploads/alumni',
    'static/uploads/ekstra'
]

for folder in UPLOAD_FOLDERS:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ================== ROUTE PUBLIC ==================

@app.route('/')
def index():
    with get_db() as conn:
        berita = conn.execute(
            "SELECT id, judul FROM berita ORDER BY id DESC LIMIT 5"
        ).fetchall()

    return render_template('index.html', berita=berita)


@app.route('/profil')
def profil():
    return render_template('profil.html')


@app.route('/kontak')
def kontak():
    return render_template('kontak.html')


@app.route('/berita')
def berita():
    with get_db() as conn:
        data = conn.execute("SELECT id, judul FROM berita").fetchall()

    return render_template('berita.html', berita=data)


@app.route('/galeri')
def galeri():
    with get_db() as conn:
        data = conn.execute("SELECT * FROM galeri ORDER BY id DESC").fetchall()

    return render_template('galeri.html', galeri=data)


@app.route('/alumni')
def alumni():
    with get_db() as conn:
        data = conn.execute("SELECT * FROM alumni").fetchall()

    return render_template('alumni.html', data_alumni=data)


@app.route('/ekstrakurikuler')
def ekstrakurikuler():
    with get_db() as conn:
        data = conn.execute("SELECT * FROM ekstrakurikuler").fetchall()

    return render_template('ekstrakurikuler.html', ekstrakurikuler=data)


# ================== PENDAFTARAN ==================

@app.route('/pendaftaran', methods=['GET', 'POST'])
def pendaftaran():
    if request.method == 'POST':
        nama = request.form['nama']
        asal = request.form['asal_sekolah']
        hp = request.form['no_hp']

        with get_db() as conn:
            conn.execute("""
                INSERT INTO pendaftaran (nama, asal_sekolah, no_hp)
                VALUES (?, ?, ?)
            """, (nama, asal, hp))

        return redirect(url_for('pendaftaran_sukses'))

    return render_template('pendaftaran.html')


@app.route('/pendaftaran/sukses')
def pendaftaran_sukses():
    return render_template('pendaftaran_sukses.html')


# ================== LOGIN ADMIN ==================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))

        flash('Login admin gagal!', 'danger')

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM pendaftaran").fetchone()[0]

    return render_template('admin/dashboard.html', total_pendaftar=total)


# ================== LOGIN USER ==================

@app.route('/users/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            ).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_logged_in'] = True
            session['user_nama'] = user['nama']
            session['user_kelas'] = user['kelas']
            return redirect(url_for('user_dashboard'))

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


# ================== ERROR ==================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ================== RUN APP ==================

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print("Database belum ada! Jalankan dulu: python create_tables.py")

    app.run()
