"""
Comprehensive Automated Test Suite for Phase 1 Structural Subsystem
File: tests/test_structural_foundation.py

Covers:
1. Input validation & range checking
2. Unit conversions & SI unit consistency
3. Geometry & array configuration calculations
4. Physical load-action registration (ACT-IL-01 to 04, ACT-ER-01)
5. Load combination generation (IS 800 Table 4 & IS 1893 seismic schedules)
6. Calculation traceability & transparent report logging
7. Hold enforcement & non-negotiable AFC blocking
8. DXF drawing generation via ezdxf with preliminary watermark
9. Failure handling (refusal of silent defaults)
10. Existing application regression protection (TNEB & Quotation System)
"""

import os
import sys
import tempfile
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import ezdxf

from structural.models import (
    MountingSystemType,
    TerrainCategory,
    SeismicZone,
    SiteParameters,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    CalculationResult,
    DrawingMetadata,
    STEEL_E250,
    ALUMINIUM_6063_T6,
    STAINLESS_STEEL_A2_70,
)
from structural.holds import (
    HoldCategory,
    HoldStatus,
    HoldRecord,
    VerificationRegister,
    MASTER_VERIFICATION_REGISTER,
)
from structural.actions import (
    ActionRegister,
    CombinationGenerator,
    LoadCombination,
)
from structural.provenance import (
    ProvenanceLevel,
    ProvenanceRecord,
    ProvenanceTracker,
)
from structural.engine import (
    StructuralCalculationEngine,
    CalculationReport,
)
from structural.workflows.system_a import SystemACanopyWorkflow
from structural.workflows.system_b import SystemBAluminiumRailWorkflow
from structural.workflows.system_c import SystemCMetalSheetWorkflow
from structural.workflows.system_d import SystemDBallastedWorkflow
from structural.drawing import DXFDrawingEngine


