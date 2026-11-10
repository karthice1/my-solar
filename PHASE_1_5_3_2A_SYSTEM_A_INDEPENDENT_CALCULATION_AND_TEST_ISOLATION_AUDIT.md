# PHASE 1.5.3.2A — SYSTEM A INDEPENDENT CALCULATION & TEST-ISOLATION AUDIT REPORT
## RENSUN SOLAR STRUCTURAL ENGINEERING VALIDATION PROGRAMME

**Platform:** Google Antigravity  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Base Commit / HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Project ID:** `RS-STR-RENSUN-2026-0059`  
**Client / Site:** 90 ERUMAPALAYAM ITTERI ROAD, SALEM, TAMIL NADU (11.6643°N, 78.1460°E)  
**Quotation Reference:** `RENSUN/2026/0059`  
**Mounting System:** `System A: Elevated Steel Canopy (H = 2.8 m)`  
**Audit Phase:** Phase 1.5.3.2A — Independent Calculation & Test-Isolation Audit  
**Date of Audit:** 2026-11-08  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED`  
**Approval Flag:** `is_approved_for_construction = false`

---

## 1. EXECUTIVE SUMMARY

This independent engineering audit evaluates Phase 1.5.3.2 System A (Elevated Steel Canopy) across mathematical reproducibility, source-code implementation fidelity, structural load-path completeness, anchor/slab feasibility, test-environment hermeticity, and statutory hold enforcement.

### Key Audit Findings:
1. **Mathematical Reproducibility (WP-01 & WP-07):**  
   All 10 primary numerical calculations in [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py) were independently derived from raw first principles using standalone equations. Numerical divergence between independent benchmarks and the production code is negligible ($\le 0.015\text{ kN}$ / $\le 0.04\%$), confirming raw arithmetic consistency.
2. **Critical Structural Discrepancy — Rafter Restraint Demand (WP-01):**  
   Under full-span unbraced conditions ($L = 9.112\text{ m}$), the rafter fails Lateral-Torsional Buckling under wind uplift ($M_u = 40.42\text{ kNm}$, $M_d = 37.12\text{ kNm} \implies \mathbf{UR = 1.089 > 1.0}$, **FAIL**).  
   However, for the restrained clear-span check ($L_b = 4.556\text{ m}$), the implementation compares full-span demand ($40.42\text{ kNm}$) directly against clear-span capacity ($M_d = 75.74\text{ kNm}$), while simultaneously reporting $M_{u,\text{half}} = 10.11\text{ kNm}$. The model conflates a nodal midspan lateral brace with a 2-span continuous framing model, and omits the codal moment gradient factor $C_1$ (IS 800 Table 42 / Annex E).
3. **Fly-Bracing System Completeness (WP-02):**  
   The ISA 40×40×5 mm member axial capacity ($P_d = 53.48\text{ kN}$, $UR = 0.093$) and M12 Grade 8.8 single bolt shear ($V_{dsb} = 31.15\text{ kN}$, $UR = 0.160$) are verified. However, restraint stiffness ($K_{br}$ vs IS 800 Cl 8.9.2 minimum requirement), single-angle connection eccentricity, and cleat plate flexural yielding were NOT checked in code.
4. **Anchor Protocol Classification (WP-03):**  
   The retraction of IS 800 Cl 10 is verified. However, the proposed proof test protocol ($27.75\text{ kN}$ group load, 25% sampling, $0.20\text{ mm}$ slip limit) represents **Engineer-Selected Project Criteria**, not universal statutory code constants. Manufacturer European Technical Assessment (ETA) dossiers remain outstanding.
5. **Host Slab & Anchorage Feasibility (WP-04):**  
   The audit confirms that $h_{ef} = 125\text{ mm}$ embedment is physically impossible in standard $125 - 150\text{ mm}$ roof slabs without blowing out the soffit or violating bottom cover. The proposed alternatives (reduced embedment, through-bolting, stub pedestals) remain conceptual proposals without site verification.
6. **Weld and Foundation Checks (WP-05):**  
   Column baseplate fillet weld ($UR = 0.037$) and RCC punching shear ($UR = 0.189$) were evaluated under pure axial downward compression only. Co-existing lateral shear ($3.50\text{ kN}$), base moment ($4.90\text{ kNm}$), wind uplift reversal ($18.50\text{ kN}$), and unbalanced moment punching were omitted from the implementation.
7. **Test Isolation & Production Database Access (WP-06):**  
   [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) imports `IsolatedTestEnvironment`, but **never instantiates it**. Tests 10 and 12 connect directly to the live production database (`structural/structural_runs.db`) via read-only SQL queries. While pre- and post-test SHA-256 hash assertions confirm zero mutations occurred, true hermetic test isolation was NOT achieved in that suite.
8. **Test Quality Classification (WP-08):**  
   None of the 12 tests in `test_phase1_5_3_2_system_a_final.py` implement independent first-principles derivations. They function as regression/fixed-output consistency tests (Category E/B) that assert hardcoded constants matching the module's own returns.
9. **Hold Enforcement & AFC Lock (WP-09):**  
   All 12 canonical engineering holds remain active. Specifically for System A, `HOLD-01` (Slab NDT), `HOLD-03` (Rooftop Boundary Survey), and `HOLD-07` (Fastener Proof Load Testing) remain strictly enforced. Construction status is locked at `BLOCKED_AFC_LOCKED`.

---

## 2. AUDIT SCOPE & WORK PACKAGES

```
+----------------------------------------------------------------------------------------------------+
|                                    PHASE 1.5.3.2A AUDIT MATRIX                                     |
+---------+----------------------------------------------+---------------------------+---------------+
| WP ID   | Audit Work Package                           | Governing Module / File   | Final Verdict |
+---------+----------------------------------------------+---------------------------+---------------+
| WP-01   | Wind Uplift & Rafter LTB Independent Audit   | system_a_final.py (L81)   | PARTIALLY VER.|
| WP-02   | Fly-Bracing System Structural Audit          | system_a_final.py (L234)  | PARTIALLY VER.|
| WP-03   | Chemical Anchor Statutory & Testing Audit    | system_a_final.py (L349)  | PARTIALLY VER.|
| WP-04   | RCC Slab Thickness & Feasibility Audit       | system_a_final.py (L467)  | VERIFIED (DEF)|
| WP-05   | Weld & Foundation Load-Path Audit            | system_a_final.py (L551)  | PARTIALLY VER.|
| WP-06   | Test Isolation & Production Safety Audit     | test_phase1_5_3_2_final   | DEFECT FOUND  |
| WP-07   | Independent Engineering Benchmarks (10 Nos.) | audit_benchmarks.py       | VERIFIED      |
| WP-08   | Test Quality Classification (12 Tests)       | test_quality_matrix.csv   | COMPLETED     |
| WP-09   | Canonical Hold & AFC Restriction Audit       | structural/holds.py       | VERIFIED (LCK)|
| WP-10   | Audit Report & Defect Register               | Current Document          | COMPLETED     |
+---------+----------------------------------------------+---------------------------+---------------+
```

---

## 3. REPOSITORY & GIT BASELINE

The repository state was inspected prior to audit commencement and remained strictly unaltered:
- **Repository Path:** `/Users/karthik/tneb-account-extractor`
- **Active Branch:** `feature/phase1-structural-foundation`
- **Git HEAD Commit:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`
- **Tracked Modifications (Unstaged):** `server.py`, `templates/index.html` (preserved from earlier phases)
- **Git Operations:** ZERO commits, pushes, merges, rebases, resets, or stashes were executed.

