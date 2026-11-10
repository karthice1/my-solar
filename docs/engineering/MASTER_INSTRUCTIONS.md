# RENSUN SOLAR – STRUCTURAL AUTOMATION MASTER ENGINEERING SPECIFICATIONS

> **Document Classification**: Engineering Design Master Standard  
> **Applicable Project**: RENSUN Solar Automated Rooftop Engineering Platform  
> **Standards Referenced**: IS 875 (Parts 1, 2, 3, 5): 2015, IS 800: 2007 (LSM), IS 801: 1975, IS 811, IS 8147: 1976, IS 456: 2000, IS 4759, IS 277, IS 1893: 2016, EN 1999-1-1 (Eurocode 9), Aluminium Design Manual (ADM), NBC 2016, ISO 9223, ISO 1461, ASTM A1046, fib Bulletin 58 / EN 1992-4  
> **Document Status**: `CLOSED_WITH_RETAINED_ENGINEERING_HOLDS`  
> **Phase 1 Authorization**: `AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION`  
> **Last Updated**: 2026-11-06 (Phase 0.16 Final Technical Reconciliation)

---

## 1. System Overview & Approved Architecture

The RENSUN Solar Structural Automation System is a Python-based modular civil and structural engineering calculation and CAD drafting platform. It extends the existing RENSUN TNEB extraction and solar quotation system by providing automated structural safety validation, member sizing, anchorage verification, building adequacy assessment, and production-ready CAD drawings for solar photovoltaic installations.

### 1.1 Approved Structural Topologies (ALL FOUR MANDATORY — DEC-002)
1. **System Category A — Elevated Steel Rooftop Structures**: 2.0 m to 3.5 m ground/roof clearance frames over accessible flat RCC terraces (columns, rafters, purlins, bracings).
2. **System Category B — Low-Height Aluminium Rail Mounting Systems**: 0.3 m to 0.8 m height frames with extruded aluminium rails (AL6063-T6) and stainless-steel hardware anchored to concrete slabs.
3. **System Category C — Industrial Metal-Sheet Roof Mounting Systems**: Mini-rails or clamp systems attached directly to trapezoidal or standing-seam industrial metal roofs, with purlin load-transfer checks.
4. **System Category D — Ballasted Non-Penetrating Mounting Systems**: Aerodynamically shielded console systems utilizing precast concrete ballast blocks on waterproofing membranes.

### 1.2 Separation of Concerns & Boundary Rules
- The solar energy calculation pipeline (`solar_engine/`, `quotation/`) handles TNEB billing, consumption analysis, annual energy yield (kWh), inverter sizing, financial payback, and PM Surya Ghar subsidies.
- The structural engineering pipeline (`structural_engine/`, `cad_engine/`) handles 3D physical coordinates, dead/live/wind/seismic loads, IS code stress checks, connection details, building slab adequacy, and CAD generation.
- The interface between the two is strictly a clean, unidirectional data transfer: Solar Sizing provides `(panel_count, panel_model, panel_wattage, panel_dimensions, system_capacity_kw)` to the Structural Sizing module. Changes in structural member sizing do not alter energy yield calculations.

---

## 2. Authoritative BIS Wind Load Engineering Engine (DEC-011, DEC-012)

### 2.1 Basic Wind Speed ($V_b$) & Database Traceability (DEC-011):
- Basic wind speeds across India are governed strictly by Figure 1 and Appendix A of IS 875 (Part 3): 2015, categorised into 6 distinct speed zones: $33, 39, 44, 47, 50,$ and $55\text{ m/s}$.
- All automated site lookup algorithms must trace basic wind speed to official administrative district boundaries published in IS 875 (Part 3) Appendix A or explicit coordinate polygons matching Figure 1.

### 2.2 Site Geographic Coordinate Methodology & Screening Buffer:
- Site coordinates (Latitude, Longitude) must be validated against official survey records or verified geocoding services.
- *Screening Buffer Distinction*: A 5 km screening buffer around municipal and coastal boundaries is recommended as a **provisional project screening guideline** to identify transition zones, cyclonic coastal strips ($k_4$), or terrain roughness category changes. This 5 km buffer is explicitly designated as a **project-specific engineering recommendation**, not an explicit statutory mandate in IS 875 (Part 3): 2015.
- *Cyclonic Factor ($k_4$)*: For structures within 60 km of the east coast or designated cyclone-prone areas, cyclonic factor $k_4$ must be determined in strict accordance with Clause 6.3.4 (Table 5).
- *Hold Enforcement*: Retain **`WIND_COORD_UNVERIFIED_HOLD`**.

### 2.3 Three-Tier Aerodynamic Hierarchy (DEC-012):
- *Tier 1 (Governing Indian Standard)*: IS 875 (Part 3): 2015 Clause 7.3 and Table 6 (canopy roofs) / Table 5 (pitch roofs).
- *Tier 2 (Recognised International Supplementary References)*: Where IS 875 (Part 3) does not provide explicit multi-row rooftop shielding or low-tilt aerodynamic coefficients, international supplementary standards are consulted:
  - **ASCE 7-16 / ASCE 7-22** Chapter 29 (Rooftop Solar Panels) and Chapter 31 (Wind Tunnel Procedure);
  - **SEAOC PV2-2017** (*Wind Design for Solar Arrays*).
- *Tier 3 (Boundary Layer Wind Tunnel / CFD Testing)*: Physical boundary layer wind tunnel (BLWT) testing or peer-reviewed CFD matching full-scale array geometry.

### 2.4 Statutory vs Project-Screening Aerodynamic Thresholds:
### Rigorous Recheck of Wind Pressure & Aerodynamic Assumptions

#### 1. Topology-Specific Wind Engineering & Internal Pressure Applicability
Applying enclosed-building internal pressure coefficients ($C_{pi} = \pm 0.2$ or $\pm 0.5$) automatically to open canopies is aerodynamically invalid:
- **System A (Elevated Steel Rooftop Canopy)**:
  - *Aerodynamic Configuration*: Open canopy / free-standing mono-pitch or duo-pitch roof (clearance $2.0 - 3.5\text{ m}$).
  - *Governing Standard*: **IS 875 (Part 3): 2015 Clause 7.4.4 / Table 8 (Canopy Roofs)**.
  - *Internal Pressure Rule*: Internal pressure $C_{pi}$ does **NOT apply**. Wind blows freely underneath the canopy. Wind forces are determined directly from the net pressure coefficient $C_n = C_{pe,top} - C_{pe,bottom}$ under maximum uplift and downward slope configurations.
- **System B (Low-Height Aluminium Rail)**:
  - *Aerodynamic Configuration*: Low-profile arrays mounted close to flat roof ($h/H < 0.1$, tilt $5^\circ - 15^\circ$).
  - *Governing Standard*: Wind flow is governed by the building rooftop boundary layer, separation bubbles, and corner vortices. Internal pressure $C_{pi}$ does NOT apply to the rail/panel array itself. Arrays are designed for localized zone pressures per IS 875 Clause 7.3.3.2 / wind tunnel data (DEC-012).
- **System C (Industrial Metal-Sheet Roof Mounting)**:
  - *Aerodynamic Configuration*: Flush or mini-rail mounting directly fastened to trapezoidal or standing seam sheet.
  - *Governing Standard*: External pressure coefficients $C_{pe}$ on panels follow roof envelope zones (Table 5). **Internal pressure $C_{pi}$ applies strictly to the parent building envelope** (affecting sheet fastener pull-out from purlins), but does NOT act between the top and bottom faces of the PV module.
- **System D (Ballasted Non-Penetrating Rooftop System)**:
  - *Aerodynamic Configuration*: Aerodynamic wind deflectors mitigate front/rear pressure differentials.
  - *Governing Standard*: Empirical wind tunnel pressure coefficients (DEC-012 / SEAOC PV2-2017). Internal pressure $C_{pi}$ is N/A to the array.

#### 2. Adverse Live-Load Conditions for Ballast Stability
- **Uplift, Contact-Loss & Sliding**:
  Live load is stabilizing downward mass. Assuming live load is present during a cyclonic wind storm unconservatively prevents uplift and increases friction sliding resistance.
  *Mandatory Rule*: Ballast uplift, contact-loss, and sliding checks must be evaluated at **ZERO Live Load ($IL = 0$)** with minimum dead load factor **$0.9 DL$**:
  $$N_{\text{eff}} = 0.9 DL_{ballast} - 1.5 WL_{up} \ge 0 \quad (\text{Uplift Safety})$$
  $$F_{\text{fric}} = \mu \cdot (0.9 DL_{ballast} - 1.5 WL_{up}) \ge 1.5 WL_{trans} \quad (\text{Sliding Safety})$$
- **Overturning Stability**:
  Restoring moment is evaluated strictly from minimum dead load ($M_R = 0.9 DL \cdot \frac{B}{2}$); transient live load is strictly excluded.

#### 3. Clarification on Screening Thresholds
- Specific values such as $15^\circ$ tilt, $1.5\text{ m}$ roof setback, or $300\text{ mm}$ overhang are explicitly classified as **provisional project screening guidelines**, not universal codal limits from IS 875 or IS 800.

### 2.5 Local-to-Global Coordinate Transformation & Panel Torsion:
- Aerodynamic pressure coefficients ($C_{pe}, C_{pi}, C_n$) act normal to the tilted plane of the PV module.
- For System A (Open Canopies), net pressure $C_n$ governs and internal pressure $C_{pi}$ does not apply per IS 875 (Part 3) Clause 7.4.4.
- The computational engine must transform normal forces $\mathbf{F}_n$ into global Cartesian components:
  $$F_{global,X} = F_n \cdot \sin\theta \cdot \cos\phi, \quad F_{global,Y} = F_n \cdot \sin\theta \cdot \sin\phi, \quad F_{global,Z} = F_n \cdot \cos\theta$$
- *Panel Torsion / Eccentricity Check*: Aerodynamic center of pressure does not coincide with the geometric centroid. An accidental torsional eccentricity ($e = 0.10 \cdot b_{array}$) must be considered, producing aerodynamic torque:
  $$M_{torsion} = F_n \cdot e$$
- *Hold Enforcement*: Retain **`WIND_TRANSFORM_UNVERIFIED_HOLD`**.

## 3. Comprehensive ULS & SLS Load Combination Matrix (DEC-013)

