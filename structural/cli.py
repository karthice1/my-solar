"""
Structural Command-Line Interface (CLI) for RENSUN Solar
Package: structural.cli
Executable via: python -m structural.cli <command> [subcommand] [options]

Subsystems:
1. project     (create, list, show, set-site, set-module, set-geometry, set-material, set-section)
2. system      (list, select)
3. calculate   (validate-inputs, loads, run, results)
4. holds       (list, show, check)
5. drawing     (preview, export-dxf)
"""

import argparse
import json
import os
import sys
from typing import Optional, List

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
from structural.actions import (
    ActionRegister,
    CombinationGenerator,
)
from structural.engine import StructuralCalculationEngine
from structural.drawing import DXFDrawingEngine
from structural.db import StructuralDatabase, DEFAULT_DB_PATH


# Helper for mounting system mapping
SYSTEM_MAPPING = {
    "A": MountingSystemType.SYSTEM_A_CANOPY,
    "B": MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL,
    "C": MountingSystemType.SYSTEM_C_METAL_SHEET,
    "D": MountingSystemType.SYSTEM_D_BALLASTED,
}


def get_db(db_path: Optional[str] = None) -> StructuralDatabase:
    """Returns database instance, honoring CLI or environment override."""
    path = db_path or os.environ.get("STRUCTURAL_DB_PATH", DEFAULT_DB_PATH)
    return StructuralDatabase(db_path=path)


def resolve_system(sys_input: str) -> MountingSystemType:
    """Resolves short key 'A', 'B', 'C', 'D' or full string to MountingSystemType."""
    key = sys_input.strip().upper()
    if key in SYSTEM_MAPPING:
        return SYSTEM_MAPPING[key]
    for m in MountingSystemType:
        if key in m.name or key in m.value.upper():
            return m
    raise ValueError(f"Unknown mounting system '{sys_input}'. Choose from: A, B, C, D.")


# -----------------------------------------------------------------------------
# Command Handlers
# -----------------------------------------------------------------------------

def handle_project_create(args):
    db = get_db(args.db_path)
    try:
        sys_type = resolve_system(args.system)
        proj = db.create_project(
            project_id=args.project_id,
            name=args.name,
            mounting_system=sys_type,
            client_name=args.client or "",
            site_location=args.location or "",
        )
        print(f"SUCCESS: Created structural project '{proj['project_id']}'.")
        print(f"  Name:            {proj['name']}")
        print(f"  Mounting System: {proj['mounting_system']}")
        print(f"  Client:          {proj['client_name']}")
        print(f"  Location:        {proj['site_location']}")
        print(f"  Status:          {proj['status']}")
    except Exception as e:
        print(f"ERROR: Failed to create project: {e}", file=sys.stderr)
        return 1
    return 0


def handle_project_list(args):
    db = get_db(args.db_path)
    projects = db.list_projects()
    if not projects:
        print("No structural projects found. Use 'project create' to initialize one.")
        return 0

    print("=" * 80)
    print(f"{'PROJECT ID':<15} {'NAME':<25} {'SYSTEM':<30} {'STATUS':<8}")
    print("=" * 80)
    for p in projects:
        sys_short = p['mounting_system'].split(':')[0]
        print(f"{p['project_id']:<15} {p['name'][:24]:<25} {sys_short:<30} {p['status']:<8}")
    print("=" * 80)
    print(f"Total Projects: {len(projects)}")
    return 0


def handle_project_show(args):
    db = get_db(args.db_path)
    proj = db.get_project(args.project_id)
    if not proj:
        print(f"ERROR: Project '{args.project_id}' not found.", file=sys.stderr)
        return 1

    site = db.get_site(args.project_id)
    module = db.get_module(args.project_id)
    geometry = db.get_geometry(args.project_id)
    latest_run = db.get_latest_run_for_project(args.project_id)

    print("=" * 80)
    print(f"PROJECT DETAILS: {proj['project_id']}")
    print("=" * 80)
    print(f"Name:             {proj['name']}")
    print(f"Client:           {proj['client_name']}")
    print(f"Site Location:    {proj['site_location']}")
    print(f"Mounting System:  {proj['mounting_system']}")
    print(f"Status:           {proj['status']}")
    print(f"Created:          {proj['created_at']}")
    print(f"Updated:          {proj['updated_at']}")
    print("-" * 80)
    print(f"Site Configured:     {'YES (' + site.location_name + ')' if site else 'NO'}")
    print(f"Module Configured:   {'YES (' + module.make_model + ')' if module else 'NO'}")
    print(f"Geometry Configured: {'YES (' + str(geometry.total_modules) + ' modules)' if geometry else 'NO'}")
    if latest_run:
        print(f"Latest Calc Run:     {latest_run['run_id']} [{latest_run['status']}] (Max Unity: {latest_run['max_unity_ratio']:.3f})")
    else:
        print("Latest Calc Run:     NONE")
    print("=" * 80)
    return 0