---

## 4. SOURCE FILE HASH REGISTER

Cryptographic SHA-256 hashes of all primary files audited under Phase 1.5.3.2A:

| Category | File Path | SHA-256 Hash |
|:---|:---|:---:|
| **Production DB** | `quotations.db` | `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf` |
| **Production DB** | `structural/structural_runs.db` | `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff` |
| **Settings File** | `quotation_settings.json` | `26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1` |
| **Implementation**| `structural/workflows/system_a_final.py` | `37564629b6c8a5409e830cb18da1bfe4fef2b9da305f8eeec2f5ce51631136e5` |
| **Implementation**| `structural/workflows/system_a_reconciliation.py`| `8cb10e8e81916f05ad785b6ba3606843a9efcf0e04d07006e8f0ad6fc61cae3f` |
| **Implementation**| `structural/workflows/system_a_validation.py` | `72029d7205540e4f48ad02c318bff687817b250c4514747341e934c53978f724` |
| **Implementation**| `structural/workflows/system_a.py` | `ebfdca9734eb5bb74081b03f6870f92b782fffb53de4d52e31cc3f7df73c8213` |
| **Core Module**   | `structural/models.py` | `a2ab700752804b4039b1713f86540ff0daed4e3ccdca3453939d9bbc6eeeff72` |
| **Core Module**   | `structural/actions.py` | `10153184d4559ac258a9250c331c7a3dc82926ac699db5f2c5cc8ad8cf2aca7f` |
| **Core Module**   | `structural/engine.py` | `a65672234d605f08914c9ec0aac0087aaed84a3086c5702fbb9b52be453c0852` |
| **Core Module**   | `structural/holds.py` | `2ae9faad2d72a247d61b8092021b39d8ad978effce5a00a465a9ce602e386378` |
| **Core Module**   | `structural/provenance.py` | `bf4550a83b622c27459d474fe875045fcb3ec344e8d591b36aeb2ad0ae0ffd5f` |
| **Test Suite**    | `tests/test_phase1_5_3_2_system_a_final.py` | `8aaa4f6d43c85d174737a54d21b141c1f8488443e3ed45c7261b26065f29cbe2` |
| **Test Suite**    | `tests/test_phase1_5_3_system_a.py` | `aac2f4721975521530e399cae6eafc6723440f011e23d46d53416564124ca0cb` |
| **Test Helper**   | `tests/test_isolation_helper.py` | `29b7834ec43fd041918cafcf02af2f2e040e930af2bb8ad69960a1748e97b008` |
| **Prior Report**  | `PHASE_1_5_3_2_SYSTEM_A_FINAL_ENGINEERING_RECONCILIATION_REPORT.md` | `687bf323347a611d8d428eb26cecef13c5018d96b37e142eb9523a9bfcde33e3` |
| **Reconstructed**| `PHASE_1_5_3_2_SYSTEM_A_ENGINEERING_VALIDATION_REPORT_RECONSTRUCTED.md` | `1f92a24b342f951885245df30aa1673a675622ee667a538e8ddf8d0df93081c7` |

