"""
auth.py — Authentication Blueprint for SmartRx
Add to app.py:
    from auth import auth_bp
    app.register_blueprint(auth_bp)
"""
import sqlite3, hashlib, os, re
from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pharmacy.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def hashpw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

# ── REGISTER ────────────────────────────────────────────────
@auth_bp.route('/api/v1/register', methods=['POST'])
def register():
    data = request.get_json() or {}

    full_name = (data.get('full_name') or '').strip()
    email     = (data.get('email')     or '').strip().lower()
    username  = (data.get('username')  or '').strip().lower()
    password  = (data.get('password')  or '').strip()
    age       = data.get('age')
    gender    = (data.get('gender')    or '').strip()
    phone     = (data.get('phone')     or '').strip()
    city      = (data.get('city')      or '').strip()

    # Validation
    errors = []
    if not full_name:               errors.append('Full name is required')
    if not email:                   errors.append('Email is required')
    elif not is_valid_email(email): errors.append('Invalid email format')
    if not username:                errors.append('Username is required')
    elif len(username) < 3:         errors.append('Username must be at least 3 characters')
    elif not re.match(r'^[a-z0-9_]+$', username): errors.append('Username: only letters, numbers, underscore')
    if not password:                errors.append('Password is required')
    elif len(password) < 6:         errors.append('Password must be at least 6 characters')
    if age is None:                 errors.append('Age is required')
    else:
        try:
            age = int(age)
            if age < 1 or age > 120: errors.append('Please enter a valid age')
        except:
            errors.append('Age must be a number')

    if errors:
        return jsonify({'success': False, 'error': errors[0]}), 400

    conn = get_db()
    try:
        # Check duplicates
        existing_email = conn.execute(
            "SELECT 1 FROM users WHERE email=?", (email,)
        ).fetchone()
        if existing_email:
            return jsonify({'success': False, 'error': 'Email already registered'}), 400

        existing_user = conn.execute(
            "SELECT 1 FROM users WHERE username=?", (username,)
        ).fetchone()
        if existing_user:
            return jsonify({'success': False, 'error': 'Username already taken'}), 400

        # Insert user
        conn.execute("""
            INSERT INTO users (full_name, email, username, password_hash, age, gender, phone, city, role)
            VALUES (?,?,?,?,?,?,?,?,'user')
        """, (full_name, email, username, hashpw(password), age, gender, phone, city))
        conn.commit()

        # Return user info (no password)
        user = conn.execute(
            "SELECT user_id, full_name, email, username, age, city, role, created_at FROM users WHERE username=?",
            (username,)
        ).fetchone()

        return jsonify({
            'success': True,
            'message': f'Welcome to SmartRx, {full_name}!',
            'data': dict(user)
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

# ── LOGIN ─────────────────────────────────────────────────────
@auth_bp.route('/api/v1/login', methods=['POST'])
def login():
    data     = request.get_json() or {}
    username = (data.get('username') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=? AND is_active=1",
            (username, hashpw(password))
        ).fetchone()

        if not user:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

        return jsonify({
            'success': True,
            'message': f'Welcome back, {user["full_name"]}!',
            'data': {
                'user_id':   user['user_id'],
                'full_name': user['full_name'],
                'username':  user['username'],
                'email':     user['email'],
                'age':       user['age'],
                'city':      user['city'],
                'role':      user['role'],
            }
        })
    finally:
        conn.close()

# ── AGE CHECK for medicines ───────────────────────────────────
@auth_bp.route('/api/v1/age_check', methods=['POST'])
def age_check():
    data         = request.get_json() or {}
    user_age     = int(data.get('age', 0))
    medicine_name = data.get('medicine_name', '')

    conn = get_db()
    try:
        med = conn.execute(
            "SELECT medicine_name, age_restriction, requires_rx, category FROM medicines WHERE medicine_name=?",
            (medicine_name,)
        ).fetchone()

        if not med:
            return jsonify({'allowed': True, 'message': ''})

        restriction = med['age_restriction'] or 0
        if restriction == 0:
            return jsonify({'allowed': True, 'message': ''})

        if user_age < restriction:
            return jsonify({
                'allowed': False,
                'message': f'This medicine requires age {restriction}+. You are {user_age}.',
                'restriction': restriction,
                'requires_rx': bool(med['requires_rx'])
            })

        return jsonify({
            'allowed': True,
            'message': med['requires_rx'] and 'Prescription required' or '',
            'requires_rx': bool(med['requires_rx'])
        })
    finally:
        conn.close()

# ── GET USER PROFILE ──────────────────────────────────────────
@auth_bp.route('/api/v1/user/<username>', methods=['GET'])
def get_user(username):
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT user_id, full_name, email, username, age, gender, phone, city, role, created_at FROM users WHERE username=?",
            (username,)
        ).fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        return jsonify({'success': True, 'data': dict(user)})
    finally:
        conn.close()
