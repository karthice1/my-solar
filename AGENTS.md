# AGENTS.md – PERMANENT AGENT INSTRUCTIONS & ENGINEERING DIRECTIVES

> **Target Codebase**: RENSUN Solar Intelligent Automation Platform  
> **Repository Path**: `/Users/karthik/tneb-account-extractor`  
> **Authority**: Project Owner / Senior Structural Reviewer  
> **Phase 0 Status**: `CLOSED_WITH_RETAINED_ENGINEERING_HOLDS`  
> **Phase 1 Status**: `AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION`  
> **Last Updated**: 2026-11-06 (Phase 0.16 Final Technical Reconciliation Incorporated)

All AI agents, pair programmers, and automated coding systems operating on this repository **MUST strictly abide by the rules, constraints, and architecture defined in this document**.

---

## 1. Frozen User-Approved Strategic Decisions

The project owner has explicitly approved and **FROZEN** the following three strategic decisions. These requirements are immutable:

### 🔒 Decision 1: Structural Automation Scope — COMPLETE [FROZEN]
The platform must automate the **complete structural engineering workflow**:
1. Structural input collection.
2. Roof geometry & obstacle modelling.
3. Solar panel positioning & row spacing.
4. Structural loading (dead, live, seismic).
5. Wind load calculations per **IS 875 (Part 3): 2015**.
6. 3D space frame structural finite element analysis.
7. Steel & aluminium member design (**IS 800: 2007 LSM, IS 801: 1975, Eurocode 9 / ADM**).
8. Connection, baseplate & chemical/mechanical anchorage design (**IS 456: 2000 / fib Bulletin 58**).
9. Existing building structural adequacy assessment with strict verification holds.
10. Transparent engineering verification reports with full formula derivations.
11. Comprehensive Bill of Quantities (BOQ), material cut-lists, and hardware schedules.
12. Automated CAD drafting and generation (multi-sheet DXF and coordinated PDF sets).

### 🔒 Decision 2: Rooftop Mounting Systems — ALL FOUR [FROZEN]
The platform must support **all four rooftop categories**:
- **System A**: Elevated steel rooftop structures (clearance 2.0 m to 3.5 m).
- **System B**: Low-height aluminium rail mounting systems (5° to 15° tilt).
- **System C**: Industrial metal-sheet roof mounting systems (trapezoidal, standing seam, sandwich panel).
- **System D**: Ballasted non-penetrating rooftop mounting systems (aerodynamic wind deflectors, concrete ballast blocks).

All four categories must be represented in the core architecture and unified data model.

### 🔒 Decision 3: CAD Delivery Architecture — BOTH [FROZEN]
The platform must implement:
1. **Core Programmatic DXF Generation (`ezdxf`)**: Standalone, 100% headless Python DXF generation producing complete fabrication-ready drawings (Sheets S01–S06). *Primary authoritative CAD source; functional independently of external CAD applications.*
2. **CADCraft Integration**: Bridge interface for optional AI agent-driven drafting and interactive web CAD viewing/editing.
3. **FreeCAD Integration**: Headless parametric 3D model generation (STEP, IFC BIM, GLTF/OBJ) via out-of-process CLI.
4. **Coordinated Multi-Sheet PDF Output**: Vector PDF drawing sets.

*Crucial Directive*: Core programmatic DXF and PDF generation **MUST remain fully functional independently of CADCraft and FreeCAD**. Never make the engineering calculation or drafting engine dependent on an external or experimental GUI application.

---

## 2. Refined Technical Engineering Directives (DEC-011 through DEC-018)

AI agents operating on this repository must enforce the following refined technical engineering directives:

### 2.1 Basic Wind Speed Mapping & Coordinates (DEC-011):
- Basic wind speed ($V_b$) mapped strictly to official administrative district boundaries in IS 875 (Part 3): 2015 Appendix A or Figure 1 ($33\text{--}55\text{ m/s}$).
- The 5 km coastal/terrain screening buffer is a **proposed project screening guideline**, not an explicit statutory clause.
- Enforce `WIND_COORD_UNVERIFIED_HOLD` until geographic GPS coordinates are verified.

