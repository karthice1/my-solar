# RENSUN SOLAR — PHASE 1.4.2
# STRUCTURAL VALIDATION MATRIX: CONSOLIDATED CROSS-SYSTEM SPECIFICATION

**Document ID:** `RS-STR-VAL-MAT-01`  
**Revision:** R0 (Validation Readiness Specification)  
**Governing Branch:** `feature/phase1-structural-foundation`  
**Platform Version:** Phase 1.4.2  
**Status:** DRAFT SPECIFICATION — PRE-VALIDATION READINESS ONLY  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  

---

## 1. Executive Summary & Purpose

The Structural Validation Matrix provides a consolidated, cross-system engineering specification across all four canonical solar mounting systems supported by the RENSUN Solar platform. 

This matrix establishes the definitive baseline against which an independent Registered Structural Engineer (RSE) or third-party engineering agency will audit:
1. Input requirements and data provenance gates.
2. Codal clauses, mathematical formulas, and load combination factors.
3. Component-level structural limit state checks (ULS and SLS).
4. Physical testing and material certification requirements.
5. Canonical verification hold triggers and prerequisite release criteria.

> [!IMPORTANT]
> **Governance Barrier**: Automated unit tests or passing numerical checks (`status = PASS`) demonstrate **software verification only**. They do **not** constitute structural validation or professional engineering certification. Construction approval (AFC) remains permanently hard-locked across all four systems (`is_approved_for_construction = 0`).

---

## 2. Master Four-System Comparative Matrix

| Engineering Dimension | System A: Elevated Steel Canopy | System B: Low-Height Aluminium Rail | System C: Metal-Sheet Fastened System | System D: Ballasted Non-Penetrating System |
| :--- | :--- | :--- | :--- | :--- |
| **System Identity** | Elevated open canopy structure above host RCC roof slab | Low-profile extruded aluminium rails on elevated tilt legs or L-feet | Flush or low-tilt standing-seam / trapezoidal sheet clamps | Non-penetrating concrete ballast blocks resting on elastomeric pads |
| **Clearance / Tilt** | $H_{\text{clear}} = 2.5\text{ m} - 3.2\text{ m}$, tilt $5^\circ - 12^\circ$ | $H_{\text{clear}} = 0.15\text{ m} - 0.45\text{ m}$, tilt $10^\circ - 15^\circ$ | Conforms to roof pitch ($3^\circ - 15^\circ$), flush mount | Low tilt ($5^\circ - 10^\circ$) to minimize aerodynamic drag |
| **Primary Material** | Structural Steel E250 Fe 410W (IS 2062: 2011) | Extruded Aluminium Alloy 6063-T6 (IS 733 / IS 8147) | Marine Grade Al 6005-T6 / SS 304 A2-70 Clamps | Precast Concrete M25/M30 blocks + Al/Steel chassis |
| **Governing Standard** | **IS 800: 2007** (LSM) & **IS 875: 2015** | **IS 8147: 1976** & **AA ADM 2020** | **IS 800: 2007** / `REF PENDING VERIF` (Sheeting) | **IS 875 (Part 3)** / `REF PENDING VERIF` (Friction) |
| **Wind Loading Standard**| IS 875 (Part 3) Clause 7.4.4.4 / Table 8 | IS 875 (Part 3) Clause 7.3.3 / Shielded Rooftop | IS 875 (Part 3) Clause 7.3.3.2 (Pitched Roofs) | IS 875 (Part 3) / SEAOC PV2-2017 (Aerodynamic) |
| **Seismic Screening** | IS 1893 (Part 1): 2016 Clause 6.3.3.1 (Amd 2) | IS 1893 (Part 1): 2016 Cl 6.4.5 (Appended Equipment) | IS 1893 (Part 1): 2016 Cl 6.4.5 (Appended Equipment) | IS 1893 (Part 1): 2016 Cl 6.4.5 & Sliding Kinetics |
| **Critical ULS Gravity** | $1.5\text{DL} + 1.5\text{IL}_{\text{array}} + 1.05\text{IL}_{\text{walkway}}$ | $1.5\text{DL} + 1.5\text{IL}$ (Point load midspan) | $1.5\text{DL} + 1.5\text{IL}$ (Clamp contact) | Self-weight sizing only; live load excluded |
| **Critical ULS Uplift** | $0.9\text{DL} + 1.5\text{WL}_{\text{up}}$ (Table 4 Row 2) | $0.9\text{DL} + 1.5\text{WL}_{\text{up}}$ (Table 4 Row 2) | $0.9\text{DL} + 1.5\text{WL}_{\text{up}}$ (Fastener tear-out) | $0.9\text{DL} + 1.5\text{WL}_{\text{up}}$ (Overturning moment) |
| **Construction Erection**| $1.2\text{DL}_{\text{bare}} + 1.2\text{ER}$ (Table 4 Row 4) | Not critical (Component placement) | Not critical (Direct sheet mount) | Not critical (Pre-cast block placement) |
| **Governing SLS Limit** | Deflection $\le L/250$ (Table 6 Row 1) | Deflection $\le L/200$ (Table 6 Cantilever / Span) | Clamp deformation $\le 2.0\text{ mm}$ under service load| Zero service contact loss ($P_{\text{net,min}} > 0$) |
| **Member Checks Evaluated**| Purlin flexure, shear, uplift, deflection; Rafter flexure, erection; Column buckling | Rail flexure, rail shear, vertical deflection, module end/mid clamp tensile pull-out | Standing-seam clamp tensile pull-out, purlin fixing screw shear, sheet tear-out | Gross sliding resistance, chassis overturning stability, maximum host slab pressure |
| **Host Interface** | Post-installed chemical anchor stanchions to RCC | Chemical anchor stanchions or L-brackets to slab | Mechanical seam clamping (non-piercing) or self-drilling screws | Direct resting on elastomeric EPDM / recycled rubber friction pads |
| **Host Slab Distress** | High stanchion moment ($M_u$), shear ($V_u$), uplift ($T_u$) | Moderate anchor tension ($T_u$) and shear ($V_u$) | Local purlin web crippling, roof sheet distortion | Distributed dead load ($0.65 - 1.20\text{ kN/m}^2$), slab shear |
| **Active Holds (Count)**| **10 Holds** active | **11 Holds** active | **10 Holds** active | **10 Holds** active |

