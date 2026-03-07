"""
backend/services/ds_manager.py
================================
Manages all in-memory data structures as singletons.
Provides a clean interface so routes don't import DS modules directly.
"""

import sys, os
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from trie               import Trie
from inventory_bplustree import InventoryBPlusTree
from expiry_priority_queue import ExpiryPriorityQueue
from location_search    import LocationSearch

# ── Singletons ──────────────────────────────────────────────────────────────
_trie:     Trie               = None
_index:    InventoryBPlusTree = None
_pq:       ExpiryPriorityQueue= None
_location: LocationSearch     = None


def build_all(medicines: list, pharmacies: list, inventory: list):
    """Rebuild every data structure from DB snapshots. Called at startup & after bulk changes."""
    global _trie, _index, _pq, _location

    # 1. Trie
    _trie = Trie()
    for m in medicines:
        _trie.insert(m["medicine_name"], {
            "name":        m["medicine_name"],
            "category":    m.get("category", "General"),
            "description": m.get("description", ""),
            "dosage_form": m.get("dosage_form", ""),
            "requires_rx": m.get("requires_rx", 0),
        })

    # 2. B+ Tree
    _index = InventoryBPlusTree()
    for rec in inventory:
        _index.insert(rec)

    # 3. Min-Heap
    _pq = ExpiryPriorityQueue()
    for rec in inventory:
        _pq.push(rec)

    # 4. QuadTree
    _location = LocationSearch()
    for ph in pharmacies:
        _location.add_pharmacy(
            pharmacy_id = ph["pharmacy_id"],
            name        = ph["pharmacy_name"],
            lat         = float(ph["latitude"]),
            lon         = float(ph["longitude"]),
            address     = ph.get("address", ""),
            phone       = ph.get("phone", ""),
        )

    print(f"[DS] Trie={_trie.total_medicines} | "
          f"BPlusTree={_index.record_count} | "
          f"Heap={_pq.active_count} | "
          f"QuadTree={_location.count}")


def get_trie()     -> Trie:               return _trie
def get_index()    -> InventoryBPlusTree: return _index
def get_pq()       -> ExpiryPriorityQueue:return _pq
def get_location() -> LocationSearch:    return _location


# ── Incremental helpers (avoid full rebuild) ─────────────────────────────────

def on_inventory_add(record: dict):
    """Update all DS after one inventory record is added."""
    _index.insert(record)
    _pq.push(record)

def on_inventory_update(record: dict):
    """Update DS after an existing inventory record is modified."""
    _index.insert(record)   # insert() is an upsert
    _pq.push(record)

def on_inventory_delete(medicine_name: str, pharmacy_id: int):
    """Remove from DS after deletion."""
    _index.delete(medicine_name, pharmacy_id)
    _pq.remove(medicine_name, pharmacy_id)

def on_medicine_add(medicine: dict):
    """Insert new medicine name into Trie."""
    _trie.insert(medicine["medicine_name"], {
        "name":        medicine["medicine_name"],
        "category":    medicine.get("category","General"),
        "description": medicine.get("description",""),
        "dosage_form": medicine.get("dosage_form",""),
        "requires_rx": medicine.get("requires_rx",0),
    })

def on_pharmacy_add(pharmacy: dict):
    """Insert new pharmacy into QuadTree."""
    _location.add_pharmacy(
        pharmacy_id = pharmacy["pharmacy_id"],
        name        = pharmacy["pharmacy_name"],
        lat         = float(pharmacy["latitude"]),
        lon         = float(pharmacy["longitude"]),
        address     = pharmacy.get("address",""),
        phone       = pharmacy.get("phone",""),
    )