### 2.2 Aerodynamics, Standards Hierarchy & Panel Torsion (DEC-012):
- **Three-Tier Aerodynamic Hierarchy**: Tier 1 is IS 875 (Part 3): 2015 Clause 7.3 & Table 6; Tier 2 is ASCE 7-16/22 Chapter 29 and SEAOC PV2-2017; Tier 3 is BLWT testing / validated CFD.
- **Open Canopy Net Pressure**: Open canopy frames (System A) are governed by IS 875 (Part 3) Clause 7.4.4 and Table 8 using net pressure coefficients ($C_n$). Enclosed-building internal pressure ($C_{pi}$) does NOT apply to open canopies.
- **Adverse Live Load for Stability**: For ballast sliding, uplift, and overturning checks against wind suction, transient live load is strictly excluded ($IL = 0$).
- **Screening Thresholds**: Screening parameters ($15^\circ$ tilt, $1.5\text{ m}$ setback, $300\text{ mm}$ overhang) are provisional project guidelines, not universal codal limits.
- **Accidental Torsion**: Accidental torsional eccentricity ($e = 0.10 \cdot b$) must be incorporated into purlin and rail checks.
- **Hold Enforcement**: Enforce `AERODYNAMIC_UNSUPPORTED_HOLD` and `WIND_TRANSFORM_UNVERIFIED_HOLD`.

### 2.3 Load Combinations, Design Codes & Dedicated Seismic Matrix (DEC-013):
- **Physical Imposed-Load Simultaneity**: Load combinations must distinguish between member-level governing live loads (max(ACT-IL-01, ACT-IL-02) on purlins/rails) and simultaneous global framing actions (simultaneous array load ACT-IL-02 and walkway load ACT-IL-04 on System A primary rafters and columns). Apply Table 4 leading factor (1.5 / 1.2) to leading live load and accompanying factor (1.05 / 0.53) to accompanying live load. Reconcile Table 4 Note 1 with dedicated construction-stage erection combination Row 4 (1.2 DL + 1.2 ER).
- **Complete IS 800 Table 4 Verbatim Transcription**: Verbatim transcription with all 12 columns non-truncated (including Crane Load in Strength and Serviceability), all 5 rows, both Row 3 sub-cases, and notes 1 to 5 verbatim against the official BIS publication.
- **Direct Independent Seismic Response Effects & Vertical Factor Formulation**: Seismic combinations must be constructed directly from independent signed response effects (E_X, E_Y, E_Z). In horizontal-dominant cases (Cases 1-16), vertical coefficient is 0.3 (net vertical force 0.45 E_Z in Comb 3, 0.36 E_Z in Comb 2). In vertical-dominant cases (Cases 17-24), vertical coefficient is 1.0 (net vertical force 1.5 E_Z in Comb 3, 1.2 E_Z in Comb 2). Effective normal reaction N_eff = 0.9 DL - 1.5 E_Z governs contact loss (when 1.5 E_Z >= 0.9 DL) and sliding resistance V_res = mu * N_eff.
- **24 Spatial Permutations Scope**: The 24 spatial permutations under Cl 6.3.4.1 apply statutorily when vertical shaking is triggered under Cl 6.3.3.1 (Amd 2). In Zone II/III for regular rooftop arrays, 24 spatial permutations represent voluntary project conservatism, not an exclusive statutory mandate.

### 2.4 Existing Building Adequacy & Ballast Friction Testing (DEC-007, DEC-014):
- Host building structural verification: prohibited unverified slab defaults; enforce `INSPECTION_REQUIRED_HOLD`.
- Coulomb sliding friction; mandatory on-site pull-out and tilt-table testing on actual membranes under dry/wet conditions; enforce `FRICTION_UNVERIFIED_HOLD`.

### 2.5 Aluminium Rail Capacity & Fastener Clamping (DEC-015):
- Structural aluminium design per IS 8147 / Eurocode 9 / AA ADM; stainless steel fasteners (A2-70/A4-70, ISO 3506); manufacturer torque-tension schedules; enforce `ALUMINIUM_DERIVATION_HOLD` and `FASTENER_TORQUE_UNVERIFIED_HOLD`.

### 2.6 Data Provenance & Zero-Uncertified Assumed Inputs (DEC-016):
- Five-tier provenance hierarchy; zero uncertified default parameters in calculation pipeline; enforce `ASSUMED_DATA_CERTIFICATION_HOLD`.