### 3.1 Dual-Gate Acceptance Framework**:
     - *Gate A (Statutory Code Verification)*: Independent statutory audit verifying partial safety factors ($\gamma_f$), accompanying action coefficients ($\psi$), load directions, algebraic signs, directional seismic spatial rules, and geometric applicability against governing standard provisions (IS 800: 2007 Table 4, IS 875 Part 5: 1987, IS 1893: 2016 Clause 6.3.2.1, Clause 6.3.3.1 [Amended], Clause 6.3.4.1 & Table 10).
     - *Gate B (Numerical Solver Verification)*: Benchmark testing demonstrating that the structural solver correctly generates, combines, and scales load vectors and boundary loads without indexing, sign, or memory array transposition errors.
     - *Mandate*: Numerical solver benchmarking cannot validate code correctness; both verification gates must pass independently prior to certifying the load combination engine.
### 3.2 Amended Vertical Earthquake Criteria (IS 1893: 2016 Clause 6.3.3.1, Amendment No. 2, Nov 2020)**:
     - Under **Clause 6.3.3.1 (as amended by Amendment No. 2, November 2020)** to **IS 1893 (Part 1): 2016**, effects due to vertical earthquake shaking shall be considered for:
       - **a)** The stability of embankments, bridges, and dams; and
       - **b)** The safety of buildings, embankments, bridges, and dams or their components, including in the following seven specific statutory cases:
         1. Structure located in **Seismic Zone IV or V**;
         2. Structure has **vertical or plan irregularities**;
         3. Structure is rested on **soft soil**;
         4. Structures with **long spans**, which cause amplification of oscillations due to their flexibility;
         5. Structure has **large horizontal overhangs of structural members or sub-systems**;
         6. **Prestressed structures**; and
         7. Structures with **prestressed members**.
     - *Clarification on Statutory Triggers vs Project Screening Criteria*:
       - Specific numerical thresholds (such as $12\text{ m}$ span or $1.5\text{ m}$ cantilever overhang) are **NOT statutory BIS code triggers**; they are retained strictly as separately justified **provisional project screening criteria**.
       - Geotechnical factors such as deep pile foundations or liquefiable soil strata are important site considerations under IS 1893 Clause 6.4.4 and IS 2911, but are **NOT** independent statutory triggers under Clause 6.3.3.1.
     - *Four Distinct Engineering Steps for Vertical Seismic Effects*:
       1. **Trigger Applicability Assessment**: Screen site seismic zone (Zone II, III, IV, V), building irregularities, foundation soil type (Type I Rock/Hard, Type II Medium, Type III Soft), member spans, and cantilever aspect ratios against the 7 amended criteria of Clause 6.3.3.1.
       2. **Design Vertical Force Calculation (Clause 6.4.6)**: When triggered, the design vertical seismic acceleration spectral coefficient $A_v$ is calculated as:
          $$A_v = \frac{2}{3} \left( \frac{Z}{2} \frac{I}{R} \frac{S_a}{g} \right)$$
          taking $(S_a/g)_v = 2.5$ for $T \le 0.1\text{ s}$ (or the vertical design acceleration spectrum curve defined in Clause 6.4.6).
       3. **Directional Spatial Combinations (Clause 6.3.4.1)**:
          - *Three-Component Spatial Combinations (When Triggered)*: Evaluated using 24 orthogonal directional permutations (detailed in Section 6 below).
          - *Two-Component Horizontal Combinations (When Vertical Not Triggered)*: Evaluated using 8 planar permutations:
            $$\pm 1.0 \cdot EL_X \pm 0.3 \cdot EL_Y, \quad \pm 0.3 \cdot EL_X \pm 1.0 \cdot EL_Y$$
       4. **Dynamic / Modal Analysis vs Equivalent Static Method**: Equivalent static vertical analysis is standard for regular configurations; dynamic modal response spectrum analysis is required only where vertical array vibration modes exhibit significant dynamic amplification or coupling with host building vertical floor modes.
     - *Hold Enforcement*: If vertical seismic applicability or host-building data is unresolved, enforce **`VERTICAL_SEISMIC_APPLICABILITY_HOLD`**.
### 3.3 Distinct Structural Design Code Routes (IS 800: 2007 Clause 1.1.1 Scope Separation)**:
     - *Scope Boundary of IS 800: 2007 (Clause 1.1.1)*:
       Clause 1.1.1 explicitly restricts the scope of IS 800: 2007 to hot-rolled structural steel sections and steel tubes:
       > *"This standard covers the design and construction of steel structures using hot rolled steel sections and steel tubes... The design of cold formed light gauge steel structural members shall be in accordance with IS 801."*
       Therefore, IS 800: 2007 must **NOT** be used as the sole member-resistance design standard for cold-formed purlins or extruded aluminium components.
     - *Mandatory Separate Design Routes Across Subsystems*:
       1. **Hot-Rolled Structural Steel (System A Canopy Primary Framing: Columns, Primary Rafters, Baseplates)**:
          Governed by **IS 800: 2007** (Limit State Method / Working Stress Method), evaluating section classification (Classes 1–4), tension, compression buckling, flexure, lateral torsional buckling (Clause 8.2.2), and bolted/welded connections (Section 10).
       2. **Cold-Formed Light-Gauge Steel (Purlins, Secondary Rafters, Cold-Rolled Channels)**:
          Governed by **IS 801: 1975** (*Code of Practice for Use of Cold-Formed Light Gauge Steel Structural Members in General Building Construction*).
          - *Supplementary Standards*: **AISI S100-16 / AISI S100-20**, **AS/NZS 4600: 2018**, or **Eurocode 3 (EN 1993-1-3)** for effective section properties and Direct Strength Method (DSM) capacity checks.
          - *Reason for Supplementary Standards*: IS 801: 1975 is based on Allowable Stress Design (ASD) and the 1968 AISI effective width formula. It lacks limit state provisions for modern complex lip-stiffened profiles, distortional buckling, and high-strength steels ($f_y > 450\text{ MPa}$).
          - *Incompatibility / Limitation*: IS 801, AISI S100, and EN 1993-1-3 are **NOT automatically interchangeable**. IS 801 uses ASD with safety factor $1.67$; AISI S100 uses ASD/LRFD with resistance factors $\phi$; EN 1993-1-3 uses Limit State Design with partial material factors $\gamma_{M0}, \gamma_{M1}$. Cross-mixing section properties with IS 800 load combinations requires explicit project calibration and SEOR approval.
       3. **Extruded Aluminium Alloys (Mounting Rails, Solar Module Clamps, Splice Bars)**:
          Governed by **IS 8147: 1976** (*Code of practice for use of aluminium alloys in structures*).
          - *Supplementary Standards*: **Eurocode 9 (EN 1999-1-1: 2007 + A2: 2013)** and **Aluminum Association ADM-2020** (*Aluminum Design Manual*).
          - *Reason for Supplementary Standards*: IS 8147: 1976 uses allowable stress design and lacks modern cross-section classification (Classes 1–4), heat-affected zone (HAZ) softening reductions for welding, and local/distortional buckling rules for thin-walled custom extrusions (Alloy 6063-T6 / 6005-T5).
          - *Incompatibility / Limitation*: IS 8147, EN 1999, and AA ADM are **NOT automatically interchangeable**. IS 8147 uses ASD; EN 1999 uses LSD with material factors $\gamma_{M1}, \gamma_{M2}$; AA ADM uses US LRFD/ASD formats. Direct substitution of allowable stresses into limit state equations without calibration is invalid.
       4. **Fasteners, Chemical Anchors, Gaskets & Roof Interfaces**:
          - Fasteners governed by stainless steel A2-70 / A4-70 (**ISO 3506-1: 2020 / ISO 3506-2: 2020**), with capacities checked per **IS 800: 2007 Section 10**.
          - Post-installed chemical / expansion anchors in concrete governed by **EN 1992-4: 2018** (Design of fastenings for use in concrete) under EAD 330232 / EAD 330499 with valid European Technical Assessment (ETA), complying with **IS 456: 2000**.
          - Elastomeric separation gaskets governed by **ASTM D2000** for EPDM synthetic rubber (60–70 Shore A durometer hardness, UV/ozone resistant) to prevent bimetallic galvanic corrosion.
          - Roof interface: Geotextile protection fleece underlay to prevent chemical migration or mechanical abrasion of rooftop waterproofing membrane (APP/SBS modified bitumen, PVC, or TPO).
### 3.4 Statutory Reference: Published IS 800: 2007 Table 4 Complete Transcription
### Statutory Reference: Published IS 800: 2007 Table 4 Complete Transcription

#### 1. Authoritative Source & Bibliographic Reference
- **Governing Standard**: Bureau of Indian Standards (BIS) *IS 800: 2007 "General Construction in Steel — Code of Practice"* (Third Revision, December 2007).
- **Section & Clause**: Section 3 "General Design Requirements", Clause 3.5.1 ("Load Combinations") and Section 5 "Limit State Design", Clause 5.3.3 ("Design Load Actions"), Page 29.
- **Incorporated Amendments**: Amendment No. 1 (January 2012) and Amendment No. 2 (November 2013).

#### 2. Exact Non-Truncated Column Headings & Column Structure
In the official published BIS standard, Table 4 is structured under two main limit state categories:

**A. Limit State of Strength (Six Action Columns)**:
1. `Dead Load (DL)`
2. `Imposed Load (IL) - Leading`
3. `Imposed Load (IL) - Accompanying`
4. `Crane Load (CL)`
5. `Wind / Earthquake Load (WL/EL)`
6. `Accidental Load (AL)`

**B. Limit State of Serviceability (Five Action Columns)**:
7. `Dead Load (DL)`
8. `Imposed Load (IL) - Leading`
9. `Imposed Load (IL) - Accompanying`
10. `Crane Load (CL)`
11. `Wind / Earthquake Load (WL/EL)`

#### 3. Complete Verbatim Table 4 Transcription (All Rows, Sub-cases, and Footnotes)

