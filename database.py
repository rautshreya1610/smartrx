"""
backend/services/database.py
=============================
Database service layer with improved error handling, pagination,
and full CRUD for all entities.
"""

import sqlite3
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from settings import DB_PATH


# ─────────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────────

import mysql.connector

import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def _row(row) -> dict:
    return dict(row) if row else None

def _rows(rows) -> list:
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# Schema bootstrap
# ─────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS medicines (
    medicine_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    generic_name  TEXT    DEFAULT '',
    category      TEXT    DEFAULT 'General',
    sub_category  TEXT    DEFAULT '',
    description   TEXT    DEFAULT '',
    manufacturer  TEXT    DEFAULT '',
    dosage_form   TEXT    DEFAULT '',   -- tablet / syrup / injection / cream
    unit          TEXT    DEFAULT 'tablet',
    requires_rx   INTEGER DEFAULT 0,   -- 1 = prescription required
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pharmacies (
    pharmacy_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    pharmacy_name TEXT    NOT NULL,
    address       TEXT    DEFAULT '',
    area          TEXT    DEFAULT '',
    city          TEXT    DEFAULT 'Bangalore',
    state         TEXT    DEFAULT 'Karnataka',
    pincode       TEXT    DEFAULT '',
    phone         TEXT    DEFAULT '',
    email         TEXT    DEFAULT '',
    owner_name    TEXT    DEFAULT '',
    rating        REAL    DEFAULT 0.0,
    is_open_24h   INTEGER DEFAULT 0,
    latitude      REAL    NOT NULL,
    longitude     REAL    NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT    NOT NULL COLLATE NOCASE,
    pharmacy_id   INTEGER NOT NULL,
    pharmacy_name TEXT    NOT NULL,
    batch_number  TEXT    DEFAULT '',
    quantity      INTEGER DEFAULT 0,
    unit_price    REAL    DEFAULT 0.0,
    mrp           REAL    DEFAULT 0.0,
    expiry_date   TEXT    NOT NULL,
    manufacture_date TEXT DEFAULT '',
    latitude      REAL    NOT NULL,
    longitude     REAL    NOT NULL,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(pharmacy_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_inv_medicine  ON inventory(medicine_name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_inv_pharmacy  ON inventory(pharmacy_id);
CREATE INDEX IF NOT EXISTS idx_inv_expiry    ON inventory(expiry_date);
CREATE INDEX IF NOT EXISTS idx_inv_quantity  ON inventory(quantity);
"""

def init_database():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print("[DB] Schema initialised.")


# ─────────────────────────────────────────────
# Medicines
# ─────────────────────────────────────────────

def get_all_medicines(page: int = 1, size: int = 200) -> list:
    offset = (page - 1) * size
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM medicines ORDER BY medicine_name LIMIT ? OFFSET ?", (size, offset)
    ).fetchall()
    conn.close()
    return _rows(rows)

def get_medicine_by_id(medicine_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM medicines WHERE medicine_id=?", (medicine_id,)).fetchone()
    conn.close()
    return _row(row)

def get_medicine_by_name(name: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM medicines WHERE LOWER(medicine_name)=LOWER(?)", (name,)
    ).fetchone()
    conn.close()
    return _row(row)

def add_medicine(data: dict) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO medicines
              (medicine_name, generic_name, category, sub_category, description,
               manufacturer, dosage_form, unit, requires_rx)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            data["medicine_name"].strip(),
            data.get("generic_name", ""),
            data.get("category", "General"),
            data.get("sub_category", ""),
            data.get("description", ""),
            data.get("manufacturer", ""),
            data.get("dosage_form", "tablet"),
            data.get("unit", "tablet"),
            int(data.get("requires_rx", 0)),
        ))
        conn.commit()
        med = get_medicine_by_id(cur.lastrowid)
        conn.close()
        return {"success": True, "medicine": med}
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "error": f"Medicine '{data['medicine_name']}' already exists."}

def update_medicine(medicine_id: int, data: dict) -> dict:
    conn = get_connection()
    conn.execute("""
        UPDATE medicines
        SET generic_name=?, category=?, sub_category=?, description=?,
            manufacturer=?, dosage_form=?, unit=?, requires_rx=?
        WHERE medicine_id=?
    """, (
        data.get("generic_name",""), data.get("category","General"),
        data.get("sub_category",""), data.get("description",""),
        data.get("manufacturer",""), data.get("dosage_form","tablet"),
        data.get("unit","tablet"), int(data.get("requires_rx",0)),
        medicine_id
    ))
    conn.commit()
    conn.close()
    return {"success": True, "medicine": get_medicine_by_id(medicine_id)}

def delete_medicine(medicine_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM medicines WHERE medicine_id=?", (medicine_id,)).fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "Not found."}
    conn.execute("DELETE FROM medicines WHERE medicine_id=?", (medicine_id,))
    conn.commit()
    conn.close()
    return {"success": True}

def count_medicines() -> int:
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
    conn.close()
    return n

def get_medicine_categories() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category, COUNT(*) as count FROM medicines GROUP BY category ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return _rows(rows)


# ─────────────────────────────────────────────
# Pharmacies
# ─────────────────────────────────────────────

def get_all_pharmacies() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM pharmacies ORDER BY pharmacy_name").fetchall()
    conn.close()
    return _rows(rows)

def get_pharmacy_by_id(pharmacy_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM pharmacies WHERE pharmacy_id=?", (pharmacy_id,)).fetchone()
    conn.close()
    return _row(row)

def add_pharmacy(data: dict) -> dict:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO pharmacies
          (pharmacy_name, address, area, city, state, pincode, phone,
           email, owner_name, rating, is_open_24h, latitude, longitude)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["pharmacy_name"], data.get("address",""), data.get("area",""),
        data.get("city","Bangalore"), data.get("state","Karnataka"),
        data.get("pincode",""), data.get("phone",""), data.get("email",""),
        data.get("owner_name",""), float(data.get("rating",0)),
        int(data.get("is_open_24h",0)),
        float(data["latitude"]), float(data["longitude"]),
    ))
    conn.commit()
    ph = get_pharmacy_by_id(cur.lastrowid)
    conn.close()
    return {"success": True, "pharmacy": ph}

def update_pharmacy(pharmacy_id: int, data: dict) -> dict:
    conn = get_connection()
    conn.execute("""
        UPDATE pharmacies
        SET pharmacy_name=?, address=?, area=?, city=?, state=?, pincode=?,
            phone=?, email=?, owner_name=?, rating=?, is_open_24h=?,
            latitude=?, longitude=?
        WHERE pharmacy_id=?
    """, (
        data.get("pharmacy_name",""), data.get("address",""), data.get("area",""),
        data.get("city","Bangalore"), data.get("state","Karnataka"),
        data.get("pincode",""), data.get("phone",""), data.get("email",""),
        data.get("owner_name",""), float(data.get("rating",0)),
        int(data.get("is_open_24h",0)),
        float(data["latitude"]), float(data["longitude"]),
        pharmacy_id
    ))
    conn.commit()
    conn.close()
    return {"success": True, "pharmacy": get_pharmacy_by_id(pharmacy_id)}

def delete_pharmacy(pharmacy_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM pharmacies WHERE pharmacy_id=?", (pharmacy_id,)).fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "Not found."}
    conn.execute("DELETE FROM pharmacies WHERE pharmacy_id=?", (pharmacy_id,))
    conn.commit()
    conn.close()
    return {"success": True}


# ─────────────────────────────────────────────
# Inventory
# ─────────────────────────────────────────────

def get_all_inventory() -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, p.latitude AS p_lat, p.longitude AS p_lon,
               p.phone, p.address, p.area, p.rating, p.is_open_24h
        FROM inventory i
        JOIN pharmacies p ON i.pharmacy_id = p.pharmacy_id
        ORDER BY i.medicine_name, i.pharmacy_id
    """).fetchall()
    conn.close()
    return _rows(rows)

def get_inventory_by_id(inventory_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("""
        SELECT i.*, p.phone, p.address, p.area, p.rating
        FROM inventory i JOIN pharmacies p ON i.pharmacy_id=p.pharmacy_id
        WHERE i.inventory_id=?
    """, (inventory_id,)).fetchone()
    conn.close()
    return _row(row)

def get_inventory_by_pharmacy(pharmacy_id: int, page: int = 1, size: int = 50) -> dict:
    offset = (page-1)*size
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) FROM inventory WHERE pharmacy_id=?", (pharmacy_id,)
    ).fetchone()[0]
    rows = conn.execute("""
        SELECT * FROM inventory WHERE pharmacy_id=?
        ORDER BY expiry_date ASC LIMIT ? OFFSET ?
    """, (pharmacy_id, size, offset)).fetchall()
    conn.close()
    return {"items": _rows(rows), "total": total, "page": page, "size": size}

def get_inventory_by_medicine(medicine_name: str) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, p.address, p.area, p.phone, p.rating, p.is_open_24h
        FROM inventory i JOIN pharmacies p ON i.pharmacy_id=p.pharmacy_id
        WHERE LOWER(i.medicine_name)=LOWER(?)
        ORDER BY i.expiry_date
    """, (medicine_name,)).fetchall()
    conn.close()
    return _rows(rows)

def add_inventory_record(data: dict) -> dict:
    ph = get_pharmacy_by_id(data["pharmacy_id"])
    if not ph:
        return {"success": False, "error": "Pharmacy not found."}
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO inventory
              (medicine_name, pharmacy_id, pharmacy_name, batch_number,
               quantity, unit_price, mrp, expiry_date, manufacture_date,
               latitude, longitude)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["medicine_name"].strip(), ph["pharmacy_id"], ph["pharmacy_name"],
            data.get("batch_number",""),
            int(data["quantity"]),
            float(data.get("unit_price", data.get("price", 0))),
            float(data.get("mrp", data.get("price", 0))),
            data["expiry_date"],
            data.get("manufacture_date",""),
            ph["latitude"], ph["longitude"],
        ))
        conn.commit()
        rec = get_inventory_by_id(cur.lastrowid)
        conn.close()
        return {"success": True, "record": rec}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

def update_inventory_record(inventory_id: int, data: dict) -> dict:
    conn = get_connection()
    conn.execute("""
        UPDATE inventory
        SET quantity=?, unit_price=?, mrp=?, expiry_date=?,
            batch_number=?, updated_at=CURRENT_TIMESTAMP
        WHERE inventory_id=?
    """, (
        int(data["quantity"]),
        float(data.get("unit_price", data.get("price",0))),
        float(data.get("mrp", data.get("price",0))),
        data["expiry_date"],
        data.get("batch_number",""),
        inventory_id
    ))
    conn.commit()
    conn.close()
    return {"success": True, "record": get_inventory_by_id(inventory_id)}

def delete_inventory_record(inventory_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM inventory WHERE inventory_id=?", (inventory_id,)).fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "Record not found."}
    rec = _row(row)
    conn.execute("DELETE FROM inventory WHERE inventory_id=?", (inventory_id,))
    conn.commit()
    conn.close()
    return {"success": True, "deleted": rec}

def get_expiring_soon(days: int = 7) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, p.phone, p.address, p.area
        FROM inventory i JOIN pharmacies p ON i.pharmacy_id=p.pharmacy_id
        WHERE date(i.expiry_date) <= date('now', '+' || ? || ' days')
        ORDER BY i.expiry_date ASC
    """, (days,)).fetchall()
    conn.close()
    return _rows(rows)

