# PHASE 1.5.3.2 — SYSTEM A FINAL ENGINEERING DISCREPANCY RESOLUTION REPORT
## RENSUN SOLAR STRUCTURAL ENGINEERING VALIDATION PROGRAMME

**Platform:** Google Antigravity  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Base Commit / HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Project ID:** `RS-STR-RENSUN-2026-0059`  
**Client / Site:** 90 ERUMAPALAYAM ITTERI ROAD, SALEM, TAMIL NADU (11.6643°N, 78.1460°E)  
**Quotation Reference:** `RENSUN/2026/0059`  
**Mounting System:** `System A: Elevated Steel Canopy`  
**Date of Audit:** 2026-11-08  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED`

---

## 1. EXECUTIVE SUMMARY & RESOLUTION STATUS

This report documents the execution of **Phase 1.5.3.2 — System A Final Engineering Discrepancy Resolution** within the RENSUN Solar Structural Engineering Validation Programme. Building upon the reconciliations achieved in Phase 1.5.3 and Phase 1.5.3.1, this stage resolves all remaining engineering, mathematical, and statutory discrepancies identified during the independent engineering audits of System A (Elevated Steel Canopy).

### Key Technical Achievements:
1. **WP-01: Wind-Uplift Rafter Lateral-Torsional Buckling (LTB) Verification:**
   - Evaluated the primary rafter under governing ULS-02 net uplift ($0.9\text{ DL} + 1.5\text{ WL}_{\text{up}}$).
   - Proved that with an unbraced bottom compression flange over the full span of $9,112\text{ mm}$, the design bending resistance drops to $M_d = 37.12\text{ kN}\cdot\text{m}$, resulting in $UR = 1.089 > 1.0$ (**STRUCTURAL FAILURE**).
   - Verified that restraining the bottom flange at intervals $\le 4,556\text{ mm}$ increases capacity to $M_d = 75.74\text{ kN}\cdot\text{m}$ ($UR = 0.534 \le 1.0$), establishing that bottom-flange fly bracing is structurally mandatory.
2. **WP-02: Bottom-Flange Fly-Bracing Design Engine (IS 800 Cl 8.9 & Cl 10.2):**
   - Derived the required stabilizing lateral restraint force per IS 800 Clause 8.9 ($2.5\%$ flange compression force: $P_{br} = 3.514\text{ kN}$, diagonal brace force $F_{\text{brace}} = 4.969\text{ kN}$).
   - Validated ISA 40 × 40 × 5 mm strut capacity: slenderness $\lambda = 77.92 \le 180$ (PASS), compressive resistance $P_d = 53.48\text{ kN}$ ($UR = 0.093$, PASS), tensile resistance $T_d = 86.14\text{ kN}$ ($UR = 0.058$, PASS).
   - Validated single M12 Gr 8.8 connection bolt shear capacity: $V_{dsb} = 31.15\text{ kN}$ ($UR = 0.160$, PASS).
   - Identified critical load transfer requirement: cold-formed purlin web ($t = 2.0\text{ mm}$) cannot take direct concentrated lateral loads without distortion; the fly brace must connect directly to the purlin support cleat (minimum 5 mm angle) to transfer lateral forces safely.
3. **WP-03: Chemical Anchor Statutory Basis Retraction & Testing Protocol:**
   - Formally retracted the erroneous citation of IS 800 Clause 10.3 (which governs steel-to-steel bolting and contains zero provisions for chemical anchors or site proof tests).
   - Established the authoritative dual standard framework: **fib Bulletin 58 / EN 1992-4:2018 / ACI 318-19 Chapter 17** for anchor design, and **BS 8539:2012 Clause 9 / ASTM E488** for site proof testing.
   - Formulated a project-specific anchor testing protocol for Grade-I RSE approval: proof load = $27.75\text{ kN}$ per 4-bolt column group ($6.94\text{ kN}$ per anchor, $1.5 \times$ factored uplift), 25% sampling, 2-minute hold, $\le 0.20\text{ mm}$ residual displacement limit.
4. **WP-04: Host Slab Thickness & Physical Anchorage Geometry Analysis:**
   - Reassessed the claimed $h_{\text{slab}} \ge 1.5 h_{ef} = 187.5\text{ mm}$ rule as an empirical rule for expansion anchors, contrasting it with manufacturer European Technical Assessments (ETA) which specify $h_{\min} = h_{ef} + 2 d_0 = 161.0\text{ mm}$.
   - Demonstrated that installing $h_{ef} = 125\text{ mm}$ anchors into existing $125 - 150\text{ mm}$ roof slabs is physically impossible without drilling through bottom rebar cover.
   - Established three viable engineering alternatives: reduced embedment ($85 - 90\text{ mm}$) with certified high-bond mortar, through-bolting with backing plates, and cast-in-place concrete stub pedestals.
5. **WP-05: Complete Foundation Load-Path Verification:**
   - Traced and validated all 10 links in the structural load transfer chain from PV modules to the building columns.
   - Verified column-to-baseplate fillet weld capacity ($910.7\text{ kN} \gg 33.84\text{ kN}$, $UR = 0.037$).
   - Verified host RCC roof slab two-way punching shear capacity per IS 456 Cl 31 ($178.88\text{ kN} \gg 33.84\text{ kN}$, $UR = 0.189$).
6. **WP-06: Independent Benchmark Unit Tests:**
   - Authored `tests/test_phase1_5_3_2_system_a_final.py` covering all 12 independent engineering checks.
   - Executed full repository regression: **154 tests passed (154/154)** with 0 failures, 0 errors, and 0 skips.
7. **WP-07: Engineering Governance & Integrity:**
   - Confirmed cryptographic immutability of all 20 historical calculation runs.
   - Maintained all 12 canonical engineering holds (10 active for System A).
   - Retained strict AFC lock (`BLOCKED_AFC_LOCKED`) and statutory preliminary watermark.

```
+----------------------------------------------------------------------------------------------------+
|                                    PHASE 1.5.3.2 AUDIT SCORECARD                                   |
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

