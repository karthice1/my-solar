"""
Phase 1.5.2: Site Coordinate, Wind Input & Host-Structure Validation Test Suite
Package: tests.test_phase1_5_2_site_inputs
Covers: WP-04 (Coordinates), WP-05 (Wind Inputs), WP-06 (Roof Inspection)

Tests:
1. Missing, non-numeric, out-of-bounds, NaN, and Inf site coordinates.
2. Retention of provisional coordinates (11.6643°N, 78.1460°E) as UNVERIFIED.
3. Incomplete survey evidence rejection (missing instrument, accuracy > 1.0m, missing surveyor).
4. Sub-meter RTK GNSS survey evidence verification.
5. Wind parameter transparent categorization (Code-derived, Site-measured, Engineer-selected, Assumed).
6. Salem unlisted status in IS 875 (Part 3): 2015 Annex A Table enforcement.
7. Mandatory 17-field roof inspection checklist audit.
8. Prohibition against inferring host roof capacity from roof type alone.
9. Verification that assumed or missing inputs CANNOT produce an engineering PASS.
10. Preservation of all 12 canonical holds and AFC block.
11. End-to-end API integration and isolated database non-interference.
"""

import os
import sys
import unittest
import math
from typing import Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from structural.site_survey import (
    SurveyMethod,
    CoordinateVerificationStatus,
    ApprovalStatus,
    SiteCoordinateRecord,
    WindParameterCategory,
    WindParameterItem,
    WindVerificationRecord,
    RoofType,
    RoofConditionRating,
    CorrosionLevel,
    InputClassification,
    RoofInspectionField,
    RoofInspectionRegister,
    SiteInputValidator,
)
from structural.models import SiteParameters, TerrainCategory, SeismicZone, MountingSystemType
from structural.provenance import ProvenanceLevel
from structural.holds import MASTER_VERIFICATION_REGISTER
from tests.test_isolation_helper import IsolatedTestEnvironment


