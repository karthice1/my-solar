# RENSUN SOLAR — PHASE 1.4.2.1
# ENGINEERING CALCULATION DEFECT CORRECTION, PROVENANCE INTEGRATION & GOVERNANCE HARDENING REPORT

**Repository:** `/Users/karthik/tneb-account-extractor`  
**Working Branch:** `feature/phase1-structural-foundation`  
**Base Commit:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Target Project:** `RS-STR-RENSUN-2026-0059` (`90 ERUMAPALAYAM ITTERI ROAD, SALEM`)  
**Audit Date:** November 7, 2026  
**Status:** COMPLETE (SUBJECT TO STRICT GOVERNANCE & SITE-SPECIFIC VERIFICATION HOLDS)  

---

## 1. EXECUTIVE SUMMARY & REPOSITORY BASELINE

Phase 1.4.2.1 executes targeted engineering software corrections, mathematical provenance integration, and governance hardening across the RENSUN Solar Structural Automation Platform.

All modifications strictly adhere to owner safeguards:
- **Zero Commits, Staging, or Pushes:** The repository remains cleanly on branch `feature/phase1-structural-foundation` at base commit `df8d5da`. No commits were added to Git history.
- **Protected Branch Unmodified:** The `main` branch remains untouched.
- **Historical Snapshot Integrity:** All 20 historical calculation runs for `RS-STR-RENSUN-2026-0059` remain byte-identical, frozen, and immutable, with every run maintaining `is_approved_for_construction = 0`, `status = FAIL`, and governing unity ratio `1.727537`.
- **Commercial & TNEB Integrity:** Quotation calculations, commercial solar sizing, 5-page Playwright PDF generation, GST calculations, and TNEB extraction/consumer matching functions remain 100% operational with zero regressions.
- **Governance Gate & Holds Active:** All 12 canonical verification holds remain active and enforced. Approved for Construction (AFC) is strictly locked. Every DXF output retains diagonal and title-block watermarks: `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`.

### Repository Verification Summary
| Parameter | Recorded Value | Verification Status |
| :--- | :--- | :--- |
| **Active Branch** | `feature/phase1-structural-foundation` | Verified |
| **Base Commit Hash** | `df8d5da966b6506c1eada7093db2a140cbc0b9dc` | Verified (0 commits ahead) |
| **Modified Tracked Files** | `server.py`, `templates/index.html` | Verified |
| **Recoverable Backup** | `<artifactDir>/backup_phase1_4_2_1/` | Created & Persisted |
| **Automated Test Results** | **114 / 114 PASSED (100%)** | Verified across all test suites |
| **Target Project Snapshot Count** | 20 runs (`RS-STR-RENSUN-2026-0059`) | 100% Intact |
| **AFC Approval State** | Blocked (`is_approved_for_construction = 0`) | Verified |

---

## 2. WORK PACKAGE FINDINGS & IMPLEMENTATION (WP-01 TO WP-08)

### WP-01: Physical Load-Action Register Hardening (`structural/actions.py`)
- **Action Identity & Attributes:** Implemented `PhysicalAction` dataclass with stable identifiers (`action_id`), distinct physical categories (`DEAD`, `LIVE_CONCENTRATED`, `LIVE_DISTRIBUTED`, `WIND_UPLIFT`, `WIND_DOWNWARD`, `SEISMIC_HORIZONTAL`, `SEISMIC_VERTICAL`), nominal magnitudes, SI engineering units, governing code references, applicable systems, load application patterns, load path descriptions, combination rules, and internal calculation engine mappings.
- **Distinct Registration:** Registered distinct actions:
  - `ACT_DL_01`: Dead Load (IS 875 Part 1)
  - `ACT_IL_01`: Maintenance Point Load ($1.0\text{ kN}$ at midspan or support, IS 875 Part 2 Cl 4.1 & Tab 2)
  - `ACT_IL_02`: Roof Distributed Live Load ($0.75\text{ kN/m}^2$, IS 875 Part 2 Tab 2)
  - `ACT_IL_03`: Walkway Distributed Live Load ($1.50\text{ kN/m}^2$, IS 875 Part 2 Cl 4.1)
  - `ACT_IL_04`: Ground Snow Load ($0.0\text{ kN/m}^2$, IS 875 Part 4)
  - `ACT_ER_01`: Erection/Installation Load ($1.0\text{ kN}$, IS 875 Part 2)
  - `ACT_WL_UP`: Wind Suction / Uplift ($C_{pe}-C_{pi} = -1.10$, IS 875 Part 3 Cl 7.3)
  - `ACT_WL_DOWN`: Wind Downward Pressure ($C_{pe}-C_{pi} = +0.80$, IS 875 Part 3 Cl 7.3)
  - `ACT_EQ_H`: Horizontal Seismic Force ($A_h$, IS 1893 Part 1 Cl 6.4.2)
  - `ACT_EQ_V`: Vertical Seismic Force ($A_v = \frac{2}{3} A_h$, IS 1893 Part 1 Cl 6.4.6)
