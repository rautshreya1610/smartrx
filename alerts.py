"""
backend/routes/alerts.py
=========================
/api/v1/alerts  — Min-Heap expiry queries
/api/v1/dashboard — system stats
"""

from flask import Blueprint, request
import sys, os
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import database as db
import ds_manager as ds
from helpers import ok, bad_request

bp = Blueprint("alerts", __name__)


@bp.route("/api/v1/alerts", methods=["GET"])
def expiry_alerts():
    """
    GET /api/v1/alerts
    Query: days (default 7), pharmacy_id, level (EXPIRED|CRITICAL|WARNING)
    Returns medicines expiring within `days` days, sorted soonest first.
    """
    days        = request.args.get("days",        7,    type=int)
    pharmacy_id = request.args.get("pharmacy_id",       type=int)
    level_filter= request.args.get("level",       "").strip().upper()

    if days < 0:
        return bad_request("'days' must be >= 0.")

    pq     = ds.get_pq()
    alerts = pq.get_expiring_within_days(days)

    if pharmacy_id is not None:
        alerts = [a for a in alerts if a.get("pharmacy_id") == pharmacy_id]

    if level_filter in ("EXPIRED", "CRITICAL", "WARNING", "NOTICE"):
        alerts = [a for a in alerts if a.get("alert_level") == level_filter]

    summary = pq.get_alert_summary()

    return ok({
        "alerts":            alerts,
        "count":             len(alerts),
        "alert_window_days": days,
        "summary":           summary,
    })


@bp.route("/api/v1/alerts/expired", methods=["GET"])
def expired():
    """GET /api/v1/alerts/expired — already-expired medicines."""
    pq = ds.get_pq()
    expired_list = pq.get_expired()
    return ok({"alerts": expired_list, "count": len(expired_list)})


@bp.route("/api/v1/alerts/summary", methods=["GET"])
def alert_summary():
    """GET /api/v1/alerts/summary — counts by severity."""
    pq = ds.get_pq()
    return ok(pq.get_alert_summary())


@bp.route("/api/v1/dashboard", methods=["GET"])
def dashboard():
    """
    GET /api/v1/dashboard
    Aggregated stats from DB + all in-memory data structures.
    """
    db_stats = db.get_dashboard_stats()

    trie    = ds.get_trie()
    index   = ds.get_index()
    pq      = ds.get_pq()
    loc     = ds.get_location()

    pq_summary = pq.get_alert_summary()

    return ok({
        # Database counters
        **db_stats,
        # In-memory DS sizes
        "ds": {
            "trie_medicines":     trie.total_medicines   if trie  else 0,
            "bptree_records":     index.record_count     if index else 0,
            "heap_active":        pq.active_count        if pq    else 0,
            "quadtree_pharmacies":loc.count              if loc   else 0,
        },
        # Expiry breakdown
        "expiry_summary": pq_summary,
    })