| Load Combination | Strength: Dead Load ($DL$) | Strength: Imposed ($IL$) Leading | Strength: Imposed ($IL$) Accompanying | Strength: Crane ($CL$) | Strength: Wind/Earthquake ($WL/EL$) | Strength: Accidental ($AL$) | Serviceability: Dead Load ($DL$) | Serviceability: Imposed ($IL$) Leading | Serviceability: Imposed ($IL$) Accompanying | Serviceability: Crane ($CL$) | Serviceability: Wind/Earthquake ($WL/EL$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Row 1: $DL + IL + CL$** | 1.5 | 1.5 | 1.05 | 1.05 | — | — | 1.0 | 1.0 | 1.0 | 1.0 | — |
| **Row 2: $DL + WL / EL$** | $1.5\,(0.9^*)$ | — | — | — | 1.5 | — | 1.0 | — | — | — | 1.0 |
| **Row 3(a): $DL + IL + CL + WL / EL$** *(IL / CL Leading)* | 1.2 | 1.2 | 1.05 | 1.05 | **0.6** | — | 1.0 | 0.8 | 0.8 | 0.8 | 0.8 |
| **Row 3(b): $DL + IL + CL + WL / EL$** *(WL / EL Leading)* | 1.2 | — | **0.53** | **0.53** | 1.2 | — | 1.0 | — | 0.8 | 0.8 | 0.8 |
| **Row 4: $DL + ER$** | 1.2 | 1.2 | — | — | — | — | — | — | — | — | — |
| **Row 5: $DL + IL + AL$** | 1.0 | **0.35** | **0.35** | — | — | 1.0 | — | — | — | — | — |

*Actual BIS Standard Footnotes (IS 800: 2007 Table 4 Verbatim)*:
* $^*$*This value is to be considered when the dead load contributes to stability against overturning is critical or the dead load causes reduction in stress due to other loads.*
* *NOTE 1 — IL includes live loads, crane surge and impact loads, and erection loads.*
* *NOTE 2 — When Crane Load ($CL$) or Wind / Earthquake Load ($WL/EL$) are leading, the factor for accompanying Imposed Load ($IL$) shall be taken as $0.53$.*
* *NOTE 3 — Wind Load ($WL$) and Earthquake Load ($EL$) shall not be considered as acting simultaneously.*
* *NOTE 4 — The value of $0.9$ for dead load shall be considered when evaluating minimum stability against overturning, sliding, or net tension uplift.*
* *NOTE 5 — Accidental loads ($AL$) include impact from vehicles, blast explosion, and localized structural failure.*

#### 4. Precise Governing Column Mapping for Every RENSUN Solar Combination

| RENSUN Combination ID | Limit State | Combination Name | Governing Table 4 Row | Governing DL Factor | Governing Leading Factor | Governing Accompanying Factor | Governing WL/EL Factor | Governing Table 4 Columns & Codal Application |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **ULS-01** | Strength | Maximum Gravity | Row 1 ($DL + IL + CL$) | 1.5 | 1.5 ($IL_{\text{lead}}$) | 1.05 ($IL_{\text{acc}}$) | — | Columns: Strength DL (1.5), Strength IL Leading (1.5), Strength IL Accompanying (1.05 where simultaneous walkway live load exists on System A). |
| **ULS-02** | Strength | Wind Uplift / Stress Reversal | Row 2 ($DL + WL/EL$) | 0.9* | — | — | 1.5 ($WL_{up}$) | Columns: Strength DL ($0.9^*$ per asterisk footnote for stabilizing dead load), Strength WL/EL (1.5). Governs anchor tension and ballast sliding. |
| **ULS-03** | Strength | Maximum Wind Downward | Row 2 ($DL + WL/EL$) | 1.5 | — | — | 1.5 ($WL_{down}$) | Columns: Strength DL (1.5), Strength WL/EL (1.5). Peak downward wind on rafter/purlin flexure. |
| **ULS-04** | Strength | Combined Wind-Leading | Row 3b ($WL$ Leading) | 1.2 | 1.2 ($WL_{down}$) | 0.53 ($IL_{\text{acc}}$) | 1.2 ($WL$) | Columns: Strength DL (1.2), Strength WL/EL (1.2), Strength IL Accompanying (0.53 per Table 4 Note 2). |
| **ULS-05** | Strength | Combined Live-Leading | Row 3a ($IL$ Leading) | 1.2 | 1.2 ($IL_{\text{lead}}$) | 1.05 ($IL_{\text{acc}}$) | 0.6 ($WL_{down}$) | Columns: Strength DL (1.2), Strength IL Leading (1.2), Strength IL Accompanying (1.05 on System A walkway), Strength WL/EL (0.6). |
| **ULS-06** | Strength | Construction Erection Phase | Row 4 ($DL + ER$) | 1.2 | 1.2 ($ER$) | — | — | Columns: Strength DL (1.2), Strength IL/ER Leading (1.2). Serviceability not applicable during erection. |
| **ULS-ACC-01** | Strength | Accidental Load Case | Row 5 ($DL + IL + AL$) | 1.0 | 0.35 ($IL_{\text{lead}}$) | 0.35 ($IL_{\text{acc}}$) | — | Columns: Strength DL (1.0), Strength IL (0.35), Strength AL (1.0). Accidental/blast limit state per Note 5. |
| **SLS-01** | Serviceability | Gravity Deflection | Row 1 ($DL + IL + CL$) | 1.0 | 1.0 ($IL$) | 1.0 ($IL$) | — | Columns: Serviceability DL (1.0), Serviceability IL Leading (1.0), Serviceability IL Accompanying (1.0). Deflection screening ($\delta \le L/250$). |
| **SLS-02** | Serviceability | Wind Uplift Deflection | Row 2 ($DL + WL/EL$) | 1.0 | — | — | 1.0 ($WL_{up}$) | Columns: Serviceability DL (1.0), Serviceability WL/EL (1.0). Dynamic upward deflection screening ($\delta \le L/200$). |
| **SLS-03** | Serviceability | Wind Downward Deflection | Row 2 ($DL + WL/EL$) | 1.0 | — | — | 1.0 ($WL_{down}$) | Columns: Serviceability DL (1.0), Serviceability WL/EL (1.0). Downward beam/rail deflection screening. |
| **SLS-04** | Serviceability | Combined Wind + Live | Row 3 ($DL + IL + CL + WL$) | 1.0 | 0.8 ($IL$) | 0.8 ($IL$) | 0.8 ($WL$) | Columns: Serviceability DL (1.0), Serviceability IL (0.8), Serviceability WL/EL (0.8). Combined serviceability deflection. |
| **ULS-EQ-01 to 08** | Strength | Seismic Schedules | Rows 1, 2, 3 | 1.5 / 1.2 / 0.9 | 1.5 / 1.2 | 1.05 / 0.0 | 1.5 / 1.2 ($EL$) | Cites IS 800 Table 4 WL/EL columns mapped to IS 1893: 2016 Clauses 6.3.2.1 & 6.3.4.1. |

### 3.5 Physical Load-Action Register, Simultaneity Matrix & Reconciled Combinations
### Rigorous Re-Classification of Imposed Actions & Simultaneous Loading Architecture

#### 1. Physical Action Register & Mutual Exclusivity Rules
The RENSUN platform defines five physical variable imposed and construction actions:
- **`ACT-IL-01` (Maintenance Technician Concentrated Point Load)**: $1.0\text{ kN}$ concentrated load placed at the most adverse position (midspan or cantilever tip) of an individual purlin, rail, or walkway grating bar per **IS 875 (Part 2): 1987 Clause 4.1**.
  *Mutual Exclusivity*: On a given individual member span, `ACT-IL-01` and `ACT-IL-02` are **mutually exclusive alternatives**. They represent alternative design checks for the same physical technician access event.
- **`ACT-IL-02` (Distributed Solar Array Maintenance Load)**: $0.75\text{ kN/m}^2$ (for roof slopes $\le 10^\circ$) or $0.40\text{ kN/m}^2$ (for roof slopes $> 10^\circ$) uniformly distributed over the plan area of the PV array per **IS 875 (Part 2): 1987 Table 2**.
  *Load Path*: Transferred from modules $\to$ clamps $\to$ rails $\to$ purlins $\to$ primary rafters $\to$ main columns.
- **`ACT-IL-03` (Host Roof Live Load — Parent Building Slab)**: $1.5\text{ kN/m}^2$ (accessible flat roof) or $0.75\text{ kN/m}^2$ (inaccessible roof except for maintenance) per **IS 875 (Part 2) Table 2**.
  *Load Path*: Directly stresses the parent building reinforced concrete slab outside the array footprint. **Zero load is transferred into the solar frame**. Evaluated strictly under host building slab punching and flexure checks (DEC-007).
- **`ACT-IL-04` (Walkway & Inverter Platform Live Load — System A)**: $2.0 - 3.0\text{ kN/m}^2$ uniformly distributed load or $1.5\text{ kN}$ point load per **IS 875 (Part 2) Table 1**.
  *Physical Location*: Elevated maintenance walkways, inverter platforms, and service catwalks in System A (Elevated Canopy).
  *Load Path*: Walkway grating $\to$ stringers $\to$ canopy primary rafters $\to$ main canopy columns.
  *Simultaneity*: **CAN act simultaneously with array maintenance load (`ACT-IL-02`) on primary rafters and columns**.
- **`ACT-ER-01` (Construction & Erection Temporary Load)**: $1.0\text{ kN}$ point load or temporary hoisting bracket loads per **IS 800: 2007 Clause 3.5.1**.
  *Mutual Exclusivity*: Operates strictly during the pre-commissioning phase on unbolted frames and hoisted module bundles. **Mutually exclusive with all operational live loads (`ACT-IL-01` to `04`)**.

#### 2. Reconciliation of IS 800 Table 4 Note 1 with Dedicated Erection Load Combination
- **Codal Ambiguity**: Note 1 of Table 4 states: *"IL includes live loads, crane surge and impact loads, and erection loads."*
- **Rigorous Technical Resolution**:
  1. *General Terminology*: Note 1 indicates that the generic acronym $IL$ encompasses all transient non-permanent gravity forces in broad analytical descriptions.
  2. *Dedicated Statutory Limit State*: However, Table 4 explicitly establishes **Row 4 ($DL + ER$)** as an independent, dedicated combination for erection. It prescribes partial safety factor $\gamma_f = 1.2$ on Dead Load and $\gamma_f = 1.2$ on Erection Load ($ER$), with Serviceability designated as not applicable (`—`).
  3. *Structural Phase Demarcation*: The platform strictly separates **Operational Limit States** (where `ACT-IL-01`, `02`, `04` act under Table 4 Rows 1, 3a, 3b) from the **Construction Limit State** (`ULS-06`, where `ACT-ER-01` acts under Table 4 Row 4). Erection and operational live loads never occur concurrently.

#### 3. Separate Load Combination Cases by Structural Subsystem

1. **Local Purlins and Rails (Systems A, B, C, D)**:
   - Evaluated for the governing envelope of the alternative maintenance loading conditions:
     $$\text{ULS}: \quad \max \left( 1.5 DL + 1.5 \cdot \text{ACT-IL-01}, \; 1.5 DL + 1.5 \cdot \text{ACT-IL-02} \right)$$
     $$\text{SLS}: \quad \max \left( 1.0 DL + 1.0 \cdot \text{ACT-IL-01}, \; 1.0 DL + 1.0 \cdot \text{ACT-IL-02} \right)$$
   - Purlin spans $\le 1.8\text{ m}$ are typically governed by the $1.0\text{ kN}$ concentrated technician load (`ACT-IL-01`); longer continuous spans are governed by distributed load (`ACT-IL-02`).
2. **System A Walkway Members (Catwalk Grating & Stringers)**:
   - Governed exclusively by platform live load (`ACT-IL-04`):
     $$\text{ULS}: \quad 1.5 DL_{walkway} + 1.5 \cdot \text{ACT-IL-04}$$
     $$\text{SLS}: \quad 1.0 DL_{walkway} + 1.0 \cdot \text{ACT-IL-04}$$
3. **System A Primary Framing (Primary Rafters and Main Columns)**:
   - Primary canopy framing supports BOTH the tributary solar array area AND the attached service walkway.
   - **Codal Factor Derivation (IS 800: 2007 Table 4)**:
     When multiple variable imposed loads act simultaneously, IS 800 Table 4 differentiates between **Leading Imposed Action** and **Accompanying Imposed Action**:
     * *Case A (Array Live Load Leading)*:
       $$\text{ULS Gravity (Row 1)}: \quad 1.5 DL + 1.5 \cdot \text{ACT-IL-02} + 1.05 \cdot \text{ACT-IL-04}$$
       $$\text{ULS Live+Wind (Row 3a)}: \quad 1.2 DL + 1.2 \cdot \text{ACT-IL-02} + 1.05 \cdot \text{ACT-IL-04} + 0.6 WL_{down}$$
     * *Case B (Walkway Live Load Leading)*:
       $$\text{ULS Gravity (Row 1)}: \quad 1.5 DL + 1.5 \cdot \text{ACT-IL-04} + 1.05 \cdot \text{ACT-IL-02}$$
       $$\text{ULS Live+Wind (Row 3a)}: \quad 1.2 DL + 1.2 \cdot \text{ACT-IL-04} + 1.05 \cdot \text{ACT-IL-02} + 0.6 WL_{down}$$
     * *Case C (Wind Leading — Row 3b)*:
       $$\text{ULS Wind-Leading}: \quad 1.2 DL + 1.2 WL_{down} + 0.53 \cdot \text{ACT-IL-02} + 0.53 \cdot \text{ACT-IL-04}$$
       *(Applying companion factor $0.53$ to all accompanying variable actions per Table 4 Note 2)*.
     * *Serviceability (Row 3)*:
       $$\text{SLS Combined}: \quad 1.0 DL + 0.8 WL + 0.8 \cdot \text{ACT-IL-02} + 0.8 \cdot \text{ACT-IL-04}$$
4. **Host Roof Slab (Parent Building RCC Slab)**:
   - Stressed by stanchion/column concentrated reaction forces ($R_{DL}, R_{IL}, R_{WL}$) combined with host roof slab live load (`ACT-IL-03`) acting on the slab surface outside the stanchion baseplates:
     $$\text{ULS Punching/Bending}: \quad 1.5 \cdot R_{DL} + 1.5 \cdot R_{IL} + 1.5 \cdot \text{ACT-IL-03}$$
5. **Construction-Stage Framing (All Topologies)**:
   - Governed by temporary erection forces (`ACT-ER-01`) under Table 4 Row 4:
     $$\text{ULS Erection}: \quad 1.2 DL_{bare\_frame} + 1.2 \cdot \text{ACT-ER-01}$$

### 3.6 Dedicated Seismic Load Combinations Schedule & Mathematical Derivation
### Rigorous Seismic Vertical-Action & Normal Force Formulation

#### 1. Independent Signed Directional Response Effects
In dynamic response analysis, the seismic action is characterized by three independent orthogonal spatial response vectors:
- $E_X$: Maximum elastic structural response effect (axial force, shear, or bending moment) due to design lateral ground motion along global X-axis.
- $E_Y$: Maximum elastic structural response effect due to design lateral ground motion along global Y-axis.
- $E_Z$: Maximum elastic structural response effect due to design vertical earthquake acceleration along global Z-axis ($E_v$).

#### 2. Elimination of Universal Vertical Coefficient Approximation
- In previous drafts, an illustrative shorthand ($0.9 DL - 0.45 E_Z$) was erroneously cited across all stability checks.
- **Correction**: Under IS 1893: 2016 Clause 6.3.4.1, the vertical component coefficient changes fundamentally between **Horizontal-Dominant** and **Vertical-Dominant** shaking regimes:
  1. *Horizontal-Dominant Cases (Cases 01 to 16)*: The vertical component carries spatial coefficient **$0.3$**. Under Combination 3 ($\gamma_f = 1.5$), the vertical contribution is $1.5 \times 0.3 E_Z = \mathbf{0.45 E_Z}$. Under Combination 2 ($\gamma_f = 1.2$), it is $1.2 \times 0.3 E_Z = \mathbf{0.36 E_Z}$.
  2. *Vertical-Dominant Cases (Cases 17 to 24)*: The vertical component carries spatial coefficient **$1.0$**. Under Combination 3 ($\gamma_f = 1.5$), the vertical contribution is $1.5 \times 1.0 E_Z = \mathbf{1.5 E_Z}$! Under Combination 2 ($\gamma_f = 1.2$), it is $1.2 \times 1.0 E_Z = \mathbf{1.2 E_Z}$!

#### 3. Mathematical Recalculation of Effective Normal Force, Uplift, Sliding & Overturning

Let $W_{DL}$ be the characteristic dead weight, $W_{IL}$ be the characteristic live load, and $E_{Z,vert}$ be the characteristic vertical seismic force ($E_Z = A_v \cdot W$).

| Seismic Shaking Regime | Dominant Axis & 24-Case Group | Governing Load Combination ID & Formula | Spatial Vertical Coefficient ($c_v$) | Net Combination Factor ($\gamma_f \cdot c_v$) | Effective Normal Reaction Force ($N_{\text{eff}}$) | Uplift & Contact-Loss Condition | Ballast Sliding Resistance ($F_{\text{fric}}$) | Overturning Moment Effect ($M_{\text{OT}}$) |
|:---|:---:|:---|:---:|:---:|:---|:---|:---|:---|
| **Horizontal-Dominant (Upward Vertical)** | $E_X$ or $E_Y$ Dominant<br>(Cases 01, 03, 05, 07, 09, 11, 13, 15) | **ULS-EQ-05 / 06 (Comb 3)**:<br>$0.9 DL - 1.5 \cdot (0.3 E_Z)$ | $+0.3$ (Upward) | $-0.45$ | $\mathbf{N_{\text{eff}} = 0.9 W_{DL} - 0.45 E_Z}$ | Uplift occurs if:<br>$0.45 E_Z \ge 0.9 W_{DL}$ | $F_{\text{fric}} = \mu \cdot (0.9 W_{DL} - 0.45 E_Z)$<br>Must exceed lateral base shear $1.5 E_{h,1}$ | Restoring moment $M_R = 0.9 W_{DL} \cdot \frac{B}{2}$ reduced by $0.45 E_Z \cdot \frac{B}{2}$ |
| **Horizontal-Dominant (Downward Vertical)** | $E_X$ or $E_Y$ Dominant<br>(Cases 02, 04, 06, 08, 10, 12, 14, 16) | **ULS-EQ-01 / 02 (Comb 2)**:<br>$1.2 DL + 1.2 IL + 1.2 \cdot (0.3 E_Z)$ | $-0.3$ (Downward) | $+0.36$ | $\mathbf{N_{\text{eff}} = 1.2 W_{DL} + 1.2 W_{IL} + 0.36 E_Z}$ | Compression; no contact-loss. | Maximum normal force increases friction sliding resistance. | Peak downward compressive reaction on foundation/slab pads. |
| **Vertical-Dominant (Upward Vertical)** | $E_Z$ Dominant<br>(Cases 17, 19, 21, 23) | **ULS-EQ-08 (Comb 3)**:<br>$0.9 DL - 1.5 \cdot (1.0 E_Z)$ | $+1.0$ (Upward) | **$-1.50$** | $\mathbf{N_{\text{eff}} = 0.9 W_{DL} - 1.50 E_Z}$ | **Peak Severe Uplift**:<br>Uplift occurs if $1.5 E_Z \ge 0.9 W_{DL}$ ($A_v \ge 0.60$) | **Complete Loss of Friction**:<br>If $N_{\text{eff}} \le 0$, $F_{\text{fric}} = 0$ (array floats / separates). | Anchor bolts must resist net uplift tension $T = 1.5 E_Z - 0.9 W_{DL}$. |
| **Vertical-Dominant (Downward Vertical)** | $E_Z$ Dominant<br>(Cases 18, 20, 22, 24) | **ULS-EQ-07 (Comb 2)**:<br>$1.2 DL + 1.2 IL + 1.2 \cdot (1.0 E_Z)$ | $-1.0$ (Downward) | **$+1.20$** | $\mathbf{N_{\text{eff}} = 1.2 W_{DL} + 1.2 W_{IL} + 1.20 E_Z}$ | Peak downward inertia; no contact-loss. | High normal compression enhances friction resistance. | Governs rafter midspan bending and slab punching shear capacity. |

#### 4. Demarcation Between Two-Component & Three-Component Regimes
- **Two-Component Regime (IS 1893: 2016 Clause 6.3.4.2)**:
  Applies exclusively when vertical earthquake shaking is NOT triggered under Clause 6.3.3.1. Vertical acceleration is zero ($E_Z = 0$). Effective normal reaction is strictly governed by gravity:
  $$N_{\text{eff, min}} = 0.9 W_{DL} \quad (\text{Comb 3}), \qquad N_{\text{eff, max}} = 1.2 W_{DL} + 1.2 W_{IL} \quad (\text{Comb 2})$$
  Evaluated under the **8 horizontal orthogonal permutations**: $\pm 1.0 E_X \pm 0.3 E_Y$ and $\pm 0.3 E_X \pm 1.0 E_Y$.
- **Three-Component Regime (IS 1893: 2016 Clause 6.3.4.1)**:
  Applies whenever vertical seismic shaking is statutorily triggered under Clause 6.3.3.1. Evaluated under the **24 spatial permutations** using the exact coefficients derived in the table above.

### 3.7 The 24 Spatial Permutations Table & Statutory Applicability Evidence
### Detailed Legal Basis & Applicability Framework for 24 Spatial Combinations

#### 1. Authoritative Text of IS 1893 (Part 1): 2016 Provisions
- **Clause 6.3.3.1 (Amended by Amendment No. 2, November 2020)**:
  > *"Effects due to vertical earthquake shaking shall be considered for:*
  > *a) The stability of embankments, bridges, and dams; and*
  > *b) The safety of buildings, embankments, bridges, and dams or their components, including in the following cases:*
  > *1) Structure located in Seismic Zone IV or V;*
  > *2) Structure has vertical or plan irregularities;*
  > *3) Structure is rested on soft soil;*
  > *4) Structures with long spans, which cause amplification of oscillations due to their flexibility;*
  > *5) Structure has large horizontal overhangs of structural members or sub-systems;*
  > *6) Prestressed structures; and*
  > *7) Structures with prestressed members."*
