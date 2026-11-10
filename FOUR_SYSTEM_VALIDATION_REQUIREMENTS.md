# RENSUN SOLAR — PHASE 1.4.2
# FOUR-SYSTEM VALIDATION REQUIREMENTS & ENGINEERING SPECIFICATION

**Document ID:** `RS-STR-SYS-REQ-01`  
**Revision:** R0 (Engineering Validation Readiness)  
**Governing Branch:** `feature/phase1-structural-foundation`  
**Applicability:** Systems A, B, C, and D  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  

---

## Part 1: System A — Elevated Steel Canopy

### 1.1 Architectural Concept & Structural Typology
Elevated open-frame canopy structure positioned above existing host reinforced cement concrete (RCC) building roof slabs. Clear stanchion height ranges from $2.5\text{ m}$ to $3.2\text{ m}$ above the finished roof slab, providing headroom for building occupant transit and servicing.

```
       [PV Modules in Portrait: 3 rows x 8 cols @ 10° Tilt]
   ═════════════════════════════════════════════════════════════   <- Cold-Formed Purlins (ISMC 100x50x2.0)
     \                /                     \                /
      \              /                       \              /
   ═════════════════════════════════════════════════════════════   <- Primary Rafter (ISMB 150 / ISMB 300)
             ║                                       ║
             ║                                       ║             <- Structural Column (ISMB / SHS)
             ║ (H_clear = 2.8 m)                     ║
            ╔╩╗                                     ╔╩╗            <- Baseplate with 4x M16 Chemical Anchors
   ═════════╩═╩═════════════════════════════════════╩═╩═════════   <- Existing Host RCC Roof Slab (M20/M25)
```

### 1.2 Required Project & Site Inputs
- **Site Parameters**: Basic wind speed ($V_b$), terrain category (1, 2, 3, 4), building height ($H_b$), rooftop elevation ($H_r$), cyclonic factor ($k_4$), topography factor ($k_3$), risk factor ($k_1$), seismic zone (II, III, IV, V), importance factor ($I$).
- **Array Geometry**: Total modules ($N$), rows ($R$), columns ($C$), tilt angle ($\theta$), purlin spacing ($s_p$), rafter spacing ($L_r$), column height ($H_c$), walkway width ($w_w$).
- **Section Properties**: Purlin section (ISMC/C-channel: $A, I_{xx}, I_{yy}, Z_{px}, Z_{py}$), rafter section (I-beam: $A, I_{xx}, Z_{px}$), column section (Tubular/I-beam: $A, r_y, I_{xx}$).
- **Material Properties**: Structural steel grade (E250 Fe 410W: $f_y = 250\text{ MPa}, f_u = 410\text{ MPa}, E = 205000\text{ MPa}, \gamma_{m0} = 1.10, \gamma_{m1} = 1.25$).

### 1.3 Material Specifications & Codal Standards
- **Structural Steel**: IS 2062: 2011 (Hot Rolled Medium and High Tensile Structural Steel).
- **Cold-Formed Purlins**: IS 801: 1975 (Code of Practice for Use of Cold-Formed Light Gauge Steel Structural Members).
- **Design Standard**: IS 800: 2007 (General Construction in Steel — Code of Practice, Limit State Method).
- **Wind Loading**: IS 875 (Part 3): 2015 Clause 7.4.4.4 & Table 8 (Open canopies, mono-slope roofs).
- **Seismic Design**: IS 1893 (Part 1): 2016 Clause 6.3.3.1 (Amd 2) & Clause 6.4.5.

### 1.4 Loading Applicability & Combinations
- **Dead Load (DL)**: Module dead load ($0.12 - 0.15\text{ kN/m}^2$), purlin self-weight, primary rafter self-weight, walkway grating ($0.25\text{ kN/m}^2$).
- **Imposed Live Loads (IL)**:
  - `ACT-IL-01`: Point live load of $1.0\text{ kN}$ midspan per IS 875 (Part 2) Clause 4.1.
  - `ACT-IL-02`: Distributed array live load of $0.75\text{ kN/m}^2$ for maintenance access.
  - `ACT-IL-04`: Walkway live load of $3.0\text{ kN/m}^2$ along service corridors.
