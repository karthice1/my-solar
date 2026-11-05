"""Generation Estimator: Monthly Seasonal Solar Generation Profile & Yield Modelling.

Models Tamil Nadu / South India solar irradiation patterns across 12 calendar months.
"""

from typing import Dict, Any, List

# Monthly specific yields (kWh generated per kWp installed in Tamil Nadu)
MONTHLY_YIELD_FACTORS: Dict[str, float] = {
    "Jan": 126.0,
    "Feb": 132.0,
    "Mar": 146.0,
    "Apr": 142.0,
    "May": 136.0,
    "Jun": 112.0,
    "Jul": 106.0,
    "Aug": 114.0,
    "Sep": 122.0,
    "Oct": 116.0,
    "Nov": 104.0,
    "Dec": 112.0
}

def estimate_generation(system_capacity_kw: float, specific_annual_yield: float = 1450.0) -> Dict[str, Any]:
    """
    Computes expected monthly and annual solar power generation.
    Distinguishes estimated generation from guaranteed generation.
    """
    cap = max(0.1, float(system_capacity_kw))
    
    # Scale factors if specific_annual_yield differs from baseline 1468
    base_sum = sum(MONTHLY_YIELD_FACTORS.values())
    scale = specific_annual_yield / base_sum if base_sum > 0 else 1.0

    monthly_breakdown: List[Dict[str, Any]] = []
    total_annual_kwh = 0.0

    for month, yield_val in MONTHLY_YIELD_FACTORS.items():
        m_kwh = round(cap * yield_val * scale, 1)
        total_annual_kwh += m_kwh
        monthly_breakdown.append({
            "month": month,
            "specific_yield_kwh_per_kw": round(yield_val * scale, 1),
            "estimated_kwh": m_kwh
        })

    average_monthly_kwh = round(total_annual_kwh / 12.0, 1)
    daily_average_kwh = round(total_annual_kwh / 365.0, 1)

    return {
        "system_capacity_kw": round(cap, 2),
        "estimated_annual_generation_kwh": round(total_annual_kwh, 1),
        "estimated_monthly_generation_kwh": average_monthly_kwh,
        "estimated_daily_generation_kwh": daily_average_kwh,
        "monthly_breakdown": monthly_breakdown,
        "generation_disclaimer": (
            "Solar power generation figures are engineering estimates derived from satellite irradiance data "
            "(MNRE / NASA SSE) for Tamil Nadu. Actual output varies with seasonal weather, panel cleanliness, "
            "ambient temperature and orientation, and does not constitute a guaranteed power generation warranty."
        )
    }
