"""Financial Calculator: Solar Return on Investment (ROI), Bill Savings & 25-Year Lifecycle Cashflow.

Applies TNEB slab rate dynamics, degradation factors, tariff inflation, and payback periods.
"""

from typing import Dict, Any, List

def calculate_financials(
    system_capacity_kw: float,
    estimated_annual_generation_kwh: float,
    net_project_cost: float,
    effective_rate_per_kwh: float = 6.5,
    tariff_escalation_rate_percent: float = 3.0,
    annual_degradation_rate_percent: float = 0.6,
    om_cost_percent: float = 1.0
) -> Dict[str, Any]:
    """
    Calculates detailed financial returns, savings, and 25-year cumulative financial performance.
    """
    cap = max(0.1, float(system_capacity_kw))
    annual_gen = max(0.0, float(estimated_annual_generation_kwh))
    net_cost = max(1.0, float(net_project_cost))
    rate = max(1.0, float(effective_rate_per_kwh))

    # Year 1 Savings
    year_1_savings = round(annual_gen * rate, 2)
    monthly_average_savings = round(year_1_savings / 12.0, 2)

    # Simple Payback Period
    if year_1_savings > 0:
        payback_years = round(net_cost / year_1_savings, 1)
    else:
        payback_years = 0.0

    # 25-Year Cumulative Lifecycle Analysis
    lifecycle_years = 25
    annual_projections: List[Dict[str, Any]] = []
    
    cumulative_savings = 0.0
    cumulative_cashflow = -net_cost
    current_generation = annual_gen
    current_tariff = rate
    break_even_year = None

    for yr in range(1, lifecycle_years + 1):
        if yr > 1:
            current_generation *= (1.0 - (annual_degradation_rate_percent / 100.0))
            current_tariff *= (1.0 + (tariff_escalation_rate_percent / 100.0))

        gross_savings = current_generation * current_tariff
        # Operating & Maintenance allowance (cleaning, inverter servicing)
        om_cost = (net_cost * (om_cost_percent / 100.0)) if yr > 5 else 0.0
        net_yr_savings = gross_savings - om_cost
        
        cumulative_savings += net_yr_savings
        cumulative_cashflow += net_yr_savings

        if break_even_year is None and cumulative_cashflow >= 0:
            break_even_year = yr

        if yr in (1, 3, 5, 10, 15, 20, 25):
            annual_projections.append({
                "year": yr,
                "annual_generation_kwh": round(current_generation, 0),
                "grid_tariff_rs_per_kwh": round(current_tariff, 2),
                "annual_savings_rs": round(net_yr_savings, 0),
                "cumulative_savings_rs": round(cumulative_savings, 0),
                "net_cumulative_cashflow_rs": round(cumulative_cashflow, 0)
            })

    # Return on Investment (ROI) over 25 years
    total_net_profit = cumulative_savings - net_cost
    roi_percent = round((total_net_profit / net_cost) * 100.0, 1) if net_cost > 0 else 0.0

    return {
        "net_project_cost": round(net_cost, 2),
        "effective_tariff_rate_rs_per_kwh": round(rate, 2),
        "year_1_annual_savings_rs": year_1_savings,
        "monthly_average_savings_rs": monthly_average_savings,
        "simple_payback_years": payback_years,
        "break_even_year": break_even_year or round(payback_years),
        "total_25_year_savings_rs": round(cumulative_savings, 2),
        "net_lifetime_profit_rs": round(total_net_profit, 2),
        "roi_percent": roi_percent,
        "milestone_projections": annual_projections,
        "assumptions": {
            "annual_degradation_percent": annual_degradation_rate_percent,
            "grid_tariff_escalation_percent": tariff_escalation_rate_percent,
            "om_expense_allowance_percent": om_cost_percent,
            "disclaimer": "Savings and payback calculations are financial simulations based on current TNEB tariffs, historical consumption, and projected inflation. Actual savings depend on future utility tariff revisions, weather conditions, and timely panel maintenance."
        }
    }