---

## 5. CALCULATION INPUT REGISTER

| Parameter | Symbol | Nominal Value | Unit | Provenance & Standard | Verification Status |
|:---|:---:|:---:|:---:|:---|:---:|
| Basic Wind Speed (Salem) | $V_b$ | $39.0$ | $\text{m/s}$ | IS 875 (Part 3): 2015 Map | Regional Constant |
| Terrain & Height Factor | $k_2$ | $1.028$ | — | IS 875 Table 2 (Cat 2, 10 m) | Codal Value |
| Risk / Topo / Cyclone Factors | $k_1, k_3, k_4$| $1.0, 1.0, 1.0$ | — | IS 875 Part 3 Clauses 6.3–6.5 | Codal Default |
| Aerodynamic Uplift Coeff. | $C_{n,\text{up}}$ | $-1.10$ | — | Monopitch canopy suction | Provisional Assumption |
| Rafter Tributary Width | $B_t$ | $3.0$ | $\text{m}$ | Column spacing across bay | Layout Dimension |
| PV Module Dead Load | $w_{\text{mod}}$ | $0.1044$ | $\text{kN/m}^2$ | 540 Wp module weight | Product Spec |
| Rafter Linear Mass (ISMB 300) | $m_{\text{raf}}$ | $44.2$ | $\text{kg/m}$ | IS 808: 1989 Table 1 | Certified Section |
| Purlin Linear Mass (ISMC 100) | $m_{\text{pur}}$ | $3.53$ | $\text{kg/m}$ | Cold-formed C-channel | Certified Section |
| Walkway Dead Load Allowance | $w_{\text{walk}}$| $0.20$ | $\text{kN/m}$ | Maintenance grating | Engineering Allowance |
| Total Sloped Rafter Span | $L_{\text{full}}$ | $9.112$ | $\text{m}$ | 4 rows $\times$ 2.278 m module | Layout Geometry |
| Clear Column Span | $L_{\text{clear}}$| $4.556$ | $\text{m}$ | Half-span / intermediate support | Layout Geometry |
| Steel Grade (Rafter & Strut) | — | IS 2062 E250 | — | $f_y = 250\text{ MPa}$, $f_u = 410\text{ MPa}$ | Certified Steel |
| Elastic Modulus | $E$ | $205,000$ | $\text{MPa}$ | IS 800: 2007 Cl 2.2.4.1 | Codal Constant |
| Fly-Bracing Angle Section | — | ISA 40×40×5 | — | $A = 379\text{ mm}^2$, $r_{\min} = 7.7\text{ mm}$ | IS 808 Standard Angle |
| Fly-Bracing Fastener | — | 1x M12 Gr 8.8 | — | $f_{ub} = 800\text{ MPa}$, $A_{nb} = 84.3\text{ mm}^2$ | ISO 898-1 Bolt |
| Host Concrete Grade | $f_{ck}$ | $20.0$ | $\text{MPa}$ | Assumed M20 nominal concrete | **UNVERIFIED (HOLD-01)** |

---

## 6. INDEPENDENT CALCULATION BENCHMARKS & TRACEABILITY (WP-01 & WP-07)

The 10 key structural claims were independently evaluated from first principles (see [`PHASE_1_5_3_2A_SYSTEM_A_CALCULATION_BENCHMARKS.csv`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2A_SYSTEM_A_CALCULATION_BENCHMARKS.csv)):

```
Input -> Equation -> Substitution -> Result -> Utilization -> Verdict
```

### 1. BM-01: Factored Net Wind Uplift Load ($w_{\text{net,up}}$)
- **Input:** $V_b = 39.0\text{ m/s}$, $k_2 = 1.028$, $C_{n,\text{up}} = -1.10$, $B_t = 3.0\text{ m}$, $w_{\text{DL}} = 0.9767\text{ kN/m}$.
- **Equation:**  
  $$V_z = V_b \cdot k_1 k_2 k_3 k_4 = 39.0 \times 1.028 = 40.092\text{ m/s}$$  
  $$p_z = 0.6 \times V_z^2 = 0.6 \times (40.092)^2 = 964.42\text{ Pa} = 0.9644\text{ kPa}$$  
  $$w_{\text{WL,up}} = |C_{n,\text{up}}| \cdot p_z \cdot B_t = 1.10 \times 0.9644 \times 3.0 = 3.1826\text{ kN/m}$$  
  $$w_{\text{net,up}} = 1.5 w_{\text{WL,up}} - 0.9 w_{\text{DL}} = 1.5(3.1826) - 0.9(0.9767) = \mathbf{3.8948\text{ kN/m}}$$
