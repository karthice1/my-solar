# RENSUN SOLAR — PHASE 1.5.1
## Technical Baseline Inventory Report

**Document Reference:** `RS-REP-PHASE-1-5-1-BASELINE-INVENTORY`  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Base Commit / Verified HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Target Quotation:** `RENSUN/2026/0059`  
**Target Project:** `RS-STR-RENSUN-2026-0059`  
**Site:** `90 ERUMAPALAYAM ITTERI ROAD, SALEM` (`11.6643°N, 78.1460°E`)  
**Execution Timestamp:** `2026-11-08T08:10:00+05:30`  
**Governance State:** `ENGINEERING VERIFICATION PENDING` (12 Canonical Holds Enforced | AFC Locked)

---

## 1. REPOSITORY & GIT BASELINE

### 1.1 Git Working Tree State
```bash
$ git branch -v
* feature/phase1-structural-foundation df8d5da Initial commit: TNEB Account Extractor & Interactive Solar Quotation Builder
  main                                 df8d5da Initial commit: TNEB Account Extractor & Interactive Solar Quotation Builder

$ git rev-parse HEAD
df8d5da966b6506c1eada7093db2a140cbc0b9dc

$ git status
On branch feature/phase1-structural-foundation
Changes not staged for commit:
	modified:   server.py
	modified:   templates/index.html

Untracked files:
	... (governance reports, tests/, structural/, backups/, generated_drawings/)
no changes added to commit (use "git add" and/or "git commit -a")
```

- **Active Branch:** `feature/phase1-structural-foundation` (Unaltered).
- **HEAD Commit:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc` (Unaltered).
- **Staging Area:** 0 staged files. Zero commits, zero pushes, zero branch switches.
- **Tracked Unstaged Files:**
  - [`server.py`](file:///Users/karthik/tneb-account-extractor/server.py): Contains Module H (FastAPI structural routes, hardened header-based `X-Owner-Token` authentication, AFC status lock, isolated DXF path support).
  - [`templates/index.html`](file:///Users/karthik/tneb-account-extractor/templates/index.html): Contains Structural Automation UI tabs (Projects, Configurator, History, Holds), authenticated `getAuthHeaders()` calls, and blob deliverable downloads.

---

## 2. PROJECT ARCHITECTURE & FILE STRUCTURE

### 2.1 Directory Layout
```
/Users/karthik/tneb-account-extractor/
├── quotations.db                       # Production SQLite Commercial Quotations DB
├── quotation_settings.json             # Production Owner Pricing & Engineering Settings
├── server.py                           # Unified FastAPI Application (Public TNEB + Quotation + Structural)
├── extract_tneb.py                     # Core Playwright & OCR Consumer Account Extractor
├── test_exact_matching.py              # Exact-matching & Safe Cleanup Regression Suite (23 tests)
├── test_quotation_system.py            # Commercial Quotation Logic & PDF Regression Suite (20 tests)
│
├── quotation/                          # Commercial Quotation Engine
│   ├── __init__.py
│   ├── quotation_history.py            # Quotation CRUD, SQLite Schema, Versioning
│   ├── settings_manager.py             # Owner Token Auth, Pricing Defaults
│   └── pdf_generator.py                # 5-Page Playwright PDF Generator
│
├── structural/                         # Structural Engineering Subsystem (Phase 1.0 - 1.4)
│   ├── __init__.py
│   ├── models.py                       # Data Classes (Site, Module, Geometry, Sections, Actions)
│   ├── holds.py                        # 12 Canonical Verification Holds & Master Verification Register
│   ├── db.py                           # SQLite Structural Database Engine (15 Tables)
│   ├── engine.py                       # Analytical Calculation Engine (IS 800, IS 8147, IS 875)
│   ├── wind.py                         # Wind Engine (IS 875 Part 3: 2015, Vz, pz, Cpe, Cpi)
│   ├── provenance.py                   # 5-Tier Provenance Taxonomy & Parameter Lineage Tracking
│   ├── drawing.py                      # DXF Structural GA Drawing Generator (ezdxf)
│   ├── integration.py                  # Quotation-to-Structural Subsystem Bridge
│   ├── cli.py                          # Structural CLI Interface
│   └── workflows/                      # Canonical Mounting System Workflows
│       ├── __init__.py
│       ├── system_a.py                 # System A: Elevated Steel Canopy (IS 800:2007)
│       ├── system_b.py                 # System B: Low-Height Aluminium Rail (IS 8147:1976)
│       ├── system_c.py                 # System C: Metal-Sheet Roof Mounting (Direct Fix)
│       └── system_d.py                 # System D: Ballasted Non-Penetrating System (Flat RCC)
│
├── tests/                              # Hermetic Structural Test Suites (108 tests)
│   ├── test_isolation_helper.py        # IsolatedTestEnvironment Context Manager
│   ├── test_phase1_4_2_1_verification.py   # Governance & Category A–N Verification (14 tests)
│   ├── test_phase1_4_2_2_verification.py   # Defect Corrections, WP-01 to WP-13 (14 tests)
│   ├── test_quotation_structural_integration.py # Pipeline Integration Bridge (12 tests)
│   ├── test_structural_cli.py          # Structural CLI Suite (13 tests)
│   ├── test_structural_database.py     # Structural Database & Transaction Suite (15 tests)
│   ├── test_structural_foundation.py   # Engineering Core & Codal Formula Suite (26 tests)
│   └── test_structural_web_ui.py       # Web UI & REST API Suite (14 tests)
│
├── backups/phase_1_5_1_baseline/       # Dedicated Phase 1.5.1 Production Backups
│   ├── quotations.db                   # SQLite Online Backup
│   ├── quotations_byte_copy.db         # Exact Byte-for-Byte Copy
│   ├── structural_runs.db              # SQLite Online Backup
│   ├── structural_runs_byte_copy.db    # Exact Byte-for-Byte Copy
│   ├── quotation_settings.json         # Exact Copy
│   └── generated_drawings/             # Exact Copy of 5 DXF Drawings
│
├── generated_drawings/                 # Production DXF Output Directory (5 files)
├── generated_quotations/                # Production PDF Output Directory (34 files)
├── docs/phase_1_5/                     # Phase 1.5 Validation Documentation & Reports
└── templates/
    └── index.html                      # Unified Single Page Application (Alpine.js + Tailwind)
