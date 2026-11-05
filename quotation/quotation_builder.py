"""Quotation Builder: End-to-End Orchestrator for Solar Proposal Generation.

Combines verified TNEB consumer data, owner commercial defaults, and customer-specific
overrides into an interactive, dynamically recalculating quotation.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from solar_engine.consumption_analyzer import analyze_consumption
from solar_engine.solar_sizing import size_solar_system
from solar_engine.generation_estimator import estimate_generation
from solar_engine.financial_calculator import calculate_financials
from quotation.settings_manager import load_owner_settings
from quotation.pricing_engine import calculate_quotation_pricing
from quotation.product_catalogue import generate_three_packages

def build_initial_quotation(tneb_data: Dict[str, Any], quotation_no: Optional[str] = None) -> Dict[str, Any]:
    """
    Builds the baseline recommended quotation directly from verified TNEB data
    and current persistent owner settings.
    """
    owner_settings = load_owner_settings()

    # 1. Customer Information
    consumer_no = str(tneb_data.get("consumer_no") or "").strip()
    customer_name = str(tneb_data.get("consumer_name") or "Valued TNEB Consumer").strip()
    address = str(tneb_data.get("address") or "Tamil Nadu Service Connection").strip()
    tariff = str(tneb_data.get("tariff_code") or "LA1A / DOMESTIC").strip()
    sanctioned_load_kw = float(tneb_data.get("sanctioned_load_kw") or 0.0)

    # 2. Consumption Analysis
    billing_cycles = tneb_data.get("billing_cycles", [])
    consumption_analysis = analyze_consumption(billing_cycles, sanctioned_load_kw=sanctioned_load_kw)

    # 3. Recommended Solar Sizing
    annual_kwh = consumption_analysis["annualized_units"]
    panel_cfg = owner_settings["panel"]
    sizing = size_solar_system(
        annual_consumption_kwh=annual_kwh,
        sanctioned_load_kw=sanctioned_load_kw,
        panel_wattage_wp=panel_cfg.get("wattage_wp", 540),
        system_type=owner_settings["system"].get("system_type", "on-grid")
    )

    recommended_kw = sizing["recommended_capacity_kw"]
    actual_dc_kw = sizing["actual_dc_capacity_kw"]
    panel_count = sizing["number_of_panels"]

    # 4. Generation Estimations
    gen_estimates = estimate_generation(actual_dc_kw)

    # 5. Commercial Pricing & BOQ
    pricing_cfg = owner_settings["pricing"]
    pricing = calculate_quotation_pricing(
        system_capacity_kw=actual_dc_kw,
        pricing_config=pricing_cfg,
        tariff_category=tariff
    )

    # 6. Financial ROI & Payback
    effective_rate = consumption_analysis["average_effective_rate_per_unit"]
    financials = calculate_financials(
        system_capacity_kw=actual_dc_kw,
        estimated_annual_generation_kwh=gen_estimates["estimated_annual_generation_kwh"],
        net_project_cost=pricing["net_customer_payable"],
        effective_rate_per_kwh=effective_rate
    )

    # 7. Package Tiers (Economy, Recommended, Premium)
    packages = generate_three_packages(
        recommended_kw=recommended_kw,
        baseline_price_per_kw=pricing_cfg.get("price_per_kw", 52000.0),
        gst_rate_percent=pricing_cfg.get("gst_rate_percent", 12.0)
    )

    today_str = datetime.now().strftime("%d-%b-%Y")

    # Complete Quotation Object
    return {
        "quotation_no": quotation_no or "",
        "quotation_date": today_str,
        "status": "Draft",
        "version": 1,
        "is_customized": False,

        # Customer Details (Read-only verified)
        "consumer_no": consumer_no,
        "customer_name": customer_name,
        "address": address,
        "tariff_category": tariff,
        "sanctioned_load_kw": sanctioned_load_kw,
        "phase": tneb_data.get("phase", "3 Phase"),
        "meter_number": tneb_data.get("meter_number", ""),

        # Branding
        "branding": owner_settings["branding"],

        # System Specifications
        "system_type": owner_settings["system"]["system_type"],
        "system_capacity_kw": actual_dc_kw,
        "recommended_capacity_kw": recommended_kw,

        "panel": {
            "manufacturer": panel_cfg["manufacturer"],
            "model": panel_cfg["model"],
            "wattage_wp": sizing["selected_panel_wattage_wp"],
            "quantity": panel_count,
            "technology": panel_cfg["technology"],
            "dimensions": panel_cfg.get("dimensions", "2278 x 1134 x 35 mm"),
            "product_warranty_years": panel_cfg["product_warranty_years"],
            "performance_warranty_years": panel_cfg["performance_warranty_years"]
        },

        "inverter": {
            "manufacturer": owner_settings["inverter"]["manufacturer"],
            "model": owner_settings["inverter"]["model"],
            "type": owner_settings["inverter"]["type"],
            "capacity_kw": sizing["inverter_capacity_kw"],
            "warranty_years": owner_settings["inverter"]["warranty_years"],
            "quantity": 1
        },

        "sizing": sizing,
        "consumption_analysis": consumption_analysis,
        "generation": gen_estimates,
        "pricing": pricing,
        "financials": financials,
        "packages": packages,

        "warranties": owner_settings["warranty"],
        "commercial_terms": owner_settings["commercial_terms"],

        # Customer overrides snapshot
        "overrides": {}
    }

def recalculate_quotation(quotation: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies customer-specific overrides to an existing quotation and recalculates
    all dependent technical, pricing and financial values immediately.
    Guarantees that original TNEB data and owner defaults remain intact.
    """
    owner_settings = load_owner_settings()
    updated = json.loads(json.dumps(quotation))
    updated["overrides"] = overrides
    updated["is_customized"] = True

    # 1. Capacity & Equipment overrides
    panel_wattage = int(overrides.get("panel_wattage_wp") or updated["panel"]["wattage_wp"])
    
    # If customer explicitly adjusted capacity or panel count
    if "panel_quantity" in overrides and overrides["panel_quantity"]:
        panel_count = int(overrides["panel_quantity"])
        actual_dc_kw = round((panel_count * panel_wattage) / 1000.0, 3)
    elif "system_capacity_kw" in overrides and overrides["system_capacity_kw"]:
        target_kw = float(overrides["system_capacity_kw"])
        import math
        panel_count = math.ceil((target_kw * 1000.0) / panel_wattage)
        actual_dc_kw = round((panel_count * panel_wattage) / 1000.0, 3)
    else:
        panel_count = updated["panel"]["quantity"]
        actual_dc_kw = round((panel_count * panel_wattage) / 1000.0, 3)

    updated["system_capacity_kw"] = actual_dc_kw
    updated["panel"]["wattage_wp"] = panel_wattage
    updated["panel"]["quantity"] = panel_count

    if "panel_manufacturer" in overrides:
        updated["panel"]["manufacturer"] = str(overrides["panel_manufacturer"])
    if "panel_model" in overrides:
        updated["panel"]["model"] = str(overrides["panel_model"])

    # Inverter overrides
    if "inverter_capacity_kw" in overrides and overrides["inverter_capacity_kw"]:
        updated["inverter"]["capacity_kw"] = float(overrides["inverter_capacity_kw"])
    else:
        updated["inverter"]["capacity_kw"] = round(actual_dc_kw * 1.0, 1)

    if "inverter_manufacturer" in overrides:
        updated["inverter"]["manufacturer"] = str(overrides["inverter_manufacturer"])
    if "inverter_model" in overrides:
        updated["inverter"]["model"] = str(overrides["inverter_model"])

    if "system_type" in overrides:
        updated["system_type"] = str(overrides["system_type"])

    # Roof Area Recomputation
    sqft_per_panel = (panel_wattage / 540.0) * 28.0
    updated["sizing"]["approx_roof_area_sqft"] = int(panel_count * sqft_per_panel * 1.20)
    updated["sizing"]["actual_dc_capacity_kw"] = actual_dc_kw
    updated["sizing"]["number_of_panels"] = panel_count

    # 2. Recompute Generation
    updated["generation"] = estimate_generation(actual_dc_kw)

    # 3. Recompute Commercial Pricing
    pricing_cfg = owner_settings["pricing"]
    custom_rate = float(overrides.get("price_per_kw")) if "price_per_kw" in overrides and overrides["price_per_kw"] else None
    discount_amt = float(overrides.get("discount_amount") or 0.0)
    discount_pct = float(overrides.get("discount_percent") or 0.0)
    subsidy_enabled = overrides.get("subsidy_applicable", True)
    custom_additional = float(overrides.get("custom_additional_charges") or 0.0)

    updated["pricing"] = calculate_quotation_pricing(
        system_capacity_kw=actual_dc_kw,
        pricing_config=pricing_cfg,
        discount_amount=discount_amt,
        discount_percent=discount_pct,
        subsidy_enabled=subsidy_enabled,
        tariff_category=updated.get("tariff_category", "LA1A / DOMESTIC"),
        custom_price_per_kw=custom_rate,
        custom_additional_charges=custom_additional
    )

    # 4. Recompute Financial ROI & Payback
    effective_rate = updated["consumption_analysis"].get("average_effective_rate_per_unit", 6.5)
    updated["financials"] = calculate_financials(
        system_capacity_kw=actual_dc_kw,
        estimated_annual_generation_kwh=updated["generation"]["estimated_annual_generation_kwh"],
        net_project_cost=updated["pricing"]["net_customer_payable"],
        effective_rate_per_kwh=effective_rate
    )

    # 5. Commercial terms overrides
    if "payment_terms" in overrides and overrides["payment_terms"]:
        updated["commercial_terms"]["payment_terms"] = str(overrides["payment_terms"])
    if "quotation_validity_days" in overrides and overrides["quotation_validity_days"]:
        updated["commercial_terms"]["quotation_validity_days"] = int(overrides["quotation_validity_days"])

    return updated
