# RENSUN SOLAR – STRUCTURAL AUTOMATION PHASE TRACKER

> **Document Status**: ACTIVE & REFINED IN PHASE 0.16
> **Last Updated**: 2026-11-06 (Phase 0.16 Final Technical Reconciliation)
> **Phase 0 Authorization**: `CLOSED_WITH_RETAINED_ENGINEERING_HOLDS`  
> **Phase 1 Authorization**: `AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION`  
> **Working Tree Governance**: Clean tracked application code (0 modifications); untracked documentation files (`AGENTS.md`, `docs/`) pending owner acceptance.

---

## Phase Lifecycle Governance

Implementation is governed by strict stage-gates. Advancing to any subsequent phase requires:
1. Complete verification of previous phase deliverables against acceptance criteria.
2. 100% regression test pass on existing TNEB extraction and solar quotation suites.
3. Clean Git working tree with zero unauthorized modifications to tracked application code.
4. Formal presentation of deliverables and explicit written sign-off from the project owner.

---

## Master Phase Status Board

| Phase | Title | Scope Summary | Status | Gate Status |
|---|---|---|---|---|
| **Phase 0** | **Audit & Architecture Blueprint** | Existing system audit, open-source library evaluation, IS code roadmap, CAD architecture, folder structure, refined technical decisions, permanent memory documentation. | **COMPLETE** | **`CLOSED_WITH_RETAINED_ENGINEERING_HOLDS`** |
| **Phase 1** | **Structural Data Model & Wind Engine** | Unified geometry model, panel layout generator, IS 875 (Part 3): 2015 wind load calculation engine ($V_b, k_1..k_4, p_z, C_N, C_{pe}, C_{pi}$) for all Tamil Nadu wind zones. | **PENDING** | **`AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION`** |
| **Phase 2** | **Frame Analysis & IS Code Member Design** | 3D space frame direct stiffness solver, rotational spring joints, IS 800:2007 (LSM Steel), IS 801:1975 (Cold-Formed), Eurocode 9 / ADM / IS 8147 (Aluminium) design verification. | **PENDING** | **LOCKED (Not Authorized)** |
| **Phase 3** | **Rooftop Systems (A, B, C, D) & Building Check** | Implement Elevated Steel (A), Low-Height Al (B), Metal Sheet (C), Ballasted (D), fib/IS 456 anchor bolt design, and existing building slab/purlin check with Verification Holds. | **PENDING** | **LOCKED (Not Authorized)** |
| **Phase 4** | **Automated 2D CAD Drafting (ezdxf) & PDF** | Headless multi-sheet DXF generator (S01-S06), dimensioning, callouts, title blocks, preliminary watermark, and multi-page vector PDF drawing compiler. | **PENDING** | **LOCKED (Not Authorized)** |
| **Phase 5** | **CADCraft & FreeCAD Integration** | CADCraft interactive schema adapter, FreeCAD headless 3D parametric generator (STEP/IFC/GLTF), BIM export via out-of-process CLI daemon. | **PENDING** | **LOCKED (Not Authorized)** |
| **Phase 6** | **UI Visualizer & System Validation** | 3D WebGL rooftop visualizer in dashboard, structural tab integration, comprehensive 4-level benchmark validation suite. | **PENDING** | **LOCKED (Not Authorized)** |

---

## Master Verification Hold Register

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

## Detailed Milestone Checklist

