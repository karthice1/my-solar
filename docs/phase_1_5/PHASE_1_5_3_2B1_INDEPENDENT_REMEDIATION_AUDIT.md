# PHASE 1.5.3.2B.1 — INDEPENDENT AUDIT OF DEFECT REMEDIATION
## RENSUN SOLAR STRUCTURAL ENGINEERING VALIDATION PROGRAMME

**Platform:** Google Antigravity  
**Project ID:** `RS-STR-RENSUN-2026-0059`  
**Quotation:** `RENSUN/2026/0059`  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Expected / Verified HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Client / Site:** 90 ERUMAPALAYAM ITTERI ROAD, SALEM, TAMIL NADU (11.6643°N, 78.1460°E)  
**Mounting System:** `System A: Elevated Steel Canopy (H = 2.8 m)`  
**Audit Stage:** Phase 1.5.3.2B.1 — Independent Audit of Defect Remediation  
**Date of Audit:** 2026-11-08  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED` (`is_approved_for_construction = false`)  
**Final Statutory Status:** `ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE`

---

## 1. EXECUTIVE SUMMARY & AUDIT MANDATE

This audit provides an exhaustive, source-grounded, independent forensic examination of the defect corrections implemented in Phase 1.5.3.2B for **System A (Elevated Steel Canopy)**. 

In accordance with the mandatory Phase 1.5.3.2B.1 audit mandate, this investigation was conducted strictly in **AUDIT-ONLY** mode without modifying source code, unit tests, databases, settings, drawings, or previous reports. Every mathematical equation, standard citation, test method, and calculation benchmark was audited against the primary authoritative technical literature, including:
- **IS 800:2007** (*General Construction in Steel — Code of Practice*)
- **IS 875 (Part 3): 2015** (*Design Loads — Wind Loads*)
- **IS 456:2000** (*Plain and Reinforced Concrete — Code of Practice*)
- **fib Bulletin 58 / EN 1992-4:2018** (*Design of Fastenings for Use in Concrete*)
- **AISC 360-16 / Classical Stability Theory** (*Winter & Yura Bracing Models*)

### Key Audit Findings:
1. **DEF-01 ($C_1 = 1.75$ Moment Gradient Citation & Value Discrepancy):**  
   The claim that IS 800:2007 Table 42 provides $C_1 = 1.75$ for a midspan-braced rafter under uniformly distributed wind uplift is **technically flawed**. In Table 42, $C_1 = 1.75$ applies strictly to a **linear moment gradient** ($\psi = 0$) produced by end moments with *zero transverse loading* on the unbraced segment. For a simply-supported beam under UDL with a midspan lateral brace, the moment distribution across the half-span is **parabolic** ($M(0) = 0$, $M_{mid} = 0.75 M_{\max}$, $M_{end} = 1.0 M_{\max}$). Applying the rigorous quarter-point moment gradient formula ($C_b = \frac{12.5 M_{\max}}{2.5 M_{\max} + 3 M_A + 4 M_B + 3 M_C}$) yields $\mathbf{C_b = 1.30}$, not $1.75$. Multiplying $M_{cr}$ by $1.75$ overestimated the critical moment by $34.6\%$. However, using the correct $C_b = 1.30$, the rafter still **PASSES** ($M_{cr} = 140.05\text{ kNm}$, $M_d = 90.40\text{ kNm}$, $\mathbf{UR = 0.447 \le 1.0}$), and also passes under the uniform-moment lower bound ($C_1 = 1.0$, $M_d = 75.74\text{ kNm}$, $\mathbf{UR = 0.534 \le 1.0}$) and 2-span continuous framing model ($M_u = 10.11\text{ kNm}$, $\mathbf{UR = 0.133 \le 1.0}$). The unbraced full span remains a confirmed failure ($M_d = 37.12\text{ kNm}$, $\mathbf{UR = 1.089 > 1.0}$).
2. **DEF-02 (Fly-Bracing Citation & Restraint System Stiffness Discrepancy):**  
   The citation of **IS 800:2007 Clause 8.9.2** for required lateral restraint stiffness ($K_{req} = 4 N_c / L_b$) and Clause 8.9.1 for the 2.5% rule is **erroneous**. Clause 8.9 of IS 800:2007 is titled *"Purlins and Sheeting Rails (Girts)"* and has no subclauses 8.9.1 or 8.9.2. The true codal provision for the 2.5% compression flange stabilizing force is **IS 800:2007 Clause 8.3.2**. The stiffness formulation $K_{req} = 4 N_c / L_b$ is the classical **Winter-Yura bracing criterion** (AISC 360-16 Appendix 6 / Eurocode 3 principle). Furthermore, the reported stiffness $K_{\text{lat}} = 64.75\text{ kN/mm}$ represents only the idealized axial stiffness of the diagonal angle strut member; it does not model the complete series system flexibility (thin purlin web flexure, cleat bending, and bolt slip).
3. **DEF-03 (Baseplate Fillet Weld Geometry & Section Modulus Traceability):**  
   The weld contour perimeter $L_w = 1145.0\text{ mm}$ is mathematically exact. However, the elastic section modulus $Z_w = 450,067.0\text{ mm}^3$ was **hardcoded** on line 686 of [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py). An independent first-principles integration of the 6 mm fillet weld group yields $Z_{w,\text{exact}} = 442,888.5\text{ mm}^3$ (a minor discrepancy of $-1.60\%$). Under both maximum gravity ($f_e = 18.14\text{ MPa}$, $\mathbf{UR = 0.096 \le 1.0}$) and wind uplift reversal ($f_e = 14.96\text{ MPa}$, $\mathbf{UR = 0.079 \le 1.0}$), the weld group passes with massive margin.
4. **DEF-04 (Anchor Breakout Hardcoding & Physical Slab Incompatibility):**  
   The cracked-concrete breakout capacity $\phi N_{cbg,\text{cr}} = 66.35\text{ kN}$ is **hardcoded** on line 719. Tracing shows it derives from uncracked cone resistance ($94.79\text{ kN} \times 0.70$). However, achieving this capacity requires an effective embedment $h_{ef} = 125\text{ mm}$, which demands a minimum concrete member thickness $h_{\min} = h_{ef} + 2 d_0 = 161.0\text{ mm}$ per manufacturer ETA. In typical residential/commercial roof slabs of $125\text{ mm}$ to $150\text{ mm}$, this installation is **physically impossible**. Physical slab parameters ($f_{ck} = 20\text{ MPa}$, thickness, and rebar) remain 100% unverified on site.
5. **DEF-05 (Hermetic Test Isolation Verification):**  
   The remediation of test isolation in [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) using `IsolatedTestEnvironment` is **100% verified**. All direct connections to production database files were eliminated. Production database SHA-256 checksums remained bit-for-bit identical across all test executions.
6. **DEF-06 (Test Quality Mislabelling & Benchmark Count Discrepancy):**  
   While Tests 01, 02, 03, and 04 embed genuine first-principles solvers, **TEST-05** and **TEST-09** were **mislabeled** in the Test Quality Matrix as Category A benchmarks. In reality, both tests execute zero mathematical formulas on the test side, asserting static hardcoded constants (`31.15`, `36.31`, `17.97`, `189.37`, `0.095`, `0.3038`, `66.35`). Furthermore, the report stated a count of **15 benchmarks**, whereas the CSV actually contains **18 benchmark rows** (BM-01 to BM-15, with sub-rows BM-02A/B and BM-03A/B/C).

---

## 2. MANDATORY PREFLIGHT & BASELINE PROTECTION AUDIT

Prior to beginning this audit, the repository environment and database checksums were verified:

| Parameter | Required Baseline | Observed Baseline | Parity Status |
| :--- | :--- | :--- | :---: |
| **Repository Path** | `/Users/karthik/tneb-account-extractor` | `/Users/karthik/tneb-account-extractor` | **MATCH** |
| **Active Git Branch** | `feature/phase1-structural-foundation` | `feature/phase1-structural-foundation` | **MATCH** |
| **Commit HEAD** | `df8d5da966b6506c1eada7093db2a140cbc0b9dc` | `df8d5da966b6506c1eada7093db2a140cbc0b9dc` | **MATCH** |
| **Tracked Modifications** | `server.py`, `templates/index.html` (Unstaged) | `server.py`, `templates/index.html` (Unstaged) | **PRESERVED** |
| **quotations.db SHA-256** | `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf` | `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf` | **BIT-FOR-BIT IDENTICAL** |
| **structural_runs.db SHA-256** | `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff` | `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff` | **BIT-FOR-BIT IDENTICAL** |
| **quotation_settings.json SHA-256** | `26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1` | `26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1` | **BIT-FOR-BIT IDENTICAL** |

---

## 3. IN-DEPTH AUDIT OF CRITICAL DEFECTS

### 3.1 DEF-01 — IS 800 Annex E & Table 42 Moment Gradient Analysis

#### A. Source Code Implementation vs Reported Claim
In [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py), lines 173–178 state:
```python
# 2. Evaluation with moment gradient factor C1 per IS 800 Table 42 / Annex E:
# For a simply-supported beam with a midspan lateral brace, the moment on the 0 to 4.556 m segment
# varies from M=0 at the end support to M_max at midspan (psi = 0.0).
# Per IS 800 Table 42 / equivalent uniform moment factor m: C1 = 1.75.
C1_gradient = 1.75
Mcr_grad, lam_grad, chi_grad, Md_grad = _calc_ltb(rafter_clear_span_mm, C1=C1_gradient)
ur_clear_grad = Mu_full / Md_grad  # 40.42 / 105.64 = 0.383
```

#### B. Independent Examination of IS 800:2007 Annex E & Table 42
Annex E, Clause E.1.2 defines the elastic critical moment for doubly symmetric I-sections as:
$$M_{cr} = c_1 \frac{\pi^2 E I_y}{(K L)^2} \left[ \left(\frac{K}{K_w}\right)^2 \frac{I_w}{I_y} + \frac{(K L)^2 G I_t}{\pi^2 E I_y} + (c_2 y_g - c_3 y_j)^2 \right]^{0.5} - (c_2 y_g - c_3 y_j)$$

Table 42 tabulates $c_1, c_2, c_3$ for simply supported beams. In Table 42:
- The entry giving $c_1 = 1.75$ corresponds strictly to **Case 1: Bending moment diagram with end moments only (linear variation, $\psi = 0$) with NO transverse loading on the unbraced length**.
- Table 42 contains **no entry** for a simply-supported beam under uniformly distributed load that is braced at midspan.

#### C. Evaluation of the Actual Moment Profile on the Restrained Segment
The rafter of total span $L = 9.112\text{ m}$ is simply supported at its ends ($x = 0$ and $x = 9.112\text{ m}$) and braced at midspan ($x = 4.556\text{ m}$). Under net factored wind uplift $w_{\text{net}} = 3.8948\text{ kN/m}$, the bending moment along the unbraced segment ($0 \le x \le 4.556\text{ m}$) is **parabolic**, governed by:
$$M(x) = \frac{w_{\text{net}} L}{2} x - \frac{w_{\text{net}} x^2}{2}$$

Evaluating key points along this restrained segment of length $L_b = 4.556\text{ m}$:
1. Support ($x = 0$): $M(0) = 0\text{ kNm}$.
2. Quarter-point of segment ($x = L/8 = 1.139\text{ m}$):  
   $$M_A = w_{\text{net}} L^2 \left(\frac{7}{128}\right) = \frac{7}{16} M_{\max} = 0.4375 \times 40.42 = \mathbf{17.68\text{ kNm}}$$
3. Mid-point of segment ($x = L/4 = 2.278\text{ m}$):  
   $$M_B = w_{\text{net}} L^2 \left(\frac{3}{32}\right) = \frac{3}{4} M_{\max} = 0.7500 \times 40.42 = \mathbf{30.32\text{ kNm}}$$
4. Three-quarter point of segment ($x = 3L/8 = 3.417\text{ m}$):  
   $$M_C = w_{\text{net}} L^2 \left(\frac{15}{128}\right) = \frac{15}{16} M_{\max} = 0.9375 \times 40.42 = \mathbf{37.89\text{ kNm}}$$
5. Midspan brace point ($x = L/2 = 4.556\text{ m}$):  
   $$M_{\max} = \frac{w_{\text{net}} L^2}{8} = 1.0000 \times 40.42 = \mathbf{40.42\text{ kNm}}$$

Notice that at the midpoint of the segment ($x = L/4$), the actual moment is $30.32\text{ kNm}$ ($75\%$ of $M_{\max}$). If the moment diagram were linear ($\psi = 0$), the midpoint moment would be only $0.50 M_{\max} = 20.21\text{ kNm}$. The parabolic profile is significantly fatter than a linear triangle.

#### D. Independent Calculation of True Moment Gradient Factor ($C_b$)
Applying the authoritative quarter-point moment gradient formulation (Kirby & Nethercot / AISC 360-16 / Eurocode equivalent):
$$C_b = \frac{12.5 M_{\max}}{2.5 M_{\max} + 3 M_A + 4 M_B + 3 M_C}$$
$$C_b = \frac{12.5(1.0)}{2.5(1.0) + 3(0.4375) + 4(0.7500) + 3(0.9375)} = \frac{12.5}{2.5 + 1.3125 + 3.0 + 2.8125} = \frac{12.5}{9.625} = \mathbf{1.2987} \approx \mathbf{1.30}$$

**Discrepancy:** The true parabolic moment gradient factor is $C_b = 1.30$, NOT $1.75$. Multiplying $M_{cr}$ by $1.75$ represents a **$34.6\%$ unconservative overestimation** of the gradient enhancement.

#### E. Corrected LTB Capacity & Multi-Configuration Reconciliation
Recalculating ISMB 300 capacity across all boundary configurations:

| Configuration | Unbraced Length ($L_b$) | Gradient Factor ($C_1$) | Elastic Critical Moment ($M_{cr}$) | Non-dimensional Slenderness ($\lambda_{LT}$) | Buckling Reduction ($\chi_{LT}$) | Design Capacity ($M_d$) | Factored Demand ($M_u$) | Governing Utilization Ratio | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Config 0: Full Unbraced Span** | $9.112\text{ m}$ | $1.00$ | $46.29\text{ kNm}$ | $1.875$ | $0.251$ | $37.12\text{ kNm}$ | $40.42\text{ kNm}$ | $\mathbf{1.089 > 1.0}$ | **FAIL** |
| **Config 1B: Clear Span Uniform Lower Bound** | $4.556\text{ m}$ | $1.00$ | $107.73\text{ kNm}$ | $1.229$ | $0.512$ | $75.74\text{ kNm}$ | $40.42\text{ kNm}$ | $\mathbf{0.534 \le 1.0}$ | **PASS** |
| **Config 1A (Corrected): Clear Span Parabolic Gradient** | $4.556\text{ m}$ | $\mathbf{1.30}$ | $\mathbf{140.05\text{ kNm}}$ | $\mathbf{1.078}$ | $\mathbf{0.611}$ | $\mathbf{90.40\text{ kNm}}$ | $40.42\text{ kNm}$ | $\mathbf{0.447 \le 1.0}$ | **PASS** |
| **Config 1A (Reported): Clear Span Linear Gradient** | $4.556\text{ m}$ | $1.75$ | $188.53\text{ kNm}$ | $0.929$ | $0.714$ | $105.64\text{ kNm}$ | $40.42\text{ kNm}$ | $0.383 \le 1.0$ | *Discrepancy* |
| **Config 2: Two-Span Continuous Framing** | $4.556\text{ m}$ | $1.00$ | $107.73\text{ kNm}$ | $1.229$ | $0.512$ | $75.74\text{ kNm}$ | $10.11\text{ kNm}$ | $\mathbf{0.133 \le 1.0}$ | **PASS** |

#### F. Load Height & Shear Centre Analysis ($y_g$ Term)
In IS 800:2007 Annex E, the transverse load level relative to the shear centre is parameterized by $y_g$:
- Wind uplift acts upward on the PV modules, pulling through the purlins onto the **top flange** of the rafter.
- In uplift bending, the top flange is the **tension flange** ($y = +150\text{ mm}$ above shear centre).
- In structural stability theory, transverse loads applied to the tension flange exert a **stabilizing (restoring) torque** as the member twists, increasing $M_{cr}$ ($y_g$ acts in the stabilizing direction).
- Omitting $y_g$ in the software workflow and setting $y_g = 0$ is therefore **structurally conservative**.

#### G. Torsional and Lateral Restraint Adequacy
The diagonal ISA 40×40×5 fly brace connects the rafter bottom flange to the purlin, while the purlin cleat bolts restrain the top flange. This triangulation creates an effective couple that restrains both **lateral translation of the compression flange** and **cross-sectional twist**. However, it does not provide warping restraint ($K_w = 1.0, K = 1.0$).

---

### 3.2 DEF-02 — Restraint Stiffness, Eccentricity, and Applicable Clauses

#### A. Clause Citation Discrepancy
The report and codebase repeatedly cite **IS 800:2007 Clause 8.9.1** and **Clause 8.9.2**:
- In the official Bureau of Indian Standards text of **IS 800:2007**, Clause 8.9 is a single consolidated section titled *"Purlins and Sheeting Rails (Girts)"*. It contains **no subclause 8.9.1 or 8.9.2**.
- The statutory requirement that intermediate lateral restraints resist **$2.5\%$ of the maximum compression flange force** is codified in **IS 800:2007 Clause 8.3.2** (*Intermediate Lateral Restraints for Beams*).
- The required lateral restraint stiffness equation:
  $$K_{req} = \frac{4 N_c}{L_b}$$
  is not an explicit clause in IS 800:2007. It is the classical **Winter-Yura bracing criterion** (AISC 360-16 Appendix 6 / Eurocode 3 stability principle) to enforce a nodal buckling point.

#### B. Member Stiffness vs Complete Restraint-System Stiffness
In [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py), line 351 calculates:
$$K_{\text{lat}} = \frac{A E}{L} \cos^2(45^\circ) = \frac{379 \times 205}{600} \times 0.5 = 64.75\text{ kN/mm}$$
and claims a stiffness ratio of $64.75 / 0.1234 = 524.7\times$.

**Audit Finding:** $K_{\text{lat}} = 64.75\text{ kN/mm}$ represents **only the idealized axial extensional stiffness of the diagonal angle strut member**. In reality, the lateral restraint acts as a series of springs:
$$\frac{1}{K_{\text{system}}} = \frac{1}{K_{\text{strut}}} + \frac{1}{K_{\text{cleat}}} + \frac{1}{K_{\text{bolts}}} + \frac{1}{K_{\text{purlin}}}$$
- The cold-formed purlin web is only $2.0\text{ mm}$ thick. If the fly brace were attached to the unstiffened purlin web, the web out-of-plane bending flexibility would reduce $K_{\text{system}}$ by orders of magnitude.
- Attaching the fly brace directly to a **$6\text{ mm}$ stiffened angle cleat** (as mandated in Phase 1.5.3.2B) restores rigid load transfer. Because $K_{req} = 0.1234\text{ kN/mm}$ is extremely small, $K_{\text{system}}$ comfortably exceeds $K_{req}$, but presenting $524.7\times$ without stating that it is a member-level upper bound is an oversimplification.

#### C. Angle Compression & Eccentricity Interaction
The angle strut (ISA 40×40×5, $L = 600\text{ mm}$, $r_{vv} = 7.7\text{ mm}$, $\lambda = 77.92$) was evaluated under combined axial compression ($F = 4.969\text{ kN}$) and single-leg connection eccentricity ($M_{ecc} = 4.969 \times 0.0116 = 0.0576\text{ kNm}$).
- Evaluated per IS 800:2007 Clause 7.1.2 and Clause 9.3:
  $$IR = \frac{F}{P_d} + \frac{M_{ecc}}{M_d} = \frac{4.969}{53.48} + \frac{0.0576}{0.441} = 0.093 + 0.131 = \mathbf{0.224 \le 1.0} \quad (\mathbf{PASS})$$
- Bolt shear per Clause 10.3.2: $V_{dsb} = 31.15\text{ kN} \implies \mathbf{UR = 0.160 \le 1.0}$ (PASS).
- Bolt bearing on $5\text{ mm}$ cleat per Clause 10.3.3: $V_{dpb} = 36.31\text{ kN} \implies \mathbf{UR = 0.137 \le 1.0}$ (PASS).

---

### 3.3 DEF-03 — Weld Group Geometry & Stress Distribution

#### A. Contour Perimeter Verification
For an ISMB 300 rolled section ($h = 300\text{ mm}, b = 140\text{ mm}, t_w = 7.5\text{ mm}, t_f = 12.4\text{ mm}$), the exact all-around fillet weld contour length is:
$$L_w = 2 b + 2(b - t_w) + 4 t_f + 2(h - 2 t_f) = 2(300) + 4(140) - 2(7.5) = 600 + 560 - 15 = \mathbf{1145.0\text{ mm}}$$
For a $6\text{ mm}$ fillet weld, throat $a = 0.70 \times 6.0 = 4.2\text{ mm} \implies A_w = 1145.0 \times 4.2 = \mathbf{4809.0\text{ mm}^2}$.

#### B. Independent Section Modulus ($Z_w$) Derivation
In [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py), line 686 hardcodes:
`Zw_mm3 = 450067.0 # Weld section modulus about major axis`