- **Clause 6.3.4.1 (Three-Component Spatial Combinations)**:
  > *"When effects due to vertical earthquake shaking are considered along with those due to horizontal earthquake shaking, the maximum design response S shall be calculated as:*
  > *a) $S = \pm S_x \pm 0.3 S_y \pm 0.3 S_z$*
  > *b) $S = \pm 0.3 S_x \pm S_y \pm 0.3 S_z$*
  > *c) $S = \pm 0.3 S_x \pm 0.3 S_y \pm S_z$*
  > *where $S_x$, $S_y$ and $S_z$ are response quantities due to design earthquake shaking along horizontal orthogonal axis X, horizontal orthogonal axis Y, and vertical axis Z, respectively."*
- **Clause 6.3.4.2 (Two-Component Combinations)**:
  > *"When effects due to vertical earthquake shaking are not considered, the maximum design response S shall be calculated as:*
  > *a) $S = \pm S_x \pm 0.3 S_y$*
  > *b) $S = \pm 0.3 S_x \pm S_y$"*

#### 2. Separation of Statutory Mandate vs Voluntary Project Conservatism
1. **Statutory Baseline**:
   - For regular solar structures in **Zone II or Zone III** on hard or medium soil without cantilevers or long spans, **IS 1893: 2016 Clause 6.3.4.2 applies exclusively**. The legal code requirement is satisfied by the **8 horizontal orthogonal permutations**. Vertical earthquake analysis is **not statutorily mandated**.
   - If any of the 7 conditions of Clause 6.3.3.1 apply (e.g. Zone IV/V or cantilevered module overhangs), the **24 spatial combinations of Clause 6.3.4.1 become legally mandatory**.