- **Verdict:** **VERIFIED** (Identical to production code: $3.8948\text{ kN/m}$).

---

### 2. BM-02A: Full-Span Factored Bending Moment Demand ($M_{u,\text{full}}$)
- **Input:** $w_{\text{net,up}} = 3.8948\text{ kN/m}$, $L = 9.112\text{ m}$.
- **Equation:**  
  $$M_{u,\text{full}} = \frac{w_{\text{net,up}} L^2}{8} = \frac{3.8948 \times (9.112)^2}{8} = \mathbf{40.42\text{ kN}\cdot\text{m}}$$
- **Verdict:** **VERIFIED** (Identical to production code: $40.42\text{ kNm}$).

---

### 3. BM-03A: Full-Span ISMB 300 Lateral-Torsional Buckling Capacity ($M_{d,\text{full}}$)
- **Input:** $L_b = 9,112\text{ mm}$, $I_y = 4.539 \times 10^6\text{ mm}^4$, $I_t = 168,810\text{ mm}^4$, $I_w = 9.387 \times 10^{10}\text{ mm}^6$, $Z_{px} = 651,000\text{ mm}^3$, $f_y = 250\text{ MPa}$, $\gamma_{m0} = 1.10$.
- **Equation:**  
  $$M_{cr} = \sqrt{\frac{\pi^2 E I_y}{L_b^2} \left(G I_t + \frac{\pi^2 E I_w}{L_b^2}\right)} = \mathbf{46.29\text{ kN}\cdot\text{m}}$$  
  $$\lambda_{LT} = \sqrt{\frac{Z_{px} f_y}{M_{cr}}} = \sqrt{\frac{651,000 \times 250}{46.29 \times 10^6}} = 1.875$$  
  $$\text{Curve a } (\alpha_{LT} = 0.21): \phi_{LT} = 2.434 \implies \chi_{LT} = 0.251$$  
  $$M_d = \frac{\chi_{LT} Z_{px} f_y}{\gamma_{m0}} = \frac{0.251 \times 651,000 \times 250}{1.10 \times 10^6} = \mathbf{37.12\text{ kN}\cdot\text{m}}$$  
  $$\mathbf{UR = \frac{40.42}{37.12} = 1.089 > 1.0 \implies \text{FAIL}}$$
- **Verdict:** **VERIFIED (Structural Failure Confirmed)**. Bottom-flange fly bracing is mandatory.

---

### 4. BM-03B & BM-02B: Clear-Span Capacity & Critical Demand Discrepancy
- **Clear-Span Capacity ($L_b = 4,556\text{ mm}$):**
  $$M_{cr} = 107.73\text{ kN}\cdot\text{m}, \quad \lambda_{LT} = 1.229, \quad \chi_{LT} = 0.512 \implies \mathbf{M_{d,\text{clear}} = 75.74\text{ kN}\cdot\text{m}}$$