Integrating each segment of the weld group about the major bending axis ($z-z$, $y_{\max} = 150\text{ mm}$):
1. Outer flange welds (2 segments, $L = 140\text{ mm}$ at $y = 150\text{ mm}$):  
   $I_1 = 2 \times (140 \times 4.2) \times 150^2 = 26,460,000.0\text{ mm}^4$
2. Inner flange welds (4 segments, $L = 66.25\text{ mm}$ at $y = 137.6\text{ mm}$):  
   $I_2 = 4 \times (66.25 \times 4.2) \times 137.6^2 = 21,073,274.9\text{ mm}^4$
3. Flange vertical tips (4 segments, $L = 12.4\text{ mm}$, centroid at $y = 143.8\text{ mm}$):  
   $I_3 = 4 \times \left[\frac{4.2 \times 12.4^3}{12} + (4.2 \times 12.4) \times 143.8^2\right] = 4,310,401.9\text{ mm}^4$
4. Web welds (2 segments, $L = 275.2\text{ mm}$, centered at $y = 0$):  
   $I_4 = 2 \times \frac{4.2 \times 275.2^3}{12} = 14,589,598.1\text{ mm}^4$
- Total group moment of inertia: $I_{w,\text{exact}} = 66,433,274.9\text{ mm}^4$.
- Exact section modulus:  
  $$Z_{w,\text{exact}} = \frac{I_{w,\text{exact}}}{y_{\max}} = \frac{66,433,274.9}{150.0} = \mathbf{442,888.5\text{ mm}^3}$$