def get_low_stock(threshold: int = 10) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, p.phone, p.address
        FROM inventory i JOIN pharmacies p ON i.pharmacy_id=p.pharmacy_id
        WHERE i.quantity <= ?
        ORDER BY i.quantity ASC
    """, (threshold,)).fetchall()
    conn.close()
    return _rows(rows)

def get_dashboard_stats() -> dict:
    conn = get_connection()
    today_str = date.today().isoformat()
    stats = {
        "total_medicines":    conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0],
        "total_pharmacies":   conn.execute("SELECT COUNT(*) FROM pharmacies").fetchone()[0],
        "total_inventory":    conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0],
        "total_stock_units":  conn.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory").fetchone()[0],
        "expired_count":      conn.execute("SELECT COUNT(*) FROM inventory WHERE date(expiry_date) < date('now')").fetchone()[0],
        "expiring_7d":        conn.execute("SELECT COUNT(*) FROM inventory WHERE date(expiry_date) BETWEEN date('now') AND date('now','+7 days')").fetchone()[0],
        "expiring_30d":       conn.execute("SELECT COUNT(*) FROM inventory WHERE date(expiry_date) BETWEEN date('now') AND date('now','+30 days')").fetchone()[0],
        "low_stock_count":    conn.execute("SELECT COUNT(*) FROM inventory WHERE quantity <= 10").fetchone()[0],
        "out_of_stock":       conn.execute("SELECT COUNT(*) FROM inventory WHERE quantity = 0").fetchone()[0],
        "categories":         conn.execute("SELECT COUNT(DISTINCT category) FROM medicines").fetchone()[0],
    }
    conn.close()
    return stats


# ─────────────────────────────────────────────
# CSV Seeder
# ─────────────────────────────────────────────

def seed_from_csv(medicines_csv, pharmacies_csv, inventory_csv):
    import csv
    print("[DB] Seeding from CSV...")

    if os.path.exists(medicines_csv):
        with open(medicines_csv, newline="", encoding="utf-8") as f:
            conn = get_connection()
            for row in csv.DictReader(f):
                conn.execute("""
                    INSERT OR IGNORE INTO medicines
                      (medicine_name, generic_name, category, sub_category,
                       description, manufacturer, dosage_form, unit, requires_rx)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (
                    row["medicine_name"], row.get("generic_name",""),
                    row.get("category","General"), row.get("sub_category",""),
                    row.get("description",""), row.get("manufacturer",""),
                    row.get("dosage_form","tablet"), row.get("unit","tablet"),
                    int(row.get("requires_rx",0)),
                ))
            conn.commit(); conn.close()
        print(f"  [✓] Medicines seeded")

    if os.path.exists(pharmacies_csv):
        with open(pharmacies_csv, newline="", encoding="utf-8") as f:
            conn = get_connection()
            for row in csv.DictReader(f):
                conn.execute("""
                    INSERT OR IGNORE INTO pharmacies
                      (pharmacy_id, pharmacy_name, address, area, city, state,
                       pincode, phone, email, owner_name, rating, is_open_24h,
                       latitude, longitude)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    int(row["pharmacy_id"]), row["pharmacy_name"],
                    row.get("address",""), row.get("area",""),
                    row.get("city","Bangalore"), row.get("state","Karnataka"),
                    row.get("pincode",""), row.get("phone",""),
                    row.get("email",""), row.get("owner_name",""),
                    float(row.get("rating",4.0)),
                    int(row.get("is_open_24h",0)),
                    float(row["latitude"]), float(row["longitude"]),
                ))
            conn.commit(); conn.close()
        print(f"  [✓] Pharmacies seeded")

    if os.path.exists(inventory_csv):
        with open(inventory_csv, newline="", encoding="utf-8") as f:
            conn = get_connection()
            for row in csv.DictReader(f):
                ph = get_pharmacy_by_id(int(row["pharmacy_id"]))
                if not ph: continue
                conn.execute("""
                    INSERT OR IGNORE INTO inventory
                      (medicine_name, pharmacy_id, pharmacy_name, batch_number,
                       quantity, unit_price, mrp, expiry_date, manufacture_date,
                       latitude, longitude)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    row["medicine_name"], int(row["pharmacy_id"]),
                    ph["pharmacy_name"], row.get("batch_number",""),
                    int(row["quantity"]),
                    float(row.get("unit_price", row.get("price",0))),
                    float(row.get("mrp", row.get("price",0))),
                    row["expiry_date"], row.get("manufacture_date",""),
                    ph["latitude"], ph["longitude"],
                ))
            conn.commit(); conn.close()
        print(f"  [✓] Inventory seeded")
    print("[DB] Seeding complete.")