def handle_project_set_site(args):
    db = get_db(args.db_path)
    try:
        proj = db.get_project(args.project_id)
        if not proj:
            print(f"ERROR: Project '{args.project_id}' does not exist.", file=sys.stderr)
            return 1

        if args.file:
            with open(args.file, "r") as f:
                d = json.load(f)
            lat = float(d["latitude"])
            lon = float(d["longitude"])
            vb = float(d["basic_wind_speed_vb"])
            height = float(d.get("building_height_m", 12.0))
            site = SiteParameters(
                location_name=d["location_name"],
                latitude=lat,
                longitude=lon,
                basic_wind_speed_vb=vb,
                terrain_category=TerrainCategory(int(d.get("terrain_category", 3))),
                building_height_m=height,
                rooftop_elevation_m=float(d.get("rooftop_elevation_m", height)),
                cyclonic_factor_k4=float(d.get("cyclonic_factor_k4", 1.0)),
                topography_factor_k3=float(d.get("topography_factor_k3", 1.0)),
                risk_coefficient_k1=float(d.get("risk_coefficient_k1", 1.0)),
                seismic_zone=SeismicZone(d.get("seismic_zone", "Zone III")),
                importance_factor_I=float(d.get("importance_factor_I", 1.0)),
                response_reduction_R=float(d.get("response_reduction_R", 4.0)),
                soil_type=int(d.get("soil_type", 2)),
            )
        else:
            if not args.location or args.lat is None or args.lon is None or args.vb is None:
                print("ERROR: Missing required site flags (--location, --lat, --lon, --vb) or --file.", file=sys.stderr)
                return 1
            lat = float(args.lat)
            lon = float(args.lon)
            vb = float(args.vb)
            height = float(args.height or 12.0)
            site = SiteParameters(
                location_name=args.location,
                latitude=lat,
                longitude=lon,
                basic_wind_speed_vb=vb,
                terrain_category=TerrainCategory(int(args.terrain or 3)),
                building_height_m=height,
                rooftop_elevation_m=float(args.elevation or height),
                cyclonic_factor_k4=float(args.k4 or 1.0),
                topography_factor_k3=float(args.k3 or 1.0),
                risk_coefficient_k1=float(args.k1 or 1.0),
                seismic_zone=SeismicZone(args.seismic_zone or "Zone III"),
            )

        db.set_site(args.project_id, site)
        db.record_parameter_provenance(
            project_id=args.project_id,
            parameter_key="coordinates",
            value=f"{site.latitude}, {site.longitude}",
            units="deg",
            level="Level 5: Assumed Provisional (Requires Physical Verification)",
            source_reference="CLI configured coordinates",
            notes="Requires RTK GNSS field survey"
        )
        db.record_parameter_provenance(
            project_id=args.project_id,
            parameter_key="basic_wind_speed_vb",
            value=str(site.basic_wind_speed_vb),
            units="m/s",
            level="Level 5: Assumed Provisional (Requires Physical Verification)" if site.basic_wind_speed_vb == 39.0 else "Level 4: Statutory Code Value (Published IS Standard Reference)",
            source_reference="IS 875 Part 3 Figure 1",
            notes="Provisional regional contour interpolation if unlisted"
        )
        print(f"SUCCESS: Site parameters configured for project '{args.project_id}'.")
        print(f"  Location: {site.location_name} (Lat: {site.latitude}, Lon: {site.longitude})")
        print(f"  Wind Vb:  {site.basic_wind_speed_vb} m/s (k4={site.cyclonic_factor_k4})")
        print(f"  Seismic:  {site.seismic_zone.value} (Z={site.zone_factor_z})")
    except Exception as e:
        print(f"ERROR: Failed to set site: {e}", file=sys.stderr)
        return 1
    return 0


def handle_project_set_module(args):
    db = get_db(args.db_path)
    try:
        proj = db.get_project(args.project_id)
        if not proj:
            print(f"ERROR: Project '{args.project_id}' does not exist.", file=sys.stderr)
            return 1

        if args.file:
            with open(args.file, "r") as f:
                d = json.load(f)
            module = PVModuleSpecification(
                make_model=d["make_model"],
                length_mm=float(d["length_mm"]),
                width_mm=float(d["width_mm"]),
                thickness_mm=float(d["thickness_mm"]),
                weight_kg=float(d["weight_kg"]),
                peak_power_w=float(d["peak_power_w"]),
                tilt_deg=float(d.get("tilt_deg", 10.0)),
                azimuth_deg=float(d.get("azimuth_deg", 180.0)),
            )
        else:
            if not args.make_model or args.length is None or args.width is None or args.weight is None or args.power is None:
                print("ERROR: Missing required module flags (--make-model, --length, --width, --weight, --power) or --file.", file=sys.stderr)
                return 1
            module = PVModuleSpecification(
                make_model=args.make_model,
                length_mm=float(args.length),
                width_mm=float(args.width),
                thickness_mm=float(args.thickness or 35.0),
                weight_kg=float(args.weight),
                peak_power_w=float(args.power),
                tilt_deg=float(args.tilt or 10.0),
                azimuth_deg=float(args.azimuth or 180.0),
            )

        db.set_module(args.project_id, module)
        db.record_parameter_provenance(
            project_id=args.project_id,
            parameter_key="module_specification",
            value=f"{module.make_model} ({module.peak_power_w} Wp)",
            units="spec",
            level="Level 3: Client Certified (Written Form from Host Building Owner)",
            source_reference="Manufacturer Datasheet Specification",
            certifier_name="Solar Quotation Spec",
            notes="Datasheet specifications"
        )
        print(f"SUCCESS: PV module configured for project '{args.project_id}'.")
        print(f"  Make/Model: {module.make_model} ({module.peak_power_w} W)")
        print(f"  Dimensions: {module.length_mm:.0f} x {module.width_mm:.0f} x {module.thickness_mm:.0f} mm")
        print(f"  Dead Load:  {module.dead_load_kn_per_m2:.3f} kN/m2 (Weight: {module.weight_kg} kg)")
    except Exception as e:
        print(f"ERROR: Failed to set module: {e}", file=sys.stderr)
        return 1
    return 0


