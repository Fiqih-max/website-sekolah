import sqlite3
import os

DB_PATH = 'database/sma.db'

if not os.path.exists('database'):
    os.makedirs('database')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("Membuat atau mengecek tabel database...")

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
    pekerjaan TEXT NOT NULL,
    foto TEXT
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

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nama TEXT NOT NULL,
    kelas TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1
)
''')

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
    deskripsi TEXT NOT NULL,
    gambar TEXT
)
''')

conn.commit()
conn.close()

print("✅ Semua tabel siap digunakan!")
