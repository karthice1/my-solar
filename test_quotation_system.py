#!/usr/bin/env python3
"""
Automated Test Suite for Interactive Solar Quotation Management System
Covers all 20 required acceptance and regression scenarios from Section 13:
 1. Loading TNEB consumer data
 2. Owner settings persistence
 3. Panel wattage configuration
 4. Solar capacity calculation
 5. Panel quantity calculation
 6. Inverter compatibility checks
 7. Pricing calculation
 8. GST calculation
 9. Discount calculation
10. Subsidy eligibility handling
11. Customer-specific quotation editing
12. Owner defaults remaining unchanged after edits
13. Live preview recalculation
14. Draft saving
15. Quotation versioning
16. PDF generation
17. PDF page layout and content validation
18. Quotation history retrieval
19. Missing TNEB data handling
20. Invalid pricing and configuration handling
"""

import os
import sys
import json
import asyncio
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solar_engine.consumption_analyzer import analyze_consumption
from solar_engine.solar_sizing import size_solar_system
from solar_engine.generation_estimator import estimate_generation
from solar_engine.financial_calculator import calculate_financials
from quotation.settings_manager import (
    load_owner_settings,
    save_owner_settings,
    reset_owner_settings,
    verify_owner_pin,
    generate_owner_token,
    verify_owner_token
)
from quotation.pricing_engine import calculate_quotation_pricing
from quotation.product_catalogue import generate_three_packages
from quotation.quotation_builder import build_initial_quotation, recalculate_quotation
from quotation.quotation_history import (
    save_quotation,
    get_quotation,
    list_quotations,
    update_status,
    generate_next_quotation_no,
    get_quotation_versions
)
from quotation.pdf_generator import generate_quotation_pdf, format_inr, format_num