### 2.7 Numerical Matrix Stability & Multi-Element Diagnostics (DEC-017):
- **Matrix Diagnostics & Specific Remedies**: Rigorously differentiate 8 matrix regimes: redundant constraints, massless DOFs, common nullspaces, kinematic mechanisms, rigid-body modes, singular matrix pencils, indefinite stiffness, and ill-conditioning. Guyan condensation is NOT a universal remedy for singular pencils, failing when unconstrained massless mechanisms exist in the slave set (K_ss singular).
- **Cholesky Factorization Role**: Cholesky factorization failure is strictly a symmetric positive definite (SPD) diagnostic, not automatic proof of a kinematic mechanism. Inertia check via LDL^T factorization (n_-, n_0, n_+) is required for rigorous mechanism diagnosis.
- **Complete Mindlin-Reissner Virtual-Work Formulation**: Governing plate/shell formulation must maintain complete dimensional consistency across membrane, bending, and transverse shear strain energy, external work, boundary terms, and corner forces (R_c = 2 M_xy). Differentiate pointwise traction discontinuity in displacement FE from weak-form equilibrium and assembled nodal force cancellation.
- **Provisional Project Thresholds**: L_char = sqrt(A_array), kappa(K) < 10^8, and screening band 2.5-15 Hz are provisional project guidelines pending benchmark calibration.

### 2.8 Statutory Building Governance & Height Amendment (19.50 m) (DEC-018):
- **Authenticated Statutory Source Evidence**: All statutory citations must be traced to official Government Orders: G.O.(Ms.) No. 18 (4 Feb 2019) and G.O.(Ms.) No. 194 (4 Nov 2020), amending High-Rise threshold to height exceeding 19.50 m.
- **Parent Building vs Solar Appurtenance Scope**: High-Rise classification under Rule 36 applies to parent buildings exceeding 19.50 m, requiring RSE Grade-I review of host building reserve capacity. For Non-High-Rise parent buildings (<= 19.50 m), RSE Grade-II engineers are legally authorized under Annexure XVII to certify structural stability of the host building and the solar mounting structure.
- **Exact Experience Waiver Scope**: Experience waiver under G.O.(Ms.) No. 18 Annexure XVII waives only the condition that prior experience was gained under a registered engineer; it does not waive degree or minimum years of experience.
- **Hold Enforcement**: Enforce `DRAWING_UNVERIFIED_HOLD` and retain proposed `SEOR_CREDENTIAL_HOLD`.

### 2.9 Master Verification Hold Register (Exact Original 12 Holds Active):

### Master Verification Hold Register (Exact 12 Original Holds Active)

Every verification hold flag is maintained under its **exact canonical identifier**. All 12 original holds remain **ACTIVE AND ENFORCED**. In compliance with engineering audit guidelines, each prerequisite is rigorously classified into its precise governance category:
- **Statutory Requirement**: Explicitly mandated by an enacted Act, Rule, or referenced National Standard (NBC / IS Code / TNCDBR).
- **Project Engineering Prerequisite**: Required engineering calculation, material characterization, or site measurement to ensure physical structural safety.
- **Internal Quality-Control Requirement**: Software integrity control, execution diagnostic floor, or drawing delivery standard adopted by the project.
- **Professional Approval Requirement**: Formal sign-off and stamping mandated to be executed by a registered professional (SEOR / Proof Consultant).

#### Rigorous Classification of All 12 Original Verification Holds

