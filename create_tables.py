import sqlite3

conn = sqlite3.connect('database/sma.db')
c = conn.cursor()

# Tabel ekstrakurikuler
c.execute('''
    CREATE TABLE IF NOT EXISTS ekstrakurikuler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        deskripsi TEXT
    )
''')

# Tabel nilai
c.execute('''
    CREATE TABLE IF NOT EXISTS nilai (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        mapel TEXT NOT NULL,
        nilai INTEGER NOT NULL
    )
''')

conn.commit()
conn.close()
print("✅ Tabel berhasil dibuat atau sudah ada.")
