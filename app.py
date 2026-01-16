from flask import session
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'rahasia'
DB_PATH = 'database/sma.db'
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

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


# Pastikan folder database ada
if not os.path.exists('database'):
    os.makedirs('database')

# Buat database jika belum ada
conn = sqlite3.connect('database/sma.db')
c = conn.cursor()
# ================== CREATE TABLE ==================

c.execute('''
CREATE TABLE IF NOT EXISTS pendaftaran (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    asal_sekolah TEXT NOT NULL,
    no_hp TEXT NOT NULL,
    status TEXT DEFAULT 'baru'
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS berita (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    isi TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS alumni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    tahun_lulus TEXT NOT NULL,
    pekerjaan TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS galeri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    gambar TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS guru (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nip TEXT,
    nama TEXT NOT NULL,
    mapel TEXT NOT NULL,
    kontak TEXT NOT NULL,
    foto TEXT
)
''')

# ===== TABEL TAMBAHAN (WAJIB, SEBELUMNYA HILANG) =====

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nama TEXT NOT NULL,
    kelas TEXT NOT NULL
)
''')
# ===== TAMBAHAN KOLOM USERS (AMAN) =====
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

try:
    c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
except:
    pass

try:
    c.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
except:
    pass

c.execute('''
CREATE TABLE IF NOT EXISTS nilai (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    mapel TEXT NOT NULL,
    nilai INTEGER NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS ekstrakurikuler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    deskripsi TEXT NOT NULL
)
''')

from werkzeug.utils import secure_filename
import uuid

UPLOAD_GALERI = 'static/uploads/galeri'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_GALERI, exist_ok=True)

# ================== WHATSAPP HELPER ==================
import urllib.parse   # ✅ IMPORT DI SINI (BUKAN DI BAWAH)

ADMIN_WA = "628123456789"  # GANTI nomor admin sekolah

def format_no_hp(no_hp):
    no_hp = no_hp.replace(" ", "").replace("-", "")
    if no_hp.startswith("08"):
        no_hp = "62" + no_hp[1:]
    return no_hp

def wa_link(no_hp, pesan):
    no_hp = format_no_hp(no_hp)
    pesan = urllib.parse.quote(pesan)
    return f"https://wa.me/{no_hp}?text={pesan}"
# =====================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ================== END CREATE TABLE ==================

conn.commit()
conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    berita = c.execute(
        "SELECT id, judul FROM berita ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template('index.html', berita=berita)

@app.route('/profil')
def profil():
    return render_template('profil.html')

@app.route('/berita')
def berita():
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    data = c.execute("SELECT id, judul FROM berita").fetchall()
    conn.close()
    return render_template('berita.html', berita=data)

@app.route('/galeri')
def galeri():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row   # ⬅️ INI KUNCI UTAMA
    c = conn.cursor()

    galeri = c.execute("SELECT * FROM galeri ORDER BY id DESC").fetchall()

    conn.close()
    return render_template('galeri.html', galeri=galeri)

@app.route('/ekstrakurikuler')
def ekstrakurikuler():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM ekstrakurikuler")
    data = c.fetchall()

    conn.close()
    return render_template(
        'ekstrakurikuler.html',
        ekstrakurikuler=data
    )


@app.route('/alumni')
def alumni():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM alumni")
    data_alumni = c.fetchall()

    conn.close()
    return render_template('alumni.html', data_alumni=data_alumni)
@app.route('/nilai')
def nilai():
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    data = c.execute("SELECT * FROM nilai").fetchall()
    conn.close()
    return render_template('nilai.html', nilai=data)

# ---------------- CRUD ADMIN DATA GURU ----------------

@app.route('/admin/guru')
@admin_required
def admin_guru():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM guru")
    guru = c.fetchall()
    conn.close()
    return render_template('admin/kelola_guru.html', guru=guru)




# ===== KONFIGURASI UPLOAD FOTO GURU =====
UPLOAD_GURU = 'static/uploads/guru'
os.makedirs(UPLOAD_GURU, exist_ok=True)


@app.route('/admin/guru/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_guru():
    if request.method == 'POST':
        nip = request.form['nip']
        nama = request.form['nama']
        mapel = request.form['mapel']
        kontak = request.form['kontak']

        foto_file = request.files.get('foto')
        foto_filename = None

        if foto_file and foto_file.filename != '':
            foto_filename = foto_file.filename
            foto_file.save(os.path.join(UPLOAD_GURU, foto_filename))

        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO guru (nip, nama, mapel, kontak, foto)
            VALUES (?, ?, ?, ?, ?)
        """, (nip, nama, mapel, kontak, foto_filename))
        conn.commit()
        conn.close()

        flash('Data guru berhasil ditambahkan!')
        return redirect(url_for('admin_guru'))

    # ✅ INI YANG TADI HILANG
    return render_template('admin/form_guru.html', aksi='Tambah')





@app.route('/admin/guru/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_guru(id):
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    guru = c.execute("SELECT * FROM guru WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        nip = request.form['nip']
        nama = request.form['nama']
        mapel = request.form['mapel']
        kontak = request.form['kontak']

        foto_file = request.files.get('foto')
        foto_filename = guru['foto']  # ⬅️ PERTAHANKAN FOTO LAMA

        if foto_file and foto_file.filename != '':
            ext = foto_file.filename.rsplit('.', 1)[1].lower()
            foto_filename = f"{uuid.uuid4()}.{ext}"
            foto_file.save(os.path.join(UPLOAD_GURU, foto_filename))

        c.execute("""
            UPDATE guru
            SET nip=?, nama=?, mapel=?, kontak=?, foto=?
            WHERE id=?
        """, (nip, nama, mapel, kontak, foto_filename, id))

        conn.commit()
        conn.close()

        flash('Data guru berhasil diperbarui!')
        return redirect(url_for('admin_guru'))

    conn.close()
    return render_template('admin/form_guru.html', guru=guru, aksi='Edit')
@app.route('/admin/guru/hapus/<int:id>')
@admin_required
def hapus_guru(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("DELETE FROM guru WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Data guru berhasil dihapus!')
    return redirect(url_for('admin_guru'))

@app.route('/kontak')
def kontak():
    return render_template('kontak.html')

@app.route('/pendaftaran', methods=['GET', 'POST'])
def pendaftaran():
    if request.method == 'POST':
        nama = request.form['nama']
        asal_sekolah = request.form['asal_sekolah']
        no_hp = request.form['no_hp']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO pendaftaran (nama, asal_sekolah, no_hp)
            VALUES (?, ?, ?)
        """, (nama, asal_sekolah, no_hp))
        conn.commit()
        conn.close()

        return redirect(url_for('pendaftaran_sukses'))

    return render_template('pendaftaran.html')

@app.route('/pendaftaran/sukses')
def pendaftaran_sukses():
    return render_template('pendaftaran_sukses.html')

# ================= LOGIN ADMIN =================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # LOGIN ADMIN (sementara / hardcode)
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau Password admin salah!', 'danger')
            return redirect(url_for('admin_login'))

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Admin berhasil logout.', 'info')
    return redirect(url_for('admin_login'))



@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()

    total_pendaftar = c.execute("SELECT COUNT(*) FROM pendaftaran").fetchone()[0]
    pendaftar_baru = c.execute(
    "SELECT COUNT(*) FROM pendaftaran WHERE status='baru'"
).fetchone()[0]
    total_berita = c.execute("SELECT COUNT(*) FROM berita").fetchone()[0]
    total_alumni = c.execute("SELECT COUNT(*) FROM alumni").fetchone()[0]
    total_guru = c.execute("SELECT COUNT(*) FROM guru").fetchone()[0]
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_nilai = c.execute("SELECT COUNT(*) FROM nilai").fetchone()[0]
    total_galeri = c.execute("SELECT COUNT(*) FROM galeri").fetchone()[0]
    total_ekstra = c.execute("SELECT COUNT(*) FROM ekstrakurikuler").fetchone()[0]

    conn.close()

    return render_template(
        'admin/dashboard.html',
        total_pendaftar=total_pendaftar,
        pendaftar_baru=pendaftar_baru,
        total_berita=total_berita,
        total_alumni=total_alumni,
        total_guru=total_guru,
        total_users=total_users,
        total_nilai=total_nilai,
        total_galeri=total_galeri,
        total_ekstra=total_ekstra
    )




@app.route('/admin/berita')
@admin_required
def admin_berita():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row   # 🔥 INI KUNCI
    c = conn.cursor()

    c.execute("SELECT * FROM berita")
    berita = c.fetchall()

    conn.close()
    return render_template('admin/kelola_berita.html', berita=berita)


@app.route('/admin/berita/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_berita():
    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute("INSERT INTO berita (judul, isi) VALUES (?, ?)", (judul, isi))
        conn.commit()
        conn.close()
        flash('Berita berhasil ditambahkan!')
        return redirect(url_for('admin_berita'))
    return render_template('admin/form_berita.html', aksi='Tambah')

@app.route('/admin/berita/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_berita(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        c.execute("UPDATE berita SET judul = ?, isi = ? WHERE id = ?", (judul, isi, id))
        conn.commit()
        conn.close()
        flash('Berita berhasil diperbarui!')
        return redirect(url_for('admin_berita'))
    berita = c.execute("SELECT * FROM berita WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('admin/form_berita.html', berita=berita, aksi='Edit')

@app.route('/admin/berita/hapus/<int:id>')
@admin_required
def hapus_berita(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("DELETE FROM berita WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Berita berhasil dihapus!')
    return redirect(url_for('admin_berita'))

@app.route('/admin/alumni')
@admin_required
def admin_alumni():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM alumni")
    alumni = c.fetchall()
    conn.close()
    return render_template('admin/kelola_alumni.html', alumni=alumni)


UPLOAD_ALUMNI = 'static/uploads/alumni'
os.makedirs(UPLOAD_ALUMNI, exist_ok=True)

@app.route('/admin/alumni/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_alumni():
    if request.method == 'POST':
        nama = request.form['nama']
        tahun_lulus = request.form['tahun_lulus']
        pekerjaan = request.form['pekerjaan']

        foto_file = request.files.get('foto')
        foto_filename = None

        if foto_file and foto_file.filename != '':
            ext = foto_file.filename.rsplit('.', 1)[1].lower()
            foto_filename = f"{uuid.uuid4()}.{ext}"
            foto_file.save(os.path.join(UPLOAD_ALUMNI, foto_filename))

        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO alumni (nama, tahun_lulus, pekerjaan, foto) VALUES (?, ?, ?, ?)",
            (nama, tahun_lulus, pekerjaan, foto_filename)
        )
        conn.commit()
        conn.close()

        flash('Alumni berhasil ditambahkan!')
        return redirect(url_for('admin_alumni'))

    return render_template('admin/form_alumni.html', aksi='Tambah')


@app.route('/admin/alumni/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_alumni(id):
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    alumni = c.execute("SELECT * FROM alumni WHERE id=?", (id,)).fetchone()

    if request.method == 'POST':
        nama = request.form['nama']
        tahun_lulus = request.form['tahun_lulus']
        pekerjaan = request.form['pekerjaan']

        foto_file = request.files.get('foto')
        foto_filename = alumni['foto']

        if foto_file and foto_file.filename != '':
            ext = foto_file.filename.rsplit('.', 1)[1].lower()
            foto_filename = f"{uuid.uuid4()}.{ext}"
            foto_file.save(os.path.join(UPLOAD_ALUMNI, foto_filename))

        c.execute(
            "UPDATE alumni SET nama=?, tahun_lulus=?, pekerjaan=?, foto=? WHERE id=?",
            (nama, tahun_lulus, pekerjaan, foto_filename, id)
        )
        conn.commit()
        conn.close()
        flash('Data alumni diperbarui!')
        return redirect(url_for('admin_alumni'))

    conn.close()
    return render_template('admin/form_alumni.html', alumni=alumni, aksi='Edit')


@app.route('/admin/alumni/hapus/<int:id>')
@admin_required
def hapus_alumni(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("DELETE FROM alumni WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Data alumni berhasil dihapus!')
    return redirect(url_for('admin_alumni'))
@app.route('/profil/guru')
def data_guru():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM guru")
    data_guru = c.fetchall()

    conn.close()
    return render_template('data_guru.html', data_guru=data_guru)
@app.route('/profil/alumni')
def data_alumni():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM alumni")
    data_alumni = c.fetchall()

    conn.close()
    return render_template('alumni.html', data_alumni=data_alumni)

@app.route('/admin/ekstrakurikuler')
@admin_required
def admin_ekstrakurikuler():
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    data = c.execute("SELECT * FROM ekstrakurikuler").fetchall()
    conn.close()
    ekstrakurikuler = [{'id': d[0], 'nama': d[1], 'deskripsi': d[2]} for d in data]
    return render_template('admin/kelola_ekstra.html', ekstrakurikuler=ekstrakurikuler)
UPLOAD_EKSTRA = 'static/uploads/ekstra'
os.makedirs(UPLOAD_EKSTRA, exist_ok=True)

@app.route('/admin/ekstrakurikuler/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_ekstra():
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']

        gambar_file = request.files.get('gambar')
        gambar_filename = None

        if gambar_file and gambar_file.filename != '':
            ext = gambar_file.filename.rsplit('.', 1)[1].lower()
            gambar_filename = f"{uuid.uuid4()}.{ext}"
            gambar_file.save(os.path.join(UPLOAD_EKSTRA, gambar_filename))

        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO ekstrakurikuler (nama, deskripsi, gambar) VALUES (?, ?, ?)",
            (nama, deskripsi, gambar_filename)
        )
        conn.commit()
        conn.close()

        flash('Ekstrakurikuler berhasil ditambahkan!')
        return redirect(url_for('admin_ekstrakurikuler'))

    return render_template('admin/form_ekstra.html', aksi='Tambah')

@app.route('/admin/ekstrakurikuler/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_ekstra(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    if request.method == 'POST':
        c.execute("UPDATE ekstrakurikuler SET nama = ?, deskripsi = ? WHERE id = ?", (request.form['nama'], request.form['deskripsi'], id))
        conn.commit()
        conn.close()
        flash('Ekstrakurikuler berhasil diperbarui!')
        return redirect(url_for('admin_ekstrakurikuler'))
    ekstra = c.execute("SELECT * FROM ekstrakurikuler WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('admin/form_ekstra.html', ekstra=ekstra, aksi='Edit')

@app.route('/admin/ekstrakurikuler/hapus/<int:id>')
@admin_required
def hapus_ekstra(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("DELETE FROM ekstrakurikuler WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Ekstrakurikuler berhasil dihapus!')
    return redirect(url_for('admin_ekstrakurikuler'))


# ---------------- GALERI ADMIN ----------------
@app.route('/admin/galeri')
@admin_required
def admin_galeri():
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    galeri_data = c.execute("SELECT * FROM galeri").fetchall()
    conn.close()
    galeri = [{'id': g[0], 'judul': g[1], 'gambar': g[2]} for g in galeri_data]
    return render_template('admin/kelola_galeri.html', galeri=galeri)

@app.route('/admin/galeri/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_galeri():
    if request.method == 'POST':
        judul = request.form.get('judul')

        # ⛔ VALIDASI FILE
        if 'gambar' not in request.files:
            flash('File gambar tidak ditemukan')
            return redirect(request.referrer)

        gambar = request.files['gambar']

        if gambar.filename == '':
            flash('Tidak ada file dipilih')
            return redirect(request.referrer)

        if not allowed_file(gambar.filename):
            flash('Format file tidak diizinkan')
            return redirect(request.referrer)

        # 🔐 Nama file aman & unik
        ext = gambar.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"

        gambar.save(os.path.join(UPLOAD_GALERI, filename))

        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO galeri (judul, gambar) VALUES (?, ?)",
            (judul, filename)
        )
        conn.commit()
        conn.close()

        flash('Galeri berhasil ditambahkan!')
        return redirect(url_for('admin_galeri'))

    return render_template('admin/form_galeri.html', aksi='Tambah')


@app.route('/admin/galeri/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_galeri(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    if request.method == 'POST':
        judul = request.form['judul']
        gambar = request.form['gambar']
        c.execute("UPDATE galeri SET judul = ?, gambar = ? WHERE id = ?", (judul, gambar, id))
        conn.commit()
        conn.close()
        flash('Data galeri berhasil diperbarui!')
        return redirect(url_for('admin_galeri'))
    galeri = c.execute("SELECT * FROM galeri WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('admin/form_galeri.html', galeri=galeri, aksi='Edit')

@app.route('/admin/galeri/hapus/<int:id>')
@admin_required
def hapus_galeri(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("DELETE FROM galeri WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Data galeri berhasil dihapus!')
    return redirect(url_for('admin_galeri'))


@app.route('/admin/nilai')
@admin_required
def admin_nilai():
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    data = c.execute("SELECT * FROM nilai").fetchall()
    conn.close()
    nilai = [{'id': d[0], 'nama': d[1], 'mapel': d[2], 'nilai': d[3]} for d in data]
    return render_template('admin/kelola_nilai.html', nilai=nilai)

@app.route('/admin/nilai/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_nilai():
    if request.method == 'POST':
        nama = request.form['nama']
        mapel = request.form['mapel']
        nilai = request.form['nilai']
        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute("INSERT INTO nilai (nama, mapel, nilai) VALUES (?, ?, ?)", (nama, mapel, nilai))
        conn.commit()
        conn.close()
        flash('Data nilai berhasil ditambahkan!')
        return redirect(url_for('admin_nilai'))
    return render_template('admin/form_nilai.html', aksi='Tambah')

@app.route('/admin/nilai/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_nilai(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    if request.method == 'POST':
        nama = request.form['nama']
        mapel = request.form['mapel']
        nilai = request.form['nilai']
        c.execute("UPDATE nilai SET nama = ?, mapel = ?, nilai = ? WHERE id = ?", (nama, mapel, nilai, id))
        conn.commit()
        conn.close()
        flash('Data nilai berhasil diperbarui!')
        return redirect(url_for('admin_nilai'))
    nilai = c.execute("SELECT * FROM nilai WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('admin/form_nilai.html', nilai=nilai, aksi='Edit')

@app.route('/admin/nilai/hapus/<int:id>')
@admin_required
def hapus_nilai(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("DELETE FROM nilai WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Data nilai berhasil dihapus!')
    return redirect(url_for('admin_nilai'))


@app.route('/admin/pendaftaran')
@admin_required
def admin_pendaftaran():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row   # 🔥 INI KUNCI UTAMA
    c = conn.cursor()

    c.execute("SELECT * FROM pendaftaran")
    pendaftar = c.fetchall()

    conn.close()
    return render_template(
        'admin/kelola_pendaftaran.html',
        pendaftar=pendaftar
    )
from sqlite3 import IntegrityError

@app.route('/admin/pendaftaran/terima/<int:id>')
@admin_required
def terima_pendaftaran(id):
    with get_db() as conn:
        cur = conn.cursor()

        p = cur.execute(
            "SELECT * FROM pendaftaran WHERE id=?", (id,)
        ).fetchone()

        if not p:
            flash('Data pendaftaran tidak ditemukan', 'warning')
            return redirect(url_for('admin_pendaftaran'))

        if p['status'] == 'diterima':
            flash('Pendaftaran sudah diterima sebelumnya', 'info')
            return redirect(url_for('admin_pendaftaran'))

        username = p['no_hp']

        # cek username
        user = cur.execute(
            "SELECT id FROM users WHERE username=?", (username,)
        ).fetchone()

        if not user:
            try:
                cur.execute("""
                    INSERT INTO users (username, password, nama, kelas)
                    VALUES (?, ?, ?, ?)
                """, (
                    username,
                    generate_password_hash("123456"),
                    p['nama'],
                    'X'
                ))
            except IntegrityError:
                flash('Username sudah ada', 'warning')
                return redirect(url_for('admin_pendaftaran'))

        cur.execute(
            "UPDATE pendaftaran SET status='diterima' WHERE id=?",
            (id,)
        )

        conn.commit()

    flash('Pendaftar berhasil diterima', 'success')
    return redirect(url_for('admin_pendaftaran'))

@app.route('/admin/pendaftaran/tolak/<int:id>')
@admin_required
def tolak_pendaftaran(id):
    with get_db() as conn:
        cur = conn.cursor()

        p = cur.execute(
            "SELECT * FROM pendaftaran WHERE id=?",
            (id,)
        ).fetchone()

        if not p:
            flash('Data pendaftaran tidak ditemukan', 'warning')
            return redirect(url_for('admin_pendaftaran'))

        if p['status'] == 'ditolak':
            flash('Pendaftaran sudah ditolak sebelumnya', 'info')
            return redirect(url_for('admin_pendaftaran'))

        cur.execute(
            "UPDATE pendaftaran SET status='ditolak' WHERE id=?",
            (id,)
        )

        conn.commit()

    flash('Pendaftaran berhasil ditolak', 'danger')
    return redirect(url_for('admin_pendaftaran'))

@app.route('/admin/pendaftaran/hapus/<int:id>')
@admin_required
def hapus_pendaftaran(id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM pendaftaran WHERE id = ?", (id,)
        )
        conn.commit()

    flash('Data pendaftar berhasil dihapus!')
    return redirect(url_for('admin_pendaftaran'))
@app.route('/admin/pendaftaran/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_pendaftaran():
    if request.method == 'POST':
        nama = request.form['nama']
        asal = request.form['asal_sekolah']
        no_hp = request.form['no_hp']
        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute("INSERT INTO pendaftaran (nama, asal_sekolah, no_hp) VALUES (?, ?, ?)", (nama, asal, no_hp))
        conn.commit()
        conn.close()
        flash('Pendaftar berhasil ditambahkan!')
        return redirect(url_for('admin_pendaftaran'))
    return render_template('admin/form_pendaftaran.html', aksi='Tambah', pendaftar=None)

@app.route('/admin/pendaftaran/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_pendaftaran(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    if request.method == 'POST':
        nama = request.form['nama']
        asal = request.form['asal_sekolah']
        no_hp = request.form['no_hp']
        c.execute("UPDATE pendaftaran SET nama = ?, asal_sekolah = ?, no_hp = ? WHERE id = ?", (nama, asal, no_hp, id))
        conn.commit()
        conn.close()
        flash('Data pendaftar berhasil diperbarui!')
        return redirect(url_for('admin_pendaftaran'))
    pendaftar = c.execute("SELECT * FROM pendaftaran WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('admin/form_pendaftaran.html', aksi='Edit', pendaftar=pendaftar)

# ================= ADMIN KELOLA USERS =================

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    users = c.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template('admin/kelola_users.html', users=users)



@app.route('/admin/users/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_user():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # ⬅️ HASH PASSWORD
        nama = request.form['nama']
        kelas = request.form['kelas']

        conn = sqlite3.connect('database/sma.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, password, nama, kelas) VALUES (?, ?, ?, ?)",
            (username, password, nama, kelas)
        )
        conn.commit()
        conn.close()

        flash('User berhasil ditambahkan!')
        return redirect(url_for('admin_users'))

    return render_template('admin/form_users.html', aksi='Tambah')

@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    conn = sqlite3.connect('database/sma.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nama = request.form['nama']
        kelas = request.form['kelas']

        c.execute(
            "UPDATE users SET username=?, password=?, nama=?, kelas=? WHERE id=?",
            (username, password, nama, kelas, id)
        )
        conn.commit()
        conn.close()

        flash('User berhasil diperbarui!')
        return redirect(url_for('admin_users'))

    user = c.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template('admin/form_users.html', user=user, aksi='Edit')


@app.route('/admin/users/hapus/<int:id>')
@admin_required
def hapus_user(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash('User berhasil dihapus!')
    return redirect(url_for('admin_users'))


# ================= LOGIN USER (SISWA) =================

@app.route('/users/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']   # ✅ INI YANG HILANG

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # CARI USER BERDASARKAN USERNAME
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        # CEK PASSWORD
        if user and check_password_hash(user['password'], password):
            session['user_logged_in'] = True
            session['user_id'] = user['id']
            session['user_nama'] = user['nama']
            session['user_kelas'] = user['kelas']
            return redirect(url_for('user_dashboard'))
        else:
            flash('Username atau password salah!', 'danger')

    return render_template('users/login.html')

@app.route('/register-siswa', methods=['GET', 'POST'])
def register_siswa():
    if request.method == 'POST':
        nama = request.form['nama']
        kelas = request.form['kelas']
        username = request.form['username']
        password = request.form['password']

        password_hash = generate_password_hash(password)

        conn = sqlite3.connect('database/sma.db')
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO users (username, password, nama, kelas)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, nama, kelas))

            conn.commit()
            flash('Akun berhasil dibuat, silakan login', 'success')
            return redirect(url_for('user_login'))

        except sqlite3.IntegrityError:
            flash('Username sudah digunakan!', 'danger')

        finally:
            conn.close()

    return render_template('users/register_siswa.html')

@app.route('/users/dashboard')
@user_required
def user_dashboard():
    return render_template(
        'users/dashboard.html',
        nama=session['user_nama'],
        kelas=session['user_kelas']
    )

# ================= LUPA PASSWORD USER =================

@app.route('/users/lupa-password', methods=['GET', 'POST'])
def user_lupa_password():
    if request.method == 'POST':
        username = request.form['username']

        # (sementara hanya notifikasi)
        flash('Jika username terdaftar, password akan direset', 'info')

        return redirect(url_for('user_lupa_password'))

    return render_template('users/lupa_password.html')


@app.route('/users/logout')
def user_logout():
    session.pop('user_logged_in', None)
    session.pop('user_id', None)
    session.pop('user_nama', None)
    session.pop('user_kelas', None)
    return redirect(url_for('user_login'))



@app.route('/berita/<int:id>')
def detail_berita(id):
    conn = sqlite3.connect('database/sma.db')
    c = conn.cursor()
    c.execute("SELECT * FROM berita WHERE id = ?", (id,))
    berita = c.fetchone()
    conn.close()
    if berita:
        return render_template('detail_berita.html', berita=berita)
    else:
        return render_template('404.html'), 404


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run()