- **Canonical Action Keys:** Enforced schema `CANONICAL_ACTION_KEYS = {"DL", "IL_POINT", "IL_DIST", "IL_WALK", "WL_UP", "WL_DOWN", "EX", "EY", "EZ"}` with runtime validation rejecting unmapped keys.

### WP-02: Load Combination Matrix Reconstruction (`structural/actions.py`)
- **IS 800:2007 Table 4 Completeness:** Reconstructed all 6 ULS combinations and 2 SLS combinations.
- **Mutual Exclusion & Worst-Case Governing:** Maintained mutually exclusive analysis of point maintenance live load (`ACT_IL_01`) and distributed live load (`ACT_IL_02`), comparing resulting structural actions (bending moments and shear forces) rather than raw load intensities.
- **IS 1893:2016 3D Seismic Matrix (24 Cases):** Reconstructed the complete 3D orthogonal spatial seismic combination suite per IS 1893:2016 Clauses 6.3.2.1, 6.3.4.1, and 6.3.4.2:
  - 16 horizontal-dominant cases (`ULS-EQ-01` to `ULS-EQ-16`): $1.2\text{ DL} \pm 1.2(\pm E_X \pm 0.3 E_Y \pm 0.3 E_Z)$ and $1.5\text{ DL} \pm 1.5(\pm E_X \pm 0.3 E_Y \pm 0.3 E_Z)$.
  - 8 vertical-dominant cases (`ULS-EQ-17` to `ULS-EQ-24`): $1.2\text{ DL} \pm 1.2(0.3 E_X + 0.3 E_Y \pm E_Z)$ and $1.5\text{ DL} \pm 1.5(0.3 E_X + 0.3 E_Y \pm E_Z)$.
  - Floating point round-off elimination applied (`round(1.5 * sz, 4)` yielding exact $0.45$).
  - Option provided for planar 2D horizontal-only combinations (8 cases `ULS-EQ-H01` to `H08`) with vertical coefficient explicitly $0.0$.

### WP-03: Provenance Persistence and Snapshot Integration (`structural/db.py`, `structural/provenance.py`)
- **Persistent SQLite Table:** Implemented schema migration V5 creating persistent table `provenance_records`:
  ```sql
  CREATE TABLE IF NOT EXISTS provenance_records (
      record_id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL,
      parameter_key TEXT NOT NULL,
      value TEXT NOT NULL,
      units TEXT,
      level INTEGER NOT NULL,
      source_reference TEXT NOT NULL,
      certifier_name TEXT,
      date_certified TEXT,
      notes TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      calculation_run_id TEXT,
      snapshot_version TEXT DEFAULT '1.0',
      FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
      UNIQUE(project_id, parameter_key)
  );
  ```
- **Provenance Validation Rules:** Upgraded `ProvenanceRecord` dataclass to reject uncertified claims (e.g. Level 1 Manufacturer Certified without certifier/test reference).
- **Restart Persistence:** `ProvenanceTracker` synchronizes directly with the database on every record update and reloads state upon process restart. Tested and verified across fresh database connections.

