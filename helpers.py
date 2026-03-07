"""
backend/utils/helpers.py
=========================
Shared utilities: response formatters, input validators, pagination.
"""

from datetime import date, datetime
from flask import jsonify


# ── Standard JSON responses ──────────────────────────────────────────────────

def ok(data=None, message: str = "OK", **kwargs):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    payload.update(kwargs)
    return jsonify(payload), 200

def created(data=None, message: str = "Created"):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), 201

def bad_request(error: str):
    return jsonify({"success": False, "error": error}), 400

def not_found(resource: str = "Resource"):
    return jsonify({"success": False, "error": f"{resource} not found."}), 404

def server_error(error: str = "Internal server error"):
    return jsonify({"success": False, "error": error}), 500

def conflict(error: str):
    return jsonify({"success": False, "error": error}), 409


# ── Pagination ───────────────────────────────────────────────────────────────

def paginate(items: list, page: int, size: int) -> dict:
    total = len(items)
    start = (page - 1) * size
    end   = start + size
    return {
        "items": items[start:end],
        "pagination": {
            "page":       page,
            "size":       size,
            "total":      total,
            "pages":      (total + size - 1) // size,
            "has_next":   end < total,
            "has_prev":   page > 1,
        }
    }


# ── Validators ───────────────────────────────────────────────────────────────

def validate_required(data: dict, fields: list) -> str | None:
    """Return error string if any required field is missing/empty, else None."""
    for f in fields:
        if f not in data or str(data[f]).strip() == "":
            return f"Field '{f}' is required."
    return None

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

def validate_positive_int(val, field: str = "value") -> str | None:
    try:
        n = int(val)
        if n < 0:
            return f"'{field}' must be a non-negative integer."
    except (ValueError, TypeError):
        return f"'{field}' must be an integer."
    return None

def validate_float(val, field: str = "value", min_val: float = 0) -> str | None:
    try:
        f = float(val)
        if f < min_val:
            return f"'{field}' must be >= {min_val}."
    except (ValueError, TypeError):
        return f"'{field}' must be a number."
    return None


# ── Date utilities ───────────────────────────────────────────────────────────

def days_until(date_str: str) -> int:
    try:
        exp = datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
        return (exp - date.today()).days
    except Exception:
        return 9999

def expiry_status(date_str: str) -> dict:
    d = days_until(date_str)
    if d < 0:
        level, color, label = "EXPIRED",  "#ef4444", f"Expired {abs(d)}d ago"
    elif d <= 2:
        level, color, label = "CRITICAL", "#f97316", f"Expires in {d}d"
    elif d <= 7:
        level, color, label = "WARNING",  "#eab308", f"Expires in {d}d"
    elif d <= 30:
        level, color, label = "NOTICE",   "#3b82f6", f"Expires in {d}d"
    else:
        level, color, label = "OK",       "#22c55e", f"Expires {date_str}"
    return {"level": level, "color": color, "label": label, "days": d}


# ── Query param helpers ──────────────────────────────────────────────────────

def get_page_params(request) -> tuple:
    page = max(1, request.args.get("page", 1, type=int))
    size = min(100, max(1, request.args.get("size", 20, type=int)))
    return page, size