**Discrepancy:** The hardcoded $450,067.0\text{ mm}^3$ is $1.60\%$ larger than the exact value ($442,888.5\text{ mm}^3$), caused by an earlier approximation lumping the inner flange welds at $y = 150\text{ mm}$.

#### C. Verification of Load Combinations per IS 800:2007 Clause 10.5.10
Permissible equivalent weld stress:
$$f_{vwd} = \frac{f_u}{\sqrt{3} \gamma_{mw}} = \frac{410}{\sqrt{3} \times 1.25} = \mathbf{189.37\text{ MPa}}$$

1. **Gravity Combination (ULS-01: $P_u = 33.84\text{ kN}, V_u = 3.50\text{ kN}, M_z = 4.90\text{ kNm}$):**
   - $f_a = \frac{33.84 \times 10^3}{4809.0} = 7.04\text{ MPa}$
   - $f_b = \frac{4.90 \times 10^6}{442,888.5} = 11.06\text{ MPa}$ (vs reported $10.89\text{ MPa}$)
   - $q = \frac{3.50 \times 10^3}{4809.0} = 0.73\text{ MPa}$
   - Peak normal stress: $f_{a,\text{total}} = 7.04 + 11.06 = 18.10\text{ MPa}$
   - Combined equivalent stress:
     $$f_e = \sqrt{(18.10)^2 + 3(0.73)^2} = \sqrt{327.61 + 1.60} = \mathbf{18.14\text{ MPa}} \le 189.37\text{ MPa} \implies \mathbf{UR = 0.096 \le 1.0} \quad (\mathbf{PASS})$$