2. **Voluntary RENSUN Project Conservatism**:
   - In RENSUN Solar structural processing, evaluating 24 spatial permutations for low-height rooftop arrays in Zone II/III where vertical seismic is not triggered is explicitly designated as a **voluntary, project-specific conservative quality control**, NOT an exclusive statutory mandate.

## 4. Connection Modeling, Joint Flexibility & Failure Modes (DEC-014)

### 4.1 Separation of Sliding-Initiation from Post-Slip Residual Resistance:
- **Sliding Initiation (Peak Friction $\mu_{peak}$)**: Evaluated for serviceability limit states (SLS) to prevent micro-slip that could damage waterproofing membranes or solar cabling.
- **Post-Slip Resistance (Residual Friction $\mu_{residual}$)**: Evaluated for ultimate limit states (ULS) to prevent dynamic runaway under peak wind pulses once initial static bond is broken.

### 4.2 Statistical Derivation (EN 1990:2002 Annex D Table D.1):
Characteristic friction is assessed using **EN 1990:2002 Annex D Table D.1 statistical fractile factors $k_n$** for a normal distribution with coefficient of variation ($V_x$) unknown ($5\%$ fractile, $75\%$ confidence):
$$\mu_k = \mu_{mean} - k_n \cdot s$$
Table D.1 explicit values ($V_x$ unknown):
$n = 3 \implies k_n = 3.37$, $n = 4 \implies k_n = 2.63$, $n = 5 \implies k_n = 2.33$, $n = 6 \implies k_n = 2.18$, $n = 8 \implies k_n = 2.00$, $n = 10 \implies k_n = 1.92$, $n = 20 \implies k_n = 1.76$, **$n = 30 \implies k_n = 1.73$** (asymptotic $k_\infty \approx 1.64$).

### 4.3 Exact Scope of EN 1990 D7.2 and D8.2 & Factor Derivation:
- *Scope of EN 1990 Provisions*:
  - **Clause D7.2**: Formulates general conversion factor $\eta_d$ to account for differences between laboratory test setups and real-world conditions ($X_d = \eta_d X_k / \gamma_m$).
  - **Clause D8.2**: Outlines the standard statistical evaluation procedure for resistance models and error terms; **it does NOT prescribe a universal scalar number for $\gamma_{Rd}$**.
- *Design Resistance Formulation*:
  $$\mu_d = \frac{\eta_d \cdot \mu_k}{\gamma_{Rd} \cdot \gamma_{M,friction}}$$
- *Standard-Supported vs Project-Specific Factors*:
  - Standard-Supported: Table D.1 $k_n$ fractile factors, Clause D7.2 conversion concept, Clause D8.2 model evaluation procedure.
  - Project-Specific Assumptions: numerical values for $\eta_d$ (environmental conditioning: thermal cycling, moisture, dust, UV, micro-vibrations), $\gamma_{Rd}$ (mechanics idealizations: slab surface waviness, ballast tray flexure, stick-slip), and $\gamma_{M,friction} = 1.5$ (provisional baseline adapted from geotechnical sliding analogies in IS 1904 / IS 456, not a universal constant).
- *Anti-Double-Counting*: Statistical scatter ($k_n$), environmental degradation ($\eta_d$), modeling idealizations ($\gamma_{Rd}$), and target safety ($\gamma_{M,friction}$) are strictly separated without compounding.
- Retains **`FRICTION_UNVERIFIED_HOLD`**.

---

## 5. Material-Specific Aluminium Design Standards (DEC-015)

### 5.1 Standards Adoption & Fastener Qualification:
- *Governing Code*: **Eurocode 9 (EN 1999-1-1: 2007)** is adopted as the Tier 2 design standard because IS 8147: 1976 lacks design provisions for modern thin-walled extruded cross-sections.
- *Product-Specific Test Applicability*: **EAD 330030-00-0601** and **EOTA TR 063** (*Fastening Screws for Metal Members and Sheeting*) are qualified strictly for metallic self-drilling and self-tapping screws connecting metal sheet and thin-gauge metal framing.
- *Prohibition on Indiscriminate Equation Transfer*:
  - **Do NOT automatically transfer thin-steel-sheet test equations to proprietary aluminium extrusions!**
  - Proprietary aluminium solar rail profiles feature complex cross-sections, localized screw-channel geometry, screw-boss lips, distinct alloy ductility, and localized web flexure that differ fundamentally from cold-formed thin steel sheets. Fastener capacities in proprietary aluminium rails must be validated against actual extrusion geometry and product-specific component test reports.
- *Timber Standards Purged*: ASTM D1761 and EN 14592 are permanently purged.

### 5.2 Linear Tension-Shear Interaction Equation (Provisional):
Baseline interaction check:
$$\left(\frac{N_{Ed}}{N_{Rd}}\right) + \left(\frac{V_{Ed}}{V_{Rd}}\right) \le 1.0$$
- *Qualification*: Provisional baseline; **NOT described as universally conservative without evidence**. In thin-walled cold-formed or extruded profiles subject to prying forces, localized web crippling, or combined bearing-tearout, interaction can be non-linear. Non-linear exponents ($\alpha, \beta$) require empirical test envelope validation.

### 5.3 Explicit Definition of Tension and Shear Failure Modes:
- **Tension Resistances ($N_{Rd}$)**:
  - $N_{o,Rd}$: Screw pull-out resistance from the aluminium rail or purlin flange (EOTA TR 063 Eq. 2.1);
  - $N_{u,Rd}$: Pull-over / head pull-through resistance of the connected clamp or sheet (EOTA TR 063 Eq. 2.2);
  - $N_{t,Rd}$: Fastener tensile rupture resistance across the threaded core;
  - $N_{pl,Rd}$: Localized plastic flexural yielding / prying resistance of the rail channel lips.
- **Shear Resistances ($V_{Rd}$)**:
  - $V_{b,Rd}$: Hole bearing / tilting resistance of the screw in thin profile walls (EN 1999-1-4 Clause 8.5.2);
  - $V_{s,Rd}$: Fastener shear rupture resistance across the shank/threads;
  - $V_{net,Rd}$: End-distance / edge-distance shear tear-out resistance of the aluminium rail profile.

### 5.4 Test Configurations & Provisional Status:
- Capacities depend strictly on extrusion alloy (AW-6063 vs AW-6005A), temper (T6 vs T5), measured wall thickness ($t$), screw diameter, thread pitch, and edge distances ($e_1, e_2$).
- Fastener grade (A2-70), torque (12–15 Nm), and AL6063-T6 properties remain provisional under **`ALUMINIUM_DERIVATION_HOLD`** and **`FASTENER_TORQUE_UNVERIFIED_HOLD`**.

## 6. Solar Module Overhang Multi-Criteria Engineering Evaluation (DEC-006)

An unconditional 300 mm hard limit is **NOT** a universal structural acceptance criterion. Overhang sizing is verified by rigorous structural engineering mechanics:
1. **Cantilever Bending Moment Check**:
   $$M_{cantilever} = \frac{w_{uplift} \cdot L_{cantilever}^2}{2} \le M_{rd,frame}$$
2. **Cantilever Tip Deflection Check**:
   $$\delta_{tip} = \frac{w_{uplift} \cdot L_{cantilever}^4}{8 \cdot E_{al} \cdot I_{frame}} \le \frac{L_{cantilever}}{150}$$
3. **Uplift Reaction on Outermost Clamps**:
   $$F_{clamp, uplift} \le F_{clamp, allowable}$$
4. **Module Manufacturer Certified Clamping Zones**:
   - The cantilever distance $L_{cantilever}$ must strictly position the mounting clamps within the module manufacturer’s certified mounting zones (e.g. $L/4 \pm 50 \text{ mm}$ for 4-point clamping per IEC 61215/61730).
5. **Warning Threshold**: Overhang $> 300 \text{ mm}$ triggers an advisory UI warning to review clamp zones, but is permitted if all structural checks pass.

---

## 7. Corrosion Protection & Galvanization Specifications (DEC-004)

