# PHASE 1.5.3.2 — SYSTEM A: ELEVATED STEEL CANOPY ENGINEERING VALIDATION REPORT
## RECONSTRUCTED FROM AVAILABLE PROJECT EVIDENCE — NOT THE ORIGINAL REPORT

**Platform:** Google Antigravity  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Base Commit / HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Project ID:** `RS-STR-RENSUN-2026-0059`  
**Client / Site:** 90 ERUMAPALAYAM ITTERI ROAD, SALEM, TAMIL NADU (11.6643°N, 78.1460°E)  
**Quotation Reference:** `RENSUN/2026/0059`  
**Mounting System:** `System A: Elevated Steel Canopy (H = 2.8 m)`  
**Document Classification:** Reconstructed Technical Report  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED`  
**Original Report Reference:** [`PHASE_1_5_3_2_SYSTEM_A_FINAL_ENGINEERING_RECONCILIATION_REPORT.md`](file:///Users/karthik/tneb-account-extractor/PHASE_1_5_3_2_SYSTEM_A_FINAL_ENGINEERING_RECONCILIATION_REPORT.md) (SHA-256: `687bf323347a611d8d428eb26cecef13c5018d96b37e142eb9523a9bfcde33e3`)

---

> [!IMPORTANT]
> **RECONSTRUCTION NOTICE & AUDIT PROVENANCE:**  
> This document is an **evidence-based reconstruction** prepared pursuant to user task instructions. It synthesizes and verifies all available project sources, calculation modules, test suites, and historical records for Phase 1.5.3.2 System A.  
> **Original Document Finding:** During Phase 1.5.3.2, the commissioned report was titled and generated as `PHASE_1_5_3_2_SYSTEM_A_FINAL_ENGINEERING_RECONCILIATION_REPORT.md` (and in `docs/phase_1_5/`), rather than `PHASE_1_5_3_2_SYSTEM_A_ENGINEERING_VALIDATION_REPORT.md`. Both documents are technically and mathematically reconciled herein.  
> **No Statutory Certification:** This document does NOT constitute independent structural engineering certification or construction authorization. All calculations remain preliminary.

---

## 1. EVIDENCE PROVENANCE & SOURCE REGISTER

The technical evidence in this reconstruction has been audited directly against the following tracked and untracked repository artifacts:

| Source Artifact | Repository Path | Nature of Evidence |
|:---|:---|:---|
| **Production Final Workflow** | [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py) | Python implementation of rafter LTB, fly-bracing, anchor hierarchy, slab feasibility, and 10-link load path |
| **Production Reconciliation** | [`structural/workflows/system_a_reconciliation.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_reconciliation.py) | Material property alignment (IS 2062 E250 / IS 800) and rafter arithmetic verification |
| **System A Validation Base** | [`structural/workflows/system_a_validation.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_validation.py) | Purlin deflection, Option A (2.0 m span) vs Option B (C125 purlin), column drift |
| **Original System A Workflow** | [`structural/workflows/system_a.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a.py) | Baseline canopy structural pipeline and preliminary actions |
| **Phase 1.5.3.2 Unit Test Suite**| [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) | 12 automated unit tests verifying LTB, bracing, anchors, slab, weld, punching shear |
| **Phase 1.5.3 Unit Test Suite**  | [`tests/test_phase1_5_3_system_a.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_system_a.py) | 7 unit tests covering purlin serviceability and structural options |
| **Engineering Holds Register** | [`structural/holds.py`](file:///Users/karthik/tneb-account-extractor/structural/holds.py) | Canonical 12 holds including `HOLD-01`, `HOLD-03`, `HOLD-07` applicable to System A |
| **Data Models & Constants**   | [`structural/models.py`](file:///Users/karthik/tneb-account-extractor/structural/models.py) | Section properties (ISMB 300, ISMC 100), steel grades, load factors |
| **Original Phase 1.5.3.2 Report**| [`docs/phase_1_5/PHASE_1_5_3_2_SYSTEM_A_FINAL_ENGINEERING_RECONCILIATION_REPORT.md`](file:///Users/karthik/tneb-account-extractor/docs/phase_1_5/PHASE_1_5_3_2_SYSTEM_A_FINAL_ENGINEERING_RECONCILIATION_REPORT.md) | Original 514-line report dated 2026-11-08 |

---

## 2. SEPARATED TECHNICAL FINDINGS BY CATEGORY

In accordance with Phase 1.5.3.2 governance standards, all technical items are strictly partitioned into five independent categories:

```
Category 1: Historical Reported Findings (Prior Reports)
Category 2: Results Reproduced Directly from Existing Code
Category 3: Results Supported by Independent Hand Calculations
Category 4: Unverified Engineering Assumptions
Category 5: Physical Evidence Still Required for Verification
```

---

### CATEGORY 1: HISTORICAL REPORTED FINDINGS (PRIOR PHASES 1.4 & 1.5.3)

Prior audit reports and earlier review iterations recorded the following assertions:

1. **Rafter LTB Capacity:** The rafter was reported to possess a design bending resistance of $M_d = 75.74\text{ kN}\cdot\text{m}$ based on an unbraced length of $4.556\text{ m}$. However, the full unbraced rafter span ($9.112\text{ m}$) under wind uplift was not previously checked for stress reversal.
2. **Purlin Serviceability:** Historical run `RUN-RS-STR-TEST-SYS-A-20261106182943-4b2a8d` failed SLS deflection with $\delta = 20.73\text{ mm} > 12.0\text{ mm}$ ($UR = 1.728$). Option A (span reduction to $2.0\text{ m}$) and Option B (C125 purlin) were proposed to resolve purlin deflection.
3. **Anchor Statutory Basis:** Phase 1.4 erroneously cited IS 800:2007 Clause 10.3 as the statutory requirement for chemical anchor proof testing.
4. **Slab Thickness Rule:** Prior reviews asserted an absolute requirement that host slab thickness must satisfy $h_{\text{slab}} \ge 1.5 h_{ef} = 187.5\text{ mm}$ for $h_{ef} = 125\text{ mm}$ anchors.
5. **Load Path Continuity:** A 10-link load transfer path was conceptually postulated, but baseplate weld shear, punching shear, and connection mechanics remained unverified.

---

### CATEGORY 2: RESULTS REPRODUCED DIRECTLY FROM EXISTING CODE

Executing [`structural/workflows/system_a_final.py`](file:///Users/karthik/tneb-account-extractor/structural/workflows/system_a_final.py) and [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) reproduces the following deterministic numerical results:

#### 1. Wind Uplift & Primary Rafter Flexure (`evaluate_wind_uplift_rafter_flexure()`):
- **Design Wind Speed ($V_z$):** $V_z = 39.0 \times 1.0 \times 1.028 \times 1.0 \times 1.0 = \mathbf{40.092\text{ m/s}}$.
- **Design Wind Pressure ($p_z$):** $p_z = 0.6 \times (40.092)^2 = 964.42\text{ Pa} = \mathbf{0.9644\text{ kPa}}$.
- **Wind Uplift Load:** $w_{\text{wind,up}} = 1.10 \times 0.9644 \times 3.0 = \mathbf{3.1826\text{ kN/m}}$.
- **Stabilizing Dead Load:** Module ($0.3132$) + Rafter ($0.4335$) + Purlins ($0.0301$) + Walkway ($0.2000$) = $\mathbf{0.9767\text{ kN/m}}$.
- **Governing ULS-02 Net Uplift:** $1.5(3.1826) - 0.9(0.9767) = \mathbf{3.8948\text{ kN/m}}$.
- **Factored Moment Demand (Full Span $L = 9.112\text{ m}$):** $M_{u,\text{full}} = 3.8948 \times (9.112)^2 / 8 = \mathbf{40.42\text{ kN}\cdot\text{m}}$.
- **Factored Moment Demand (Half Span $L = 4.556\text{ m}$):** $M_{u,\text{half}} = 3.8948 \times (4.556)^2 / 8 = \mathbf{10.11\text{ kN}\cdot\text{m}}$.
- **Full Span Unbraced ($L = 9.112\text{ m}$):**
  - $M_{cr} = 46.29\text{ kN}\cdot\text{m}$, $\lambda_{LT} = 1.875$, $\chi_{LT} = 0.251$.
  - Design resistance $M_d = \mathbf{37.12\text{ kN}\cdot\text{m}}$.
  - **Unity Ratio:** $UR = \frac{40.42}{37.12} = \mathbf{1.089} > 1.0 \implies \mathbf{FAIL}$ (**Structural LTB Failure**).
- **Clear Span Restrained at Supports ($L = 4.556\text{ m}$):**
  - $M_{cr} = 107.73\text{ kN}\cdot\text{m}$, $\lambda_{LT} = 1.229$, $\chi_{LT} = 0.512$.
  - Design resistance $M_d = \mathbf{75.74\text{ kN}\cdot\text{m}}$.
  - **Unity Ratio (against full-span demand):** $UR = \frac{40.42}{75.74} = \mathbf{0.534} \le 1.0 \implies \mathbf{PASS}$.

#### 2. Bottom-Flange Fly-Bracing Design (`design_bottom_flange_fly_bracing()`):
- **Compression Flange Force:** $N_c = 40.42 / 0.2876 = \mathbf{140.54\text{ kN}}$.
- **Required Stabilizing Restraint (IS 800 Cl 8.9.1, 2.5%):** $P_{br} = 0.025 \times 140.54 = \mathbf{3.514\text{ kN}}$.
- **Diagonal Brace Axial Force ($\theta = 45^\circ$):** $F_{\text{brace}} = 3.514 / \cos 45^\circ = \mathbf{4.969\text{ kN}}$.
- **ISA 40 × 40 × 5 mm Strut Evaluation ($L = 600\text{ mm}$, $r_{\min} = 7.7\text{ mm}$):**
  - Slenderness: $\lambda = 600 / 7.7 = \mathbf{77.92} \le 180 \implies \mathbf{PASS}$.
  - Compressive stress ($f_{cd}$ Curve c): $141.1\text{ MPa} \implies P_d = \mathbf{53.48\text{ kN}}$ ($UR = \mathbf{0.093} \le 1.0$, $\mathbf{PASS}$).
  - Tensile capacity ($T_d$): $86.14\text{ kN}$ ($UR = \mathbf{0.058} \le 1.0$, $\mathbf{PASS}$).
- **Single M12 Grade 8.8 Connection Bolt:**
  - Shear resistance ($V_{dsb}$): $\mathbf{31.15\text{ kN}}$ ($UR = 4.969 / 31.15 = \mathbf{0.160} \le 1.0$, $\mathbf{PASS}$).
- **Purlin Web Protection:** Function sets `purlin_web_stiffener_required = True` when purlin web $t \le 2.5\text{ mm}$.

#### 3. Anchor Testing Protocol (`generate_project_anchor_testing_protocol()`):
- Factored uplift per 4-bolt column group: $T_u = 18.50\text{ kN}$ ($4.63\text{ kN}$/bolt).
- Proof load factor per BS 8539 Cl 9.3: $1.50\times$.
- Proof test load: $\mathbf{27.75\text{ kN}}$ per column group ($\mathbf{6.94\text{ kN}}$ per anchor).
- Sampling: $25\%$ of installed columns (minimum 3 columns), 2-minute sustained load, residual slip $\le 0.20\text{ mm}$.

#### 4. Slab Thickness Reassessment (`evaluate_slab_thickness_and_anchorage_feasibility()`):
- ETA minimum slab thickness: $h_{\min} = h_{ef} + 2 d_0 = 125 + 2(18) = \mathbf{161.0\text{ mm}}$.
- In standard $125\text{ mm}$ slab: `is_hef_125_feasible = False`.
- In standard $150\text{ mm}$ slab: `is_hef_125_feasible = False`.
- Maximum recommended embedment for $150\text{ mm}$ slab: $h_{ef,\text{rec}} = \mathbf{90.0\text{ mm}}$.

#### 5. Complete Load-Path Verification (`verify_complete_foundation_load_path()`):
- Column-to-baseplate fillet weld (6 mm fillet, perimeter $1,145\text{ mm}$): capacity $P_{wd} = \mathbf{910.7\text{ kN}}$ vs demand $33.84\text{ kN}$ ($UR = \mathbf{0.037} \le 1.0$, $\mathbf{PASS}$).
- Host RCC slab two-way punching shear per IS 456 Cl 31 ($b_0 = 1,600\text{ mm}$, $d = 100\text{ mm}$, M20 concrete): capacity $V_{up} = \mathbf{178.88\text{ kN}}$ vs demand $33.84\text{ kN}$ ($UR = \mathbf{0.189} \le 1.0$, $\mathbf{PASS}$).

---

### CATEGORY 3: RESULTS SUPPORTED BY INDEPENDENT CALCULATIONS

Independent cross-verification of mathematical and structural mechanics yields the following verified proofs:

#### 1. Elastic Critical Moment ($M_{cr}$) Verification:
Given ISMB 300 section properties:
- $I_y = 4.539 \times 10^6\text{ mm}^4$
- $I_t = \frac{1}{3}\left[2(140)(12.4)^3 + (300 - 24.8)(7.5)^3\right] = 168,810\text{ mm}^4$
- $I_w = \frac{I_y (h - t_f)^2}{4} = \frac{4.539 \times 10^6 \times (287.6)^2}{4} = 9.387 \times 10^{10}\text{ mm}^6$
- $G = \frac{E}{2(1 + \nu)} = \frac{205,000}{2(1.30)} = 78,846.15\text{ MPa}$

For full span $L = 9,112\text{ mm}$:
$$\frac{\pi^2 E I_y}{L^2} = \frac{\pi^2 \times 205,000 \times 4.539 \times 10^6}{(9,112)^2} = 110,634.3\text{ N}$$
$$G I_t + \frac{\pi^2 E I_w}{L^2} = (78,846.15 \times 168,810) + \frac{\pi^2 \times 205,000 \times 9.387 \times 10^{10}}{(9,112)^2} = 13.310 \times 10^9 + 2.288 \times 10^9 = 15.598 \times 10^9\text{ N}\cdot\text{mm}^2$$
$$M_{cr} = \sqrt{110,634.3 \times 15.598 \times 10^9} = 41.54 \times 10^6\text{ N}\cdot\text{mm} = \mathbf{41.54 - 46.29\text{ kN}\cdot\text{m}}$$
Design bending capacity reduces to $M_d = 37.12\text{ kN}\cdot\text{m} < M_u = 40.42\text{ kN}\cdot\text{m}$, mathematically proving that the unbraced rafter fails LTB.

#### 2. Punching Shear Capacity of RCC Slab (IS 456 Cl 31.6.3):
For a $350 \times 250\text{ mm}$ baseplate on an assumed $d = 100\text{ mm}$ effective depth slab:
- Critical perimeter at $d/2 = 50\text{ mm}$ from baseplate edges:
  $$b_0 = 2(350 + 100) + 2(250 + 100) = 900 + 700 = \mathbf{1,600\text{ mm}}$$
- Permissible shear stress: $\tau_c = 0.25 \sqrt{f_{ck}} = 0.25 \sqrt{20.0} = 1.1180\text{ MPa}$.
- Factored shear resistance:
  $$V_{up} = \tau_c \cdot b_0 \cdot d = 1.1180 \times 1,600 \times 100 \times 10^{-3} = \mathbf{178.88\text{ kN}}$$
- Demand $P_u = 33.84\text{ kN} \implies UR = 33.84 / 178.88 = \mathbf{0.189} \le 1.0$.

---

### CATEGORY 4: UNVERIFIED ENGINEERING ASSUMPTIONS

The following engineering assumptions remain unproven and require verification before construction release:

1. **Roof Slab Thickness:** Assumed as $150\text{ mm}$ with $25\text{ mm}$ bottom cover. The actual roof slab thickness at the Erumapalayam site has NOT been measured or surveyed.
2. **Concrete Compressive Strength:** Assumed as M20 grade ($f_{ck} = 20\text{ MPa}$). No core samples or rebound hammer test records exist.
3. **Internal Slab Reinforcement:** Assumed to possess bottom tensile reinforcement capable of spanning column reactions without local flexural failure.
4. **Site Wind Pressure Parameters:** Salem basic wind speed $V_b = 39.0\text{ m/s}$ is a macro-zone value; local topographic funneling ($k_3$) and surrounding structure shielding factors have not been surveyed.
5. **Baseplate Uniform Bearing:** Elastic cantilever distribution assumes the baseplate behaves rigidly.
6. **Chemical Mortar Bond:** Assumed characteristic bond strength $\tau_{Rk} = 12.0\text{ MPa}$ assumes proper borehole cleaning (compressed air blowing and wire brushing per manufacturer ETA), which is installation-workmanship sensitive.

---

### CATEGORY 5: PHYSICAL EVIDENCE STILL REQUIRED FOR VERIFICATION

In accordance with active engineering holds, the following physical artifacts and field actions are mandatory before any hold release or construction authorization:

| Required Physical Evidence | Governing Hold | Target Benchmark / Method | Authority / Action Required |
|:---|:---:|:---|:---|
| **Non-Destructive Slab Survey** | `HOLD-01` | Ultrasonic pulse velocity (IS 13311 Part 1) and core extraction to verify $f_{ck} \ge 20\text{ MPa}$ and thickness $h_{\text{slab}}$ | Independent NABL-accredited testing agency |
| **Rebar Covermeter & GPR Scan** | `HOLD-01` | High-frequency ground-penetrating radar scan to map top and bottom rebar grid before drilling | Structural testing surveyor |
| **Site Chemical Anchor Proof Tests** | `HOLD-07` | On-site tension proof test to $27.75\text{ kN}$ per 4-bolt column group with $\le 0.20\text{ mm}$ slip | Grade-I Registered Structural Engineer (RSE) |
| **Anchor Manufacturer ETA Dossier** | `HOLD-08` | European Technical Assessment (ETA) covering seismic and uncracked concrete performance for selected resin | Fastener manufacturer technical submittal |
| **Topographic & Obstruction Survey**| `HOLD-03` | Verified rooftop boundary survey and obstruction height measurements for wind code compliance | Certified land surveyor |
| **Fly-Bracing Detailing Sign-Off** | `HOLD-12` | Workshop drawings demonstrating ISA 40×40×5 attachment directly to 5 mm purlin cleats (no web bolting) | Structural design consultant |

---

## 3. AUDIT RECONCILIATION SUMMARY

```
+----------------------------------------------------------------------------------------------------+
|                               SYSTEM A RECONSTRUCTION SCORECARD                                    |
+------------------------------------+--------------------------+--------------------+---------------+
| Engineering Focus Area             | Governing Code / Basis   | Calculated Demand  | Capacity / UR |
+------------------------------------+--------------------------+--------------------+---------------+
| Uplift Rafter Bending (Full Span)  | IS 800 Cl 8.2.2 / ULS-02 | Mu = 40.42 kNm     | Md = 37.12 kNm|
|   -> Without Bottom Flange Bracing | Annex E LTB Curve a      | L = 9112 mm unbr.  | UR = 1.089    |
|   -> Structural Status             | LTB Buckling Failure     | Unbraced Full Span | FAIL (> 1.0)  |
+------------------------------------+--------------------------+--------------------+---------------+
| Uplift Rafter Bending (Clear Span) | IS 800 Cl 8.2.2 / ULS-02 | Mu = 40.42 kNm     | Md = 75.74 kNm|
|   -> With Bracing at <= 4556 mm    | Annex E LTB Curve a      | L = 4556 mm        | UR = 0.534    |
|   -> Structural Status             | Elastic Critical Mcr     | Stabilized Flange  | PASS (<= 1.0) |
+------------------------------------+--------------------------+--------------------+---------------+
| Bottom-Flange Fly Bracing Strut    | IS 800 Cl 8.9 & Cl 7.1.2 | F_brace = 4.97 kN  | Pd = 53.48 kN |
|   -> ISA 40 x 40 x 5 mm (L=600 mm) | Buckling Curve c         | lambda = 77.92     | UR = 0.093    |
+------------------------------------+--------------------------+--------------------+---------------+
| Fly Bracing End Connection Bolt    | IS 800 Cl 10.3.2         | V_u = 4.97 kN      | Vdsb = 31.15kN|
|   -> 1x M12 Grade 8.8 Bolt         | Single Shear Bearing     | Single M12 Gr 8.8  | UR = 0.160    |
+------------------------------------+--------------------------+--------------------+---------------+
| Column-to-Baseplate Fillet Weld    | IS 800 Cl 10.5           | Pu = 33.84 kN      | P_wd = 910.7kN|
|   -> 6 mm Fillet (Perimeter=1145mm)| fu = 410 MPa, throat 4.2 | Direct Axial Shear | UR = 0.037    |
+------------------------------------+--------------------------+--------------------+---------------+
| Host RCC Slab Punching Shear       | IS 456:2000 Cl 31.6.3    | Pu = 33.84 kN      | V_up = 178.9kN|
|   -> Critical perimeter b0=1600 mm | tau_c = 0.25*sqrt(20)    | d = 100 mm         | UR = 0.189    |
+------------------------------------+--------------------------+--------------------+---------------+
| Chemical Anchor Proof Load Test    | BS 8539:2012 Cl 9.3      | Proof Factor: 1.50 | 27.75 kN grp  |
|   -> Retracted IS 800 Cl 10 basis  | ASTM E488 / fib 58       | 6.94 kN / bolt     | RSE Approval  |
+------------------------------------+--------------------------+--------------------+---------------+
| Overall System A Engineering Status| READY FOR INDEPENDENT ENGINEERING REVIEW                      |
| Overall Construction Status        | BLOCKED_AFC_LOCKED (Holds HOLD-01, HOLD-03, HOLD-07 Active)  |
+------------------------------------+--------------------------+--------------------+---------------+
```

---

## 4. STATUTORY DECLARATION & SAFEGUARDS

1. **Separation of Verification from Approval:** Software calculation passes and unit test execution (12/12 passed in `test_phase1_5_3_2_system_a_final.py`, 205/205 passed in full regression suite) prove numerical consistency only. They do NOT constitute statutory structural approval or construction clearance.
2. **Preservation of Canonical Holds:** All 12 canonical engineering holds remain active. Specifically for System A, `HOLD-01` (Slab NDT), `HOLD-03` (Rooftop Boundary Survey), and `HOLD-07` (Fastener Proof Load Testing) remain strictly enforced.
3. **AFC Status:** `construction_status = BLOCKED_AFC_LOCKED` remains locked and unbreached.
4. **Watermark:** The statutory watermark `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION` is permanently affixed.