```

---

## 3. DATABASE BASELINE & CANONICAL PATHS

### 3.1 Production Database Identification
1. **Commercial Quotations Database:**
   - Canonical Path: `/Users/karthik/tneb-account-extractor/quotations.db`
   - Active Tables: `quotations`, `quotation_versions`, `settings`
   - Pre-Execution SHA-256: `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf`
2. **Structural Engineering Database:**
   - Canonical Path: `/Users/karthik/tneb-account-extractor/structural/structural_runs.db`
   - Active Tables (15 Tables):
     - `structural_projects`
     - `project_sites`
     - `project_modules`
     - `project_geometries`
     - `project_sections`
     - `project_holds`
     - `calculation_runs`
     - `run_member_results`
     - `run_load_combinations`
     - `quotation_structural_links`
     - `parameter_provenance`
     - `unsupported_checks_log`
     - `database_audit_log`
     - `drawing_deliverables`
     - `sqlite_sequence`
   - Pre-Execution SHA-256: `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff`

---

## 4. STRUCTURAL REST API ROUTE INVENTORY

All fourteen (14) structural endpoints in [`server.py`](file:///Users/karthik/tneb-account-extractor/server.py) enforce `verify_structural_auth()` via HTTP header `X-Owner-Token`:

| HTTP Method | Route Path | Handler Function | Security / Auth | Query Tokens |
|---|---|---|:---:|:---:|
| `POST` | `/api/quotations/{quotation_no}/structural` | `api_attach_structural_assessment` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/quotations/{quotation_no}/structural` | `api_get_structural_assessment` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/quotations/{quotation_no}/structural/report` | `api_get_structural_report` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/quotations/{quotation_no}/structural/dxf` | `api_download_structural_dxf` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/structural/projects` | `api_list_structural_projects` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `POST` | `/api/structural/projects` | `api_create_structural_project` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/structural/projects/{project_id}` | `api_get_structural_project_details` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `PUT` | `/api/structural/projects/{project_id}/inputs` | `api_update_structural_project_inputs` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `POST` | `/api/structural/projects/{project_id}/calculate` | `api_calculate_structural_project` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/structural/runs` | `api_list_all_structural_runs` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/structural/projects/{project_id}/runs` | `api_list_structural_project_runs` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/structural/runs/{run_id}` | `api_get_structural_run_details` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/structural/holds` | `api_get_structural_holds` | `X-Owner-Token` Header Mandatory | **REJECTED** |
| `GET` | `/api/structural/projects/{project_id}/deliverables/{item}` | `api_download_structural_deliverable` | `X-Owner-Token` Header Mandatory | **REJECTED** |

