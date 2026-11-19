import sqlite3
import json
import urllib.request
from db import DB_NAME

def pull_catalog(ip):
    url = f"http://{ip.strip()}:8085/catalog"
    req = urllib.request.urlopen(url, timeout=4)
    data = json.loads(req.read().decode("utf-8"))
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM products")
    for item in data:
        cur.execute(
            "INSERT INTO products VALUES (?, ?, ?, ?)",
            (item["barcode"], item["name"], item["price"], item["stock"]),
        )
    conn.commit()
    conn.close()
    return len(data)

def pull_users(ip):
    url = f"http://{ip.strip()}:8085/users"
    req = urllib.request.urlopen(url, timeout=4)
    data = json.loads(req.read().decode("utf-8"))
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE source = 'network'")
    for u in data:
        cur.execute(
            "INSERT INTO users (name, role, pin, source) VALUES (?, ?, ?, 'network')",
            (u["name"], u.get("role", "cashier"), str(u.get("pin", "1111"))),
        )
    conn.commit()
    conn.close()
    return len(data)

def push_receipts(ip):
    url = f"http://{ip.strip()}:8085/upload_receipts"
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, total, payment_type, items_json FROM receipts WHERE synced = 0")
    unsynced = cur.fetchall()
    if not unsynced:
        conn.close()
        return 0

    payload = [
        {"id": r, "created_at": r, "total": r, "payment_type": r, "items": json.loads(r)}
        for r in unsynced
    ]
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=4)
    cur.execute("UPDATE receipts SET synced = 1 WHERE synced = 0")
    conn.commit()
    conn.close()
    return len(unsynced)
