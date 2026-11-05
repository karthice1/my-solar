"""Pricing Engine: Accurate Solar Commercial Pricing, GST, Discounts & Subsidies.

Guarantees zero double-counting between bundled per-kW pricing and itemized BOQ components.
"""

from typing import Dict, Any, Optional

def calculate_quotation_pricing(
    system_capacity_kw: float,
    pricing_config: Dict[str, Any],
    discount_amount: float = 0.0,
    discount_percent: float = 0.0,
    subsidy_enabled: bool = True,
    tariff_category: str = "LA1A / DOMESTIC",
    custom_price_per_kw: Optional[float] = None,
    custom_additional_charges: float = 0.0
) -> Dict[str, Any]:
    """
    Computes rigorous commercial quotation pricing.
    Supports both bundled-per-kW and itemized models, GST treatment,
    and official PM Surya Ghar subsidy rules.
    """
    cap = max(0.1, float(system_capacity_kw))
    model = pricing_config.get("pricing_model", "bundled_per_kw")
    gst_rate = float(pricing_config.get("gst_rate_percent", 12.0))
    includes_gst = bool(pricing_config.get("price_per_kw_includes_gst", False))

    if custom_price_per_kw is not None and custom_price_per_kw > 0:
        base_rate = float(custom_price_per_kw)
    else:
        base_rate = float(pricing_config.get("price_per_kw", 52000.0))

    itemized_boq = []

    if model == "bundled_per_kw":
        # Bundled system cost
        if includes_gst:
            # Base price already includes GST -> back-calculate
            gross_system = round(cap * base_rate, 2)
            base_system_cost = round(gross_system / (1.0 + (gst_rate / 100.0)), 2)
            gst_amount = round(gross_system - base_system_cost, 2)
        else:
            base_system_cost = round(cap * base_rate, 2)
            gst_amount = round(base_system_cost * (gst_rate / 100.0), 2)
            gross_system = round(base_system_cost + gst_amount, 2)

        # Generate itemized BOQ for presentation only (breakdown of the bundled price)
        panel_share = round(base_system_cost * 0.48, 2)
        inverter_share = round(base_system_cost * 0.22, 2)
        structure_share = round(base_system_cost * 0.12, 2)
        electrical_share = round(base_system_cost * 0.08, 2)
        install_share = round(base_system_cost * 0.10, 2)

        itemized_boq = [
            {"item": "Solar PV Modules (Tier-1 Mono PERC / TOPCon)", "amount": panel_share, "category": "Equipment"},
            {"item": "Solar Grid-Tied Inverter & Wi-Fi Monitoring", "amount": inverter_share, "category": "Equipment"},
            {"item": "Module Mounting Structure (Hot-Dip Galvanized / Al)", "amount": structure_share, "category": "Hardware"},
            {"item": "DC/AC Cables, Combiner Boxes & SPD Earthing", "amount": electrical_share, "category": "Electrical"},
            {"item": "Turnkey Installation, Testing & TANGEDCO Liaisoning", "amount": install_share, "category": "Services"}
        ]
    else:
        # Itemized pricing model
        item_cfg = pricing_config.get("itemized", {})
        panel_cost = round(cap * 1000.0 * float(item_cfg.get("panel_per_wp", 24.0)), 2)
        inv_cost = round(cap * float(item_cfg.get("inverter_per_kw", 11000.0)), 2)
        struct_cost = round(cap * float(item_cfg.get("mounting_structure_per_kw", 4500.0)), 2)
        cable_cost = round(cap * float(item_cfg.get("cables_and_wiring_per_kw", 3500.0)), 2)
        elec_cost = round(float(item_cfg.get("electrical_accessories_lump", 6000.0)), 2)
        inst_cost = round(cap * float(item_cfg.get("installation_charges_per_kw", 4000.0)), 2)
        trans_cost = round(float(item_cfg.get("transportation_charges_lump", 3500.0)), 2)
        add_cost = round(float(item_cfg.get("additional_charges_lump", 0.0)) + custom_additional_charges, 2)

        base_system_cost = panel_cost + inv_cost + struct_cost + cable_cost + elec_cost + inst_cost + trans_cost + add_cost
        gst_amount = round(base_system_cost * (gst_rate / 100.0), 2)
        gross_system = base_system_cost + gst_amount

        itemized_boq = [
            {"item": "Solar PV Modules", "amount": panel_cost, "category": "Equipment"},
            {"item": "Solar Grid-Tied Inverter", "amount": inv_cost, "category": "Equipment"},
            {"item": "Mounting Structure", "amount": struct_cost, "category": "Hardware"},
            {"item": "Cables & Wiring", "amount": cable_cost, "category": "Electrical"},
            {"item": "Electrical Accessories & Earthing", "amount": elec_cost, "category": "Electrical"},
            {"item": "Installation & Commissioning", "amount": inst_cost, "category": "Services"},
            {"item": "Transportation & Logistics", "amount": trans_cost, "category": "Logistics"}
        ]
        if add_cost > 0:
            itemized_boq.append({"item": "Additional Custom Charges", "amount": add_cost, "category": "Other"})

    # Commercial Discounts
    discount_val = 0.0
    if discount_amount > 0:
        discount_val += discount_amount
    if discount_percent > 0:
        discount_val += (base_system_cost * (discount_percent / 100.0))
    discount_val = round(min(discount_val, base_system_cost), 2)

    # Net system cost post-discount
    discounted_base = base_system_cost - discount_val
    discounted_gst = round(discounted_base * (gst_rate / 100.0), 2)
    final_contract_value = round(discounted_base + discounted_gst, 2)

    # Central Financial Assistance (Subsidy) Evaluation
    # Applicable primarily to Domestic / Residential LT customers under PM Surya Ghar
    is_domestic = "DOMESTIC" in tariff_category.upper() or "LA1A" in tariff_category.upper() or "1A" in tariff_category.upper()
    subsidy_amount = 0.0

    if subsidy_enabled and is_domestic:
        if cap >= 3.0:
            subsidy_amount = 78000.0
        elif cap >= 2.0:
            subsidy_amount = 60000.0
        elif cap >= 1.0:
            subsidy_amount = 30000.0
        else:
            subsidy_amount = round(cap * 30000.0, 2)

    # Final Customer Net Investment (Payable)
    net_customer_payable = max(0.0, round(final_contract_value - subsidy_amount, 2))

    return {
        "pricing_model": model,
        "system_capacity_kw": round(cap, 2),
        "rate_per_kw": round(base_rate, 2),
        "price_includes_gst": includes_gst,
        "base_system_cost": base_system_cost,
        "gst_rate_percent": gst_rate,
        "gst_amount": discounted_gst,
        "discount_amount": discount_val,
        "discount_percent": discount_percent,
        "gross_contract_value": final_contract_value,
        "subsidy_eligible": (subsidy_amount > 0),
        "subsidy_amount": subsidy_amount,
        "subsidy_scheme_name": "PM Surya Ghar: Muft Bijli Yojana (Central Financial Assistance)",
        "net_customer_payable": net_customer_payable,
        "itemized_boq": itemized_boq
    }