## 2. WP-01 — WIND-UPLIFT RAFTER LATERAL-TORSIONAL BUCKLING VERIFICATION

### 2.1 Governing Load Combination & Loading Derivation
Under downward gravity loading (ULS-01: $1.5\text{ DL} + 1.5\text{ LL}$), the rafter top flange is in compression and is continuously restrained by the purlin cleat connections at $1,150\text{ mm}$ spacing ($\lambda_{LT} = 0.309 \le 0.40$), developing the full plastic moment capacity $M_{dp} = 147.95\text{ kN}\cdot\text{m}$.

However, under wind uplift suction (ULS-02: $0.9\text{ DL} + 1.5\text{ WL}_{\text{up}}$), stress reversal occurs:
- The **bottom flange** is subjected to axial compression.
- The top flange (connected to purlins) is in tension.
- The bottom flange has **no inherent lateral restraint** from the purlins.

#### Loading Parameters:
- Basic wind speed: $V_b = 39.0\text{ m/s}$ (Salem, IS 875 Part 3: 2015).
- Combined factors: $k_1 = 1.0$, $k_2 = 1.028$ (Terrain Cat 2, $10\text{ m}$), $k_3 = 1.0$, $k_4 = 1.0$.
- Design wind speed: $V_z = 39.0 \times 1.028 = 40.092\text{ m/s}$.
- Design wind pressure: $p_z = 0.6 \times (40.092)^2 = 964.42\text{ Pa} = 0.9644\text{ kPa}$.
- Net uplift aerodynamic coefficient: $C_{n,\text{up}} = -1.10$.
- Rafter tributary width: $B_t = 3.0\text{ m}$.
- Wind uplift per linear meter: $w_{\text{wind,up}} = 1.10 \times 0.9644 \times 3.0 = 3.1826\text{ kN/m}$.

#### Stabilizing Permanent Dead Load:
- PV Module dead load: $0.1044\text{ kN/m}^2 \times 3.0\text{ m} = 0.3132\text{ kN/m}$.
- ISMB 300 rafter self-weight: $44.2\text{ kg/m} \times 9.80665 / 1000 = 0.4335\text{ kN/m}$.
- Purlin self-weight (C100 purlins at $1.15\text{ m}$ spacing): $0.0301\text{ kN/m}$.
- Walkway / cable tray allowance: $0.2000\text{ kN/m}$.
- Total stabilizing dead load: $w_{\text{DL}} = 0.3132 + 0.4335 + 0.0301 + 0.2000 = 0.9767\text{ kN/m}$.

#### Net Factored Design Load (ULS-02):
$$w_{\text{net,up}} = 1.5 \times w_{\text{wind,up}} - 0.9 \times w_{\text{DL}} = 1.5 \times 3.1826 - 0.9 \times 0.9767 = 3.8948\text{ kN/m}$$

#### Factored Bending Moments:
- Full simply supported span ($L = 9.112\text{ m}$):
  $$M_{u,\text{up}} = \frac{3.8948 \times (9.112)^2}{8} = 40.42\text{ kN}\cdot\text{m}$$
- Clear span between column supports ($L_{\text{clear}} = 4.556\text{ m}$):
  $$M_{u,\text{half}} = \frac{3.8948 \times (4.556)^2}{8} = 10.11\text{ kN}\cdot\text{m}$$

---

### 2.2 Lateral-Torsional Buckling Capacity Comparison (IS 800 Cl 8.2.2 & Annex E)

Section: ISMB 300 ($h = 300\text{ mm}$, $b = 140\text{ mm}$, $t_w = 7.5\text{ mm}$, $t_f = 12.4\text{ mm}$, $I_y = 4.539 \times 10^6\text{ mm}^4$, $Z_{px} = 651,000\text{ mm}^3$, $E = 205,000\text{ MPa}$, $f_y = 250\text{ MPa}$, $\gamma_{m0} = 1.10$).
- Torsional constant: $I_t = 168,810\text{ mm}^4$.
- Warping constant: $I_w = 9.387 \times 10^{10}\text{ mm}^6$.
- Imperfection factor: $\alpha_{LT} = 0.21$ (Rolled section, Buckling Curve a).

$$\begin{aligned}
M_{cr} &= \sqrt{\left(\frac{\pi^2 E I_y}{L^2}\right) \left(G I_t + \frac{\pi^2 E I_w}{L^2}\right)} \\
\lambda_{LT} &= \sqrt{\frac{Z_{px} f_y}{M_{cr}}} \\
\phi_{LT} &= 0.5 \left[1 + \alpha_{LT}(\lambda_{LT} - 0.2) + \lambda_{LT}^2\right] \\
\chi_{LT} &= \frac{1}{\phi_{LT} + \sqrt{\phi_{LT}^2 - \lambda_{LT}^2}} \le 1.0 \\
M_d &= \frac{\chi_{LT} Z_{px} f_y}{\gamma_{m0}}
\end{aligned}$$

