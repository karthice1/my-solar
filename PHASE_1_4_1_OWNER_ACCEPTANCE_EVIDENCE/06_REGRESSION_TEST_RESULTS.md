# RENSUN SOLAR — PHASE 1.4.1 INDEPENDENT OWNER ACCEPTANCE EVIDENCE
## AUDIT REPORT 06: AUTOMATED REGRESSION TESTING RESULTS

**Auditor:** Independent Engineering Verification Auditor  
**Date:** 2026-11-07  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Working Branch:** `feature/phase1-structural-foundation`  
**Base Commit:** `df8d5da` | **Head Commit:** `df8d5da`  
**Test Framework:** Python `unittest`  

---

### 1. Executive Summary & Audit Scope

This audit report documents the fresh, independent execution of the entire automated regression testing suite across all structural and commercial subsystems.

The objectives of this test run are:
1. Validate that the reported 100/100 pass rate is mathematically genuine and reproducible.
2. Confirm that commercial quotation logic, TNEB consumer data ingestion, and 5-page Playwright PDF generation remain 100% operational.
3. Verify that Phase 1.4.1 UI refinement additions (Salem unlisted site provenance `test_13`, authoritative hold standards `test_14`) execute cleanly without regressions.
4. Confirm zero skipped tests, zero failures, and zero errors.

---

### 2. Comprehensive Classification Summary

| Check ID | Verification Area | Target Test Suite | Finding Classification | Auditor Notes |
| :--- | :--- | :--- | :--- | :--- |
| **TEST-01** | Structural Web UI Suite | `tests/test_structural_web_ui.py` | **VERIFIED** | 14/14 passed; verifies API, Salem provenance, standards column. |
| **TEST-02** | Quotation-Structural Integration | `tests/test_quotation_structural_integration.py` | **VERIFIED** | 11/11 passed; verifies bridging, holds gatekeeper, and quotation link. |
| **TEST-03** | Structural SQLite Persistence | `tests/test_structural_database.py` | **VERIFIED** | 20/20 passed; verifies immutable snapshot, runs DB, foreign keys. |
| **TEST-04** | Structural Foundation Mechanics | `tests/test_structural_foundation.py` | **VERIFIED** | 22/22 passed; verifies Systems A, B, C, D closed-form solvers. |
| **TEST-05** | Structural CLI Tools | `tests/test_structural_cli.py` | **VERIFIED** | 13/13 passed; verifies CLI commands, options, and governance blocks. |
| **TEST-06** | Commercial Quotation Engine | `test_quotation_system.py` | **VERIFIED** | 20/20 passed; verifies pricing, GST, Playwright PDF, TNEB data. |
| **TEST-07** | Overall Suite Pass Rate | Full test suite execution | **VERIFIED** | **100/100 tests passed (100% pass rate, 0 failures, 0 errors).** |

---

### 3. Test Execution Command & Environment

The test suite was executed via the standard Python unittesting runner against the active branch:

```bash
cd /Users/karthik/tneb-account-extractor && python3 -m unittest -v \
  tests/test_structural_web_ui.py \
  tests/test_quotation_structural_integration.py \
  tests/test_structural_database.py \
  tests/test_structural_foundation.py \
  tests/test_structural_cli.py \
  test_quotation_system.py
```

- **Python Version**: Python 3.11+
- **Execution Mode**: Synchronous / In-process
- **Operating System**: macOS (Darwin 24.6.0)
- **Execution Timestamp**: 2026-11-07 12:33:55 IST
- **Duration**: 14.074 seconds
- **Exit Code**: 0 (Clean OK)

---

### 4. Suite-by-Suite Test Execution Breakdown

```
========================================================================================================================
AUTOMATED REGRESSION TEST SUITE BREAKDOWN
========================================================================================================================
Test Suite File                                  | Total Tests | Passed | Failed | Errors | Skipped | Pass Rate
-------------------------------------------------+-------------+--------+--------+--------+---------+-----------
tests/test_structural_web_ui.py                  | 14          | 14     | 0      | 0      | 0       | 100.0%
tests/test_quotation_structural_integration.py   | 11          | 11     | 0      | 0      | 0       | 100.0%
tests/test_structural_database.py                | 20          | 20     | 0      | 0      | 0       | 100.0%
tests/test_structural_foundation.py              | 22          | 22     | 0      | 0      | 0       | 100.0%
tests/test_structural_cli.py                     | 13          | 13     | 0      | 0      | 0       | 100.0%
test_quotation_system.py                         | 20          | 20     | 0      | 0      | 0       | 100.0%
-------------------------------------------------+-------------+--------+--------+--------+---------+-----------
TOTAL CONSOLIDATED SUITE                         | 100         | 100    | 0      | 0      | 0       | 100.0%
========================================================================================================================
```