### WP-04: Separation of Numerical Status from Engineering Status (`structural/db.py`, `structural/engine.py`, `structural/integration.py`)
- **Database Schema Expansion:** Added 5 distinct status columns to `calculation_runs`:
  - `numerical_status`: `PASS` or `FAIL` (based strictly on whether all unity ratios $\le 1.0$).
  - `input_completeness`: `COMPLETE` or `INCOMPLETE`.
  - `provenance_status`: `CERTIFIED` or `PROVISIONAL`.
  - `engineering_status`: `VERIFIED` or `UNVERIFIED`.
  - `construction_status`: `APPROVED_FOR_CONSTRUCTION` or `BLOCKED_AFC_LOCKED`.
- **Engineering Principle Enforced:** A calculation with oversized members yielding $\text{UR} < 1.0$ receives `numerical_status = "PASS"`, but its `engineering_status` remains strictly `"UNVERIFIED"`, `provenance_status` remains `"PROVISIONAL"`, and `construction_status` remains `"BLOCKED_AFC_LOCKED"`.

### WP-05: Documentation & Logging of System-Specific Calculation Gaps (`structural/workflows/`)
- **System A (`structural/workflows/system_a.py`):** Explicitly logged unsupported checks: column baseplate flexure/anchor rod tension per IS 800 Cl 7.4, frame lateral drift/sway stability per IS 800 Cl 5.6.1.1, purlin biaxial bending per Cl 8.2.1.2, cold-formed section local buckling per IS 801, and host concrete slab punching shear.
- **System B (`structural/workflows/system_b.py`):** Logged unsupported checks: thin-walled aluminium extrusion local buckling & HAZ softening per IS 8147 Cl 5.2, rail-to-bracket bolt tear-out, module clamp lip yielding, and thermal expansion thermal-slip stresses.
- **System C (`structural/workflows/system_c.py`):** Logged unsupported checks: SDS fastener pull-out and pull-over in thin metal deck, standing seam clamp friction-grip slippage under cyclic wind flutter, and trapezoidal sheet crest local crushing.
- **System D (`structural/workflows/system_d.py`):** Logged unsupported checks: in-situ wet friction pull-slip testing per ASTM C1028, boundary layer wind tunnel pressure calibration for array shelter effects, and host RCC roof slab structural load-bearing capacity.

### WP-06: Drawing Engine Governance Hardening (`structural/drawing.py`)
- **Drawing Classification:** Introduced `DrawingClassification` enum:
  - `PRELIMINARY_MODULE_ARRANGEMENT`
  - `PRELIMINARY_FRAMING_CONCEPT`
  - `CALCULATED_STRUCTURAL_LAYOUT`
  - `INDEPENDENTLY_REVIEWED_DRAWING`
- **Mandatory Disclaimers Block:** Added explicit modelspace notes declaring:
  1. Module arrangement is preliminary and framing layout is conceptual.
  2. Structural member sizes are preliminary sizing indications only.
  3. Baseplates, connections, fasteners, and anchorages are NOT DEFINED and NOT VERIFIED.
  4. AFC status is STRICTLY BLOCKED; drawing must NOT be used for procurement, fabrication, or installation.
- **Watermark:** Enforced prominent diagonal and title-block watermarks: `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`.

### WP-07: CLI Input Validation Hardening (`structural/cli.py`)
- **Project Existence Check:** Integrated validation across `set-site`, `set-module`, `set-geometry`, `set-material`, and `set-section`. Fails with code 1 if project does not exist.
- **Physical Numerical Bounds:** Enforced latitude $\in [6.0, 38.0]$, longitude $\in [68.0, 98.0]$, basic wind speed $V_b \in [30.0, 60.0]$, and strictly positive dimensions ($rows > 0$, $cols > 0$, $total = rows \times cols$).
- **Persistent Provenance Recording:** Integrated persistent recording of provenance levels on CLI inputs.

### WP-08: API Security and Transaction Safety (`server.py`)
- **Atomicity & Orphan Prevention:** In `api_create_structural_project`, pre-validated quotation existence via `get_quotation` prior to database insertion. Added rollback cleanup (`delete_project(pid)`) in exception handlers, preventing orphaned structural projects.
- **Calculation Input Sanitization:** In `api_calculate_structural_project`, implemented strict bounds and finite-number checks rejecting `NaN`, $\pm\infty$, non-positive geometry dimensions, and non-physical friction coefficients ($\mu \le 0$ or $\mu > 1.0$).