| Evaluation Case | Unbraced Length $L$ | Elastic Moment $M_{cr}$ | Slenderness $\lambda_{LT}$ | Reduction $\chi_{LT}$ | Capacity $M_d$ | Demand $M_{u,\text{up}}$ | Unity Ratio (UR) | Codal Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Case A: Unbraced Full Span** | $9,112\text{ mm}$ | $46.29\text{ kN}\cdot\text{m}$ | $1.875$ | $0.251$ | $37.12\text{ kN}\cdot\text{m}$ | $40.42\text{ kN}\cdot\text{m}$ | **1.089** | **FAIL (> 1.0)** |
| **Case B: Restrained at Columns** | $4,556\text{ mm}$ | $107.73\text{ kN}\cdot\text{m}$ | $1.229$ | $0.512$ | $75.74\text{ kN}\cdot\text{m}$ | $40.42\text{ kN}\cdot\text{m}$ | **0.534** | **PASS (<= 1.0)** |
| **Case C: Restrained at Alternate Purlins** | $2,300\text{ mm}$ | $244.52\text{ kN}\cdot\text{m}$ | $0.815$ | $0.781$ | $115.55\text{ kN}\cdot\text{m}$ | $40.42\text{ kN}\cdot\text{m}$ | **0.350** | **PASS (<= 1.0)** |

> [!WARNING]
> **Engineering Finding — Unbraced Full Span Fails:**  
> If the bottom compression flange is unbraced across the full $9.112\text{ m}$ length of the rafter, the rafter fails by Lateral-Torsional Buckling under governing wind uplift ($UR = 1.089 > 1.0$). Intermediate bottom-flange fly bracing is structurally mandatory to ensure $L \le 4,556\text{ mm}$.

---

## 3. WP-02 — BOTTOM-FLANGE FLY-BRACING DESIGN ENGINE

### 3.1 Required Restraint Force (IS 800:2007 Clause 8.9)
Per IS 800:2007 Clause 8.9.1, lateral bracing to compression flanges must be designed to resist an equivalent lateral stabilizing force of not less than **2.5% of the maximum compression flange force**:

1. Compression flange force in ISMB 300 ($d = h - t_f = 300 - 12.4 = 287.6\text{ mm}$):
   $$N_c = \frac{M_{u,\text{up}}}{d} = \frac{40.42\text{ kN}\cdot\text{m}}{0.2876\text{ m}} = 140.54\text{ kN}$$
2. Required lateral stabilizing restraint force $P_{br}$:
   $$P_{br} = 0.025 \times N_c = 0.025 \times 140.54\text{ kN} = 3.514\text{ kN}$$
3. Diagonal fly-brace strut axial force demand ($\theta = 45^\circ$ to vertical):
   $$F_{\text{brace}} = \frac{P_{br}}{\cos 45^\circ} = \frac{3.514\text{ kN}}{0.7071} = 4.969\text{ kN}$$

---

### 3.2 Member Sizing: ISA 40 × 40 × 5 mm Strut Capacity
- Strut length: $L = 600\text{ mm}$.
- Section: ISA 40 × 40 × 5 mm ($A = 379\text{ mm}^2$, $r_{vv} = r_{\min} = 7.7\text{ mm}$, $f_y = 250\text{ MPa}$, $E = 205,000\text{ MPa}$, $\gamma_{m0} = 1.10$).
- Effective length factor (bolted at both ends per Cl 7.5.1.2): $K = 1.0 \implies KL = 600\text{ mm}$.
- Slenderness:
  $$\lambda = \frac{KL}{r_{\min}} = \frac{600}{7.7} = 77.92 \le 180 \quad (\text{PASS per Table 3})$$
- Euler buckling stress:
  $$f_{cc} = \frac{\pi^2 E}{\lambda^2} = \frac{\pi^2 \times 205,000}{(77.92)^2} = 332.9\text{ MPa}$$
- Non-dimensional slenderness:
  $$\lambda_0 = \sqrt{\frac{f_y}{f_{cc}}} = \sqrt{\frac{250}{332.9}} = 0.867$$
- Compressive stress (Buckling Curve c, $\alpha = 0.49$):
  $$\phi = 0.5 \left[1 + 0.49(0.867 - 0.2) + (0.867)^2\right] = 1.039 \implies \chi = 0.621$$
  $$f_{cd} = \frac{\chi f_y}{\gamma_{m0}} = \frac{0.621 \times 250}{1.10} = 141.1\text{ MPa}$$
- Design Compressive Resistance:
  $$P_d = \frac{A \times f_{cd}}{1000} = \frac{379 \times 141.1}{1000} = 53.48\text{ kN}$$
  $$\text{Utilization Ratio (Compression)} = \frac{F_{\text{brace}}}{P_d} = \frac{4.969}{53.48} = \mathbf{0.093} \le 1.0 \quad (\mathbf{PASS})$$
- Design Tensile Resistance:
  $$T_d = \frac{A_g f_y}{\gamma_{m0}} = \frac{379 \times 250}{1.10 \times 1000} = 86.14\text{ kN}$$
  $$\text{Utilization Ratio (Tension)} = \frac{F_{\text{brace}}}{T_d} = \frac{4.969}{86.14} = \mathbf{0.058} \le 1.0 \quad (\mathbf{PASS})$$

---

### 3.3 Connection Detailing & Thin-Walled Load Transfer

#### 1. Bolted Connection at Rafter Bottom Flange:
- Fastener: Single M12 Grade 8.8 bolt ($f_{ub} = 800\text{ MPa}$, $A_{nb} = 84.3\text{ mm}^2$, $\gamma_{mb} = 1.25$).
- Design shear capacity per IS 800 Clause 10.3.2:
  $$V_{dsb} = \frac{f_{ub}}{\sqrt{3} \gamma_{mb}} A_{nb} = \frac{800}{\sqrt{3} \times 1.25} \times 84.3 \times 10^{-3} = 31.15\text{ kN}$$
  $$\text{Utilization Ratio (Bolt Shear)} = \frac{4.969}{31.15} = \mathbf{0.160} \le 1.0 \quad (\mathbf{PASS})$$