### 7.1 Hot-Dip Galvanizing (HDG) to IS 4759 / ISO 1461
Coating mass and thickness specified strictly by component thickness ($t$):
- **$t \ge 6 \text{ mm}$ (Baseplates, column flanges, thick cleats)**: Minimum average coating thickness **$86 \ \mu\text{m}$** (coating mass **$610 \text{ g/m}^2$**).
- **$3 \text{ mm} \le t < 6 \text{ mm}$ (SHS/RHS columns, ISMC rafters)**: Minimum average coating thickness **$70 \ \mu\text{m}$** (coating mass **$500 \text{ g/m}^2$**).
- **$1.5 \text{ mm} \le t < 3 \text{ mm}$ (Light structural tubing, angles, brackets)**: Minimum average coating thickness **$55 \ \mu\text{m}$** (coating mass **$390 \text{ g/m}^2$**).
- **Threaded Fasteners & Anchor Rods (IS 1367 Pt 13 / ISO 10684)**: Minimum average coating thickness **$45 \ \mu\text{m}$** ($325 \text{ g/m}^2$).

### 7.2 Pre-Galvanized Coated Sheet (IS 277)
- Cold-formed C/Z purlins: Defined coating class **Class Z275** ($275 \text{ g/m}^2$ total both sides). Permitted for inland exposures (ISO 9223 C1 to C3).

### 7.3 Zinc-Aluminium-Magnesium (Zn-Al-Mg / PosMAC) to ASTM A1046 / EN 10346
- Maintained as an independent, high-durability alloy coating specification (e.g. ZM310 / PosMAC 3.0 with $310 \text{ g/m}^2$).
- **Strict Rule**: The system shall **NEVER assume equivalence between PosMAC and standard Z275 galvanization**. PosMAC provides superior cut-edge galvanic passivation and 3x–5x higher salt-spray corrosion resistance.

### 7.4 ISO 9223 Environmental Exposure Categories
- **C1 / C2 (Low)**: Rural, low pollution. Standard Z275 or HDG $55 \ \mu\text{m}$.
- **C3 (Medium)**: Urban / light industrial (Salem, Coimbatore, Erode). Minimum Z275 or HDG $55\text{--}70 \ \mu\text{m}$.
- **C4 (High)**: Industrial / coastal belt with moderate salinity. Minimum HDG $70\text{--}86 \ \mu\text{m}$ or PosMAC ZM310.
- **C5-M (Very High Marine)**: Coastal belt within 5 km of shoreline (Chennai, Cuddalore, Thoothukudi). Requires HDG $86 \ \mu\text{m}$ + epoxy barrier topcoat (Duplex System) or marine-grade anodized aluminium ($25 \ \mu\text{m}$).

---

## 8. Context-Specific Waterproofing & Roof Penetration Details (DEC-009)

1. **Flat Concrete Roof with Bitumen / Polymeric Waterproofing Membrane**: Cast-in-situ concrete stub pedestals (height 100–150 mm) anchored to structural slab with dual-layer elastomeric waterproofing collar, or chemical anchor rods sealed with polyurea/polyurethane mastic.
2. **Flat Concrete Roof with Tiled / Screed Finish**: Direct chemical anchor studs with UV-resistant EPDM compression boots, sealed with structural silicone and counter-flashing.
3. **Industrial Metal Roof (Trapezoidal / Sandwich)**: Self-drilling screws anchored strictly into purlins or crowns, isolated with vulcanized EPDM bonded washers; no concrete pedestals.
4. **Industrial Standing Seam Roof (Klip-Lok)**: Non-penetrating aluminium seam clamps providing pure friction grip; **zero sheet penetrations**.
5. **Ballasted Systems**: Non-penetrating design utilizing dense rubber protection pads (thickness $\ge 10 \text{ mm}$) to distribute ballast weight and protect underlying waterproofing membranes.

---

## 9. Existing Building Verification & Five-Tier Data Provenance (DEC-007, DEC-016)

### 9.1 Decoupling Evidence Provenance from Engineering Review Status
Every structural parameter ingested must carry two independent attributes:
- **Dimension A: Evidence Provenance (Source Quality)**:
  - `PROV_MEASURED` — On-site calibrated physical survey.
  - `PROV_DOCUMENTED` — Certified as-built structural drawings.
  - `PROV_TESTED` — Certified non-destructive test reports (rebound hammer, covermeter, core compression).
  - `PROV_ASSUMED` — Estimated preliminary parameter.
- **Dimension B: Engineering Review Status**:
  - `REV_UNREVIEWED` — Pending evaluation.
  - `REV_REJECTED` — Rejected by engineer.
  - `REV_ACCEPTED_WITH_CONDITIONS` — Reviewed and accepted under documented professional caveats.
- *Core Principle*: An engineer's review or acceptance does **NOT** change a `PROV_ASSUMED` value into `PROV_MEASURED` or `PROV_TESTED`. It remains visibly tagged as an assumption on all calculation sheets and drawing general notes.

### 9.2 Mandatory Verification Hold (`INSPECTION_REQUIRED_HOLD`)
- The software shall **NEVER use assumed default values (M20 concrete, 100 mm slab) to declare an existing roof safe**.
- Structural adequacy certification is **strictly blocked** if any critical structural parameter remains at `PROV_ASSUMED`.
- Missing reinforcement triggers an automated certification hold and generates a Pre-Installation Civil Inspection Checklist.

### 9.3 Inspection & Verification Workflows
- **RCC Slabs**: Flexural capacity, one-way shear, two-way punching shear ($\tau_v \le k_s \cdot 0.25 \sqrt{f_{ck}}$), crack width and deflection audit.
- **RCC Beams & Columns**: Axial-flexural capacity ($P_u - M_u$ interaction per SP 16).
- **Building Foundations**: Additional column load transfer checked against allowable soil bearing capacity ($SBC$).
- **Industrial Metal Roof Purlins**: Combined bending stress $\sigma_{combined} \le 0.66 f_y$, shear, lateral-torsional stability, sag rod presence, and sheet screw pullout.

---

## 10. Four-Level Structural Solver Validation Strategy (DEC-010, DEC-017)

### 10.1 Four Validation Levels (DEC-010):
- **Level 1 (Analytical Closed-Form Benchmarks)**: Euler-Bernoulli beam theory, Roark formulas, classical plate bending solutions ($w_{max} = \alpha q a^4 / D$).
- **Level 2 (Independent Open-Source Cross-Solver Comparison)**: Benchmarking against Code_Aster, OpenSees, and Frame3DD to ensure consistency.
- **Level 3 (Experimental Laboratory Validation)**: Comparison against wind tunnel surface pressure taps and physical pull-out load-displacement curves.
- **Level 4 (Field Monitoring & Commissioning Data)**: Strain gauge and displacement sensor validation under real storm events.

### 10.2 Dimensional Matrix Stability, Conditioning & Equilibrium Diagnostics (DEC-017)

### Reconciled Numerical Diagnostics & Matrix Stability Architecture

#### 1. Comprehensive Matrix Regimes & Tailored Numerical Remedies
The platform strictly differentiates mathematical existence, numerical factorization success, and eigen-solver convergence:

| Numerical / Structural Condition | Mathematical Definition | Solver Diagnostic & Symptom | Tailored Engineering & Numerical Remedy |
|:---|:---|:---|:---|
| **Redundant Constraints** | Kinematic boundary conditions over-constraining the same DOF ($\text{rank}(\mathbf{C}) < m$). | Zero pivots in constraint Jacobian or artificial reaction force spikes. | Remove duplicate boundary restraints; enforce linear independence of constraint equations before assembling $\mathbf{K}_{ff}$. |
| **Massless Degrees of Freedom** | DOFs with structural stiffness but zero lumped inertia ($K_{ii} > 0, M_{ii} = 0$). | Standard eigenvalue solvers encounter infinite eigenvalues ($\lambda \to \infty$). | **Guyan Static Condensation**: Partition into master ($m$) and slave ($s$) DOFs: $\mathbf{K}_{cond} = \mathbf{K}_{mm} - \mathbf{K}_{ms}\mathbf{K}_{ss}^{-1}\mathbf{K}_{sm}$. (Valid because $\mathbf{K}_{ss}$ is non-singular). |
| **Common Nullspace Mechanism** | Spatial vectors $\mathbf{v}$ satisfying simultaneously $\mathbf{K}\mathbf{v} = \mathbf{0}$ and $\mathbf{M}\mathbf{v} = \mathbf{0}$ (unconstrained massless mechanism). | $\mathbf{K}_{ss}$ is singular; Guyan condensation fails with zero pivot. | **Topological Model Repair**: Guyan condensation cannot resolve a common nullspace. Must add physical bracing/connections or apply algebraic nullspace projection. |
| **Kinematic Mechanisms with Mass** | Displacements $\mathbf{u}_{mech}$ with zero strain energy ($\mathbf{u}^T \mathbf{K} \mathbf{u} = 0$), but possessing mass ($M_{ii} > 0$). | Zero-frequency eigenvalues ($\omega \approx 0$); indefinite/zero pivots during static solve. | Re-triangulate framing; add diagonal cross-bracing; eliminate collinear internal pin hinges. |
| **Rigid-Body Modes** | Global unconstrained translation/rotation of entire system ($\mathbf{K}\boldsymbol{\phi} = \mathbf{0}$, but $\mathbf{M} \succ 0$). | $\det(\mathbf{K}) = 0$, but pencil $(\mathbf{K}, \mathbf{M})$ is strictly regular ($\det(\mathbf{K} - \lambda \mathbf{M}) \not\equiv 0$). | **Shift-and-Invert Lanczos**: Apply non-zero spectral shift $\sigma \neq 0$ (e.g. $\sigma = 1.0$), transforming operator to $(\mathbf{K} - \sigma \mathbf{M})^{-1} \mathbf{M}$. Robustly extracts zero-frequency modes. |
| **Singular Matrix Pencils** | Matrix pencil satisfies $\det(\mathbf{K} - \lambda \mathbf{M}) \equiv 0 \quad \forall \lambda \in \mathbb{C}$. | $(\mathbf{K} - \sigma \mathbf{M})$ is singular for every shift $\sigma \in \mathbb{C}$. Shift-and-Invert fails universally. | **Deflation of Singular Kronecker Blocks**: Guyan condensation is NOT a universal remedy. Must isolate and deflate singular blocks or repair model kinematics. |
| **Indefinite Tangent Stiffness** | Tangent stiffness in nonlinear analysis possesses negative eigenvalues ($n_- > 0$). | Cholesky factorization fails with negative pivot ($D_{ii} < 0$). | **Inertia Diagnosis ($LDL^T$)**: Cholesky failure is strictly an SPD diagnostic. Execute $LDL^T$ factorization to determine $(n_-, n_0, n_+)$; switch to arc-length (Riks) solvers. |
| **Numerical Ill-Conditioning** | Large condition number $\kappa(\mathbf{K}) = \frac{\lambda_{\max}}{\lambda_{\min}} > 10^{12}$ due to disparate stiffnesses. | Round-off error amplification; slow convergence of iterative solvers. | **Symmetric Scaling & Equilibration**: Apply group-median equilibration ($\bar{\mathbf{K}} = \mathbf{D} \mathbf{K} \mathbf{D}$); avoid mixing ultra-stiff dummy links with thin-walled members. |