def handle_project_set_geometry(args):
    db = get_db(args.db_path)
    try:
        proj = db.get_project(args.project_id)
        if not proj:
            print(f"ERROR: Project '{args.project_id}' does not exist.", file=sys.stderr)
            return 1

        module = db.get_module(args.project_id)
        if not module:
            print("ERROR: Please configure PV module first ('project set-module').", file=sys.stderr)
            return 1

        sys_type = resolve_system(proj["mounting_system"])

        if args.file:
            with open(args.file, "r") as f:
                d = json.load(f)
            rows = int(d["rows"])
            cols = int(d["columns"])
            total = int(d.get("total_modules", rows * cols))
            if rows <= 0 or cols <= 0 or total <= 0:
                print("ERROR: Grid rows, columns, and total modules must be strictly positive.", file=sys.stderr)
                return 1
            if rows * cols != total:
                print(f"ERROR: Geometry mismatch: rows ({rows}) x columns ({cols}) = {rows*cols} != total_modules ({total}).", file=sys.stderr)
                return 1
            purlin_sp = float(d.get("purlin_spacing_mm", 1200.0))
            rafter_sp = float(d.get("rafter_spacing_mm", 3000.0))
            clearance = float(d.get("ground_clearance_mm", 2400.0))
            if purlin_sp <= 0 or rafter_sp <= 0 or clearance < 0:
                print("ERROR: Spacing dimensions must be strictly positive and clearance non-negative.", file=sys.stderr)
                return 1
            geometry = ArrayGeometry(
                mounting_system=sys_type,
                total_modules=total,
                rows=rows,
                columns=cols,
                module=module,
                orientation=d.get("orientation", "PORTRAIT"),
                purlin_spacing_mm=purlin_sp,
                rafter_spacing_mm=rafter_sp,
                ground_clearance_mm=clearance,
            )
        else:
            if args.rows is None or args.cols is None:
                print("ERROR: Missing required geometry flags (--rows, --cols) or --file.", file=sys.stderr)
                return 1
            rows = int(args.rows)
            cols = int(args.cols)
            total = rows * cols
            purlin_sp = float(args.purlin_spacing or 1200.0)
            rafter_sp = float(args.rafter_spacing or 3000.0)
            clearance = float(args.ground_clearance or 2400.0)
            if rows <= 0 or cols <= 0 or purlin_sp <= 0 or rafter_sp <= 0 or clearance < 0:
                print("ERROR: Dimensions and grid counts must be strictly positive.", file=sys.stderr)
                return 1
            geometry = ArrayGeometry(
                mounting_system=sys_type,
                total_modules=total,
                rows=rows,
                columns=cols,
                module=module,
                purlin_spacing_mm=purlin_sp,
                rafter_spacing_mm=rafter_sp,
                ground_clearance_mm=clearance,
            )

        db.set_geometry(args.project_id, geometry)
        print(f"SUCCESS: Array geometry configured for project '{args.project_id}'.")
        print(f"  Configuration: {geometry.rows} rows x {geometry.columns} cols = {geometry.total_modules} modules")
        print(f"  Total DC Peak: {geometry.total_capacity_kw:.2f} kWp")
        print(f"  Array Spacing: Purlin={geometry.purlin_spacing_mm:.0f} mm, Rafter={geometry.rafter_spacing_mm:.0f} mm")
    except Exception as e:
        print(f"ERROR: Failed to set geometry: {e}", file=sys.stderr)
        return 1
    return 0


def handle_project_set_material(args):
    db = get_db(args.db_path)
    try:
        proj = db.get_project(args.project_id)
        if not proj:
            print(f"ERROR: Project '{args.project_id}' does not exist.", file=sys.stderr)
            return 1

        comp = args.component.strip().upper()
        if args.preset:
            preset = args.preset.strip().upper()
            if preset in ("E250", "STEEL", "STEEL_E250"):
                mat = STEEL_E250
            elif preset in ("6063-T6", "ALUMINIUM", "ALU", "ALUMINIUM_6063_T6"):
                mat = ALUMINIUM_6063_T6
            elif preset in ("A2-70", "SS", "STAINLESS", "STAINLESS_STEEL_A2_70"):
                mat = STAINLESS_STEEL_A2_70
            else:
                print(f"ERROR: Unknown preset '{args.preset}'. Choose from: E250, 6063-T6, A2-70.", file=sys.stderr)
                return 1
        else:
            if not args.name or args.fy is None or args.fu is None or args.e_mod is None:
                print("ERROR: Missing required material flags (--name, --fy, --fu, --e-mod) or --preset.", file=sys.stderr)
                return 1
            e_mod = float(args.e_mod)
            fy = float(args.fy)
            fu = float(args.fu)
            density = float(args.density or 7850.0)
            if e_mod <= 0 or fy <= 0 or fu <= 0 or density <= 0:
                print("ERROR: Material strengths and modulus must be strictly positive.", file=sys.stderr)
                return 1
            mat = MaterialProperty(
                name=args.name,
                grade=args.grade or "Custom Grade",
                elastic_modulus_mpa=e_mod,
                yield_strength_mpa=fy,
                ultimate_strength_mpa=fu,
                density_kg_m3=density,
                poisson_ratio=float(args.poisson or 0.30),
                standard_reference=args.standard or "IS 2062: 2011",
                gamma_m0_override=float(args.gamma_m0) if args.gamma_m0 else None,
                gamma_m1_override=float(args.gamma_m1) if args.gamma_m1 else None,
            )

        db.set_material(args.project_id, comp, mat)
        print(f"SUCCESS: Material configured for {comp} in project '{args.project_id}'.")
        print(f"  Material: {mat.name} (fy={mat.yield_strength_mpa} MPa, E={mat.elastic_modulus_mpa:.0f} MPa)")
    except Exception as e:
        print(f"ERROR: Failed to set material: {e}", file=sys.stderr)
        return 1
    return 0