#### 2. Load Transfer into Purlin — Purlin Cleat Web Stiffener Requirement:
> [!IMPORTANT]
> **Critical Detailing Requirement — Thin Web Protection:**  
> The cold-formed purlin web is only $t = 2.0\text{ mm}$ thick. Fastening the fly-brace upper end directly to the un-stiffened purlin web would induce severe out-of-plane localized bending and web distortion under the $3.514\text{ kN}$ lateral load component.  
> **Mandatory Rule:** The fly-brace top connection must attach directly to the **purlin support cleat** (minimum 5 mm thick hot-rolled angle cleat), which is rigidly bolted to the primary rafter web. This routes the stabilizing restraint force directly into the triangulated purlin-rafter node without causing web crippling.

---

## 4. WP-03 — CHEMICAL ANCHOR STATUTORY BASIS & TESTING PROTOCOL

### 4.1 Retraction of Erroneous IS 800 Clause 10.3 Citation
The Phase 1.4 report cited IS 800:2007 Clause 10.3 as the statutory basis requiring three chemical-anchor proof tests at 1.5 times design tension.

**Formal Engineering Retraction:**
- IS 800:2007 Clause 10 governs structural steel connections (bearing bolts, high-strength friction-grip bolts, welds).
- Clause 10 contains **ZERO provisions** for post-installed chemical anchors, adhesive bond mechanics, concrete breakout failure, or on-site anchor pull-out proof testing.
- The citation of IS 800 Clause 10.3 for chemical anchor proof testing is **formally retracted as legally and technically incorrect**.

---

### 4.2 Authoritative Fastener Standards Hierarchy for Solar Canopies in India

```mermaid
flowchart TD
    A["Structural Solar Canopy Fastener Hierarchy"] --> B["Statutory Indian Building Codes"]
    A --> C["International Anchor Design Standards"]
    A --> D["Site Proof-Testing & Verification"]

    B --> B1["IS 456:2000 Cl 31 & 34<br/>(Concrete Bearing & Punching Shear)"]
    B --> B2["IS 800:2007 Cl 10<br/>(Steel-to-Steel Connections Only)"]

    C --> C1["fib Bulletin 58 / EN 1992-4:2018<br/>(Primary Technical Specification for Post-Installed Fasteners)"]
    C --> C2["ACI 318-19 Chapter 17 / ACI 355.4<br/>(Adhesive Anchor Design in Cracked/Uncracked Concrete)"]

    D --> D1["BS 8539:2012 Clause 9<br/>(Code of Practice for Testing Anchors in Concrete)"]
    D --> D2["ASTM E488 / ASTM E1512<br/>(Standard Test Methods for Strength of Anchors)"]
```

---

### 4.3 Comprehensive Failure Mode Evaluation for Anchor Group (4× M16)
Under maximum factored uplift reaction $T_u = 18.50\text{ kN}$ ($4.63\text{ kN}$ per anchor) and resultant shear $V_u = 3.50\text{ kN}$ ($0.88\text{ kN}$ per anchor):

1. **Steel Tension Failure (fib 58 Cl 7.2.1.3):**
   - $N_{Rk,s} = A_{se} \times f_{uk} = 157\text{ mm}^2 \times 800\text{ MPa} = 125.6\text{ kN}$.
   - $\phi N_{sa} = N_{Rk,s} / \gamma_{Ms} = 125.6 / 1.50 = 83.73\text{ kN} \implies \text{Group } = 334.9\text{ kN} \gg 18.50\text{ kN}$ ($UR = 0.055$).
2. **Concrete Cone Breakout (fib 58 Cl 7.2.1.4):**
   - Effective embedment $h_{ef} = 125\text{ mm}$, group spacing $s_x = 250\text{ mm}$, $s_y = 150\text{ mm}$.
   - Uncracked concrete cone resistance: $\phi N_{cbg} = 94.79\text{ kN} \gg 18.50\text{ kN}$ ($UR = 0.195$).
   - Cracked concrete cone resistance ($\times 0.70$): $\phi N_{cbg,\text{cr}} = 66.35\text{ kN} \gg 18.50\text{ kN}$ ($UR = 0.279$).
3. **Adhesive Combined Pull-Out & Concrete Failure (fib 58 Cl 7.2.1.5):**
   - Characteristic bond strength $\tau_{Rk} = 12.0\text{ MPa}$ (Hilti HIT-RE 500 V4 / Fischer FIS EM Plus in uncracked M20 concrete).
   - $\phi N_{p} = (\pi \times 16 \times 125 \times 12.0) / (1.50 \times 1000) = 50.27\text{ kN} \implies \text{Group } = 201.0\text{ kN} \gg 18.50\text{ kN}$ ($UR = 0.092$).
4. **Steel Shear Failure (fib 58 Cl 7.2.2.3):**
   - $V_{Rk,s} = 0.5 \times A_{se} \times f_{uk} = 62.8\text{ kN} \implies \phi V_{sa} = 48.98\text{ kN} \implies \text{Group } = 195.9\text{ kN} \gg 3.50\text{ kN}$ ($UR = 0.018$).
5. **Concrete Pry-Out Failure (fib 58 Cl 7.2.2.5):**
   - $V_{Rk,cp} = k_8 \times N_{Rk,c} = 2.0 \times 135.4\text{ kN} = 270.8\text{ kN} \implies \phi V_{cpg} = 180.5\text{ kN} \gg 3.50\text{ kN}$ ($UR = 0.019$).
