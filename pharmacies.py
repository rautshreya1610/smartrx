"""
backend/routes/pharmacies.py
=============================
/api/v1/pharmacies — CRUD + nearby search
"""

from flask import Blueprint, request
import sys, os
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import database as db
import ds_manager as ds
from helpers import (
    ok, created, bad_request, not_found,
    validate_required, validate_float, get_page_params, paginate
)

bp = Blueprint("pharmacies", __name__, url_prefix="/api/v1/pharmacies")


@bp.route("", methods=["GET"])
def list_pharmacies():
    """GET /api/v1/pharmacies — all pharmacies (optionally near a point)."""
    lat    = request.args.get("lat",    type=float)
    lon    = request.args.get("lon",    type=float)
    radius = request.args.get("radius", 10.0, type=float)

    if lat is not None and lon is not None:
        loc  = ds.get_location()
        data = loc.find_nearby_pharmacies(lat, lon, radius)
        return ok({"pharmacies": data, "count": len(data), "radius_km": radius})

    pharmacies = db.get_all_pharmacies()
    return ok({"pharmacies": pharmacies, "count": len(pharmacies)})


@bp.route("/<int:pharmacy_id>", methods=["GET"])
def get_pharmacy(pharmacy_id):
    """GET /api/v1/pharmacies/<id>"""
    ph = db.get_pharmacy_by_id(pharmacy_id)
    if not ph:
        return not_found("Pharmacy")
    return ok(ph)


@bp.route("", methods=["POST"])
def create_pharmacy():
    """
    POST /api/v1/pharmacies
    Body: { pharmacy_name, latitude, longitude, address, ... }
    """
    data = request.get_json(silent=True) or {}
    err  = validate_required(data, ["pharmacy_name", "latitude", "longitude"])
    if err:
        return bad_request(err)

    for f in ["latitude", "longitude"]:
        e = validate_float(data[f], f)
        if e: return bad_request(e)

    result = db.add_pharmacy(data)
    if result["success"]:
        ds.on_pharmacy_add(result["pharmacy"])
        return created(result["pharmacy"], "Pharmacy added.")
    return bad_request(result.get("error", "Failed."))


@bp.route("/<int:pharmacy_id>", methods=["PUT"])
def update_pharmacy(pharmacy_id):
    """PUT /api/v1/pharmacies/<id>"""
    data = request.get_json(silent=True) or {}
    if not db.get_pharmacy_by_id(pharmacy_id):
        return not_found("Pharmacy")
    result = db.update_pharmacy(pharmacy_id, data)
    return ok(result["pharmacy"], "Pharmacy updated.")


@bp.route("/<int:pharmacy_id>", methods=["DELETE"])
def delete_pharmacy(pharmacy_id):
    """DELETE /api/v1/pharmacies/<id>"""
    result = db.delete_pharmacy(pharmacy_id)
    if not result["success"]:
        return not_found("Pharmacy")
    return ok(message="Pharmacy deleted.")


@bp.route("/<int:pharmacy_id>/inventory", methods=["GET"])
def pharmacy_inventory(pharmacy_id):
    """GET /api/v1/pharmacies/<id>/inventory?page=1&size=50"""
    ph = db.get_pharmacy_by_id(pharmacy_id)
    if not ph:
        return not_found("Pharmacy")

    page, size = get_page_params(request)

    # Use B+ Tree for the lookup
    index   = ds.get_index()
    records = index.get_by_pharmacy(pharmacy_id)

    # Enrich with expiry status
    from helpers import expiry_status
    for r in records:
        r["expiry_status"] = expiry_status(r["expiry_date"])

    result = paginate(records, page, size)
    result["pharmacy"] = ph
    return ok(result)


@bp.route("/<int:pharmacy_id>/alerts", methods=["GET"])
def pharmacy_alerts(pharmacy_id):
    """GET /api/v1/pharmacies/<id>/alerts?days=7"""
    ph = db.get_pharmacy_by_id(pharmacy_id)
    if not ph:
        return not_found("Pharmacy")

    days   = request.args.get("days", 7, type=int)
    pq     = ds.get_pq()
    alerts = [a for a in pq.get_expiring_within_days(days) if a.get("pharmacy_id") == pharmacy_id]
    return ok({"pharmacy": ph, "alerts": alerts, "count": len(alerts)})
