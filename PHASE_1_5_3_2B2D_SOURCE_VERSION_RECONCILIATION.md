# PHASE 1.5.3.2B.2D — ACTIVE SOURCE VERSION RECONCILIATION REPORT
## Comprehensive Audit of Source Lineage, Import Graphs, and File Immutability

**Platform:** Google Antigravity  
**Project:** RS-STR-RENSUN-2026-0059  
**Quotation:** RENSUN/2026/0059  
**Mounting System:** System A — Elevated Steel Canopy  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Verified HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Audit Stage:** Phase 1.5.3.2B.2D (Source Reconciliation & Independent Benchmark Audit)  
**Verification Date:** 2026-11-08  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED`

---

## 1. EXECUTIVE SUMMARY & SOURCE RECONCILIATION FINDINGS

A systematic source-level reconciliation was conducted to identify the active implementation of System A, resolve the discrepancy between three versions of `system_a_final.py` identified by the engineering reviewer, and trace the full import graph across production modules and test suites.

### Key Audit Findings:
1. **The Active Source File:** The sole active production source path is:
   `/Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py`
   - File Size: **69,532 bytes**
   - SHA-256: `9788ff729270df448ec22d479ae84c1c22de2c8b0cfbf233a47e658042363e04`
2. **Identification of the Two Uploaded Duplicate Versions:**
   - Location 1: `docs/phase_1_5/evidence_1_5_3_2b2/source_audit_export/system_a_final.py` (60,363 bytes, SHA-256: `c9807e13a796b57159be7af274c54520708dcd4cc0c276aeae683847c4b1d329`)
   - Location 2: `evidence_1_5_3_2b2/source_audit_export/system_a_final.py` (60,363 bytes, SHA-256: `c9807e13a796b57159be7af274c54520708dcd4cc0c276aeae683847c4b1d329`)
   - **Reconciliation Verdict:** These two files are **100% byte-identical duplicates**. They represent the **Phase 1.5.3.2B.2 export** made prior to the Phase 1.5.3.2B.2B implementation. They do **NOT** correspond to the active file. They lack the Phase 1.5.3.2B.2B defect corrections (`LTBCalculationMethod` enum, 6-DOF weld group solver, product-specific anchor temperature deration, and HSFG bolt slip criteria).
3. **Exact Matching Test File:**
   - Active Path: `tests/test_phase1_5_3_2_system_a_final.py`
   - File Size: **38,614 bytes**
   - SHA-256: `a77e63a94f2013655f268fd66b5426425c2e6173ef9dcf6fe27c0dce345b9fac`
   - Test Results: All 15 tests pass in 0.45s against the active source file.
4. **Zero Runtime CSV or External Benchmark Dependencies:**
   - Inspection of `tests/test_phase1_5_3_2_system_a_final.py` confirms that the test suite does **NOT** import any separate external benchmark module and does **NOT** read any benchmark CSV file at runtime. All benchmark calculation routines are embedded directly within the individual test methods.
5. **Fresh Versioned Export:**
   - All active source, test, and isolation helper files have been exported into `docs/phase_1_5/evidence_1_5_3_2b2d/source_audit_export/` with a cryptographic manifest in `PHASE_1_5_3_2B2D_SOURCE_EXPORT_MANIFEST.csv`.

---

## 2. ACTIVE FILE VS HISTORICAL EXPORT COMPARISON

The table below contrasts the active production file with the historical pre-B.2B export duplicates.

| Attribute | Active Source File | Historical Export Duplicates (B.2) | Audit Finding / Variance |
| :--- | :--- | :--- | :--- |
| **Filesystem Path** | `structural/workflows/system_a_final.py` | `docs/phase_1_5/evidence_1_5_3_2b2/source_audit_export/system_a_final.py` & `evidence_1_5_3_2b2/source_audit_export/system_a_final.py` | Active path is the live package module |
| **Byte Size** | **69,532 bytes** | **60,363 bytes** | Active file has +9,169 bytes of defect remediation code |
| **SHA-256 Checksum** | `9788ff729270df448ec22d479ae84c1c22de2c8b0cfbf233a47e658042363e04` | `c9807e13a796b57159be7af274c54520708dcd4cc0c276aeae683847c4b1d329` | Hash difference confirmed |
| **LTB Method Architecture (DEF-01)** | Includes `LTBCalculationMethod` Enum, governing $C_b = 1.2987$, $M_d = 90.40\text{ kNm}$, and relegates $C_1 = 1.75$ to comparative field | Exposes $C_1 = 1.75$ and $M_d = 105.64\text{ kNm}$ as primary output | Active file implements B.2B remediation |
| **Fly-Bracing Series Model (DEF-02)** | Evaluates $K_{sys} = 10.72\text{ kN/mm}$, enforces HSFG pre-tensioned bolts, and sets governance status | Basic stiffness check only, lacked HSFG slip capacity check | Active file implements series compliance |
| **Weld Group Analysis (DEF-03)** | Implements `ParametricWeldGroupSolver` with transformed local $I_{0x}, I_{0y}, I_{0xy}$, product of inertia $I_{xy}$, and 6-DOF solver | Simplified 1D projected weld section modulus | Active file implements spatial geometry |
| **Chemical Anchorage (DEF-04)** | Implements `ProductSpecificChemicalAnchorModel` with ETA-20/0541 Temperature Range II ($6.5\text{ MPa}$) and $h_{\min} = 161\text{ mm}$ clash | Generic anchor capacity without product-specific thermal deration | Active file implements product-specific model |

---

## 3. IMPORT GRAPH AND CALL HIERARCHY RECONCILIATION

A full codebase search was performed across all 62 Python files in the repository to trace every reference to `system_a_final`.

### 3.1. Modules Importing `structural.workflows.system_a_final`:
1. `structural/workflows/__init__.py`:
   - Line 36: Imports `LTBCalculationMethod`, `WindUpliftRafterAudit`, `evaluate_wind_uplift_rafter_flexure`, `FlyBracingDesignCheck`, `design_bottom_flange_fly_bracing`, `StatutoryAnchorStandardBasis`, `get_chemical_anchor_standards_hierarchy`, `ProjectSpecificAnchorTestingProtocol`, `generate_project_anchor_testing_protocol`, `SlabThicknessEvaluation`, `evaluate_slab_thickness_and_anchorage_feasibility`, `FoundationLoadPathStep`, `CompleteFoundationLoadPathReport`, `verify_complete_foundation_load_path`.
   - Exposes these symbols as the public API for the `structural.workflows` package.
2. `tests/test_phase1_5_3_2_system_a_final.py`:
   - Line 42: Imports all calculation routines, solvers, and data structures from `structural.workflows.system_a_final` for ASME V&V 10 testing.

### 3.2. Alternative Mounting System A Workflows in Repository:
The repository contains four chronological stages of System A engineering development:
1. `structural/workflows/system_a.py`: Original Phase 1.3 canopy workflow (initial draft).
2. `structural/workflows/system_a_validation.py`: Phase 1.4 cold-formed purlin and extended framing validator.
3. `structural/workflows/system_a_reconciliation.py`: Phase 1.5.3.1 preliminary independent reconciliation workflow.
4. `structural/workflows/system_a_final.py`: The **governing Phase 1.5.3.2 / 1.5.3.2B.2B workflow** incorporating all defect corrections.

### 3.3. Web UI and Server Integration:
- `server.py` delegates structural requests to `structural.integration.STRUCTURAL_BRIDGE`.
- `STRUCTURAL_BRIDGE` uses `StructuralCalculationEngine` in `structural/engine.py` for standard assessment generation, while detailed deep-dive audits invoke `structural.workflows.system_a_final`.
- No conflicting or alternate version of `system_a_final.py` is invoked anywhere in the active execution path.

---

## 4. AUDIT OF TEST BENCHMARK MODULES AND CSVS

The audit investigated whether `tests/test_phase1_5_3_2_system_a_final.py` relies on external CSV benchmark files or auxiliary benchmark modules:

1. **Benchmark Python Modules:**
   - Does `tests/test_phase1_5_3_2_system_a_final.py` import a separate benchmark file? **NO.**
   - All benchmark equations (Kirby-Nethercot Simpson formula, Winter-Yura spring stiffness, Blodgett weld stress, fib 58 concrete breakout) are embedded directly inside the 15 test methods.
2. **Benchmark CSV Files:**
   - Does `tests/test_phase1_5_3_2_system_a_final.py` read any CSV file from disk during execution? **NO.**
   - The test file contains zero `csv` imports and zero file-reading calls to `.csv` paths.
   - The CSV benchmark files located in the repository (`PHASE_1_5_3_2B2B_LTB_INDEPENDENT_VALIDATION.csv`, `PHASE_1_5_3_2B2B_FLY_BRACING_STIFFNESS_VALIDATION.csv`, `PHASE_1_5_3_2B2B_WELD_GROUP_BENCHMARKS.csv`, `PHASE_1_5_3_2B2B_ANCHOR_PRODUCT_VALIDATION.csv`) are post-test evidence deliverables, not test-suite runtime inputs.

---

## 5. VERSIONED EVIDENCE EXPORT

The active source code, matching test suite, and isolation harness have been exported to:
`docs/phase_1_5/evidence_1_5_3_2b2d/source_audit_export/`

| Exported File | Size | SHA-256 Checksum |
| :--- | :--- | :--- |
| `system_a_final.py` | 69,532 B | `9788ff729270df448ec22d479ae84c1c22de2c8b0cfbf233a47e658042363e04` |
| `test_phase1_5_3_2_system_a_final.py` | 38,614 B | `a77e63a94f2013655f268fd66b5426425c2e6173ef9dcf6fe27c0dce345b9fac` |
| `test_isolation_helper.py` | 13,005 B | `6e72416ff805070ffb06d9edb37e8687f16eb240e93554c15e406b6603d3c206` |

The export manifest is formally recorded in [PHASE_1_5_3_2B2D_SOURCE_EXPORT_MANIFEST.csv](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/evidence_1_5_3_2b2d/PHASE_1_5_3_2B2D_SOURCE_EXPORT_MANIFEST.csv).
