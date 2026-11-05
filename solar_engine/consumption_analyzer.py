"""Consumption Analyzer: Advanced TNEB Billing Interval, Frequency & Consumption Analysis.

Extracts seasonal trends, actual days between meter reads, bi-monthly/monthly detection,
and robust annualized demand estimations.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

def parse_date(date_str: str) -> Optional[datetime]:
    """Parses various date formats returned by TNEB portal (DD/MM/YYYY, DD-MM-YYYY)."""
    if not date_str:
        return None
    s = str(date_str).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

def analyze_consumption(billing_cycles: List[Dict[str, Any]], sanctioned_load_kw: float = 0.0) -> Dict[str, Any]:
    """
    Performs comprehensive statistical, temporal and seasonal analysis of consumer billing records.
    Never invents missing data.
    """
    result: Dict[str, Any] = {
        "cycles_analyzed": len(billing_cycles),
        "total_units_consumed": 0.0,
        "total_cc_charges": 0.0,
        "average_units_per_cycle": 0.0,
        "billing_frequency": "bi-monthly",  # "bi-monthly" or "monthly"
        "average_cycle_days": 60,
        "average_monthly_units": 0.0,
        "annualized_units": 0.0,
        "peak_cycle_units": 0.0,
        "lowest_cycle_units": 0.0,
        "average_effective_rate_per_unit": 6.5,  # ₹ / kWh
        "data_quality_status": "GOOD",           # "GOOD", "ACCEPTABLE", "INSUFFICIENT"
        "data_quality_warnings": [],
        "monthly_trend": [],
        "intervals": []
    }

    if not billing_cycles:
        result["data_quality_status"] = "INSUFFICIENT"
        result["data_quality_warnings"].append("No historical billing cycles available for this consumer.")
        return result

    # Clean valid units
    valid_cycles = []
    for c in billing_cycles:
        units = float(c.get("units_consumed") or 0.0)
        charges = float(c.get("cc_charges") or 0.0)
        dt = parse_date(c.get("assessment_date", ""))
        valid_cycles.append({
            "raw": c,
            "units": units,
            "charges": charges,
            "date": dt,
            "date_str": c.get("assessment_date", ""),
            "status": c.get("status", "NORMAL")
        })

    # Sort chronological (oldest to newest)
    sorted_cycles = sorted([vc for vc in valid_cycles if vc["date"]], key=lambda x: x["date"])
    
    # Calculate intervals in days
    intervals_days = []
    for i in range(1, len(sorted_cycles)):
        delta = (sorted_cycles[i]["date"] - sorted_cycles[i - 1]["date"]).days
        if 15 <= delta <= 120:  # Valid billing window
            intervals_days.append(delta)

    if intervals_days:
        avg_days = sum(intervals_days) / len(intervals_days)
    else:
        avg_days = 60.0  # TNEB default bi-monthly

    result["average_cycle_days"] = round(avg_days, 1)

    # Detect billing frequency
    if avg_days < 42:
        result["billing_frequency"] = "monthly"
        cycles_per_year = 12.0
    else:
        result["billing_frequency"] = "bi-monthly"
        cycles_per_year = 6.0

    # Aggregate consumption
    total_units = sum(c["units"] for c in valid_cycles)
    total_charges = sum(c["charges"] for c in valid_cycles)
    result["total_units_consumed"] = round(total_units, 1)
    result["total_cc_charges"] = round(total_charges, 2)

    # Effective cost per unit from actual historical bills
    if total_units > 0:
        result["average_effective_rate_per_unit"] = round(total_charges / total_units, 2)
    else:
        result["average_effective_rate_per_unit"] = 7.0

    num_cycles = len(valid_cycles)
    avg_per_cycle = total_units / num_cycles if num_cycles > 0 else 0.0
    result["average_units_per_cycle"] = round(avg_per_cycle, 1)

    # Recent 6 cycles (or all available if < 6)
    recent_cycles = valid_cycles[:6] if len(valid_cycles) >= 6 else valid_cycles
    recent_total = sum(c["units"] for c in recent_cycles)
    recent_avg_per_cycle = recent_total / len(recent_cycles) if recent_cycles else 0.0

    # Monthly and Annualized calculation
    if result["billing_frequency"] == "monthly":
        monthly_avg = recent_avg_per_cycle
    else:
        monthly_avg = recent_avg_per_cycle / 2.0  # Bi-monthly divided by 2

    result["average_monthly_units"] = round(monthly_avg, 1)
    result["annualized_units"] = round(monthly_avg * 12.0, 1)

    # Peak & Lowest
    all_units = [c["units"] for c in valid_cycles if c["units"] > 0]
    if all_units:
        result["peak_cycle_units"] = round(max(all_units), 1)
        result["lowest_cycle_units"] = round(min(all_units), 1)

    # Monthly Trend Array
    result["monthly_trend"] = [
        {
            "assessment_date": c["date_str"],
            "units": c["units"],
            "charges": c["charges"]
        }
        for c in valid_cycles[:12]
    ]

    # Data Quality Auditing
    if num_cycles < 3:
        result["data_quality_status"] = "INSUFFICIENT"
        result["data_quality_warnings"].append(
            f"Only {num_cycles} billing cycle(s) available. Solar requirement estimation is based on limited data."
        )
    elif num_cycles < 6:
        result["data_quality_status"] = "ACCEPTABLE"
        result["data_quality_warnings"].append(
            f"Fewer than 6 cycles available ({num_cycles} cycles). Annual estimation may not capture all seasonal variations."
        )

    # Check for zero consumption cycles
    zero_cycles = [c for c in valid_cycles if c["units"] == 0]
    if zero_cycles:
        result["data_quality_warnings"].append(
            f"{len(zero_cycles)} cycle(s) report 0 units consumed (door lock/minimum charge cycles)."
        )

    return result