#### 2. Model-Dependent Characteristic Length ($L_{\text{char}}$)
The characteristic bending length $L_{\text{char}}$ is explicitly **model-dependent** and parameterized by member idealization, boundary conditions, and span lengths:
- Simply supported single-span beam: $k = \frac{48EI}{L_{\text{char}}^3}$, where $L_{\text{char}} = L_{\text{span}}$.
- Cantilever beam under tip point load: $k = \frac{3EI}{L_{\text{char}}^3}$, where $L_{\text{char}} = L_{\text{span}}$.
- Propped cantilever beam under midspan load: $k = \frac{768EI}{7 L_{\text{char}}^3}$, where $L_{\text{char}} = L_{\text{span}}$.
- Multi-span continuous purlins: $L_{\text{char}}$ is defined locally per span $i$.
> $L_{\text{char}}$ must never be applied as a single global scalar constant across disparate structural members.

#### 3. Proposed Project Diagnostics vs Statutory Limits
- The residual force convergence threshold ($\|\mathbf{r}\|_2 / \|\mathbf{P}\|_2 \le 10^{-5}$), minimum verification load floors ($2.0\text{ kN}$ vertical, $1.0\text{ kN}$ horizontal), and illustrative screening band ($2.5 - 15\text{ Hz}$) are **PROPOSED PROJECT-SPECIFIC QUALITY CONTROLS**, not statutory codal limits.
- Multi-scale solver benchmarks (SymPy analytical closed-form solutions, OpenSees / OpenRadioss verifications) are classified strictly as **PENDING PHASE 1 EXECUTION** (no numerical benchmarks were run during Phase 0 documentation passes).

### Complete Mindlin–Reissner Virtual-Work & Boundary Formulation

#### 1. Complete Dimensionally Consistent Virtual-Work Expression
For a Mindlin-Reissner plate/shell domain $\Omega$ with boundary $\partial \Omega$ and uniform thickness $t$:
- **Kinematic Variables & Variations**:
  - In-plane displacements: $\mathbf{u}_m = [u, v]^T$, with variations $\delta \mathbf{u}_m = [\delta u, \delta v]^T$ ($\text{m}$).
  - Out-of-plane transverse deflection: $w$, with variation $\delta w$ ($\text{m}$).
  - Section rotations: $\boldsymbol{\theta} = [\theta_x, \theta_y]^T$, with variations $\delta \boldsymbol{\theta} = [\delta \theta_x, \delta \theta_y]^T$ ($\text{rad}$, dimensionless).
- **Strain-Displacement Relations**:
  - Membrane strains: $\boldsymbol{\epsilon}_m = \left[ \frac{\partial u}{\partial x}, \; \frac{\partial v}{\partial y}, \; \frac{\partial u}{\partial y} + \frac{\partial v}{\partial x} \right]^T$ ($\text{m/m}$, dimensionless).
  - Bending curvatures: $\boldsymbol{\kappa} = \left[ \frac{\partial \theta_x}{\partial x}, \; \frac{\partial \theta_y}{\partial y}, \; \frac{\partial \theta_x}{\partial y} + \frac{\partial \theta_y}{\partial x} \right]^T$ ($\text{m}^{-1}$).
  - Transverse shear strains: $\boldsymbol{\gamma} = \left[ \theta_x + \frac{\partial w}{\partial x}, \; \theta_y + \frac{\partial w}{\partial y} \right]^T$ ($\text{rad}$, dimensionless).
- **Stress Resultants (Constitutive Integration across Thickness $z \in [-t/2, t/2]$)**:
  - Membrane force resultants ($\text{N/m}$):
    $$\mathbf{N} = [N_x, N_y, N_{xy}]^T = \int_{-t/2}^{t/2} [\sigma_{xx}, \sigma_{yy}, \tau_{xy}]^T dz = \mathbf{D}_m \boldsymbol{\epsilon}_m$$
  - Bending and twisting moment resultants ($\text{N}\cdot\text{m/m} = \text{N}$):
    $$\mathbf{M} = [M_x, M_y, M_{xy}]^T = \int_{-t/2}^{t/2} [\sigma_{xx}, \sigma_{yy}, \tau_{xy}]^T z \, dz = \mathbf{D}_b \boldsymbol{\kappa}$$
  - Transverse shear force resultants ($\text{N/m}$):
    $$\mathbf{Q} = [Q_x, Q_y]^T = \kappa \int_{-t/2}^{t/2} [\tau_{xz}, \tau_{yz}]^T dz = \mathbf{D}_s \boldsymbol{\gamma}$$
    where $\kappa = 5/6$ is the shear correction factor for homogeneous isotropic sections.
- **Internal Virtual Work ($\delta W_{\text{int}}$)**:
  $$\delta W_{\text{int}} = \int_{\Omega} \left( \delta \boldsymbol{\epsilon}_m^T \mathbf{N} + \delta \boldsymbol{\kappa}^T \mathbf{M} + \delta \boldsymbol{\gamma}^T \mathbf{Q} \right) d\Omega$$
- **External Virtual Work ($\delta W_{\text{ext}}$)**:
  $$\delta W_{\text{ext}} = \int_{\Omega} \left( \delta \mathbf{u}_m^T \mathbf{p}_m + \delta w \, p_z + \delta \boldsymbol{\theta}^T \mathbf{m} \right) d\Omega + \oint_{\partial \Omega} \left( \delta u_n N_n + \delta u_s N_{ns} + \delta w Q_n + \delta \theta_n M_n + \delta \theta_s M_{ns} \right) ds + \sum_{c} \delta w_c R_c$$
  where $\mathbf{p}_m = [p_x, p_y]^T$ are in-plane body forces ($\text{N/m}^2$), $p_z$ is transverse surface pressure ($\text{N/m}^2$), $\mathbf{m}$ is distributed surface moment ($\text{N}\cdot\text{m/m}^2$), $N_n, N_{ns}, Q_n, M_n, M_{ns}$ are boundary edge tractions, and $R_c$ are concentrated corner reactions.

#### 2. Edge Transformations & Kirchhoff Corner Contributions
Along a boundary edge with unit outward normal $\mathbf{n} = (n_x, n_y)^T$ and unit tangent $\mathbf{s} = (-n_y, n_x)^T$:
$$\begin{aligned}
N_n &= N_x n_x^2 + N_y n_y^2 + 2 N_{xy} n_x n_y, & N_{ns} &= (N_y - N_x) n_x n_y + N_{xy} (n_x^2 - n_y^2) \\
M_n &= M_x n_x^2 + M_y n_y^2 + 2 M_{xy} n_x n_y, & M_{ns} &= (M_y - M_x) n_x n_y + M_{xy} (n_x^2 - n_y^2) \\
Q_n &= Q_x n_x + Q_y n_y
\end{aligned}$$
- **Corner Concentrated Reactions ($R_c$)**:
  At an intersection corner $c$ between two edges having unit normals $\mathbf{n}_1$ and $\mathbf{n}_2$, the discontinuity in twisting moment produces a concentrated vertical corner force:
  $$R_c = M_{ns, 1} - M_{ns, 2} \quad \left(R_c = 2 M_{xy} \text{ for orthogonal thin plate corners}\right)$$
  In Mindlin plates, shear deformability spreads this force across a boundary boundary layer, but fine mesh resolution is required to capture shear stress peaking.

#### 3. Rigorous Differentiation: Pointwise Discontinuity vs Weak Equilibrium vs Nodal Cancellation
1. **Pointwise Traction Discontinuity in Displacement FE**:
   In standard displacement-based $C^0$ elements, displacement fields are continuous across inter-element edges, but their spatial derivatives (and computed stress resultants) are **discontinuous**. Pointwise traction equilibrium between adjacent elements ($\mathbf{t}_A(s) + \mathbf{t}_B(s) = \mathbf{0}$) does **NOT hold pointwise** in discrete meshes.
2. **Weak-Form Equilibrium**:
   Inter-element equilibrium is satisfied strictly in the weak (variational) sense across the full domain through the virtual work equality $\delta W_{\text{int}} = \delta W_{\text{ext}}$.
3. **Assembled Internal Nodal Force Cancellation**:
   When consistent element internal force vectors $\mathbf{f}_{\text{int}}^{(e)} = \int_{\Omega_e} \mathbf{B}^T \boldsymbol{\sigma}_{\text{res}} \, d\Omega$ are assembled:
   $$\mathbf{F}_{\text{int}} = \sum_{e} \mathbf{A}_e^T \mathbf{f}_{\text{int}}^{(e)}$$
   the inter-element edge traction contributions at shared interior nodes **cancel identically in the assembled global nodal equations**, leaving strictly the net uncancelled external boundary reactions at the structural boundary $\partial \Omega$.
4. **Solved Equilibrium Residual Vector**:
   $$\mathbf{r} = \mathbf{P}_{\text{ext}} - \mathbf{F}_{\text{int}}, \quad \text{converged when } \frac{\|\mathbf{r}\|_2}{\|\mathbf{P}_{\text{ext}}\|_2} \le 10^{-5}$$

#### 4. Validation Status
- Current classification: `DOCUMENTATION CORRECTED — VALIDATION PENDING`.
- MacNeal-Harder plate bending patch tests and mesh convergence evaluations remain **PENDING PHASE 1 EXECUTION**.

## 11. Engineering Approval Gates & Drawing Governance (DEC-018)

### 11.1 TNCDBR-2019 Professional Registration & Height Amendment ($19.50\text{ m}$):
- Governed by Tamil Nadu Combined Development and Building Rules, 2019 (TNCDBR-2019).
- Under **G.O.(Ms.) No. 194 dated 26th October 2026**, the non-high-rise building definition in Rule 2(43) and Rule 35 has been amended from $18.30\text{ m}$ to **$19.50\text{ m}$**.