class TestPhase152SiteInputs(unittest.TestCase):
    """Test suite for Phase 1.5.2 site input, wind parameter, and roof validation."""

    # -------------------------------------------------------------------------
    # WP-04: SITE-COORDINATE VERIFICATION TESTS
    # -------------------------------------------------------------------------

    def test_wp04_coordinate_bounds_and_finite_validation(self):
        """Coordinates must be finite real numbers within Indian territorial bounds."""
        # Valid Indian coordinates
        rec = SiteCoordinateRecord(latitude=11.6643, longitude=78.1460)
        self.assertEqual(rec.latitude, 11.6643)
        self.assertEqual(rec.longitude, 78.1460)

        # None coordinates
        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=None, longitude=78.1460)

        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=11.6643, longitude=None)

        # Non-numeric string coordinates
        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude="invalid", longitude=78.1460)

        # NaN / Inf coordinates
        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=float("nan"), longitude=78.1460)

        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=11.6643, longitude=float("inf"))

        # Out-of-bounds latitude (< 6.0 or > 38.0)
        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=5.5, longitude=78.1460)

        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=38.5, longitude=78.1460)

        # Out-of-bounds longitude (< 68.0 or > 98.0)
        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=11.6643, longitude=67.5)

        with self.assertRaises(ValueError):
            SiteCoordinateRecord(latitude=11.6643, longitude=99.0)

    def test_wp04_provisional_salem_coordinates_retained_as_unverified(self):
        """
        Salem coordinates (11.6643°N, 78.1460°E) are preserved as historical provisional data
        and strictly marked UNVERIFIED — ROOFTOP SURVEY REQUIRED.
        """
        rec = SiteCoordinateRecord(
            latitude=11.6643,
            longitude=78.1460,
            location_name="90 ERUMAPALAYAM ITTERI ROAD, SALEM",
            survey_method=SurveyMethod.PROVISIONAL_CENTROID,
            provenance_level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
            verification_status=CoordinateVerificationStatus.UNVERIFIED_ROOFTOP_SURVEY_REQUIRED,
        )

        self.assertFalse(rec.is_verified_rooftop_survey())
        self.assertEqual(rec.display_status, "UNVERIFIED — ROOFTOP SURVEY REQUIRED")
        self.assertEqual(rec.provenance_level, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL)
        self.assertEqual(rec.survey_method, SurveyMethod.PROVISIONAL_CENTROID)

    def test_wp04_incomplete_survey_evidence_rejected(self):
        """Incomplete survey evidence must NOT qualify as a verified rooftop survey."""
        # 1. Missing instrument
        rec1 = SiteCoordinateRecord(
            latitude=11.6643,
            longitude=78.1460,
            survey_method=SurveyMethod.RTK_GNSS,
            survey_instrument=None,
            accuracy_m=0.02,
            surveyor_name="Er. S. Murugan",
            survey_date="2026-11-08",
            source_document="Survey Report #059",
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            verification_status=CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY,
        )
        self.assertFalse(rec1.is_verified_rooftop_survey())

        # 2. Accuracy > 1.0 m (e.g. handheld GPS ± 5.0m)
        rec2 = SiteCoordinateRecord(
            latitude=11.6643,
            longitude=78.1460,
            survey_method=SurveyMethod.HANDHELD_GPS,
            survey_instrument="Garmin eTrex 32x",
            accuracy_m=5.0,
            surveyor_name="Er. S. Murugan",
            survey_date="2026-11-08",
            source_document="GPS Log",
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            verification_status=CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY,
        )
        self.assertFalse(rec2.is_verified_rooftop_survey())

        # 3. Missing surveyor name
        rec3 = SiteCoordinateRecord(
            latitude=11.6643,
            longitude=78.1460,
            survey_method=SurveyMethod.RTK_GNSS,
            survey_instrument="Leica GS18 T",
            accuracy_m=0.02,
            surveyor_name="",
            survey_date="2026-11-08",
            source_document="Survey Report #059",
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            verification_status=CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY,
        )
        self.assertFalse(rec3.is_verified_rooftop_survey())

        # 4. Missing survey date
        rec4 = SiteCoordinateRecord(
            latitude=11.6643,
            longitude=78.1460,
            survey_method=SurveyMethod.RTK_GNSS,
            survey_instrument="Leica GS18 T",
            accuracy_m=0.02,
            surveyor_name="Er. S. Murugan",
            survey_date="",
            source_document="Survey Report #059",
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            verification_status=CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY,
        )
        self.assertFalse(rec4.is_verified_rooftop_survey())

        # 5. Missing source document
        rec5 = SiteCoordinateRecord(
            latitude=11.6643,
            longitude=78.1460,
            survey_method=SurveyMethod.RTK_GNSS,
            survey_instrument="Leica GS18 T",
            accuracy_m=0.02,
            surveyor_name="Er. S. Murugan",
            survey_date="2026-11-08",
            source_document="",
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            verification_status=CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY,
        )
        self.assertFalse(rec5.is_verified_rooftop_survey())

    def test_wp04_certified_rtk_gnss_survey_acceptance(self):
        """Sub-meter RTK GNSS survey with complete evidence certifies coordinates."""
        rec = SiteCoordinateRecord(
            latitude=11.665123,
            longitude=78.146892,
            location_name="90 ERUMAPALAYAM ITTERI ROAD, SALEM",
            survey_method=SurveyMethod.RTK_GNSS,
            survey_instrument="Leica GS18 T GNSS RTK",
            accuracy_m=0.02,
            surveyor_name="Er. S. Murugan (RSE License #TN/SAL/2019/042)",
            surveyor_organization="GeoPrecision Engineering Consultants",
            survey_date="2026-11-08",
            source_document="Rooftop Topographic Survey Certificate #RTK-2026-059",
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            verification_status=CoordinateVerificationStatus.VERIFIED_ROOFTOP_SURVEY,
            approval_status=ApprovalStatus.VERIFIED_BY_RSE,
            notes="Physical rooftop RTK benchmark established at southwest parapet corner.",
        )

        self.assertTrue(rec.is_verified_rooftop_survey())
        self.assertIn("VERIFIED ROOFTOP SURVEY", rec.display_status)
        self.assertIn("±0.02m", rec.display_status)
        self.assertIn("Er. S. Murugan", rec.display_status)

    # -------------------------------------------------------------------------
    # WP-05: WIND INPUT VERIFICATION TESTS
    # -------------------------------------------------------------------------

    def test_wp05_salem_unlisted_status_and_is875_governance(self):
        """
        Confirms Salem is unlisted in IS 875 (Part 3): 2015 Annex A Table.
        Requires WIND_COORD_UNVERIFIED_HOLD and ASSUMED_DATA_CERTIFICATION_HOLD.
        """
        wind = WindVerificationRecord(
            governing_standard="IS 875 (Part 3): 2015, Third Revision (Reaffirmed 2020)",
            location_name="Salem, Tamil Nadu",
            basic_wind_speed_vb=39.0,
            is_salem_annex_a_listed=False,
        )

        self.assertFalse(wind.is_salem_annex_a_listed)
        self.assertTrue(wind.has_provisional_assumptions())
        self.assertEqual(wind.governing_standard, "IS 875 (Part 3): 2015, Third Revision (Reaffirmed 2020)")

        # Verify required holds
        holds = wind.get_active_wind_governance_holds()
        self.assertIn("WIND_COORD_UNVERIFIED_HOLD", holds)
        self.assertIn("ASSUMED_DATA_CERTIFICATION_HOLD", holds)

        # Verify Vb parameter item
        vb_param = wind.parameters["basic_wind_speed_vb"]
        self.assertEqual(vb_param.value, 39.0)
        self.assertEqual(vb_param.units, "m/s")
        self.assertEqual(vb_param.category, WindParameterCategory.ASSUMED_PROVISIONAL)
        self.assertEqual(vb_param.provenance_level, ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL)
        self.assertTrue(vb_param.is_provisional)

    def test_wp05_wind_parameter_category_separation(self):
        """Transparently separates Statutory Code, Site-Measured, Engineer-Selected, and Assumed values."""
        wind = WindVerificationRecord(
            location_name="Salem, Tamil Nadu",
            basic_wind_speed_vb=39.0,
            is_salem_annex_a_listed=False,
            risk_coefficient_k1=1.0,
            terrain_category=3,
            topography_factor_k3=1.0,
            cyclonic_factor_k4=1.0,
        )

        code_derived = wind.get_parameters_by_category(WindParameterCategory.CODE_DERIVED)
        code_keys = {p.parameter_key for p in code_derived}
        self.assertIn("risk_coefficient_k1", code_keys)
        self.assertIn("cyclonic_factor_k4", code_keys)
        self.assertIn("cpe_uplift", code_keys)

        eng_selected = wind.get_parameters_by_category(WindParameterCategory.ENGINEER_SELECTED)
        eng_keys = {p.parameter_key for p in eng_selected}
        self.assertIn("terrain_category", eng_keys)

        assumed = wind.get_parameters_by_category(WindParameterCategory.ASSUMED_PROVISIONAL)
        assumed_keys = {p.parameter_key for p in assumed}
        self.assertIn("basic_wind_speed_vb", assumed_keys)
        self.assertIn("topography_factor_k3", assumed_keys)
        self.assertIn("building_height_m", assumed_keys)

    # -------------------------------------------------------------------------
    # WP-06: ROOF INSPECTION & HOST STRUCTURE TESTS
    # -------------------------------------------------------------------------

    def test_wp06_mandatory_17_fields_inspection_register(self):
        """Verifies presence and initial state of all 17 mandatory roof inspection fields."""
        reg = RoofInspectionRegister(project_id="RS-STR-RENSUN-2026-0059")
        audit = reg.audit_completeness()

        self.assertEqual(audit["total_mandatory_fields"], 17)
        self.assertGreater(audit["missing_fields_count"], 0)
        self.assertGreater(audit["assumed_fields_count"], 0)
        self.assertEqual(audit["verified_fields_count"], 0)
        self.assertFalse(audit["is_complete"])
        self.assertEqual(audit["status"], "INCOMPLETE")

        # Verify key mandatory field existence
        self.assertIn("roof_length_m", reg.fields)
        self.assertIn("roof_width_m", reg.fields)
        self.assertIn("concrete_strength_mpa", reg.fields)
        self.assertIn("slab_thickness_mm", reg.fields)
        self.assertIn("reinforcement_details", reg.fields)
        self.assertIn("member_sizes", reg.fields)

    def test_wp06_roof_capacity_cannot_be_inferred_from_type_alone(self):
        """Setting roof_type = RCC_FLAT_SLAB does NOT prove structural capacity without NDT / drawings."""
        reg = RoofInspectionRegister(
            project_id="RS-STR-RENSUN-2026-0059",
            roof_type=RoofType.RCC_FLAT_SLAB,
        )

        can_certify, reasons = reg.can_certify_roof_capacity()
        self.assertFalse(can_certify)
        self.assertGreaterEqual(len(reasons), 3)

        # Confirm specific deficiencies are flagged
        reason_text = " ".join(reasons)
        self.assertIn("Concrete compressive strength", reason_text)
        self.assertIn("Slab thickness is unverified", reason_text)
        self.assertIn("framing member sizes", reason_text)
        self.assertIn("Reinforcement schedule", reason_text)

    def test_wp06_physical_testing_evidence_certification(self):
        """When concrete NDT, core gauge, and reinforcement drawings are verified, capacity check passes."""
        reg = RoofInspectionRegister(
            project_id="RS-STR-RENSUN-2026-0059",
            roof_type=RoofType.RCC_FLAT_SLAB,
            condition_rating=RoofConditionRating.GOOD,
            corrosion_level=CorrosionLevel.NONE,
        )

        # Provide Level 1 Measured evidence for concrete
        reg.set_field_evidence(
            field_key="concrete_strength_mpa",
            value=25.0,
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            test_method="Rebound Hammer IS 13311 (Part 2) + Core Compressive Test IS 516",
            evidence_document_id="DOC-NDT-SALEM-059-2026",
            inspector_notes="Average rebound number 32, equivalent cube compressive strength 26.5 MPa >= M20.",
        )

        # Provide Level 1 Measured evidence for slab thickness
        reg.set_field_evidence(
            field_key="slab_thickness_mm",
            value=160.0,
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            test_method="Ultrasonic Pulse Thickness Gauge",
            evidence_document_id="DOC-THK-SALEM-059-2026",
            inspector_notes="Measured solid core thickness 160 mm across 6 grid points.",
        )

        # Provide Level 2 Drawing Verified evidence for framing member sizes
        reg.set_field_evidence(
            field_key="member_sizes",
            value="Beams: 230x450mm; Columns: 300x450mm",
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED,
            evidence_document_id="DWG-STR-ASBUILT-2018-04",
            inspector_notes="Verified against signed as-built structural drawings.",
        )

        # Provide Level 2 Drawing Verified evidence for reinforcement details
        reg.set_field_evidence(
            field_key="reinforcement_details",
            value="Bottom mesh 10mm dia @ 150mm c/c Fe500, top negative bars 12mm dia",
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED,
            evidence_document_id="DWG-STR-ASBUILT-2018-04",
            inspector_notes="Rebar layout and clear cover verified.",
        )

        can_certify, reasons = reg.can_certify_roof_capacity()
        self.assertTrue(can_certify, f"Expected certification success but got deficiencies: {reasons}")
        self.assertEqual(len(reasons), 0)

    def test_wp06_poor_or_critical_condition_blocks_certification(self):
        """Even with material testing, a poor or critical roof condition blocks capacity certification."""
        reg = RoofInspectionRegister(
            project_id="RS-STR-RENSUN-2026-0059",
            roof_type=RoofType.RCC_FLAT_SLAB,
            condition_rating=RoofConditionRating.POOR,  # Significant cracking and spalling
            corrosion_level=CorrosionLevel.SEVERE,
        )

        # Provide material values
        reg.set_field_evidence(
            field_key="concrete_strength_mpa",
            value=25.0,
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            test_method="Core Test",
            evidence_document_id="DOC-01",
        )
        reg.set_field_evidence(
            field_key="slab_thickness_mm",
            value=160.0,
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_1_MEASURED,
            test_method="Gauge",
            evidence_document_id="DOC-02",
        )
        reg.set_field_evidence(
            field_key="member_sizes",
            value="230x450mm",
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED,
            evidence_document_id="DOC-03",
        )
        reg.set_field_evidence(
            field_key="reinforcement_details",
            value="10mm @ 150mm",
            classification=InputClassification.VERIFIED_INPUT,
            provenance_level=ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED,
            evidence_document_id="DOC-04",
        )

        can_certify, reasons = reg.can_certify_roof_capacity()
        self.assertFalse(can_certify)
        self.assertTrue(any("POOR" in r for r in reasons))

    # -------------------------------------------------------------------------
    # CONSOLIDATED VALIDATOR & GOVERNANCE TESTS
    # -------------------------------------------------------------------------

    def test_consolidated_site_validation_prevents_engineering_pass(self):
        """
        Salem baseline project with provisional coordinates and assumed parameters
        CANNOT produce an engineering PASS.
        """
        coords, wind, roof = SiteInputValidator.create_salem_baseline("RS-STR-RENSUN-2026-0059")
        audit = SiteInputValidator.audit_project_site_validation(coords, wind, roof)

        # Strict checks
        self.assertFalse(audit["is_engineering_pass_permitted"])
        self.assertEqual(audit["engineering_status"], "UNVERIFIED_MISSING_PHYSICAL_EVIDENCE")
        self.assertEqual(audit["construction_status"], "BLOCKED_AFC_LOCKED")
        self.assertEqual(audit["coordinate_status"], "UNVERIFIED — ROOFTOP SURVEY REQUIRED")
        self.assertFalse(audit["is_coordinate_verified"])
        self.assertFalse(audit["is_salem_annex_a_listed"])
        self.assertTrue(audit["has_wind_provisional_assumptions"])
        self.assertFalse(audit["can_certify_roof_capacity"])

        # Check active holds
        self.assertIn("WIND_COORD_UNVERIFIED_HOLD", audit["active_site_holds"])
        self.assertIn("ASSUMED_DATA_CERTIFICATION_HOLD", audit["active_site_holds"])
        self.assertIn("INSPECTION_REQUIRED_HOLD", audit["active_site_holds"])

        # Check required physical evidence list
        evidence = audit["required_physical_evidence_from_owner"]
        self.assertGreaterEqual(len(evidence), 5)
        evidence_str = " ".join(evidence)
        self.assertIn("RTK GNSS", evidence_str)
        self.assertIn("concrete rebound hammer", evidence_str)
        self.assertIn("slab thickness", evidence_str)
        self.assertIn("as-built structural drawings", evidence_str)

    def test_all_12_canonical_holds_remain_active_and_enforced(self):
        """All 12 original canonical holds remain registered and active."""
        canonical_holds = [
            "INSPECTION_REQUIRED_HOLD",
            "AERODYNAMIC_UNSUPPORTED_HOLD",
            "WIND_COORD_UNVERIFIED_HOLD",
            "WIND_TRANSFORM_UNVERIFIED_HOLD",
            "VERTICAL_SEISMIC_APPLICABILITY_HOLD",
            "LOAD_COMBINATION_PROVISIONAL_HOLD",
            "FRICTION_UNVERIFIED_HOLD",
            "ALUMINIUM_DERIVATION_HOLD",
            "FASTENER_TORQUE_UNVERIFIED_HOLD",
            "NUMERICAL_INSTABILITY_HOLD",
            "ASSUMED_DATA_CERTIFICATION_HOLD",
            "DRAWING_UNVERIFIED_HOLD",
        ]

        all_registered = MASTER_VERIFICATION_REGISTER.get_all_holds()
        registered_dict = {h.hold_id: h for h in all_registered}

        for h_id in canonical_holds:
            self.assertIn(h_id, registered_dict, f"Canonical hold {h_id} is missing!")
            self.assertTrue(registered_dict[h_id].is_active(), f"Canonical hold {h_id} is inactive!")

        # Verify AFC cannot be approved across any system
        for sys_type in MountingSystemType:
            self.assertFalse(
                MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction(sys_type.value)
            )

    def test_integration_bridge_audit_site_and_roof_validation(self):
        """Tests QuotationStructuralBridge.audit_site_and_roof_validation in isolated environment."""
        from starlette.testclient import TestClient
        from server import app
        from quotation.settings_manager import generate_owner_token, load_owner_settings
        from structural.integration import STRUCTURAL_BRIDGE

        with IsolatedTestEnvironment() as iso:
            iso.assert_isolated_paths()
            client = TestClient(app)
            pin = load_owner_settings().get("admin_pin", "admin123")
            auth_headers = {"X-Owner-Token": generate_owner_token(pin)}

            # Create test project
            pid = "RS-STR-VAL-TEST-01"
            iso.structural_db.create_project(pid, "Validation Test Project", MountingSystemType.SYSTEM_A_CANOPY)
            site = SiteParameters(
                location_name="90 ERUMAPALAYAM ITTERI ROAD, SALEM",
                latitude=11.6643,
                longitude=78.1460,
                basic_wind_speed_vb=39.0,
                terrain_category=TerrainCategory.CATEGORY_3,
                building_height_m=12.0,
                rooftop_elevation_m=12.0,
            )
            iso.structural_db.set_site(pid, site)

            # 1. Direct Bridge audit
            audit = STRUCTURAL_BRIDGE.audit_site_and_roof_validation(pid)
            self.assertFalse(audit["is_engineering_pass_permitted"])
            self.assertEqual(audit["coordinate_status"], "UNVERIFIED — ROOFTOP SURVEY REQUIRED")
            self.assertIn("WIND_COORD_UNVERIFIED_HOLD", audit["active_site_holds"])

            # 2. REST API GET /api/structural/projects/{pid}
            res_proj = client.get(f"/api/structural/projects/{pid}", headers=auth_headers)
            self.assertEqual(res_proj.status_code, 200)
            proj_data = res_proj.json()
            self.assertIn("site_validation", proj_data)
            self.assertEqual(
                proj_data["site_validation"]["coordinate_status"],
                "UNVERIFIED — ROOFTOP SURVEY REQUIRED"
            )

            # 3. REST API GET /api/structural/projects/{pid}/site-validation
            res_val = client.get(f"/api/structural/projects/{pid}/site-validation", headers=auth_headers)
            self.assertEqual(res_val.status_code, 200)
            val_data = res_val.json()
            self.assertEqual(val_data["project_id"], pid)
            self.assertFalse(val_data["validation"]["is_engineering_pass_permitted"])
            self.assertEqual(
                val_data["validation"]["engineering_status"],
                "UNVERIFIED_MISSING_PHYSICAL_EVIDENCE"
            )

            # 4. Unauthenticated check returns 401
            res_unauth = client.get(f"/api/structural/projects/{pid}/site-validation")
            self.assertEqual(res_unauth.status_code, 401)


if __name__ == "__main__":
    unittest.main()