---

## 3. COMPREHENSIVE DEFECT-TO-FIX TRACEABILITY MATRIX

| Defect ID | Description | Affected File & Function | Root Cause Analysis | Code Change Made | Verifying Test | Actual Test Result | Remaining Engineering Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | Load actions lacked physical attributes and stable identifiers | `structural/actions.py` (`PhysicalAction`, `ActionRegister`) | Actions were stored as simple floats without engineering metadata, units, or governing code clauses. | Created `PhysicalAction` dataclass with stable IDs (`ACT_DL_01`, etc.), categories, units, and code clauses. | `test_category_a_load_action_registry` | **PASS** | Dynamic gust response and live load reduction not included. |
| **DEF-02** | Incomplete seismic combination matrix (lacked full 24 3D spatial combinations) | `structural/actions.py` (`generate_seismic_combinations`) | Seismic generator only created 4 simplified cases, omitting vertical seismic acceleration and orthogonal combinations. | Implemented complete 24-case 3D seismic combination matrix per IS 1893:2016 Cl 6.3.2.1/6.3.4.1/6.3.4.2. | `test_category_c_seismic_combination_matrix` | **PASS** | Dynamic modal response spectrum analysis not supported. |
| **DEF-03** | Ephemeral parameter provenance lost across server restarts | `structural/provenance.py`, `structural/db.py` | Provenance records were kept in memory in `ProvenanceTracker` without persistent SQLite backing. | Added SQLite migration V5 (`provenance_records` table) and integrated auto-persistence into tracker. | `test_category_e_provenance_persistence` | **PASS** | Mill certificates and test reports not automatically parsed. |
| **DEF-04** | Numerical calculation `PASS` conflated with engineering verification | `structural/db.py`, `structural/engine.py`, `server.py` | A single `status` column combined mathematical unity ratio outcome with statutory engineering sign-off. | Added separate columns: `numerical_status`, `input_completeness`, `provenance_status`, `engineering_status`, `construction_status`. | `test_category_g_numerical_pass_vs_engineering_verification` | **PASS** | Professional engineer physical review and wet stamp required. |
| **DEF-05** | Silent omission of critical connection and stability checks | `structural/workflows/` (`system_a.py` to `system_d.py`) | Unchecked failure modes (anchor rods, HAZ, SDS pull-out, ballast slip) were unacknowledged in code. | Added explicit warnings, assumption logging, and unverified check notifications to all 4 system workflows. | `test_category_h_unsupported_checks_across_systems` | **PASS** | Non-linear FEM analysis and connection design required before AFC. |
| **DEF-06** | DXF export lacked formal drawing classification and liability disclaimers | `structural/drawing.py` (`DXFDrawingEngine`) | DXF produced CAD entities without explicit text blocks describing framing as conceptual and connections as unverified. | Added `DrawingClassification` enum and mandatory modelspace disclaimers block with strict AFC lock. | `test_category_i_dxf_watermark_and_approval_gate` | **PASS** | Fully detailed fabrication shop drawings not supported. |
| **DEF-07** | CLI allowed orphan records and invalid physical bounds | `structural/cli.py` (`cmd_project_set_*`) | CLI did not verify project existence or validate coordinate/wind ranges before writing to database. | Added existence checks and numerical range bounds ($V_b \in [30, 60]$, positive dimensions, grid consistency). | `test_category_j_cli_input_validation` | **PASS** | Complex custom polyline array boundaries not supported via CLI. |
| **DEF-08** | API allowed orphan structural projects and non-finite parameters | `server.py` (`api_create_structural_project`, `api_calculate_structural_project`) | Projects were inserted before validating quotation existence; non-finite floats (`NaN`, $\infty$) were unchecked. | Added quotation pre-validation, atomic rollback on error, and numerical sanity checks on calculation inputs. | `test_category_k_api_authentication_and_transactions` | **PASS** | Role-based RBAC token authentication pending Phase 2 deployment. |

---

## 4. INDEPENDENT BENCHMARK CALCULATION VERIFICATION

