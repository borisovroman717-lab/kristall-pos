import sqlite3
import json
from datetime import datetime

DB_NAME = "kristall_mobile.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            stock REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            total REAL,
            payment_type TEXT,
            items_json TEXT,
            synced INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            pin TEXT,
            source TEXT DEFAULT 'local'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    defaults = {
        "work_mode": "autonomous",
        "server_ip": "192.168.1.100",
        "shop_name": "Магазин «Кристалл»",
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone() == 0:
        cur.execute(
            "INSERT INTO users (name, role, pin, source) VALUES (?, ?, ?, ?)",
            ("Администратор", "admin", "0000", "local"),
        )

    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone() == 0:
        demo_items = [
            ("4600001", "Хлеб Бородинский 400г", 54.00, 25),
            ("4600002", "Молоко Домик 3.2% 1л", 89.50, 40),
            ("4600003", "Кофе зерновой 250г", 450.00, 12),
            ("4600004", "Вода питьевая 0.5л", 35.00, 100),
            ("4600005", "Шоколад молочный 90г", 115.00, 30),
        ]
        cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", demo_items)

    conn.commit()
    conn.close()

def get_setting(key, default=""):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name, role, pin, source FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_local_user(name, role, pin):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, role, pin, source) VALUES (?, ?, ?, 'local')", (name, role, pin))
    conn.commit()
    conn.close()

def update_user_pin(user_id, new_pin):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE users SET pin = ? WHERE id = ?", (new_pin, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def clear_network_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE source = 'network'")
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT barcode, name, price, stock FROM products ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def upsert_product(barcode, name, price, stock):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)", (barcode, name, float(price), float(stock)))
    conn.commit()
    conn.close()

def delete_product(barcode):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
    conn.commit()
    conn.close()

def save_receipt(total, pay_type, cart):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO receipts (created_at, total, payment_type, items_json, synced) VALUES (?, ?, ?, ?, 0)",
        (now_str, total, pay_type, json.dumps(cart, ensure_ascii=False)),
    )
    for b, item in cart.items():
        cur.execute("UPDATE products SET stock = stock - ? WHERE barcode = ?", (item["qty"], b))
    conn.commit()
    conn.close()

def get_receipts():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, total, payment_type, synced FROM receipts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
