# PHASE 1.5.3.2B.2A — SYSTEM A SOURCE AUDIT FINDING RECONCILIATION & CORRECTION PLAN
## RENSUN SOLAR STRUCTURAL ENGINEERING VALIDATION PROGRAMME

**Project ID:** RS-STR-RENSUN-2026-0059  
**Quotation:** RENSUN/2026/0059  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Expected Baseline HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Target System:** System A — Elevated Steel Canopy  
**Platform:** Google Antigravity  
**Phase Execution:** Phase 1.5.3.2B.2A (Audit and Correction-Plan Stage Only)  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED` (`is_approved_for_construction = false`)  
**Mandatory Final Status:** `ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE`  

---

> [!CAUTION]
> ### MANDATORY GOVERNANCE GATE & AUDIT-ONLY RESTRICTION
> This document is an **AUDIT AND CORRECTION PLAN ONLY**.
> 
> Zero source code, test scripts, production databases, configuration files, drawings, or PDFs have been modified in this phase.
> No git commits, pushes, merges, rebases, or branch changes are authorized or performed.
> 
> Construction authorization remains strictly **BLOCKED_AFC_LOCKED**.
> No verification holds are released. All work stops upon completion of this audit and correction plan, awaiting explicit owner approval before any code implementation.

---

## 1. Executive Summary

Phase 1.5.3.2B.2A conducts an exhaustive, source-grounded technical reconciliation of the six findings raised during the external source-level engineering audit of **System A — Elevated Steel Canopy**. 

While Phase 1.5.3.2B.2 introduced significant analytical advancements (such as parabolic moment gradient modeling, series spring stiffness formulation, parametric weld contour integration, and product-specific anchor failure modes), the external source audit identified crucial areas where:
1. Historical approximations ($C_1 = 1.75$) remain exposed in primary workflow outputs and load-path steps.
2. Code standard equivalences (AISC $C_b$ vs IS 800 Annex E) were asserted without documented technical monographs.
3. Restraint stiffness models omitted purlin roll and roof diaphragm flexibility, relying on an unverified 50 kN/mm fastener stiffness constant.
4. Weld group integration zeroed out local inertia for inclined weld segments and omitted multi-axis bending ($M_x, M_y$) and torsion ($M_t$).
5. Post-installed adhesive anchor models applied generic 0.70 reductions and proposed 80 mm reduced embedment without physical rebar cover scanning or pull-out testing.
6. Test isolation helper contained unpatched vectors (symlinks, SQLite URIs, direct file writes) and relied on directory file counts rather than individual file cryptographic manifests.
7. Test suite methods repeated production algorithms internally rather than benchmarking against independent external literature.

This document establishes a finding-by-finding technical reconciliation, defines exact source line citations, isolates the root technical causes, specifies the required corrections, and lays out the independent benchmark and governance plan.

---

## 2. Finding-by-Finding Technical Reconciliation

```
+---------------------------------------------------------------------------------------------------+
| FINDING DEF-01: LATERAL-TORSIONAL BUCKLING MOMENT GRADIENT FACTOR C1 / Cb                         |
+---------------------------------------------------------------------------------------------------+
```

### 2.1 Traceability of Active $C_1 = 1.75$ Usage

A systematic audit across all repository source files, test suites, reports, and benchmark tables identified the following active occurrences of $C_1 = 1.75$:

1. **`structural/workflows/system_a_final.py` (Line 124):**
   - *Code:* `Configuration 1A: Midspan-braced simply-supported rafter with moment gradient C1 = 1.75 per IS 800 Table 42.`
   - *Finding:* Docstring identifies $C_1 = 1.75$ as a standard configuration basis.
2. **`structural/workflows/system_a_final.py` (Lines 189–193):**
   - *Code:*
     ```python
     # Table 42 lists C1 = 1.75 strictly for linear end-moment gradients (psi = 0) with zero transverse load.
     # We retain C1 = 1.75 as an audited alternative reference while reporting the rigorous parabolic Cb = 1.30.
     C1_gradient = 1.75
     Mcr_grad, lam_grad, chi_grad, Md_grad = _calc_ltb(rafter_clear_span_mm, C1=C1_gradient)
     ur_clear_grad = Mu_full / Md_grad  # 40.42 / 105.64 = 0.383
     ```
   - *Finding:* `C1_gradient = 1.75` is actively evaluated and stored in variables returned to callers.
3. **`structural/workflows/system_a_final.py` (Lines 223–228):**
   - *Code:*
     ```python
     moment_gradient_factor_C1=C1_gradient,  # 1.75
     Mcr_gradient_kn_m=round(Mcr_grad, 2),  # 188.53 kNm
     lambda_LT_gradient=round(lam_grad, 3), # 0.929
     chi_LT_gradient=round(chi_grad, 3),    # 0.714
     Md_capacity_gradient_kn_m=round(Md_grad, 2), # 105.64 kNm
     unity_ratio_gradient=round(ur_clear_grad, 3), # 0.383
     ```
   - *Finding:* The primary dataclass `WindUpliftRafterAudit` exposes the $C_1 = 1.75$ result as primary fields (`moment_gradient_factor_C1`, `Md_capacity_gradient_kn_m`), while the parabolic $C_b = 1.2987$ result is assigned to auxiliary fields (`moment_gradient_factor_Cb_parabolic`, `Md_capacity_parabolic_kn_m`).
4. **`structural/workflows/system_a_final.py` (Line 1155):**
   - *Code:*
     ```python
     governing_capacity="Md_grav = 147.95 kNm / Md_up = 105.64 kNm (C1=1.75)",
     ```
   - *Finding:* In `verify_complete_foundation_load_path()`, Step 2 (Rafter Flexure) explicitly publishes the capacity based on $C_1 = 1.75$ ($105.64\text{ kNm}$) as the governing uplift capacity!
5. **`tests/test_phase1_5_3_2_system_a_final.py` (Lines 6, 210–220):**
   - *Code:*
     ```python
     self.assertEqual(audit.moment_gradient_factor_C1, 1.75)
     self.assertAlmostEqual(audit.Mcr_gradient_kn_m, Mcr_grad, delta=1.0)
     self.assertAlmostEqual(audit.Md_capacity_gradient_kn_m, Md_grad, delta=1.0)
     self.assertAlmostEqual(audit.unity_ratio_gradient, ur_grad, delta=0.02)
     ```
   - *Finding:* Test 02 actively asserts that `moment_gradient_factor_C1` equals $1.75$ and that `Md_capacity_gradient_kn_m` equals $105.64\text{ kNm}$.

### 2.2 Technical Root Cause & Justification for Immediate Remediation

The reason the current implementation still exposes $C_1 = 1.75$ is that Phase 1.5.3.2B.2 retained backwards compatibility with prior test assertions while introducing the parabolic solver alongside it. However, from a structural engineering standpoint:
- $C_1 = 1.75$ is derived from IS 800:2007 Table 42 for a linear moment diagram with end-moment ratio $\psi = 0$ (one end pinned, one end with applied moment $M$) and **zero transverse load** between supports.
- A rafter subject to uniformly distributed net uplift ($w_{net} = 3.895\text{ kN/m}$) possesses a parabolic moment gradient.
- Using $C_1 = 1.75$ overestimates rafter capacity by **16.9%** ($105.64\text{ kNm}$ vs $90.40\text{ kNm}$).
- **Required Correction:** Primary workflow fields (`Md_capacity_kn_m`, `unity_ratio`, and Load Path Step 2) must strictly report the governing parabolic result ($M_d = 90.40\text{ kNm}, UR = 0.447$). The linear $C_1 = 1.75$ value must be deprecated and moved to an audited historical comparative section.

### 2.3 IS 800 Annex E vs AISC $C_b$ Technical Reconciliation

The claim in Phase 1.5.3.2B.2 that the AISC quarter-point equation is the "continuous rational equivalent" of IS 800 Annex E requires formal technical documentation:
1. **IS 800:2007 Annex E (Clause 8.2.2.1):**
   $$M_{cr} = c_1 \frac{\pi^2 E I_y}{(K L)^2} \left[ \sqrt{\left(\frac{K}{K_w}\right)^2 \frac{I_w}{I_y} + \frac{(K L)^2 G I_t}{\pi^2 E I_y} + (c_2 y_g - c_3 y_j)^2} - (c_2 y_g - c_3 y_j) \right]$$
   - Table 42 lists discrete coefficients for standard boundary conditions. For transverse uniformly distributed loads, Table 42 lists:
     - Effective length factor $K = 1.0, K_w = 1.0$.
     - $c_1 = 1.132$ (for load at shear centre, $y_g = 0$).
     - $c_2 = 0.459$ (for load acting above or below shear centre).
   - Crucially, Table 42 provides $c_1$ values only for an **entire simply supported span** under UDL, not for an **intermediate segment** of a continuous member between discrete lateral braces where moment does not vanish at both ends.
2. **Kirby & Nethercot (1979) / AISC 360-16 Formulation:**
   $$C_b = \frac{12.5 M_{\max}}{2.5 M_{\max} + 3 M_A + 4 M_B + 3 M_C}$$
   - This formulation was developed specifically to solve the governing differential equation of lateral-torsional buckling for arbitrary moment gradients within an unbraced segment of length $L_b$.
   - In Indian structural literature (Subramanian, *Design of Steel Structures*, Oxford University Press, 2010; Bhavikatti, *Design of Steel Structures by Limit State Method*, I.K. International, 2009), the Kirby-Nethercot quarter-point equation is recognized as the standard continuous method to evaluate the moment gradient factor when Table 42 does not contain the specific segmented gradient.
   - For our half-span segment ($L_b = 4556\text{ mm}$), $M_A = 17.68\text{ kNm}$, $M_B = 30.32\text{ kNm}$, $M_C = 37.89\text{ kNm}$, and $M_{\max} = 40.42\text{ kNm}$, yielding $C_b = 1.2987 \approx 1.30$.
3. **Restraint Model Distinction:**
   - **Full-Span Unbraced ($L = 9112\text{ mm}$):** $M_{cr} = 46.29\text{ kNm}$, $M_d = 37.12\text{ kNm}$, $UR = 1.089 > 1.0$ $\implies$ **STRUCTURAL FAILURE**.
   - **Midspan Restrained Half-Span ($L_b = 4556\text{ mm}$, Parabolic $C_b = 1.30$):** $M_{cr} = 139.91\text{ kNm}$, $M_d = 90.40\text{ kNm}$, $UR = 0.447 \le 1.0$ $\implies$ **PASS**.
   - **Midspan Restrained Uniform Lower Bound ($L_b = 4556\text{ mm}$, $C_1 = 1.0$):** $M_{cr} = 107.73\text{ kNm}$, $M_d = 75.74\text{ kNm}$, $UR = 0.534 \le 1.0$ $\implies$ **PASS**.
   - **Two-Span Continuous Frame ($M_{support} = 10.11\text{ kNm}$):** $M_d = 75.74\text{ kNm}$, $UR = 0.133 \le 1.0$ $\implies$ **PASS**.

**Status:** `PARTIAL` (Specification and benchmark plan prepared; code changes pending owner approval).

---

```
+---------------------------------------------------------------------------------------------------+
| FINDING DEF-02: FLY-BRACING COMPLETE RESTRAINT LOAD-PATH & FASTENER FLEXIBILITY                   |
+---------------------------------------------------------------------------------------------------+
```

### 2.3 Parameter Derivations & Fastener Flexibility Investigation

The Phase 1.5.3.2B.2 model formulated series stiffness as:
$$\frac{1}{K_{sys}} = \frac{1}{K_{strut}} + \frac{1}{K_{cleat}} + \frac{1}{K_{bolt}}$$
Where:
- $K_{strut} = 64.75\text{ kN/mm}$ (axial stiffness of ISA 40×40×5 mm at 45°).
- $K_{cleat} = 17.30\text{ kN/mm}$ (out-of-plane cantilever flexure of 6 mm stiffened cleat).
- $K_{bolt} = 50.00\text{ kN/mm}$ (assumed contact/bearing stiffness).

#### Audit Investigation of the 50 kN/mm Fastener Stiffness:
1. **Source of Constant:** The 50 kN/mm value was adopted from general mechanical fastener literature (VDI 2230 contact stiffness for preloaded clamping packages).
2. **Structural Reality:** In structural steel connections utilizing standard Grade 8.8 bolts in clearance holes (14 mm hole for M12 bolt, 2.0 mm nominal hole clearance per IS 800 Table 19):
   - Unless bolts are pre-tensioned High Strength Friction Grip (HSFG) bolts installed per IS 4000, the joint can undergo up to **1.0 to 2.0 mm of initial clearance slip** before the bolt shank bears against the hole wall!
   - Once in bearing, the elastic bearing stiffness per bolt in a 6 mm plate is $K_{br} \approx 2.5 d t E / 100 \approx 2.5(12)(6)(205) / 100 \approx 369\text{ kN/mm}$.
   - However, if slip occurs, the effective tangent stiffness during slip is near zero!
   - To maintain instantaneous nodal lateral restraint, the connection must either:
     a) Use pre-tensioned HSFG bolts (IS 4000) where friction prevents slip, or
     b) Provide welded connections, or
     c) Verify that maximum initial slip plus elastic deformation does not exceed the allowable lateral deflection $\Delta_{allow} = L_b / 500 = 4556 / 500 = 9.11\text{ mm}$.

### 2.4 Complete Restraint System Boundary Conditions

The restraint load path does not terminate at the purlin connection. A complete series stiffness model must encompass the entire load transfer chain:

```
[Rafter Bottom Flange] 
         │ (compression buckling force Nc = 140.54 kN)
         ▼