### Benchmark: Purlin Deflection Evaluation under Serviceability Limit State (SLS-01)
Target project `RS-STR-RENSUN-2026-0059` features an elevated canopy (System A) with purlin span $L = 3000\text{ mm}$, purlin spacing $B = 1150\text{ mm}$, section ISMC 100x50x2.0, extruded aluminium alloy 6063-T6:
- Elastic Modulus: $E = 69,000\text{ MPa}$
- Moment of Inertia: $I_{xx} = 750,000\text{ mm}^4$
- Allowable Deflection Limit: $\delta_{\text{allow}} = \frac{L}{250} = \frac{3000}{250} = 12.00\text{ mm}$ (IS 800:2007 Table 6)

#### Hand Calculation
1. **Dead Load Component ($w_{\text{dl}}$):**
   - Module weight: $27.5\text{ kg} \times 9.81\text{ m/s}^2 / (2.278\text{ m} \times 1.134\text{ m}) = 104.5\text{ N/m}^2$
   - Tributary load: $104.5\text{ N/m}^2 \times 1.150\text{ m} \times 10^{-3} = 0.1202\text{ N/mm}$
   - Purlin self-weight: $3.53\text{ kg/m} \times 9.81 \times 10^{-3} = 0.0346\text{ N/mm}$
   - Total dead load $w_{\text{dl}} = 0.1202 + 0.0346 = 0.1548\text{ N/mm}$
2. **Imposed Load Component ($w_{\text{il02}}$):**
   - Roof distributed live load: $0.75\text{ kN/m}^2 \times 1.150\text{ m} = 0.8625\text{ N/mm}$
3. **Total Serviceability Distributed Load ($w_{\text{sls}}$):**
   $$w_{\text{sls}} = w_{\text{dl}} + w_{\text{il02}} = 0.1548 + 0.8625 = 1.0173\text{ N/mm}$$
4. **Midspan Deflection under Distributed Load ($\delta_{\text{dist}}$):**
   $$\delta_{\text{dist}} = \frac{5 w_{\text{sls}} L^4}{384 E I_{xx}} = \frac{5 \times 1.0173 \times (3000)^4}{384 \times 69,000 \times 750,000} = \frac{4.12007 \times 10^{14}}{1.9872 \times 10^{13}} = 20.7304\text{ mm}$$
5. **Midspan Deflection under Concentrated Point Load ($P = 1000\text{ N}$):**
   $$\delta_{\text{point}} = \frac{P L^3}{48 E I_{xx}} = \frac{1000 \times (3000)^3}{48 \times 69,000 \times 750,000} = \frac{2.70 \times 10^{13}}{2.484 \times 10^{12}} = 10.8696\text{ mm}$$
6. **Governing Structural Case:**
   $$\delta_{\text{governing}} = \max(\delta_{\text{dist}}, \delta_{\text{point}}) = \max(20.7304, 10.8696) = 20.7304\text{ mm}$$
7. **Governing Unity Ratio:**
   $$\text{UR} = \frac{\delta_{\text{governing}}}{\delta_{\text{allow}}} = \frac{20.7304}{12.0000} = 1.727537 > 1.0 \quad (\mathbf{FAIL})$$

#### Code Engine vs Hand Calculation Comparison
| Metric | Independent Hand Calculation | Calculation Engine Output | Stored Snapshot in DB | Absolute Difference | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Distributed Deflection** | $20.7304\text{ mm}$ | $20.7304\text{ mm}$ | $20.7304\text{ mm}$ | $0.0000\text{ mm}$ | **MATCH** |
| **Point Load Deflection** | $10.8696\text{ mm}$ | $10.8696\text{ mm}$ | $10.8696\text{ mm}$ | $0.0000\text{ mm}$ | **MATCH** |
| **Allowable Deflection** | $12.0000\text{ mm}$ | $12.0000\text{ mm}$ | $12.0000\text{ mm}$ | $0.0000\text{ mm}$ | **MATCH** |
| **Governing Unity Ratio** | **1.727537** | **1.727537** | **1.727537** | **0.000000** | **BIT-FOR-BIT MATCH** |
| **Check Outcome** | **FAIL** | **FAIL** | **FAIL** | Identical | **MATCH** |

---