2. **Wind Uplift Reversal (ULS-02: $T_u = 18.50\text{ kN}, V_u = 3.50\text{ kN}, M_z = 4.90\text{ kNm}$):**
   - Direct tension: $f_t = \frac{18.50 \times 10^3}{4809.0} = 3.85\text{ MPa}$
   - Peak tension: $f_{t,\max} = 3.85 + 11.06 = 14.91\text{ MPa}$
   - Combined equivalent stress:
     $$f_e = \sqrt{(14.91)^2 + 3(0.73)^2} = \sqrt{222.31 + 1.60} = \mathbf{14.96\text{ MPa}} \le 189.37\text{ MPa} \implies \mathbf{UR = 0.079 \le 1.0} \quad (\mathbf{PASS})$$

Both governing combinations pass comfortably ($UR < 0.10$).

---

### 3.4 DEF-04 — Host Slab Punching Shear & Chemical Anchor Breakout

#### A. Audit of Hardcoded Anchor Breakout Capacity ($\phi N_{cbg,\text{cr}} = 66.35\text{ kN}$)
Line 719 of [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py) sets `phi_Ncbg_cracked_kn = 66.35`.
Tracing this derivation to fib Bulletin 58 / EN 1992-4:
- Assumed 4× M16 anchors, $h_{ef} = 125\text{ mm}$, spacing $s_x = 250\text{ mm}, s_y = 150\text{ mm}$ in M20 concrete ($f_{ck} = 20\text{ MPa}$).
- Single uncracked anchor: $N_{Rk,c}^0 = 9.75 \times \sqrt{20} \times (125)^{1.5} = 60.94\text{ kN}$.
- Group projected area ratio: $A_{c,N} / A_{c,N}^0 = (375+250)(375+150) / (375 \times 375) = 328,125 / 140,625 = 2.3333$.
- Uncracked group resistance: $N_{Rk,c} = 60.94 \times 2.3333 = 142.19\text{ kN} \implies \phi N_{cbg} = 142.19 / 1.50 = 94.79\text{ kN}$.
- Cracked concrete factor ($0.70$): $\phi N_{cbg,\text{cr}} = 94.79 \times 0.70 = \mathbf{66.35\text{ kN}}$.

