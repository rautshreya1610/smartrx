"""
setup_users.py
Adds users table to pharmacy.db and seeds default admin + demo users.
Run ONCE: python setup_users.py
"""
import sqlite3, hashlib, os
from datetime import datetime

DB = 'pharmacy.db'
if not os.path.exists(DB):
    print("ERROR: pharmacy.db not found! Run from project folder.")
    exit()

conn = sqlite3.connect(DB)

# ── Create users table ───────────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    age           INTEGER NOT NULL,
    gender        TEXT,
    phone         TEXT,
    city          TEXT,
    role          TEXT    NOT NULL DEFAULT 'user',
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✅ users table created")

# ── Add age_restriction column to medicines if not exists ────
cols = [c[1] for c in conn.execute("PRAGMA table_info(medicines)").fetchall()]
if 'age_restriction' not in cols:
    conn.execute("ALTER TABLE medicines ADD COLUMN age_restriction INTEGER DEFAULT 0")
    print("✅ age_restriction column added to medicines")

    # Set age restrictions for specific categories
    # 18+ for: Antidepressant, Blood Thinner, Neuropathic Pain, controlled substances
    conn.execute("""
        UPDATE medicines SET age_restriction = 18
        WHERE category IN ('Antidepressant','Blood Thinner','Neuropathic Pain')
        OR requires_rx = 1
    """)
    # 12+ for: some Rx medicines
    conn.execute("""
        UPDATE medicines SET age_restriction = 12
        WHERE age_restriction = 0
        AND category IN ('Antibiotic','Antifungal','Respiratory')
    """)
    affected = conn.execute("SELECT COUNT(1) FROM medicines WHERE age_restriction > 0").fetchone()[0]
    print(f"✅ Age restrictions set on {affected} medicines")
else:
    print("ℹ age_restriction column already exists")

# ── Hash function ────────────────────────────────────────────
def hashpw(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── Seed default users ───────────────────────────────────────
seed_users = [
    # (full_name, email, username, password, age, gender, phone, city, role)
    ("Admin SmartRx",  "admin@smartrx.com",  "admin", "admin@smartrx", 30, "M", "9000000001", "Pune",      "admin"),
    ("Demo User",      "user@smartrx.com",   "user",  "user123",       25, "F", "9000000002", "Pune",      "user"),
    ("Rahul Sharma",   "rahul@example.com",  "rahul", "rahul123",      17, "M", "9000000003", "Bangalore", "user"),
    ("Priya Patil",    "priya@example.com",  "priya", "priya123",      22, "F", "9000000004", "Pune",      "user"),
]

inserted = 0
for u in seed_users:
    try:
        conn.execute("""
            INSERT OR IGNORE INTO users
            (full_name, email, username, password_hash, age, gender, phone, city, role)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (u[0], u[1], u[2], hashpw(u[3]), u[4], u[5], u[6], u[7], u[8]))
        inserted += 1
    except Exception as e:
        print(f"  skip {u[2]}: {e}")

conn.commit()

# ── Show results ─────────────────────────────────────────────
users = conn.execute("SELECT user_id, username, role, age, city FROM users").fetchall()
print(f"\n✅ {inserted} users seeded. All users in DB:")
print(f"  {'ID':<4} {'Username':<12} {'Role':<8} {'Age':<5} {'City'}")
print("  " + "-"*45)
for u in users:
    print(f"  {u[0]:<4} {u[1]:<12} {u[2]:<8} {u[3]:<5} {u[4]}")

meds_restricted = conn.execute("SELECT COUNT(1) FROM medicines WHERE age_restriction > 0").fetchone()[0]
print(f"\n✅ Medicines with age restriction: {meds_restricted}")
print(f"\n{'='*50}")
print("NOW: Update app.py with the new /register and /login endpoints")
print("(see instructions below)")
print(f"{'='*50}")

conn.close()