- **Wind Actions (WL)**: Design wind pressure $p_z = 0.6 \cdot V_z^2$, net aerodynamic coefficients from Table 8 ($C_{n,\text{up}} = -1.02$ to $-1.30$, $C_{n,\text{down}} = +0.40$ to $+0.80$).
- **Load Combinations**:
  - `ULS-01`: $1.5\text{DL} + \max(1.5\text{IL}_{\text{array}} + 1.05\text{IL}_{\text{walkway}}, 1.5\text{IL}_{\text{walkway}} + 1.05\text{IL}_{\text{array}})$
  - `ULS-02`: $0.9\text{DL} + 1.5\text{WL}_{\text{up}}$ (Uplift stress reversal and net anchor tension)
  - `ULS-06`: $1.2\text{DL}_{\text{bare}} + 1.2\text{ER}$ (Erection stage before module installation)
  - `SLS-01`: $1.0\text{DL} + 1.0\text{IL}$ (Purlin vertical deflection $\le L/250$)

### 1.5 Structural Member Strength & Serviceability Checks
1. **Purlin Sagging Flexure ($M_u \le M_d$)**: Evaluated independently under distributed load vs midspan point load. Governing response compared against major-axis plastic moment capacity $M_{dz} = \beta_b Z_p f_y / \gamma_{m0}$ per IS 800 Clause 8.2.1.2.
2. **Purlin Major-Axis Shear ($V_u \le V_d$)**: Factored shear checked against plastic shear resistance $V_d = A_v f_y / (\sqrt{3} \gamma_{m0})$ per IS 800 Clause 8.4.1.
3. **Purlin Wind Uplift Reversal ($M_{u,\text{up}} \le M_{dz}$)**: Net suction bending evaluated with stabilizing dead load reduced by factor 0.9.
4. **Purlin Serviceability Deflection ($\delta \le \delta_{\text{allow}}$)**: Actual deflection compared against $L/250$ per IS 800 Table 6.
5. **Primary Rafter Biaxial Bending**: Sagging moment evaluated under simultaneous leading/accompanying array and walkway live loads.
6. **Primary Rafter Construction Erection Flexure**: Temporary stability evaluated under self-weight plus erection allowance.
7. **Canopy Column Axial Buckling Resistance ($P_u \le P_d$)**: Slenderness $\lambda = KL/r_y$, non-dimensional slenderness $\lambda_0 = \sqrt{f_y / f_{cc}}$, buckling curve b ($\alpha = 0.34$), design compressive strength $f_{cd} = \chi f_y / \gamma_{m0}$ per IS 800 Clause 7.1.2 & Table 9c.

### 1.6 Host Interface & Foundation Mechanics
- **Base Connection**: Stiffened steel baseplate with 4x post-installed chemical anchors.
- **Anchor Embedment Check**: Combined anchor tensile pull-out, concrete cone breakout, and anchor shear per `EOTA TR 048 / REFERENCE PENDING VERIFICATION`.
- **Host Slab Check**: Slab local punching shear and column load-path transfer per IS 456: 2000 Clause 31.

### 1.7 Physical Testing & Evidence Required for Hold Release
- **`INSPECTION_REQUIRED_HOLD`**: Rebound hammer and UPV test logs (IS 13311) proving host slab compressive strength $f_{ck} \ge 20\text{ MPa}$; visual crack mapping report signed by Grade-I RSE.
- **`AERODYNAMIC_UNSUPPORTED_HOLD`**: Wind tunnel test report (ASCE 49-21) or validated 3D CFD validating net pressure coefficients where array tilt $> 10^\circ$ or canopy aspect ratio exceeds Table 8 bounds.
- **`FASTENER_TORQUE_UNVERIFIED_HOLD`**: Site torque-wrench calibration logs verifying specified bolt torques (A2-70 M10/M12/M16).

---

## Part 2: System B — Low-Height Aluminium Rail

### 2.1 Architectural Concept & Structural Typology
Low-profile rooftop mounting system utilizing custom extruded aluminium guide rails mounted on elevated tilt legs or L-feet fastened directly into the host concrete slab. Clearance height is minimal ($0.15\text{ m} - 0.45\text{ m}$), substantially reducing the wind exposure envelope compared to elevated canopies.

```
       [PV Module @ 10°-15° Tilt]
   ════════════════════════════════════════   <- PV Module Frame
      ║ (Mid/End Clamp)      ║
   ═══╩══════════════════════╩═════════════   <- Extruded Al Rail (AL-RAIL-40x40)
      │                      │
     /_\ (L-Foot Bracket)   /_\               <- Tilt Leg / L-Foot Bracket
      ║                      ║                <- M10 Mechanical Expansion Anchor
   ═══╩══════════════════════╩═════════════   <- Host Concrete Roof Slab
```