6. **Combined Tension & Shear Interaction (fib 58 Cl 7.2.3):**
   $$\left(\frac{N_{Ed}}{\phi N_{Rd}}\right)^{1.5} + \left(\frac{V_{Ed}}{\phi V_{Rd}}\right)^{1.5} = (0.195)^{1.5} + (0.018)^{1.5} = 0.086 + 0.002 = \mathbf{0.088} \le 1.0 \quad (\mathbf{PASS})$$

---

### 4.4 Project-Specific Site Anchor Testing Protocol (BS 8539:2012)
To provide the legal and engineering basis for Grade-I RSE sign-off, the following protocol is established:

```
+----------------------------------------------------------------------------------------------------+
|                         PROJECT-SPECIFIC CHEMICAL ANCHOR TESTING PROTOCOL                          |
+--------------------------+-------------------------------------------------------------------------+
| Target Anchor            | 4x M16 Grade 8.8 Threaded Rods per Baseplate                            |
| Certified Mortar         | Pure Epoxy Resin (ETA qualified for cracked & uncracked concrete)       |
| Factored Uplift Demand   | Ned = 18.50 kN per column (4.63 kN per individual anchor rod)           |
| Proof Load Factor        | 1.50 x Design Factored Action (BS 8539 Cl 9.3)                         |
| Proof Test Load (Bolt)   | 6.94 kN per anchor rod                                                  |
| Proof Test Load (Group)  | 27.75 kN per column 4-bolt group                                        |
| Sampling Frequency       | 25% of all installed canopy columns (Minimum 3 complete column groups)   |
| Test Equipment           | Calibrated hollow-ram hydraulic jack with digital displacement gauge    |
| Sustained Load Duration  | 2 minutes at peak test load (27.75 kN)                                  |
| Maximum Residual Slip    | <= 0.20 mm permanent displacement after release                         |
| Visual Rejection Criteria| Zero concrete cone cracking, spalling, mortar extrusion, or baseplate tilt|
| Mandatory Sign-Off       | Testing witnessed and certified by Grade-I Structural Engineer (RSE)   |
+--------------------------+-------------------------------------------------------------------------+
```

---

## 5. WP-04 — HOST SLAB THICKNESS & ANCHORAGE GEOMETRY ANALYSIS

### 5.1 Reassessment of the Claimed $h_{\text{slab}} \ge 1.5 h_{ef} = 187.5\text{ mm}$ Rule
The Phase 1.4 review stated that $h_{ef} = 125\text{ mm}$ requires a minimum slab thickness of $h_{\text{slab}} \ge 1.5 h_{ef} = 187.5\text{ mm}$.

**Technical Audit Finding:**
- The $1.5 h_{ef}$ requirement is an **empirical rule of thumb** originating from torque-controlled mechanical expansion anchors to avoid splitting the concrete during expansion wedging.
- For post-installed chemical adhesive anchors, manufacturer European Technical Assessments (e.g., Hilti ETA-20/0541 for HIT-RE 500 V4, Fischer ETA-17/0979 for FIS EM Plus) specify:
  $$h_{\min} = h_{ef} + 2 d_0 = 125\text{ mm} + 2(18\text{ mm}) = \mathbf{161.0\text{ mm}} \quad (\text{or } h_{ef} + 30\text{ mm} = 155.0\text{ mm})$$
- Therefore, $187.5\text{ mm}$ is not a statutory Indian code requirement.

---

### 5.2 Physical Feasibility in Standard $125 - 150\text{ mm}$ Roof Slabs
Standard residential and commercial RCC roof slabs in Salem and Tamil Nadu have an actual slab thickness of **$125\text{ mm}$ to $150\text{ mm}$**.

```
Existing Roof Slab Section:
+-------------------------------------------------------------+  Top Surface (Canopy Baseplate)
|                                                             |
|   |<- M16 Anchor hef = 125 mm ->|                           |
|   ==============================================            |  Top Rebar Mesh
|                                                             |
|                                                             |
|   ==============================================            |  Bottom Rebar Mesh (Clear cover = 25 mm)
|   ..............................................            |  Bottom Concrete Cover Zone
+-------------------------------------------------------------+  Ceiling Soffit
    |<-------------------- h_slab = 125 - 150 mm ------------>|
```

In an existing slab of $125\text{ mm}$ or $150\text{ mm}$:
- Bottom rebar clear cover = $25\text{ mm}$.
- Available solid concrete depth before penetrating rebar zone = $150 - 25 = 125\text{ mm}$ (in a $150\text{ mm}$ slab) or $100\text{ mm}$ (in a $125\text{ mm}$ slab).
- Drilling a hole of depth $h_0 = h_{ef} + 5\text{ mm} = 130\text{ mm}$ in a $125\text{ mm}$ slab would blow through the bottom soffit. In a $150\text{ mm}$ slab, it leaves only $20\text{ mm}$ clearance, destroying the bottom cover and risking spalling/water leakage.

> [!CAUTION]
> **Physical Construction Barrier:**  
> An effective embedment of $h_{ef} = 125\text{ mm}$ is physically unfeasible in a standard $125 - 150\text{ mm}$ roof slab without compromising slab integrity or breaching bottom cover. Site core drilling and ultrasonic thickness measurements (HOLD-01) are mandatory before anchoring details can be approved.

---

### 5.3 Three Defensible Engineering Alternatives