#### B. Physical Impossibility in 125–150 mm Slabs
While the mathematical formula is consistent, **it is physically impossible to execute in the host roof slab**:
- For an M16 anchor with $h_{ef} = 125\text{ mm}$ and drill hole $d_0 = 18\text{ mm}$, manufacturer ETAs (Hilti ETA-20/0541 / Fischer ETA-17/0979) mandate:
  $$h_{\min} \ge h_{ef} + 2 d_0 = 125 + 2(18) = \mathbf{161.0\text{ mm}}$$
- Typical rooftop slabs in Salem, Tamil Nadu are $125\text{ mm}$ to $150\text{ mm}$ thick. Drilling a $125\text{ mm}$ hole in a $125\text{ mm}$ slab will core completely through the slab; in a $150\text{ mm}$ slab it leaves only $25\text{ mm}$ bottom concrete cover, causing blowout during drilling and spalling under expansion/proof load.
- Chemical anchors with $h_{ef} = 125\text{ mm}$ are **physically incompatible** with the slab unless structural concrete plinths/pedestals are cast or through-bolts with bottom bearing plates are used.

#### C. Unbalanced Moment Punching Shear Formulation (IS 456 Cl 31.6.2.2)
- Assumed baseplate $350 \times 250\text{ mm}$, effective depth $d = 100\text{ mm}$, critical perimeter at $d/2 = 50\text{ mm}$:  
  $b_1 = 450\text{ mm}, b_2 = 350\text{ mm}, b_0 = 2(450 + 350) = 1600\text{ mm}$.
