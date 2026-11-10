# RENSUN SOLAR — PHASE 1.4.2
# SITE DATA EVIDENCE REQUIREMENTS & GEOGRAPHIC GOVERNANCE SPECIFICATION

**Document ID:** `RS-STR-SITE-GOV-01`  
**Revision:** R0 (Engineering Validation Readiness)  
**Governing Branch:** `feature/phase1-structural-foundation`  
**Target Reference Project:** `RS-STR-RENSUN-2026-0059`  
**Site Address:** `90 ERUMAPALAYAM ITTERI ROAD, SALEM, TAMIL NADU`  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  

---

## 1. Executive Summary & Purpose

This specification governs the collection, validation, and elevation of site-specific meteorological and geographic parameters across the RENSUN Solar platform. It directly addresses the findings of the Phase 1.4.1 Owner Review regarding project `RS-STR-RENSUN-2026-0059` and establishes the definitive evidentiary protocol required before provisional site data can be certified for construction.

> [!IMPORTANT]
> **Mandatory Governance Rule**:
> 1. The current coordinates ($11.6643^\circ\text{N}, 78.1460^\circ\text{E}$) are explicitly classified as a **Provisional Municipal Centroid**. They must **never** be represented as surveyed rooftop coordinates.
> 2. The basic wind speed ($V_b = 39.0\text{ m/s}$) is a **Provisional Regional Contour Interpretation** derived from IS 875 (Part 3): 2015 Figure 1. It must **never** be represented as an independently certified site value.
> 3. Database coordinates and wind speeds must **not** be altered without explicit Owner authorization.
> 4. Verification holds **`WIND_COORD_UNVERIFIED_HOLD`** and **`ASSUMED_DATA_CERTIFICATION_HOLD`** remain strictly active and enforced.

---

## 2. Three-Level Site Parameter Hierarchy

To prevent confusion between geographical names and physical wind actions, the platform establishes a strict three-tier parameter classification:

```
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 1: SITE GEOGRAPHIC IDENTIFICATION                                │
│ - Property address: 90 Erumapalayam Itteri Road, Salem                 │
│ - Current status: Salem Municipal Centroid (11.6643°N, 78.1460°E)      │
│ - Evidence level: Level 3 (General District/City Reference Point)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 2: REGIONAL METEOROLOGICAL WIND INTERPRETATION                   │
│ - Statutory basis: IS 875 (Part 3): 2015 Figure 1 (Inland Isotach)     │
│ - Codal listing: UNLISTED in Annex A Selected Cities Table             │
│ - Assigned value: Vb = 39.0 m/s (Provisional Regional Interpretation)  │
│ - Evidence level: Level 2 (Codal Map Manual Interpretation)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 3: VERIFIED MICRO-TOPOGRAPHY & SITE EXPOSURE                     │
│ - Upwind terrain category (TC 1, TC 2, TC 3, or TC 4)                  │
│ - Topographic acceleration factor (k3: hills, valleys, escarpments)    │
│ - Cyclonic importance factor (k4: coastal buffer distance)             │
│ - Ground & rooftop obstruction wake exposure                           │
│ - Evidence level: PENDING (Physical Site Inspection & Survey Required) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Salem Project Specific Discrepancy & Spatial Analysis

### 3.1 Municipal Centroid vs Erumapalayam Physical Site
Project `RS-STR-RENSUN-2026-0059` has its address recorded from TNEB consumer connection `044060072111` as:
$$\text{Address: 90 ERUMAPALAYAM ITTERI ROAD, SALEM}$$

- **Centroid Coordinates in DB**: Latitude $11.6643^\circ\text{N}$, Longitude $78.1460^\circ\text{E}$.
- **Geographic Landmark**: Salem District Collectorate / Corporation Municipal Office.
- **Physical Location of Erumapalayam**: Located in eastern Salem (~PIN Code 636015), approximately between $11.63^\circ\text{N} - 11.65^\circ\text{N}$ and $78.18^\circ\text{E} - 78.20^\circ\text{E}$.
- **Spatial Offset**: The distance between the database reference coordinates and the actual neighborhood is approximately **$4.5\text{ to }6.0\text{ kilometers}$**.

### 3.2 Meteorological Significance of the Offset
Salem is situated in an inland valley surrounded by the Shevaroy Hills (Yercaud) to the north, Nagarmalai to the northeast, and Jarugumalai to the south. 

1. **Regional Baseline**: The regional basic wind speed from IS 875 (Part 3) Figure 1 contour map across the Salem valley plain is consistently within the $39.0\text{ m/s}$ isotach contour. The $5\text{ km}$ offset between the municipal center and Erumapalayam does not alter the macro-level $V_b$ zone.
2. **Micro-Topographic Risk**: However, proximity to surrounding hill ranges can trigger localized wind acceleration (funneling through saddles or escarpment crest effects) governed by **IS 875 Clause 6.3.3 ($k_3$ factor)**.
3. **Conclusion**: While $39.0\text{ m/s}$ is valid as a provisional baseline, certifying the structural design for construction without verifying the local $k_3$ factor and rooftop exposure violates Indian Standard statutory requirements.

---

## 4. Physical & Documentary Evidence Protocol for Hold Release

To elevate site data from **Level 3 (Provisional)** to **Level 1 (Certified)** and enable consideration for releasing `WIND_COORD_UNVERIFIED_HOLD` and `ASSUMED_DATA_CERTIFICATION_HOLD`, the following four mandatory evidentiary packages must be submitted:

```
========================================================================================================================
EVIDENTIARY REQUIREMENTS REGISTER FOR SITE DATA CERTIFICATION
========================================================================================================================
Package ID | Evidence Document Description             | Required Source / Authority | Statutory / Technical Standard
-----------+-------------------------------------------+-----------------------------+----------------------------------
EV-SITE-01 | Differential GPS (DGPS) Rooftop Survey    | Licensed Land Surveyor / GIS| Accuracy: Sub-meter (< 1.0 m)
EV-SITE-02 | Cadastral Property Deed & Tax Receipt     | Salem Municipal Corporation | Property Tax / Survey Ward No.
EV-SITE-03 | Topographic Escarpment & Upwind Audit     | Registered Structural Eng.  | IS 875 (Part 3): 2015 Clause 6.3.3
EV-SITE-04 | Host Building Structural Integrity Signoff| RSE (Grade-I / Grade-II)    | TNCDBR-2019 Rule 35 & Annexure XVII
========================================================================================================================
```

### Detailed Requirement per Package:

#### Package EV-SITE-01: Differential GPS (DGPS) Rooftop Survey
- **Requirement**: Certified on-site DGPS or dual-frequency RTK GNSS survey recording:
  - Latitude and Longitude of all four building roof corners to 6 decimal places.
  - Finished roof slab level above mean sea level (MSL).
  - Parapet wall top elevation at all corners.
- **Verification Method**: Polygon containment validation within the registered cadastral property boundary.

#### Package EV-SITE-02: Cadastral Property Boundary Verification
- **Requirement**: Copy of the latest Salem City Municipal Corporation property tax receipt and approved building plan indicating the exact revenue survey number and door number (90 Erumapalayam Itteri Road).
- **Verification Method**: Documented reconciliation confirming that the TNEB consumer service connection `044060072111` physically powers the surveyed building.

#### Package EV-SITE-03: Topographic Escarpment & Micro-Exposure Audit ($k_3$)
- **Requirement**: Engineering site report signed by a structural engineer auditing:
  - Upwind ground slope ($\theta$) over a distance of $1.5\text{ km}$ in all eight principal wind directions.
  - Determination of whether the building is located on a hill crest, ridge, cliff, or escarpment where ground slope exceeds $3^\circ$.
  - Formal computation of topography factor $k_3$ per IS 875 (Part 3) Appendix C (values range from $1.00$ to $1.36$).
  - Upwind terrain category determination (TC 2 for open terrain with scattered obstructions vs TC 3 for industrial/suburban area).

#### Package EV-SITE-04: Host Building Structural Stability & Slab Integrity
- **Requirement**: Comprehensive structural stability certificate per **TNCDBR-2019 Annexure XVII** signed by a Registered Structural Engineer (RSE) containing:
  - Measured host RCC slab thickness (minimum $125\text{ mm}$ recommended).
  - Concrete core compressive strength or calibrated NDT rebound hammer/UPV logs ($f_{ck} \ge 20\text{ MPa}$).
  - Slab reinforcement cover and rebar detection scan.
  - Written confirmation that the host building has sufficient reserve live-load capacity to support added solar dead and wind reactions without distress.

---

## 5. Implementation & Database Governance Guardrails

```
========================================================================================================================
GOVERNANCE GUARDRAILS FOR PROJECT RS-STR-RENSUN-2026-0059
========================================================================================================================
Parameter / Field      | Current Database State     | Provisional Governance Rule              | Permitted Phase 1 Action
-----------------------+----------------------------+------------------------------------------+------------------------
Latitude               | 11.6643° N                 | Classified strictly as municipal centroid| PRESERVED UNCHANGED
Longitude              | 78.1460° E                 | Classified strictly as municipal centroid| PRESERVED UNCHANGED
Basic Wind Speed (Vb)  | 39.0 m/s                   | Provisional regional contour map value   | PRESERVED UNCHANGED
Wind Provenance Label  | PROVISIONAL REGIONAL       | Continuous GIS interpolation disclaimed  | PRESERVED UNCHANGED
WIND_COORD Hold        | ACTIVE / ENFORCED          | Blocks AFC release until EV-SITE-01/02   | HARD-LOCKED
ASSUMED_DATA Hold      | ACTIVE / ENFORCED          | Blocks AFC release until EV-SITE-03/04   | HARD-LOCKED
AFC Approval Flag      | 0 (Hardcoded False)        | Construction release strictly blocked    | ZERO BYPASS PERMITTED
========================================================================================================================
```

> [!CAUTION]
> Any automated tool, script, or user interface action that attempts to mark `is_approved_for_construction = 1` or delete active verification holds without the four verified evidentiary packages constitutes an immediate breach of platform engineering governance.