```mermaid
flowchart LR
    A["Anchorage in 125-150 mm Slab"] --> B["Alternative 1: Reduced Embedment<br/>hef = 85 - 90 mm<br/>High-performance epoxy mortar"]
    A --> C["Alternative 2: Through-Bolting<br/>M16 rods through full depth<br/>150x150x10 mm backing plate"]
    A --> D["Alternative 3: Cast Pedestals<br/>250 mm high M25 concrete<br/>Dowelled into existing slab"]
```

1. **Alternative 1 — Engineered Reduced Embedment ($h_{ef} = 85 - 90\text{ mm}$):**
   - Utilize premium injectable pure epoxy mortar with bond strength $\tau_{Rk} \ge 15.0\text{ MPa}$.
   - At $h_{ef} = 85\text{ mm}$, uncracked cone breakout capacity is $\phi N_{cbg} = 53.6\text{ kN} \gg 18.50\text{ kN}$ ($UR = 0.345$).
   - Safely preserves $35 - 60\text{ mm}$ of bottom concrete cover, preventing soffit blowout.
2. **Alternative 2 — Through-Bolting System:**
   - Core-drill through the full depth of the $125 - 150\text{ mm}$ slab.
   - Install M16 Grade 8.8 threaded rods clamping the roof slab between the top $350 \times 250 \times 16\text{ mm}$ baseplate and a $150 \times 150 \times 10\text{ mm}$ steel backing plate on the underside ceiling.
   - Eliminates concrete breakout vulnerability and relies on direct slab flexural bearing.
3. **Alternative 3 — Cast-in-Place Concrete Stub Pedestals:**
   - Cast $400 \times 300 \times 250\text{ mm}$ high M25 concrete stub pedestals dowelled into the existing roof slab with 4× 12 mm rebars chemical-anchored into the slab.
   - Provides $250\text{ mm}$ solid depth, permitting full $h_{ef} = 125\text{ mm}$ embedment with $> 125\text{ mm}$ clearance.

---

## 6. WP-05 — COMPLETE FOUNDATION LOAD-PATH VERIFICATION

The complete structural load path from the wind-exposed PV module to the building columns is traced and verified below:

```mermaid
graph TD
    M["1. PV Module Frame"] -->|"Tu = 1.74 kN / clamp (UR = 0.387)"| CL["2. Mid/End Module Clamps"]
    CL -->|"Bending & SLS-01 Deflection"| P["3. Purlins (ISMC 100x50x2.0 / C125)"]
    P -->|"Cleat Shear Vu = 2.29 kN (UR = 0.079)"| C["4. Purlin Cleat Angle"]
    C -->|"Mu = 40.42 kNm (Fly-braced UR = 0.534)"| R["5. Primary Rafter (ISMB 300)"]
    R -->|"Mu = 4.90 kNm, Vu = 33.84 kN (UR = 0.151)"| RC["6. Rafter-to-Column Moment Conn."]
    RC -->|"Axial Pu = 33.84 kN, Mz = 4.90 kNm (UR = 0.082)"| COL["7. Canopy Column (ISMB 300, H=2.8m)"]
    COL -->|"6 mm Fillet Weld P_wd = 910.7 kN (UR = 0.037)"| W["8. Column-to-Baseplate Fillet Weld"]
    W -->|"Cantilever Bending tp = 16 mm (UR = 0.775)"| BP["9. Baseplate (350x250x16 mm)"]
    BP -->|"Uplift Tu = 18.50 kN (UR = 0.195)"| AN["10. Chemical Anchors (4x M16)"]
    AN -->|"Two-Way Punching Vup = 178.88 kN (UR = 0.189)"| SL["11. Host RCC Roof Slab (M20)"]
```

### Detailed Structural Verification Steps:

| Step | Structural Component | Governing Action & Formula | Factored Demand | Design Capacity | Unity Ratio (UR) | Engineering Status |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| **1** | PV Module to Clamp | Tension pull-out under wind uplift | $1.74\text{ kN}$ / clamp | $4.50\text{ kN}$ (Certified rating) | **0.387** | PASS (HOLD-07 torque check) |
| **2** | Cold-Formed Purlin | SLS-01 Deflection ($L/250$) | $1.38\text{ mm}$ (Opt A) | $8.00\text{ mm}$ allowable | **0.172** | PASS (Lipped channel) |
| **3** | Purlin Cleat to Rafter | Fastener shear (M12 Gr 8.8) | $V_u = 2.29\text{ kN}$ | $V_{dsb} = 28.9\text{ kN}$ | **0.079** | PASS (Direct bearing) |
| **4** | Primary Rafter (ISMB 300) | Uplift flexure & LTB (IS 800 Cl 8.2) | $M_{u,\text{up}} = 40.42\text{ kNm}$ | $M_d = 75.74\text{ kNm}$ (braced) | **0.534** | PASS (Fly-braced at $\le 4.56\text{ m}$) |
| **5** | Rafter-to-Column Conn. | End-plate moment & bolt shear | $M_u = 4.90\text{ kNm}$ | $M_d = 32.5\text{ kNm}$ | **0.151** | PASS (4-bolt stiffened) |
| **6** | Canopy Column (ISMB 300) | Combined axial-bending (Cl 9.3) | $P_u = 33.84\text{ kN}$, $M_z = 4.90$ | $N_d = 1278.6\text{ kN}$, $M_{dz} = 147.9$ | **0.082** | PASS ($\lambda = 98.6$, drift $0.36\text{ mm}$) |
| **7** | Column-Base Fillet Weld | All-around fillet weld shear (Cl 10.5) | $P_u = 33.84\text{ kN}$ | $P_{wd} = 910.7\text{ kN}$ | **0.037** | PASS ($6\text{ mm}$ fillet weld) |
| **8** | Baseplate ($350 \times 250 \times 16$) | Cantilever bending ($t_p \ge t_f$) | $t_{p,\text{calc}} = 3.47\text{ mm}$ | $t_{p,\text{prov}} = 16.0\text{ mm} \ge 12.4$ | **0.775** | PASS (IS 800 Cl 7.4 minimum) |
| **9** | Post-Installed Anchors | Group uplift cone breakout | $T_u = 18.50\text{ kN}$ | $\phi N_{cbg} = 94.79\text{ kN}$ | **0.195** | PASS_THEORETICAL (Test pending) |
| **10** | Host RCC Roof Slab | Punching shear (IS 456 Cl 31.6.3) | $P_u = 33.84\text{ kN}$ | $V_{up} = 178.88\text{ kN}$ | **0.189** | PASS_THEORETICAL (Survey pending) |

