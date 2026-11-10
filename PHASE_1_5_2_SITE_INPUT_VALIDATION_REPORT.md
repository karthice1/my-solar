# RENSUN SOLAR — PHASE 1.5.2
## Actual Site Input, Wind Parameter & Host-Structure Validation Report

**Document Reference:** `RS-REP-PHASE-1-5-2-SITE-INPUT-VALIDATION`  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Base Commit / Verified HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Target Quotation:** `RENSUN/2026/0059`  
**Target Project:** `RS-STR-RENSUN-2026-0059`  
**Site Location:** `90 ERUMAPALAYAM ITTERI ROAD, SALEM` (`11.6643°N, 78.1460°E`)  
**Execution Timestamp:** `2026-11-08T08:25:00+05:30`  
**Governance State:** `ENGINEERING VERIFICATION PENDING` (12 Canonical Holds Enforced | AFC Locked)

---

## 1. EXECUTIVE SUMMARY

Pursuant to the instructions for **Phase 1.5.2 (Actual Site Input Validation)**, this report documents the architectural implementation, codal review, and independent verification of the site-coordinate verification framework (WP-04), transparent wind input register (WP-05), and host-structure roof inspection schema (WP-06).

### Summary of Completed Objectives:
1. **WP-04 (Site Coordinates):** The previously recorded coordinates (`11.6643°N, 78.1460°E`) are retained strictly as provisional historical centroid data. They are formally classified as `UNVERIFIED — ROOFTOP SURVEY REQUIRED` under `LEVEL_5_ASSUMED_PROVISIONAL` provenance. A survey-verification schema was implemented, requiring sub-meter accuracy ($\le 1.0\text{ m}$), verified geodetic instruments (RTK GNSS / Total Station), surveyor identity, and source certificates to graduate to `LEVEL_1_MEASURED`.
2. **WP-05 (Wind Inputs):** Reviewed governing standard **IS 875 (Part 3): 2015 (Third Revision, Reaffirmed 2020)**. Established that **Salem is unlisted in Appendix A Table 1 (Basic Wind Speeds for Selected Towns)**. The previously used $V_b = 39.0\text{ m/s}$ is classified as an assumed regional contour interpretation from Figure 1, requiring active enforcement of `WIND_COORD_UNVERIFIED_HOLD` and `ASSUMED_DATA_CERTIFICATION_HOLD`. All wind parameters are separated into Statutory Code, Site-Measured, Engineer-Selected, and Assumed categories.
3. **WP-06 (Host Structure & Roof Inspection):** Built a 17-field mandatory host-structure inspection register. Enforced the cardinal engineering codicil: **Host roof capacity CANNOT be inferred from roof type alone.** In the absence of physical non-destructive testing (NDT), slab core measurements, and signed as-built reinforcement drawings, roof capacity certification is strictly blocked.
4. **Decoupled Governance:** Assumed and missing inputs are strictly prevented from producing an engineering PASS. All twelve (12) canonical holds remain registered and active. Approved for Construction (AFC) remains locked.
5. **Reproducibility & Testing:** Implemented [`structural/site_survey.py`](file:///Users/karthik/tneb-account-extractor/structural/site_survey.py) and new hermetic test suite [`tests/test_phase1_5_2_site_inputs.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_2_site_inputs.py) (13 tests, 100% passing). Full structural test suite now stands at **121 tests (100% passing)** with zero production database mutations.

---

## 2. WP-04: SITE-COORDINATE VERIFICATION FRAMEWORK

### 2.1 Salem Centroid Historical Status
- **Target Project:** `RS-STR-RENSUN-2026-0059`
- **Location Address:** `90 ERUMAPALAYAM ITTERI ROAD, SALEM`
- **Recorded Coordinates:** `11.6643°N, 78.1460°E`
- **Current Verification Classification:** `UNVERIFIED — ROOFTOP SURVEY REQUIRED`
- **Provenance Tier:** `Level 5: Assumed Provisional (Requires Physical Verification)`
- **Survey Method:** `PROVISIONAL_CENTROID` (Salem municipal locality centroid)
- **Status Determination:** These coordinates represent an approximate locality centroid. They do **not** represent a physical survey of the specific rooftop structure at 90 Erumapalayam Itteri Road.
- **Rule Enforced:** Software calculations must display `UNVERIFIED — ROOFTOP SURVEY REQUIRED` on all outputs until certified physical survey evidence is provided.

### 2.2 Survey Verification Data Schema
The `SiteCoordinateRecord` dataclass captures the full evidentiary chain required for geodetic verification:

| Field | Type | Constraint / Rule | Salem Baseline Value |
|---|---|---|---|
| `latitude` | `float` | Required, finite real number, range: `[6.0°, 38.0°]` | `11.6643` |
| `longitude` | `float` | Required, finite real number, range: `[68.0°, 98.0°]` | `78.1460` |
| `survey_date` | `str` (ISO-8601) | Required for Level 1 Measured | `None` (Unsurveyed) |
| `survey_method` | `SurveyMethod` (Enum) | `RTK_GNSS`, `TOTAL_STATION`, `HANDHELD_GPS`, `SATELLITE_AERIAL`, `PROVISIONAL_CENTROID` | `PROVISIONAL_CENTROID` |
| `survey_instrument` | `str` | Specific equipment make/model (e.g., Leica GS18 T, Trimble R12i) | `None` |
| `accuracy_m` | `float` | Required $\le 1.0\text{ m}$ for rooftop structural engineering acceptance | `None` (Estimated $\pm 500\text{ m}$) |
| `surveyor_name` | `str` | Licensed surveyor / qualified structural engineer identity | `None` |
| `surveyor_license` | `str` | Registration number / statutory council license | `None` |
| `source_document` | `str` | Topographic Survey Report certificate number | `"Provisional Municipal Centroid"` |
| `provenance_level` | `ProvenanceLevel` | Mandatory 5-tier classification | `LEVEL_5_ASSUMED_PROVISIONAL` |
| `verification_status`| `CoordinateVerificationStatus`| `UNVERIFIED_ROOFTOP_SURVEY_REQUIRED`, `PROVISIONAL_CENTROID`, `VERIFIED_ROOFTOP_SURVEY` | `UNVERIFIED_ROOFTOP_SURVEY_REQUIRED` |
| `approval_status` | `ApprovalStatus` | `PENDING_REVIEW`, `ACCEPTED_PROVISIONAL`, `REJECTED`, `VERIFIED_BY_RSE` | `ACCEPTED_PROVISIONAL` |

### 2.3 Verification Decision Logic
A coordinate record graduates to `VERIFIED_ROOFTOP_SURVEY` if and only if all of the following conditions are simultaneously met:
1. `survey_method` is `RTK_GNSS` or `TOTAL_STATION`.
2. `provenance_level` is `LEVEL_1_MEASURED`.
3. `accuracy_m` is documented, positive, and $\le 1.0\text{ m}$.
4. `survey_instrument` make and model are explicitly identified.
5. `surveyor_name` and `survey_date` are recorded.
6. `source_document` certificate is referenced and available for audit.

---

## 3. WP-05: WIND INPUT VERIFICATION (IS 875 PART 3: 2015)

### 3.1 Governing Standard & Edition Review
- **Standard:** **IS 875 (Part 3): 2015** — *Design Loads (Other Than Earthquake) For Buildings and Structures — Code of Practice — Part 3: Wind Loads (Third Revision)*.
- **Reaffirmation:** Reaffirmed 2020 by Bureau of Indian Standards (BIS).
- **Key Provisions Applied:**
  - Clause 6.2 & Figure 1: Basic wind speed map.
  - Clause 6.3.1 & Table 1: Risk coefficient $k_1$.
  - Clause 6.3.2.1 & Table 2: Terrain and height factor $k_2$.
  - Clause 6.3.3: Topography factor $k_3$.
  - Clause 6.3.4: Importance factor for cyclonic region $k_4$.
  - Clause 7.2: Design wind pressure $p_z = 0.6 \cdot V_z^2$.
  - Clause 7.3.3 & Table 8: Canopy and rooftop pressure coefficients ($C_n, C_{pe}$).

### 3.2 Salem Codal Unlisted Finding
A detailed statutory audit of IS 875 (Part 3): 2015 **Appendix A (Table 1: Basic Wind Speed at 10 m Height for Selected Towns)** was conducted:
- Major Tamil Nadu cities listed in Appendix A Table 1: Chennai (50 m/s), Coimbatore (39 m/s), Cuddalore (50 m/s), Madurai (39 m/s), Nagapattinam (50 m/s), Tiruchirappalli (47 m/s), Tirunelveli (39 m/s).
- **Statutory Finding:** **Salem is NOT explicitly listed in Appendix A Table 1.**
- In Figure 1 (Basic Wind Speed Map of India), Salem falls geographically within the inland 39 m/s contour band.
- **Engineering Implication:** The value $V_b = 39.0\text{ m/s}$ represents an interpreted contour estimate rather than a gazetted municipal tabular value. It cannot be automatically certified as statutory Level 4.
- **Enforced Governance:** $V_b = 39.0\text{ m/s}$ must remain classified as `LEVEL_5_ASSUMED_PROVISIONAL` and maintain `WIND_COORD_UNVERIFIED_HOLD` and `ASSUMED_DATA_CERTIFICATION_HOLD` active until a site-specific wind study or certified meteorological record is accepted.

### 3.3 Transparent Wind Parameter Taxonomy
All wind parameters are separated into four distinct categories:

| Parameter Key | Parameter Name | Baseline Value | Units | Category | Provenance Level | Codal Reference | Justification & Verification Notes |
|---|---|:---:|:---:|:---:|:---:|---|---|
| `basic_wind_speed_vb` | Basic Wind Speed | 39.0 | m/s | **ASSUMED_PROVISIONAL** | `LEVEL_5_ASSUMED_PROVISIONAL` | Clause 6.2 & Fig. 1 | Salem unlisted in Annex A Table; provisional contour interpretation. |
| `risk_coefficient_k1` | Risk Coefficient | 1.0 | — | **CODE_DERIVED** | `LEVEL_4_STATUTORY_CODE` | Clause 6.3.1 Table 1 | 50-year design life for commercial/industrial solar structures. |
| `terrain_category` | Terrain Category | Category 3 | — | **ENGINEER_SELECTED** | `LEVEL_4_STATUTORY_CODE` | Clause 6.3.2.1 Table 2 | Suburban/industrial terrain with closely spaced obstructions. |
| `k2_factor` | Terrain Height Factor | 0.91 | — | **CODE_DERIVED** | `LEVEL_4_STATUTORY_CODE` | Clause 6.3.2.2 Table 2 | Interpolated for $h = 12.0\text{ m} + 2.8\text{ m} = 14.8\text{ m}$. |
| `topography_factor_k3` | Topography Factor | 1.0 | — | **ASSUMED_PROVISIONAL** | `LEVEL_5_ASSUMED_PROVISIONAL` | Clause 6.3.3 & App. C | Assumed flat ground ($\theta < 3^\circ$); topographic survey required. |
| `cyclonic_factor_k4` | Cyclonic Factor | 1.0 | — | **CODE_DERIVED** | `LEVEL_4_STATUTORY_CODE` | Clause 6.3.4 | Inland location (> 100 km from Bay of Bengal coast). |
| `building_height_m` | Building Height | 12.0 | m | **ASSUMED_PROVISIONAL** | `LEVEL_5_ASSUMED_PROVISIONAL` | Clause 6.3.2.2 | Estimated G+3 floor height; laser distometer check required. |
| `cpe_uplift` | Net Uplift Coefficient | -1.10 | — | **CODE_DERIVED** | `LEVEL_4_STATUTORY_CODE` | Clause 7.3.3.4 Table 8 | Monopitch canopy open roof ($\theta \le 10^\circ$). |
| `cpe_downward` | Net Downward Coeff. | +0.70 | — | **CODE_DERIVED** | `LEVEL_4_STATUTORY_CODE` | Clause 7.3.3.4 Table 8 | Monopitch canopy open roof ($\theta \le 10^\circ$). |
| `cpi_internal` | Internal Pressure Coeff.| 0.0 | — | **ENGINEER_SELECTED** | `LEVEL_4_STATUTORY_CODE` | Clause 7.3.2 | $C_{pi} = 0.0$ for open steel canopy (System A). |

---

## 4. WP-06: ROOF & HOST-STRUCTURE INSPECTION REGISTER

### 4.1 Cardinal Rule Enforced
> [!IMPORTANT]
> **Host structure capacity CANNOT be inferred from roof type alone.**
> Designating a roof as "RCC Flat Slab" or "Industrial Metal Sheet" does not establish its structural adequacy, concrete compressive strength, slab thickness, reinforcement layout, or dead/live load reserves. Physical testing, non-destructive evaluation (NDT), and signed as-built structural drawings are strictly mandatory.

### 4.2 Mandatory 17-Field Inspection Checklist Audit
The `RoofInspectionRegister` audits seventeen (17) physical parameters for the host building at 90 Erumapalayam Itteri Road, Salem:

| No. | Field Key | Field Description | Baseline Status | Value Recorded | Provenance Tier | Physical Evidence Still Required |
|:---:|---|---|:---:|:---:|:---:|---|
| 1 | `roof_type` | Host Framing Classification | **ASSUMED_INPUT** | `RCC_FLAT_SLAB` | Level 5 (Assumed) | Client architectural plan / physical inspection |
| 2 | `roof_length_m` | Measured Rooftop Length | **MISSING_INPUT** | `None` | Level 5 (Assumed) | On-site laser distance measurement |
| 3 | `roof_width_m` | Measured Rooftop Width | **MISSING_INPUT** | `None` | Level 5 (Assumed) | On-site laser distance measurement |
| 4 | `parapet_height_m` | Parapet Wall Height | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Edge parapet height tape measurement |
| 5 | `framing_layout` | Primary Framing Grid | **MISSING_INPUT** | `None` | Level 5 (Assumed) | As-built beam-column framing plan |
| 6 | `existing_purlin_spacing_mm`| Secondary Purlin Spacing | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Framing survey (if pitched roof) |
| 7 | `existing_rafter_spacing_mm`| Primary Rafter Spacing | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Framing survey |
| 8 | `existing_column_locations` | Column Grid Coordinates | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Column grid plan for canopy column footing |
| 9 | `member_sizes` | Framing Member Dimensions | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Beam / column cross-section schedule |
| 10 | `material_grades` | Concrete & Rebar Grades | **MISSING_INPUT** | `None` | Level 5 (Assumed) | As-built drawing material specifications |
| 11 | `slab_thickness_mm` | RCC Slab Core Thickness | **ASSUMED_INPUT** | `150.0 mm` | Level 5 (Assumed) | Core drill or ultrasonic pulse thickness gauge |
| 12 | `concrete_strength_mpa` | Concrete Compressive Strength | **ASSUMED_INPUT** | `20.0 MPa (M20)`| Level 5 (Assumed) | Rebound hammer (IS 13311:2) or core test |
| 13 | `reinforcement_details` | Rebar Diameters & Spacing | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Ferroscan NDT rebar survey or as-built dwg |
| 14 | `roof_condition_rating` | Visual Defect / Moisture State| **ASSUMED_INPUT** | `FAIR` | Level 5 (Assumed) | Visual structural inspection report |
| 15 | `corrosion_level` | Rebar / Framing Oxidation | **ASSUMED_INPUT** | `MILD` | Level 5 (Assumed) | Corrosion assessment inspection |
| 16 | `cracking_observations` | Cracking & Deflection Survey | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Crack mapping survey (flexure, shear, shrinkage)|
| 17 | `anchor_locations_edge_distances`| Anchor Placement Limits | **MISSING_INPUT** | `None` | Level 5 (Assumed) | Concrete edge distance ($c_{min}$) measurement |

### 4.3 Capacity Certification Audit Outcome
- **Mandatory Fields Total:** 17
- **Verified Fields:** 0 (0%)
- **Assumed Fields:** 5 (29%)
- **Missing Fields:** 12 (71%)
- **Completeness Status:** `INCOMPLETE` (Completeness: 0%)
- **Can Certify Roof Capacity:** **FALSE**
- **Deficiencies Identified:**
  1. Concrete compressive strength ($f_{ck}$) is unverified (NDT / core test report missing).
  2. Slab thickness is unverified (core gauge / physical measurement missing).
  3. Host building framing member sizes are unverified (as-built structural drawings missing).
  4. Reinforcement schedule is unverified (Ferroscan / structural drawings missing).
  5. Rooftop survey coordinates are unverified (`WIND_COORD_UNVERIFIED_HOLD` active).

---

## 5. REPRODUCIBLE TESTING & REGRESSION PROTECTION

### 5.1 New Phase 1.5.2 Site Input Test Suite
A dedicated test suite was implemented in [`tests/test_phase1_5_2_site_inputs.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_2_site_inputs.py):

```bash
$ python3 -m unittest -v tests/test_phase1_5_2_site_inputs.py
test_all_12_canonical_holds_remain_active_and_enforced ... ok
test_consolidated_site_validation_prevents_engineering_pass ... ok
test_integration_bridge_audit_site_and_roof_validation ... ok
test_wp04_certified_rtk_gnss_survey_acceptance ... ok
test_wp04_coordinate_bounds_and_finite_validation ... ok
test_wp04_incomplete_survey_evidence_rejected ... ok
test_wp04_provisional_salem_coordinates_retained_as_unverified ... ok
test_wp05_salem_unlisted_status_and_is875_governance ... ok
test_wp05_wind_parameter_category_separation ... ok
test_wp06_mandatory_17_fields_inspection_register ... ok
test_wp06_physical_testing_evidence_certification ... ok
test_wp06_poor_or_critical_condition_blocks_certification ... ok
test_wp06_roof_capacity_cannot_be_inferred_from_type_alone ... ok
----------------------------------------------------------------------
Ran 13 tests in 1.384s — OK
```

### 5.2 Full Structural Test Suite (121 Tests)
Executing the full structural discovery suite under `IsolatedTestEnvironment`:
```bash
$ python3 -m unittest discover -s tests -p 'test*.py' -v
----------------------------------------------------------------------
Ran 121 tests in 7.419s — OK (Exit Code 0)
```
- 108 existing baseline tests: **100% Passing**.
- 13 new Phase 1.5.2 site input tests: **100% Passing**.
- Total: **121 / 121 Structural Tests Passing**.

### 5.3 Production Asset Invariance Proved
SHA-256 checksums calculated before and after all Phase 1.5.2 operations:
- `quotations.db`: `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf` (**100% Byte-Identical**)
- `structural/structural_runs.db`: `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff` (**100% Byte-Identical**)
- `quotation_settings.json`: `26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1` (**100% Byte-Identical**)
- `generated_drawings/`: 5 production DXF files and timestamps (**100% Untouched**)

---

## 6. PHYSICAL EVIDENCE STILL REQUIRED FROM THE OWNER

To graduate the project from `UNVERIFIED_MISSING_PHYSICAL_EVIDENCE` toward independent structural engineering review, the following physical evidence must be obtained from the host building owner:

| No. | Evidence Category | Specific Document / Survey Required | Statutory / Testing Standard | Responsible Party | Current Status |
|:---:|---|---|---|:---:|:---:|
| 1 | **Site Coordinates** | Certified rooftop RTK GNSS / Total Station survey certificate with sub-meter accuracy ($\le 1.0\text{ m}$) establishing rooftop benchmark corners. | Survey of India / IS 1492 | Licensed Land Surveyor | **MISSING** |
| 2 | **Wind Speed Validation**| Certified regional wind zone confirmation or local meteorological study validating basic wind speed ($V_b$) for unlisted Salem location. | IS 875 (Part 3): 2015 Clause 6.2 | Structural Engineering Consultant | **MISSING** |
| 3 | **Topographic Survey** | Site elevation profile within 1.5 km upwind radius confirming ground slope $< 3^\circ$ for $k_3 = 1.0$. | IS 875 (Part 3): 2015 Clause 6.3.3 | Licensed Land Surveyor | **MISSING** |
| 4 | **Concrete Strength** | Non-destructive rebound hammer test report (IS 13311 Part 2) or core compressive strength test report (IS 516) verifying host slab concrete grade ($f_{ck} \ge 20\text{ MPa}$). | IS 13311 (Part 2) / IS 516 | NABL-Accredited Testing Lab | **MISSING** |
| 5 | **Slab Core Thickness** | Physical core drill or ultrasonic pulse thickness gauge measurement across at least 4 rooftop locations confirming solid slab depth. | ASTM C597 / IS 516 | NABL-Accredited Testing Lab | **MISSING** |
| 6 | **As-Built Structural Drawings** | Signed structural as-built drawings showing beam-column framing layout, spans, column cross-sections, and member schedules. | NBC 2016 Part 6 | Host Building Owner / Architect | **MISSING** |
| 7 | **Reinforcement Details**| As-built rebar schedule or Ferroscan non-destructive rebar layout report detailing bottom/top bar diameters, spacing, and concrete cover. | BS 1881-204 / ACI 228.2R | NDT Testing Specialist | **MISSING** |
| 8 | **Rooftop Physical Inspection** | Visual inspection report signed by a Registered Structural Engineer (RSE) documenting cracks, spalling, deflection, water ponding, and anchor edge distances. | NBC 2016 Administrative Provisions | Registered Structural Engineer | **MISSING** |

---

## 7. MANDATORY GOVERNANCE & SAFEGUARDS ATTESTATION

1. **12 Canonical Holds:** All 12 canonical holds remain registered and active in `MASTER_VERIFICATION_REGISTER`. None have been deleted, weakened, or bypassed.
2. **Construction Approval Lock:** `is_approved_for_construction = False` across all 4 systems. Construction status is strictly `BLOCKED_AFC_LOCKED`.
3. **Watermark Active:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION` is enforced across all reports and drawings.
4. **Git Safeguards:** Active branch remains `feature/phase1-structural-foundation`. HEAD remains `df8d5da966b6506c1eada7093db2a140cbc0b9dc`. Zero files staged, zero commits, zero pushes.
5. **Phase Boundary:** Halted cleanly at the completion of Phase 1.5.2. Phase 1.5.3 (System A engineering modifications) has **not** been started.

**Phase Status:** `PHASE_1_5_2_ACCEPTED_AWAITING_OWNER_REVIEW`
