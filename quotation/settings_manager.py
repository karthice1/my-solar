"""Settings Manager: Persistent Owner Configuration and Commercial Defaults.

Supports authentication, validation, persistent JSON storage, and reset to defaults.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quotation_settings.json")
AUTH_SECRET = "rensun_solar_owner_secret_key_2026"

DEFAULT_SETTINGS: Dict[str, Any] = {
    # 1. Solar Panel Configuration
    "panel": {
        "manufacturer": "Waaree Energies Ltd",
        "model": "Bi-55-540 Wp",
        "wattage_wp": 540,
        "technology": "Mono PERC Half-Cut Cell (Bifacial)",
        "product_warranty_years": 12,
        "performance_warranty_years": 25,
        "dimensions": "2278 × 1134 × 35 mm",
        "efficiency_percent": 20.9,
        "standard_wattages": [540, 550, 580, 600]
    },
    # 2. Commercial Pricing
    "pricing": {
        "pricing_model": "bundled_per_kw",  # "bundled_per_kw" or "itemized"
        "price_per_kw": 52000.0,
        "price_per_kw_includes_gst": False,
        "gst_rate_percent": 12.0,  # Composite solar GST rate
        "subsidy_applicable": True,
        # Itemized breakdown (used if model == 'itemized', or for itemized BOQ reference)
        "itemized": {
            "panel_per_wp": 24.0,
            "inverter_per_kw": 11000.0,
            "mounting_structure_per_kw": 4500.0,
            "cables_and_wiring_per_kw": 3500.0,
            "electrical_accessories_lump": 6000.0,
            "installation_charges_per_kw": 4000.0,
            "transportation_charges_lump": 3500.0,
            "additional_charges_lump": 0.0
        }
    },
    # 3. Quotation Branding
    "branding": {
        "company_name": "RenSun Solar Energy Pvt Ltd",
        "tagline": "Empowering Tamil Nadu with High-Yield Clean Rooftop Solar",
        "logo_url": "/static/rensun_logo.svg",
        "address": "142, Cross Cut Road, Gandhipuram, Coimbatore - 641012, Tamil Nadu",
        "phone": "+91 98421 54321 / 0422 2498765",
        "email": "proposals@rensunenergy.com",
        "website": "www.rensunenergy.com",
        "gstin": "33AAACR1234F1Z8",
        "authorized_signatory": "K. R. Vasanth",
        "signatory_title": "Managing Director & Solar Solutions Architect",
        "primary_color": "#0f766e",    # Emerald teal
        "secondary_color": "#f59e0b"   # Solar amber
    },
    # 4. System Type
    "system": {
        "system_type": "on-grid",  # "on-grid", "hybrid", "off-grid"
        "battery_included": False,
        "battery": {
            "capacity_kwh": 0.0,
            "voltage": 48,
            "technology": "LiFePO4 Lithium Iron Phosphate",
            "warranty_years": 5,
            "price": 0.0
        }
    },
    # 5. Inverter Configuration
    "inverter": {
        "manufacturer": "Solis / Growatt",
        "model": "S6-GR1P-K Series Single Phase Grid-Tied",
        "type": "Single Phase MPPT On-Grid String Inverter",
        "rated_capacity_kw": 3.0,
        "warranty_years": 5,
        "quantity": 1,
        "efficiency_percent": 97.7
    },
    # 6. Warranty Configuration
    "warranty": {
        "module_product_warranty": "12 Years Comprehensive Product Workmanship Warranty",
        "module_performance_warranty": "25 Years Linear Performance Warranty (≥ 84.8% at Year 25)",
        "inverter_warranty": "5 Years Standard Replacement Warranty (Extendable to 10 Years)",
        "mounting_structure_warranty": "10 Years Structural & Rust-Proof Warranty (Hot-Dip Galvanized / Anodized Al)",
        "workmanship_warranty": "5 Years Installation Workmanship & Free Comprehensive Maintenance Service",
        "battery_warranty": "5 Years Replacement Warranty (Applicable only for Hybrid / Off-Grid battery systems)"
    },
    # 7. Additional Commercial Terms
    "commercial_terms": {
        "payment_terms": "20% Booking Advance with Work Order • 70% Upon Material Delivery at Site • 10% Upon Net-Meter Synchronization",
        "quotation_validity_days": 15,
        "delivery_period_weeks": "2 to 3 Weeks from TANGEDCO Net-Metering Feasibility Sanction",
        "terms_and_conditions": [
            "Net-metering feasibility sanction and bi-directional meter issuance are subject to TANGEDCO/TNEB rules and distribution transformer capacity.",
            "Client must provide shadow-free terrace/roof access and uninterrupted single/three-phase AC electricity connection for installation work.",
            "PM Surya Ghar subsidy will be directly credited by MNRE into consumer's Aadhaar-linked bank account post grid commissioning."
        ],
        "subsidy_disclosure": "Eligible for PM Surya Ghar: Muft Bijli Yojana Central Financial Assistance: ₹30,000 for 1kW, ₹60,000 for 2kW, ₹78,000 for 3kW and above (Domestic LT category).",
        "net_metering_disclaimer": "Net-metering approval is granted by TANGEDCO based on distribution transformer load availability (up to 100% of sanctioned load for LT domestic connections)."
    },
    # Security PIN (default)
    "admin_pin": "admin123"
}

def load_owner_settings() -> Dict[str, Any]:
    """Loads owner quotation settings from disk or returns defaults if not yet created."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # Deep merge defaults so new keys are always populated
                return _deep_merge(DEFAULT_SETTINGS, saved)
        except Exception as e:
            print(f"[SettingsManager] Error reading settings file: {e}. Using defaults.")
    return json.loads(json.dumps(DEFAULT_SETTINGS))

def save_owner_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Persistently saves owner settings to disk."""
    # Never overwrite with empty dict
    if not settings:
        raise ValueError("Cannot save empty settings.")
    
    # Preserve admin_pin if not explicitly supplied
    current = load_owner_settings()
    if "admin_pin" not in settings:
        settings["admin_pin"] = current.get("admin_pin", "admin123")
        
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        
    return settings

def reset_owner_settings() -> Dict[str, Any]:
    """Resets settings back to original factory defaults."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_SETTINGS, f, indent=2, ensure_ascii=False)
    return json.loads(json.dumps(DEFAULT_SETTINGS))

def verify_owner_pin(pin: str) -> bool:
    """Verifies owner/admin PIN securely."""
    current = load_owner_settings()
    expected = current.get("admin_pin", "admin123")
    return hmac.compare_digest(str(pin).strip(), str(expected).strip())

def generate_owner_token(pin: str) -> str:
    """Generates a simple session verification token for the owner session."""
    return hashlib.sha256(f"{pin}:{AUTH_SECRET}".encode()).hexdigest()

def verify_owner_token(token: str) -> bool:
    """Verifies whether provided token matches current admin PIN."""
    current = load_owner_settings()
    expected_pin = current.get("admin_pin", "admin123")
    expected_token = generate_owner_token(expected_pin)
    return hmac.compare_digest(str(token or "").strip(), expected_token)

def _deep_merge(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges overrides into defaults without dropping keys."""
    result = json.loads(json.dumps(defaults))
    for k, v in overrides.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