#### Component Calculations:
1. **Column-to-Baseplate Fillet Weld (IS 800 Cl 10.5):**
   - Column ISMB 300 perimeter: $L_w = 2(300) + 4(140) - 2(7.5) = 1,145\text{ mm}$.
   - Fillet size: $s = 6.0\text{ mm} \implies t_t = 0.70 \times 6.0 = 4.2\text{ mm}$.
   - Design shear strength: $f_{vwd} = f_u / (\sqrt{3} \gamma_{mw}) = 410 / (\sqrt{3} \times 1.25) = 189.37\text{ MPa}$.
   - Total capacity: $P_{wd} = 1,145 \times 4.2 \times 189.37 \times 10^{-3} = \mathbf{910.7\text{ kN}} \gg 33.84\text{ kN}$ ($UR = 0.037$).
2. **Host Slab Punching Shear (IS 456:2000 Clause 31.6.3):**
   - Baseplate dimensions: $350 \times 250\text{ mm}$. Effective slab depth: $d = 100\text{ mm}$ (assuming $125\text{ mm}$ slab with $25\text{ mm}$ cover).
   - Critical punching shear perimeter at $d/2 = 50\text{ mm}$:
     $$b_0 = 2(350 + 100) + 2(250 + 100) = 900 + 700 = 1,600\text{ mm}$$
   - Permissible concrete shear strength:
     $$\tau_c = 0.25 \sqrt{f_{ck}} = 0.25 \sqrt{20} = 1.118\text{ MPa}$$
   - Design punching shear resistance:
     $$V_{up} = \frac{\tau_c \times b_0 \times d}{1000} = \frac{1.118 \times 1600 \times 100}{1000} = \mathbf{178.88\text{ kN}} \gg 33.84\text{ kN} \quad (\mathbf{UR = 0.189})$$

---

## 7. WP-06 — INDEPENDENT BENCHMARK UNIT TESTS & REGRESSION RESULTS