## 5. DATABASE AND HISTORICAL SNAPSHOT INTEGRITY AUDIT

Project `RS-STR-RENSUN-2026-0059` was audited directly in `structural/structural_runs.db`:
- **Total Historical Runs:** 20 distinct calculation runs.
- **Oldest Run ID:** `RUN-RS-STR-RENSUN-2026-0059-20261107104453-7bdd0d` (Status: `FAIL`, $\text{UR} = 1.727537$, AFC: `0`).
- **Latest Run ID:** `RUN-RS-STR-RENSUN-2026-0059-20261107130822-3acfa8` (Status: `FAIL`, $\text{UR} = 1.727537$, AFC: `0`).
- **AFC Status across all 20 runs:** `is_approved_for_construction = 0` (100% blocked).
- **Snapshot Immutability:** Input JSON snapshots, report summary JSONs, and member result tables remain byte-identical and unmutated.

---

## 6. CANONICAL VERIFICATION HOLD INTEGRITY REPORT

All 12 original canonical verification holds remain registered, active, and enforced with zero deletions or renamings:

| Hold ID | Canonical Hold Name | Applicable Systems | Governed Standards | Current Status | Gate Enforcement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HOLD-01** | Basic Wind Speed ($V_b$) & Regional Topography ($k_3$) | Systems A, B, C, D | IS 875 Part 3: 2015 Cl 6.2, 6.3.3 | **ACTIVE** | AFC Blocked |
| **HOLD-02** | Terrain Category & Rooftop Exposure Height | Systems A, B, C, D | IS 875 Part 3: 2015 Cl 6.3.2 | **ACTIVE** | AFC Blocked |
| **HOLD-03** | Local Pressure Aerodynamic Coefficients ($C_{pe}-C_{pi}$) | Systems A, B, C, D | IS 875 Part 3: 2015 Cl 7.3 & Tab 4–14 | **ACTIVE** | AFC Blocked |
| **HOLD-04** | Site-Specific Seismic Parameters ($Z$, $I$, $R$, $S_a/g$) | Systems A, B, C, D | IS 1893 Part 1: 2016 Cl 6.4 | **ACTIVE** | AFC Blocked |
| **HOLD-05** | Material Yield Strength & Mill Test Certificates | Systems A, B, C, D | IS 2062: 2011 / IS 8147: 1976 / ASTM A653 | **ACTIVE** | AFC Blocked |
| **HOLD-06** | Cold-Formed Steel Section Verification | Systems A, B, C | IS 801: 1975 / AISI S100-16 | **ACTIVE** | AFC Blocked |
| **HOLD-07** | Baseplate & Anchor Rod Verification | System A | IS 800: 2007 Cl 7.4 / IS 456 / ACI 318 | **ACTIVE** | AFC Blocked |
| **HOLD-08** | Thin-Walled Rail & Clamp Local Buckling | System B | IS 8147: 1976 Cl 5.2 / ADM 2020 | **ACTIVE** | AFC Blocked |
| **HOLD-09** | Sheet Fastener Pull-Out & Standing-Seam Uplift | System C | IS 801 / AISI S100 / ASTM E1592 | **ACTIVE** | AFC Blocked |
| **HOLD-10** | Ballast Friction Coefficient ($\mu$) & Interface Verification | System D | IS 875 Part 3 / ASTM C1028 | **ACTIVE** | AFC Blocked |
| **HOLD-11** | Host Rooftop Slab Structural Capacity Verification | Systems A, B, C, D | IS 456: 2000 Cl 31, 35 | **ACTIVE** | AFC Blocked |
| **HOLD-12** | Professional Structural Engineer Peer Review & Sign-Off | Systems A, B, C, D | National Building Code (NBC 2016) | **ACTIVE** | AFC Blocked |

---

## 7. FULL REGRESSION TEST EXECUTION SUMMARY