| No. | Exact Canonical Hold Identifier | Governance Status | Associated Decision | Detailed Prerequisite Scope | Precise Governance Category | Designated Sign-Off Authority |
|:---:|:---|:---:|:---:|:---|:---:|:---|
| 1 | `INSPECTION_REQUIRED_HOLD` | **ACTIVE / RETAINED** | DEC-007 | Physical site structural audit report, parent building framing verification, and structural adequacy sign-off where as-built drawings are unavailable. | **Project Engineering Prerequisite** (Engineering verification of host structure capacity) | SEOR (Grade-I / Grade-II per building height) |
| 2 | `AERODYNAMIC_UNSUPPORTED_HOLD` | **ACTIVE / RETAINED** | DEC-012 | Independent boundary layer wind tunnel (BLWT) test report to IS 875 (Part 3) Clause 8.3 / ASCE 49-21, or CFD validation where module tilt exceeds codal tables ($> 15^\circ$). | **Project Engineering Prerequisite** (Aerodynamic force calibration for non-codal geometry) | Wind Engineering Specialist & SEOR |
| 3 | `WIND_COORD_UNVERIFIED_HOLD` | **ACTIVE / RETAINED** | DEC-011 | Certified site survey verifying GPS site boundary coordinates and radial distance to nearest IS 875: 2015 basic wind speed reference city. | **Internal Quality-Control Requirement** (Spatial database query precision) | Lead Structural Engineer / Surveyor |
| 4 | `WIND_TRANSFORM_UNVERIFIED_HOLD` | **ACTIVE / RETAINED** | DEC-012 | Numerical verification that module normal wind pressures are transformed into 3D Cartesian frame without sign errors, including panel torsional moment ($M_{\text{torsion}} = F_n \cdot e$). | **Internal Quality-Control Requirement** (Vector transformation software QA) | Structural Software Auditor |
| 5 | `VERTICAL_SEISMIC_APPLICABILITY_HOLD` | **ACTIVE / RETAINED** | DEC-013 | Technical screening determination against the 7 amended conditions of IS 1893: 2016 Clause 6.3.3.1 (Amd 2) to establish whether vertical seismic analysis is statutorily triggered. | **Statutory Requirement** (IS 1893: 2016 Cl 6.3.3.1) | Structural Engineer on Record (SEOR) |
| 6 | `LOAD_COMBINATION_PROVISIONAL_HOLD` | **ACTIVE / RETAINED** | DEC-013 | Dual-gate verification: statutory check of partial safety factors against IS 800 Table 4 & IS 1893 Cl 6.3.2.1 (Gate A), and numerical solver assembly verification (Gate B). | **Statutory Requirement** (IS 800: 2007 Section 3 / 5) | Proof Consultant / Senior Reviewer |
| 7 | `FRICTION_UNVERIFIED_HOLD` | **ACTIVE / RETAINED** | DEC-014 | Certified pull-slip static friction coefficient test report per ASTM C1028 / EN 13893 on host roof membrane under wet and dry conditions, or conservative factor $\mu \le 0.30$. | **Project Engineering Prerequisite** (Empirical contact safety factor calibration) | Geotechnical / Testing Agency & SEOR |
| 8 | `ALUMINIUM_DERIVATION_HOLD` | **ACTIVE / RETAINED** | DEC-015 | Certified manufacturer extrusion die drawings, metallurgical tensile coupon test report to IS 8147 / ASTM B221, and analytical derivation of effective section modulus ($Z_{eff}$). | **Project Engineering Prerequisite** (Material characterization & section property derivation) | Metallurgical Testing Lab & SEOR |
| 9 | `FASTENER_TORQUE_UNVERIFIED_HOLD` | **ACTIVE / RETAINED** | DEC-015 | Fastener manufacturer installation torque table, calibrated torque wrench procedure, and stainless steel A2-70 / A4-70 metallurgical test certificate. | **Internal Quality-Control Requirement** (Installation QA/QC & clamping integrity) | Site QA/QC Manager & Lead Erector |
| 10 | `NUMERICAL_INSTABILITY_HOLD` | **ACTIVE / RETAINED** | DEC-017 | Verification that global stiffness matrix $\mathbf{K}$ is non-singular, free of unconstrained mechanisms, well-conditioned ($\kappa(\mathbf{K}) < 10^{12}$), and residual forces satisfy $\|\mathbf{r}\| \le 10^{-5}$. | **Internal Quality-Control Requirement** (Solver numerical stability & convergence check) | Computational Mechanics Specialist |
| 11 | `ASSUMED_DATA_CERTIFICATION_HOLD` | **ACTIVE / RETAINED** | DEC-016 | Written formal certification and sign-off by SEOR on any unmeasured host building dimension, member cross-section, or assumed material strength (Tier-1 data). | **Professional Approval Requirement** (Professional assumption liability sign-off) | SEOR (Grade-I / Grade-II) |
| 12 | `DRAWING_UNVERIFIED_HOLD` | **ACTIVE / RETAINED** | DEC-018 | Execution of the mandatory 4-gate verification sign-off across Preparation, Checking, SEOR Approval, and Statutory Review. Mandatory PRELIMINARY watermark. | **Professional Approval Requirement & Internal QC** (Drawing release protocol) | SEOR & Statutory Authority (where applicable) |

#### Proposed Supplemental Governance Item (Pending Owner Approval)

| Proposed Identifier | Proposed Governance Category | Associated Decision | Proposed Scope & Rationale | Status |
|:---|:---|:---:|:---|:---:|
| `SEOR_CREDENTIAL_HOLD` | Supplemental Professional Approval Control | DEC-018 | Verification of Registered Structural Engineer (RSE) credentials against CMDA/DTCP registration registers, specifically verifying that High-Rise installations ($> 19.50\text{ m}$) are certified exclusively by RSE Grade-I per TNCDBR-2019 Annexure XVII. | **PROPOSED SUPPLEMENTAL ITEM — PENDING FORMAL OWNER ACCEPTANCE (DOES NOT REPLACE ANY ORIGINAL HOLD)** |