class TestStructuralFoundation(unittest.TestCase):
    """Test suite for Phase 1 structural foundation modules."""

    def setUp(self):
        # Canonical test site: Chennai, TN (Vb = 50 m/s, Category 3, Height = 12 m)
        self.site = SiteParameters(
            location_name="Chennai Industrial Park",
            latitude=13.0827,
            longitude=80.2707,
            basic_wind_speed_vb=50.0,
            terrain_category=TerrainCategory.CATEGORY_3,
            building_height_m=12.0,
            rooftop_elevation_m=12.0,
            cyclonic_factor_k4=1.15, # Coastal Tamil Nadu
            topography_factor_k3=1.0,
            risk_coefficient_k1=1.0,
            seismic_zone=SeismicZone.ZONE_III,
            importance_factor_I=1.0,
            response_reduction_R=4.0,
            soil_type=2,
        )

        # Standard 540W mono-PERC PV module
        self.module = PVModuleSpecification(
            make_model="Tier-1 Mono-PERC 540W",
            length_mm=2278.0,
            width_mm=1134.0,
            thickness_mm=35.0,
            weight_kg=27.5,
            peak_power_w=540.0,
            tilt_deg=10.0,
            azimuth_deg=180.0,
        )

        # 4x5 array (20 modules = 10.8 kWp)
        self.geometry_canopy = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3200.0,
            ground_clearance_mm=2800.0,
        )

        # Standard Cold-Formed Steel C-Channel purlin (100x50x20x2.0 mm)
        self.purlin_section = SectionProperty(
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

    # -------------------------------------------------------------------------
    # 1. Input Validation & Physical Ranges
    # -------------------------------------------------------------------------
    def test_input_validation_valid_ranges(self):
        """Valid site parameters must construct without error."""
        self.assertEqual(self.site.basic_wind_speed_vb, 50.0)
        self.assertEqual(self.site.zone_factor_z, 0.16)
        self.assertFalse(self.site.is_high_rise_parent_building) # 12 m <= 19.5 m

    def test_input_validation_invalid_latitude_raises(self):
        """Latitude outside Indian subcontinent bounds must raise ValueError."""
        with self.assertRaises(ValueError):
            SiteParameters(
                location_name="Invalid Lat",
                latitude=45.0, # Beyond 38.0 deg N
                longitude=80.0,
                basic_wind_speed_vb=44.0,
                terrain_category=TerrainCategory.CATEGORY_2,
                building_height_m=10.0,
                rooftop_elevation_m=10.0,
            )

    def test_input_validation_invalid_wind_speed_raises(self):
        """Basic wind speed outside IS 875 bounds must raise ValueError."""
        with self.assertRaises(ValueError):
            SiteParameters(
                location_name="Invalid Wind",
                latitude=13.0,
                longitude=80.0,
                basic_wind_speed_vb=95.0, # Beyond 60 m/s
                terrain_category=TerrainCategory.CATEGORY_2,
                building_height_m=10.0,
                rooftop_elevation_m=10.0,
            )

    def test_input_validation_module_geometry_mismatch_raises(self):
        """Module count mismatch between rows*cols and total must raise ValueError."""
        with self.assertRaises(ValueError):
            ArrayGeometry(
                mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
                total_modules=25, # 4x5 = 20 != 25
                rows=4,
                columns=5,
                module=self.module,
            )

    # -------------------------------------------------------------------------
    # 2. Geometry & Unit Consistency
    # -------------------------------------------------------------------------
    def test_module_area_and_dead_load(self):
        """Verify SI unit consistency for module area and surface dead load."""
        area = self.module.area_m2
        expected_area = (2.278 * 1.134)
        self.assertAlmostEqual(area, expected_area, places=4)

        # Weight: 27.5 kg -> 27.5 * 9.80665 / 1000 = 0.26968 kN
        expected_dl = (27.5 * 9.80665 / 1000.0) / area
        self.assertAlmostEqual(self.module.dead_load_kn_per_m2, expected_dl, places=4)
        self.assertGreater(self.module.dead_load_kn_per_m2, 0.08) # Typically ~0.10 kN/m2

    def test_array_geometry_totals(self):
        """Verify array capacity and total module dead weight."""
        self.assertEqual(self.geometry_canopy.total_capacity_kw, 10.8) # 20 * 540W = 10.8 kW
        expected_total_weight_kn = 20 * (27.5 * 9.80665 / 1000.0)
        self.assertAlmostEqual(self.geometry_canopy.total_module_dead_weight_kn, expected_total_weight_kn, places=2)

    # -------------------------------------------------------------------------
    # 3. Physical Actions & Load Combination Generator
    # -------------------------------------------------------------------------
    def test_physical_action_register_nominal_values(self):
        """Verify nominal action values match IS 875 / IS 800 codal specifications."""
        self.assertEqual(ActionRegister.ACT_IL_01.nominal_value, 1.0)
        self.assertEqual(ActionRegister.ACT_IL_01.units, "kN")
        self.assertEqual(ActionRegister.ACT_IL_02.nominal_value, 0.75)
        self.assertEqual(ActionRegister.ACT_IL_04.nominal_value, 3.0)
        self.assertEqual(ActionRegister.ACT_ER_01.nominal_value, 1.0)

    def test_table_4_load_combinations_structure(self):
        """Verify IS 800: 2007 Table 4 load combinations include all 6 ULS cases."""
        combs = CombinationGenerator.generate_gravity_and_wind_combinations()
        comb_ids = [c.comb_id for c in combs]
        self.assertIn("ULS-01", comb_ids)
        self.assertIn("ULS-02", comb_ids)
        self.assertIn("ULS-03", comb_ids)
        self.assertIn("ULS-04", comb_ids)
        self.assertIn("ULS-05", comb_ids)
        self.assertIn("ULS-06", comb_ids)
        self.assertIn("SLS-01", comb_ids)

        # ULS-02 must use 0.9 DL factor for stabilizing dead load
        uls02 = next(c for c in combs if c.comb_id == "ULS-02")
        self.assertEqual(uls02.factors["DL"], 0.9)
        self.assertEqual(uls02.factors["WL_up"], 1.5)

        # ULS-06 must use 1.2 DL and 1.2 ER for erection stage
        uls06 = next(c for c in combs if c.comb_id == "ULS-06")
        self.assertEqual(uls06.factors["DL"], 1.2)
        self.assertEqual(uls06.factors["ER"], 1.2)

    def test_seismic_combinations_differentiate_vertical_coefficient(self):
        """Verify horizontal-dominant cases use 0.45 Ez while vertical-dominant use 1.5 Ez."""
        seismic_combs = CombinationGenerator.generate_seismic_combinations(include_vertical=True)
        eq01 = next(c for c in seismic_combs if c.comb_id == "ULS-EQ-01")
        eq17 = next(c for c in seismic_combs if c.comb_id == "ULS-EQ-17")

        # In ULS-EQ-01 (horizontal dominant), net Ez is 1.5 * 0.3 = 0.45
        self.assertEqual(eq01.factors["EZ"], 0.45)
        # In ULS-EQ-17 (vertical dominant), net Ez is 1.5 * 1.0 = 1.50!
        self.assertEqual(eq17.factors["EZ"], 1.50)

    # -------------------------------------------------------------------------
    # 4. Independent Calculation Engine (Traceability & Precision)
    # -------------------------------------------------------------------------
    def test_wind_engine_calculation_trace(self):
        """Verify wind engine calculates Vz and pz deterministically with trace log."""
        engine = StructuralCalculationEngine(site=self.site, geometry=self.geometry_canopy)
        Vz, pz_kpa, trace = engine.calculate_design_wind_speed_and_pressure()

        self.assertGreater(Vz, self.site.basic_wind_speed_vb) # Vz > 50 due to k4=1.15
        self.assertGreater(pz_kpa, 1.5) # Expected ~1.8 to 2.2 kN/m2 for Chennai coast
        self.assertIn("Vz_m_s", trace)
        self.assertIn("pz_kpa", trace)

    def test_seismic_engine_calculation(self):
        """Verify seismic engine calculates base shear Ah * W without live load."""
        engine = StructuralCalculationEngine(site=self.site, geometry=self.geometry_canopy)
        Vb_eq, Fz_eq, trace = engine.calculate_equivalent_static_seismic_forces()

        # In Zone III: Z=0.16, I=1.0, R=4.0, Sa/g=2.5 -> Ah = (0.16/2) * (1/4) * 2.5 = 0.05
        expected_Ah = (0.16 / 2.0) * (1.0 / 4.0) * 2.5
        self.assertAlmostEqual(trace["Ah"], expected_Ah, places=4)
        self.assertAlmostEqual(trace["Av"], (2.0 / 3.0) * expected_Ah, places=4)

    def test_purlin_member_check_governed_by_point_load(self):
        """Short-span purlins (e.g. 1.5 m) must be governed by 1.0 kN point load ACT-IL-01."""
        geometry_short = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=1500.0, # 1.5 m span
            ground_clearance_mm=2800.0,
        )
        engine = StructuralCalculationEngine(site=self.site, geometry=geometry_short)
        results = engine.check_purlin_member(
            section=self.purlin_section,
            span_mm=1500.0,
            tributary_width_mm=1150.0,
        )
        sagging_res = next(r for r in results if "Sagging Flexure" in r.check_name)
        self.assertIn("ACT-IL-01 Point Load", sagging_res.governing_combination)

    # -------------------------------------------------------------------------
    # 5. Verification Hold Register & Gate Enforcement
    # -------------------------------------------------------------------------
    def test_all_12_canonical_holds_active(self):
        """Verify exactly 12 original verification holds are present and active."""
        reg = VerificationRegister()
        active_holds = reg.get_active_holds()
        self.assertEqual(len(active_holds), 12)

        expected_ids = [
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
        active_ids = [h.hold_id for h in active_holds]
        for exp_id in expected_ids:
            self.assertIn(exp_id, active_ids)

    def test_gate_forbids_approved_for_construction(self):
        """In Phase 1, can_label_approved_for_construction must return False for all systems."""
        reg = VerificationRegister()
        for sys_type in MountingSystemType:
            can_approve = reg.can_label_approved_for_construction(sys_type.value)
            self.assertFalse(can_approve, f"{sys_type.value} was erroneously marked approvable!")
            watermark = reg.get_drawing_watermark(sys_type.value)
            self.assertEqual(watermark, "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION")

    # -------------------------------------------------------------------------
    # 6. DXF Generation Engine
    # -------------------------------------------------------------------------
    def test_dxf_generation_creates_valid_file_with_watermark(self):
        """DXF drawing engine must create a valid DXF file containing watermark and title block."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dxf_path = os.path.join(tmp_dir, "test_system_a_layout.dxf")
            metadata = DrawingMetadata(
                project_id="RENSUN-TEST-001",
                client_name="Test Industrial Client",
                site_location="Chennai",
                system_type=MountingSystemType.SYSTEM_A_CANOPY,
                drawing_number="RS-STR-A-001",
                revision="R0",
                date="2026-11-06",
            )
            drawer = DXFDrawingEngine(geometry=self.geometry_canopy, metadata=metadata)
            generated_file = drawer.generate_dxf(dxf_path)

            self.assertTrue(os.path.exists(generated_file))
            self.assertGreater(os.path.getsize(generated_file), 1000)

            # Inspect DXF with ezdxf
            doc = ezdxf.readfile(generated_file)
            msp = doc.modelspace()
            layers = [l.dxf.name for l in doc.layers]
            self.assertIn("MODULES", layers)
            self.assertIn("WATERMARK", layers)
            self.assertIn("TITLE_BLOCK", layers)

            # Verify watermark entity exists
            watermark_texts = [
                e.dxf.text for e in msp.query("TEXT")
                if "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION" in e.dxf.text
            ]
            self.assertGreater(len(watermark_texts), 0)

    # -------------------------------------------------------------------------
    # 7. Four Dedicated Workflows
    # -------------------------------------------------------------------------
    def test_workflow_system_a_canopy(self):
        """System A workflow must execute and check simultaneous array and walkway live loads."""
        workflow = SystemACanopyWorkflow(site=self.site, geometry=self.geometry_canopy)
        rafter_section = SectionProperty(
            designation="ISMB 200",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=3230.0,
            Ixx_mm4=22354000.0,
            Iyy_mm4=1500000.0,
            Zxx_mm3=223500.0,
            Zyy_mm3=30000.0,
            rxx_mm=83.2,
            ryy_mm=21.5,
            mass_kg_m=25.4,
        )
        report = workflow.run_workflow_analysis(
            purlin_section=self.purlin_section,
            rafter_section=rafter_section,
            column_section=rafter_section,
            walkway_width_m=0.80,
        )
        self.assertGreater(len(report.results), 0)
        self.assertTrue(any("Primary Rafter Sagging Flexure" in r.check_name for r in report.results))

    def test_workflow_system_d_ballasted_sliding(self):
        """System D workflow must evaluate ballast sliding with zero adverse live load."""
        geom_d = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_D_BALLASTED,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=2000.0,
            ground_clearance_mm=200.0,
        )
        workflow = SystemDBallastedWorkflow(site=self.site, geometry=geom_d)
        report = workflow.run_workflow_analysis(
            ballast_weight_kn_per_m2=0.75,
            friction_coeff_mu=0.40,
        )
        self.assertGreater(len(report.results), 0)
        self.assertTrue(any("Sliding Resistance" in r.check_name for r in report.results))

    def test_individual_hold_enforcement_blocks_each_system(self):
        """Each of the 12 canonical holds must independently block approval and enforce watermark."""
        expected_ids = [
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
        for target_hold_id in expected_ids:
            reg = VerificationRegister()
            # Release all holds except target_hold_id
            for h in reg.get_all_holds():
                if h.hold_id != target_hold_id:
                    h.status = HoldStatus.RELEASED_WITH_CERTIFICATE
                else:
                    h.status = HoldStatus.ACTIVE_ENFORCED

            target_hold = reg.get_hold(target_hold_id)
            self.assertIsNotNone(target_hold)
            self.assertTrue(target_hold.is_active())

            # For every affected system, approval must be forbidden and watermark enforced
            for sys_name in target_hold.affected_systems:
                can_approve = reg.can_label_approved_for_construction(sys_name)
                self.assertFalse(can_approve, f"Hold {target_hold_id} failed to block approval for {sys_name}!")
                watermark = reg.get_drawing_watermark(sys_name)
                self.assertEqual(
                    watermark,
                    "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION",
                    f"Hold {target_hold_id} failed to enforce watermark for {sys_name}!",
                )

    def test_dxf_drawing_engine_permission_check_blocks_approval(self):
        """DXF generation must raise PermissionError if require_approved or is_approved_for_construction is set."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dxf_path = os.path.join(tmp_dir, "test_blocked.dxf")
            metadata = DrawingMetadata(
                project_id="RENSUN-TEST-GATE",
                client_name="Test Gate Client",
                site_location="Chennai",
                system_type=MountingSystemType.SYSTEM_A_CANOPY,
                drawing_number="RS-STR-A-GATE",
            )
            drawer = DXFDrawingEngine(geometry=self.geometry_canopy, metadata=metadata)

            # Explicit require_approved=True must raise PermissionError
            with self.assertRaises(PermissionError):
                drawer.generate_dxf(dxf_path, require_approved=True)

            # Metadata with is_approved_for_construction=True must raise PermissionError
            metadata_afc = DrawingMetadata(
                project_id="RENSUN-TEST-GATE",
                client_name="Test Gate Client",
                site_location="Chennai",
                system_type=MountingSystemType.SYSTEM_A_CANOPY,
                drawing_number="RS-STR-A-GATE",
                is_approved_for_construction=True,
            )
            drawer_afc = DXFDrawingEngine(geometry=self.geometry_canopy, metadata=metadata_afc)
            with self.assertRaises(PermissionError):
                drawer_afc.generate_dxf(dxf_path)

    def test_purlin_shear_check_under_point_and_distributed_load(self):
        """Purlin checks must evaluate shear capacity under both LC-DIST and LC-POINT."""
        engine = StructuralCalculationEngine(site=self.site, geometry=self.geometry_canopy)
        results = engine.check_purlin_member(
            section=self.purlin_section,
            span_mm=2500.0,
            tributary_width_mm=1150.0,
        )
        shear_res = next((r for r in results if "Purlin Major-Axis Shear" in r.check_name), None)
        self.assertIsNotNone(shear_res)
        self.assertAlmostEqual(shear_res.capacity_value, self.purlin_section.design_shear_capacity_major_kn, places=2)
        self.assertGreater(shear_res.demand_value, 0.0)
        self.assertIn("IS 800: 2007 Clause 8.4.1", shear_res.clause_reference)

    def test_workflow_system_a_canopy_column_buckling(self):
        """System A canopy workflow must evaluate column axial compression & buckling resistance."""
        workflow = SystemACanopyWorkflow(site=self.site, geometry=self.geometry_canopy)
        rafter_section = SectionProperty(
            designation="ISMB 200",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=3230.0,
            Ixx_mm4=22354000.0,
            Iyy_mm4=1500000.0,
            Zxx_mm3=223500.0,
            Zyy_mm3=30000.0,
            rxx_mm=83.2,
            ryy_mm=21.5,
            mass_kg_m=25.4,
        )
        report = workflow.run_workflow_analysis(
            purlin_section=self.purlin_section,
            rafter_section=rafter_section,
            column_section=rafter_section,
            walkway_width_m=0.80,
        )
        buckling_res = next((r for r in report.results if "Canopy Column Axial Buckling Resistance" in r.check_name), None)
        self.assertIsNotNone(buckling_res)
        self.assertGreater(buckling_res.demand_value, 0.0)
        self.assertGreater(buckling_res.capacity_value, 0.0)
        self.assertIn("IS 800: 2007 Clause 7.1.2", buckling_res.clause_reference)

    def test_workflow_system_d_overturning_stability(self):
        """System D workflow must evaluate overturning stability with adverse live load strictly zero."""
        geom_d = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_D_BALLASTED,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=2000.0,
            ground_clearance_mm=200.0,
        )
        workflow = SystemDBallastedWorkflow(site=self.site, geometry=geom_d)
        report = workflow.run_workflow_analysis(
            ballast_weight_kn_per_m2=0.75,
            friction_coeff_mu=0.40,
        )
        ot_res = next((r for r in report.results if "Ballast Overturning Stability about Leeward Toe" in r.check_name), None)
        self.assertIsNotNone(ot_res)
        self.assertIn("adverse live load strictly zero", ot_res.notes)
        self.assertIn("IL = 0", ot_res.governing_combination)

    def test_dxf_dimensions_layer_verification(self):
        """DXF drawing must contain DIMENSIONS layer with width and length linear annotations."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dxf_path = os.path.join(tmp_dir, "test_dim_layout.dxf")
            metadata = DrawingMetadata(
                project_id="RENSUN-TEST-DIM",
                client_name="Dimension Check Client",
                site_location="Chennai",
                system_type=MountingSystemType.SYSTEM_A_CANOPY,
                drawing_number="RS-STR-DIM-001",
            )
            drawer = DXFDrawingEngine(geometry=self.geometry_canopy, metadata=metadata)
            generated_file = drawer.generate_dxf(dxf_path)

            doc = ezdxf.readfile(generated_file)
            msp = doc.modelspace()
            dim_layers = [e.dxf.layer for e in msp if e.dxf.layer == "DIMENSIONS"]
            self.assertGreater(len(dim_layers), 0)

            dim_texts = [e.dxf.text for e in msp.query("TEXT") if e.dxf.layer == "DIMENSIONS"]
            self.assertTrue(any("OVERALL ARRAY WIDTH" in t for t in dim_texts))
            self.assertTrue(any("OVERALL ARRAY LENGTH" in t for t in dim_texts))

    def test_workflow_system_b_aluminium_rail(self):
        """System B workflow must evaluate extruded aluminium rail flexure, shear, and clamp tension."""
        geom_b = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=1400.0,
            ground_clearance_mm=250.0,
        )
        rail_section = SectionProperty(
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
        workflow = SystemBAluminiumRailWorkflow(site=self.site, geometry=geom_b)
        report = workflow.run_workflow_analysis(
            rail_section=rail_section,
            bracket_spacing_mm=1400.0,
        )
        self.assertGreater(len(report.results), 0)
        self.assertTrue(any("Purlin Sagging Flexure" in r.check_name for r in report.results))
        self.assertTrue(any("Module Mid-Clamp Fastener Tension" in r.check_name for r in report.results))
        self.assertEqual(report.system_type, MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL)

    def test_workflow_system_c_metal_sheet(self):
        """System C workflow must evaluate standing-seam clamp tensile pull-out under wind uplift."""
        geom_c = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_C_METAL_SHEET,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=1500.0,
            ground_clearance_mm=100.0,
        )
        workflow = SystemCMetalSheetWorkflow(site=self.site, geometry=geom_c)
        report = workflow.run_workflow_analysis(
            sheet_clamp_tensile_capacity_kn=3.50,
            sheet_gauge_bmt_mm=0.50,
        )
        self.assertGreater(len(report.results), 0)
        self.assertTrue(any("Metal Sheet Clamp Seam Tensile Pull-Out" in r.check_name for r in report.results))
        self.assertEqual(report.system_type, MountingSystemType.SYSTEM_C_METAL_SHEET)

    # -------------------------------------------------------------------------
    # 8. Existing Application Regression Protection
    # -------------------------------------------------------------------------
    def test_existing_quotation_modules_regression(self):
        """Verify existing quotation engine, solar sizing, and pricing remain 100% operational."""
        from solar_engine.solar_sizing import size_solar_system
        from quotation.pricing_engine import calculate_quotation_pricing
        from quotation.settings_manager import load_owner_settings

        # Test solar sizing
        sizing = size_solar_system(annual_consumption_kwh=12000.0)
        self.assertGreater(sizing["recommended_capacity_kw"], 0)

        # Test owner settings
        settings = load_owner_settings()
        self.assertIn("pricing", settings)
        self.assertIn("price_per_kw", settings["pricing"])

        # Test pricing engine
        pricing = calculate_quotation_pricing(
            system_capacity_kw=5.0,
            pricing_config=settings["pricing"],
        )
        self.assertIn("net_customer_payable", pricing)
        self.assertGreater(pricing["net_customer_payable"], 0)


if __name__ == "__main__":
    unittest.main()