- **Critical Discrepancy Investigation:**
  In [`system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py#L157):
  ```python
  Mu_half = (w_net_up * ((rafter_clear_span_mm / 1000.0) ** 2)) / 8.0  # 10.11 kNm
  ur_clear = Mu_full / Md_clear                                        # 40.42 / 75.74 = 0.534
  ```
  1. If the rafter has a nodal bottom-flange fly brace at midspan ($L = 9.112\text{ m}$ simply supported):  
     The maximum in-plane moment is $40.42\text{ kNm}$ at midspan. However, the moment diagram over the half-span ($0$ to $4.556\text{ m}$) is a moment gradient varying from $0$ at the end support to $M_{\max}$ at midspan. Per IS 800 Table 42 / Annex E, the moment gradient factor $C_1 \approx 1.75$. Applying uniform moment ($C_1 = 1.0$) severely underestimates $M_{cr}$ ($107.73\text{ kNm}$ vs actual $\sim 188\text{ kNm}$).
  2. If the rafter is supported on an intermediate column ($2$-span continuous beam):  
     The peak negative moment over the intermediate column is $10.11\text{ kNm}$, and the midspan sagging moment is $5.69\text{ kNm}$. In that case, comparing against $40.42\text{ kNm}$ is grossly erroneous ($4\times$ too high).
- **Verdict:** **PARTIALLY VERIFIED / MODEL DEFECT IDENTIFIED**. The implementation computes $M_{d,\text{clear}} = 75.74\text{ kNm}$ assuming uniform moment ($C_1 = 1.0$) and re-uses the full-span demand ($40.42\text{ kNm}$).

---

### 5. BM-04 & BM-05: Bottom-Flange Fly-Bracing Design (ISA 40×40×5)
- **Flange Compression Force ($N_c$):**  
  $$N_c = \frac{M_{u,\text{full}}}{h - t_f} = \frac{40.42\text{ kNm}}{0.2876\text{ m}} = \mathbf{140.54\text{ kN}}$$
- **Required Lateral Restraint Force (IS 800 Cl 8.9.1, 2.5%):**  
  $$P_{br} = 0.025 \times 140.54 = \mathbf{3.514\text{ kN}}$$
- **Diagonal Strut Axial Demand ($\theta = 45^\circ$):**  
  $$F_{\text{brace}} = \frac{3.514}{\cos 45^\circ} = \mathbf{4.969\text{ kN}}$$
- **ISA 40×40×5 Strut Compressive Resistance ($L = 600\text{ mm}$, $r_{\min} = 7.7\text{ mm}$):**  
  $$\lambda = \frac{600}{7.7} = 77.92 \le 180 \quad (\mathbf{PASS})$$  
  $$f_{cc} = 332.9\text{ MPa}, \quad \lambda_0 = 0.867, \quad \text{Curve c } (\alpha = 0.49) \implies \chi = 0.621$$  
  $$f_{cd} = \frac{0.621 \times 250}{1.10} = 141.1\text{ MPa} \implies P_d = \frac{379 \times 141.1}{1000} = \mathbf{53.48\text{ kN}}$$  
  $$\mathbf{UR = \frac{4.969}{53.48} = 0.093 \le 1.0 \quad (PASS)}$$
- **ISA 40×40×5 Tensile Resistance:**  
  $$T_d = \frac{379 \times 250}{1.10 \times 1000} = \mathbf{86.14\text{ kN}} \implies \mathbf{UR = \frac{4.969}{86.14} = 0.058 \le 1.0 \quad (PASS)}$$
- **Single M12 Grade 8.8 Bolt Shear Resistance:**  
  $$V_{dsb} = \frac{800}{\sqrt{3} \times 1.25} \times 84.3 \times 10^{-3} = \mathbf{31.15\text{ kN}} \implies \mathbf{UR = \frac{4.969}{31.15} = 0.160 \le 1.0 \quad (PASS)}$$
- **Verdict:** **VERIFIED (Member & Fastener Strength)**.

---

### 6. BM-08: Anchor Minimum Slab Thickness Reassessment
- **Manufacturer European Technical Assessment (ETA) Rule:**  
  $$h_{\min} = h_{ef} + 2 d_0 = 125 + 2(18) = \mathbf{161.0\text{ mm}}$$
- **Physical Installation Reality in 125 mm or 150 mm Slab:**  
  In a $150\text{ mm}$ slab with $25\text{ mm}$ bottom rebar cover, solid depth is $125\text{ mm}$. Drilling a $130\text{ mm}$ hole leaves negative clearance, breaching cover. In a $125\text{ mm}$ slab, drilling $130\text{ mm}$ blows through the ceiling soffit.
- **Verdict:** **VERIFIED (Physical Incompatibility Confirmed)**.

---

### 7. BM-09: Column Baseplate Fillet Weld Capacity
- **Weld Dimensions:** 6 mm fillet around ISMB 300 perimeter ($1,145\text{ mm}$), throat $a = 4.2\text{ mm}$.
- **Design Shear Strength:**  
  $$f_{vwd} = \frac{410}{\sqrt{3} \times 1.25} = 189.37\text{ MPa}$$  
  $$P_{wd} = 1,145 \times 4.2 \times 189.37 \times 10^{-3} = \mathbf{910.68\text{ kN}}$$  
  $$\text{Pure Axial Demand } P_u = 33.84\text{ kN} \implies \mathbf{UR = 0.037 \le 1.0}$$
- **Verdict:** **PARTIALLY VERIFIED**. Calculation is accurate for pure axial force, but incomplete because co-existing base shear ($3.50\text{ kN}$) and moment ($4.90\text{ kNm}$) were omitted.

---

### 8. BM-10: Host RCC Slab Two-Way Punching Shear Capacity
- **Critical Perimeter:** Baseplate $350 \times 250\text{ mm}$, effective depth $d = 100\text{ mm}$.  
  $$b_0 = 2(350 + 100) + 2(250 + 100) = \mathbf{1,600\text{ mm}}$$  
  $$\tau_c = 0.25 \sqrt{20.0} = 1.118\text{ MPa}$$  
  $$V_{up} = 1.118 \times 1,600 \times 100 \times 10^{-3} = \mathbf{178.89\text{ kN}}$$  
  $$\text{Pure Downward Demand } P_u = 33.84\text{ kN} \implies \mathbf{UR = 0.189 \le 1.0}$$
- **Verdict:** **PARTIALLY VERIFIED**. Calculation is accurate for downward axial push, but omits upward tension breakout and unbalanced moment transfer.

---

## 7. TEST ISOLATION & PRODUCTION SAFETY AUDIT (WP-06)

A detailed inspection of [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) was conducted:

```
Test Suite Inspection Trace:
Line 27: from tests.test_isolation_helper import IsolatedTestEnvironment, PROD_STRUCTURAL_DB...
Line 57: class TestPhase1532SystemAFinal(unittest.TestCase):
Line 68:     @classmethod
Line 69:     def setUpClass(cls): -> Computes SHA-256 hashes of production files.
             [DEFECT]: IsolatedTestEnvironment is NOT instantiated here or in setUp()!
Line 225:    def test_10_historical_records_immutability(self):
Line 226:        conn = sqlite3.connect(PROD_STRUCTURAL_DB)  <-- DIRECT PRODUCTION DB CONNECTION
Line 260:    def test_12_afc_lock_and_statutory_watermark(self):
Line 261:        conn = sqlite3.connect(PROD_STRUCTURAL_DB)  <-- DIRECT PRODUCTION DB CONNECTION
Line 270:    def tearDownClass(cls): -> Asserts production hashes remain unchanged.
```

### Safety Evaluation:
1. **Did the test mutate production data?**  
   **NO.** Pre- and post-test SHA-256 hashes were bit-for-bit identical (`ff234f...` for `structural_runs.db`). Only read-only `SELECT` queries were executed.
2. **Did the test use an isolated test environment?**  
   **NO.** The suite violated the project architectural guideline by connecting directly to the live production database instead of launching `IsolatedTestEnvironment()`.

---

## 8. TEST QUALITY CLASSIFICATION MATRIX (WP-08)

All 12 tests in [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) were audited and classified (see [`PHASE_1_5_3_2A_SYSTEM_A_TEST_QUALITY_MATRIX.csv`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2A_SYSTEM_A_TEST_QUALITY_MATRIX.csv)):

| Test ID | Test Method | Test Category | Independent Benchmark? | Primary Limitation |
|:---|:---|:---:|:---:|:---|
| **TEST-01** | `test_01_wind_uplift_factored_moment_demand` | Category E: Regression / Fixed Output | No | Asserts hardcoded output constants ($3.8948$, $40.42$) |
| **TEST-02** | `test_02_rafter_ltb_unbraced_failure_vs_clear_span`| Category E: Regression / Fixed Output | No | Compares clear-span capacity against full-span demand |
| **TEST-03** | `test_03_fly_bracing_required_stabilizing_force` | Category B: Formula / Unit Consistency | No | Repeats 2.5% formula; does not verify brace stiffness |
| **TEST-04** | `test_04_isa_40x40x5_strut_buckling_capacity` | Category E: Regression / Fixed Output | No | Validates axial force only; omits connection eccentricity |
| **TEST-05** | `test_05_fly_bracing_connection_and_purlin_cleat` | Category C: Input Validation & Detailing Flag| No | Checks boolean flag; does not calculate cleat bending |
| **TEST-06** | `test_06_chemical_anchor_standards_hierarchy` | Category D: Governance / Standard Mapping | No | Tests dictionary metadata string tags |
| **TEST-07** | `test_07_project_specific_anchor_testing_protocol` | Category E: Regression / Protocol Verification| No | Tests engineer-selected protocol values ($27.75\text{ kN}$) |
| **TEST-08** | `test_08_slab_thickness_evaluation_and_alternatives`| Category C: Feasibility & Boundary Check | No | Checks heuristic geometry; does not verify alternative capacities |
| **TEST-09** | `test_09_complete_foundation_load_path_verification` | Category H: Integration / Load Path Chain | No | Checks axial weld/punching capacities; omits moments |
| **TEST-10** | `test_10_historical_records_immutability` | Category F: Production Data Integrity | No | Directly queries `PROD_STRUCTURAL_DB` without isolation |
| **TEST-11** | `test_11_original_holds_active_and_enforced` | Category D: Governance / Hold Enforcement | No | In-memory registry query |
| **TEST-12** | `test_12_afc_lock_and_statutory_watermark` | Category D: Governance / Statutory Lock | No | Directly queries `PROD_STRUCTURAL_DB` without isolation |

---

## 9. WELD AND FOUNDATION LOAD-PATH DEFECT AUDIT (WP-05)

### 1. Fillet Weld Combined Stress Evaluation:
Under ULS load combinations, the column-to-baseplate weld is subjected to simultaneous actions:
- Factored axial load: $P_u = 33.84\text{ kN}$
- Factored shear: $V_u = 3.50\text{ kN}$
- Factored bending moment: $M_z = 4.90\text{ kN}\cdot\text{m}$

```
Combined Weld Stress Check (IS 800 Cl 10.5.10):
- Direct shear from axial force: fa = Pu / Aw = 33,840 / 4,809 = 7.04 MPa
- Direct shear from lateral force: q = Vu / Aw = 3,500 / 4,809 = 0.73 MPa
- Bending shear stress at extreme flange: fb = Mz / Zw = 4.90e6 / 200,000 = 24.50 MPa
- Peak equivalent resultant stress:
  fe = sqrt((fa + fb)^2 + 3*q^2) = sqrt((7.04 + 24.50)^2 + 3*(0.73)^2) = 31.57 MPa
- Capacity: fvwd = 189.37 MPa
- Combined Utilization Ratio: UR = 31.57 / 189.37 = 0.167 <= 1.0 (PASS)
```
**Defect:** The production code in [`system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py#L562-L572) checks only $f_a$ ($UR = 0.037$), omitting $f_b$ and $q$. While the weld has ample structural reserve ($UR = 0.167$), the check is mathematically incomplete.

---

### 2. RCC Slab Punching Shear & Unbalanced Moment:
- The production check calculates downward punching under $P_u = 33.84\text{ kN}$ ($\tau_v = 0.21\text{ MPa} \ll 1.118\text{ MPa}$).
- Under wind uplift, $T_u = 18.50\text{ kN}$ acts as an upward pull. The failure mode shifts to concrete cone breakout and slab flexural tension.
- Unbalanced moment $M_z = 4.90\text{ kNm}$ must be transferred by a combination of flexure and eccentric shear per IS 456 Clause 31.6.2.2.

---

## 10. CHEMICAL ANCHOR & TESTING PROTOCOL CLASSIFICATION (WP-03)

| Criterion | Value in Protocol | Formal Technical Classification | Authority / Status |
|:---|:---:|:---|:---|
| **Proof Test Load** | $27.75\text{ kN}$ / group ($6.94\text{ kN}$ / bolt) | **Engineer-Selected Project Criterion** | Derived from BS 8539 Cl 9.3 ($1.5 \times N_{Ed}$); not a statutory codal constant |
| **Proof Load Factor** | $1.50\times$ Factored Action | **Standard Recommendation (Upper Bound)**| BS 8539 Table 3 recommends $1.25$ to $1.50\times$ |
| **Sampling Frequency**| $25\%$ of columns (min 3) | **Engineer-Selected Conservative Policy**| BS 8539 recommends minimum 3 anchors; 25% is project-specific |
| **Hold Duration** | 2 minutes at peak load | **Standard Procedure** | BS 8539 Cl 9.3 / ASTM E488 |
| **Residual Slip Limit**| $\le 0.20\text{ mm}$ permanent displacement | **Engineer-Selected Performance Tolerance** | General structural tolerance; not a universal threshold across all resins |
| **RSE Witnessing** | Mandatory sign-off | **Statutory Indian Legal Requirement** | TNCDBR-2019 Rule 35 / NBC 2016 Part 2 |

---

## 11. CANONICAL HOLD & AFC STATUS (WP-09)

All 12 canonical engineering holds were verified in [`structural/holds.py`](file:///Users/karthik/tneb-account-extractor/structural/holds.py):

| Hold ID | Description | Status | Applicability to System A |
|:---|:---|:---:|:---:|
| `HOLD-01` | `INSPECTION_REQUIRED_HOLD` (Slab NDT & Thickness) | **ACTIVE** | **APPLICABLE (GOVERNING)** |
| `HOLD-02` | `AERODYNAMIC_UNSUPPORTED_HOLD` | **ACTIVE** | Not applicable to canopy |
| `HOLD-03` | `WIND_COORD_UNVERIFIED_HOLD` (Rooftop Survey) | **ACTIVE** | **APPLICABLE** |
| `HOLD-04` | `WIND_TRANSFORM_UNVERIFIED_HOLD` | **ACTIVE** | **APPLICABLE** |
| `HOLD-05` | `VERTICAL_SEISMIC_APPLICABILITY_HOLD` | **ACTIVE** | **APPLICABLE** |
| `HOLD-06` | `LOAD_COMBINATION_PROVISIONAL_HOLD` | **ACTIVE** | **APPLICABLE** |
| `HOLD-07` | `FRICTION_UNVERIFIED_HOLD` / Fastener Proof Testing | **ACTIVE** | **APPLICABLE (GOVERNING)** |
| `HOLD-08` | `ALUMINIUM_DERIVATION_HOLD` | **ACTIVE** | Not applicable to steel |
| `HOLD-09` | `FASTENER_TORQUE_UNVERIFIED_HOLD` | **ACTIVE** | **APPLICABLE** |
| `HOLD-10` | `NUMERICAL_INSTABILITY_HOLD` | **ACTIVE** | **APPLICABLE** |
| `HOLD-11` | `ASSUMED_DATA_CERTIFICATION_HOLD` | **ACTIVE** | **APPLICABLE** |
| `HOLD-12` | `DRAWING_UNVERIFIED_HOLD` | **ACTIVE** | **APPLICABLE** |

- **Construction Authorization:** `is_approved_for_construction = false`
- **AFC Status:** `BLOCKED_AFC_LOCKED`
- **Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`

---

## 12. COMPREHENSIVE DEFECT REGISTER & REQUIRED CORRECTIONS

```
+----------------------------------------------------------------------------------------------------+
|                                    AUDIT DEFECT REGISTER                                           |
+--------+--------------------------+-----------------------+----------------------------------------+
| Defect | File & Location          | Defect Description   | Required Engineering Correction        |
+--------+--------------------------+-----------------------+----------------------------------------+
| DEF-01 | system_a_final.py: L157  | Clear-span LTB uses   | Calculate effective moment gradient    |
|        |                          | full-span moment      | factor C1 (IS 800 Table 42) for nodal  |
|        |                          | demand (40.42 kNm)    | midspan brace, or evaluate 2-span frame|
+--------+--------------------------+-----------------------+----------------------------------------+
| DEF-02 | system_a_final.py: L260  | Fly-bracing stiffness | Add IS 800 Cl 8.9.2 restraint stiffness|
|        |                          | and eccentricity not  | check K_req = 4*Nc/Lb vs K_brace, and  |
|        |                          | checked in code       | verify angle single-leg eccentricity   |
+--------+--------------------------+-----------------------+----------------------------------------+
| DEF-03 | system_a_final.py: L565  | Fillet weld check     | Implement IS 800 Cl 10.5.10 combined   |
|        |                          | omits base moment     | stress check: fe = sqrt((fa+fb)^2+3q^2)|
|        |                          | and shear (axial only)| to verify flange tip stress state      |
+--------+--------------------------+-----------------------+----------------------------------------+
| DEF-04 | system_a_final.py: L575  | Punching shear check  | Add upward tension pull-out check and  |
|        |                          | omits uplift tension  | unbalanced moment transfer check per   |
|        |                          | and unbalanced moment | IS 456 Cl 31.6.2.2                     |
+--------+--------------------------+-----------------------+----------------------------------------+
| DEF-05 | test_phase1_5_3_2_final  | IsolatedTestEnv not   | Instantiate IsolatedTestEnvironment in |
|        | Lines 226, 260           | used; queries live    | setUpClass and run queries against     |
|        |                          | PROD_STRUCTURAL_DB    | hermetic temporary SQLite database     |
+--------+--------------------------+-----------------------+----------------------------------------+
| DEF-06 | test_phase1_5_3_2_final  | Tests assert hardcoded| Implement independent formula solvers  |
|        | Tests 01 - 09            | return constants      | inside test fixtures to verify results |
+--------+--------------------------+-----------------------+----------------------------------------+
```

---

## 13. OUTSTANDING PHYSICAL EVIDENCE & SITE ACTION PLAN

Before any active hold on System A can be released, the following site evidence is mandatory:
1. **Host Roof Slab NDT Survey (`HOLD-01`):**  
   Ultrasonic Pulse Velocity (UPV per IS 13311 Part 1) and core extraction to verify $f_{ck} \ge 20.0\text{ MPa}$ and slab thickness $h_{\text{slab}}$.
2. **Rebar Covermeter & GPR Scan (`HOLD-01`):**  
   Non-destructive magnetic/radar mapping of existing reinforcement grid to prevent rebar severing during anchor hole drilling.
3. **On-Site Proof Load Testing (`HOLD-07`):**  
   $27.75\text{ kN}$ hydraulic tension proof load testing on minimum 3 canopy columns, witnessed and certified by a Grade-I RSE.
4. **Fastener Manufacturer Technical Submittal (`HOLD-08`):**  
   Certified European Technical Assessment (ETA) covering performance of selected epoxy/hybrid resin in cracked concrete.
5. **Detailed Fly-Bracing Workshop Drawing (`HOLD-12`):**  
   Connection detailing confirming diagonal strut attachment to minimum 5 mm purlin cleats (strictly prohibiting direct connection to thin purlin webs).

---

## 14. FINAL AUDIT DECISION & GOVERNANCE STATUS

```
====================================================================================================
FINAL AUDIT DECISION:
Phase 1.5.3.2 System A demonstrates solid baseline mathematical reproducibility and successfully
proves the necessity of bottom-flange fly bracing and the physical impossibility of 125 mm anchors
in 125-150 mm slabs.

However, the calculation model contains five specific engineering and testing defects (DEF-01 to DEF-05):
- Incomplete moment gradient handling in rafter clear-span LTB (DEF-01).
- Unchecked bracing restraint stiffness and connection eccentricity (DEF-02).
- Axial-only weld and punching shear calculations omitting co-existing moments (DEF-03, DEF-04).
- Direct production database access in the test suite without test isolation (DEF-05).

All 12 canonical engineering holds remain active and enforced.
====================================================================================================
```

**FINAL STATUTORY STATUS:**

`ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE`

`CONSTRUCTION STATUS: BLOCKED_AFC_LOCKED`

`PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`

---
*End of Phase 1.5.3.2A Independent Audit Report.*