### Phase 0: Audit & Architecture Documentation (`CLOSED_WITH_RETAINED_ENGINEERING_HOLDS`)
- [x] Comprehensive audit of existing RENSUN web application, database, and APIs.
- [x] TNEB integration preservation and zero-regression audit (verified 100% offline mock execution with zero browser instances or network calls; call-graph verified).
- [x] Complete open-source library and repository evaluation (PyNiteFEA, ezdxf, FreeCAD, CADCraft, OpenSeesPy).
- [x] License and dependency compatibility matrix (FreeCAD CLI subprocess isolation, CADCraft optional decoupled bridge, LGPL-2.1 compliance without in-process linkage).
- [x] Approved target architecture covering all four rooftop mounting systems (A, B, C, D).
- [x] Pure Python structural calculation engine architecture with decoupled 7-stage pipeline.
- [x] Indian Standard (IS) code implementation roadmap (IS 875 Pt 3, IS 800, IS 801, IS 8147, IS 456).
- [x] Refined Galvanization & Corrosion Protection framework (DEC-004: IS 4759 thickness-based HDG, IS 277 Z275, PosMAC separate spec, ISO 9223 C1-C5M).
- [x] Refined Design Life (DEC-005: 50-yr default, decoupled from module warranty, IS 875 Table 1 $k_1$).
- [x] Refined Overhang Engineering (DEC-006: multi-criteria bending, deflection, uplift, and manufacturer clamping zones; 300 mm warning threshold).
- [x] Refined Building Adequacy (DEC-007: M20/100mm default prohibited; mandatory `INSPECTION_REQUIRED_HOLD` check).
- [x] Refined Cyclonic Factor $k_4$ (DEC-008: strict IS 875:2015 Clause 6.3.4 based on geographical inputs; blanket 60km removed).
- [x] Refined Waterproofing (DEC-009: context-specific details for membrane, screed, metal sheet, standing seam clamp, ballasted pads; 150mm universal pedestal removed).
- [x] Refined Primary Validation (DEC-010: analytical benchmarks, published standards, dual open-source solvers; STAAD.Pro dependency removed).
- [x] Authoritative BIS Wind Database Verification & Site Coordinates (DEC-011: Appendix A & Fig 1, municipal screening defaults marked provisional, GIS coordinates required for certified calculation; WIND_COORD_UNVERIFIED_HOLD).
- [x] Standards Hierarchy, Distinct Aerodynamic Methodologies & Vector Transformation (DEC-012: Tier 1 statutory BIS/TNCDBR, Tier 2 adopted international EN 1999 / ASCE 7 / SEAOC, Tier 3 product test standards, Tier 4 manufacturer MTCs; distinct aerodynamic procedures for all 4 systems; vector coordinate transformation and panel torsion; WIND_TRANSFORM_UNVERIFIED_HOLD, AERODYNAMIC_UNSUPPORTED_HOLD).
- [x] Complete Published IS 800 Table 4, Design Code Scope & Behaviour-Specific Seismic (DEC-013: Faithful published IS 800 Table 4 preserved with DL, IL leading/acc, WL/EL, AL; 0.6 factor located strictly in WL/EL column under DL+IL+CL+WL/EL; 0.53 factor for accompanying IL in wind-leading; 0.35 factor for accompanying IL in DL+IL+AL; DL+ER corrected to 1.2 DL + 1.2 IL without 0.9; 0.9 DL strictly in DL+WL/EL; actual BIS footnotes restored; derived solar matrix with CL=0, AL=0 kept strictly separate; separate design code routes for hot-rolled steel IS 800, cold-formed steel IS 801/AISI S100, extruded aluminium IS 8147/EN 1999, hybrid fasteners; amended IS 1893: 2016 Cl 6.3.3.1 (Amendment No. 2, Nov 2020) vertical seismic triggers without arbitrary statutory 12m/1.5m thresholds; 24 spatial permutations under Cl 6.3.4.1; LOAD_COMBINATION_PROVISIONAL_HOLD, VERTICAL_SEISMIC_APPLICABILITY_HOLD).
- [x] Friction Factor Scope & Anti-Double-Counting (DEC-014: EN 1990:2002 Annex D Table D.1 fractile factors $k_n$, $n=30 \implies 1.73$; clarification of D7.2 conversion vs D8.2 model evaluation scope; standard-supported vs project-specific factors; non-universal provisional $\gamma_{M,friction}=1.5$ baseline; anti-double-counting framework; FRICTION_UNVERIFIED_HOLD).
- [x] Aluminium Rail & Fastener Verification Protocol (DEC-015: Inapplicable timber standards purged; EOTA TR 063 & EAD 330030-00-0601 scope verified; prohibition on transferring thin-steel equations to proprietary aluminium extrusions; provisional linear interaction; explicit tension/shear failure modes; ALUMINIUM_DERIVATION_HOLD, FASTENER_TORQUE_UNVERIFIED_HOLD).
- [x] Orthogonal Data Provenance (PROV) & Review Status (REV) Decoupling (DEC-016: 4 provenance tiers, 3 review statuses; assumed data blocks certification; ASSUMED_DATA_CERTIFICATION_HOLD).
- [x] Rigorous Numerical Diagnostics, Rank Stability & Residual Scaling (DEC-017: Subspace projection verifying full restraint of rigid-body basis $\operatorname{rank}(\mathbf{C}\boldsymbol{\Phi}_{RB}) = r_{RB}$ replacing unconditional $\ge 6$; graph connectivity limitations; coordinate scaling / dimensional homogenization of mass matrix $\mathbf{M}_{dim} = \mathbf{D}_m \mathbf{M} \mathbf{D}_m$ using $L_{char}$; deterministic rank tolerance $\tau_m = \epsilon_{mach} \cdot n_{dof} \cdot \sigma_{\max}(\mathbf{M}_{dim})$; materially negative mass eigenvalues trigger `MASS_MATRIX_INDEFINITE_ERROR` and retain hold; infinite eigenvalue filtering; consistent mass coupling; Guyan recovery conditions; Group-Based Symmetric Scaling vs Per-DOF Point-wise Jacobi Equilibration; nonlinear indefinite matrices; Sylvester inertia via $LDL^T$ pivots; independent force and moment equilibrium about $(0,0,0)$ with explicit $F_{ref}, M_{ref}$; physical member action scale; shell patch boundary edge aggregation without double-counting internal edges; mesh-refinement sensitivity check; provisional screening floors 1 kN / 1 kNm; project diagnostic thresholds 1e-12, 1e12, 1e-4; NUMERICAL_INSTABILITY_HOLD).
- [x] Actual TNCDBR-2019 Scope, 19.50 m Height Amendment & Registration Categories (DEC-018: Incorporating G.O.(Ms.) No. 194 dated 26 October 2026 substituting 19.50 m for applicable 18.30 m references in Rule 2 and Rule 35; professional categories delineated; Grade-I ME/PhD + 5 yrs authorized for all structures including high-rise > 19.50 m; Grade-II BE + 3 yrs or ME + 1 yr strictly restricted to Rule 35(1) small non-high-rise <= 19.50 m; 10-year experience waiver running 4th February 2019 to 3rd February 2029 waives only experience under SEOR without relaxing 5-yr/3-yr minimum; four distinct responsibilities: preparation, independent check, professional approval, statutory permission; 4-condition AFC release protocol; mandatory PRELIMINARY watermark; DRAWING_UNVERIFIED_HOLD).
- [x] All five required project artifacts finalized and placed in project directory and brain directory.
- [x] Phase 0.16 Documentation-Only Correction & Acceptance Readiness Audit: Eliminated Table 4 header display truncation and provided complete 12 columns, 5 rows, both Row 3 sub-cases, notes 1-5, and RENSUN combination mapping; resolved imposed-load simultaneity on purlins (max(IL_point, IL_dist)) vs System A primary frames (simultaneous array + walkway live loads with leading/accompanying factors per Table 4) and reconciled Table 4 Note 1 with dedicated erection row (1.2 DL + 1.2 ER); eliminated universal 0.45 E_Z shorthand and derived complete vertical seismic directional schedule (0.3 E_Z -> 0.45 E_Z / 0.36 E_Z in horizontal-dominant cases vs 1.0 E_Z -> 1.5 E_Z / 1.2 E_Z in vertical-dominant cases, effective normal force N_eff = 0.9 DL - 1.5 E_Z, contact loss, sliding, overturning); separated statutory triggers of IS 1893 Cl 6.3.3.1 Amd 2 from combination rules Cl 6.3.4.1/6.3.4.2 and voluntary project conservatism; restored all 12 original canonical holds with 4-tier governance taxonomy and isolated SEOR_CREDENTIAL_HOLD as proposed supplemental item; transcribed unabbreviated TNCDBR statutory text and separated parent building classification (> 19.50 m High-Rise) from solar rooftop appurtenances (<= 19.50 m Grade-II); reconciled numerical diagnostics across 8 matrix regimes, demonstrated Guyan condensation limitations on singular pencils, and retained Cholesky SPD diagnostic distinction; completed dimensionally consistent Mindlin-Reissner virtual-work formulation and reconciled pointwise traction discontinuity vs weak-form equilibrium vs assembled nodal cancellation; rechecked wind assumptions (open canopy Table 8 C_n vs C_pi, adverse live load IL = 0 for ballast sliding); verified clean Git working tree (0 staged, 0 modified tracked files); stopped strictly at CLOSED_WITH_RETAINED_ENGINEERING_HOLDS and AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION.
- [x] Phase 0.15 Documentation Correction & Independent Acceptance Audit: Resolved imposed-load simultaneity conflict (member-level max(IL_point, IL_dist) vs simultaneous IL_array + IL_walkway on primary frames); reproduced complete non-truncated IS 800: 2007 Table 4 verbatim with all 12 columns, 5 rows, both sub-cases, and notes 1-5; corrected seismic algebra by defining direct independent signed response effects (E_X, E_Y, E_Z) eliminating double-counted companion forces; full 24 spatial permutations schedule citing IS 1893 Cl 6.3.4.1 with verbatim applicability triggers of amended Cl 6.3.3.1; restored exact 12 original hold identifiers (including FRICTION_UNVERIFIED_HOLD and ALUMINIUM_DERIVATION_HOLD) and separated SEOR_CREDENTIAL_HOLD as proposed supplemental item; attached unabbreviated verbatim statutory text for TNCDBR G.O. 18, G.O. 194, Rules 2(43), 23, 24, 35, 36, Annexure XVII, and experience waiver boundary; corrected numerical-method classifications (regular vs singular pencils, shift-and-invert scope, Cholesky failure as SPD diagnostic, proposed project thresholds); corrected Mindlin-Reissner shell formulation (pointwise traction discontinuity vs weak-form equilibrium vs assembled nodal cancellation); conducted semantic audit with discrepancy table across all 5 canonical documents; verified clean Git working tree (0 staged, 0 modified tracked files); stopped strictly at CLOSED_WITH_RETAINED_ENGINEERING_HOLDS and AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION.
- [x] Phase 0.14 Final Technical Defect Correction: Completely eliminated duplicate imposed loads ($IL_{lead} + IL_{acc}$), established Physical Load-Action Register across Systems A, B, C, D and single-IL combination matrix; completed full 11-column IS 800: 2007 Table 4 transcription verbatim; step-by-step mathematical derivation of seismic schedules from IS 1893: 2016 Cl 6.3.2.1, 6.3.3.1, 6.3.4.1, 6.4.6, and Table 10; completed 24-case spatial permutation schedule under 30% rule; established 12-hold historical migration table; attached verbatim primary statutory text for TNCDBR G.O. 194, Rule 2(43), Rule 23, Rule 24, Rule 35, Annexure XVII, and G.O. 18; reconciled numerical diagnostics (model-dependent $L_{char}$, physical/scaled coordinate transformations, singular pencil vs massless DOFs vs rigid body modes, support restraint vs internal stability, proposed project diagnostic thresholds, benchmarks marked pending execution); Mindlin-Reissner shell boundary equilibrium formulation with shared-edge cancellation (retaining validation required status); clean Git working tree (0 staged, 0 modified tracked files); stop at `CLOSED_WITH_RETAINED_ENGINEERING_HOLDS` and `AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION`.