---

### 5. Detailed Test Inventory & Individual Test Results

#### A. `tests/test_structural_web_ui.py` (14 Tests)
1. `test_01_home_page_renders_structural_ui`: Main single-page application renders structural views and components. `[PASS]`
2. `test_02_list_structural_projects_endpoint`: `GET /api/structural/projects` returns enriched project list and metadata. `[PASS]`
3. `test_03_projects_search_and_filters`: Search query and multi-parameter filtering on structural projects. `[PASS]`
4. `test_04_create_project_and_canonical_enforcement`: `POST /api/structural/projects` creates canonical projects and blocks non-canonical ones. `[PASS]`
5. `test_05_get_project_details_and_completeness`: `GET /api/structural/projects/{id}` returns input sections and completeness. `[PASS]`
6. `test_06_update_project_inputs`: `PUT /api/structural/projects/{id}/inputs` updates parameters and lineage. `[PASS]`
7. `test_07_calculate_project_assessment`: `POST /api/structural/projects/{id}/calculate` executes multi-code checks. `[PASS]`
8. `test_08_run_history_and_immutable_snapshot_inspection`: Run history and auditability via frozen immutable snapshot inspection. `[PASS]`
9. `test_09_verification_holds_dashboard`: `GET /api/structural/holds` returns all 12 canonical holds and enforces AFC block. `[PASS]`
10. `test_10_one_click_deliverables_download`: 1-click download endpoints for report, DXF, summary, inputs, and sections. `[PASS]`
11. `test_11_strict_afc_gatekeeper_enforcement`: Requesting AFC / approved deliverables strictly returns HTTP 403 Forbidden. `[PASS]`
12. `test_12_quotation_builder_structural_card_integration`: Seamless quotation linking without impacting commercial pricing. `[PASS]`
13. `test_13_salem_site_provenance_and_unlisted_flag`: Salem site coordinates, codal wind speed, and unlisted provenance. `[PASS]`
14. `test_14_hold_register_standards_and_member_results`: All 12 holds have standards and calculation returns member results. `[PASS]`

#### B. `tests/test_quotation_structural_integration.py` (11 Tests)
15. `test_calculation_invocation_and_summary`: Complete inputs execute structural workflows and persist calculation run. `[PASS]`
16. `test_canonical_12_holds_identity_and_presence`: All 12 original canonical verification holds exist under exact identifiers. `[PASS]`
17. `test_hold_gate_enforcement_in_apis`: FastAPI endpoints enforce hold gates and forbid AFC bypass. `[PASS]`
18. `test_http_api_structural_integration_flow`: FastAPI endpoints return correct status and artifacts. `[PASS]`
19. `test_idempotent_project_linking_prevents_duplicates`: Repeated linking calls return existing project without duplicates. `[PASS]`
20. `test_input_completeness_audit`: Bridge distinguishes complete vs incomplete input status. `[PASS]`
21. `test_input_transfer_maps_module_and_geometry`: Transfers module specs and geometry without loss. `[PASS]`
22. `test_pdf_integration_remains_intact`: 5-page Playwright PDF generation executes without corruption. `[PASS]`
23. `test_quotation_data_protection`: Quotation numbers, pricing, and GST are preserved. `[PASS]`
24. `test_quotation_status_reflects_assessment`: Structural assessment summary embeds into quotation draft. `[PASS]`
25. `test_structural_failure_does_not_corrupt_quotation`: Failed structural calculation does not invalidate commercial quote. `[PASS]`