### 2.2 Required Project & Site Inputs
- **Site Parameters**: Basic wind speed ($V_b$), terrain category, building height, parapet height ($h_p$), parapet distance from roof edge ($d_p$).
- **Geometry**: Span between L-foot roof brackets ($L_{\text{bracket}} = 1000 - 1500\text{ mm}$), cantilever overhang ($L_{\text{overhang}} \le 400\text{ mm}$), module width, rail cross-section geometry.
- **Material Properties**: Aluminium alloy 6063-T6 ($f_y = 170\text{ MPa}, f_u = 205\text{ MPa}, E = 70000\text{ MPa}, \nu = 0.33, \gamma_m = 1.10$).
- **Clamp Properties**: Mid-clamp and end-clamp tensile pull-out capacity ($T_{\text{clamp}}$), bolt diameter ($M8$ SS 304 A2-70).

### 2.3 Material Specifications & Codal Standards
- **Extruded Aluminium**: IS 733: 1983 (Wrought Aluminium and Aluminium Alloy Bars, Rods and Sections for General Engineering Purposes).
- **Structural Aluminium Design**: **IS 8147: 1976** (Code of Practice for Use of Aluminium Alloys in Structures) & **AA ADM 2020** (Aluminium Design Manual).
- **Fasteners**: ISO 3506-1: 2020 (Corrosion-resistant stainless steel fasteners).
- **Wind Shielding**: IS 875 (Part 3): 2015 Clause 7.3.3.4 (Parapet shielding and rooftop low-profile arrays).

### 2.4 Loading Applicability & Combinations
- **Dead Load**: Module self-weight ($0.12 - 0.14\text{ kN/m}^2$) + rail self-weight ($0.8 - 1.2\text{ kg/m}$).
- **Imposed Load**: $1.0\text{ kN}$ concentrated technician load placed midspan or on cantilever tip.
- **Wind Actions**: Shielded rooftop velocity pressure with zone edge factors ($C_{pe} = -1.1$ to $-1.6$ near eaves/corners, attenuated by parapet).
- **Load Combinations**:
  - `ULS-01`: $1.5\text{DL} + 1.5\text{IL}$ (Down-force flexure and shear).
  - `ULS-02`: $0.9\text{DL} + 1.5\text{WL}_{\text{up}}$ (Rail uplift bending and clamp pull-out).
  - `SLS-01`: $1.0\text{DL} + 1.0\text{IL}$ (Rail deflection limit $\delta \le L/200$).

### 2.5 Structural Member Strength & Serviceability Checks
1. **Aluminium Rail Bending Capacity ($M_u \le M_d$)**: Calculated using section modulus $Z_{xx}$ and allowable bending stress $F_b = f_y / \gamma_m$ per IS 8147 Clause 6.1.
2. **Rail Shear Capacity ($V_u \le V_d$)**: Major-axis shear resistance of thin-walled aluminium web per IS 8147 Clause 6.3.
3. **Module Clamp Pull-Out Capacity ($T_u \le T_{d,\text{clamp}}$)**: Factored wind uplift per clamp compared against certified clamp proof load:
   $$T_u = 1.5 \cdot |C_{n,\text{up}}| \cdot p_z \cdot A_{\text{trib,clamp}}$$
   Fastener tensile capacity verified against A2-70 M8 bolt tensile limit:
   $$T_{d,\text{bolt}} = \frac{0.9 f_{ub} A_s}{\gamma_{m2}} = \frac{0.9 \cdot 700 \cdot 36.6}{1.25 \cdot 1000} = 18.45\text{ kN}$$
4. **Rail Vertical Deflection**: Elastic deflection under unfactored serviceability loads verified against span limit $\delta \le L/200$.

### 2.6 Physical Testing & Evidence Required for Hold Release
- **`ALUMINIUM_DERIVATION_HOLD`**: Mill test certificates (MTC) to EN 10204 Type 3.1 and tensile coupon testing (IS 1608) verifying $f_y \ge 170\text{ MPa}$ for custom rail profile.
- **`FASTENER_TORQUE_UNVERIFIED_HOLD`**: Documented torque calibration logs (12–15 N·m for M8 A2-70 module mid/end clamps).

---

## Part 3: System C — Metal-Sheet Roof Mounting

### 3.1 Architectural Concept & Structural Typology
Direct fastening of solar modules onto industrial pitched metal roofs (trapezoidal profiled metal sheets or standing-seam roofs). The structural system relies on specialized non-penetrating seam clamps (for standing-seam) or self-drilling screws with EPDM seals penetrating into the underlying purlins.