**Status Guards:**
- Status update endpoint `PUT /api/quotations/{quotation_no}/status` strictly blocks any attempt to transition status to `APPROVED_FOR_CONSTRUCTION` or `AFC` with HTTP 403 Forbidden.

---

## 5. CANONICAL VERIFICATION HOLDS STATUS

The 12 immutable canonical holds in [`structural/holds.py`](file:///Users/karthik/tneb-account-extractor/structural/holds.py) are managed system-wide by `MASTER_VERIFICATION_REGISTER`:

| Hold Identifier | Canonical Title | Active State | Codal / Statutory Standard |
|---|---|:---:|---|
| `INSPECTION_REQUIRED_HOLD` | Host Building Structural Adequacy & Physical Inspection | **ACTIVE** | NBC 2016 Part 6 / IS 456 / IS 800 |
| `AERODYNAMIC_UNSUPPORTED_HOLD` | Aerodynamic Wind Tunnel & CFD Pressure Calibration | **ACTIVE** | IS 875 (Part 3): 2015 Clause 7.3.3.4 |
| `WIND_COORD_UNVERIFIED_HOLD` | Geographic Coordinates & Regional Wind Zone Verification | **ACTIVE** | IS 875 (Part 3): 2015 Fig. 1 & Annex A |
| `WIND_TRANSFORM_UNVERIFIED_HOLD` | 3D Wind Vector Transformation & Accidental Torsion Gate | **ACTIVE** | IS 875 (Part 3): 2015 Clause 6.3.2.1 |
| `VERTICAL_SEISMIC_APPLICABILITY_HOLD` | Vertical Seismic Screening & 24 Permutations Determination | **ACTIVE** | IS 1893 (Part 1): 2016 Clause 6.3.2.2 |
| `LOAD_COMBINATION_PROVISIONAL_HOLD` | Limit State Load Combinations Dual-Gate Check | **ACTIVE** | IS 800: 2007 Section 3 Table 4 |
| `FRICTION_UNVERIFIED_HOLD` | Membrane Sliding Friction Testing & Calibration | **ACTIVE** | ASTM D1894 / IS 875 (Part 3) |
| `ALUMINIUM_DERIVATION_HOLD` | Aluminium Section Modulus & Coupon Tensile Testing | **ACTIVE** | IS 8147: 1976 Clause 6.2 |
| `FASTENER_TORQUE_UNVERIFIED_HOLD` | Fastener Installation Torque & Clamping Integrity | **ACTIVE** | IS 4000: 1992 / IS 1367 |
| `NUMERICAL_INSTABILITY_HOLD` | FEA Solver Matrix Conditioning & Kinematic Mechanism Gate | **ACTIVE** | IS 800: 2007 Annex B & Section 4 |
| `ASSUMED_DATA_CERTIFICATION_HOLD` | Client Data & Host Building Assumption Sign-Off | **ACTIVE** | NBC 2016 Part 6 Administrative Provisions |
| `DRAWING_UNVERIFIED_HOLD` | 4-Gate Verification & Registered Structural Engineer Stamping | **ACTIVE** | Engineers Bill / Statutory Council of India |

### System-Level Hold Distribution:
- **System A (Elevated Steel Canopy):** 10 Active Holds (`can_label_approved_for_construction = False`)
- **System B (Low-Height Aluminium Rail):** 11 Active Holds (`can_label_approved_for_construction = False`)
- **System C (Metal-Sheet Roof Mounting):** 11 Active Holds (`can_label_approved_for_construction = False`)
- **System D (Ballasted Non-Penetrating System):** 12 Active Holds (`can_label_approved_for_construction = False`)

---

## 6. CALCULATION & DRAWING SUBSYSTEM BASELINE

### 6.1 Calculation Subsystem
- **Core Engine:** [`structural/engine.py`](file:///Users/karthik/tneb-account-extractor/structural/engine.py) provides multi-code evaluation routines for dead load, live load, wind load, seismic load, and load combination generation.
- **System Workflows:**
  - `structural/workflows/system_a.py`: Cold-formed purlins (IS 801 / IS 800) and column axial compression. Known purlin serviceability deflection failure (utilization 1.728 > 1.0).
  - `structural/workflows/system_b.py`: Extruded aluminium rail bending/shear and clamp tension.
  - `structural/workflows/system_c.py`: Standing-seam direct fixture clamp pull-out with provisional capacity (3.5 kN).
  - `structural/workflows/system_d.py`: Ballasted non-penetrating sliding and overturning with provisional friction ($\mu = 0.40$).
- **Wind Engine:** [`structural/wind.py`](file:///Users/karthik/tneb-account-extractor/structural/wind.py) implements $V_z = V_b \cdot k_1 \cdot k_2 \cdot k_3 \cdot k_4$ and $p_z = 0.6 \cdot V_z^2$ per IS 875 (Part 3): 2015.

### 6.2 Drawing Subsystem
- **Module:** [`structural/drawing.py`](file:///Users/karthik/tneb-account-extractor/structural/drawing.py)
- **Library:** `ezdxf`
- **Enforced Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION` placed on all layers and title blocks.
- **Approval Gate:** Calling `generate_structural_dxf(..., require_approved=True)` strictly raises `PermissionError` when active holds exist.
- **Output Redirection:** Uses `STRUCTURAL_BRIDGE.drawing_output_dir` (falling back to canonical default `generated_drawings/` only in production).

---

## 7. BASELINE TEST SUITE INVENTORY

The test suite consists of 10 files across unit, integration, web, and regression domains:

| Test File Path | Test Count | Scope / Execution Framework |
|---|:---:|---|
| [`tests/test_phase1_4_2_1_verification.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_4_2_1_verification.py) | 14 | Phase 1.4.2.1 defect corrections and Category A–N governance verification. |
| [`tests/test_phase1_4_2_2_verification.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_4_2_2_verification.py) | 14 | WP-01 to WP-13 verification: TEST-01 rollback, SEC-01/02 matrix, ISO-01/02 isolation. |
| [`tests/test_quotation_structural_integration.py`](file:///Users/karthik/tneb-account-extractor/tests/test_quotation_structural_integration.py) | 12 | Subsystem bridge, quotation linking, hold gates, and calculations. |
| [`tests/test_structural_cli.py`](file:///Users/karthik/tneb-account-extractor/tests/test_structural_cli.py) | 13 | CLI commands, project administration, input setting, runs, hold queries. |
| [`tests/test_structural_database.py`](file:///Users/karthik/tneb-account-extractor/tests/test_structural_database.py) | 15 | Database schema, CRUD operations, transactions, audit logs, run records. |
| [`tests/test_structural_foundation.py`](file:///Users/karthik/tneb-account-extractor/tests/test_structural_foundation.py) | 26 | Structural engineering core: loads, IS 800/8147/875 formulas, geometry, purlin. |
| [`tests/test_structural_web_ui.py`](file:///Users/karthik/tneb-account-extractor/tests/test_structural_web_ui.py) | 14 | Web UI routes, HTML template components, hold notices, deliverables, modals. |
| **Structural Tests Total** | **108** | **Hermetically isolated execution (`python3 -m unittest discover -s tests -p 'test*.py' -v`)** |
| [`test_exact_matching.py`](file:///Users/karthik/tneb-account-extractor/test_exact_matching.py) | 23 | Multi-page TNEB consumer extraction and exact-matching algorithms. |
| [`test_quotation_system.py`](file:///Users/karthik/tneb-account-extractor/test_quotation_system.py) | 20 | Commercial quotation pricing, sizing, subsidy rules, PDF generation. |
| **Grand Total Tests** | **151** | **All 151 tests verified passing in current baseline.** |

---

## 8. SUMMARY CONCLUSION

The Phase 1.5.1 Baseline Inventory is fully established. All code symbols, database tables, REST routes, governance holds, calculation engines, and test suites are mapped, verified, and protected under strict read-only inspection.