#### C. `tests/test_structural_database.py` (20 Tests)
26. `test_db_initialization_and_schema_version`: Database tables created and schema migrated to version 4. `[PASS]`
27. `test_foreign_key_constraints`: Foreign key enforcement blocks orphaned child rows. `[PASS]`
28. `test_create_and_get_project`: Canonical project insertion and retrieval. `[PASS]`
29. `test_project_code_uniqueness`: Duplicate project codes rejected with constraint error. `[PASS]`
30. `test_site_inputs_upsert_and_fetch`: Coordinates, wind speed, terrain category upserted cleanly. `[PASS]`
31. `test_module_spec_upsert_and_fetch`: Module dimensions, wattage, and dead loads preserved. `[PASS]`
32. `test_geometry_upsert_and_fetch`: Rows, columns, tilt angle, and spacings persisted. `[PASS]`
33. `test_material_upsert_and_fetch`: Material yield strength, tensile strength, and elastic modulus. `[PASS]`
34. `test_section_upsert_and_fetch`: Section properties (area, mass, Ixx, Iyy, Zpx, Zpy). `[PASS]`
35. `test_input_completeness_validation`: Comprehensive audit of required fields per mounting system. `[PASS]`
36. `test_input_snapshot_generation`: Frozen immutable JSON snapshot capturing complete input state. `[PASS]`
37. `test_calculation_run_persistence`: Run records persisted with engine version and status. `[PASS]`
38. `test_calculation_results_persistence`: Member-level checks stored with Ed, Rd, ratio, clause. `[PASS]`
39. `test_run_reproducibility_verification`: Historical calculation verified against input snapshot. `[PASS]`
40. `test_active_holds_snapshot_integrity`: Active verification holds snapshot preserved bit-for-bit. `[PASS]`
41. `test_afc_flag_hardcoded_zero`: Column `is_approved_for_construction` hard-locked to 0. `[PASS]`
42. `test_drawing_records_persistence`: Drawing records persisted with preliminary watermark. `[PASS]`
43. `test_quotation_link_persistence`: Quotation number to structural project mapping. `[PASS]`
44. `test_audit_history_logging`: User actions, parameter edits, and calculation runs logged. `[PASS]`
45. `test_database_isolation`: Structural SQLite operations never touch commercial quotation DB. `[PASS]`

#### D. `tests/test_structural_foundation.py` (22 Tests)
46. `test_action_register_nominal_values`: IS 875 nominal values for dead, live, wind, and seismic actions. `[PASS]`
47. `test_load_combinations_uls_and_sls`: IS 800 Table 4 combinations (ULS-01 to ULS-06, SLS-01 to SLS-02). `[PASS]`
48. `test_materials_and_section_properties`: Structural steel and aluminium material specifications. `[PASS]`
49. `test_is875_wind_speed_and_pressure`: Design wind speed ($V_z$) and pressure ($p_z$) calculations. `[PASS]`
50. `test_aerodynamic_coefficients_canopy`: Multi-bay canopy net pressure coefficients ($C_n$). `[PASS]`
51. `test_purlin_sagging_flexure_uls01`: Purlin bending under distributed vs point live loads. `[PASS]`
52. `test_purlin_shear_capacity_uls01`: Purlin major-axis shear check under governing live load. `[PASS]`
53. `test_purlin_uplift_stress_reversal`: Net wind uplift flexure with 0.9 stabilizing dead load. `[PASS]`
54. `test_purlin_deflection_sls01`: Unfactored serviceability deflection vs $L/250$ limit. `[PASS]`
55. `test_workflow_system_a_elevated_canopy`: Multi-component evaluation (purlin, rafter, column). `[PASS]`
56. `test_system_a_rafter_simultaneous_live`: Combined array live and walkway live load cases. `[PASS]`
57. `test_system_a_column_axial_buckling`: Euler buckling, slenderness, and IS 800 Clause 7.1.2. `[PASS]`
58. `test_workflow_system_b_aluminium_rail`: Aluminium rail flexure and clamp capacity checks. `[PASS]`
59. `test_workflow_system_c_metal_sheet`: Standing-seam clamp tensile pull-out under wind uplift. `[PASS]`
60. `test_workflow_system_d_ballasted_sliding`: Ballast sliding resistance with zero adverse live load. `[PASS]`
61. `test_workflow_system_d_overturning_stability`: Overturning stability with stabilizing dead load. `[PASS]`
62. `test_master_verification_register_12_holds`: Exact 12 canonical verification holds presence. `[PASS]`
63. `test_hold_categories_and_authorities`: Hold categories (SITE, AERO, STRUCTURAL, DETAILING). `[PASS]`
64. `test_governance_block_construction_release`: Construction release blocked while holds remain active. `[PASS]`
65. `test_preliminary_watermark_enforcement`: Watermark string strictly present on all deliverables. `[PASS]`
66. `test_drawing_export_blocked_without_override`: Drawing release gatekeeper blocks unapproved exports. `[PASS]`
67. `test_governing_unity_ratio_calculation`: Maximum unity ratio and governing check identification. `[PASS]`

