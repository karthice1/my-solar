"""Product Catalogue & Tiered Solar Package Definitions.

Provides verified equipment specifications and bundles for:
1. Economy Package
2. Recommended Package
3. Premium Package
"""

from typing import Dict, Any, List

CATALOGUE = {
    "panels": {
        "economy": {
            "tier": "Economy",
            "manufacturer": "Vikram Solar / Goldi",
            "model": "Somera Grand Half-Cut",
            "wattage_wp": 540,
            "technology": "Mono PERC Half-Cut Monofacial",
            "efficiency_percent": 20.8,
            "product_warranty_years": 10,
            "performance_warranty_years": 25,
            "price_multiplier": 0.94  # 6% discount relative to baseline
        },
        "recommended": {
            "tier": "Recommended",
            "manufacturer": "Waaree Energies Ltd",
            "model": "Bi-55-550 Bifacial",
            "wattage_wp": 550,
            "technology": "Mono PERC Half-Cut Dual-Glass Bifacial",
            "efficiency_percent": 21.3,
            "product_warranty_years": 12,
            "performance_warranty_years": 25,
            "price_multiplier": 1.00  # Baseline standard
        },
        "premium": {
            "tier": "Premium",
            "manufacturer": "Jinko Solar / Adani Solar",
            "model": "Tiger Neo N-Type TOPCon 580Wp",
            "wattage_wp": 580,
            "technology": "N-Type TOPCon Ultra-High Efficiency Dual-Glass",
            "efficiency_percent": 22.4,
            "product_warranty_years": 15,
            "performance_warranty_years": 30,
            "price_multiplier": 1.10  # 10% premium for N-Type TOPCon & 30yr warranty
        }
    },
    "inverters": {
        "economy": {
            "manufacturer": "Growatt / Deye",
            "model": "MIN 3000-6000TL-X",
            "type": "Single Phase Grid-Tied String Inverter",
            "warranty_years": 5,
            "monitoring": "Basic Wi-Fi Dongle",
            "efficiency_percent": 97.4
        },
        "recommended": {
            "manufacturer": "Solis / Sungrow",
            "model": "S6-GR1P Smart Series",
            "type": "Smart Dual-MPPT Single/Three Phase Grid-Tied Inverter",
            "warranty_years": 7,
            "monitoring": "Cloud 24x7 Wi-Fi + Mobile App Telemetry",
            "efficiency_percent": 97.8
        },
        "premium": {
            "manufacturer": "Sungrow / SolarEdge / Enphase",
            "model": "Hybrid-Ready Smart Power Hub",
            "type": "Smart Hybrid-Ready Bi-Directional Inverter with Arc-Fault Protection",
            "warranty_years": 10,
            "monitoring": "Advanced AI Cloud Analytics & Module-Level Monitoring",
            "efficiency_percent": 98.4
        }
    },
    "structures": {
        "economy": {
            "type": "Hot-Dip Galvanized (HDG 80 Micron) Standard Flush Mount",
            "warranty_years": 10,
            "wind_speed_rating_kmph": 150
        },
        "recommended": {
            "type": "Pre-Galvanized High-Tensile Steel & Anodized Marine Aluminum Fasteners",
            "warranty_years": 15,
            "wind_speed_rating_kmph": 170
        },
        "premium": {
            "type": "SuperDyma / High-Rise Elevated Walkway Gazebo-Grade Structure",
            "warranty_years": 20,
            "wind_speed_rating_kmph": 180
        }
    }
}

def generate_three_packages(
    recommended_kw: float,
    baseline_price_per_kw: float = 52000.0,
    gst_rate_percent: float = 12.0
) -> Dict[str, Any]:
    """
    Generates three side-by-side package tiers (Economy, Recommended, Premium)
    scaled to the target capacity.
    """
    import math

    packages = {}
    tiers = [("economy", "Economy Package"), ("recommended", "Recommended Package"), ("premium", "Premium Package")]

    for key, title in tiers:
        p_info = CATALOGUE["panels"][key]
        i_info = CATALOGUE["inverters"][key]
        s_info = CATALOGUE["structures"][key]

        # Panel count calculation for this specific package wattage
        wattage = p_info["wattage_wp"]
        panel_count = math.ceil((recommended_kw * 1000.0) / wattage)
        dc_capacity = round((panel_count * wattage) / 1000.0, 2)

        # Inverter capacity matches system
        inv_cap = round(recommended_kw * 1.0, 1)

        # Package Pricing
        mult = p_info["price_multiplier"]
        pkg_price_per_kw = round(baseline_price_per_kw * mult, 0)
        system_cost = round(dc_capacity * pkg_price_per_kw, 0)
        gst_amount = round(system_cost * (gst_rate_percent / 100.0), 0)
        total_price = system_cost + gst_amount

        # Subsidy (PM Surya Ghar rules for domestic rooftop in India)
        # 1 kW: ₹30,000; 2 kW: ₹60,000; 3 kW+: ₹78,000
        subsidy_amount = 0.0
        if dc_capacity >= 3.0:
            subsidy_amount = 78000.0
        elif dc_capacity >= 2.0:
            subsidy_amount = 60000.0
        elif dc_capacity >= 1.0:
            subsidy_amount = 30000.0

        net_payable = max(0.0, total_price - subsidy_amount)

        packages[key] = {
            "tier_key": key,
            "title": title,
            "is_recommended": (key == "recommended"),
            "system_capacity_kw": dc_capacity,
            "panel": {
                "manufacturer": p_info["manufacturer"],
                "model": p_info["model"],
                "wattage_wp": wattage,
                "technology": p_info["technology"],
                "efficiency_percent": p_info["efficiency_percent"],
                "panel_count": panel_count,
                "product_warranty_years": p_info["product_warranty_years"],
                "performance_warranty_years": p_info["performance_warranty_years"]
            },
            "inverter": {
                "manufacturer": i_info["manufacturer"],
                "model": i_info["model"],
                "type": i_info["type"],
                "capacity_kw": inv_cap,
                "warranty_years": i_info["warranty_years"],
                "monitoring": i_info["monitoring"],
                "efficiency_percent": i_info["efficiency_percent"]
            },
            "structure": {
                "type": s_info["type"],
                "warranty_years": s_info["warranty_years"],
                "wind_rating": s_info["wind_speed_rating_kmph"]
            },
            "pricing": {
                "price_per_kw": pkg_price_per_kw,
                "system_cost": system_cost,
                "gst_rate_percent": gst_rate_percent,
                "gst_amount": gst_amount,
                "gross_total": total_price,
                "subsidy_applicable": True,
                "subsidy_amount": subsidy_amount,
                "net_payable_amount": net_payable
            }
        }

    return packages
