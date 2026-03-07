import os, sys, time, logging
from flask import Flask, jsonify, send_from_directory

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from settings import SECRET_KEY, DEBUG, PORT, DATASET_DIR
import database as db
import ds_manager as ds

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("pharmacy")

FRONTEND_DIR = ROOT_DIR   # index.html is in the same folder

_start_time = time.time()


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False

    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"]  = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.before_request
    def handle_options():
        from flask import request
        if request.method == "OPTIONS":
            return "", 204

    # Import and register blueprints
    import medicines     as med_mod
    import pharmacies    as ph_mod
    import inventory     as inv_mod
    import alerts        as alt_mod
    import auth          as auth_mod
    import predict_expiry as exp_mod

    app.register_blueprint(med_mod.bp)
    app.register_blueprint(ph_mod.bp)
    app.register_blueprint(inv_mod.bp)
    app.register_blueprint(alt_mod.bp)
    app.register_blueprint(auth_mod.auth_bp)
    app.register_blueprint(exp_mod.predict_bp)

    @app.route("/api/v1/health")
    def health():
        return jsonify({"status": "ok", "version": "2.0.0",
                        "uptime": round(time.time() - _start_time, 1)})

    @app.route("/api/v1")
    def api_root():
        return jsonify({"api_version": "v1", "message": "Smart Pharmacy API running!"})

    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/expiry_dashboard")
    def expiry_dashboard():
        return send_from_directory(FRONTEND_DIR, "expiry_dashboard.html")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Not found."}), 404

    @app.errorhandler(500)
    def internal(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app


def bootstrap():
    log.info("Smart Pharmacy System v2 — Starting up...")
    db.init_database()

    # Create users table if not exists
    import sqlite3, hashlib
    conn = sqlite3.connect(os.path.join(ROOT_DIR, "pharmacy.db"))
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
    # Seed default admin if not exists
    def hashpw(p): return hashlib.sha256(p.encode()).hexdigest()
    conn.execute("INSERT OR IGNORE INTO users (full_name,email,username,password_hash,age,gender,city,role) VALUES (?,?,?,?,?,?,?,?)",
        ("Admin SmartRx","admin@smartrx.com","admin",hashpw("admin@smartrx"),30,"M","Pune","admin"))
    conn.execute("INSERT OR IGNORE INTO users (full_name,email,username,password_hash,age,gender,city,role) VALUES (?,?,?,?,?,?,?,?)",
        ("Demo User","user@smartrx.com","user",hashpw("user123"),25,"F","Pune","user"))
    conn.commit()
    conn.close()
    log.info("Users table ready ✓")

    import sqlite3
    conn = sqlite3.connect(os.path.join(ROOT_DIR, "pharmacy.db"))
    count = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
    conn.close()

    if count == 0:
        db.seed_from_csv(
            os.path.join(ROOT_DIR, "medicines.csv"),
            os.path.join(ROOT_DIR, "pharmacies.csv"),
            os.path.join(ROOT_DIR, "inventory.csv"),
        )

    medicines  = db.get_all_medicines()
    pharmacies = db.get_all_pharmacies()
    inventory  = db.get_all_inventory()
    ds.build_all(medicines, pharmacies, inventory)

    stats = db.get_dashboard_stats()
    log.info(f"Medicines: {stats['total_medicines']} | Pharmacies: {stats['total_pharmacies']} | Inventory: {stats['total_inventory']}")
    log.info(f"Server ready → http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    bootstrap()
    app = create_app()
    app.run(debug=DEBUG, port=PORT, use_reloader=False)