```
       [PV Module Mounted Flush to Pitched Roof]
   ═══════════════════════════════════════════════════════════   <- PV Module
      ║ (Module Clamp)                       ║ (Module Clamp)
   ───╨──────────────────────────────────────╨────────────────   <- Short Rail or Direct Bracket
   /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\   <- Pitched Metal Sheeting (0.50mm BMT)
   ═══════════════════════════════════════════════════════════   <- Host Cold-Formed Z-Purlin
```

### 3.2 Required Project & Site Inputs
- **Sheet Parameters**: Sheet profile type (Standing seam vs Trapezoidal), base metal thickness (BMT, typically $0.45 - 0.60\text{ mm}$), yield strength of steel sheet ($f_y = 350 - 550\text{ MPa}$), purlin spacing ($s_{\text{purlin}} = 1200 - 1600\text{ mm}$).
- **Clamp / Fastener Specifications**: Standing-seam clamp model, manufacturer tensile pull-out rating, self-drilling screw gauge and thread pitch, EPDM washer specification.

### 3.3 Material Specifications & Codal Standards
- **Cold-Formed Steel Sheeting**: IS 513: 2008 (Cold-reduced carbon steel sheets) & IS 14246: 1995 (Continuously pre-painted galvanized steel).
- **Fasteners in Light-Gauge Steel**: `AISI S904 / AISI S905 / REFERENCE PENDING VERIFICATION` (Standard Test Methods for Determining Structural Performance of Sheet Metal Fasteners).
- **Wind Pressure**: IS 875 (Part 3): 2015 Clause 7.3.3.2 (Pitched roofs of clad buildings).

### 3.4 Loading Applicability & Combinations
- **Dead Load**: Negligible self-weight of brackets ($< 0.05\text{ kN/m}^2$) + module self-weight ($0.12 - 0.14\text{ kN/m}^2$).
- **Wind Uplift Actions**: Local suction peaks at eaves, ridges, and gables ($C_{pe} = -1.2\text{ to } -2.0$).
- **Combinations**:
  - `ULS-02`: $0.9\text{DL} + 1.5\text{WL}_{\text{up}}$ (Dominant critical mode: clamp seam pull-off and screw tear-out).

### 3.5 Structural Strength Checks
1. **Standing-Seam Clamp Tensile Pull-Out ($T_u \le T_{\text{capacity}}$)**: Factored wind uplift compared against verified clamp-seam slip resistance:
   $$T_u = 1.5 \cdot |C_{n,\text{up}}| \cdot p_z \cdot A_{\text{trib,clamp}} \le T_{\text{cap}}$$
2. **Sheet Fastener Pull-Out / Stripping Resistance**: Pull-out capacity of screw from thin-gauge purlin web evaluated per cold-formed design standards.
3. **Purlin Additional Bending & Web Crippling**: Evaluation of whether host purlin can carry module weight and wind loads without localized buckling.

### 3.6 Physical Testing & Evidence Required for Hold Release
- **`FASTENER_TORQUE_UNVERIFIED_HOLD`**: On-site pull-out testing on actual roof sheet profile verifying that seam clamp slips at load $> 1.5 \times T_{\text{demand}}$.
- **`INSPECTION_REQUIRED_HOLD`**: Inspection report certifying host metal roof purlin spacing, sheet gauge, and absence of corrosion or fatigue cracks.

---

## Part 4: System D — Ballasted Non-Penetrating System

### 4.1 Architectural Concept & Structural Typology
Flat-roof mounting configuration utilizing pre-cast concrete ballast blocks placed in aerodynamic chasses to resist wind uplift and lateral sliding without roof penetrations. The system relies entirely on dead weight, roof-to-ballast interface friction, and aerodynamic deflection skirts.

```
                  [PV Module @ 5°-10° Low Tilt]
               ══════════════════════════════
              / │                          │ \   <- Aerodynamic Wind Deflector
   [Ballast] █  │                          │  █  <- Pre-cast Concrete Ballast Blocks
   ══════════╩══╧══════════════════════════╧══╩═════════   <- Elastomeric Friction Interface Pad (EPDM)
   ─────────────────────────────────────────────────────   <- Waterproofing Membrane
   ═════════════════════════════════════════════════════   <- RCC Host Roof Slab
```

### 4.2 Required Project & Site Inputs
- **Site Parameters**: Building height, parapet height ($h_p$), basic wind speed ($V_b$), terrain category.
- **Interface Parameters**: Waterproofing membrane material (APP modified bitumen, EPDM, PVC, TPO), surface condition (dry, damp, ponding), static friction coefficient ($\mu$).
- **Ballast Parameters**: Concrete block density ($\ge 2300\text{ kg/m}^3$), block unit mass ($35 - 50\text{ kg}$), chassis length, module tilt angle ($5^\circ - 10^\circ$).