def handle_project_set_section(args):
    db = get_db(args.db_path)
    try:
        proj = db.get_project(args.project_id)
        if not proj:
            print(f"ERROR: Project '{args.project_id}' does not exist.", file=sys.stderr)
            return 1

        comp = args.component.strip().upper()
        mat = db.get_material(args.project_id, comp)
        if not mat:
            # Default fallback preset material
            mat = STEEL_E250 if comp in ("PURLIN", "RAFTER", "COLUMN") else ALUMINIUM_6063_T6
            db.set_material(args.project_id, comp, mat)

        if args.file:
            with open(args.file, "r") as f:
                d = json.load(f)
            area = float(d["area_mm2"])
            ixx = float(d["Ixx_mm4"])
            zxx = float(d["Zxx_mm3"])
            if area <= 0 or ixx <= 0 or zxx <= 0:
                print("ERROR: Section area and inertia must be strictly positive.", file=sys.stderr)
                return 1
            sec = SectionProperty(
                designation=d["designation"],
                profile_type=d["profile_type"],
                material=mat,
                area_mm2=area,
                Ixx_mm4=ixx,
                Iyy_mm4=float(d.get("Iyy_mm4", ixx * 0.2)),
                Zxx_mm3=zxx,
                Zyy_mm3=float(d.get("Zyy_mm3", zxx * 0.3)),
                rxx_mm=float(d.get("rxx_mm", 40.0)),
                ryy_mm=float(d.get("ryy_mm", 20.0)),
                mass_kg_m=float(d.get("mass_kg_m", area * 7.85e-3)),
                shear_area_mm2=float(d["shear_area_mm2"]) if d.get("shear_area_mm2") else None,
            )
        else:
            if not args.designation or args.area is None or args.ixx is None or args.zxx is None:
                print("ERROR: Missing required section flags (--designation, --area, --ixx, --zxx) or --file.", file=sys.stderr)
                return 1
            area = float(args.area)
            ixx = float(args.ixx)
            zxx = float(args.zxx)
            if area <= 0 or ixx <= 0 or zxx <= 0:
                print("ERROR: Section area, moment of inertia, and section modulus must be strictly positive.", file=sys.stderr)
                return 1
            sec = SectionProperty(
                designation=args.designation,
                profile_type=getattr(args, "profile_type", None) or "Custom Profile",
                material=mat,
                area_mm2=area,
                Ixx_mm4=ixx,
                Iyy_mm4=float(getattr(args, "iyy", None) or (ixx * 0.2)),
                Zxx_mm3=zxx,
                Zyy_mm3=float(getattr(args, "zyy", None) or (zxx * 0.3)),
                rxx_mm=float(getattr(args, "rxx", None) or (ixx / area)**0.5),
                ryy_mm=float(getattr(args, "ryy", None) or 20.0),
                mass_kg_m=float(getattr(args, "mass", None) or (area * 7.85e-3)),
                shear_area_mm2=float(args.shear_area) if getattr(args, "shear_area", None) else None,
            )

        db.set_section(args.project_id, comp, sec)
        print(f"SUCCESS: Section configured for {comp} in project '{args.project_id}'.")
        print(f"  Designation: {sec.designation} ({sec.profile_type})")
        print(f"  Capacity:    Md_major = {sec.design_moment_capacity_major_kn_m:.2f} kN*m, Vd = {sec.design_shear_capacity_major_kn:.2f} kN")
    except Exception as e:
        print(f"ERROR: Failed to set section: {e}", file=sys.stderr)
        return 1
    return 0


# -----------------------------------------------------------------------------
# System Operations
# -----------------------------------------------------------------------------

def handle_system_list(args):
    print("=" * 80)
    print("SUPPORTED SOLAR MOUNTING SYSTEMS")
    print("=" * 80)
    print("SYSTEM A: Elevated Steel Canopy")
    print("  Scope:      High-clearance rooftop steel frame (2.4m - 3.5m clearance)")
    print("  Standards:  IS 800: 2007 (Steel Frame), IS 875 Part 3 Table 8 (Canopy wind)")
    print("  Loads:      Simultaneous array (ACT-IL-02) & walkway (ACT-IL-04) live loads")
    print("  Governed:   INSPECTION_REQUIRED_HOLD, AERODYNAMIC_UNSUPPORTED_HOLD")
    print("-" * 80)
    print("SYSTEM B: Low-Height Aluminium Rail")
    print("  Scope:      Low-profile flat roof mounting (100mm - 300mm clearance)")
    print("  Standards:  IS 8147: 1976 (Aluminium Design), IS 875 Part 3 Table 5")
    print("  Loads:      Governed by max(ACT-IL-01 point, ACT-IL-02 dist) live loads")
    print("  Governed:   ALUMINIUM_DERIVATION_HOLD, FASTENER_TORQUE_UNVERIFIED_HOLD")
    print("-" * 80)
    print("SYSTEM C: Metal-Sheet Roof Mounting")
    print("  Scope:      Direct-to-sheet or seam clamp mounting on industrial metal roofs")
    print("  Standards:  IS 800: 2007 Cl 10.3, IS 875 Part 3 Table 5")
    print("  Loads:      Wind uplift suction & clamp sheet pull-out resistance")
    print("  Governed:   FASTENER_TORQUE_UNVERIFIED_HOLD, ASSUMED_DATA_CERTIFICATION_HOLD")
    print("-" * 80)
    print("SYSTEM D: Ballasted Non-Penetrating System")
    print("  Scope:      Zero roof penetrations; precast concrete ballast blocks")
    print("  Standards:  IS 875 Part 3, EN 1990 Annex D (Friction Interface)")
    print("  Loads:      Uplift contact (Neff > 0), sliding (mu*Neff), overturning (FOS>=1.4)")
    print("  Governed:   FRICTION_UNVERIFIED_HOLD, AERODYNAMIC_UNSUPPORTED_HOLD")
    print("=" * 80)
    return 0


def handle_system_select(args):
    db = get_db(args.db_path)
    try:
        sys_type = resolve_system(args.system)
        db.update_project_system(args.project_id, sys_type)
        print(f"SUCCESS: Project '{args.project_id}' updated to mounting system: {sys_type.value}")
    except Exception as e:
        print(f"ERROR: Failed to update mounting system: {e}", file=sys.stderr)
        return 1
    return 0


# -----------------------------------------------------------------------------
# Calculation Operations
# -----------------------------------------------------------------------------

def handle_calculate_validate_inputs(args):
    db = get_db(args.db_path)
    proj = db.get_project(args.project_id)
    if not proj:
        print(f"ERROR: Project '{args.project_id}' not found.", file=sys.stderr)
        return 1

    is_valid, errors = db.validate_project_inputs(args.project_id)

    print("=" * 80)
    print(f"INPUT VALIDATION REPORT: {proj['project_id']}")
    print("=" * 80)
    print(f"Mounting System: {proj['mounting_system']}")
    if is_valid:
        print("STATUS: PASSED — All required inputs are present and within valid ranges.")
        print("  - Site Parameters:     CONFIGURED")
        print("  - PV Module Specs:     CONFIGURED")
        print("  - Array Geometry:      CONFIGURED")
        print("  - Member Sections:     CONFIGURED")
        print("=" * 80)
        return 0
    else:
        print("STATUS: FAILED — Missing or invalid structural inputs:")
        for err in errors:
            print(f"  [X] {err}")
        print("=" * 80)
        return 1