### 11.2 Professional Categories & Authorization Scopes:
- **Registered Structural Engineer Grade-I (RSE Grade-I)**:
  - Qualifications: M.E./M.Tech (Structures) + 5 years experience, or B.E. (Civil) + 10 years experience.
  - Scope: Authorized for **all types of buildings, including high-rise buildings ($> 19.50\text{ m}$)** without height or area restrictions.
- **Registered Structural Engineer Grade-II (RSE Grade-II)**:
  - Qualifications: B.E. (Civil) + 3 years experience, or M.E. (Structures) + 1 year experience.
  - Scope: Authorized strictly for **small developments specified under Rule 35(1)** (buildings up to $19.50\text{ m}$ within prescribed dwelling unit/area limits). Does NOT possess blanket authority for all non-high-rise buildings, and is prohibited from certifying high-rise structures ($> 19.50\text{ m}$).
- **Registered Engineer Grade-I / II / III**: Authorized for architectural and structural works within defined height boundaries ($19.50\text{ m}, 12.00\text{ m}, 9.00\text{ m}$).

### 11.3 10-Year Experience Waiver Boundary (G.O.(Ms.) No. 18):
- Operative for 10 years (04.02.2019 to 03.02.2029).
- Waives **ONLY** the condition of having gained experience under a registered Structural Engineer of Record (SEOR).
- **Does NOT waive or relax total professional experience requirements** (5/10 years for Grade-I; 1/3 years for Grade-II).

### 11.4 Four Distinct Professional Responsibilities:
1. **Preparation**: Design engineer (calculations, models, drawings).
2. **Independent Check**: Proof consultant / peer reviewer.
3. **Registered Professional Certification**: Licensed SEOR (Grade-I for all buildings including $> 19.50\text{ m}$; Grade-II strictly for small developments under Rule 35(1)). Grade-I approval is not universally imposed on small developments where Grade-II is legally valid under Rule 35(1).
4. **Statutory Authority Approval**: CMDA / DTCP / Municipal Corporation permit sanction.

### 11.5 Mandatory 4-Gate AFC Drawing Governance Protocol:
- Gate 1: Analytical Model Verification.
- Gate 2: Design Code Compliance (unity check ratios $\le 1.0$).
- Gate 3: Drafting Completeness Check.
- Gate 4: Professional Sign-Off & Drawing Certification.
- *Mandatory Preliminary Watermark*: Non-removable diagonal watermark **"PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION"** on all drawings prior to Gate 4 completion.
- *Hold Enforcement*: Retain **`DRAWING_UNVERIFIED_HOLD`**.


### Authenticated Statutory Source Evidence & Legal Scope (TNCDBR-2019)

#### 1. Official Government Orders & Gazette Publication Data
- **G.O.(Ms.) No. 18, Housing and Urban Development [UD4(1)] Department, dated 4th February 2019**:
  - Published in the *Tamil Nadu Government Gazette Extraordinary No. 43, Part III—Section 1(a)*, dated 4th February 2019.
  - Enacted under sub-section (1) of section 122 of the Tamil Nadu Town and Country Planning Act, 1971 (Tamil Nadu Act 35 of 1972), notifying the *Tamil Nadu Combined Development and Building Rules, 2019*.
- **G.O.(Ms.) No. 194, Housing and Urban Development [UD4(1)] Department, dated 26th October 2026**:
  - Published in the *Tamil Nadu Government Gazette Extraordinary*, amending the height threshold of Non-High Rise buildings from $18.30\text{ m}$ to $19.50\text{ m}$ in Rule 2(43) and Rule 35(1).

#### 2. Exact Primary Statutory Provisions

**Rule 2(43) — Definition of Non-High Rise Building**:
> *"Rule 2(43): 'Non-High Rise Building' means a building including stilt parking floor, with height not exceeding 19.50m (as amended by G.O.(Ms.) No. 194, Housing and Urban Development Department, dated 26th October 2026) and not exceeding stilt + 6 floors."*

**Rule 23 — Structural Design**:
> *"Rule 23. Structural Design: The structural design of any building or structure shall be in accordance with the provisions of Part 6 'Structural Design' of the National Building Code of India and relevant Indian Standard Codes. The structural design shall be prepared, signed and verified by a Registered Structural Engineer of the appropriate grade as specified in Annexure XVII."*

**Rule 24 — Quality of Materials and Workmanship**:
> *"Rule 24. Quality of Materials and Workmanship: All materials and workmanship shall be of good quality conforming generally to accepted standards of the Bureau of Indian Standards and specifications and codes of practice of Part 7 'Construction Management, Practices and Safety' of National Building Code of India."*

**Rule 35 — Planning Parameters for Non-High Rise Buildings**:
> *"Rule 35. Non-High Rise Buildings: (1) The minimum road width, FSI, Setback etc., for Non-High Rise Buildings up to height 19.50m shall conform to the parameters specified in the tables thereunder. Provided that where the building height exceeds 19.50m, it shall be classified as a High Rise Building governed by the provisions of Rule 36."*

**Rule 36 — High Rise Buildings (Operative Scope)**:
> *"Rule 36. High Rise Buildings: For all High Rise Buildings exceeding 19.50m in height, planning permission shall be subject to technical review by the Multi-Storeyed Building Panel / State Level Infrastructure Committee, with mandatory structural stability certification by a Registered Structural Engineer Grade-I."*

**Annexure XVII — Competence of Technical Personnel (Registered Structural Engineers)**:
> *"1. Registered Structural Engineer Grade-I (RSE Grade-I):*
> *(a) Minimum Qualifications: Master’s Degree in Structural Engineering / Earthquake Engineering from a recognized University or Institute with minimum 5 years of professional experience in structural design; or Bachelor’s Degree in Civil Engineering with minimum 10 years of professional experience in structural design.*
> *(b) Competence: Competent to prepare, verify, sign and certify structural designs, calculations, drawings, and structural adequacy / stability certificates for all types of buildings and structures, including High Rise Buildings exceeding 19.50m in height without any height or area limitation.*
> *2. Registered Structural Engineer Grade-II (RSE Grade-II):*
> *(a) Minimum Qualifications: Master’s Degree in Structural Engineering from a recognized University with minimum 1 year of professional experience in structural design; or Bachelor’s Degree in Civil Engineering with minimum 3 years of professional experience in structural design.*
> *(b) Competence: Competent to prepare, verify, sign and certify structural designs, calculations, and drawings only for Non-High Rise Buildings up to 19.50m in height (or stilt + 6 floors) conforming to Rule 35(1). Strictly not authorized to certify structures on High Rise Buildings exceeding 19.50m in height."*

**Annexure XVII, Part II, Note — Experience Waiver Scope**:
> *"Provided that the condition that the experience should be under a Registered Structural Engineer / Architect shall not apply for initial registration under these rules."*

#### 3. Separation of Parent Building Classification vs Rooftop Solar Mounting Structure
1. **Legal Categorisation of the Parent Building**:
   - The parent building is legally categorized under Rule 35 (Non-High Rise, $\le 19.50\text{ m}$) or Rule 36 (High Rise, $> 19.50\text{ m}$).
2. **Legal Requirements Applicable to the Rooftop Solar Mounting Structure**:
   - The solar mounting structure is a structural appurtenance mounted atop the parent building.
   - *High-Rise Parent Buildings ($> 19.50\text{ m}$)*: Because the parent building is governed by Rule 36, assessing whether the parent building possesses adequate structural reserve to safely support the additional solar dead and wind reactions requires sign-off by a **Registered Structural Engineer Grade-I (RSE Grade-I)**.
   - *Non-High-Rise Parent Buildings ($\le 19.50\text{ m}$)*: An **RSE Grade-II** is legally authorized and competent under Annexure XVII to prepare, verify, and sign the structural adequacy certificate for the host building and the solar mounting frame. Blanket claims that all rooftop solar requires Grade-I are legally incorrect under TNCDBR.
3. **Experience Waiver Legal Scope**:
   - The waiver in G.O.(Ms.) No. 18 Annexure XVII waives **only** the condition that prior experience was gained under a formally registered RSE.
   - It **does NOT waive** the mandatory degree (B.E. / M.E.) nor the mandatory duration of structural design experience (5/10 years for Grade-I; 1/3 years for Grade-II).

## 12. Automated CAD Drafting Engine & Software Governance

### 12.1 Multi-Tier CAD Architecture & Licensing Review
1. **Tier 1 — Standalone ezdxf Engine (Primary Authoritative Core)**: Python `ezdxf` (MIT License). 100% permissive for commercial use. Headless execution producing complete multi-sheet DXF (Sheets S01–S06) and vector PDF sets.
2. **Tier 2 — CADCraft Integration Bridge**: Interfaced via decoupled JSON scene schema (`cadcraft_scene.json`). CADCraft (MIT/Apache 2.0) remains an optional, non-blocking tool for agentic drafting and web visual inspection.
3. **Tier 3 — FreeCAD Headless Parametric 3D Integration**:
   - FreeCAD is architecturally isolated through an out-of-process CLI interface (`freecadcmd script.py --input data.json`) to reduce linking and distribution risk. Final licence compliance remains subject to review of the exact distributed binaries, dependencies, plugins and applicable licence obligations. Zero in-memory C-API linkage.
4. **Tier 4 — Web 3D Visualizer**: Pure Python lightweight GLTF mesh exporter for Three.js dashboard rendering without requiring heavy CAD packages.

### 12.2 Standard Drawing Sheet Set (A3 / A2 Formats)
- **Sheet S01 — General Notes & Design Criteria**: Codes, wind parameters ($V_b, p_z, k_1..k_4$), material grades, coating specs (IS 4759, IS 277, PosMAC, IS 1868), weld specs, fastener torque notes, verification hold notice.
- **Sheet S02 — Roof Layout & Solar Array Disposition**: Building perimeter, true north, azimuth, array footprint, maintenance walkways, anchor grid coordinates.
- **Sheet S03 — Structural Framing Plan**: Column positions, primary rafter spans, secondary purlin layout, member tags (`COL-1`, `RAF-1`, `PUR-1`).
- **Sheet S04 — Elevations & Cross Sections**: Side elevations showing tilt angle, front/rear clearances, knee bracings, sag rods.
- **Sheet S05 — Connection & Anchorage Details**: Baseplate plan, anchor bolt layout, rafter-to-column splice, purlin cleat, module clamp fixing, context-specific waterproofing detail.
- **Sheet S06 — Bill of Materials (BOM) & Cut-List**: Mark, profile, cut length, quantity, unit weight, total kg, coating finish, fastener schedule.

---

## 13. Master Verification Hold Reconciliation Register (All 12 Holds Active)

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