### 4.3 Material Specifications & Codal Standards
- **Ballast Blocks**: Precast concrete conforming to IS 456: 2000 (M25 grade minimum, water absorption $< 6\%$).
- **Aerodynamic Wind Coefficients**: `SEAOC PV2-2017 / ASCE 49-21 / REFERENCE PENDING VERIFICATION` (Wind Design for Low-Profile Solar Photovoltaic Arrays on Flat Roofs).
- **Interface Friction**: `REFERENCE PENDING VERIFICATION` (ASTM C1028 withdrawn; EN 13893 / in-situ test protocol required).

### 4.4 Loading Applicability & Strict Boundary Conditions
- **Live Load Rule**: **Adverse live load is strictly zero ($IL = 0$) during sliding and overturning checks**. Live load cannot be relied upon to provide stabilizing friction or counterweight!
- **Stabilizing Factor**: Dead load stabilizing factor is restricted to $0.9$ (or $0.8$ per international best practice).
- **Wind Actions**: Dynamic wind uplift suction ($q_{\text{wind}}$) and concurrent horizontal aerodynamic drag ($F_{w,h}$).

### 4.5 Fundamental Stability & Safety Equations
1. **Sliding Resistance Safety Margin ($F_{\text{friction}} \ge F_{\text{drag}}$)**:
   - Net vertical contact reaction:
     $$N_{\text{net}} = 0.9 \cdot W_{\text{DL}} - 1.5 \cdot F_{\text{wind,v}}$$
   - Available frictional resistance:
     $$F_{\text{fric}} = \mu_{\text{design}} \cdot N_{\text{net}}$$
   - Applied horizontal wind drag:
     $$F_{\text{drag}} = 1.5 \cdot q_{\text{wind}} \cdot A_{\text{chassis}} \cdot \sin(\theta)$$
   - Sliding Unity Ratio:
     $$\text{Unity}_{\text{slide}} = \frac{F_{\text{drag}}}{F_{\text{fric}}} \le 1.0$$
2. **Overturning Moment Equilibrium ($M_{\text{restoring}} \ge M_{\text{overturn}}$)**:
   - Restoring moment about forward ballast toe:
     $$M_{\text{restoring}} = (0.9 \cdot W_{\text{DL}}) \cdot \frac{L_{\text{chassis}}}{2}$$
   - Overturning moment from aerodynamic lift and drag:
     $$M_{\text{overturn}} = (F_{w,h} \cdot h_{cg}) + \left(F_{w,v} \cdot \frac{L_{\text{chassis}}}{2}\right)$$
   - Overturning Unity Ratio:
     $$\text{Unity}_{\text{overturn}} = \frac{M_{\text{overturn}}}{M_{\text{restoring}}} \le 1.0$$
3. **Host Slab Pressure Check**: Total dead load (modules + ballast = $0.75 - 1.25\text{ kN/m}^2$) checked against host roof slab live-load reserve capacity.

### 4.6 Physical Testing & Evidence Required for Hold Release
- **`FRICTION_UNVERIFIED_HOLD`**: In-situ static pull-slip test on actual roof membrane under wet conditions; safety factor of $1.5$ applied to measured mean $\mu$.
- **`AERODYNAMIC_UNSUPPORTED_HOLD`**: Wind tunnel pressure calibration proving that parapet edge wake does not cause localized blow-off.

---

## Part 5: Governance Summary & Readiness Restrictions

```
========================================================================================================================
FOUR-SYSTEM VALIDATION PREREQUISITE GATES
========================================================================================================================
System Code | System Description                  | Critical Safety Mechanism         | Blocking Governance Gate
------------+-------------------------------------+-----------------------------------+---------------------------------
System A    | Elevated Steel Canopy               | Host slab punching & column sway  | INSPECTION & DRAWING STAMPING
System B    | Low-Height Aluminium Rail           | Rail flexure & clamp pull-out     | ALUMINIUM SPEC & FASTENER TORQUE
System C    | Metal-Sheet Fastened System         | Sheet seam pull-off & screw shear | ROOF SHEET INSPECTION & CLAMP PULL
System D    | Ballasted Non-Penetrating System    | Membrane sliding & blow-off       | MEMBRANE FRICTION & BLWT TUNNEL
========================================================================================================================
```

> [!CAUTION]
> Under no circumstances may any of the 12 canonical verification holds be released algorithmically or through the UI in Phase 1.4.2. All outputs must retain `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`.
