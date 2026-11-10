"""
Site Coordinate, Wind Parameter & Host-Structure Survey Verification Framework
Package: structural.site_survey
Phase: 1.5.2 (WP-04, WP-05, WP-06)

Enforces strict engineering governance and evidence-driven validation:
- WP-04: Rooftop Survey Coordinate Verification Framework
  - Prohibits classifying provisional coordinates as verified rooftop data.
  - Requires physical survey instrument, accuracy, date, surveyor, and evidence.
  - Marks unverified coordinates as 'UNVERIFIED — ROOFTOP SURVEY REQUIRED'.
- WP-05: Transparent Wind Input Verification Framework (IS 875 Part 3: 2015)
  - Identifies unlisted status of Salem in IS 875 (Part 3): 2015 Annex A Table.
  - Explicitly separates Statutory Code, Site-Measured, Engineer-Selected, and Assumed values.
  - Enforces WIND_COORD_UNVERIFIED_HOLD and ASSUMED_DATA_CERTIFICATION_HOLD for provisional wind data.
- WP-06: Host Structure & Roof Inspection Mandatory Register
  - Captures 17 mandatory structural inspection parameters.
  - Prohibits inferring host-structure capacity from roof type alone.
  - Rejects engineering PASS if physical concrete/rebar/framing evidence is missing or assumed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import math

from structural.models import SiteParameters, TerrainCategory, SeismicZone
from structural.provenance import ProvenanceLevel, ProvenanceRecord
from structural.holds import MASTER_VERIFICATION_REGISTER


# ======================================================================
# WP-04: SITE-COORDINATE VERIFICATION ENUMS & MODELS
# ======================================================================

class SurveyMethod(str, Enum):
    RTK_GNSS = "RTK GNSS (Real-Time Kinematic Geodetic Receiver)"
    TOTAL_STATION = "Total Station Terrestrial Optical Survey"
    HANDHELD_GPS = "Handheld / Smartphone GPS (Uncertified)"
    SATELLITE_AERIAL = "Satellite / Aerial Imagery Centroid Estimation"
    PROVISIONAL_CENTROID = "Municipal / Locality Centroid (Unverified)"


class CoordinateVerificationStatus(str, Enum):
    UNVERIFIED_ROOFTOP_SURVEY_REQUIRED = "UNVERIFIED — ROOFTOP SURVEY REQUIRED"
    PROVISIONAL_CENTROID = "PROVISIONAL — CENTROID ESTIMATE ONLY"
    VERIFIED_ROOFTOP_SURVEY = "VERIFIED — ROOFTOP SURVEY COMPLETED"


class ApprovalStatus(str, Enum):
    PENDING_REVIEW = "PENDING_INDEPENDENT_REVIEW"
    ACCEPTED_PROVISIONAL = "ACCEPTED_AS_PROVISIONAL_SCREENING"
    REJECTED = "REJECTED_INSUFFICIENT_ACCURACY"
    VERIFIED_BY_RSE = "VERIFIED_AND_SIGNED_BY_RSE"


@dataclass
class SiteCoordinateRecord:
    """
    Structured site coordinate and rooftop survey record (WP-04).
    Retains provisional Salem centroid (11.6643°N, 78.1460°E) as historical data,
    while enforcing survey verification requirements before engineering acceptance.
    """
    latitude: float
    longitude: float
    location_name: str = "90 ERUMAPALAYAM ITTERI ROAD, SALEM"
    survey_date: Optional[str] = None
    survey_method: SurveyMethod = SurveyMethod.PROVISIONAL_CENTROID
    survey_instrument: Optional[str] = None
    accuracy_m: Optional[float] = None
    surveyor_name: Optional[str] = None
    surveyor_organization: Optional[str] = None
    source_document: Optional[str] = None
    provenance_level: ProvenanceLevel = ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL
    verification_status: CoordinateVerificationStatus = CoordinateVerificationStatus.UNVERIFIED_ROOFTOP_SURVEY_REQUIRED
    approval_status: ApprovalStatus = ApprovalStatus.ACCEPTED_PROVISIONAL
    notes: str = "Provisional Salem municipal centroid. Physical rooftop RTK survey required."
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        self.validate_coordinates()

    def validate_coordinates(self) -> None:
        """Validates physical range and numerical validity of coordinates."""
        if self.latitude is None or self.longitude is None:
            raise ValueError("Coordinates latitude and longitude must not be None.")
        try:
            lat = float(self.latitude)
            lon = float(self.longitude)
        except (ValueError, TypeError):
            raise ValueError(f"Non-numeric coordinates: lat={self.latitude}, lon={self.longitude}")

        if math.isnan(lat) or math.isinf(lat) or math.isnan(lon) or math.isinf(lon):
            raise ValueError("Coordinates must be finite real numbers.")

        # Indian territorial bounds: Lat 6.0°N to 38.0°N, Lon 68.0°E to 98.0°E
        if not (6.0 <= lat <= 38.0):
            raise ValueError(f"Latitude {lat}° out of Indian subcontinent territory [6.0°, 38.0°].")
        if not (68.0 <= lon <= 98.0):
            raise ValueError(f"Longitude {lon}° out of Indian subcontinent territory [68.0°, 98.0°].")

    def is_verified_rooftop_survey(self) -> bool:
        """
        Determines whether coordinates qualify as physically verified rooftop survey.
        Strictly requires Level 1 Measured provenance, sub-meter accuracy, verified instrument,
        surveyor identity, date, and source documentation.
        """
        if self.verification_status != CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY:
            return False
        if self.provenance_level != ProvenanceLevel.LEVEL_1_MEASURED:
            return False
        if self.survey_method not in (SurveyMethod.RTK_GNSS, SurveyMethod.TOTAL_STATION):
            return False
        if self.accuracy_m is None or self.accuracy_m <= 0.0 or self.accuracy_m > 1.0:
            return False
        if not self.survey_instrument or not self.survey_instrument.strip():
            return False
        if not self.surveyor_name or not self.surveyor_name.strip():
            return False
        if not self.survey_date or not self.survey_date.strip():
            return False
        if not self.source_document or not self.source_document.strip():
            return False
        return True

    @property
    def display_status(self) -> str:
        """Returns visible status indicator for drawings and reports."""
        if self.is_verified_rooftop_survey():
            return f"VERIFIED ROOFTOP SURVEY (±{self.accuracy_m:.2f}m by {self.surveyor_name})"
        return CoordinateVerificationStatus.UNVERIFIED_ROOFTOP_SURVEY_REQUIRED.value


# ======================================================================
# WP-05: WIND INPUT VERIFICATION ENUMS & MODELS
# ======================================================================

class WindParameterCategory(str, Enum):
    CODE_DERIVED = "Statutory / Code-Derived (IS 875 Part 3: 2015)"
    SITE_MEASURED = "Site-Measured (Anemometer / Meteorological Station)"
    ENGINEER_SELECTED = "Engineer-Selected (Design Basis Selection)"
    ASSUMED_PROVISIONAL = "Assumed Provisional (Requires Verification)"


@dataclass
class WindParameterItem:
    """Individual wind load parameter with explicit codal basis and provenance."""
    parameter_key: str
    parameter_name: str
    value: Any
    units: str
    category: WindParameterCategory
    provenance_level: ProvenanceLevel
    codal_clause: str
    source_reference: str
    is_provisional: bool
    notes: str = ""


@dataclass
class WindVerificationRecord:
    """
    Transparent wind parameter verification record under IS 875 (Part 3): 2015 (WP-05).
    Reconciles statutory code provisions, Salem unlisted status, and design factors.
    """
    governing_standard: str = "IS 875 (Part 3): 2015, Third Revision (Reaffirmed 2020)"
    location_name: str = "Salem, Tamil Nadu"
    basic_wind_speed_vb: float = 39.0
    is_salem_annex_a_listed: bool = False  # Salem is NOT listed in IS 875 Annex A table!
    vb_codal_basis: str = (
        "IS 875 (Part 3): 2015 Figure 1 Regional Wind Zone Map (39 m/s contour). "
        "Salem is unlisted in Appendix A Table 1 (Selected Towns). "
        "Value is provisional interpretation subject to site verification."
    )
    risk_coefficient_k1: float = 1.0  # Clause 6.3.1 Table 1 (Mean design life 50 years)
    terrain_category: int = 3         # Clause 6.3.2 Table 2 (Suburban / industrial obstructions)
    topography_factor_k3: float = 1.0 # Clause 6.3.3 (Ground slope < 3° assumed)
    cyclonic_factor_k4: float = 1.0   # Clause 6.3.4 (Inland Salem > 60 km from east coast)
    building_height_m: float = 12.0
    rooftop_elevation_m: float = 12.0
    cpe_uplift: float = -1.10
    cpe_downward: float = +0.70
    cpi_internal: float = 0.0          # 0.0 for open canopy System A
    local_wind_effects_considered: bool = True
    load_directions: List[str] = field(default_factory=lambda: [
        "0° Windward Transverse",
        "90° Longitudinal Parallel",
        "180° Leeward Transverse",
        "270° Longitudinal Parallel",
    ])
    parameters: Dict[str, WindParameterItem] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        self._populate_parameter_register()

    def _populate_parameter_register(self) -> None:
        """Populates the comprehensive transparent parameter taxonomy."""
        # 1. Basic Wind Speed Vb
        self.parameters["basic_wind_speed_vb"] = WindParameterItem(
            parameter_key="basic_wind_speed_vb",
            parameter_name="Basic Wind Speed (Vb)",
            value=self.basic_wind_speed_vb,
            units="m/s",
            category=WindParameterCategory.ASSUMED_PROVISIONAL if not self.is_salem_annex_a_listed else WindParameterCategory.CODE_DERIVED,
            provenance_level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL if not self.is_salem_annex_a_listed else ProvenanceLevel.LEVEL_4_STATUTORY_CODE,
            codal_clause="IS 875 (Part 3): 2015 Clause 6.2 & Figure 1",
            source_reference=self.vb_codal_basis,
            is_provisional=not self.is_salem_annex_a_listed,
            notes="Salem unlisted in Annex A Table; provisional 39 m/s contour requires certified regional check.",
        )

        # 2. Risk Coefficient k1
        self.parameters["risk_coefficient_k1"] = WindParameterItem(
            parameter_key="risk_coefficient_k1",
            parameter_name="Risk Coefficient / Probability Factor (k1)",
            value=self.risk_coefficient_k1,
            units="dimensionless",
            category=WindParameterCategory.CODE_DERIVED,
            provenance_level=ProvenanceLevel.LEVEL_4_STATUTORY_CODE,
            codal_clause="IS 875 (Part 3): 2015 Clause 6.3.1 Table 1",
            source_reference="50-Year Design Return Period for General Industrial & Commercial Buildings",
            is_provisional=False,
            notes="Statutory factor for standard solar installation life.",
        )

        # 3. Terrain Category Factor k2
        self.parameters["terrain_category"] = WindParameterItem(
            parameter_key="terrain_category",
            parameter_name="Terrain Category",
            value=f"Category {self.terrain_category}",
            units="category",
            category=WindParameterCategory.ENGINEER_SELECTED,
            provenance_level=ProvenanceLevel.LEVEL_4_STATUTORY_CODE,
            codal_clause="IS 875 (Part 3): 2015 Clause 6.3.2.1 Table 2",
            source_reference="Terrain with numerous closely spaced obstructions (suburban industrial estate)",
            is_provisional=False,
            notes="Requires rooftop visual confirmation of surrounding building density within 500m.",
        )

        # 4. Topography Factor k3
        self.parameters["topography_factor_k3"] = WindParameterItem(
            parameter_key="topography_factor_k3",
            parameter_name="Topography Factor (k3)",
            value=self.topography_factor_k3,
            units="dimensionless",
            category=WindParameterCategory.ASSUMED_PROVISIONAL,
            provenance_level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
            codal_clause="IS 875 (Part 3): 2015 Clause 6.3.3 & Appendix C",
            source_reference="Assumed flat terrain with upwind slope theta < 3°",
            is_provisional=True,
            notes="Topographic survey required to confirm no escarpments, hills, or ridges within 1.5 km.",
        )

        # 5. Cyclonic Importance Factor k4
        self.parameters["cyclonic_factor_k4"] = WindParameterItem(
            parameter_key="cyclonic_factor_k4",
            parameter_name="Cyclonic Importance Factor (k4)",
            value=self.cyclonic_factor_k4,
            units="dimensionless",
            category=WindParameterCategory.CODE_DERIVED,
            provenance_level=ProvenanceLevel.LEVEL_4_STATUTORY_CODE,
            codal_clause="IS 875 (Part 3): 2015 Clause 6.3.4",
            source_reference="Inland Tamil Nadu location (> 60 km from Bay of Bengal coastline)",
            is_provisional=False,
            notes="Salem is > 150 km from coast; k4 = 1.0 applies.",
        )

        # 6. Building Height & Rooftop Elevation
        self.parameters["building_height_m"] = WindParameterItem(
            parameter_key="building_height_m",
            parameter_name="Parent Building Height (h)",
            value=self.building_height_m,
            units="m",
            category=WindParameterCategory.ASSUMED_PROVISIONAL,
            provenance_level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
            codal_clause="IS 875 (Part 3): 2015 Clause 6.3.2.2",
            source_reference="Preliminary architectural estimate (12.0 m / G+3 floors)",
            is_provisional=True,
            notes="Physical tape / laser distometer measurement of building parapet height mandatory.",
        )

        # 7. External Pressure Coefficients Cpe
        self.parameters["cpe_uplift"] = WindParameterItem(
            parameter_key="cpe_uplift",
            parameter_name="Net Wind Uplift Coefficient (Cpe/Cn)",
            value=self.cpe_uplift,
            units="coefficient",
            category=WindParameterCategory.CODE_DERIVED,
            provenance_level=ProvenanceLevel.LEVEL_4_STATUTORY_CODE,
            codal_clause="IS 875 (Part 3): 2015 Clause 7.3.3.4 Table 8",
            source_reference="Monopitch canopy roof with tilt <= 10 deg",
            is_provisional=False,
            notes="Codal pressure coefficient for canopy structure.",
        )

    def get_parameters_by_category(self, category: WindParameterCategory) -> List[WindParameterItem]:
        """Returns parameter items filtered by category."""
        return [p for p in self.parameters.values() if p.category == category]

    def has_provisional_assumptions(self) -> bool:
        """Determines if any critical wind parameter relies on provisional assumptions."""
        return any(p.is_provisional for p in self.parameters.values())

    def get_active_wind_governance_holds(self) -> List[str]:
        """Identifies governance holds mandated by wind parameter status."""
        holds = []
        if not self.is_salem_annex_a_listed:
            holds.append("WIND_COORD_UNVERIFIED_HOLD")
        if self.has_provisional_assumptions():
            holds.append("ASSUMED_DATA_CERTIFICATION_HOLD")
        return holds


# ======================================================================
# WP-06: HOST STRUCTURE & ROOF INSPECTION REGISTER
# ======================================================================

class RoofType(str, Enum):
    RCC_FLAT_SLAB = "RCC Flat Slab (Reinforced Cement Concrete)"
    PITCHED_METAL_SHEET = "Pitched Trapezoidal / Corrugated Metal Sheet"
    STANDING_SEAM_SHEET = "Standing Seam Metal Roof"
    TILED_ROOF = "Clay / Concrete Tile on Timber / Steel Truss"
    PRECAST_HOLLOW_CORE = "Precast Prestressed Hollow Core Plank"
    STRUCTURAL_STEEL_DECK = "Composite Steel Deck with Concrete Topping"
    OTHER = "Other Unclassified Host Structure"


class RoofConditionRating(str, Enum):
    EXCELLENT = "EXCELLENT (Sound, no cracking or deflection)"
    GOOD = "GOOD (Minor surface weathering, structurally sound)"
    FAIR = "FAIR (Hairline non-structural cracks, minor dampness)"
    POOR = "POOR (Significant cracking, water ponding, active spalling)"
    CRITICAL = "CRITICAL (Severe structural distress, exposed rebar, unviable)"


class CorrosionLevel(str, Enum):
    NONE = "NONE (Freshly coated / non-corroded)"
    MILD = "MILD (Superficial surface oxidation < 1% section loss)"
    MODERATE = "MODERATE (Pitting rust, 1-5% section loss)"
    SEVERE = "SEVERE (Laminar exfoliation > 5% section loss)"


class InputClassification(str, Enum):
    REQUIRED = "REQUIRED (Mandatory Engineering Parameter)"
    UPLOADED_EVIDENCE = "UPLOADED_EVIDENCE (Document Attached)"
    VERIFIED_INPUT = "VERIFIED_INPUT (Physically Measured / Tested)"
    MISSING_INPUT = "MISSING_INPUT (Data Not Provided)"
    ASSUMED_INPUT = "ASSUMED_INPUT (Provisional Default Only)"
    ENGINEERING_ACCEPTANCE = "ENGINEERING_ACCEPTANCE (RSE Approved)"


@dataclass
class RoofInspectionField:
    """Individual roof inspection item tracking value, classification, and test evidence."""
    field_key: str
    field_name: str
    value: Any
    units: str
    classification: InputClassification
    provenance_level: ProvenanceLevel
    test_method: Optional[str] = None
    evidence_document_id: Optional[str] = None
    inspector_notes: str = ""
    is_mandatory: bool = True

    @property
    def is_verified(self) -> bool:
        return (
            self.classification == InputClassification.VERIFIED_INPUT
            and self.provenance_level in (ProvenanceLevel.LEVEL_1_MEASURED, ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED)
        )


@dataclass
class RoofInspectionRegister:
    """
    Mandatory host-structure inspection register (WP-06).
    Enforces the rule: Roof capacity CANNOT be inferred from roof type alone.
    Prohibits engineering PASS when critical physical structural inputs are missing or assumed.
    """
    project_id: str
    roof_type: RoofType = RoofType.RCC_FLAT_SLAB
    condition_rating: RoofConditionRating = RoofConditionRating.FAIR
    corrosion_level: CorrosionLevel = CorrosionLevel.MILD
    inspector_name: Optional[str] = None
    inspection_date: Optional[str] = None
    inspection_company: Optional[str] = None
    fields: Dict[str, RoofInspectionField] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        self._initialize_mandatory_checklist()

    def _initialize_mandatory_checklist(self) -> None:
        """Sets up the 17 mandatory inspection fields required for structural verification."""
        checklist = [
            ("roof_type", "Host Roof Framing Type", self.roof_type.value, "category", InputClassification.ASSUMED_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Nominal RCC slab assumption"),
            ("roof_length_m", "Roof Total Length", None, "m", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Measured rooftop dimensions required"),
            ("roof_width_m", "Roof Total Width", None, "m", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Measured rooftop dimensions required"),
            ("parapet_height_m", "Rooftop Parapet Height", None, "m", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Parapet edge height for wind vortex determination"),
            ("framing_layout", "Host Building Structural Framing Grid", None, "drawing", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Beam-column framing layout drawing"),
            ("existing_purlin_spacing_mm", "Host Framing Purlin Spacing", None, "mm", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Applicable for pitched roofs"),
            ("existing_rafter_spacing_mm", "Host Framing Rafter Spacing", None, "mm", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Primary framing rafter spacing"),
            ("existing_column_locations", "Existing Column Coordinates & Grid", None, "plan", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Location of load-bearing columns"),
            ("member_sizes", "Existing Structural Member Sizes", None, "schedule", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Cross-section callouts for beams and columns"),
            ("material_grades", "Host Member Material Grades", None, "grade", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Concrete fck and steel fy material grades"),
            ("slab_thickness_mm", "RCC Slab Core Thickness", 150.0, "mm", InputClassification.ASSUMED_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Provisional 150mm assumption — core drill or NDT required"),
            ("concrete_strength_mpa", "Concrete Compressive Strength", 20.0, "MPa", InputClassification.ASSUMED_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Provisional M20 assumption — rebound hammer or core test required"),
            ("reinforcement_details", "Slab & Beam Rebar Reinforcement Details", None, "schedule", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Bar diameters, spacing, and cover depth"),
            ("roof_condition_rating", "Host Roof Condition Assessment", self.condition_rating.value, "rating", InputClassification.ASSUMED_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Visual structural inspection report required"),
            ("corrosion_level", "Steel / Rebar Corrosion Level", self.corrosion_level.value, "rating", InputClassification.ASSUMED_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Corrosion assessment report required"),
            ("cracking_observations", "Structural Cracking & Deflection Survey", None, "report", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Mapping of flexural, shear, or thermal cracks"),
            ("anchor_locations_edge_distances", "Anchor Placement & Edge Distances", None, "mm", InputClassification.MISSING_INPUT, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL, None, "Available concrete edge distance c_min and embedment depth"),
        ]

        for key, name, val, units, cls_type, prov, test_m, notes in checklist:
            self.fields[key] = RoofInspectionField(
                field_key=key,
                field_name=name,
                value=val,
                units=units,
                classification=cls_type,
                provenance_level=prov,
                test_method=test_m,
                inspector_notes=notes,
                is_mandatory=True,
            )

    def set_field_evidence(
        self,
        field_key: str,
        value: Any,
        classification: InputClassification,
        provenance_level: ProvenanceLevel,
        test_method: Optional[str] = None,
        evidence_document_id: Optional[str] = None,
        inspector_notes: str = "",
    ) -> None:
        """Updates a field with verifiable physical evidence."""
        if field_key not in self.fields:
            raise KeyError(f"Field '{field_key}' is not a recognized mandatory inspection parameter.")
        self.fields[field_key] = RoofInspectionField(
            field_key=field_key,
            field_name=self.fields[field_key].field_name,
            value=value,
            units=self.fields[field_key].units,
            classification=classification,
            provenance_level=provenance_level,
            test_method=test_method,
            evidence_document_id=evidence_document_id,
            inspector_notes=inspector_notes,
            is_mandatory=True,
        )

    def audit_completeness(self) -> Dict[str, Any]:
        """Audits the inspection register and classifies parameters into discrete status buckets."""
        missing = [f.field_name for f in self.fields.values() if f.classification == InputClassification.MISSING_INPUT]
        assumed = [f.field_name for f in self.fields.values() if f.classification == InputClassification.ASSUMED_INPUT]
        verified = [f.field_name for f in self.fields.values() if f.is_verified]

        total = len(self.fields)
        complete_cnt = len(verified)
        pct = round((complete_cnt / total) * 100) if total > 0 else 0

        is_complete = (len(missing) == 0 and len(assumed) == 0)

        return {
            "total_mandatory_fields": total,
            "verified_fields_count": len(verified),
            "assumed_fields_count": len(assumed),
            "missing_fields_count": len(missing),
            "completeness_percent": pct,
            "is_complete": is_complete,
            "status": "COMPLETE" if is_complete else ("PROVISIONAL" if len(missing) == 0 else "INCOMPLETE"),
            "verified_fields": verified,
            "assumed_fields": assumed,
            "missing_fields": missing,
        }

    def can_certify_roof_capacity(self) -> Tuple[bool, List[str]]:
        """
        Determines whether host building structural capacity can be certified.
        STRICT CODICIL: Host roof capacity CANNOT be inferred from roof type alone.
        Physical testing or signed as-built drawings are strictly mandatory.
        """
        reasons = []

        # 1. Concrete strength check
        fc = self.fields.get("concrete_strength_mpa")
        if not fc or not fc.is_verified:
            reasons.append("Concrete compressive strength (fck) is unverified (NDT / core test report missing).")

        # 2. Slab thickness check
        th = self.fields.get("slab_thickness_mm")
        if not th or not th.is_verified:
            reasons.append("Slab thickness is unverified (Physical measurement / ultrasonic gauge missing).")

        # 3. Framing member sizes
        mem = self.fields.get("member_sizes")
        if not mem or not mem.is_verified:
            reasons.append("Host building framing member sizes are unverified (As-built drawings missing).")

        # 4. Rebar reinforcement
        reb = self.fields.get("reinforcement_details")
        if not reb or not reb.is_verified:
            reasons.append("Reinforcement schedule is unverified (Ferroscan / structural drawings missing).")

        # 5. Condition rating
        if self.condition_rating in (RoofConditionRating.POOR, RoofConditionRating.CRITICAL):
            reasons.append(f"Host structure condition is rated {self.condition_rating.name} (Requires rehabilitation).")

        can_certify = (len(reasons) == 0)
        return can_certify, reasons


# ======================================================================
# WP-04 / 05 / 06 CONSOLIDATED SITE VALIDATOR & BASELINE FACTORY
# ======================================================================

class SiteInputValidator:
    """
    Consolidated engineering validator for Site Coordinates, Wind Inputs,
    and Roof Inspection data (Phase 1.5.2).
    """

    @staticmethod
    def create_salem_baseline(project_id: str = "RS-STR-RENSUN-2026-0059") -> Tuple[SiteCoordinateRecord, WindVerificationRecord, RoofInspectionRegister]:
        """
        Constructs the authoritative baseline for project RS-STR-RENSUN-2026-0059:
        - Coordinates: 11.6643°N, 78.1460°E (PROVISIONAL municipal centroid).
        - Wind Speed: 39.0 m/s (IS 875 Fig. 1 regional contour; UNLISTED in Annex A).
        - Roof: RCC Flat Slab (Assumed 150mm, M20, NDT/rebar MISSING).
        - Governance: All 12 Canonical Holds Enforced | AFC Locked.
        """
        coords = SiteCoordinateRecord(
            latitude=11.6643,
            longitude=78.1460,
            location_name="90 ERUMAPALAYAM ITTERI ROAD, SALEM",
            survey_method=SurveyMethod.PROVISIONAL_CENTROID,
            survey_instrument=None,
            accuracy_m=None,
            surveyor_name=None,
            source_document="Salem Municipal Area Centroid",
            provenance_level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
            verification_status=CoordinateVerificationStatus.UNVERIFIED_ROOFTOP_SURVEY_REQUIRED,
            approval_status=ApprovalStatus.ACCEPTED_PROVISIONAL,
            notes="Provisional Salem municipal centroid (11.6643°N, 78.1460°E). Physical rooftop RTK survey required.",
        )

        wind = WindVerificationRecord(
            governing_standard="IS 875 (Part 3): 2015, Third Revision (Reaffirmed 2020)",
            location_name="Salem, Tamil Nadu",
            basic_wind_speed_vb=39.0,
            is_salem_annex_a_listed=False,
            vb_codal_basis="IS 875 (Part 3): 2015 Figure 1 Regional Contour Map (39 m/s contour). Unlisted in Annex A Table.",
            risk_coefficient_k1=1.0,
            terrain_category=3,
            topography_factor_k3=1.0,
            cyclonic_factor_k4=1.0,
            building_height_m=12.0,
            rooftop_elevation_m=12.0,
            cpe_uplift=-1.10,
            cpe_downward=+0.70,
            cpi_internal=0.0,
        )

        roof = RoofInspectionRegister(
            project_id=project_id,
            roof_type=RoofType.RCC_FLAT_SLAB,
            condition_rating=RoofConditionRating.FAIR,
            corrosion_level=CorrosionLevel.MILD,
            inspector_name=None,
            inspection_date=None,
        )

        return coords, wind, roof

    @staticmethod
    def audit_project_site_validation(
        coords: SiteCoordinateRecord,
        wind: WindVerificationRecord,
        roof: RoofInspectionRegister,
    ) -> Dict[str, Any]:
        """
        Audits consolidated site inputs and calculates overall engineering validity:
        - Numerical PASS is strictly decoupled from engineering verification.
        - Missing or assumed inputs strictly prevent Engineering PASS.
        - Active holds are deterministically identified.
        """
        coord_verified = coords.is_verified_rooftop_survey()
        wind_provisional = wind.has_provisional_assumptions()
        can_certify_roof, roof_reasons = roof.can_certify_roof_capacity()
        roof_audit = roof.audit_completeness()

        # Compile active holds
        active_holds = []
        if not coord_verified:
            active_holds.append("WIND_COORD_UNVERIFIED_HOLD")
        if wind_provisional or roof_audit["assumed_fields_count"] > 0:
            active_holds.append("ASSUMED_DATA_CERTIFICATION_HOLD")
        if not can_certify_roof or roof_audit["missing_fields_count"] > 0:
            active_holds.append("INSPECTION_REQUIRED_HOLD")

        # Compile outstanding physical evidence list
        required_evidence = []
        if not coord_verified:
            required_evidence.append("Rooftop RTK GNSS / Total Station survey coordinates with certificate (< 1.0m accuracy).")
        if not wind.is_salem_annex_a_listed:
            required_evidence.append("Site-specific wind study or local meteorological station certification for Salem basic wind speed.")
        if wind.parameters["topography_factor_k3"].is_provisional:
            required_evidence.append("Topographic elevation profile confirming upwind slope < 3° within 1.5 km.")
        if not roof.fields["concrete_strength_mpa"].is_verified:
            required_evidence.append("Host building concrete rebound hammer (IS 13311 Part 2) or core compressive test report.")
        if not roof.fields["slab_thickness_mm"].is_verified:
            required_evidence.append("Host building slab thickness physical gauge / core drill measurement.")
        if not roof.fields["reinforcement_details"].is_verified:
            required_evidence.append("Host building as-built structural drawings or Ferroscan non-destructive rebar layout report.")
        if not roof.fields["framing_layout"].is_verified:
            required_evidence.append("Host building structural framing layout drawing showing beams, columns, and spans.")

        # Determine engineering status
        if len(required_evidence) > 0 or not coord_verified or not can_certify_roof:
            engineering_status = "UNVERIFIED_MISSING_PHYSICAL_EVIDENCE"
            overall_pass = False
        else:
            engineering_status = "READY_FOR_INDEPENDENT_RSE_REVIEW"
            overall_pass = True

        return {
            "coordinate_status": coords.display_status,
            "is_coordinate_verified": coord_verified,
            "wind_standard": wind.governing_standard,
            "is_salem_annex_a_listed": wind.is_salem_annex_a_listed,
            "has_wind_provisional_assumptions": wind_provisional,
            "roof_type": roof.roof_type.value,
            "roof_audit": roof_audit,
            "can_certify_roof_capacity": can_certify_roof,
            "roof_deficiencies": roof_reasons,
            "active_site_holds": list(set(active_holds)),
            "engineering_status": engineering_status,
            "construction_status": "BLOCKED_AFC_LOCKED",
            "is_engineering_pass_permitted": overall_pass,
            "required_physical_evidence_from_owner": required_evidence,
        }