An independent verification suite was authored in [`tests/test_phase1_5_3_2_system_a_final.py`](file:///Users/karthik/tneb-account-extractor/tests/test_phase1_5_3_2_system_a_final.py) implementing 12 isolated test cases.

### Test Execution Summary:
```
================================================================================
TEST EXECUTION REPORT: Phase 1.5.3.2 System A Final Engineering Suite
Test Module: tests/test_phase1_5_3_2_system_a_final.py
Environment: Isolated SQLite in-memory / temporary mock sandbox
================================================================================
[PASS] test_01_wind_uplift_factored_moment_demand
       -> Verifies w_net_up = 3.8948 kN/m and Mu_full = 40.42 kNm under ULS-02.
[PASS] test_02_rafter_ltb_unbraced_failure_vs_clear_span
       -> Verifies unbraced 9112 mm fails LTB (UR = 1.089), clear span 4556 mm passes (UR = 0.534).
[PASS] test_03_fly_bracing_required_stabilizing_force
       -> Verifies 2.5% stabilizing force Pbr = 3.514 kN and diagonal brace demand 4.969 kN.
[PASS] test_04_isa_40x40x5_strut_buckling_capacity
       -> Verifies ISA 40x40x5 slenderness lambda = 77.92 <= 180 and Pd = 53.48 kN (UR = 0.093).
[PASS] test_05_fly_bracing_connection_and_purlin_cleat_requirement
       -> Verifies M12 Gr 8.8 bolt shear (UR = 0.160) and flags purlin cleat web stiffener.
[PASS] test_06_chemical_anchor_standards_hierarchy
       -> Formally retracts IS 800 Cl 10 citation and establishes fib 58 / BS 8539 hierarchy.
[PASS] test_07_project_specific_anchor_testing_protocol
       -> Verifies proof load = 27.75 kN (1.5x Ned), 0.20 mm slip limit, and RSE sign-off.
[PASS] test_08_slab_thickness_evaluation_and_alternatives
       -> Reassesses h_min = 161 mm (ETA), demonstrates 125-150 mm physical limits, details 3 alternatives.
[PASS] test_09_complete_foundation_load_path_verification
       -> Verifies 10 load path steps, baseplate fillet weld (910.7 kN), and slab punching (178.88 kN).
[PASS] test_10_historical_records_immutability
       -> Verifies exactly 20 historical calculation runs remain intact and unmutated.
[PASS] test_11_original_holds_active_and_enforced
       -> Verifies all 12 canonical holds active (10 applicable to System A).
[PASS] test_12_afc_lock_and_statutory_watermark
       -> Verifies BLOCKED_AFC_LOCKED and PRELIMINARY watermark across all runs.
--------------------------------------------------------------------------------
Ran 12 tests in 0.040s — ALL PASSED (12/12)
================================================================================
```

### Full Repository Regression Suite:
```
$ python3 -m unittest discover -s tests -p "test_*.py"
Ran 154 tests in 7.634s
OK (154/154 PASSED, 0 FAILURES, 0 ERRORS, 0 SKIPS)
```

---

## 8. WP-07 — ENGINEERING GOVERNANCE & SEPARATION OF STATUSES

In accordance with mandatory structural engineering governance, four separate status categories are maintained:

```
+----------------------------------------------------------------------------------------------------+
|                               FOUR-TIER GOVERNANCE STATUS MATRIX                                   |
+----------------------+---------------+-------------------------------------------------------------+
| Governance Category  | Status Value  | Technical & Legal Definition                                |
+----------------------+---------------+-------------------------------------------------------------+
| Numerical Status     | PASS          | All mathematical formulas, code checks, and section checks  |
|                      |               | satisfy unity ratios (UR <= 1.0) under proposed fly bracing.|
+----------------------+---------------+-------------------------------------------------------------+
| Input Completeness   | INCOMPLETE    | Physical host slab thickness, concrete compressive strength |
|                      |               | (fck), and rebar layout are unmeasured pending site NDT.   |
+----------------------+---------------+-------------------------------------------------------------+
| Provenance Status    | AUDITED       | All equations, loads, and material properties traceable to  |
|                      |               | IS 875:2015, IS 800:2007, IS 801, and fib Bulletin 58.      |
+----------------------+---------------+-------------------------------------------------------------+
| Engineering Status   | READY FOR     | Analytical models and discrepancy reconciliations are fully |
|                      | INDEPENDENT   | documented and defensible for Grade-I RSE review.           |
|                      | REVIEW        |                                                             |
+----------------------+---------------+-------------------------------------------------------------+
| Construction Status  | BLOCKED_      | Construction strictly prohibited. All 12 canonical holds   |
|                      | AFC_LOCKED    | remain enforced. Watermark mandatory.                       |
+----------------------+---------------+-------------------------------------------------------------+
```

### Active Engineering Holds Applicable to System A:
1. `HOLD-01` (INSPECTION_REQUIRED_HOLD): Physical roof slab NDT core/ultrasonic survey pending.
2. `HOLD-02` (AERODYNAMIC_UNSUPPORTED_HOLD): Local peak aerodynamic suction coefficient validation pending.
3. `HOLD-03` (WIND_COORD_UNVERIFIED_HOLD): Physical rooftop latitude/longitude boundary survey pending.
4. `HOLD-04` (WIND_TRANSFORM_UNVERIFIED_HOLD): Coordinate transformation audit for sloped panels pending.
5. `HOLD-05` (VERTICAL_SEISMIC_APPLICABILITY_HOLD): Statutory seismic screening pending.
6. `HOLD-06` (LOAD_COMBINATION_PROVISIONAL_HOLD): Partial safety factor verification pending.
7. `HOLD-07` (FASTENER_TORQUE_UNVERIFIED_HOLD): On-site chemical anchor pull-out test ($27.75\text{ kN}$) pending.
8. `HOLD-08` (NUMERICAL_INSTABILITY_HOLD): Rafter stiffness matrix conditioning audit pending.
9. `HOLD-11` (ASSUMED_DATA_CERTIFICATION_HOLD): Sign-off on unmeasured host building framing pending.
10. `HOLD-12` (DRAWING_UNVERIFIED_HOLD): Statutory AFC drawing release audit pending.

---

## 9. PRODUCTION DATABASE CRYPTOGRAPHIC PARITY

Cryptographic SHA-256 hashes were calculated before and after all Phase 1.5.3.2 verification activities:

| Production File | Baseline SHA-256 Hash | Post-Audit SHA-256 Hash | Cryptographic Parity |
|:---|:---|:---|:---:|
| `quotations.db` | `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf` | `3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf` | **BIT-FOR-BIT IDENTICAL** |
| `structural_runs.db` | `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff` | `ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff` | **BIT-FOR-BIT IDENTICAL** |
| `quotation_settings.json` | `26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1` | `26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1` | **BIT-FOR-BIT IDENTICAL** |

Zero bytes of production database records or historical calculation runs were mutated.

---

## 10. DEFINITIVE CONCLUSION & STOP BOUNDARY

### Final Determination:
1. **Mathematical & Analytical Readiness:**  
   The engineering models and calculations for System A (Elevated Steel Canopy) are **complete, mathematically reconciled, and ready for Independent Engineering Review**. All identified discrepancies (wind-uplift rafter LTB, fly-bracing sizing, purlin web load transfer, anchor standards retraction, slab thickness feasibility, and full load path verification) have been resolved with rigorous codal backing.
2. **Construction Status:**  
   System A is **STILL BLOCKED from construction (`BLOCKED_AFC_LOCKED`)**.
3. **Missing Physical Evidence:**  
   System A remains **INCOMPLETE FOR FABRICATION OR SITE INSTALLATION** until physical rooftop evidence is obtained:
   - On-site RCC roof slab thickness and rebar depth survey (ultrasonic/core drill).
   - On-site concrete compressive strength testing per IS 13311 ($f_{ck} \ge 20\text{ MPa}$).
   - On-site chemical anchor pull-out proof load testing ($27.75\text{ kN}$ per column group).
4. **Boundary Enforced:**  
   Phase 1.5.3.2 is cleanly terminated at this boundary. **Phase 1.5.4 (System B) has NOT been started.** Zero holds have been released, and zero git commits or branch switches have been performed.
