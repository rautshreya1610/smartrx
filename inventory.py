"""
backend/routes/inventory.py
============================
/api/v1/inventory — CRUD for inventory records
"""

from flask import Blueprint, request
import sys, os
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import database as db
import ds_manager as ds
from helpers import (
    ok, created, bad_request, not_found,
    validate_required, validate_date, validate_positive_int, validate_float,
    expiry_status, get_page_params, paginate
)

bp = Blueprint("inventory", __name__, url_prefix="/api/v1/inventory")


@bp.route("", methods=["GET"])
def list_inventory():
    """
    GET /api/v1/inventory
    Query: medicine_name, pharmacy_id, expiring_days, low_stock, page, size
    """
    page, size    = get_page_params(request)
    medicine_name = request.args.get("medicine_name", "").strip()
    pharmacy_id   = request.args.get("pharmacy_id",   type=int)
    exp_days      = request.args.get("expiring_days", type=int)
    low_stock     = request.args.get("low_stock",     type=int)   # threshold

    # B+ Tree lookups
    index = ds.get_index()

    if medicine_name:
        records = index.get_by_medicine(medicine_name)
    elif pharmacy_id:
        records = index.get_by_pharmacy(pharmacy_id)
    elif exp_days is not None:
        records = db.get_expiring_soon(exp_days)
    elif low_stock is not None:
        records = index.get_low_stock(threshold=low_stock)
    else:
        records = index.get_all_records()

    # Enrich with expiry status
    for r in records:
        r["expiry_status"] = expiry_status(r["expiry_date"])

    result = paginate(records, page, size)
    return ok(result)


@bp.route("/<int:inventory_id>", methods=["GET"])
def get_record(inventory_id):
    """GET /api/v1/inventory/<id>"""
    rec = db.get_inventory_by_id(inventory_id)
    if not rec:
        return not_found("Inventory record")
    rec["expiry_status"] = expiry_status(rec["expiry_date"])
    return ok(rec)


@bp.route("", methods=["POST"])
def create_record():
    """
    POST /api/v1/inventory
    Body: { medicine_name, pharmacy_id, quantity, expiry_date, unit_price, mrp, batch_number }
    """
    data = request.get_json(silent=True) or {}

    err = validate_required(data, ["medicine_name", "pharmacy_id", "quantity", "expiry_date"])
    if err: return bad_request(err)

    err = validate_positive_int(data["quantity"], "quantity")
    if err: return bad_request(err)

    if not validate_date(data["expiry_date"]):
        return bad_request("Invalid expiry_date. Use YYYY-MM-DD format.")

    result = db.add_inventory_record(data)
    if not result["success"]:
        return bad_request(result["error"])

    rec = result["record"]
    rec["expiry_status"] = expiry_status(rec["expiry_date"])

    ds.on_inventory_add(rec)

    # Auto-add medicine to Trie if it's new
    trie = ds.get_trie()
    if not trie.exact_search(data["medicine_name"]):
        db.add_medicine({"medicine_name": data["medicine_name"],
                         "category": data.get("category", "General")})
        ds.on_medicine_add({"medicine_name": data["medicine_name"],
                             "category": data.get("category", "General")})

    return created(rec, "Inventory record added.")


@bp.route("/<int:inventory_id>", methods=["PUT"])
def update_record(inventory_id):
    """PUT /api/v1/inventory/<id>"""
    data = request.get_json(silent=True) or {}

    existing = db.get_inventory_by_id(inventory_id)
    if not existing:
        return not_found("Inventory record")

    err = validate_required(data, ["quantity", "expiry_date"])
    if err: return bad_request(err)

    if not validate_date(data["expiry_date"]):
        return bad_request("Invalid expiry_date.")

    result = db.update_inventory_record(inventory_id, data)
    if not result["success"]:
        return bad_request("Update failed.")

    rec = result["record"]
    rec["expiry_status"] = expiry_status(rec["expiry_date"])
    ds.on_inventory_update(rec)
    return ok(rec, "Inventory updated.")


@bp.route("/<int:inventory_id>", methods=["DELETE"])
def delete_record(inventory_id):
    """DELETE /api/v1/inventory/<id>"""
    result = db.delete_inventory_record(inventory_id)
    if not result["success"]:
        return not_found("Inventory record")

    deleted = result["deleted"]
    ds.on_inventory_delete(deleted["medicine_name"], deleted["pharmacy_id"])
    return ok(message="Record deleted.")


@bp.route("/low-stock", methods=["GET"])
def low_stock():
    """GET /api/v1/inventory/low-stock?threshold=10"""
    threshold = request.args.get("threshold", 10, type=int)
    records   = ds.get_index().get_low_stock(threshold=threshold)
    for r in records:
        r["expiry_status"] = expiry_status(r["expiry_date"])
    return ok({"records": records, "count": len(records), "threshold": threshold})
