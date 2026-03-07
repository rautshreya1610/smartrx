# ============================================================
# predict_expiry.py  — Flask Blueprint
# Save this file in your project folder (same level as app.py)
# Then register it in app.py (instructions at bottom)
# ============================================================

from flask import Blueprint, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import math

predict_bp = Blueprint('predict', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pharmacy.db")

# ── ExpiryPredictor Class ────────────────────────────────────
class ExpiryPredictor:
    """
    Predicts expiry risk for each inventory item.

    Algorithm:
    1. Calculate days until expiry
    2. Estimate expected sales based on quantity and days
    3. Calculate possible waste (unsold stock before expiry)
    4. Assign risk level and suggest action
    """

    # Average daily sales rate per medicine category (units/day)
    # Based on Indian pharmacy statistics
    CATEGORY_SALES_RATE = {
        'Painkiller':       3.5,
        'Antibiotic':       2.0,
        'Diabetes':         1.5,
        'Blood Pressure':   1.2,
        'Cholesterol':      0.8,
        'Respiratory':      1.8,
        'Antacid':          2.5,
        'Antihistamine':    1.5,
        'Supplement':       0.6,
        'Antifungal':       0.9,
        'Antidepressant':   0.5,
        'Thyroid':          0.7,
        'Anti-nausea':      1.2,
        'Blood Thinner':    0.6,
        'Neuropathic Pain': 0.8,
        'Anti-inflammatory':2.2,
        'General':          1.5,
    }

    def predict(self, items):
        """Run prediction on all inventory items."""
        results = []
        today = datetime.today().date()

        for item in items:
            try:
                expiry = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
            except:
                continue

            days_left   = (expiry - today).days
            quantity    = int(item['quantity'] or 0)
            category    = item.get('category') or 'General'
            daily_rate  = self.CATEGORY_SALES_RATE.get(category, 1.5)

            # Expected sales before expiry
            if days_left > 0:
                expected_sales = min(quantity, round(daily_rate * days_left))
            else:
                expected_sales = 0

            # Waste = stock that won't sell before expiry
            possible_waste = max(0, quantity - expected_sales)

            # Financial loss estimate
            mrp = float(item.get('mrp') or 0)
            loss_estimate = round(possible_waste * mrp, 2)

            # Risk score (0-100)
            if days_left <= 0:
                risk_score = 100
                risk_level = 'CRITICAL'
                action     = 'DISCARD'
            elif days_left <= 7:
                waste_ratio = possible_waste / quantity if quantity else 0
                risk_score  = min(99, int(60 + waste_ratio * 39))
                risk_level  = 'HIGH'
                action      = 'URGENT_DISCOUNT'
            elif days_left <= 30:
                waste_ratio = possible_waste / quantity if quantity else 0
                risk_score  = min(59, int(30 + waste_ratio * 29))
                risk_level  = 'MEDIUM' if possible_waste > 0 else 'LOW'
                action      = 'DISCOUNT' if possible_waste > 0 else 'MONITOR'
            elif days_left <= 90:
                risk_score = max(5, int((90 - days_left) / 90 * 30))
                risk_level = 'LOW'
                action     = 'MONITOR'
            else:
                risk_score = 0
                risk_level = 'SAFE'
                action     = 'NO_ACTION'

            results.append({
                'inventory_id':   item['inventory_id'],
                'medicine_name':  item['medicine_name'],
                'pharmacy_id':    item['pharmacy_id'],
                'pharmacy_name':  item['pharmacy_name'],
                'category':       category,
                'quantity':       quantity,
                'mrp':            mrp,
                'expiry_date':    item['expiry_date'],
                'days_left':      days_left,
                'daily_sales_rate': daily_rate,
                'expected_sales': expected_sales,
                'possible_waste': possible_waste,
                'loss_estimate':  loss_estimate,
                'risk_score':     risk_score,
                'risk_level':     risk_level,
                'action':         action,
                'batch_number':   item.get('batch_number') or '—',
            })

        # Sort by risk score descending (most critical first)
        results.sort(key=lambda x: x['risk_score'], reverse=True)
        return results


# ── Flask Endpoint ───────────────────────────────────────────
@predict_bp.route('/api/v1/predict_expiry', methods=['GET'])
def predict_expiry():
    """
    GET /api/v1/predict_expiry
    Returns expiry risk predictions for all inventory items.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                inv.inventory_id,
                inv.medicine_name,
                inv.pharmacy_id,
                ph.pharmacy_name,
                inv.quantity,
                inv.mrp,
                inv.unit_price,
                inv.expiry_date,
                inv.batch_number,
                m.category
            FROM inventory inv
            JOIN pharmacies ph ON inv.pharmacy_id = ph.pharmacy_id
            LEFT JOIN medicines m ON LOWER(inv.medicine_name) = LOWER(m.medicine_name)
            WHERE inv.quantity > 0
            ORDER BY inv.expiry_date ASC
        """).fetchall()
        conn.close()

        items = [dict(r) for r in rows]
        predictor = ExpiryPredictor()
        predictions = predictor.predict(items)

        # Summary stats
        total   = len(predictions)
        critical= sum(1 for p in predictions if p['risk_level'] == 'CRITICAL')
        high    = sum(1 for p in predictions if p['risk_level'] == 'HIGH')
        medium  = sum(1 for p in predictions if p['risk_level'] == 'MEDIUM')
        low     = sum(1 for p in predictions if p['risk_level'] == 'LOW')
        safe    = sum(1 for p in predictions if p['risk_level'] == 'SAFE')
        total_loss = round(sum(p['loss_estimate'] for p in predictions), 2)
        total_waste= sum(p['possible_waste'] for p in predictions)

        return jsonify({
            'success': True,
            'data': {
                'predictions': predictions,
                'summary': {
                    'total':        total,
                    'critical':     critical,
                    'high':         high,
                    'medium':       medium,
                    'low':          low,
                    'safe':         safe,
                    'total_waste':  total_waste,
                    'total_loss':   total_loss,
                }
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# HOW TO REGISTER IN app.py:
# Add these 2 lines in your app.py (after creating the Flask app):
#
#   from predict_expiry import predict_bp
#   app.register_blueprint(predict_bp)
#
# ============================================================