### Phase 1: Structural Data Model & Wind Engine (`AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION`)
- [ ] Initialize `structural_engine/` modular structure.
- [ ] Implement `RoofGeometry` and `Obstacle` 3D bounding polygon models.
- [ ] Implement `SolarArrayArrangement` (tilt, pitch, portrait/landscape, row spacing, shadow calculation).
- [ ] Implement authoritative BIS wind speed database ($V_b$ per district per Appendix A).
- [ ] Implement IS 875 (Part 3): 2015 wind engine ($V_z = V_b \cdot k_1 \cdot k_2 \cdot k_3 \cdot k_4$, $p_z = 0.6 V_z^2$).
- [ ] Implement rooftop aerodynamic procedures for all 4 systems (Table 8 canopy, NBC 2016 low-height, Table 5/6 metal sheet, console drag/lift).
- [ ] Implement `AERODYNAMIC_UNSUPPORTED_HOLD` trigger logic.
- [ ] Unit tests for wind pressure against standard IS 875 worked examples.

### Phase 2: Frame Analysis & Member Design Engines [LOCKED]
- [ ] Implement 3D Space Frame direct stiffness solver (stiffness matrix formulation, 6 DOF per node).
- [ ] Implement rotational spring elements ($K_\theta = S_{j,ini}$) for semi-rigid joint modeling.
- [ ] Implement full 16-case load combination generator (ULS-01 to ULS-11, SLS-01 to SLS-05).
- [ ] Implement Indian structural steel section library (SHS, RHS, ISMC channels, ISA angles, C/Z purlins).
- [ ] Implement IS 800:2007 Limit State Method design checks (tension, compression buckling, bending, shear, combined biaxial bending).
- [ ] Implement IS 801:1975 cold-formed light gauge steel design checks.
- [ ] Implement IS 8147 / Eurocode 9 aluminium extruded rail design checks (screw-channel lip tear-out, local buckling).
- [ ] Implement module overhang multi-criteria engineering checks.