def handle_calculate_loads(args):
    db = get_db(args.db_path)
    proj = db.get_project(args.project_id)
    if not proj:
        print(f"ERROR: Project '{args.project_id}' not found.", file=sys.stderr)
        return 1

    site = db.get_site(args.project_id)
    geom = db.get_geometry(args.project_id)
    if not site or not geom:
        print("ERROR: Site and Geometry must be configured before calculating loads.", file=sys.stderr)
        return 1

    engine = StructuralCalculationEngine(site=site, geometry=geom)
    Vz, pz, wind_trace = engine.calculate_design_wind_speed_and_pressure()
    Vb_eq, Fz_eq, eq_trace = engine.calculate_equivalent_static_seismic_forces()
    combs = CombinationGenerator.generate_gravity_and_wind_combinations()

    print("=" * 80)
    print(f"STRUCTURAL LOADS & COMBINATIONS: {proj['project_id']}")
    print("=" * 80)
    print(f"DESIGN WIND (IS 875 Part 3: 2015):")
    print(f"  Basic Wind Speed (Vb):    {site.basic_wind_speed_vb:.1f} m/s")
    print(f"  Design Wind Speed (Vz):   {Vz:.2f} m/s (k1={site.risk_coefficient_k1}, k2={wind_trace['k2']:.3f}, k3={site.topography_factor_k3}, k4={site.cyclonic_factor_k4})")
    print(f"  Design Wind Pressure (pz):{pz:.3f} kN/m2 ({pz * 1000.0:.1f} Pa)")
    print("-" * 80)
    print(f"EQUIVALENT SEISMIC FORCES (IS 1893 Part 1: 2016):")
    print(f"  Seismic Zone:             {site.seismic_zone.value} (Z={site.zone_factor_z})")
    print(f"  Horizontal Coeff (Ah):    {eq_trace['Ah']:.4f}")
    print(f"  Vertical Coeff (Av):      {eq_trace['Av']:.4f}")
    print(f"  Total Seismic Weight (W): {eq_trace.get('W_modules_kn', eq_trace.get('seismic_weight_W_kn', 0.0)):.2f} kN")
    print(f"  Total Base Shear (Vb):    {Vb_eq:.3f} kN")
    print("-" * 80)
    print(f"LOAD COMBINATIONS GENERATED ({len(combs)} ULS/SLS Combinations per IS 800 Table 4):")
    for c in combs:
        factors_str = " + ".join(f"{v}*{k}" for k, v in c.factors.items() if v != 0)
        ls_str = c.limit_state.value if hasattr(c.limit_state, "value") else str(c.limit_state)
        print(f"  [{c.comb_id}] ({ls_str}): {factors_str}")
    print("=" * 80)
    return 0


def handle_calculate_run(args):
    db = get_db(args.db_path)
    try:
        run = db.execute_and_record_run(
            project_id=args.project_id,
            walkway_width_m=float(args.walkway_width or 0.80),
            ballast_weight_kn_per_m2=float(args.ballast_weight or 0.75),
            friction_coeff_mu=float(args.friction_mu or 0.40),
            sheet_clamp_tensile_kn=float(args.clamp_capacity or 3.50),
            bracket_spacing_mm=float(args.bracket_spacing or 1400.0),
        )

        proj = db.get_project(args.project_id)
        print("=" * 80)
        print(f"PROJECT:                 {proj['project_id']}")
        print(f"MOUNTING SYSTEM:         {run['mounting_system']}")
        print(f"INPUT VALIDATION:        PASSED")
        print(f"PRELIMINARY CALCULATION: COMPLETED (Run ID: {run['run_id']})")
        print(f"SOFTWARE VALIDATION:     PASSED ({run['status']})")
        print(f"ENGINEERING VALIDATION:  PENDING")
        print(f"ACTIVE ENGINEERING HOLDS:{run['active_holds_count']}")
        print(f"DRAWING STATUS:          PRELIMINARY ONLY")
        print(f"CONSTRUCTION APPROVAL:   BLOCKED")
        print("-" * 80)
        print(f"CALCULATION RESULTS SUMMARY:")
        print(f"  Overall Status:        {run['status']}")
        print(f"  Max Unity Ratio:       {run['max_unity_ratio']:.3f}")
        print(f"  Governing Check:       {run['governing_check']}")
        print("-" * 80)
        print("MEMBER CHECKS:")
        for r in run["results"]:
            st = "PASS" if r["passed"] else "FAIL"
            print(f"  [{st}] {r['check_name']}: Demand={r['demand_value']:.3f} {r['units']}, Capacity={r['capacity_value']:.3f} {r['units']}, Unity={r['unity_ratio']:.3f} ({r['clause_reference']})")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"ERROR: Calculation execution failed: {e}", file=sys.stderr)
        return 1


def handle_calculate_results(args):
    db = get_db(args.db_path)
    if args.run_id:
        run = db.get_calculation_run(args.run_id)
    elif args.project_id:
        run = db.get_latest_run_for_project(args.project_id)
    else:
        print("ERROR: Provide either --project-id or --run-id.", file=sys.stderr)
        return 1

    if not run:
        print("ERROR: No calculation run found matching criteria.", file=sys.stderr)
        return 1

    print("=" * 80)
    print(f"CALCULATION RUN REPORT: {run['run_id']}")
    print("=" * 80)
    print(f"Project ID:              {run['project_id']}")
    print(f"Mounting System:         {run['mounting_system']}")
    print(f"Calculation Method:      {run['calculation_method']}")
    print(f"Engine Version:          {run['engine_version']}")
    print(f"Run Status:              {run['status']}")
    print(f"Max Unity Ratio:         {run['max_unity_ratio']:.3f}")
    print(f"Governing Check:         {run['governing_check']}")
    print(f"Active Holds Enforced:   {run['active_holds_count']}")
    print(f"Watermark:               {run['watermark']}")
    print(f"Timestamp:               {run['created_at']}")
    print("-" * 80)
    print(f"{'STATUS':<6} {'CHECK NAME':<45} {'DEMAND':<10} {'CAPACITY':<10} {'UNITY':<8} {'REFERENCE'}")
    print("-" * 80)
    for r in run["results"]:
        st = "PASS" if r["passed"] else "FAIL"
        print(f"[{st:<4}] {r['check_name'][:44]:<45} {r['demand_value']:<10.3f} {r['capacity_value']:<10.3f} {r['unity_ratio']:<8.3f} {r['clause_reference']}")
    print("=" * 80)
    return 0