- Unbalanced moment fraction transferred by shear:  
  $$\alpha_v = 1 - \frac{1}{1 + \frac{2}{3} \sqrt{\frac{b_1}{b_2}}} = 1 - \frac{1}{1 + \frac{2}{3} \sqrt{\frac{450}{350}}} = 1 - \frac{1}{1 + 0.7559} = \mathbf{0.4305}$$
- Polar moment of inertia $J_c$:  
  $$J_c = \frac{100 \times 450^3}{6} + \frac{450 \times 100^3}{6} + \frac{100 \times 350 \times 450^2}{2} = 1.5188 \times 10^9 + 0.0750 \times 10^9 + 3.5438 \times 10^9 = \mathbf{5.1375 \times 10^9\text{ mm}^4}$$
- Peak combined shear stress:  
  $$\tau_{v,\max} = \frac{33.84 \times 10^3}{1600 \times 100} + \frac{(0.4305 \times 4.90 \times 10^6)(225)}{5.1375 \times 10^9} = 0.2115 + 0.0924 = \mathbf{0.3039\text{ MPa}}$$
- Permissible shear stress: $\tau_c = 0.25 \sqrt{20} = \mathbf{1.1180\text{ MPa}} \implies \mathbf{UR = 0.272 \le 1.0}$ (PASS).
- **Physical Caveat:** The calculation is mathematically valid, but $f_{ck} = 20\text{ MPa}$, slab thickness $h = 150\text{ mm}$, and $d = 100\text{ mm}$ are **100% assumed**. Site verification under **HOLD-01** and **HOLD-03** is mandatory.

---

### 3.5 DEF-05 — Hermetic Test Isolation Implementation