#### E. `tests/test_structural_cli.py` (13 Tests)
68. `test_cli_system_list_and_select`: CLI lists canonical mounting systems A, B, C, D. `[PASS]`
69. `test_cli_project_create_and_show`: CLI creates project and displays project attributes. `[PASS]`
70. `test_cli_project_list`: CLI lists existing projects with completeness and status. `[PASS]`
71. `test_cli_project_show_not_found`: CLI handles nonexistent project code with proper error code. `[PASS]`
72. `test_cli_set_site_valid_and_out_of_bounds`: CLI validates site parameters against bounds. `[PASS]`
73. `test_cli_set_module_and_geometry`: CLI updates module dimensions and array geometry. `[PASS]`
74. `test_cli_set_material_and_section`: CLI configures section designations and materials. `[PASS]`
75. `test_cli_calculate_validate_missing_vs_complete`: CLI blocks calculation when inputs are missing. `[PASS]`
76. `test_cli_calculate_loads`: CLI computes design wind pressure and action register. `[PASS]`
77. `test_cli_calculate_run_and_results`: CLI executes workflow and outputs member checks table. `[PASS]`
78. `test_cli_holds_list_show_and_check`: CLI lists active verification holds and explains standards. `[PASS]`
79. `test_cli_drawing_preview_and_export_dxf`: CLI generates DXF preview with preliminary watermark. `[PASS]`
80. `test_cli_drawing_export_approved_blocked_by_governance_gate`: Requesting `--require-approved` exits with code 2. `[PASS]`

#### F. `test_quotation_system.py` (20 Tests)
81. `test_01_loading_tneb_consumer_data`: Ingests real TNEB consumer data and billing records. `[PASS]`
82. `test_02_owner_settings_persistence`: Preserves owner quotation settings across sessions. `[PASS]`
83. `test_03_panel_wattage_configuration`: Configures mono-PERC and TOPCon module wattages. `[PASS]`
84. `test_04_solar_capacity_calculation`: Sizing solar capacity based on monthly energy units. `[PASS]`
85. `test_05_panel_quantity_calculation`: Computes exact module counts matching inverter capacity. `[PASS]`
86. `test_06_inverter_compatibility_checks`: Validates string voltage and inverter MPPT ranges. `[PASS]`
87. `test_07_pricing_calculation`: Calculates module, inverter, BOS, and installation pricing. `[PASS]`
88. `test_08_gst_calculation`: Computes 18% GST ($13,478.40$) with exact mathematical precision. `[PASS]`
89. `test_09_discount_calculation`: Evaluates customer promotional discounts without corruption. `[PASS]`
90. `test_10_subsidy_eligibility_handling`: Handles PM Surya Ghar Muft Bijli Yojana subsidy logic. `[PASS]`
91. `test_11_customer_specific_quotation_editing`: Allows customer-specific adjustments in quotation builder. `[PASS]`
92. `test_12_owner_defaults_remain_unchanged_after_edits`: Customer edits do not overwrite owner default profile. `[PASS]`
93. `test_13_live_preview_recalculation`: Dynamic live preview updates pricing on parameter edits. `[PASS]`
94. `test_14_draft_saving`: Saves draft quotation records into SQLite database. `[PASS]`
95. `test_15_quotation_versioning`: Increments quotation versioning upon edits. `[PASS]`
96. `test_16_pdf_generation`: Generates commercial quotation PDF using Playwright headless browser. `[PASS]`
97. `test_17_pdf_page_layout_and_content_validation`: Validates 5-page Playwright PDF structure and content. `[PASS]`
98. `test_18_quotation_history_retrieval`: Queries historical quotation database records. `[PASS]`
99. `test_19_missing_tneb_data_handling`: Gracefully handles partial or missing TNEB billing cycles. `[PASS]`
100. `test_20_invalid_pricing_and_configuration_handling`: Rejects negative prices and zero-capacity configurations. `[PASS]`

---

### 6. Auditor Sign-Off & Finding Classification

**Finding Classification: VERIFIED**  
- Fresh verbatim execution of all 100 tests completed in 14.074s.
- Pass rate is 100.0% (100 passed, 0 failed, 0 errors, 0 skipped).
- Zero tests modified or disabled to produce this result.
- Commercial quotation workflows and structural automation coexist with 100% test integrity.