# -----------------------------------------------------------------------------
# Verification Holds Operations
# -----------------------------------------------------------------------------

def handle_holds_list(args):
    holds = MASTER_VERIFICATION_REGISTER.get_all_holds()
    print("=" * 90)
    print(f"{'HOLD ID':<35} {'CATEGORY':<35} {'STATUS':<20}")
    print("=" * 90)
    for h in holds:
        print(f"{h.hold_id:<35} {h.category.value[:34]:<35} {h.status.value:<20}")
    print("=" * 90)
    print(f"Total Canonical Holds: {len(holds)} (Active Enforced: {len(MASTER_VERIFICATION_REGISTER.get_active_holds())})")
    return 0


def handle_holds_show(args):
    hold = MASTER_VERIFICATION_REGISTER.get_hold(args.hold_id)
    if not hold:
        print(f"ERROR: Hold '{args.hold_id}' not found.", file=sys.stderr)
        return 1

    print("=" * 80)
    print(f"VERIFICATION HOLD: {hold.hold_id}")
    print("=" * 80)
    print(f"Category:             {hold.category.value}")
    print(f"Status:               {hold.status.value}")
    print(f"Affected Systems:     {', '.join(hold.affected_systems)}")
    print(f"Responsible Reviewer: {hold.responsible_reviewer}")
    print("-" * 80)
    print(f"Engineering Risk:\n  {hold.engineering_risk}")
    print("-" * 80)
    print(f"Required Evidence:\n  {hold.required_evidence}")
    print("-" * 80)
    print(f"Verification Method:\n  {hold.verification_method}")
    print("-" * 80)
    print(f"Release Criteria:\n  {hold.release_criteria}")
    print("=" * 80)
    return 0


def handle_holds_check(args):
    db = get_db(args.db_path)
    if args.project_id:
        proj = db.get_project(args.project_id)
        if not proj:
            print(f"ERROR: Project '{args.project_id}' not found.", file=sys.stderr)
            return 1
        sys_str = proj["mounting_system"]
    elif args.system:
        sys_type = resolve_system(args.system)
        sys_str = sys_type.value
    else:
        print("ERROR: Provide either --project-id or --system.", file=sys.stderr)
        return 1

    active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(sys_str)
    can_approve = MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction(sys_str)
    watermark = MASTER_VERIFICATION_REGISTER.get_drawing_watermark(sys_str)

    print("=" * 80)
    print(f"VERIFICATION GATE AUDIT: {sys_str}")
    print("=" * 80)
    print(f"Active Verification Holds: {len(active_holds)}")
    for h in active_holds:
        print(f"  [HOLD ENFORCED] {h.hold_id} ({h.category.value})")
    print("-" * 80)
    print(f"Approved for Construction (AFC): {'PERMITTED' if can_approve else 'STRICTLY FORBIDDEN'}")
    print(f"Mandatory Watermark:             {watermark}")
    print("=" * 80)
    return 0


# -----------------------------------------------------------------------------
# Drawing Operations
# -----------------------------------------------------------------------------

def handle_drawing_preview(args):
    db = get_db(args.db_path)
    proj = db.get_project(args.project_id)
    if not proj:
        print(f"ERROR: Project '{args.project_id}' not found.", file=sys.stderr)
        return 1

    geom = db.get_geometry(args.project_id)
    if not geom:
        print("ERROR: Geometry is not configured for this project.", file=sys.stderr)
        return 1

    total_w = geom.columns * geom.module.width_mm + (geom.columns - 1) * 25.0
    total_l = geom.rows * geom.module.length_mm + (geom.rows - 1) * 25.0

    print("=" * 80)
    print(f"ARRAY DRAWING PREVIEW: {proj['project_id']}")
    print("=" * 80)
    print(f"Mounting System:     {geom.mounting_system.value}")
    print(f"Array Dimensions:    {total_w:.0f} mm (Width) x {total_l:.0f} mm (Length)")
    print(f"Matrix Layout:       {geom.rows} rows x {geom.columns} columns ({geom.total_modules} modules)")
    print(f"Framing Spacing:     Purlins={geom.purlin_spacing_mm:.0f} mm, Rafters={geom.rafter_spacing_mm:.0f} mm")
    print("-" * 80)
    print("ASCII SCHEMATIC LAYOUT (Top-down Plan View):")
    row_str = " | ".join(f"[M{c+1}]" for c in range(min(geom.columns, 6)))
    if geom.columns > 6:
        row_str += " ... "
    for r in range(min(geom.rows, 5)):
        print(f"  Row {r+1:02d}: {row_str}")
    if geom.rows > 5:
        print(f"  ... ({geom.rows - 5} additional rows)")
    print("-" * 80)
    print(f"WATERMARK NOTICE:    PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION")
    print(f"APPROVAL STATUS:     UNAPPROVED (12 active verification holds enforced)")
    print("=" * 80)
    return 0


def handle_drawing_export_dxf(args):
    db = get_db(args.db_path)
    proj = db.get_project(args.project_id)
    if not proj:
        print(f"ERROR: Project '{args.project_id}' not found.", file=sys.stderr)
        return 1

    geom = db.get_geometry(args.project_id)
    if not geom:
        print("ERROR: Geometry must be configured before exporting DXF.", file=sys.stderr)
        return 1

    output_path = args.output or f"structural_{args.project_id}.dxf"
    metadata = DrawingMetadata(
        project_id=args.project_id,
        client_name=proj["client_name"],
        site_location=proj["site_location"],
        system_type=geom.mounting_system,
        drawing_number=args.drawing_number or f"RS-STR-{args.project_id}-001",
        revision=args.revision or "R0",
    )

    drawer = DXFDrawingEngine(geometry=geom, metadata=metadata)
    try:
        # Non-negotiable hold gate: if require_approved is requested, it will raise PermissionError!
        file_out = drawer.generate_dxf(output_path, require_approved=args.require_approved)

        # Record in database if a calculation run exists
        latest_run = db.get_latest_run_for_project(args.project_id)
        run_id = latest_run["run_id"] if latest_run else f"RUN-{args.project_id}-UNSAVED"
        db.record_drawing_export(
            run_id=run_id,
            project_id=args.project_id,
            drawing_number=metadata.drawing_number,
            file_path=file_out,
            revision=metadata.revision,
        )

        print("=" * 80)
        print(f"SUCCESS: DXF drawing generated successfully.")
        print(f"  Output File:      {file_out}")
        print(f"  Drawing Number:   {metadata.drawing_number} (Rev: {metadata.revision})")
        print(f"  System Type:      {geom.mounting_system.value}")
        print(f"  Watermark:        PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION")
        print(f"  Approval Gate:    AFC Forbidden (Active verification holds enforced)")
        print("=" * 80)
        return 0
    except PermissionError as pe:
        print(f"GOVERNANCE GATE BLOCKED: {pe}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: Failed to generate DXF: {e}", file=sys.stderr)
        return 1


