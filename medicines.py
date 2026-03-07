"""
backend/routes/medicines.py
============================
/api/v1/medicines  — full CRUD + autocomplete
"""

from flask import Blueprint, request
import sys, os
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import database as db
import ds_manager as ds
from helpers import (
    ok, created, bad_request, not_found, conflict,
    validate_required, get_page_params, paginate
)

bp = Blueprint("medicines", __name__, url_prefix="/api/v1/medicines")


@bp.route("", methods=["GET"])
def list_medicines():
    """
    GET /api/v1/medicines
    Query params: page, size, category, q (name search)
    Returns paginated medicine list.
    """
    page, size = get_page_params(request)
    category   = request.args.get("category", "").strip()
    q          = request.args.get("q", "").strip()

    medicines = db.get_all_medicines(page=1, size=9999)

    if category:
        medicines = [m for m in medicines if m.get("category","").lower() == category.lower()]
    if q:
        medicines = [m for m in medicines if q.lower() in m["medicine_name"].lower()]

    result = paginate(medicines, page, size)
    return ok(result)


@bp.route("/autocomplete", methods=["GET"])
def autocomplete():
    """
    GET /api/v1/medicines/autocomplete?q=para&limit=10
    Trie-powered prefix autocomplete.
    """
    q     = request.args.get("q", "").strip()
    limit = min(20, max(1, request.args.get("limit", 10, type=int)))

    if not q:
        return ok([])

    trie    = ds.get_trie()
    results = trie.search_prefix(q, max_results=limit)
    return ok(results)


@bp.route("/search", methods=["GET"])
def search():
    """
    GET /api/v1/medicines/search?q=para&lat=12.97&lon=77.59&radius=10&category=Painkiller
    Full pipeline: Trie → B+Tree → QuadTree.
    """
    q      = request.args.get("q", "").strip()
    lat    = request.args.get("lat",    type=float)
    lon    = request.args.get("lon",    type=float)
    radius = request.args.get("radius", 10.0, type=float)
    cat    = request.args.get("category", "").strip()

    if not q:
        return bad_request("Query parameter 'q' is required.")

    trie  = ds.get_trie()
    index = ds.get_index()
    loc   = ds.get_location()

    # Step 1: Trie prefix search
    suggestions = trie.search_prefix(q, max_results=10)
    if cat:
        suggestions = [s for s in suggestions if s.get("category","").lower() == cat.lower()]

    if not suggestions:
        return ok({"query": q, "results": [], "total": 0})

    # Step 2: Nearby pharmacies via QuadTree
    nearby_map = {}
    if lat is not None and lon is not None:
        nearby = loc.find_nearby_pharmacies(lat, lon, radius)
        nearby_map = {p["pharmacy_id"]: p for p in nearby}

    # Step 3: B+Tree inventory lookup per medicine
    results = []
    for sug in suggestions:
        name = sug["name"]
        records = index.get_by_medicine(name)
        pharmacy_list = []

        for rec in records:
            pid = rec["pharmacy_id"]
            if nearby_map and pid not in nearby_map:
                continue  # outside radius

            entry = {
                "pharmacy_id":   pid,
                "pharmacy_name": rec["pharmacy_name"],
                "quantity":      rec["quantity"],
                "unit_price":    rec.get("unit_price", rec.get("price", 0)),
                "mrp":           rec.get("mrp", 0),
                "expiry_date":   rec["expiry_date"],
                "batch_number":  rec.get("batch_number", ""),
                "latitude":      rec["latitude"],
                "longitude":     rec["longitude"],
            }
            if nearby_map and pid in nearby_map:
                np = nearby_map[pid]
                entry["distance_km"]  = np["distance_km"]
                entry["distance_str"] = np["distance_str"]
                entry["address"]      = np.get("address", "")
                entry["phone"]        = np.get("phone", "")

            # Enrich expiry status
            from helpers import expiry_status
            entry["expiry_status"] = expiry_status(rec["expiry_date"])
            pharmacy_list.append(entry)

        if nearby_map:
            pharmacy_list.sort(key=lambda x: x.get("distance_km", 9999))

        results.append({
            "medicine_name": name,
            "category":      sug.get("category", "General"),
            "description":   sug.get("description", ""),
            "dosage_form":   sug.get("dosage_form", ""),
            "requires_rx":   sug.get("requires_rx", 0),
            "pharmacies":    pharmacy_list,
            "in_stock_count": len(pharmacy_list),
        })

    return ok({"query": q, "results": results, "total": len(results)})


@bp.route("/categories", methods=["GET"])
def categories():
    """GET /api/v1/medicines/categories — all medicine categories with counts."""
    cats = db.get_medicine_categories()
    return ok(cats)


@bp.route("/<int:medicine_id>", methods=["GET"])
def get_medicine(medicine_id):
    """GET /api/v1/medicines/<id>"""
    med = db.get_medicine_by_id(medicine_id)
    if not med:
        return not_found("Medicine")
    return ok(med)


@bp.route("", methods=["POST"])
def create_medicine():
    """
    POST /api/v1/medicines
    Body: { medicine_name, category, description, ... }
    """
    data = request.get_json(silent=True) or {}
    err  = validate_required(data, ["medicine_name"])
    if err:
        return bad_request(err)

    result = db.add_medicine(data)
    if not result["success"]:
        return conflict(result["error"])

    ds.on_medicine_add(result["medicine"])
    return created(result["medicine"], "Medicine added.")


@bp.route("/<int:medicine_id>", methods=["PUT"])
def update_medicine(medicine_id):
    """PUT /api/v1/medicines/<id>"""
    data = request.get_json(silent=True) or {}
    if not db.get_medicine_by_id(medicine_id):
        return not_found("Medicine")

    result = db.update_medicine(medicine_id, data)
    return ok(result["medicine"], "Medicine updated.")


@bp.route("/<int:medicine_id>", methods=["DELETE"])
def delete_medicine(medicine_id):
    """DELETE /api/v1/medicines/<id>"""
    result = db.delete_medicine(medicine_id)
    if not result["success"]:
        return not_found("Medicine")
    return ok(message="Medicine deleted.")