### Phase 3: All 4 Rooftop Topologies & Existing Building Verification [LOCKED]
- [ ] System A: Elevated Steel Structure design module (columns, rafters, purlins, knee/cross bracings).
- [ ] System B: Low-Height Aluminium Rail Structure design module (L-feet, mid/end clamps, rails).
- [ ] System C: Industrial Metal-Sheet Structure design module (mini-rail, standing seam clamp, sheet purlin load check).
- [ ] System D: Ballasted Structure design module (aerodynamic wind deflectors, concrete ballast weight, verified friction checks).
- [ ] Connection & Baseplate design module (7 failure modes, weld sizes, stiffener plates, baseplate thickness per IS 800).
- [ ] Anchor bolt design module (chemical/mechanical anchor pullout, concrete cone shear per IS 456 / ACI 318).
- [ ] Existing building adequacy check with 5-tier data provenance and mandatory `INSPECTION_REQUIRED_HOLD`.

### Phase 4: Headless ezdxf Automated Drafting & PDF [LOCKED]
- [ ] Programmatic DXF generator using `ezdxf` with layer definitions, linetypes, colors, and line weights.
- [ ] Standard title block generator with automated project metadata.
- [ ] Mandatory "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION" watermark renderer.
- [ ] Sheet S01: General Notes, Code Citations, Coating Specs & Design Criteria.
- [ ] Sheet S02: Roof Layout Plan & Coordinate Grid.
- [ ] Sheet S03: Structural Framing Plan & Member Schedule.
- [ ] Sheet S04: Elevations, Cross Sections & Bracing Details.
- [ ] Sheet S05: Baseplate, Anchorage & Context-Specific Waterproofing Details.
- [ ] Sheet S06: Member Cut-List, Hardware & Bill of Quantities (BOQ).
- [ ] Automated multi-page vector PDF compiler for A3/A2 drawing sets.

### Phase 5: CADCraft & FreeCAD Integration [LOCKED]
- [ ] CADCraft JSON scene serializer and drawing command interface.
- [ ] FreeCAD headless script bridge (out-of-process CLI `freecadcmd`).
- [ ] Automated 3D solid geometry generation (STEP and IFC BIM formats).
- [ ] Lightweight 3D GLTF/OBJ export for web rendering.

### Phase 6: Web UI Integration & Comprehensive Validation [LOCKED]
- [ ] Add "Structural Engineering & CAD" tab to existing responsive dashboard in `templates/index.html`.
- [ ] Three.js / WebGL interactive 3D rooftop and structural framing viewer.
- [ ] Dynamic parameter adjustments (structure height, wind speed, tilt, member profiles) with live recalculation.
- [ ] Instant DXF and structural report download endpoints in `server.py`.
- [ ] Chartered Structural Engineer digital signature and stamp integration for AFC drawing release.
- [ ] 4-Level benchmark validation test suite comparing output against closed-form analytical solutions and dual open-source solvers.
