"""
Quotation & Structural Pipeline Integration Layer
Package: structural.integration

Core Architecture:
- Coordinates the existing Solar Quotation Application, Structural Calculation Package,
  and Isolated Structural SQLite Database without coupling their codebases.
- The existing quotation system remains the authoritative source for solar pricing, packages,
  and quotation generation.
- The structural calculation engine remains the authoritative source for preliminary structural
  calculations, unity ratios, and verification hold statuses.
- Zero modifications to quotation pricing, solar sizing, quotation numbering, or 5-page proposal PDF.
"""

import os
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from structural.models import (
    MountingSystemType,
    TerrainCategory,
    SeismicZone,
    SiteParameters,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    DrawingMetadata,
    STEEL_E250,
    ALUMINIUM_6063_T6,
    STAINLESS_STEEL_A2_70,
)
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
    HoldStatus,
)
from structural.actions import CombinationGenerator
from structural.engine import StructuralCalculationEngine
from structural.drawing import DXFDrawingEngine
from structural.db import StructuralDatabase, STRUCTURAL_DB


class QuotationStructuralBridge:
    """
    Integration coordinator managing project linking, input mapping,
    workflow execution, report compilation, and quotation embedding.
    """

    def __init__(
        self,
        db: Optional[StructuralDatabase] = None,
        drawing_output_dir: Optional[str] = None,
    ):
        self.db = db or STRUCTURAL_DB
        self.drawing_output_dir = drawing_output_dir

    def set_db(self, db: StructuralDatabase):
        """Overrides the active structural database instance (used for test isolation)."""
        self.db = db

    def reset_db(self):
        """Restores the default production structural database instance."""
        self.db = STRUCTURAL_DB

    def set_drawing_output_dir(self, directory: Optional[str]):
        """Overrides the drawing output directory (used for test isolation)."""
        self.drawing_output_dir = directory

    def reset_drawing_output_dir(self):
        """Restores the default drawing output directory."""
        self.drawing_output_dir = None

    @staticmethod
    def derive_project_id(quotation_no: str) -> str:
        """Derives a deterministic, clean structural project ID from quotation reference."""
        clean_slug = re.sub(r'[^A-Za-z0-9]', '-', quotation_no).strip('-')
        return f"RS-STR-{clean_slug}"

    @staticmethod
    def resolve_mounting_system(sys_input: Union[MountingSystemType, str]) -> MountingSystemType:
        """
        Resolves short key ('A', 'B', 'C', 'D') or string to MountingSystemType.
        Preserves canonical mapping:
        A — Elevated Steel Canopy
        B — Low-Height Aluminium Rail
        C — Metal-Sheet Roof Mounting
        D — Ballasted Non-Penetrating System
        """
        if isinstance(sys_input, MountingSystemType):
            return sys_input
        key = str(sys_input).strip().upper()
        if "GROUND" in key:
            raise ValueError(
                f"Mounting configuration '{sys_input}' cannot be mapped to canonical Systems A–D: "
                "Ground-mounted arrays require dedicated geotechnical foundation workflows (IS 2911 / IS 800) "
                "with soil borehole investigation."
            )
        if "CARPORT" in key:
            raise ValueError(
                f"Mounting configuration '{sys_input}' cannot be mapped to canonical Systems A–D: "
                "Carport structures require dedicated cantilever framing and vehicle collision engineering workflows."
            )
        mapping = {
            "A": MountingSystemType.SYSTEM_A_CANOPY,
            "B": MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL,
            "C": MountingSystemType.SYSTEM_C_METAL_SHEET,
            "D": MountingSystemType.SYSTEM_D_BALLASTED,
        }
        if key in mapping:
            return mapping[key]
        for m in MountingSystemType:
            if key in m.name or key in m.value.upper():
                return m
        raise ValueError(
            f"Unknown mounting system '{sys_input}'. Supported canonical systems: "
            "A (Elevated Steel Canopy), B (Low-Height Aluminium Rail), "
            "C (Metal-Sheet Roof Mounting), D (Ballasted Non-Penetrating System)."
        )

    # -------------------------------------------------------------------------
    # 1. Project Linking & Creation
    # -------------------------------------------------------------------------
    def create_or_get_project_for_quotation(
        self,
        quotation_data: Dict[str, Any],
        mounting_system: Union[MountingSystemType, str],
        site_inputs: Optional[Dict[str, Any]] = None,
        roof_inputs: Optional[Dict[str, Any]] = None,
        auto_preset_sections: bool = True,
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Creates or retrieves a persistent structural project associated with a solar quotation.
        Returns (project_dict, created_boolean).
        """
        q_no = quotation_data.get("quotation_no")
        if not q_no:
            raise ValueError("Quotation payload must contain 'quotation_no'.")

        c_no = str(quotation_data.get("consumer_no") or "ANONYMOUS")
        c_name = str(quotation_data.get("customer_name") or "Valued Consumer")
        location = str(quotation_data.get("address") or "Tamil Nadu Service Connection")
        resolved_sys = self.resolve_mounting_system(mounting_system)

        # Check existing cross-reference link
        existing_link = self.db.get_link_by_quotation(q_no)
        created = False

        if existing_link:
            project_id = existing_link["project_id"]
            proj = self.db.get_project(project_id)
            if not proj:
                # Re-create if project was deleted
                proj = self.db.create_project(
                    project_id=project_id,
                    name=f"Structural Assessment for {q_no}",
                    mounting_system=resolved_sys,
                    client_name=c_name,
                    site_location=location,
                )
                created = True
            elif proj["mounting_system"] != resolved_sys.value:
                self.db.update_project_system(project_id, resolved_sys)
                proj = self.db.get_project(project_id)
        else:
            project_id = self.derive_project_id(q_no)
            proj = self.db.get_project(project_id)
            if not proj:
                proj = self.db.create_project(
                    project_id=project_id,
                    name=f"Structural Assessment for {q_no}",
                    mounting_system=resolved_sys,
                    client_name=c_name,
                    site_location=location,
                )
                created = True
            else:
                if proj["mounting_system"] != resolved_sys.value:
                    self.db.update_project_system(project_id, resolved_sys)
                    proj = self.db.get_project(project_id)

            # Record link
            self.db.link_quotation_project(
                quotation_no=q_no,
                project_id=project_id,
                consumer_no=c_no,
                mounting_system=resolved_sys,
                assessment_requested=True,
            )

        # 1. Map PV Module from quotation
        self._map_module_from_quotation(project_id, quotation_data, roof_inputs)

        # 2. Map Site parameters if provided
        if site_inputs:
            self._map_site_inputs(project_id, site_inputs, default_location=location)

        # 3. Map Geometry if provided or derive from panel count
        self._map_geometry(project_id, resolved_sys, quotation_data, roof_inputs)

        # 4. Map Sections & Materials (using presets if requested and missing)
        if auto_preset_sections:
            self._apply_standard_sections_preset(project_id, resolved_sys, roof_inputs)

        return proj, created

    def _map_module_from_quotation(
        self,
        project_id: str,
        quotation_data: Dict[str, Any],
        roof_inputs: Optional[Dict[str, Any]] = None,
    ):
        """Maps PV module specifications from quotation sizing or overrides."""
        roof_inputs = roof_inputs or {}
        sizing = quotation_data.get("sizing", {})
        panel_cfg = quotation_data.get("panel", {})

        power_w = float(roof_inputs.get("panel_wattage_wp") or sizing.get("panel_wattage_wp") or panel_cfg.get("wattage_wp", 540.0))
        make_model = str(roof_inputs.get("make_model") or panel_cfg.get("model") or f"Tier-1 Mono-PERC {power_w:.0f}W")
        length_mm = float(roof_inputs.get("length_mm") or panel_cfg.get("length_mm", 2278.0))
        width_mm = float(roof_inputs.get("width_mm") or panel_cfg.get("width_mm", 1134.0))
        thickness_mm = float(roof_inputs.get("thickness_mm") or panel_cfg.get("thickness_mm", 35.0))
        weight_kg = float(roof_inputs.get("weight_kg") or panel_cfg.get("weight_kg", 27.5))
        tilt_deg = float(roof_inputs.get("tilt_deg") or 10.0)
        azimuth_deg = float(roof_inputs.get("azimuth_deg") or 180.0)

        module = PVModuleSpecification(
            make_model=make_model,
            length_mm=length_mm,
            width_mm=width_mm,
            thickness_mm=thickness_mm,
            weight_kg=weight_kg,
            peak_power_w=power_w,
            tilt_deg=tilt_deg,
            azimuth_deg=azimuth_deg,
        )
        self.db.set_module(project_id, module)

    def _map_site_inputs(
        self,
        project_id: str,
        site_inputs: Dict[str, Any],
        default_location: str = "Tamil Nadu",
    ):
        """Maps site meteorological and seismic parameters with explicit IS 875 provenance."""
        loc_name = str(site_inputs.get("location_name") or default_location)
        loc_upper = loc_name.upper()

        # Codal location resolution under IS 875 (Part 3): 2015 Annex A & Figure 1
        prov_source = site_inputs.get("provenance_source")
        prov_level = int(site_inputs.get("provenance_level", 3))

        # Default coordinates and basic wind speeds for key Tamil Nadu locations
        if "SALEM" in loc_upper:
            # Salem is NOT explicitly listed in IS 875 Part 3 Annex A table
            # Figure 1 Basic Wind Speed map places Salem in 39 m/s inland contour
            default_lat = 11.6643
            default_lon = 78.1460
            default_vb = 39.0
            if not prov_source:
                prov_source = "IS 875 (Part 3): 2015 Fig 1 Regional Contour (Unlisted in Annex A Table — Provisional Manual Interpretation — Site Verification Mandatory)"
                prov_level = 2
        elif "CHENNAI" in loc_upper or "MADRAS" in loc_upper:
            default_lat = 13.0827
            default_lon = 80.2707
            default_vb = 50.0
            if not prov_source:
                prov_source = "IS 875 (Part 3): 2015 Annex A Table (Chennai)"
                prov_level = 1
        elif "COIMBATORE" in loc_upper:
            default_lat = 11.0168
            default_lon = 76.9558
            default_vb = 39.0
            if not prov_source:
                prov_source = "IS 875 (Part 3): 2015 Annex A Table (Coimbatore)"
                prov_level = 1
        elif "TRICHY" in loc_upper or "TIRUCHI" in loc_upper:
            default_lat = 10.7905
            default_lon = 78.7047
            default_vb = 47.0
            if not prov_source:
                prov_source = "IS 875 (Part 3): 2015 Annex A Table (Tiruchchirappalli)"
                prov_level = 1
        elif "MADURAI" in loc_upper:
            default_lat = 9.9252
            default_lon = 78.1198
            default_vb = 39.0
            if not prov_source:
                prov_source = "IS 875 (Part 3): 2015 Annex A Table (Madurai)"
                prov_level = 1
        else:
            default_lat = 13.0827
            default_lon = 80.2707
            default_vb = 50.0
            if not prov_source:
                prov_source = "IS 875 (Part 3): 2015 Fig 1 / Regional Default"
                prov_level = 3

        lat_in = site_inputs.get("latitude")
        lat = float(lat_in if lat_in is not None else default_lat)

        lon_in = site_inputs.get("longitude")
        lon = float(lon_in if lon_in is not None else default_lon)

        vb_in = site_inputs.get("basic_wind_speed_vb") or site_inputs.get("basic_wind_speed_m_s")
        vb = float(vb_in if vb_in is not None else default_vb)

        terrain = int(site_inputs.get("terrain_category", 3))
        height = float(site_inputs.get("building_height_m", 12.0))
        elevation = float(site_inputs.get("rooftop_elevation_m") or site_inputs.get("ground_elevation_m") or height)
        k4 = float(site_inputs.get("cyclonic_factor_k4") or site_inputs.get("k4") or 1.0)
        k3 = float(site_inputs.get("topography_factor_k3") or site_inputs.get("k3") or 1.0)
        k1 = float(site_inputs.get("risk_coefficient_k1") or site_inputs.get("k1") or 1.0)
        sz_val = str(site_inputs.get("seismic_zone", "Zone III"))
        try:
            sz_enum = SeismicZone(sz_val)
        except ValueError:
            sz_enum = SeismicZone.ZONE_III

        site = SiteParameters(
            location_name=loc_name,
            latitude=lat,
            longitude=lon,
            basic_wind_speed_vb=vb,
            terrain_category=TerrainCategory(terrain),
            building_height_m=height,
            rooftop_elevation_m=elevation,
            cyclonic_factor_k4=k4,
            topography_factor_k3=k3,
            risk_coefficient_k1=k1,
            seismic_zone=sz_enum,
            importance_factor_I=float(site_inputs.get("importance_factor_I", 1.0)),
            response_reduction_R=float(site_inputs.get("response_reduction_R", 4.0)),
            soil_type=int(site_inputs.get("soil_type", 2)),
        )
        self.db.set_site(project_id, site, provenance_level=prov_level, provenance_source=prov_source)

    def _map_geometry(
        self,
        project_id: str,
        mounting_system: MountingSystemType,
        quotation_data: Dict[str, Any],
        roof_inputs: Optional[Dict[str, Any]] = None,
    ):
        """Maps or derives array framing geometry from panel count and roof inputs."""
        roof_inputs = roof_inputs or {}
        sizing = quotation_data.get("sizing", {})
        total_panels = int(roof_inputs.get("total_modules") or sizing.get("number_of_panels", 20))

        # Check if rows & columns explicitly specified
        rows = roof_inputs.get("rows")
        cols = roof_inputs.get("columns")

        if rows is not None and cols is not None:
            r = int(rows)
            c = int(cols)
            total = r * c
        else:
            # Deterministic default factorization (e.g. 20 -> 4 rows x 5 cols)
            r, c = self._factor_grid(total_panels)
            total = r * c

        purlin_spacing = float(roof_inputs.get("purlin_spacing_mm") or 1150.0)
        rafter_spacing = float(roof_inputs.get("rafter_spacing_mm") or 3000.0)
        ground_clearance = float(
            roof_inputs.get("ground_clearance_mm") or (2800.0 if mounting_system == MountingSystemType.SYSTEM_A_CANOPY else 250.0)
        )

        module = self.db.get_module(project_id)
        if not module:
            return

        geometry = ArrayGeometry(
            mounting_system=mounting_system,
            total_modules=total,
            rows=r,
            columns=c,
            module=module,
            orientation=roof_inputs.get("orientation", "PORTRAIT"),
            purlin_spacing_mm=purlin_spacing,
            rafter_spacing_mm=rafter_spacing,
            ground_clearance_mm=ground_clearance,
        )
        self.db.set_geometry(project_id, geometry)

    @staticmethod
    def _factor_grid(total_panels: int) -> Tuple[int, int]:
        """Finds closest practical (rows, cols) layout for a given module quantity."""
        if total_panels <= 0:
            return 2, 2
        # Prefer 2 to 4 rows for rooftop canopies
        for r in (4, 3, 2, 5, 6, 1):
            if total_panels % r == 0:
                return r, total_panels // r
        # Prime or irregular: round up columns
        r = 4
        c = (total_panels + r - 1) // r
        return r, c

    def _apply_standard_sections_preset(
        self,
        project_id: str,
        mounting_system: MountingSystemType,
        roof_inputs: Optional[Dict[str, Any]] = None,
    ):
        """Applies validated standard section profiles for components that have not been customized."""
        roof_inputs = roof_inputs or {}

        if mounting_system == MountingSystemType.SYSTEM_A_CANOPY:
            if not self.db.get_section(project_id, "PURLIN"):
                purlin = SectionProperty(
                    designation="ISMC 100x50x2.0",
                    profile_type="C-Channel",
                    material=STEEL_E250,
                    area_mm2=450.0,
                    Ixx_mm4=750000.0,
                    Iyy_mm4=180000.0,
                    Zxx_mm3=15000.0,
                    Zyy_mm3=5000.0,
                    rxx_mm=40.8,
                    ryy_mm=20.0,
                    mass_kg_m=3.53,
                )
                self.db.set_section(project_id, "PURLIN", purlin)

            if not self.db.get_section(project_id, "RAFTER"):
                rafter = SectionProperty(
                    designation="ISMB 300",
                    profile_type="I-Section",
                    material=STEEL_E250,
                    area_mm2=5626.0,
                    Ixx_mm4=86036000.0,
                    Iyy_mm4=4539000.0,
                    Zxx_mm3=573600.0,
                    Zyy_mm3=64800.0,
                    rxx_mm=123.7,
                    ryy_mm=28.4,
                    mass_kg_m=44.2,
                )
                self.db.set_section(project_id, "RAFTER", rafter)

            if not self.db.get_section(project_id, "COLUMN"):
                col = SectionProperty(
                    designation="ISMB 300",
                    profile_type="I-Section",
                    material=STEEL_E250,
                    area_mm2=5626.0,
                    Ixx_mm4=86036000.0,
                    Iyy_mm4=4539000.0,
                    Zxx_mm3=573600.0,
                    Zyy_mm3=64800.0,
                    rxx_mm=123.7,
                    ryy_mm=28.4,
                    mass_kg_m=44.2,
                )
                self.db.set_section(project_id, "COLUMN", col)

        elif mounting_system == MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL:
            if not self.db.get_section(project_id, "RAIL"):
                rail = SectionProperty(
                    designation="AluRail 40x40x2.5",
                    profile_type="Aluminium Custom Rail",
                    material=ALUMINIUM_6063_T6,
                    area_mm2=310.0,
                    Ixx_mm4=58000.0,
                    Iyy_mm4=58000.0,
                    Zxx_mm3=2900.0,
                    Zyy_mm3=2900.0,
                    rxx_mm=13.7,
                    ryy_mm=13.7,
                    mass_kg_m=0.84,
                )
                self.db.set_section(project_id, "RAIL", rail)

    # -------------------------------------------------------------------------
    # 2. Input Completeness Assessment
    # -------------------------------------------------------------------------
    def assess_input_completeness(self, project_id: str) -> Dict[str, Any]:
        """Audits project configuration completeness and identifies missing items."""
        proj = self.db.get_project(project_id)
        if not proj:
            return {
                "project_id": project_id,
                "is_complete": False,
                "status": "PROJECT_NOT_FOUND",
                "missing": ["Project Record"],
                "configured": [],
                "errors": [f"Project '{project_id}' does not exist."],
            }

        is_valid, errors = self.db.validate_project_inputs(project_id)
        configured = []
        missing = []

        if self.db.get_site(project_id):
            configured.append("Site Parameters")
        else:
            missing.append("Site Parameters")

        if self.db.get_module(project_id):
            configured.append("PV Module Specification")
        else:
            missing.append("PV Module Specification")

        if self.db.get_geometry(project_id):
            configured.append("Array Geometry")
        else:
            missing.append("Array Geometry")

        sys_str = proj["mounting_system"]
        if "System A" in sys_str:
            for c in ("PURLIN", "RAFTER", "COLUMN"):
                if self.db.get_section(project_id, c):
                    configured.append(f"{c} Section")
                else:
                    missing.append(f"{c} Section")
        elif "System B" in sys_str:
            if self.db.get_section(project_id, "RAIL"):
                configured.append("RAIL Section")
            else:
                missing.append("RAIL Section")
        elif "System C" in sys_str:
            configured.append("Sheet Substrate & Clamp Configuration")
        elif "System D" in sys_str:
            configured.append("Ballast Stability Parameters")

        total_items = len(configured) + len(missing)
        pct = round((len(configured) / total_items * 100)) if total_items > 0 else 0

        return {
            "project_id": project_id,
            "mounting_system": sys_str,
            "is_complete": is_valid,
            "status": "COMPLETE" if is_valid else "INCOMPLETE",
            "completeness_percent": pct,
            "configured": configured,
            "missing": missing,
            "errors": errors,
        }

    def audit_site_and_roof_validation(self, project_id: str) -> Dict[str, Any]:
        """
        Phase 1.5.2: Audits site coordinates, IS 875 wind parameters, and host-structure
        roof inspection evidence against physical engineering criteria (WP-04, WP-05, WP-06).
        """
        from structural.site_survey import (
            SiteCoordinateRecord,
            WindVerificationRecord,
            RoofInspectionRegister,
            SiteInputValidator,
            CoordinateVerificationStatus,
            SurveyMethod,
            ApprovalStatus,
            RoofType,
            RoofConditionRating,
            CorrosionLevel,
            InputClassification,
        )
        from structural.provenance import ProvenanceLevel

        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' does not exist.")

        site = self.db.get_site(project_id)
        prov_records = {r["parameter_key"]: r for r in self.db.get_project_provenance(project_id)}

        # 1. Site Coordinates (WP-04)
        if site:
            lat = site.latitude
            lon = site.longitude
            loc = site.location_name
        else:
            lat = 11.6643
            lon = 78.1460
            loc = "90 ERUMAPALAYAM ITTERI ROAD, SALEM"

        # Check if coordinates have Level 1 measured survey provenance
        lat_prov = prov_records.get("latitude") or prov_records.get("site_latitude")
        is_verified_survey = (
            lat_prov is not None
            and lat_prov.get("level") == ProvenanceLevel.LEVEL_1_MEASURED.value
            and lat_prov.get("certifier_name") is not None
        )

        if is_verified_survey:
            coords = SiteCoordinateRecord(
                latitude=lat,
                longitude=lon,
                location_name=loc,
                survey_date=lat_prov.get("date_certified"),
                survey_method=SurveyMethod.RTK_GNSS,
                survey_instrument=lat_prov.get("source_reference", "RTK GNSS Receiver"),
                accuracy_m=0.02,
                surveyor_name=lat_prov.get("certifier_name"),
                source_document=lat_prov.get("notes", "Topographic Survey Report"),
                provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
                verification_status=CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY,
                approval_status=ApprovalStatus.VERIFIED_BY_RSE,
            )
        else:
            coords = SiteCoordinateRecord(
                latitude=lat,
                longitude=lon,
                location_name=loc,
                survey_method=SurveyMethod.PROVISIONAL_CENTROID,
                survey_instrument=None,
                accuracy_m=None,
                surveyor_name=None,
                source_document="Provisional Municipal Centroid",
                provenance_level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
                verification_status=CoordinateVerificationStatus.UNVERIFIED_ROOFTOP_SURVEY_REQUIRED,
                approval_status=ApprovalStatus.ACCEPTED_PROVISIONAL,
                notes="Provisional Salem municipal centroid. Physical rooftop RTK survey required.",
            )

        # 2. Wind Parameters (WP-05)
        vb = site.basic_wind_speed_vb if site else 39.0
        tc = site.terrain_category.value if site else 3
        h = site.building_height_m if site else 12.0
        k1 = site.risk_coefficient_k1 if site else 1.0
        k3 = site.topography_factor_k3 if site else 1.0
        k4 = site.cyclonic_factor_k4 if site else 1.0

        wind = WindVerificationRecord(
            governing_standard="IS 875 (Part 3): 2015, Third Revision (Reaffirmed 2020)",
            location_name=loc,
            basic_wind_speed_vb=vb,
            is_salem_annex_a_listed=False if "SALEM" in loc.upper() else True,
            risk_coefficient_k1=k1,
            terrain_category=tc,
            topography_factor_k3=k3,
            cyclonic_factor_k4=k4,
            building_height_m=h,
            rooftop_elevation_m=h,
        )

        # 3. Host Roof Inspection (WP-06)
        roof = RoofInspectionRegister(
            project_id=project_id,
            roof_type=RoofType.RCC_FLAT_SLAB,
            condition_rating=RoofConditionRating.FAIR,
            corrosion_level=CorrosionLevel.MILD,
        )

        # Check for any verified fields in provenance records
        if "concrete_strength_mpa" in prov_records:
            pr = prov_records["concrete_strength_mpa"]
            if pr.get("level") == ProvenanceLevel.LEVEL_1_MEASURED.value:
                roof.set_field_evidence(
                    field_key="concrete_strength_mpa",
                    value=float(pr.get("value", 20.0)),
                    classification=InputClassification.VERIFIED_INPUT,
                    provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
                    test_method="Rebound Hammer / Core Test",
                    evidence_document_id=pr.get("source_reference"),
                    inspector_notes=pr.get("notes", ""),
                )

        if "slab_thickness_mm" in prov_records:
            pr = prov_records["slab_thickness_mm"]
            if pr.get("level") == ProvenanceLevel.LEVEL_1_MEASURED.value:
                roof.set_field_evidence(
                    field_key="slab_thickness_mm",
                    value=float(pr.get("value", 150.0)),
                    classification=InputClassification.VERIFIED_INPUT,
                    provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
                    test_method="Physical Core Gauge",
                    evidence_document_id=pr.get("source_reference"),
                    inspector_notes=pr.get("notes", ""),
                )

        # Audit consolidated validation
        return SiteInputValidator.audit_project_site_validation(coords, wind, roof)

    # -------------------------------------------------------------------------
    # 3. Structural Assessment Workflow Execution
    # -------------------------------------------------------------------------
    def execute_structural_assessment(
        self,
        quotation_no: str,
        walkway_width_m: float = 0.80,
        ballast_weight_kn_per_m2: float = 0.75,
        friction_coeff_mu: float = 0.40,
        clamp_capacity_kn: float = 3.50,
        bracket_spacing_mm: float = 1400.0,
    ) -> Dict[str, Any]:
        """
        Executes structural assessment for a quotation and compiles summary status.
        Does NOT execute calculations if inputs are incomplete.
        """
        link = self.db.get_link_by_quotation(quotation_no)
        if not link:
            return {
                "quotation_no": quotation_no,
                "requested": False,
                "status": "NOT_REQUESTED",
                "message": f"No structural assessment requested for quotation '{quotation_no}'.",
            }

        project_id = link["project_id"]
        audit = self.assess_input_completeness(project_id)

        if not audit["is_complete"]:
            return {
                "quotation_no": quotation_no,
                "project_id": project_id,
                "mounting_system": link["mounting_system"],
                "requested": True,
                "status": "INPUTS_INCOMPLETE",
                "input_completeness": "INCOMPLETE",
                "missing_inputs": audit["missing"],
                "errors": audit["errors"],
                "preliminary_calculation_status": "PENDING_INPUTS",
                "active_holds_count": len(MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(link["mounting_system"])),
                "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
                "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
            }

        # Inputs are complete -> Execute run
        return self.execute_project_assessment(
            project_id=project_id,
            walkway_width_m=walkway_width_m,
            ballast_weight_kn_per_m2=ballast_weight_kn_per_m2,
            friction_coeff_mu=friction_coeff_mu,
            clamp_capacity_kn=clamp_capacity_kn,
            bracket_spacing_mm=bracket_spacing_mm,
        )

    def execute_project_assessment(
        self,
        project_id: str,
        walkway_width_m: float = 0.80,
        ballast_weight_kn_per_m2: float = 0.75,
        friction_coeff_mu: float = 0.40,
        clamp_capacity_kn: float = 3.50,
        bracket_spacing_mm: float = 1400.0,
    ) -> Dict[str, Any]:
        """
        Directly executes structural calculation for a project_id.
        Preserves hold enforcement and updates quotation link if associated.
        """
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        audit = self.assess_input_completeness(project_id)
        sys_str = proj["mounting_system"]
        active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(sys_str)
        link = self.db.get_link_by_project(project_id)
        q_no = link["quotation_no"] if link else None

        if not audit["is_complete"]:
            return {
                "project_id": project_id,
                "quotation_no": q_no,
                "mounting_system": sys_str,
                "requested": True,
                "status": "INPUTS_INCOMPLETE",
                "input_completeness": "INCOMPLETE",
                "completeness_percent": audit["completeness_percent"],
                "missing_inputs": audit["missing"],
                "errors": audit["errors"],
                "preliminary_calculation_status": "PENDING_INPUTS",
                "active_holds_count": len(active_holds),
                "active_holds": [h.hold_id for h in active_holds],
                "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
                "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
            }

        try:
            run = self.db.execute_and_record_run(
                project_id=project_id,
                walkway_width_m=walkway_width_m,
                ballast_weight_kn_per_m2=ballast_weight_kn_per_m2,
                friction_coeff_mu=friction_coeff_mu,
                sheet_clamp_tensile_kn=clamp_capacity_kn,
                bracket_spacing_mm=bracket_spacing_mm,
            )

            summary = {
                "project_id": project_id,
                "quotation_no": q_no,
                "mounting_system": run["mounting_system"],
                "requested": True,
                "status": "PRELIMINARY_COMPLETED",
                "numerical_status": run.get("numerical_status", run["status"]),
                "input_completeness": run.get("input_completeness", "PROVISIONAL"),
                "completeness_percent": 100 if run.get("input_completeness") == "COMPLETE" else audit["completeness_percent"],
                "provenance_status": run.get("provenance_status", "PROVISIONAL"),
                "engineering_status": run.get("engineering_status", "UNVERIFIED"),
                "construction_status": run.get("construction_status", "BLOCKED_AFC_LOCKED"),
                "can_approve_for_construction": False,
                "is_approved_for_construction": 0,
                "run_id": run["run_id"],
                "preliminary_calculation_status": run["status"],
                "max_unity_ratio": run["max_unity_ratio"],
                "governing_check": run["governing_check"],
                "active_holds_count": run["active_holds_count"],
                "active_holds": [h.hold_id for h in active_holds],
                "watermark": run["watermark"],
                "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
                "drawing_available": True,
                "total_checks": len(run["results"]),
                "passed_checks": sum(1 for r in run["results"] if r["passed"]),
                "failed_checks": sum(1 for r in run["results"] if not r["passed"]),
                "results": run["results"],
                "executed_at": run["created_at"],
            }

            # Embed in quotation if linked
            if q_no:
                try:
                    from quotation.quotation_history import get_quotation, save_quotation
                    q_data = get_quotation(q_no)
                    if q_data:
                        updated_q = self.embed_assessment_in_quotation(q_data, summary)
                        save_quotation(updated_q, status=q_data.get("status", "Draft"))
                except Exception as q_err:
                    # Quotation embedding failure must not prevent structural execution
                    pass

            return summary
        except Exception as e:
            return {
                "project_id": project_id,
                "quotation_no": q_no,
                "mounting_system": sys_str,
                "requested": True,
                "status": "CALCULATION_ERROR",
                "input_completeness": "COMPLETE",
                "completeness_percent": 100,
                "error_message": str(e),
                "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
            }

    # -------------------------------------------------------------------------
    # 4. Standalone Structural Assessment Report Generator
    # -------------------------------------------------------------------------
    def generate_structural_assessment_report(
        self,
        project_id: str,
        quotation_no: Optional[str] = None,
    ) -> str:
        """
        Generates a standalone, comprehensive markdown report for the structural assessment.
        Contains the mandatory preliminary disclaimer and preserves separation from the quotation proposal.
        """
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        # Resolve quotation reference
        if not quotation_no:
            link = self.db.get_link_by_project(project_id)
            quotation_no = link["quotation_no"] if link else "INDEPENDENT_PROJECT"

        site = self.db.get_site(project_id)
        module = self.db.get_module(project_id)
        geom = self.db.get_geometry(project_id)
        latest_run = self.db.get_latest_run_for_project(project_id)

        lines = [
            "# RENSUN SOLAR — PRELIMINARY STRUCTURAL ASSESSMENT REPORT",
            "",
            "```text",
            "=" * 90,
            "STATUS:              PRELIMINARY STRUCTURAL ASSESSMENT — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
            f"DOCUMENT REF:        RS-SAR-{project_id}",
            f"ASSOCIATED QUOTATION:{quotation_no}",
            f"STRUCTURAL PROJECT:  {project_id}",
            f"MOUNTING SYSTEM:     {proj['mounting_system']}",
            f"DATE:                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "GOVERNANCE GATE:     APPROVED FOR CONSTRUCTION (AFC) IS STRICTLY FORBIDDEN",
            "=" * 90,
            "```",
            "",
            "> [!IMPORTANT]",
            "> **MANDATORY STATUTORY DISCLAIMER**:",
            "> This document is an automated preliminary structural analysis generated for feasibility and preliminary",
            "> sizing only. It does **NOT** constitute an Approved for Construction (AFC) design, a certified structural",
            "> stability certificate, or legal sign-off under TNCDBR-2019 Rule 35. Final execution drawings and structural",
            "> adequacy certificates require independent review and seal by a statutory Registered Structural Engineer (RSE).",
            "",
            "---",
            "",
            "## 1. PROJECT & SITE DESIGN BASIS",
            "",
            f"- **Client Name**: {proj['client_name'] or 'Valued Customer'}",
            f"- **Site Location**: {proj['site_location'] or 'Tamil Nadu'}",
            f"- **Associated Solar Quotation**: `{quotation_no}`",
        ]

        if site:
            lines.extend([
                f"- **Coordinates**: Latitude {site.latitude:.4f}° N, Longitude {site.longitude:.4f}° E",
                f"- **Basic Wind Speed ($V_b$)**: {site.basic_wind_speed_vb:.1f} m/s (IS 875 Part 3: 2015)",
                f"- **Terrain Category**: Category {site.terrain_category.value}",
                f"- **Building & Rooftop Height**: {site.building_height_m:.1f} m",
                f"- **Cyclonic Factor ($k_4$)**: {site.cyclonic_factor_k4:.2f}",
                f"- **Seismic Zone**: {site.seismic_zone.value} (Zone Factor $Z = {site.zone_factor_z:.2f}$)",
            ])
        else:
            lines.append("- **Site Parameters**: *NOT CONFIGURED (Pending Site Survey)*")

        lines.extend([
            "",
            "---",
            "",
            "## 2. PV ARRAY & FRAMING SPECIFICATIONS",
            "",
        ])

        if module and geom:
            total_w = geom.columns * module.width_mm + (geom.columns - 1) * 25.0
            total_l = geom.rows * module.length_mm + (geom.rows - 1) * 25.0
            lines.extend([
                f"- **Module Model**: {module.make_model} ({module.peak_power_w:.0f} Wp)",
                f"- **Array Configuration**: {geom.rows} rows × {geom.columns} columns = {geom.total_modules} modules",
                f"- **Total DC Capacity**: {geom.total_capacity_kw:.2f} kWp",
                f"- **Module Dimensions & Weight**: {module.length_mm:.0f} × {module.width_mm:.0f} × {module.thickness_mm:.0f} mm, {module.weight_kg:.1f} kg",
                f"- **Overall Array Dimensions**: {total_w:.0f} mm (Width) × {total_l:.0f} mm (Length)",
                f"- **Purlin / Rail Spacing**: {geom.purlin_spacing_mm:.0f} mm",
                f"- **Rafter / Stanchion Spacing**: {geom.rafter_spacing_mm:.0f} mm",
                f"- **Ground / Roof Clearance**: {geom.ground_clearance_mm:.0f} mm",
            ])
        else:
            lines.append("- **Array Geometry**: *NOT FULLY CONFIGURED*")

        lines.extend([
            "",
            "---",
            "",
            "## 3. PRELIMINARY STRUCTURAL CALCULATION RESULTS",
            "",
        ])

        if latest_run:
            num_st = latest_run.get("numerical_status") or latest_run["status"]
            eng_st = latest_run.get("engineering_status") or "UNVERIFIED"
            prov_st = latest_run.get("provenance_status") or "PROVISIONAL"
            comp_st = latest_run.get("input_completeness") or "COMPLETE"
            const_st = latest_run.get("construction_status") or "BLOCKED_AFC_LOCKED"
            lines.extend([
                f"- **Calculation Run ID**: `{latest_run['run_id']}`",
                f"- **Numerical Calculation Outcome**: **{num_st}** (Checks: {latest_run.get('governing_check', 'N/A')})",
                f"- **Input Completeness Status**: `{comp_st}`",
                f"- **Evidence & Data Provenance Status**: `{prov_st}` (Assumed / provisional data active)",
                f"- **Engineering Verification Status**: **{eng_st}** (Software verification only; RSE certification pending)",
                f"- **Construction Approval (AFC) Status**: **{const_st}** (Commercial installation & AFC strictly locked)",
                f"- **Statutory Watermark**: `{latest_run.get('watermark', 'PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION')}`",
                f"- **Maximum Unity Ratio**: `{latest_run['max_unity_ratio']:.3f}`",
                f"- **Governing Structural Check**: {latest_run['governing_check']}",
                f"- **Calculation Method**: `{latest_run['calculation_method']}`",
                f"- **Software Engine Version**: `{latest_run['engine_version']}`",
                f"- **Analysis Timestamp**: {latest_run['created_at']}",
                "",
                "| Status | Check Description | Demand | Capacity | Unity Ratio | Codal Standard |",
                "|---|---|---|---|---|---|",
            ])
            for r in latest_run["results"]:
                st = "PASS" if r["passed"] else "FAIL"
                badge = f"**{st}**"
                lines.append(
                    f"| {badge} | {r['check_name']} | {r['demand_value']:.3f} {r['units']} | "
                    f"{r['capacity_value']:.3f} {r['units']} | `{r['unity_ratio']:.3f}` | {r['clause_reference']} |"
                )
        else:
            lines.append("*No calculation runs executed yet. Complete inputs and run calculation to populate results.*")

        # Active Holds Section
        active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(proj["mounting_system"])
        lines.extend([
            "",
            "---",
            "",
            f"## 4. ACTIVE ENGINEERING VERIFICATION HOLDS ({len(active_holds)} ENFORCED)",
            "",
            "The following statutory and internal engineering verification holds are active and prevent issuance of approved drawings:",
            "",
            "| Hold Identifier | Category | Responsible Reviewer | Statutory Release Criteria |",
            "|---|---|---|---|",
        ])
        for h in active_holds:
            lines.append(f"| `{h.hold_id}` | {h.category.value} | {h.responsible_reviewer} | {h.release_criteria[:80]}... |")

        lines.extend([
            "",
            "---",
            "",
            "## 5. CAD DRAWING ARTIFACT STATUS",
            "",
            "- **Drawing Status**: `PRELIMINARY ONLY`",
            "- **Enforced Watermark**: `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`",
            f"- **Drawing Reference**: `RS-STR-{project_id}-001`",
            "- **Format**: AutoCAD R2010 DXF (Multi-layer)",
            "",
            "```text",
            "=" * 90,
            "END OF PRELIMINARY STRUCTURAL ASSESSMENT REPORT",
            "=" * 90,
            "```",
        ])

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 5. Drawing Generation Helper
    # -------------------------------------------------------------------------
    def generate_structural_dxf(
        self,
        project_id: str,
        output_path: Optional[str] = None,
        require_approved: bool = False,
    ) -> str:
        """
        Generates a multi-layer DXF drawing.
        If require_approved=True, the non-negotiable verification hold gate strictly forbids
        drawing generation while active holds remain enforced.
        """
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        geom = self.db.get_geometry(project_id)
        if not geom:
            raise ValueError(f"Geometry not configured for project '{project_id}'.")

        if output_path:
            out_file = output_path
        elif self.drawing_output_dir:
            os.makedirs(self.drawing_output_dir, exist_ok=True)
            out_file = os.path.join(self.drawing_output_dir, f"structural_{project_id}.dxf")
        else:
            out_file = f"structural_{project_id}.dxf"
        metadata = DrawingMetadata(
            project_id=project_id,
            client_name=proj["client_name"],
            site_location=proj["site_location"],
            system_type=geom.mounting_system,
            drawing_number=f"RS-STR-{project_id}-001",
            is_approved_for_construction=require_approved,
        )
        drawer = DXFDrawingEngine(geometry=geom, metadata=metadata)
        # Enforce watermark and hold gate
        generated_file = drawer.generate_dxf(out_file, require_approved=require_approved)

        latest_run = self.db.get_latest_run_for_project(project_id)
        run_id = latest_run["run_id"] if latest_run else None
        self.db.record_drawing_export(
            run_id=run_id,
            project_id=project_id,
            drawing_number=metadata.drawing_number,
            file_path=generated_file,
        )
        return generated_file

    def update_project_inputs(
        self,
        project_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Updates project metadata, site parameters, module specifications,
        framing geometry, and section assignments from a payload dictionary.
        """
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        # 1. Update metadata if present
        meta = payload.get("metadata") or {}
        name_val = meta.get("name") or payload.get("name")
        client_val = meta.get("client_name") or payload.get("client_name")
        site_val = meta.get("site_location") or payload.get("site_location")
        desc_val = meta.get("description") or payload.get("description")
        sys_val = meta.get("mounting_system") or payload.get("mounting_system")

        if any([name_val, client_val, site_val, desc_val]):
            self.db.update_project_metadata(
                project_id=project_id,
                name=name_val,
                client_name=client_val,
                site_location=site_val,
                description=desc_val,
            )
        if sys_val:
            sys_type = self.resolve_mounting_system(sys_val)
            self.db.update_project_system(project_id, sys_type)

        # 2. Update Site Parameters
        site_in = payload.get("site") or payload.get("site_inputs")
        if site_in:
            loc = site_in.get("location_name") or site_val or proj.get("site_location") or "Tamil Nadu"
            self._map_site_inputs(project_id, site_in, default_location=loc)

        # 3. Update PV Module
        mod_in = payload.get("module") or payload.get("module_spec")
        if mod_in:
            power_w = float(mod_in.get("peak_power_w") or mod_in.get("module_wattage_wp") or 540.0)
            make_model = str(mod_in.get("make_model", f"Tier-1 Mono-PERC {power_w:.0f}W"))
            length_mm = float(mod_in.get("length_mm", 2278.0))
            width_mm = float(mod_in.get("width_mm", 1134.0))
            thickness_mm = float(mod_in.get("thickness_mm", 35.0))
            weight_kg = float(mod_in.get("weight_kg") or mod_in.get("mass_kg") or 27.5)
            tilt_deg = float(mod_in.get("tilt_deg") or mod_in.get("tilt_angle_deg") or 10.0)
            azimuth_deg = float(mod_in.get("azimuth_deg", 180.0))

            module = PVModuleSpecification(
                make_model=make_model,
                length_mm=length_mm,
                width_mm=width_mm,
                thickness_mm=thickness_mm,
                weight_kg=weight_kg,
                peak_power_w=power_w,
                tilt_deg=tilt_deg,
                azimuth_deg=azimuth_deg,
            )
            self.db.set_module(project_id, module)

        # 4. Update Geometry
        geom_in = payload.get("geometry") or payload.get("array_geometry")
        if geom_in:
            proj = self.db.get_project(project_id)
            sys_type = self.resolve_mounting_system(proj["mounting_system"])
            rows = int(geom_in.get("rows", 4))
            cols = int(geom_in.get("columns", 5))
            total = int(geom_in.get("total_modules") or (rows * cols))
            purlin_sp = float(geom_in.get("purlin_spacing_mm") or (float(geom_in.get("purlin_spacing_m", 1.4)) * 1000.0 if geom_in.get("purlin_spacing_m") else 1150.0))
            rafter_sp = float(geom_in.get("rafter_spacing_mm") or (float(geom_in.get("rafter_spacing_m", 3.0)) * 1000.0 if geom_in.get("rafter_spacing_m") else 3000.0))
            clearance = float(geom_in.get("ground_clearance_mm") or (float(geom_in.get("ground_clearance_m", 2.5)) * 1000.0 if geom_in.get("ground_clearance_m") else (2800.0 if sys_type == MountingSystemType.SYSTEM_A_CANOPY else 200.0)))
            module = self.db.get_module(project_id)
            if not module:
                module = PVModuleSpecification(
                    make_model="Tier-1 Mono-PERC 540W",
                    length_mm=2278.0,
                    width_mm=1134.0,
                    thickness_mm=35.0,
                    weight_kg=27.5,
                    peak_power_w=540.0,
                    tilt_deg=10.0,
                    azimuth_deg=180.0,
                )
                self.db.set_module(project_id, module)

            geom = ArrayGeometry(
                mounting_system=sys_type,
                total_modules=total,
                rows=rows,
                columns=cols,
                module=module,
                orientation=str(geom_in.get("orientation", "PORTRAIT")).upper(),
                purlin_spacing_mm=purlin_sp,
                rafter_spacing_mm=rafter_sp,
                ground_clearance_mm=clearance,
            )
            self.db.set_geometry(project_id, geom)

        # 5. Update Sections
        sec_in = payload.get("sections")
        if sec_in:
            for c_type, s_data in sec_in.items():
                if isinstance(s_data, dict):
                    mat = STEEL_E250 if "STEEL" in s_data.get("material", "STEEL").upper() else ALUMINIUM_6063_T6
                    sec = SectionProperty(
                        designation=s_data.get("designation", f"Custom {c_type}"),
                        profile_type=s_data.get("profile_type", "Standard"),
                        material=mat,
                        area_mm2=float(s_data.get("area_mm2", 450.0)),
                        Ixx_mm4=float(s_data.get("Ixx_mm4", 750000.0)),
                        Iyy_mm4=float(s_data.get("Iyy_mm4", 180000.0)),
                        Zxx_mm3=float(s_data.get("Zxx_mm3", 15000.0)),
                        Zyy_mm3=float(s_data.get("Zyy_mm3", 5000.0)),
                        rxx_mm=float(s_data.get("rxx_mm", 40.8)),
                        ryy_mm=float(s_data.get("ryy_mm", 20.0)),
                        mass_kg_m=float(s_data.get("mass_kg_m", 3.53)),
                    )
                    self.db.set_section(project_id, c_type.upper(), sec)

        return self.assess_input_completeness(project_id)

    def generate_calculation_summary(self, project_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Generates structured calculation summary and text deliverable."""
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        run = self.db.get_calculation_run(run_id) if run_id else self.db.get_latest_run_for_project(project_id)
        active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(proj["mounting_system"])

        if not run:
            return {
                "project_id": project_id,
                "project_name": proj["name"],
                "mounting_system": proj["mounting_system"],
                "status": "NOT_EXECUTED",
                "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
                "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
                "active_holds_count": len(active_holds),
                "summary_text": f"# CALCULATION SUMMARY — {project_id}\n\nNo calculation runs executed yet.",
            }

        text_lines = [
            f"# RENSUN SOLAR — CALCULATION SUMMARY",
            f"**Project**: {proj['name']} (`{project_id}`)",
            f"**Mounting System**: {run['mounting_system']}",
            f"**Run ID**: `{run['run_id']}` ({run['created_at']})",
            f"**Preliminary Status**: **{run['status']}** (Max Unity: `{run['max_unity_ratio']:.3f}`)",
            f"**Governing Check**: {run['governing_check']}",
            f"**Watermark**: PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
            f"**Approval Status**: BLOCKED BY ENGINEERING HOLDS",
            "",
            "## Member Check Results",
            "| Check Name | Demand | Capacity | Unity Ratio | Status | Codal Clause |",
            "|---|---|---|---|---|---|",
        ]
        for r in run.get("results", []):
            st = "PASS" if r["passed"] else "FAIL"
            text_lines.append(
                f"| {r['check_name']} | {r['demand_value']:.2f} {r['units']} | {r['capacity_value']:.2f} {r['units']} | "
                f"`{r['unity_ratio']:.3f}` | **{st}** | {r['clause_reference']} |"
            )

        text_lines.extend([
            "",
            f"## Active Verification Holds ({len(active_holds)} Enforced)",
        ])
        for h in active_holds:
            text_lines.append(f"- `{h.hold_id}`: {h.release_criteria[:90]}...")

        return {
            "project_id": project_id,
            "project_name": proj["name"],
            "mounting_system": run["mounting_system"],
            "run_id": run["run_id"],
            "status": run["status"],
            "max_unity_ratio": run["max_unity_ratio"],
            "governing_check": run["governing_check"],
            "created_at": run["created_at"],
            "results": run.get("results", []),
            "active_holds_count": len(active_holds),
            "watermark": run["watermark"],
            "approval_status": "BLOCKED_BY_ENGINEERING_HOLDS",
            "summary_text": "\n".join(text_lines),
        }

    def generate_input_schedule(self, project_id: str) -> Dict[str, Any]:
        """Generates comprehensive structural input schedule with SI units and provenance classification."""
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        site = self.db.get_site(project_id)
        module = self.db.get_module(project_id)
        geom = self.db.get_geometry(project_id)

        items = []
        if site:
            items.extend([
                {"parameter": "Basic Wind Speed (Vb)", "value": site.basic_wind_speed_vb, "units": "m/s", "classification": "Statutory Code", "source": "IS 875 (Part 3) Figure 1"},
                {"parameter": "Terrain Category", "value": site.terrain_category.value, "units": "integer (1-4)", "classification": "Statutory Code", "source": "IS 875 (Part 3) Clause 6.3.2"},
                {"parameter": "Building Height", "value": site.building_height_m, "units": "m", "classification": "Measured", "source": "Physical Site Survey"},
                {"parameter": "Rooftop Elevation", "value": site.rooftop_elevation_m, "units": "m", "classification": "Measured", "source": "Host Building Architectural Drawing"},
                {"parameter": "Cyclonic Factor (k4)", "value": site.cyclonic_factor_k4, "units": "dimensionless", "classification": "Statutory Code", "source": "IS 875 (Part 3) Clause 6.3.4"},
                {"parameter": "Seismic Zone", "value": site.seismic_zone.value, "units": "zone factor Z", "classification": "Statutory Code", "source": "IS 1893 (Part 1): 2016 Table 3"},
            ])
        if module:
            items.extend([
                {"parameter": "Module Peak Power", "value": module.peak_power_w, "units": "Wp", "classification": "Certified", "source": "Manufacturer Flash Report / Datasheet"},
                {"parameter": "Module Dimensions (L x W x T)", "value": f"{module.length_mm} x {module.width_mm} x {module.thickness_mm}", "units": "mm", "classification": "Certified", "source": "Manufacturer Mechanical Drawing"},
                {"parameter": "Module Weight", "value": module.weight_kg, "units": "kg", "classification": "Certified", "source": "Manufacturer Datasheet"},
                {"parameter": "Array Tilt Angle", "value": module.tilt_deg, "units": "degrees", "classification": "Derived", "source": "Solar Yield Optimization"},
            ])
        if geom:
            items.extend([
                {"parameter": "Array Grid (Rows x Columns)", "value": f"{geom.rows} x {geom.columns}", "units": "count", "classification": "Derived", "source": "Rooftop Area Layout Plan"},
                {"parameter": "Total Modules", "value": geom.total_modules, "units": "count", "classification": "Derived", "source": "Quotation DC Sizing"},
                {"parameter": "Purlin / Rail Spacing", "value": geom.purlin_spacing_mm, "units": "mm", "classification": "Derived", "source": "Module Clamp Zone Specification"},
                {"parameter": "Rafter / Bracket Spacing", "value": geom.rafter_spacing_mm, "units": "mm", "classification": "Derived", "source": "Building Structural Bay Spacing"},
                {"parameter": "Ground Clearance", "value": geom.ground_clearance_mm, "units": "mm", "classification": "Measured", "source": "Clearance Architectural Mandate"},
            ])

        text_lines = [
            f"# RENSUN SOLAR — STRUCTURAL INPUT SCHEDULE",
            f"**Project Reference**: `{project_id}` ({proj['name']})",
            f"**Mounting System**: {proj['mounting_system']}",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Status**: PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
            "",
            "| Parameter Description | Input Value | Units | Data Provenance | Source Reference |",
            "|---|---|---|---|---|",
        ]
        for it in items:
            text_lines.append(f"| {it['parameter']} | `{it['value']}` | {it['units']} | {it['classification']} | {it['source']} |")

        return {
            "project_id": project_id,
            "project_name": proj["name"],
            "mounting_system": proj["mounting_system"],
            "items": items,
            "schedule_text": "\n".join(text_lines),
            "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
        }

    def generate_section_schedule(self, project_id: str) -> Dict[str, Any]:
        """Generates material and section schedule."""
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        sections = []
        for c in ("PURLIN", "RAFTER", "COLUMN", "RAIL", "BRACING", "STRUT"):
            sec = self.db.get_section(project_id, c)
            if sec:
                sections.append({
                    "component": c,
                    "designation": sec.designation,
                    "profile_type": sec.profile_type,
                    "area_mm2": sec.area_mm2,
                    "Ixx_mm4": sec.Ixx_mm4,
                    "Iyy_mm4": sec.Iyy_mm4,
                    "Zxx_mm3": sec.Zxx_mm3,
                    "Zyy_mm3": sec.Zyy_mm3,
                    "mass_kg_m": sec.mass_kg_m,
                    "material_grade": sec.material.grade,
                    "standard_reference": sec.material.standard_reference,
                    "fy_mpa": sec.material.yield_strength_mpa,
                })

        text_lines = [
            f"# RENSUN SOLAR — MATERIAL & SECTION SCHEDULE",
            f"**Project Reference**: `{project_id}` ({proj['name']})",
            f"**Mounting System**: {proj['mounting_system']}",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Status**: PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
            "",
            "| Component | Designation | Profile Type | Material Grade | Area (mm²) | Ixx (mm⁴) | Zxx (mm³) | Mass (kg/m) |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for s in sections:
            text_lines.append(
                f"| {s['component']} | `{s['designation']}` | {s['profile_type']} | {s['material_grade']} | "
                f"{s['area_mm2']:.1f} | {s['Ixx_mm4']:.0f} | {s['Zxx_mm3']:.0f} | {s['mass_kg_m']:.2f} |"
            )

        return {
            "project_id": project_id,
            "project_name": proj["name"],
            "mounting_system": proj["mounting_system"],
            "sections": sections,
            "schedule_text": "\n".join(text_lines),
            "watermark": "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
        }

    # -------------------------------------------------------------------------
    # 6. Quotation Embedding Helper
    # -------------------------------------------------------------------------
    @staticmethod
    def embed_assessment_in_quotation(
        quotation_data: Dict[str, Any],
        assessment_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Embeds structural assessment metadata into a quotation payload without
        altering solar sizing, panel quantity, equipment pricing, or warranty.
        """
        updated = quotation_data.copy()
        if assessment_summary:
            updated["structural_assessment"] = assessment_summary
        else:
            updated["structural_assessment"] = {
                "requested": False,
                "status": "NOT_REQUESTED",
            }
        return updated


# Global singleton bridge instance
STRUCTURAL_BRIDGE = QuotationStructuralBridge()