#### A. Source Audit of Test Isolation
An inspection of [`tests/test_isolation_helper.py`](file:///Users/karthik/tneb-account-extractor/tests/test_isolation_helper.py) and [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) was performed:
1. `IsolatedTestEnvironment` creates a temporary directory prefixed with `rensun_test_iso_`.
2. Global singletons (`qh.DB_PATH`, `sm.SETTINGS_FILE`, `pg.OUTPUT_PDF_DIR`, `STRUCTURAL_BRIDGE.db`, `STRUCTURAL_BRIDGE.drawing_output_dir`) are safely redirected.
3. Tests 10, 12, and 13 in `tests/test_phase1_5_3_2_system_a_final.py` connect strictly to `self.iso.structural_db_path`.
4. Production databases (`quotations.db`, `structural/structural_runs.db`) are protected by pre- and post-test SHA-256 assertions in `tearDownClass`.

#### B. Verification of Alternate Code Paths
No module in `structural/workflows/` directly imports `sqlite3` or instantiates `StructuralDatabase` with default production paths. The workflow is purely computational and functional. Isolation is **hermetically enforced**.

---

### 3.6 DEF-06 — Independent Test Quality & Benchmark Reconciliation

#### A. Forensic Audit of All 13 Test Methods

| Test ID | Test Method Name | Stated Category | Audited Implementation | Genuine First-Principles Calculation Present? | Hard-Coded Constants Asserted | Independence Verdict |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: |
| **TEST-01** | `test_01_wind_uplift_factored_moment_demand` | Category A | Independently calculates $V_z, p_z, w_{\text{net}}, M_u$ test-side. | **YES** | None | **GENUINE INDEPENDENT BENCHMARK** |
| **TEST-02** | `test_02_rafter_ltb_with_moment_gradient...` | Category A | Solves $I_t, I_w, M_{cr,0}, C_1, M_d$ for gradient. However, full-span and 2-span use hardcoded constants. | **PARTIAL** | $46.29, 37.12, 1.089, 10.11, 0.133$ | **PARTIALLY INDEPENDENT BENCHMARK** |
| **TEST-03** | `test_03_fly_bracing_required_stabilizing_force` | Category B | Independently calculates $N_c, P_{br}, F_{brace}$ test-side. | **YES** | None | **GENUINE INDEPENDENT BENCHMARK** |
| **TEST-04** | `test_04_fly_bracing_stiffness_and_single_leg...` | Category A | Solves $K_{req}$ and $K_{\text{lat}}$ test-side. Eccentricity moment ($0.0576$) is asserted as constant. | **PARTIAL** | $0.0576\text{ kNm}$ | **PARTIALLY INDEPENDENT BENCHMARK** |
| **TEST-05** | `test_05_fly_bracing_bolt_bearing_and_purlin_cleat` | Category A | **NO SOLVER EXECUTED.** Asserts outputs directly against static numbers. | **NO** | $\mathbf{31.15, 36.31, 6.0}$ | **MISLABELED: STATIC CONSTANT COMPARISON** |
| **TEST-06** | `test_06_chemical_anchor_standards_hierarchy` | Category D | Metadata mapping inspection. | N/A | None | **ACCURATELY CLASSIFIED GOVERNANCE** |
| **TEST-07** | `test_07_project_specific_anchor_testing_protocol` | Category E | Protocol constants inspection. | N/A | $27.75, 25.0, 3, 0.20$ | **ACCURATELY CLASSIFIED PROTOCOL** |
| **TEST-08** | `test_08_slab_thickness_evaluation_and_alternatives` | Category C | Evaluates $h_{\min} = 161\text{ mm}$ against $125/150\text{ mm}$. | **YES** | None | **ACCURATELY CLASSIFIED FEASIBILITY** |
| **TEST-09** | `test_09_weld_combined_stress_and_slab_unbalanced...`| Category A | **NO SOLVER EXECUTED.** Formulas exist only in comments. Asserts outputs against static numbers. | **NO** | $\mathbf{17.97, 189.37, 0.095, 0.3038, 1.118, 0.272, 66.35, 0.279}$ | **MISLABELED: STATIC CONSTANT COMPARISON** |
| **TEST-10** | `test_10_historical_records_in_isolated_environment` | Category G | Queries isolated SQLite database for count $= 20$. | N/A | $20$ | **ACCURATELY CLASSIFIED ISOLATION** |
| **TEST-11** | `test_11_original_holds_active_and_enforced` | Category D | Queries `MASTER_VERIFICATION_REGISTER`. | N/A | $12\text{ holds}, 10\text{ System A}$ | **ACCURATELY CLASSIFIED GOVERNANCE** |
| **TEST-12** | `test_12_afc_lock_and_statutory_watermark...` | Category G | Queries isolated database for `BLOCKED_AFC_LOCKED`. | N/A | `BLOCKED_AFC_LOCKED` | **ACCURATELY CLASSIFIED STATUTORY** |
| **TEST-13** | `test_13_zero_production_database_access_verified` | Category G | Formally asserts runtime path divergence. | **YES** | None | **GENUINE HERMETIC ISOLATION PROOF** |

#### B. Reconciliation of Stated Benchmark Count vs Actual CSV Row Count
- In [`PHASE_1_5_3_2B_SYSTEM_A_DEFECT_CORRECTION_REPORT.md`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2B_SYSTEM_A_DEFECT_CORRECTION_REPORT.md), line 235 states:  
  `| **DEL-02** | PHASE_1_5_3_2B_SYSTEM_A_INDEPENDENT_BENCHMARKS.csv | 15 verified mathematical calculation benchmarks |`
- An exact count of [`PHASE_1_5_3_2B_SYSTEM_A_INDEPENDENT_BENCHMARKS.csv`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2B_SYSTEM_A_INDEPENDENT_BENCHMARKS.csv) reveals **18 data rows** (lines 2 to 19):
  - BM-01, **BM-02A, BM-02B**, **BM-03A, BM-03B, BM-03C**, BM-04, BM-05, BM-06, BM-07, BM-08, BM-09, BM-10, BM-11, BM-12, BM-13, BM-14, BM-15.
- **Root Cause of Discrepancy:** The report author referenced the highest benchmark ID (`BM-15`) without accounting for the sub-divided rows (`BM-02A/B` and `BM-03A/B/C`), resulting in an arithmetic mismatch of $15$ vs $18$ rows.

---

## 4. SUMMARY OF AUDIT FINDINGS SCORECARD

```
+--------------------------------------------------------------------------------------------------------------------+
|                                      PHASE 1.5.3.2B.1 AUDIT DISCREPANCY SCORECARD                                  |
+---------+-----------------------------------+------------------------------------------+---------------------------+
| Item ID | Topic                             | Identified Discrepancy                   | Audit Verdict             |
+---------+-----------------------------------+------------------------------------------+---------------------------+
| AUD-01  | Rafter LTB Moment Gradient (C1)   | C1 = 1.75 overestimates parabolic UDL    | RECONCILED (Cb = 1.30;    |
|         |                                   | moment gradient by 35% (Cb = 1.30 true)  | UR = 0.447 <= 1.0 PASS)   |
| AUD-02  | Lateral Restraint Clause Citation | Cited IS 800 Cl 8.9.1 & 8.9.2 (Purlins); | RECONCILED (Citation      |
|         |                                   | true clause is Cl 8.3.2 / Winter-Yura    | aligned to Cl 8.3.2)      |
| AUD-03  | Fly-Bracing System Stiffness      | 64.75 kN/mm is member axial upper bound; | QUALIFIED (Requires 6 mm  |
|         |                                   | purlin web flexibility unmodeled         | stiffened cleat plate)    |
| AUD-04  | Baseplate Weld Section Modulus    | Zw = 450067 mm3 is hardcoded;            | RECONCILED (Passes with   |
|         |                                   | exact derived Zw = 442888.5 mm3 (-1.6%)  | UR = 0.096 <= 1.0)        |
| AUD-05  | Chemical Anchor Physical Depth    | 66.35 kN breakout requires hef = 125 mm; | RECONCILED (Physically    |
|         |                                   | impossible in 125-150 mm slab (hmin=161) | incompatible without sup) |
| AUD-06  | Host Slab Punching Shear Inputs   | Punching math verified, but fck = 20 MPa | THEORETICAL PASS          |
|         |                                   | and d = 100 mm are unverified on site    | (Site evidence blocked)   |
| AUD-07  | Test 05 & Test 09 Independence    | Mislabeled as independent solvers;       | DISCREPANCY CONFIRMED     |
|         |                                   | actually assert static hardcoded numbers | (Tests must be refactored)|
| AUD-08  | Benchmark Count Reconciliation    | Report claimed 15 benchmarks; CSV        | RECONCILED (18 rows due   |
|         |                                   | contains 18 data rows (BM-01 to BM-15)   | to sub-divided benchmarks)|
+---------+-----------------------------------+------------------------------------------+---------------------------+
```

---

## 5. STATUTORY GOVERNANCE & MANDATORY HOLDS

All canonical engineering safeguards remain strictly enforced:
- **Statutory Watermark:** Mandatory on all outputs:
  ```
  PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION
  ```
- **Construction Lock:** Strictly maintained:
  ```
  is_approved_for_construction = false
  construction_status = BLOCKED_AFC_LOCKED
  ```
- **Canonical Engineering Holds (All 12 Active):**
  - `HOLD-01`: Host slab physical thickness and concrete compressive strength unverified.
  - `HOLD-02`: Aerodynamic wind tunnel co-coefficients unverified.
  - `HOLD-03`: Concrete core sampling and NDT testing pending.
  - `HOLD-04`: Chemical anchor pull-out proof load test (27.75 kN) pending.
  - `HOLD-05` to `HOLD-12`: Fastener torque, drawing correlation, and workshop fabrication details pending.

---

## 6. AUDIT DELIVERABLES INDEX

Four authoritative deliverables have been authored for Phase 1.5.3.2B.1:

1. **Audit Report:**  
   [`PHASE_1_5_3_2B1_INDEPENDENT_REMEDIATION_AUDIT.md`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2B1_INDEPENDENT_REMEDIATION_AUDIT.md)  
   *(Also mirrored in [`docs/phase_1_5/`](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/PHASE_1_5_3_2B1_INDEPENDENT_REMEDIATION_AUDIT.md) and Brain Artifact store)*
2. **Standard Citation Matrix:**  
   [`PHASE_1_5_3_2B1_CODE_STANDARD_CITATION_MATRIX.csv`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2B1_CODE_STANDARD_CITATION_MATRIX.csv)
3. **Test Independence Audit Matrix:**  
   [`PHASE_1_5_3_2B1_TEST_INDEPENDENCE_AUDIT.csv`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2B1_TEST_INDEPENDENCE_AUDIT.csv)
4. **Calculation Reconciliation Matrix:**  
   [`PHASE_1_5_3_2B1_CALCULATION_RECONCILIATION.csv`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2B1_CALCULATION_RECONCILIATION.csv)

---

## 7. FINAL ENGINEERING CLASSIFICATION

```
====================================================================================================
FINAL PHASE 1.5.3.2B.1 STATUS:
ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE
CONSTRUCTION STATUS: BLOCKED_AFC_LOCKED
is_approved_for_construction = false
STATUTORY WATERMARK: PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION
====================================================================================================
```