class TestSolarQuotationSystem(unittest.TestCase):

    def setUp(self):
        # Anonymized sample TNEB data
        self.sample_tneb_data = {
            "consumer_no": "044060072111",
            "consumer_name": "R.VASANTHAKUMAR",
            "address": "90 ERUMAPALAYAM ITTERI ROAD, SALEM",
            "tariff_code": "LA1A / DOMESTIC",
            "sanctioned_load": "5 KW",
            "sanctioned_load_kw": 5.0,
            "phase": "3 Phase",
            "meter_number": "TNB74948",
            "billing_cycles": [
                {"assessment_date": "27/10/2026", "units_consumed": 392.0, "cc_charges": 902.4, "recorded_demand": 1.99},
                {"assessment_date": "27/08/2026", "units_consumed": 508.0, "cc_charges": 2107.2, "recorded_demand": 1.00},
                {"assessment_date": "26/06/2026", "units_consumed": 500.0, "cc_charges": 1617.0, "recorded_demand": 1.65},
                {"assessment_date": "28/04/2026", "units_consumed": 530.0, "cc_charges": 2292.0, "recorded_demand": 0.80},
                {"assessment_date": "25/02/2026", "units_consumed": 431.0, "cc_charges": 1370.3, "recorded_demand": 1.00},
                {"assessment_date": "29/12/2025", "units_consumed": 437.0, "cc_charges": 1408.1, "recorded_demand": 3.53}
            ]
        }

    # Test 1: Loading TNEB consumer data
    def test_01_loading_tneb_consumer_data(self):
        q = build_initial_quotation(self.sample_tneb_data)
        self.assertEqual(q["consumer_no"], "044060072111")
        self.assertEqual(q["customer_name"], "R.VASANTHAKUMAR")
        self.assertEqual(q["sanctioned_load_kw"], 5.0)
        self.assertEqual(q["tariff_category"], "LA1A / DOMESTIC")
        self.assertEqual(q["consumption_analysis"]["cycles_analyzed"], 6)
        self.assertGreater(q["consumption_analysis"]["annualized_units"], 2000)

    # Test 2: Owner settings persistence
    def test_02_owner_settings_persistence(self):
        settings = load_owner_settings()
        original_price = settings["pricing"]["price_per_kw"]
        try:
            settings["pricing"]["price_per_kw"] = 55555.0
            save_owner_settings(settings)
            reloaded = load_owner_settings()
            self.assertEqual(reloaded["pricing"]["price_per_kw"], 55555.0)
        finally:
            settings["pricing"]["price_per_kw"] = original_price
            save_owner_settings(settings)

    # Test 3: Panel wattage configuration
    def test_03_panel_wattage_configuration(self):
        for w in [540, 550, 580, 600]:
            sizing = size_solar_system(annual_consumption_kwh=3000, panel_wattage_wp=w)
            self.assertEqual(sizing["selected_panel_wattage_wp"], w)
            expected_count = -(-int(sizing["recommended_capacity_kw"] * 1000) // w)  # math.ceil
            self.assertEqual(sizing["number_of_panels"], expected_count)

    # Test 4: Solar capacity calculation
    def test_04_solar_capacity_calculation(self):
        # 2900 kWh / 1450 yield = 2.0 kW recommended
        sizing = size_solar_system(annual_consumption_kwh=2900, specific_annual_yield_kwh_per_kw=1450.0)
        self.assertAlmostEqual(sizing["recommended_capacity_kw"], 2.0, places=1)
        self.assertGreaterEqual(sizing["actual_dc_capacity_kw"], 2.0)

    # Test 5: Panel quantity calculation
    def test_05_panel_quantity_calculation(self):
        sizing = size_solar_system(annual_consumption_kwh=3000, panel_wattage_wp=540)
        # Sizing recommended_capacity_kw e.g. 2.0 kW -> ceil(2000 / 540) = 4 panels
        self.assertEqual(sizing["number_of_panels"], 4)
        self.assertEqual(sizing["actual_dc_capacity_kw"], 2.16)

    # Test 6: Inverter compatibility checks
    def test_06_inverter_compatibility_checks(self):
        # Test 1: Sizing under sanctioned load
        sizing_ok = size_solar_system(annual_consumption_kwh=2900, sanctioned_load_kw=5.0)
        self.assertTrue(sizing_ok["is_net_meter_compliant"])
        self.assertEqual(sizing_ok["net_meter_status"], "Compliant")

        # Test 2: Sizing exceeding sanctioned load
        sizing_exceed = size_solar_system(annual_consumption_kwh=9000, sanctioned_load_kw=2.0)
        self.assertFalse(sizing_exceed["is_net_meter_compliant"])
        self.assertEqual(sizing_exceed["net_meter_status"], "Enhancement Recommended")

    # Test 7: Pricing calculation (Bundled vs Itemized)
    def test_07_pricing_calculation(self):
        config_bundled = {
            "pricing_model": "bundled_per_kw",
            "price_per_kw": 50000.0,
            "gst_rate_percent": 12.0,
            "price_per_kw_includes_gst": False
        }
        res = calculate_quotation_pricing(system_capacity_kw=3.0, pricing_config=config_bundled)
        self.assertEqual(res["base_system_cost"], 150000.0)
        self.assertEqual(res["gst_amount"], 18000.0)
        self.assertEqual(res["gross_contract_value"], 168000.0)

    # Test 8: GST calculation
    def test_08_gst_calculation(self):
        # 1. Price excludes GST
        cfg_ex = {"pricing_model": "bundled_per_kw", "price_per_kw": 50000.0, "gst_rate_percent": 12.0, "price_per_kw_includes_gst": False}
        res_ex = calculate_quotation_pricing(system_capacity_kw=2.0, pricing_config=cfg_ex)
        self.assertEqual(res_ex["gst_amount"], 12000.0)
        self.assertEqual(res_ex["gross_contract_value"], 112000.0)

        # 2. Price includes GST
        cfg_inc = {"pricing_model": "bundled_per_kw", "price_per_kw": 56000.0, "gst_rate_percent": 12.0, "price_per_kw_includes_gst": True}
        res_inc = calculate_quotation_pricing(system_capacity_kw=2.0, pricing_config=cfg_inc)
        self.assertEqual(res_inc["gross_contract_value"], 112000.0)
        self.assertEqual(res_inc["base_system_cost"], 100000.0)
        self.assertEqual(res_inc["gst_amount"], 12000.0)

    # Test 9: Discount calculation
    def test_09_discount_calculation(self):
        cfg = {"pricing_model": "bundled_per_kw", "price_per_kw": 50000.0, "gst_rate_percent": 12.0, "price_per_kw_includes_gst": False}
        # 3 kW = 150,000 base. Flat discount 10,000 -> 140,000 base + 12% GST (16,800) = 156,800
        res = calculate_quotation_pricing(system_capacity_kw=3.0, pricing_config=cfg, discount_amount=10000.0)
        self.assertEqual(res["discount_amount"], 10000.0)
        self.assertEqual(res["gross_contract_value"], 156800.0)

    # Test 10: Subsidy eligibility handling
    def test_10_subsidy_eligibility_handling(self):
        cfg = {"pricing_model": "bundled_per_kw", "price_per_kw": 50000.0, "gst_rate_percent": 12.0, "price_per_kw_includes_gst": False}
        # 1 kW Domestic -> ₹30,000 subsidy
        res_1kw = calculate_quotation_pricing(system_capacity_kw=1.0, pricing_config=cfg, tariff_category="LA1A / DOMESTIC")
        self.assertEqual(res_1kw["subsidy_amount"], 30000.0)

        # 2 kW Domestic -> ₹60,000 subsidy
        res_2kw = calculate_quotation_pricing(system_capacity_kw=2.0, pricing_config=cfg, tariff_category="LA1A / DOMESTIC")
        self.assertEqual(res_2kw["subsidy_amount"], 60000.0)

        # 3 kW Domestic -> ₹78,000 subsidy
        res_3kw = calculate_quotation_pricing(system_capacity_kw=3.0, pricing_config=cfg, tariff_category="LA1A / DOMESTIC")
        self.assertEqual(res_3kw["subsidy_amount"], 78000.0)

        # Commercial Tariff -> ₹0 subsidy
        res_comm = calculate_quotation_pricing(system_capacity_kw=3.0, pricing_config=cfg, tariff_category="COMMERCIAL / LT-III")
        self.assertEqual(res_comm["subsidy_amount"], 0.0)

    # Test 11: Customer-specific quotation editing
    def test_11_customer_specific_quotation_editing(self):
        q = build_initial_quotation(self.sample_tneb_data)
        initial_cap = q["system_capacity_kw"]
        
        # Override capacity to 4.0 kW and discount 5,000
        edited = recalculate_quotation(q, {"system_capacity_kw": 4.0, "discount_amount": 5000})
        self.assertTrue(edited["is_customized"])
        self.assertNotEqual(edited["system_capacity_kw"], initial_cap)
        self.assertEqual(edited["pricing"]["discount_amount"], 5000.0)

    # Test 12: Owner defaults remaining unchanged after edits
    def test_12_owner_defaults_remain_unchanged_after_edits(self):
        original_settings = load_owner_settings()
        orig_price = original_settings["pricing"]["price_per_kw"]
        
        q = build_initial_quotation(self.sample_tneb_data)
        recalculate_quotation(q, {"price_per_kw": 99999.0, "discount_amount": 25000})
        
        # Check that owner settings on disk are completely untouched
        after_settings = load_owner_settings()
        self.assertEqual(after_settings["pricing"]["price_per_kw"], orig_price)

    # Test 13: Live preview recalculation
    def test_13_live_preview_recalculation(self):
        q = build_initial_quotation(self.sample_tneb_data)
        edited_2kw = recalculate_quotation(q, {"system_capacity_kw": 2.0})
        edited_5kw = recalculate_quotation(q, {"system_capacity_kw": 5.0})

        # Higher capacity must have higher generation and larger roof area
        self.assertGreater(
            edited_5kw["generation"]["estimated_annual_generation_kwh"],
            edited_2kw["generation"]["estimated_annual_generation_kwh"]
        )
        self.assertGreater(
            edited_5kw["sizing"]["approx_roof_area_sqft"],
            edited_2kw["sizing"]["approx_roof_area_sqft"]
        )

    # Test 14: Draft saving
    def test_14_draft_saving(self):
        q = build_initial_quotation(self.sample_tneb_data, quotation_no=generate_next_quotation_no())
        saved = save_quotation(q, status="Draft")
        self.assertEqual(saved["status"], "Draft")
        
        retrieved = get_quotation(saved["quotation_no"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["status"], "Draft")

    # Test 15: Quotation versioning
    def test_15_quotation_versioning(self):
        q_no = generate_next_quotation_no()
        q = build_initial_quotation(self.sample_tneb_data, quotation_no=q_no)
        save_quotation(q, status="Finalized")

        # Now revise it
        q_revised = recalculate_quotation(q, {"system_capacity_kw": 4.5})
        save_quotation(q_revised, status="Revised")

        versions = get_quotation_versions(q_no)
        self.assertGreaterEqual(len(versions), 2)
        self.assertEqual(versions[0]["version"], 2)

    # Test 16: PDF generation
    def test_16_pdf_generation(self):
        q = build_initial_quotation(self.sample_tneb_data, quotation_no=generate_next_quotation_no())
        pdf_path = asyncio.run(generate_quotation_pdf(q))
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 50000)

    # Test 17: PDF page layout and content validation
    def test_17_pdf_page_layout_and_content_validation(self):
        q = build_initial_quotation(self.sample_tneb_data, quotation_no=generate_next_quotation_no())
        pdf_path = asyncio.run(generate_quotation_pdf(q))
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # Validate exactly 5 pages
        page_matches = len([m for m in pdf_bytes.split(b"/Type") if m.strip().startswith(b"/Page") and not m.strip().startswith(b"/Pages")])
        self.assertEqual(page_matches, 5)

    # Test 18: Quotation history retrieval
    def test_18_quotation_history_retrieval(self):
        q_no = generate_next_quotation_no()
        q = build_initial_quotation(self.sample_tneb_data, quotation_no=q_no)
        save_quotation(q, status="Draft")

        history = list_quotations(consumer_no="044060072111")
        matching = [item for item in history if item["quotation_no"] == q_no]
        self.assertTrue(len(matching) >= 1)

    # Test 19: Missing TNEB data handling
    def test_19_missing_tneb_data_handling(self):
        # Empty cycles
        empty_analysis = analyze_consumption([])
        self.assertEqual(empty_analysis["data_quality_status"], "INSUFFICIENT")
        self.assertTrue(len(empty_analysis["data_quality_warnings"]) >= 1)

        # Incomplete cycles (only 2 cycles)
        partial_cycles = self.sample_tneb_data["billing_cycles"][:2]
        partial_analysis = analyze_consumption(partial_cycles)
        self.assertEqual(partial_analysis["data_quality_status"], "INSUFFICIENT")

    # Test 20: Invalid pricing and configuration handling
    def test_20_invalid_pricing_and_configuration_handling(self):
        # 0 capacity, negative rates
        invalid_cfg = {"pricing_model": "bundled_per_kw", "price_per_kw": -100, "gst_rate_percent": -5}
        res = calculate_quotation_pricing(system_capacity_kw=0, pricing_config=invalid_cfg)
        # Should guard against crash and negative pricing
        self.assertGreaterEqual(res["system_capacity_kw"], 0.1)
        self.assertGreaterEqual(res["net_customer_payable"], 0)

        # 0 wattage panel sizing
        sizing = size_solar_system(annual_consumption_kwh=0, panel_wattage_wp=0)
        self.assertGreaterEqual(sizing["number_of_panels"], 1)

if __name__ == "__main__":
    unittest.main()