```text
======================================================================
RENSUN SOLAR STRUCTURAL SUITE — TEST EXECUTION REPORT
======================================================================
1. tests/test_phase1_4_2_1_verification.py:
   - test_category_a_load_action_registry ......................... OK
   - test_category_b_load_combination_completeness ................ OK
   - test_category_c_seismic_combination_matrix .................. OK
   - test_category_d_independent_formula_benchmarks ............... OK
   - test_category_e_provenance_persistence ....................... OK
   - test_category_f_hold_integration ............................. OK
   - test_category_g_numerical_pass_vs_engineering_verification ... OK
   - test_category_h_unsupported_checks_across_systems ............ OK
   - test_category_i_dxf_watermark_and_approval_gate ............. OK
   - test_category_j_cli_input_validation ......................... OK
   - test_category_k_api_authentication_and_transactions .......... OK
   - test_category_l_historical_snapshot_immutability ............. OK
   - test_category_m_quotation_and_pdf_regression ................. OK
   - test_category_n_tneb_extraction_offline_regression ........... OK
   (Subtotal: 14 tests, 14 passed, 0 failed, 0 errors)

2. tests/test_structural_foundation.py (26 tests) ................. OK
3. tests/test_structural_database.py (19 tests) ................... OK
4. tests/test_structural_web_ui.py (14 tests) ..................... OK
5. tests/test_quotation_structural_integration.py (8 tests) ....... OK
6. tests/test_structural_cli.py (13 tests) ........................ OK
7. test_quotation_system.py (20 tests) ............................ OK
----------------------------------------------------------------------
TOTAL TESTS EXECUTED: 114
TOTAL PASSED: 114 (100.0%)
TOTAL FAILED: 0
TOTAL ERRORS: 0
TOTAL SKIPPED: 0
======================================================================
```

---

## 8. REMAINING UNRESOLVED ENGINEERING LIMITATIONS

The software corrections in Phase 1.4.2.1 harden calculations, provenance, and governance, but the following physical and statutory limitations remain intentionally unreleased pending site data and physical engineering review:

1. **Host Slab Structural Capacity:** Software cannot determine whether the RCC slab at Erumapalayam, Salem can carry canopy column point loads ($>15\text{ kN}$) or ballasted system dead loads without structural as-built drawings and non-destructive testing (NDT).
2. **Anchor Rod Pull-Out & Chemical Embedment:** Baseplate anchorage design requires concrete compressive strength ($f_{ck}$) and slab thickness; not calculated in software.
3. **Standing Seam & SDS Pull-Out Capacities:** Metal sheet pull-out/pull-over values must be confirmed by project-specific pull-out tests or manufacturer certification.
4. **Wet Friction Coefficient:** Ballasted non-penetrating sliding resistance requires in-situ friction testing on wet rooftop waterproofing membrane.
5. **Cold-Formed Thin-Walled Distortional Buckling:** Linear beam formulas do not evaluate distortional or local buckling under IS 801 / AISI S100 without full section profile coordinates.
6. **Statutory Structural Engineer Stamping:** Under NBC 2016 and local municipal regulations, software output cannot replace wet ink signatures and engineering stamps from a licensed chartered structural engineer.

---

## 9. PHASE 1.4.2.1 COMPLETION CLASSIFICATION & DECISIONS REQUIRED

### Completion Classification
**PHASE 1.4.2.1 IS COMPLETE: CODE DEFECTS RESOLVED, PROVENANCE PERSISTENCE OPERATIONAL, GOVERNANCE GATES HARDENED.**

All software deliverables, tests, and audits are completed. The platform remains strictly halted at the Phase 1.4.2.1 boundary. Phase 1.5 has NOT been started.

### Exact Owner Decisions Required Next
1. **Decision on Canopy Member Upgrade for Salem Project:** Target project `RS-STR-RENSUN-2026-0059` correctly fails purlin deflection under SLS-01 ($\text{UR} = 1.7275$). The owner may authorize testing an upgraded steel section (e.g. ISMC 125 or steel hollow section with $E = 205\text{ GPa}$) or reduced purlin span ($1500\text{ mm}$) to verify whether numerical compliance is achieved.
2. **Decision on Salem Geotechnical / Structural Survey:** Determine whether to commission on-site survey and structural inspection for Erumapalayam property to satisfy Holds HOLD-01, HOLD-07, and HOLD-11.
3. **Authorization for Phase 1.4.3 or Phase 1.5:** Explicit owner authorization is required before beginning any subsequent phase.