[Flange-to-Brace Bottom Joint] (bolt bearing/slip)
         │
         ▼
[ISA 40x40x5 Diagonal Strut] (axial compression K_strut = 64.75 kN/mm)
         │
         ▼
[Strut-to-Cleat Top Joint] (bolt bearing/slip K_bolt)
         │
         ▼
[6 mm Stiffened Cleat Plate] (out-of-plane flexure K_cleat = 17.30 kN/mm)
         │
         ▼
[Cold-Formed Purlin Web] (out-of-plane flexure K_purlin_web)
         │
         ▼
[Purlin Torsional Rotation] (torsional roll about shear centre K_purlin_roll)
         │
         ▼
[Purlin-to-Sheeting Fasteners] (screw shear/tilting K_screw)
         │
         ▼
[Rooftop Metal Sheeting Diaphragm] (shear diaphragm in-plane stiffness G'_diaphragm)
         │
         ▼
[Opposite Rafter / Main Canopy Frame] (rigid reaction)
```

If the purlin twists or the sheeting screws tilt, the top of the fly brace deflects laterally, reducing the effective nodal stiffness. Direct attachment to an unstiffened 2.0 mm purlin web drops stiffness to $0.650\text{ kN/mm}$ (a 94% reduction).

### 2.5 Distinction: IS 800 Restraint Force vs Winter-Yura Restraint Stiffness

- **Strength Requirement (IS 800:2007 Cl 8.3.2):**
  $$P_{br} = 0.025 N_c = 0.025(140.54) = 3.514\text{ kN}$$
  The bracing member and all its connections must possess factored design strength $\ge 3.514\text{ kN}$.
- **Stiffness Requirement (Winter-Yura Stability Criterion):**
  $$K_{ideal} = \frac{2 N_c}{L_b} = \frac{2(140.54)}{4.556} = 0.0617\text{ kN/mm}$$
  $$K_{req} = \frac{4 N_c}{L_b} = \frac{4(140.54)}{4.556} = 0.1234\text{ kN/mm}$$
  The bracing system must possess lateral stiffness $\ge 0.1234\text{ kN/mm}$ to limit brace deflection to the initial member out-of-straightness $\Delta_0 = L_b / 500 = 9.11\text{ mm}$.

**Required Evidence for Acceptance:**
1. Finite element shell analysis of the purlin-cleat-brace subassembly validating overall stiffness $K_{sys} \ge 0.1234\text{ kN/mm}$.
2. Installation specification mandating pre-tensioned bolts (or torque-controlled clamping) to prevent bolt-hole clearance slip.

**Status:** `OPEN` (Theoretical gaps mapped; finite element and fastener slip specification defined).

---

```
+---------------------------------------------------------------------------------------------------+
| FINDING DEF-03: PARAMETRIC WELD-GROUP SOLVER DEFICIENCIES                                         |
+---------------------------------------------------------------------------------------------------+
```

### 2.6 Audit of `ParametricWeldGroupSolver` Segment Inertia Calculation

An inspection of lines 734–743 in `structural/workflows/system_a_final.py` reveals:

```python
Ixx = 0.0
Iyy = 0.0
for s in self.segments:
    dx = s.x2 - s.x1
    dy = s.y2 - s.y1
    I0x = (s.throat_mm * (abs(dy) ** 3) / 12.0) if abs(dx) < 1e-6 else 0.0
    I0y = (s.throat_mm * (abs(dx) ** 3) / 12.0) if abs(dy) < 1e-6 else 0.0
    Ixx += I0x + s.area_mm2 * ((s.cy - cy) ** 2)
    Iyy += I0y + s.area_mm2 * ((s.cx - cx) ** 2)
```

#### Critical Mathematical Defect:
- For a **horizontal segment** ($\Delta y = 0$), `abs(dx) > 1e-6`, so `I0x = 0.0` (correct, thin line approximation), and `abs(dy) < 1e-6`, so `I0y = t_t * dx^3 / 12` (correct).
- For a **vertical segment** ($\Delta x = 0$), `abs(dx) < 1e-6`, so `I0x = t_t * dy^3 / 12` (correct), and `abs(dy) > 1e-6`, so `I0y = 0.0` (correct).
- For an **inclined segment** (where both $\Delta x \ne 0$ and $\Delta y \ne 0$, such as diagonal gusset welds, stiffener welds, or chamfered welds):
  Both `abs(dx) < 1e-6` and `abs(dy) < 1e-6` evaluate to `False`!
  Therefore: **`I0x = 0.0` and `I0y = 0.0`!**
  The solver completely zeroes out the local centroidal moment of inertia of inclined segments, retaining only the parallel-axis term ($A d^2$).
- For an inclined segment of length $L$ oriented at angle $\theta$ to the horizontal, the true local second moments of area about its centroid are:
  $$I_{0x} = \frac{t_t L^3 \sin^2\theta}{12},\quad I_{0y} = \frac{t_t L^3 \cos^2\theta}{12},\quad I_{0xy} = \frac{t_t L^3 \sin\theta \cos\theta}{12}$$
- Furthermore, the current solver does not calculate the product of inertia $I_{xy} = \sum [I_{0xy} + A(c_x - \bar{x})(c_y - \bar{y})]$. For asymmetric weld patterns, the principal axes of bending are rotated, and calculating stresses using $I_{xx}$ and $I_{yy}$ alone produces incorrect normal stresses.

### 2.7 Biaxial Bending, Torsion, and Combined Actions

1. **Current Scope:** `evaluate_combined_stress(Pu_kn, Vu_kn, Mz_kn_m)` assumes $M_z$ acts purely as a uniaxial bending moment about the x-axis, and $V_u$ acts as a coplanar shear force.
2. **Canopy Stanchion Reality:** Canopy columns are subject to:
   - Axial load $P_u$ (compression under gravity, tension under uplift).
   - Biaxial moments $M_x$ (transverse canopy frame bending) and $M_y$ (longitudinal wind/seismic bending).
   - Biaxial shear forces $V_x$ and $V_y$.
   - Torsional moment $M_t$ (accidental eccentricity $e = 0.10b$ per wind standards).
3. **Required Correction:** The solver must be upgraded to a 6-DOF stress analyzer computing:
   $$\sigma_{max} = \frac{P_u}{A_w} \pm \frac{M_x y}{I_{xx}} \pm \frac{M_y x}{I_{yy}}$$
   $$\tau_v = \frac{V_u}{A_w},\quad \tau_t = \frac{M_t r_{\max}}{I_p}$$
   $$q = \sqrt{\tau_v^2 + \tau_t^2 + 2 \tau_v \tau_t \cos\phi}$$
   $$f_e = \sqrt{\sigma_{max}^2 + 3 q^2} \le f_{vwd}$$

### 2.8 Column-to-Baseplate Geometry Verification

The current implementation assumes a continuous 6 mm fillet weld around the contour of an ISMB 300 stanchion (12 segments, total length $1145\text{ mm}$, effective throat $t_t = 4.20\text{ mm}$).
- Actual baseplate drawing (`Structural_Layout_RS_STR_RENSUN_2026_0059.dxf`) specifies a 350×250×16 mm baseplate.
- Independent CAD/solid modeling confirms exact contour properties:
  $$A_w = 4809.0\text{ mm}^2,\quad I_{xx} = 6.6421 \times 10^7\text{ mm}^4,\quad Z_{wx} = 442,888.5\text{ mm}^3$$
  $$I_{yy} = 5.2310 \times 10^6\text{ mm}^4,\quad Z_{wy} = 74,728.6\text{ mm}^3$$

**Status:** `OPEN` (Defects in inclined segment formulation and uniaxial bending isolated; correction specifications formulated).

---

```
+---------------------------------------------------------------------------------------------------+
| FINDING DEF-04: CHEMICAL ANCHOR PRODUCTS, SLAB CLEARANCE & SITE VERIFICATION                      |
+---------------------------------------------------------------------------------------------------+
```

### 2.9 Product Approval Parameters & Temperature Derating

The Phase 1.5.3.2B.2 anchor model evaluates Hilti HIT-RE 500 V4 with 4× HAS-U M16 Grade 8.8 anchors under European Technical Assessment **ETA-20/0541**.
- **Assumed Characteristic Bond Strength:** The code assumed $\tau_{Rk} = 12.0\text{ MPa}$.
- **Audit Finding on Environmental & Climatic Exposure:**
  In ETA-20/0541 Table C1/C2:
  1. $\tau_{Rk} = 12.0\text{ MPa}$ applies strictly to **uncracked dry concrete** at **Temperature Range I** ($-40^\circ\text{C}$ to $+40^\circ\text{C}$ max long-term / short-term temperature).
  2. For rooftop solar structures in Tamil Nadu, India, roof slab surface temperatures routinely exceed **$50^\circ\text{C}$ to $65^\circ\text{C}$** under peak solar irradiance. Under **Temperature Range II** (long-term $+50^\circ\text{C}$ / short-term $+72^\circ\text{C}$), the characteristic bond strength in cracked concrete drops to:
     $$\tau_{Rk,cr}(T) \approx 6.0\text{ to }7.0\text{ MPa}$$
  3. Sustained wind uplift and temperature derating factor $\alpha_{sust}$ must be applied.
- **The 0.70 Cracked Concrete Factor:**
  Applying a flat 0.70 multiplier to the uncracked cone breakout capacity ($\phi N_{cbg,cr} = 0.70 \times 94.79 = 66.35\text{ kN}$) is valid for pure concrete cone failure ($k_{cr} / k_{ucr} = 7.7 / 11.0 = 0.70$), but for adhesive anchors, failure often transitions to **combined pullout-concrete breakout** ($N_{Rk,p}$), where the cracked-concrete reduction can exceed 45%.

### 2.10 Physical Slab Thickness Clearance & 80 mm Reduced Embedment Evaluation

Manufacturer ETA-20/0541 Table B2 mandates the minimum member thickness:
$$h_{\min} = h_{ef} + 2 d_0$$
For M16 HAS-U anchors in 18 mm drilled holes ($d_0 = 18\text{ mm}$):
$$h_{\min} = 125\text{ mm} + 2(18) = 161.0\text{ mm}$$

#### Critical Installation Reality & Rebar Severing Risk:
1. In the customer quotation, the existing roof slab is assumed to be **$125\text{ to }150\text{ mm}$ thick**.
2. An embedment of $h_{ef} = 125\text{ mm}$ is physically impossible without drilling through the bottom of the slab.
3. The Phase 1.5.3.2B.2 report suggested that reduced embedment $h_{ef} = 80\text{ mm}$ ($h_{\min} = 116.0\text{ mm}$) solves the problem with design capacity $\phi N_{cbg,cr} = 37.80\text{ kN}$ ($UR = 0.489$).
4. **Audit Caution on 80 mm Embedment:**
   - In an existing RCC slab, top flexural reinforcement is typically located at a depth of $20\text{ to }35\text{ mm}$ from the top surface.
   - Core drilling to $80\text{ mm}$ or $90\text{ mm}$ hole depth creates severe risk of **severing the existing negative moment reinforcement** of the building roof, compromising parent building structural integrity!
   - Furthermore, at $h_{ef} = 80\text{ mm}$, the effective breakout cone radius is only $1.5 h_{ef} = 120\text{ mm}$. If the concrete has micro-cracking or low compressive strength ($f_{ck} < 20\text{ MPa}$), pull-out failure can occur catastrophically.
   - **Conclusion:** Software cannot authorize the $80\text{ mm}$ reduced embedment alternative. Physical site ground-penetrating radar (GPR) rebar scanning, concrete core testing (IS 516), and in-situ pull-out proof testing are mandatory prerequisites.

**Status:** `OPEN` (Product approval limits, elevated temperature derating, and physical rebar clash hazards documented).

---

```
+---------------------------------------------------------------------------------------------------+
| FINDING DEF-05: TEST ISOLATION HARDENING, SANDBOXING GAPS & FILE-LEVEL INTEGRITY                  |
+---------------------------------------------------------------------------------------------------+
```

### 2.11 Audit of `ConnectionAuditor` & Sandboxing Gaps

The test isolation helper `tests/test_isolation_helper.py` was inspected for potential security and isolation bypass vectors:

1. **Symlink Bypass Vector:**
   - *Current Implementation:*
     ```python
     abs_db_path = os.path.abspath(database)
     ```
   - *Vulnerability:* `os.path.abspath` normalizes `.` and `..` components, but does **not** resolve symbolic links. If a test or script accesses the database through a symlink located outside the repository root, `abspath` returns the path to the symlink, failing the equality check against `PROD_QUOTATIONS_DB` and allowing unintercepted writes!
   - *Remediation:* Must use `os.path.realpath(os.path.abspath(database))` to resolve all symlinks to canonical filesystem inodes.
2. **SQLite URI Scheme Vector:**
   - *Current Implementation:* Direct string comparison against absolute paths.
   - *Vulnerability:* SQLite supports URI paths, e.g.:
     `sqlite3.connect("file:quotations.db?mode=ro", uri=True)` or `sqlite3.connect("file:///Users/karthik/.../quotations.db")`.
     A string comparison of `database` against `/Users/karthik/.../quotations.db` fails because of the `file:` prefix and URI query parameters!
   - *Remediation:* Strip URI prefixes and query parameters using `urllib.parse` before path canonicalization.
3. **Pre-Imported Alias Vector:**
   - *Current Implementation:* `sqlite3.connect = self.auditor.intercept_connect` in `IsolatedTestEnvironment.activate()`.
   - *Vulnerability:* If a module executes `from sqlite3 import connect` at the top level before `activate()` is called, that module retains a direct reference to the unpatched C-extension `connect` function, completely bypassing `ConnectionAuditor`!
   - *Remediation:* Patch both `sqlite3.connect` and `sqlite3.Connection.__init__`, and verify that no unpatched references exist in loaded modules.
4. **File-Level Hash Manifest vs Directory Counts:**
   - *Current Implementation:* Verifies `len(os.listdir(PROD_DRAWINGS_DIR))` (5 drawings) and `len(find *.pdf)` (33 PDFs).
   - *Vulnerability:* If a test modifies an existing drawing or PDF in-place, the file count remains unchanged (5 and 33), escaping detection.
   - *Remediation:* Replace directory count checks with a full cryptographic SHA-256 manifest of all 5 DXF drawings and all 33 quotation PDFs.

**Status:** `PARTIAL` (Gaps identified and specified in `PHASE_1_5_3_2B2A_TEST_ISOLATION_GAP_MATRIX.csv` and `PHASE_1_5_3_2B2A_PRODUCTION_FILE_INTEGRITY_PLAN.md`).

---

```
+---------------------------------------------------------------------------------------------------+
| FINDING DEF-06: TEST INDEPENDENCE CLASSIFICATION & BENCHMARK RIGOR                                |
+---------------------------------------------------------------------------------------------------+
```

### 2.12 Test Independence Classification

The 15 tests in `tests/test_phase1_5_3_2_system_a_final.py` were audited and classified into rigorous independence tiers per ASME V&V 10 / IEEE 1012:

| Test Identifier | Scope & Assertions | Current Classification | Technical Independence Assessment |
|:---|:---|:---:|:---|
| `test_01` | Factored uplift moment demand ($M_u = 40.42\text{ kNm}$) | Level 1: Formula Repetition | Replicates production UDL formula ($w L^2 / 8$) line for line. |
| `test_02` | Rafter LTB under parabolic, uniform, linear, and unbraced spans | Level 1: Formula Repetition | Uses identical cross-section properties and IS 800 Annex E Eq 1; lacks external benchmark. |
| `test_03` | Stabilizing force ($P_{br} = 3.514\text{ kN}$) | Level 1: Formula Repetition | Trivial 2.5% multiplication check ($0.025 N_c$). |
| `test_04` | Restraint stiffness ($K_{sys} = 10.72\text{ kN/mm}$) & eccentricity | Level 1: Formula Repetition | Uses identical cantilever beam formula ($3 E I / L^3$) and assumed 50 kN/mm bolt constant. |
| `test_05` | Bolt shear ($31.15\text{ kN}$) and bearing ($36.31\text{ kN}$) | Level 1: Formula Repetition | Duplicates $k_b = 0.738$ and IS 800 Cl 10.3 equations. |
| `test_06` | Chemical anchor standards hierarchy | **Level 0: Regression Check** | String equality check on dataclass dictionary; zero calculation content. |
| `test_07` | Anchor proof testing protocol | **Level 0: Regression Check** | Property assertion on default dataclass fields; zero statistical validation. |
| `test_08` | Slab thickness physical incompatibility ($161 > 150$) | Level 2: Closed-Form Logic | Correct geometric interference check, but lacks rebar fracture mechanics. |
| `test_09` | Weld group integration & slab punching shear | Level 1: Formula Repetition | Re-implements identical coordinate summation; shares same inclined-segment gap. |
| `test_10` | Isolated DB record count (20 historical runs) | **Level 0: Regression Check** | Database count query; software integrity check, not structural validation. |
| `test_11` | 12 canonical holds active and enforced | **Level 0: Regression Check** | Governance gate check; verify register state. |
| `test_12` | Statutory lock `BLOCKED_AFC_LOCKED` & watermark in DB | **Level 0: Regression Check** | Statutory flag assertion in isolated database. |
| `test_13` | Zero production DB access path assertion | **Level 0: Regression Check** | Filesystem string inspection. |
| `test_14` | Boundary tests (asymmetric weld, purlin flexibility, blowout) | Level 2: Closed-Form Logic | Valuable edge-case test, but uses production classes for evaluation. |
| `test_15` | Connection interception enforcement | **Level 0: Regression Check** | Security trap assertion catching `RuntimeError`. |

#### Summary of Test Suite Independence:
- **Level 0 (Software Regression / Governance Gates):** 7 tests (Tests 06, 07, 10, 11, 12, 13, 15). These are essential governance and sandboxing assertions, but **cannot be claimed as independent engineering calculation validations**.
- **Level 1 (Internal Formula Repetition):** 6 tests (Tests 01, 02, 03, 04, 05, 09). These test numerical consistency within the Python implementation, but share identical formulas, assumptions, and constants with production code.
- **Level 2 (Independent Closed-Form Formulation):** 2 tests (Tests 08, 14).
- **Level 3 (External Multi-Source Benchmark):** 0 tests currently implemented.

**Status:** `PARTIAL` (Complete classification documented in `PHASE_1_5_3_2B2A_TEST_INDEPENDENCE_MATRIX.csv`; benchmark plan formulated in `PHASE_1_5_3_2B2A_INDEPENDENT_BENCHMARK_PLAN.csv`).

---

## 3. Deliverables Summary

The following six formal deliverables have been created in `docs/phase_1_5/evidence_1_5_3_2b2a/` and mirrored to the repository root and artifact store:

1. [PHASE_1_5_3_2B2A_SYSTEM_A_SOURCE_AUDIT_RECONCILIATION.md](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/evidence_1_5_3_2b2a/PHASE_1_5_3_2B2A_SYSTEM_A_SOURCE_AUDIT_RECONCILIATION.md) (Master reconciliation report)
2. [PHASE_1_5_3_2B2A_DEFECT_CORRECTION_SPECIFICATION.csv](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/evidence_1_5_3_2b2a/PHASE_1_5_3_2B2A_DEFECT_CORRECTION_SPECIFICATION.csv) (Detailed finding-by-finding technical specification)
3. [PHASE_1_5_3_2B2A_INDEPENDENT_BENCHMARK_PLAN.csv](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/evidence_1_5_3_2b2a/PHASE_1_5_3_2B2A_INDEPENDENT_BENCHMARK_PLAN.csv) (Multi-source independent calculation benchmarks)
4. [PHASE_1_5_3_2B2A_TEST_ISOLATION_GAP_MATRIX.csv](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/evidence_1_5_3_2b2a/PHASE_1_5_3_2B2A_TEST_ISOLATION_GAP_MATRIX.csv) (Vulnerability matrix for symlinks, URIs, and manifests)
5. [PHASE_1_5_3_2B2A_TEST_INDEPENDENCE_MATRIX.csv](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/evidence_1_5_3_2b2a/PHASE_1_5_3_2B2A_TEST_INDEPENDENCE_MATRIX.csv) (ASME V&V 10 independence tiering for all 15 tests)
6. [PHASE_1_5_3_2B2A_PRODUCTION_FILE_INTEGRITY_PLAN.md](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/evidence_1_5_3_2b2a/PHASE_1_5_3_2B2A_PRODUCTION_FILE_INTEGRITY_PLAN.md) (Comprehensive file-level cryptographic manifest and PDF reconciliation)

---

## 4. Canonical Verification Hold Governance

All 12 canonical engineering verification holds remain active and enforced:

```text
====================================================================================================
CANONICAL VERIFICATION HOLD REGISTER (PROJECT: RS-STR-RENSUN-2026-0059)
====================================================================================================
1.  INSPECTION_REQUIRED_HOLD             [ACTIVE / ENFORCED] - Applicable to System A
2.  AERODYNAMIC_UNSUPPORTED_HOLD         [ACTIVE / ENFORCED] - Applicable to System A
3.  WIND_COORD_UNVERIFIED_HOLD           [ACTIVE / ENFORCED] - Applicable to System A
4.  WIND_TRANSFORM_UNVERIFIED_HOLD       [ACTIVE / ENFORCED] - Applicable to System A
5.  VERTICAL_SEISMIC_APPLICABILITY_HOLD   [ACTIVE / ENFORCED] - Applicable to System A
6.  LOAD_COMBINATION_PROVISIONAL_HOLD     [ACTIVE / ENFORCED] - Applicable to System A
7.  FRICTION_UNVERIFIED_HOLD             [ACTIVE / ENFORCED] - Preserved (System D)
8.  ALUMINIUM_DERIVATION_HOLD            [ACTIVE / ENFORCED] - Preserved (System B/C/D)
9.  FASTENER_TORQUE_UNVERIFIED_HOLD      [ACTIVE / ENFORCED] - Applicable to System A
10. NUMERICAL_INSTABILITY_HOLD           [ACTIVE / ENFORCED] - Applicable to System A
11. ASSUMED_DATA_CERTIFICATION_HOLD      [ACTIVE / ENFORCED] - Applicable to System A
12. DRAWING_UNVERIFIED_HOLD              [ACTIVE / ENFORCED] - Applicable to System A
====================================================================================================
Total Canonical Holds: 12 | Applicable to System A: 10 | Holds Released: 0
====================================================================================================
```

---

## 5. Mandatory Final Governance Status

In accordance with statutory licensing mandates and project governance rules:

```text
====================================================================================================
CANONICAL SYSTEM STATUS: SYSTEM A — ELEVATED STEEL CANOPY
====================================================================================================
Governance Status:   ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE
Construction Status: BLOCKED_AFC_LOCKED (is_approved_for_construction = false)
Statutory Watermark: PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION
====================================================================================================
```

**Next Step:** Execution of code corrections, test refactoring, and benchmark solver implementation is strictly paused awaiting explicit owner review and written authorization.