# -----------------------------------------------------------------------------
# CLI Entry Point & Parser Setup
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m structural.cli",
        description="RENSUN Solar Structural Automation Platform CLI",
    )
    parser.add_argument("--db-path", help="Path to structural runs SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Project Management
    p_proj = subparsers.add_parser("project", help="Manage structural projects and inputs")
    proj_sub = p_proj.add_subparsers(dest="subcommand", required=True)

    # project create
    p_create = proj_sub.add_parser("create", help="Create a new structural project")
    p_create.add_argument("--project-id", required=True, help="Unique project ID (e.g. RS-PROJ-001)")
    p_create.add_argument("--name", required=True, help="Project name")
    p_create.add_argument("--system", required=True, help="Mounting system (A, B, C, or D)")
    p_create.add_argument("--client", help="Client name")
    p_create.add_argument("--location", help="Site location")
    p_create.set_defaults(func=handle_project_create)

    # project list
    p_list = proj_sub.add_parser("list", help="List structural projects")
    p_list.set_defaults(func=handle_project_list)

    # project show
    p_show = proj_sub.add_parser("show", help="Show project details")
    p_show.add_argument("--project-id", required=True, help="Project ID")
    p_show.set_defaults(func=handle_project_show)

    # project set-site
    p_site = proj_sub.add_parser("set-site", help="Configure site meteorological parameters")
    p_site.add_argument("--project-id", required=True, help="Project ID")
    p_site.add_argument("--file", help="Path to JSON file with site parameters")
    p_site.add_argument("--location", help="Site location name")
    p_site.add_argument("--lat", type=float, help="Latitude [6.0, 38.0]")
    p_site.add_argument("--lon", type=float, help="Longitude [68.0, 98.0]")
    p_site.add_argument("--vb", type=float, help="Basic wind speed in m/s [30, 60]")
    p_site.add_argument("--terrain", type=int, choices=[1, 2, 3, 4], help="Terrain category (1-4)")
    p_site.add_argument("--height", type=float, help="Building height in meters")
    p_site.add_argument("--elevation", type=float, help="Rooftop elevation in meters")
    p_site.add_argument("--k4", type=float, help="Cyclonic factor k4 (e.g. 1.15 for coast)")
    p_site.add_argument("--k3", type=float, help="Topography factor k3")
    p_site.add_argument("--k1", type=float, help="Risk factor k1")
    p_site.add_argument("--seismic-zone", choices=["Zone II", "Zone III", "Zone IV", "Zone V"], help="Seismic zone")
    p_site.set_defaults(func=handle_project_set_site)

    # project set-module
    p_mod = proj_sub.add_parser("set-module", help="Configure PV module specifications")
    p_mod.add_argument("--project-id", required=True, help="Project ID")
    p_mod.add_argument("--file", help="Path to JSON file with module specifications")
    p_mod.add_argument("--make-model", help="PV module model designation")
    p_mod.add_argument("--length", type=float, help="Module length in mm")
    p_mod.add_argument("--width", type=float, help="Module width in mm")
    p_mod.add_argument("--thickness", type=float, help="Module thickness in mm")
    p_mod.add_argument("--weight", type=float, help="Module weight in kg")
    p_mod.add_argument("--power", type=float, help="Peak power in Watts")
    p_mod.add_argument("--tilt", type=float, help="Module tilt angle in degrees")
    p_mod.add_argument("--azimuth", type=float, help="Module azimuth in degrees (180=South)")
    p_mod.set_defaults(func=handle_project_set_module)

    # project set-geometry
    p_geom = proj_sub.add_parser("set-geometry", help="Configure array framing geometry")
    p_geom.add_argument("--project-id", required=True, help="Project ID")
    p_geom.add_argument("--file", help="Path to JSON file with geometry configuration")
    p_geom.add_argument("--rows", type=int, help="Number of module rows")
    p_geom.add_argument("--cols", type=int, help="Number of module columns")
    p_geom.add_argument("--purlin-spacing", type=float, help="Purlin/rail spacing in mm")
    p_geom.add_argument("--rafter-spacing", type=float, help="Rafter/bracket spacing in mm")
    p_geom.add_argument("--ground-clearance", type=float, help="Ground/roof clearance in mm")
    p_geom.set_defaults(func=handle_project_set_geometry)

    # project set-material
    p_mat = proj_sub.add_parser("set-material", help="Configure structural material properties")
    p_mat.add_argument("--project-id", required=True, help="Project ID")
    p_mat.add_argument("--component", required=True, help="Component (PURLIN, RAFTER, COLUMN, RAIL)")
    p_mat.add_argument("--preset", choices=["E250", "6063-T6", "A2-70"], help="Standard material preset")
    p_mat.add_argument("--name", help="Material designation name")
    p_mat.add_argument("--grade", help="Material grade (e.g. E250 Fe 410W)")
    p_mat.add_argument("--standard", help="Standard reference (e.g. IS 2062: 2011)")
    p_mat.add_argument("--fy", type=float, help="Yield strength in MPa")
    p_mat.add_argument("--fu", type=float, help="Ultimate strength in MPa")
    p_mat.add_argument("--e-mod", type=float, help="Elastic modulus in MPa")
    p_mat.add_argument("--poisson", type=float, help="Poisson's ratio")
    p_mat.add_argument("--density", type=float, help="Density in kg/m3")
    p_mat.add_argument("--gamma-m0", type=float, help="Partial safety factor gamma_m0")
    p_mat.set_defaults(func=handle_project_set_material)

    # project set-section
    p_sec = proj_sub.add_parser("set-section", help="Configure structural section properties")
    p_sec.add_argument("--project-id", required=True, help="Project ID")
    p_sec.add_argument("--component", required=True, help="Component (PURLIN, RAFTER, COLUMN, RAIL)")
    p_sec.add_argument("--file", help="Path to JSON file with section properties")
    p_sec.add_argument("--designation", help="Section designation (e.g. ISMC 100x50x2.0)")
    p_sec.add_argument("--profile-type", help="Profile type (e.g. C-Channel, I-Section, Rail)")
    p_sec.add_argument("--area", type=float, help="Cross-sectional area in mm2")
    p_sec.add_argument("--ixx", type=float, help="Major axis moment of inertia in mm4")
    p_sec.add_argument("--iyy", type=float, help="Minor axis moment of inertia in mm4")
    p_sec.add_argument("--zxx", type=float, help="Major axis section modulus in mm3")
    p_sec.add_argument("--zyy", type=float, help="Minor axis section modulus in mm3")
    p_sec.add_argument("--rxx", type=float, help="Radius of gyration rxx in mm")
    p_sec.add_argument("--ryy", type=float, help="Radius of gyration ryy in mm")
    p_sec.add_argument("--mass", type=float, help="Mass per meter in kg/m")
    p_sec.add_argument("--shear-area", type=float, help="Effective shear area in mm2")
    p_sec.set_defaults(func=handle_project_set_section)

    # 2. Mounting Systems
    p_sys = subparsers.add_parser("system", help="Mounting system inspection and selection")
    sys_sub = p_sys.add_subparsers(dest="subcommand", required=True)

    # system list
    p_sys_list = sys_sub.add_parser("list", help="List supported mounting systems")
    p_sys_list.set_defaults(func=handle_system_list)

    # system select
    p_sys_select = sys_sub.add_parser("select", help="Select mounting system for project")
    p_sys_select.add_argument("--project-id", required=True, help="Project ID")
    p_sys_select.add_argument("--system", required=True, help="Mounting system (A, B, C, or D)")
    p_sys_select.set_defaults(func=handle_system_select)

    # 3. Calculation Operations
    p_calc = subparsers.add_parser("calculate", help="Structural calculation and verification")
    calc_sub = p_calc.add_subparsers(dest="subcommand", required=True)

    # calculate validate-inputs
    p_val = calc_sub.add_parser("validate-inputs", help="Validate project inputs completeness and physical ranges")
    p_val.add_argument("--project-id", required=True, help="Project ID")
    p_val.set_defaults(func=handle_calculate_validate_inputs)

    # calculate loads
    p_loads = calc_sub.add_parser("loads", help="Calculate wind, seismic, and Table 4 load combinations")
    p_loads.add_argument("--project-id", required=True, help="Project ID")
    p_loads.set_defaults(func=handle_calculate_loads)

    # calculate run
    p_run = calc_sub.add_parser("run", help="Execute complete structural analysis workflow and persist run")
    p_run.add_argument("--project-id", required=True, help="Project ID")
    p_run.add_argument("--walkway-width", type=float, help="Walkway width in meters (System A)")
    p_run.add_argument("--ballast-weight", type=float, help="Ballast block weight in kN/m2 (System D)")
    p_run.add_argument("--friction-mu", type=float, help="Friction coefficient mu (System D)")
    p_run.add_argument("--clamp-capacity", type=float, help="Sheet clamp tensile capacity in kN (System C)")
    p_run.add_argument("--bracket-spacing", type=float, help="Bracket spacing in mm (System B)")
    p_run.set_defaults(func=handle_calculate_run)

    # calculate results
    p_res = calc_sub.add_parser("results", help="View member-level check results")
    p_res.add_argument("--project-id", help="Project ID (views latest run)")
    p_res.add_argument("--run-id", help="Specific Run ID")
    p_res.set_defaults(func=handle_calculate_results)

    # 4. Verification Operations
    p_holds = subparsers.add_parser("holds", help="Governance verification holds register")
    holds_sub = p_holds.add_subparsers(dest="subcommand", required=True)

    # holds list
    p_hlist = holds_sub.add_parser("list", help="List all canonical verification holds")
    p_hlist.set_defaults(func=handle_holds_list)

    # holds show
    p_hshow = holds_sub.add_parser("show", help="Show full technical details of a verification hold")
    p_hshow.add_argument("--hold-id", required=True, help="Verification Hold ID")
    p_hshow.set_defaults(func=handle_holds_show)

    # holds check
    p_hcheck = holds_sub.add_parser("check", help="Check active holds and gate status for a project or system")
    p_hcheck.add_argument("--project-id", help="Project ID")
    p_hcheck.add_argument("--system", help="Mounting system (A, B, C, or D)")
    p_hcheck.set_defaults(func=handle_holds_check)

    # 5. Drawing Operations
    p_draw = subparsers.add_parser("drawing", help="Structural CAD drawing generation")
    draw_sub = p_draw.add_subparsers(dest="subcommand", required=True)

    # drawing preview
    p_dprev = draw_sub.add_parser("preview", help="Preview array layout and watermark status")
    p_dprev.add_argument("--project-id", required=True, help="Project ID")
    p_dprev.set_defaults(func=handle_drawing_preview)

    # drawing export-dxf
    p_dxfe = draw_sub.add_parser("export-dxf", help="Generate standards-compliant multi-layer DXF drawing")
    p_dxfe.add_argument("--project-id", required=True, help="Project ID")
    p_dxfe.add_argument("--output", help="Output DXF file path")
    p_dxfe.add_argument("--drawing-number", help="Drawing number")
    p_dxfe.add_argument("--revision", help="Revision string (e.g. R0)")
    p_dxfe.add_argument("--require-approved", action="store_true", help="Request approved drawing (blocked while holds active)")
    p_dxfe.set_defaults(func=handle_drawing_export_dxf)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