---

## 3. Limit State Check & Governing Equation Inventory

```
========================================================================================================================
LIMIT STATE LOAD COMBINATIONS & FORMULATION SUMMARY (IS 800: 2007 & APPLICABLE CODES)
========================================================================================================================
Combination Code | Combination Formulation                    | Codal Authority            | Structural Engineering Intent
-----------------+--------------------------------------------+----------------------------+--------------------------------------------
ULS-01 (Gravity) | 1.5 DL + 1.5 IL (or leading/accompanying)  | IS 800: 2007 Table 4 Row 1 | Maximum sagging bending and vertical shear.
ULS-02 (Wind Up) | 0.9 DL + 1.5 WL_up                         | IS 800: 2007 Table 4 Row 2 | Reversal of stress, purlin uplift, anchor tension.
ULS-03 (Wind Dn) | 1.2 DL + 1.2 IL + 1.2 WL_down              | IS 800: 2007 Table 4 Row 1 | Combined gravity plus downward wind suction.
ULS-04 (Seismic) | 1.2 DL + 1.2 IL + 1.2 EL_h ± 0.36 EL_v     | IS 1893: 2016 Cl 6.3.2.1   | Spatial earthquake combination (where triggered).
ULS-05 (Seismic) | 0.9 DL ± 1.5 EL_h ± 0.45 EL_v              | IS 1893: 2016 Cl 6.3.2.1   | Minimum gravity stabilizing seismic combination.
ULS-06 (Erection)| 1.2 DL_bare + 1.2 ER                       | IS 800: 2007 Table 4 Row 4 | Bare frame construction stage before module mounting.
SLS-01 (Gravity) | 1.0 DL + 1.0 IL                            | IS 800: 2007 Table 6       | Serviceability vertical deflection under gravity.
SLS-02 (Wind)    | 1.0 DL + 1.0 WL                            | IS 800: 2007 Table 6       | Serviceability lateral sway and wind deflection.
========================================================================================================================
```

---

## 4. Verification Hold Linkage & Release Requirements

The platform enforces 12 canonical verification holds. The table below correlates each mounting system with the holds that govern its validation readiness:

```
========================================================================================================================
SYSTEM-BY-SYSTEM CANONICAL VERIFICATION HOLD MAPPING
========================================================================================================================
Hold Identifier                     | System A | System B | System C | System D | Codal Authority / Audit Status
------------------------------------+----------+----------+----------+----------+-----------------------------------------------
INSPECTION_REQUIRED_HOLD            | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | TNCDBR-2019 Rule 35 / IS 13311 / IS 456
AERODYNAMIC_UNSUPPORTED_HOLD        | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | IS 875 (Part 3): 2015 Clause 8.3 / ASCE 49
WIND_COORD_UNVERIFIED_HOLD          | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | IS 875 (Part 3): 2015 Figure 1 & Annex A
WIND_TRANSFORM_UNVERIFIED_HOLD      | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | REFERENCE PENDING VERIFICATION
VERTICAL_SEISMIC_APPLICABILITY_HOLD | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | IS 1893 (Part 1): 2016 Clause 6.3.3.1 (Amd 2)
LOAD_COMBINATION_PROVISIONAL_HOLD   | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | IS 800: 2007 Table 4 / IS 1893: 2016
FRICTION_UNVERIFIED_HOLD            | EXEMPT   | EXEMPT   | EXEMPT   | ACTIVE   | REFERENCE PENDING VERIFICATION
ALUMINIUM_DERIVATION_HOLD           | EXEMPT   | ACTIVE   | ACTIVE   | EXEMPT   | IS 8147: 1976 / ASTM B221 / AA ADM
FASTENER_TORQUE_UNVERIFIED_HOLD     | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | IS 1367 / ISO 3506 (Grade A2-70 / A4-70)
NUMERICAL_INSTABILITY_HOLD          | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | REFERENCE PENDING VERIFICATION
ASSUMED_DATA_CERTIFICATION_HOLD     | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | TNCDBR-2019 Annexure XVII / SEOR Sign-Off
DRAWING_UNVERIFIED_HOLD             | ACTIVE   | ACTIVE   | ACTIVE   | ACTIVE   | TNCDBR-2019 Rule 38 / NBC 2016
------------------------------------+----------+----------+----------+----------+-----------------------------------------------
TOTAL ACTIVE HOLDS ENFORCED         | 10 HOLDS | 11 HOLDS | 10 HOLDS | 10 HOLDS | ZERO HOLDS RELEASED — AFC HARD-LOCKED
========================================================================================================================
```

---

## 5. Physical Testing & Experimental Evidence Matrix

For any system to transition from Phase 1 Software Readiness to Phase 2 Professional Validation, experimental evidence must be generated in NABL-accredited or statutory testing laboratories:

```
========================================================================================================================
PHYSICAL TESTING & LABORATORY VALIDATION PROTOCOL
========================================================================================================================
Mounting System | Physical Test Required                       | Governing Test Standard   | Minimum Acceptable Criterion
----------------+----------------------------------------------+----------------------------+-------------------------------------------
System A        | Concrete Core Compressive Strength           | IS 516 (Part 1/Sec 1)      | $f_{ck} \ge 20\text{ MPa}$ host slab/column
System A        | Rebound Hammer & Ultrasonic Pulse Velocity   | IS 13311 (Parts 1 & 2)     | Quality Grade: "Good" ($V > 3.5\text{ km/s}$)
System A        | Chemical Anchor Proof Load Pull-Out Test     | IS 800 / EOTA TR 048       | Minimum proof load $1.5 \times T_u$ (no slip)
System B        | Extruded Aluminium Tensile Coupon Test       | IS 1608 (Part 1) / ASTM B557| $f_y \ge 170\text{ MPa}, f_u \ge 205\text{ MPa}$
System B        | Module Mid/End Clamp Static Tension Pull-Out | ASTM E8 / Custom Rig       | Failure load $T_{ult} \ge 2.0 \times T_{demand}$
System C        | Standing-Seam Clamp Slip and Uplift Test     | AISI S904 / Custom Tensile | Slip resistance $\ge 3.5\text{ kN}$ per clamp
System C        | Roof Sheeting Fastener Pull-Out / Tear-Out   | IS 10459 / AISI S905       | Fastener tension $\ge 2.2\text{ kN}$ in 0.5mm BMT
System D        | In-Situ Membrane Static Pull-Slip Friction   | EN 13893 / Contact Test    | $\mu_{\text{design}} \le 0.85 \times \mu_{\text{test,wet}}$
System D        | Boundary Layer Wind Tunnel Aerodynamic Model | ASCE 49-21 / SEAOC PV2     | Net peak suction coefficient calibration
========================================================================================================================
```

---

## 6. Document Sign-Off & Governance Record

- **Prepared By:** Antigravity Structural Verification Auditor
- **Reviewed By:** Structural Systems Engineering Team
- **Endorsement Status:** SPECIFICATION BASELINE ESTABLISHED — AWAITING OWNER VALIDATION PROTOCOL APPROVAL
- **Statutory Restriction:** Not valid for structural steel fabrication, anchor drilling, clamp installation, or ballast placement.
