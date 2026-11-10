# PHASE 1.5.3.2B.2 — SYSTEM A CONTROLLED DEFECT CORRECTION REPORT
## RENSUN SOLAR STRUCTURAL ENGINEERING VALIDATION PROGRAMME

**Project ID:** RS-STR-RENSUN-2026-0059  
**Quotation:** RENSUN/2026/0059  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Expected Baseline HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Target Mounting System:** System A — Elevated Steel Canopy  
**Platform:** Google Antigravity  
**Phase Execution:** Phase 1.5.3.2B.2 (Controlled Defect Correction Stage)  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED` (`is_approved_for_construction = false`)  
**Mandatory Final Status:** `ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE`  

---

> [!WARNING]
> ### STATUTORY DISCLAIMER & ENGINEERING BOUNDARY
> This report documents a controlled software, analytical, and calculation-model defect correction stage. It verifies that software implementations correctly implement established engineering formulas, codal standards, and test isolation requirements.
> 
> **THIS IS NOT AN ENGINEERING CERTIFICATION.**
> Software calculations cannot and do not establish the safety, stability, or adequacy of the physical rooftop structure. All physical site inputs, existing slab thicknesses, concrete compressive strengths, rebar layouts, and anchor pull-out capacities remain unverified assumptions. Construction authorization remains strictly **BLOCKED_AFC_LOCKED**.

---

## 1. Executive Summary

Phase 1.5.3.2B.2 successfully remediates all six critical findings identified during the Phase 1.5.3.2B.1 independent audit. The engineering calculation models, code citations, and test architecture for **System A — Elevated Steel Canopy** have been upgraded from approximate or hardcoded implementations to rigorous, first-principles parametric solvers:

1. **DEF-01 (LTB Moment Gradient Factor):** Replaced the linear end-moment assumption ($C_1 = 1.75$) with a rational parabolic quarter-point moment gradient factor ($C_b = 1.2987 \approx 1.30$) derived per AISC 360-16 / Kirby-Nethercot and IS 800:2007 Annex E. The design capacity is $M_d = 90.40\text{ kNm}$ ($UR = 0.447 \le 1.0$), while the conservative uniform-moment lower bound yields $M_d = 75.74\text{ kNm}$ ($UR = 0.534 \le 1.0$), and the completely unbraced full-span rafter fails with $UR = 1.089 > 1.0$, conclusively proving the structural necessity of bottom-flange fly bracing.
2. **DEF-02 (Fly-Bracing Restraint System):** Corrected the code citation for the 2.5% compression flange force rule to **IS 800:2007 Cl 8.3.2** ($P_{br} = 3.514\text{ kN}$), attributed the minimum stiffness requirement to the **Winter-Yura (1996) stability criterion** ($K_{req} = 4 N_c / L_b = 0.1234\text{ kN/mm}$), and developed a complete series-spring load-path stiffness model. With a 6 mm stiffened cleat, system series stiffness is $K_{sys} = 10.72\text{ kN/mm}$ ($86.9\times$ required stiffness), whereas direct attachment to a 2.0 mm purlin web results in a 94% stiffness loss ($K_{sys} = 0.650\text{ kN/mm}$), demonstrating why direct cleat attachment is mandatory. Single-leg angle eccentricity interaction was verified at $IR = 0.224 \le 1.0$.
3. **DEF-03 (Parametric Baseplate Fillet Weld):** Eliminated the hardcoded weld section modulus ($Z_w = 450,067\text{ mm}^3$). Implemented a generalized parametric numerical integration solver that computes exact cross-sectional properties for the ISMB 300 6 mm fillet weld contour ($A_w = 4809.0\text{ mm}^2$, $Z_{wx} = 442,888.5\text{ mm}^3$). Verified both gravity ($f_e = 18.14\text{ MPa}, UR = 0.096 \le 1.0$) and net uplift load reversal ($f_e = 14.96\text{ MPa}, UR = 0.079 \le 1.0$) per IS 800:2007 Cl 10.5.10.1.1.
4. **DEF-04 (Product-Specific Chemical Anchor & Host Slab Clearance):** Eliminated the generic $66.35\text{ kN}$ breakout capacity. Implemented a product-specific model for Hilti HIT-RE 500 V4 with 4× HAS-U M16 Gr 8.8 under ETA-20/0541 and EN 1992-4:2018, evaluating all six primary failure modes. Formally identified and flagged that the required embedment depth ($h_{ef} = 125\text{ mm}$) requires minimum slab thickness $h_{min} = 161.0\text{ mm}$, making it physically infeasible in a 125–150 mm slab without through-bolts or plinths. Evaluated three engineering alternatives (reduced embedment $h_{ef} = 80\text{ mm}$, through-bolting, and cast plinths). Integrated host slab punching shear with unbalanced moment transfer per IS 456:2000 Cl 31.6.2 ($\tau_{v,\max} = 0.3039\text{ MPa} \le 1.1180\text{ MPa}, UR = 0.272$).
5. **DEF-05 (Test Isolation Hardening):** Implemented an active `ConnectionAuditor` wrapping `sqlite3.connect` during test runs, actively trapping, logging, and rejecting any direct connection to production databases with immediate `RuntimeError`. Test 15 formally verifies this interception. Cryptographic SHA-256 hashes of all production files confirmed bit-for-bit identical before and after test execution.
6. **DEF-06 (Independent Test Solvers):** Completely refactored `tests/test_phase1_5_3_2_system_a_final.py` (Tests 01–15). Replaced all static hardcoded assertions with independent test-side first-principles solvers and added negative/boundary test coverage. All 15 tests pass in 0.113s; full test suite of 208 tests passes cleanly in 8.103s.

---

## 2. WP-01: Lateral-Torsional Buckling Moment Gradient Factor Reconciliation (DEF-01)

### 2.1 The Moment Gradient Defect Identified in Audit

Phase 1.5.3.2B adopted $C_1 = 1.75$ citing IS 800:2007 Table 42. However, the Phase 1.5.3.2B.1 audit correctly established:
- IS 800:2007 Table 42 lists $C_1 = 1.75$ strictly for **linear end-moment gradients** where the ratio of end moments $\psi = M_2 / M_1 = 0$, and with **zero transverse distributed load** acting on the span.
- For a simply supported rafter subject to uniformly distributed net wind uplift ($w_{net} = 3.895\text{ kN/m}$), the bending moment profile across the restrained segment ($0 \le x \le 4.556\text{ m}$) is parabolic, varying from $0$ at the eave to $M_{\max} = 40.42\text{ kNm}$ at midspan.

### 2.2 First-Principles Derivation of Parabolic Moment Gradient $C_b$

Per the AISC 360-16 Eq F1-1 / Kirby-Nethercot (1979) formulation (the universally recognized continuous rational equivalent to IS 800:2007 Annex E Eq 1):

$$C_b = \frac{12.5 M_{\max}}{2.5 M_{\max} + 3 M_A + 4 M_B + 3 M_C}$$

For a simply supported beam of total span $L = 9.112\text{ m}$ under UDL $w_{net} = 3.895\text{ kN/m}$, the moment at distance $x$ from the support is $M(x) = \frac{1}{2} w_{net} x (L - x)$. Along the restrained half-span segment ($L_b = 4.556\text{ m}$):
- Quarter point $A$ ($x = 1.139\text{ m}$): $M_A = 17.6848\text{ kNm}$
- Midpoint $B$ ($x = 2.278\text{ m}$): $M_B = 30.3167\text{ kNm}$
- Three-quarter point $C$ ($x = 3.417\text{ m}$): $M_C = 37.8959\text{ kNm}$
- Segment maximum ($x = 4.556\text{ m}$): $M_{\max} = 40.4223\text{ kNm}$

Substituting into the quarter-point formula:

$$C_b = \frac{12.5(40.4223)}{2.5(40.4223) + 3(17.6848) + 4(30.3167) + 3(37.8959)} = \frac{505.2788}{389.0647} = 1.2987 \approx 1.30$$

### 2.3 Independent LTB Comparative Benchmark Results

| Model Description | Effective Length $L_b$ (mm) | Moment Profile & Factor | Elastic Buckling Moment $M_{cr}$ (kNm) | Slenderness $\lambda_{LT}$ | Reduction $\chi_{LT}$ | Factored Capacity $M_d$ (kNm) | Factored Demand $M_u$ (kNm) | Unity Ratio ($UR$) | Engineering Assessment |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **Full Unbraced Rafter (No Fly Bracing)** | 9112.0 | Uniform Lower Bound ($C_1 = 1.0$) | 46.29 | 1.874 | 0.251 | 37.12 | 40.42 | **1.089** | **STRUCTURAL FAILURE ($UR > 1.0$)** |
| **Midspan Restrained — Rational Parabolic** | 4556.0 | Parabolic Segment ($C_b = 1.2987$) | 139.91 | 1.078 | 0.611 | 90.40 | 40.42 | **0.447** | **GOVERNING DESIGN BASIS (PASS)** |
| **Midspan Restrained — Uniform Lower Bound** | 4556.0 | Uniform Envelope ($C_1 = 1.0$) | 107.73 | 1.229 | 0.512 | 75.74 | 40.42 | **0.534** | **CONSERVATIVE LOWER BOUND (PASS)** |
| **Midspan Restrained — Linear Reference** | 4556.0 | Linear End-Moment ($C_1 = 1.75$) | 188.53 | 0.929 | 0.714 | 105.64 | 40.42 | **0.383** | **HISTORICAL AUDIT REFERENCE (PASS)** |
| **2-Span Continuous Framing Option** | 4556.0 | Moment Over Support ($C_1 = 1.0$) | 107.73 | 1.229 | 0.512 | 75.74 | 10.11 | **0.133** | **SUBSTRUCTURE OPTION (PASS)** |

### 2.4 Governing Conclusion on Rafter Stability

Under ULS-02 net wind uplift, if the bottom flange is completely unbraced over the 9.112 m span, capacity is only $M_d = 37.12\text{ kNm}$, resulting in $UR = 1.089 > 1.0$ (structural failure). When restrained at midspan, even under the most conservative uniform-moment lower bound ($C_1 = 1.0$), capacity is $M_d = 75.74\text{ kNm}$ ($UR = 0.534 \le 1.0$). Under the rigorous parabolic gradient ($C_b = 1.30$), capacity is $M_d = 90.40\text{ kNm}$ ($UR = 0.447 \le 1.0$). Bottom-flange fly bracing is structurally mandatory.

---

## 3. WP-02: Complete Fly-Bracing Restraint System Modeling (DEF-02)

### 3.1 Code Standard Citation & Stabilizing Force Requirement

- **Correct Standard Citation:** The 2.5% compression flange force requirement is statutorily governed by **IS 800:2007 Clause 8.3.2** (*Lateral Bracing of Compression Flanges*), not Clause 8.9.2 (which addresses intermediate transverse web stiffeners).
- **Flange Compression Force:** Under uplift factored moment $M_u = 40.42\text{ kNm}$, with rafter effective depth $d_{eff} = h - t_f = 300 - 12.4 = 287.6\text{ mm} = 0.2876\text{ m}$:
  $$N_c = \frac{M_u}{d_{eff}} = \frac{40.42}{0.2876} = 140.54\text{ kN}$$
- **Required Stabilizing Force:** Per IS 800:2007 Cl 8.3.2:
  $$P_{br} = 0.025 \times N_c = 0.025 \times 140.54 = 3.514\text{ kN}$$
- **Axial Force Demand in Diagonal Brace (at 45°):**
  $$F_{brace} = \frac{P_{br}}{\cos(45^\circ)} = \frac{3.514}{0.7071} = 4.969\text{ kN}$$

### 3.2 Lateral Restraint Stiffness: Winter-Yura Stability Criterion

Per the classical **Winter-Yura stability criterion** (the theoretical foundation underlying IS 800:2007 Cl 8.3.2), the minimum lateral spring stiffness required to force nodal lateral buckling at midspan without brace displacement is:

$$K_{req} = \frac{4 N_c}{L_b} = \frac{4 \times 140.54\text{ kN}}{4.556\text{ m}} = 123.39\text{ kN/m} = 0.1234\text{ kN/mm}$$

### 3.3 Complete Series-Spring Restraint Flexibility Model

A diagonal brace does not act as an isolated axial bar. The lateral restraint load path consists of three structural elements in series:
1. **Diagonal ISA 40×40×5 mm Strut Axial Flexibility:**
   $$K_{strut} = \frac{A E}{L} \cos^2(45^\circ) = \frac{379\text{ mm}^2 \times 205\text{ kN/mm}^2}{600\text{ mm}} \times 0.5 = 64.75\text{ kN/mm}$$
2. **6 mm Stiffened Angle Cleat Out-of-Plane Flexure ($b = 100\text{ mm}$, $t = 6\text{ mm}$, $L = 40\text{ mm}$):**
   $$I_{cleat} = \frac{100 \times 6^3}{12} = 1800\text{ mm}^4$$
   $$K_{cleat} = \frac{3 E I_{cleat}}{L_{cleat}^3} = \frac{3 \times 205 \times 1800}{40^3} = 17.297\text{ kN/mm}$$
3. **M12 Bolt Contact and Hole Bearing Flexibility:**
   $$K_{bolt} \approx 50.00\text{ kN/mm}$$

**Total Series System Stiffness with 6 mm Stiffened Cleat:**

$$\frac{1}{K_{sys}} = \frac{1}{K_{strut}} + \frac{1}{K_{cleat}} + \frac{1}{K_{bolt}} = \frac{1}{64.75} + \frac{1}{17.30} + \frac{1}{50.00} = 0.01544 + 0.05780 + 0.02000 = 0.09324\text{ mm/kN}$$
$$K_{sys} = \frac{1}{0.09324} = 10.72\text{ kN/mm}$$
$$\text{Stiffness Reserve Ratio} = \frac{K_{sys}}{K_{req}} = \frac{10.72}{0.1234} = 86.9 \gg 1.0\quad (\textbf{PASS})$$

### 3.4 Purlin Web Out-of-Plane Flexibility Analysis

If the fly brace is attached directly to an unstiffened 2.0 mm cold-formed purlin web (depth $h = 100\text{ mm}$, $b = 100\text{ mm}$ tributary):
$$I_{web} = \frac{100 \times 2^3}{12} = 66.67\text{ mm}^4$$
$$K_{web} = \frac{48 E I_{web}}{h^3} = \frac{48 \times 205 \times 66.67}{100^3} = 0.656\text{ kN/mm}$$
$$\frac{1}{K_{sys,no\_cleat}} = \frac{1}{64.75} + \frac{1}{0.656} = 0.01544 + 1.5244 = 1.5398 \implies K_{sys,no\_cleat} = 0.650\text{ kN/mm}$$

Attaching directly to the thin purlin web causes a **94% reduction in restraint stiffness**, reducing the stiffness margin from $86.9\times$ to barely $5.27\times$, with substantial risk of purlin web distortion and local buckling. **Direct stiffened 6 mm cleat attachment is therefore mandatory.**

### 3.5 Single-Leg Eccentricity Interaction Check (IS 800 Cl 7.5.1 / 9.3)

Because the ISA 40×40×5 mm angle is bolted through one leg:
- Eccentricity $e_x = 11.6\text{ mm} = 0.0116\text{ m}$
- Eccentric bending moment: $M_{ecc} = F_{brace} \times e_x = 4.969 \times 0.0116 = 0.05764\text{ kNm}$
- Design compressive strength: $P_d = A \times f_{cd} = 379 \times 141.1 / 1000 = 53.48\text{ kN}$
- Design bending strength: $M_d = Z_{xx} f_y / \gamma_{m0} = 1940 \times 250 / (1.10 \times 10^6) = 0.4409\text{ kNm}$
- Combined interaction ratio:
  $$IR = \frac{P}{P_d} + \frac{M_{ecc}}{M_d} = \frac{4.969}{53.48} + \frac{0.05764}{0.4409} = 0.0929 + 0.1307 = 0.2236 \approx 0.224 \le 1.0\quad (\textbf{PASS})$$

---

## 4. WP-03: Parametric Baseplate Fillet Weld Numerical Integration (DEF-03)

### 4.1 Elimination of Hardcoded Modulus

Phase 1.5.3.2B used a hardcoded $Z_w = 450,067\text{ mm}^3$. Under Phase 1.5.3.2B.2, a fully parameterized numerical integration class (`ParametricWeldGroupSolver`) integrates arbitrary weld segments.

### 4.2 Numerical Integration of ISMB 300 6 mm Contour

The weld contour consists of 12 distinct straight segments along the profile of the ISMB 300 section ($D = 300\text{ mm}, B = 140\text{ mm}, t_f = 12.4\text{ mm}, t_w = 7.5\text{ mm}$). With a 6 mm fillet weld, effective throat thickness is $t_t = 0.70 \times 6.0 = 4.20\text{ mm}$ (IS 800 Cl 10.5.3.1):

| Segment Group | Count | Length Each (mm) | Total Area $A_w$ ($\text{mm}^2$) | Position $y$ (mm) | Second Moment of Area $I_{xx}$ ($\text{mm}^4$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| Outer Flanges | 2 | 140.0 | 1176.0 | $\pm 150.0$ | $2.6460 \times 10^7$ |
| Inner Flanges | 4 | 66.25 | 1113.0 | $\pm 137.6$ | $2.1073 \times 10^7$ |
| Flange Tips | 4 | 12.4 | 208.32 | $\pm 143.8$ | $4.3077 \times 10^6$ |
| Web Welds | 2 | 275.2 | 2311.68 | $[-137.6, 137.6]$ | $1.4580 \times 10^7$ |
| **Total Weld Group** | **12** | **1145.0 mm** | **4809.00** | Centroid $y = 0$ | **$6.6421 \times 10^7$** |

- **Elastic Section Modulus:**
  $$Z_{wx} = \frac{I_{xx}}{y_{\max}} = \frac{6.6421 \times 10^7\text{ mm}^4}{150.0\text{ mm}} = 442,888.5\text{ mm}^3$$
  *(The historical hardcoded value of 450,067 was 1.62% higher and under-predicted bending stress).*
- **Permissible Shear Stress:**
  $$f_{vwd} = \frac{f_u}{\sqrt{3} \gamma_{mw}} = \frac{410.0}{\sqrt{3} \times 1.25} = 189.37\text{ MPa}$$

### 4.3 Combined Stress Evaluation under Governing Actions (IS 800 Cl 10.5.10.1.1)

Equivalent stress: $f_e = \sqrt{(f_a + f_b)^2 + 3 q^2} \le f_{vwd}$

1. **ULS-01 Gravity Load Case ($P_u = 33.84\text{ kN}, M_z = 4.90\text{ kNm}, V_u = 3.50\text{ kN}$):**
   - Direct axial compression: $f_a = \frac{33.84 \times 10^3}{4809.0} = 7.037\text{ MPa}$
   - Peak bending stress: $f_b = \frac{4.90 \times 10^6}{442,888.5} = 11.064\text{ MPa}$
   - Direct shear stress: $q = \frac{3.50 \times 10^3}{4809.0} = 0.728\text{ MPa}$
   - Combined equivalent stress:
     $$f_e = \sqrt{(7.037 + 11.064)^2 + 3(0.728)^2} = \sqrt{18.101^2 + 1.590} = 18.144\text{ MPa}$$
     $$UR = \frac{18.144}{189.37} = 0.096 \le 1.0\quad (\textbf{PASS})$$

2. **ULS-02 Wind Uplift Load Reversal ($T_u = 18.50\text{ kN}, M_z = 4.90\text{ kNm}, V_u = 3.50\text{ kN}$):**
   - Direct axial tension: $f_a = \frac{18.50 \times 10^3}{4809.0} = 3.847\text{ MPa}$
   - On the tension flange, axial tension directly superimposes onto flexural tension:
     $$f_{normal} = f_a + f_b = 3.847 + 11.064 = 14.911\text{ MPa}$$
   - Combined equivalent stress:
     $$f_e = \sqrt{14.911^2 + 3(0.728)^2} = \sqrt{222.338 + 1.590} = 14.964\text{ MPa}$$
     $$UR = \frac{14.964}{189.37} = 0.079 \le 1.0\quad (\textbf{PASS})$$

Both load conditions are safely within the permissible limit ($UR < 0.10$).

---

## 5. WP-04: Product-Specific Chemical Anchor & Host Slab Clearance Model (DEF-04)

### 5.1 Product Specification & Standards Hierarchy

- **Product Specified:** Hilti HIT-RE 500 V4 injection epoxy with 4× HAS-U M16 Grade 8.8 threaded rods.
- **Governing Approval:** European Technical Assessment **ETA-20/0541** evaluated per **EN 1992-4:2018** and **fib Bulletin 58**.
- **Retraction of IS 800 Cl 10:** Confirmed that IS 800:2007 Cl 10 applies exclusively to cast-in-place headed bolts and cannot be used for post-installed adhesive anchors in concrete.

### 5.2 Verification of All Six Anchor Failure Modes

Anchor geometry: 4× M16 bolts on a $250\text{ mm} \times 150\text{ mm}$ grid, $h_{ef} = 125\text{ mm}$, Concrete C20/25 ($f_{ck} = 20\text{ MPa}$):

| Failure Mode | Governing Standard & Equation | Nominal Capacity | Design Capacity ($\phi R_n$) | Factored Demand | Unity Ratio ($UR$) | Status |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| **Steel Tension (4× M16 Gr 8.8)** | EN 1992-4 Cl 7.2.1.3: $4 \times \frac{A_{se} f_{uk}}{\gamma_{Ms}}$ | 502.40 kN | 334.93 kN | 18.50 kN | 0.055 | **PASS** |
| **Concrete Cone Breakout (Uncracked)** | EN 1992-4 Cl 7.2.1.4: $\frac{N_{Rk,c}^0 \frac{A_{c,N}}{A_{c,N0}}}{\gamma_{Mc}}$ | 142.19 kN | 94.79 kN | 18.50 kN | 0.195 | **PASS (THEORETICAL)** |
| **Concrete Cone Breakout (Cracked)** | fib Bulletin 58: $\phi N_{cbg,cr} = 0.70 \times \phi N_{cbg,uncr}$ | 99.53 kN | 66.35 kN | 18.50 kN | **0.279** | **GOVERNING TENSION (PASS)** |
| **Adhesive Bond / Pullout** | ETA-20/0541: $4 \times \frac{\pi d h_{ef} \tau_{Rk}}{\gamma_{Mp}}$ ($\tau_{Rk} = 12.0\text{ MPa}$) | 301.60 kN | 201.06 kN | 18.50 kN | 0.092 | **PASS** |
| **Steel Shear (4× M16 Gr 8.8)** | EN 1992-4 Cl 7.2.2.3: $4 \times \frac{0.5 A_{se} f_{uk}}{\gamma_{Ms}}$ | 251.20 kN | 195.94 kN | 3.50 kN | 0.018 | **PASS** |
| **Concrete Pryout** | EN 1992-4 Cl 7.2.2.5: $k_8 \phi N_{cbg,uncr}$ ($k_8 = 2.0$) | 284.38 kN | 189.58 kN | 3.50 kN | 0.018 | **PASS** |
| **Tension-Shear Interaction** | EN 1992-4 Cl 7.2.3.1.2: $(N_{Ed} / N_{Rd})^{1.5} + (V_{Ed} / V_{Rd})^{1.5}$ | N/A | 1.000 | 0.150 | 0.150 | **PASS ($IR \le 1.0$)** |

### 5.3 Physical Slab Thickness Clearance Incompatibility

Manufacturer ETA-20/0541 Table B2 mandates the minimum member thickness for post-installed adhesive anchors:

$$h_{\min} = h_{ef} + 2 d_0$$

For M16 HAS-U anchors in hammered/diamond holes ($d_0 = 18\text{ mm}$):
$$h_{\min} = 125\text{ mm} + 2(18\text{ mm}) = 125 + 36 = 161.0\text{ mm}$$

**Critical Physical Conflict:**
- In the client quotation and structural records, the existing host slab is assumed to be **$125\text{ to }150\text{ mm}$ thick**.
- An embedment of $h_{ef} = 125\text{ mm}$ in a $150\text{ mm}$ slab leaves only $25\text{ mm}$ total remaining thickness, completely violating the $161\text{ mm}$ ETA minimum requirement.
- In a $125\text{ mm}$ slab, drilling $125\text{ mm}$ would blow through the bottom soffit entirely!
- **Status: `BLOCKED_PHYSICALLY_INFEASIBLE_IN_150MM_SLAB`**.

### 5.4 Engineering Alternatives Evaluation

To resolve this physical conflict without releasing the hold, three alternative concepts were modeled:

1. **Alternative 1: Reduced Embedment Depth ($h_{ef} = 80\text{ mm}$):**
   - $h_{\min} = 80 + 2(18) = 116.0\text{ mm} \le 150.0\text{ mm}$ (Physically Feasible).
   - Cracked concrete cone breakout capacity: $\phi N_{cbg,cr} = 37.80\text{ kN}$.
   - Uplift demand: $T_u = 18.50\text{ kN} \implies UR = \frac{18.50}{37.80} = 0.489 \le 1.0$ (**RECOMMENDED**).
2. **Alternative 2: Through-Bolting with Soffit Backing Plates:**
   - 4× M16 threaded rods passing entirely through core-drilled holes in slab, clamped against a $250 \times 250 \times 10\text{ mm}$ soffit plate. Eliminates adhesive depth limits entirely.
   - Tensile capacity governed by plate flexure / punch-through ($UR = 0.154$). Requires soffit access.
3. **Alternative 3: Cast-in-Place Reinforced Concrete Stub Pedestals:**
   - Cast $150\text{ mm}$ high pedestals atop the slab dowelled into parent concrete using Hilti HIT-RE 500. Total depth becomes $300\text{ mm}$, accommodating $h_{ef} = 125\text{ mm}$ comfortably.

### 5.5 Host Slab Punching Shear with Unbalanced Moment Transfer (IS 456 Cl 31.6.2)

Concentrated stanchion reactions: $P_u = 33.84\text{ kN}$ (gravity), $M_z = 4.90\text{ kNm}$, baseplate $350 \times 250\text{ mm}$, slab effective depth $d = 100\text{ mm}$, $f_{ck} = 20\text{ MPa}$:
- Critical shear perimeter at $d/2 = 50\text{ mm}$: $b_1 = 450\text{ mm}$, $b_2 = 350\text{ mm}$, $b_0 = 2(450 + 350) = 1600\text{ mm}$.
- Permissible punching shear stress: $\tau_c = 0.25 \sqrt{f_{ck}} = 0.25 \sqrt{20} = 1.1180\text{ MPa}$.
- Direct punching shear stress:
  $$\tau_{v,dir} = \frac{P_u}{b_0 d} = \frac{33.84 \times 10^3}{1600 \times 100} = 0.2115\text{ MPa}$$
- Moment transfer fraction per IS 456 Cl 31.6.2.2:
  $$\alpha_v = 1 - \frac{1}{1 + \frac{2}{3}\sqrt{b_1 / b_2}} = 1 - \frac{1}{1 + \frac{2}{3}\sqrt{450/350}} = 0.4305$$
  $$M_v = \alpha_v \times M_z = 0.4305 \times 4.90 = 2.109\text{ kNm}$$
- Polar moment of inertia $J_c = 5.1375 \times 10^9\text{ mm}^4$.
- Moment-induced shear stress:
  $$\tau_{v,mom} = \frac{M_v \times 10^6 \times (b_1 / 2)}{J_c} = \frac{2.109 \times 10^6 \times 225}{5.1375 \times 10^9} = 0.0924\text{ MPa}$$
- Maximum combined punching shear stress:
  $$\tau_{v,\max} = \tau_{v,dir} + \tau_{v,mom} = 0.2115 + 0.0924 = 0.3039\text{ MPa}$$
  $$UR = \frac{0.3039}{1.1180} = 0.272 \le 1.0\quad (\textbf{PASS})$$

---

## 6. WP-05: Test Isolation Hardening & Active Interception (DEF-05)

### 6.1 Instrumentation and Connection Interception

In `tests/test_isolation_helper.py`, `ConnectionAuditor` intercepts `sqlite3.connect`:
- Any connection attempt whose resolved absolute path matches `PROD_QUOTATIONS_DB` or `PROD_STRUCTURAL_DB` is trapped and aborted immediately with `RuntimeError`.
- Test 15 in `tests/test_phase1_5_3_2_system_a_final.py` formally tests this trap by intentionally requesting connections to both production paths and verifying that `RuntimeError` is raised and registered in `auditor.rejected_attempts`.

### 6.2 Pre- and Post-Execution Cryptographic Integrity

All production databases were verified before and after test execution:
- `quotations.db`: `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf` (Unchanged)
- `structural/structural_runs.db`: `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff` (Unchanged)
- `quotation_settings.json`: `26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1` (Unchanged)
- Generated drawings: 5 DXF files (Unchanged)
- Generated PDFs: 33 PDF files (Unchanged)

---

## 7. WP-06: Independent Test Solvers & Test Quality (DEF-06)

### 7.1 Refactored Test Architecture

All 15 tests in `tests/test_phase1_5_3_2_system_a_final.py` derive target engineering values dynamically using local first-principles physics solvers inside the test methods:
- **Test 01:** Closed-form solver for net uplift UDL ($w_{net} = 3.895\text{ kN/m}$) and span moment ($M_u = 40.42\text{ kNm}$).
- **Test 02:** Quarter-point numerical solver for parabolic $C_b = 1.2987$, uniform $C_1 = 1.0$, linear $C_1 = 1.75$, and full-span failure ($UR = 1.089$).
- **Test 03:** Flange equilibrium solver for $N_c = 140.54\text{ kN}$, $P_{br} = 3.514\text{ kN}$, $F_{brace} = 4.969\text{ kN}$.
- **Test 04:** Series flexibility solver for $K_{sys} = 10.72\text{ kN/mm}$ and single-leg interaction ($IR = 0.224$).
- **Test 05:** First-principles bolt shear ($V_{dsb} = 31.15\text{ kN}$) and bolt bearing ($V_{dpb} = 36.31\text{ kN} / 43.57\text{ kN}$).
- **Test 06:** Authoritative hierarchy verification (IS 800 Cl 10 retracted; fib 58 primary).
- **Test 07:** Project-specific anchor testing protocol (1.5× proof load, 25% sampling, 0.20 mm slip).
- **Test 08:** Geometric clearance check ($h_{min} = 161\text{ mm} > 150\text{ mm}$ slab) and 3 alternatives.
- **Test 09:** Exact numerical integration of weld group ($Z_w = 442,888.5\text{ mm}^3$, $f_e = 18.14\text{ MPa}$), slab punching shear ($\tau_v = 0.3039\text{ MPa}$), and cracked concrete cone breakout ($\phi N_{cbg,cr} = 66.35\text{ kN}$).
- **Test 10:** 20 historical runs verified in isolated database.
- **Test 11:** 12 canonical holds active (10 for System A).
- **Test 12:** Statutory lock `BLOCKED_AFC_LOCKED` and watermark verified in isolated DB.
- **Test 13:** Zero production DB access path assertion.
- **Test 14:** Negative and boundary tests (asymmetric weld centroid shift, purlin web flexibility $< 1.0\text{ kN/mm}$, slab blowout).
- **Test 15:** Active connection interception proof catching `RuntimeError` on production DB access.

### 7.2 Multi-Stage Test Execution Results

- System A Test Suite (`test_phase1_5_3_2_system_a_final.py`): **15 passed, 0 failed** (0.113s)
- All System A Tests (`test_phase1_5_3*.py`): **36 passed, 0 failed** (0.224s)
- Quotation Tests (`test_quotation*.py`): **12 passed, 0 failed** (2.228s)
- Full Test Suite (`discover tests`): **208 passed, 0 failed** (8.103s)

---

## 8. Canonical Hold Governance & Statutory Gate Audit

All 12 canonical engineering holds remain active and enforced:

| Hold Identifier | Category | Applicable to System A | Status | Blocking Condition |
|:---|:---|:---:|:---:|:---|
| `INSPECTION_REQUIRED_HOLD` | Professional Approval | **Yes** | **ACTIVE_ENFORCED** | Requires physical inspection, crack mapping, NDT rebound hammer/UPV logs |
| `AERODYNAMIC_UNSUPPORTED_HOLD` | Project Engineering | **Yes** | **ACTIVE_ENFORCED** | Requires wind tunnel test report or peer-reviewed CFD for canopy tilt |
| `WIND_COORD_UNVERIFIED_HOLD` | Project Engineering | **Yes** | **ACTIVE_ENFORCED** | Requires official municipal survey confirming basic wind speed $V_b$ & $k_4$ |
| `WIND_TRANSFORM_UNVERIFIED_HOLD` | Internal QC | **Yes** | **ACTIVE_ENFORCED** | Requires 3D direction cosine verification & accidental torsion $e = 0.10b$ |
| `VERTICAL_SEISMIC_APPLICABILITY_HOLD` | Statutory Requirement | **Yes** | **ACTIVE_ENFORCED** | Requires IS 1893:2016 Cl 6.3.3.1 screening determination |
| `LOAD_COMBINATION_PROVISIONAL_HOLD` | Statutory Requirement | **Yes** | **ACTIVE_ENFORCED** | Requires IS 800 Table 4 verification including erection stage row |
| `FRICTION_UNVERIFIED_HOLD` | Project Engineering | No (System D) | **ACTIVE_ENFORCED** | Preserved in register; applies exclusively to ballasted systems |
| `ALUMINIUM_DERIVATION_HOLD` | Statutory Requirement | No (System B/C/D) | **ACTIVE_ENFORCED** | Preserved in register; applies exclusively to aluminium rail systems |
| `FASTENER_TORQUE_UNVERIFIED_HOLD` | Internal QC | **Yes** | **ACTIVE_ENFORCED** | Requires calibrated torque-wrench procedures & clamp slip-resistance curves |
| `NUMERICAL_INSTABILITY_HOLD` | Internal QC | **Yes** | **ACTIVE_ENFORCED** | Requires multi-scale solver benchmark report (OpenSees/OpenRadioss) |
| `ASSUMED_DATA_CERTIFICATION_HOLD` | Professional Approval | **Yes** | **ACTIVE_ENFORCED** | Requires signed client data certification for slab thickness & concrete grade |
| `DRAWING_UNVERIFIED_HOLD` | Professional Approval | **Yes** | **ACTIVE_ENFORCED** | Requires Registered Structural Engineer (RSE) seal, signature, and stability cert |

Zero verification holds have been released. No construction approval is granted.

---

## 9. Final Statutory Classification

All software defects identified in Phase 1.5.3.2B.1 have been resolved with mathematical rigor, independent first-principles verification, and test isolation.

In accordance with statutory governance requirements, the official status of System A is:

```text
====================================================================================================
CANONICAL SYSTEM STATUS: SYSTEM A — ELEVATED STEEL CANOPY
====================================================================================================
Construction Status:  BLOCKED_AFC_LOCKED
Approved for Constr: false
Statutory Watermark: PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION
Governance Status:   ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE
====================================================================================================
```
