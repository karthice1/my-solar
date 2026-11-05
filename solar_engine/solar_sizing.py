"""Solar Sizing: Comprehensive Photovoltaic Engineering Capacity & Equipment Sizing.

Uses South India / Tamil Nadu specific irradiation physics, performance ratios,
panel wattage configurations, and inverter capacity matching.
"""

import math
from typing import Dict, Any, Optional

STANDARD_INVERTERS_KW = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0]

def size_solar_system(
    annual_consumption_kwh: float,
    sanctioned_load_kw: float = 0.0,
    panel_wattage_wp: int = 540,
    specific_annual_yield_kwh_per_kw: float = 1450.0,
    performance_ratio: float = 0.78,
    system_type: str = "on-grid",
    coverage_target_percent: float = 100.0
) -> Dict[str, Any]:
    """
    Computes rigorous photovoltaic system sizing based on annual demand,
    standard equipment ratings, and TANGEDCO grid parameters.
    """
    # Target generation
    target_annual_kwh = annual_consumption_kwh * (coverage_target_percent / 100.0)

    # Raw engineering capacity required
    if specific_annual_yield_kwh_per_kw <= 0:
        specific_annual_yield_kwh_per_kw = 1450.0

    raw_required_kw = target_annual_kwh / specific_annual_yield_kwh_per_kw
    
    # Practical minimum 1 kW for residential grid-tie
    raw_required_kw = max(1.0, raw_required_kw)

    # Standard commercial recommended capacity (rounded to nearest 0.5 kW)
    recommended_kw = round(raw_required_kw * 2) / 2
    recommended_kw = max(1.0, recommended_kw)

    # Panel count calculation
    if panel_wattage_wp <= 0:
        panel_wattage_wp = 540

    panel_count = math.ceil((recommended_kw * 1000.0) / panel_wattage_wp)
    # Recompute exact DC capacity from physical panels
    actual_dc_capacity_kw = round((panel_count * panel_wattage_wp) / 1000.0, 3)

    # Inverter sizing (Target DC:AC ratio between 1.0 and 1.25)
    inverter_capacity_kw = 1.0
    for inv_cap in STANDARD_INVERTERS_KW:
        if inv_cap >= recommended_kw * 0.90:
            inverter_capacity_kw = inv_cap
            break
    if inverter_capacity_kw < recommended_kw * 0.90:
        inverter_capacity_kw = STANDARD_INVERTERS_KW[-1]

    # Estimated roof area
    # 540W module dimensions approx 2.28m x 1.13m = 2.58 sqm = 27.8 sq.ft
    # Adding ~20% inter-row shadow buffer and walkway space
    sqft_per_panel = (panel_wattage_wp / 540.0) * 28.0
    roof_area_sqft = int(math.ceil(panel_count * sqft_per_panel * 1.20))

    # Sanctioned Load & Net-Metering Compliance Check
    load_exceeded = False
    load_ratio_percent = 100.0
    net_meter_status = "Compliant"
    net_meter_notes = "System capacity is within 100% of sanctioned load."

    if sanctioned_load_kw > 0:
        load_ratio_percent = round((actual_dc_capacity_kw / sanctioned_load_kw) * 100.0, 1)
        if actual_dc_capacity_kw > sanctioned_load_kw:
            load_exceeded = True
            net_meter_status = "Enhancement Recommended"
            net_meter_notes = (
                f"Recommended capacity ({actual_dc_capacity_kw:.1f} kW) exceeds current sanctioned load ({sanctioned_load_kw:.1f} kW). "
                f"TANGEDCO load enhancement to {math.ceil(actual_dc_capacity_kw)} kW is recommended for 100% net-metering sanction."
            )

    return {
        "raw_required_capacity_kw": round(raw_required_kw, 2),
        "recommended_capacity_kw": round(recommended_kw, 1),
        "actual_dc_capacity_kw": actual_dc_capacity_kw,
        "selected_panel_wattage_wp": panel_wattage_wp,
        "number_of_panels": panel_count,
        "inverter_capacity_kw": inverter_capacity_kw,
        "approx_roof_area_sqft": roof_area_sqft,
        "specific_annual_yield_kwh_per_kw": specific_annual_yield_kwh_per_kw,
        "performance_ratio": performance_ratio,
        "system_type": system_type,
        "sanctioned_load_kw": sanctioned_load_kw,
        "load_ratio_percent": load_ratio_percent,
        "net_meter_status": net_meter_status,
        "net_meter_notes": net_meter_notes,
        "is_net_meter_compliant": not load_exceeded,
        "disclaimer": "Capacity estimation is based on historical electricity demand and standard Tamil Nadu solar irradiance. Actual site feasibility, shading factors, and transformer limits are subject to pre-installation survey."
    }