## 3. Phase-Gate Authorization Protocol & Working Tree Rules

Advancement through project phases is governed by strict stage-gates:
- **Phase 0 Status**: `CLOSED_WITH_RETAINED_ENGINEERING_HOLDS`.
- **Phase 1 Status**: `AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION`.
- **Phases 2 through 6**: `LOCKED`.

### Working Tree Governance:
- All tracked application source code ([`server.py`](file:///Users/karthik/tneb-account-extractor/server.py), [`tneb_tool.py`](file:///Users/karthik/tneb-account-extractor/tneb_tool.py), [`solar_engine/`](file:///Users/karthik/tneb-account-extractor/solar_engine), [`quotation/`](file:///Users/karthik/tneb-account-extractor/quotation), [`templates/`](file:///Users/karthik/tneb-account-extractor/templates)) must have **zero modifications**.
- Newly added documentation files ([`AGENTS.md`](file:///Users/karthik/tneb-account-extractor/AGENTS.md), [`docs/`](file:///Users/karthik/tneb-account-extractor/docs)) remain intentionally untracked until approved by the owner. Do not stage or commit untracked documentation solely to make Git status appear clean.

> [!CAUTION]
> **STRICT PROHIBITION**:
> No agent is authorized to begin implementation of Phase 1 or any subsequent phase without explicit, written authorization from the project owner. Approving requirements or Phase 0 documentation DOES NOT authorize Phase 1 coding.

---

## 4. Preservation of Existing Core Functionality

The existing TNEB Account Extractor and Solar Quotation Builder application is in **production status**. Agents must never break, degrade, or disrupt existing functionality:

1. **TNEB Scraping & Automation (`tneb_tool.py`)**:
   - Optical CAPTCHA OCR solving must remain intact.
   - Dynamic credential authentication must remain intact.
   - Exact consumer number matching must remain intact.
   - Primary consumer account protection must **NEVER** be bypassed or weakened. The primary account must never be deleted under any circumstance.
   - Verified cleanup of temporary connections must remain intact.
2. **Solar Quotation Engine (`solar_engine/`, `quotation/`)**:
   - Monthly and bi-monthly TNEB billing cycle analysis must remain intact.
   - Solar sizing based on past consumption ($\text{Capacity} = \text{Units} / 1450$) must remain intact.
   - TANGEDCO 100% sanctioned load net-metering limit rules must remain intact.
   - PM Surya Ghar central subsidy calculations (₹30k / ₹60k / ₹78k) must remain intact.
   - SQLite quotation database (`quotations.db`) and sequential numbering (`RENSUN/YYYY/XXXX`) must remain intact.
   - 5-page Playwright PDF quotation generator must remain intact.
3. **Regression Testing Requirement**:
   - Any agent modifying or adding code must run both test suites:
     - `python3 test_quotation_system.py` (20 tests must pass).
     - `python3 test_exact_matching.py` (23 tests must pass).

### Before/After Hold Identifier & Decision Mapping Table (Historical Migration & Scope)

| No. | Hold Identifier | Original Decision Mapping (Phase 0.1 / 0.10) | Authoritative Decision Mapping (Phase 0.14) | Subsystem Engineering Scope | Historical Traceability & Rationale for Remapping | Universal Statutory vs Internal Project Classification |
|:---:|:---|:---:|:---:|:---|:---|:---|
| 1 | `INSPECTION_REQUIRED_HOLD` | DEC-007 | **DEC-007 / DEC-010** | Existing Building Structural Adequacy | Retained continuously. Prohibits arbitrary assumed slab properties (M20/100mm) without NDT/rebar scans or SEOR certification. | **Condition-Based**: Mandatory when host building structural records are missing. |
| 2 | `AERODYNAMIC_UNSUPPORTED_HOLD` | DEC-010 | **DEC-012** | Module Aerodynamic Database Scope | In early drafts (Phase 0.1), boundary layer wind tunnel (BLWT) testing was grouped under DEC-010 as a "Level 3 experimental solver validation" method. In Phase 0.2, aerodynamic methodologies and wind pressure coefficients were centralized into DEC-012. Remapped to DEC-012 to maintain aerodynamic integrity. | **Project-Specific**: Triggered when tilt $	heta > 10^\circ$ or $h/H > 0.05$ exceeds codified database scope. |
| 3 | `WIND_COORD_UNVERIFIED_HOLD` | DEC-011 | **DEC-011** | Geographic Coordinates & Wind Zone | Restored strictly to DEC-011. Governs verification of site latitude/longitude against IS 875 (Part 3) Figure 1 basic wind speed contours ($V_b = 33	ext{--}55	ext{ m/s}$). | **Universal Statutory**: Mandatory compliance with IS 875 (Part 3) Figure 1. |
| 4 | `WIND_TRANSFORM_UNVERIFIED_HOLD` | Ambiguous with DEC-011 | **DEC-012** | Wind Vector Transformation & Panel Torsion | In Phase 0.10, local-to-global force transformation was ambiguously merged with the coordinate hold. In Phase 0.11/0.12, it was separated into an independent hold under DEC-012 to govern 3D vector transformations and panel accidental torsion ($M_{torsion} = F_n \cdot e$). | **Universal Engineering**: Verification of vector mechanics algorithms. |
| 5 | `VERTICAL_SEISMIC_APPLICABILITY_HOLD` | DEC-013 | **DEC-013** | Vertical Seismic Shaking Applicability | Retained continuously under DEC-013. Aligned strictly with amended IS 1893: 2016 Clause 6.3.3.1 (7 statutory triggers). | **Statutory Screening**: Triggered only if Clause 6.3.3.1 criteria are met. |
| 6 | `LOAD_COMBINATION_PROVISIONAL_HOLD` | DEC-013 | **DEC-013** | Load Combination Envelopes | Retained continuously under DEC-013. Reconciled with published IS 800 Table 4 and dedicated seismic combinations. | **Universal Statutory**: Mandatory compliance with BIS design combinations. |
| 7 | `FRICTION_UNVERIFIED_HOLD` | DEC-014 | **DEC-014** | Ballast Sliding Stability | Retained continuously under DEC-014. Formulates Coulomb friction and mandates on-site pull-out / tilt-table testing under wet and dry conditions. | **Project-Specific**: Mandatory for unanchored ballasted installations. |
| 8 | `ALUMINIUM_DERIVATION_HOLD` | DEC-015 | **DEC-015** | Aluminium Rail Section Capacity | Retained continuously under DEC-015. Governs thin-walled extrusion design per Eurocode 9 / IS 8147, prohibiting transfer of thin-steel formulas to aluminium. | **Universal Statutory**: Mandatory compliance with structural aluminium codes. |
| 9 | `FASTENER_TORQUE_UNVERIFIED_HOLD` | DEC-016 | **DEC-015** | Fastener Clamping & Torque Calibration | In Phase 0.10, torque values were treated as an assumed data parameter under DEC-016 (data provenance). In Phase 0.11/0.12, torque-tension calibration ($T = k \cdot d \cdot F$), thin aluminium slot pull-out, and clamp relaxation were recognized as structural connection matters directly belonging to DEC-015. Remapped to DEC-015. | **Project-Specific**: Quality control verification for clamping security. |
| 10 | `NUMERICAL_INSTABILITY_HOLD` | DEC-017 | **DEC-017** | Solver Stability & Equilibrium Residuals | Retained continuously under DEC-017. Reconciles active mass subspace, rigid-body restraint $\operatorname{rank}(\mathbf{C}oldsymbol{\Phi}_{RB}) = r_{RB}$, DOF scaling, and vector equilibrium residuals. | **Universal Engineering**: Mandatory verification of numerical stability. |
| 11 | `ASSUMED_DATA_CERTIFICATION_HOLD` | DEC-018 | **DEC-016** | Engineering Data Provenance | In Phase 0.10, DEC-018 combined drawing watermarks, SEOR licensing, and assumed data. In Phase 0.11, DEC-016 was specifically defined as "Decoupling Evidence Provenance from Engineering Approval", making it the dedicated home for zero-uncertified data governance, while DEC-018 focused on statutory licensing and TNCDBR rules. | **Universal Engineering**: Quality assurance preventing unverified inputs. |
| 12 | `DRAWING_UNVERIFIED_HOLD` | DEC-019 | **DEC-018** | Statutory Drawing Governance & Watermark | DEC-019 was initially proposed as a separate decision for "CAD Delivery Architecture". However, drawing governance, the 4-Gate AFC release protocol, and preliminary watermarks were directly bound to SEOR statutory licensing and TNCDBR Rule 24/35. Consolidated under DEC-018. | **Universal Statutory / Project Control**: Stamped drawings mandatory for statutory permits; watermark is project quality control. |


