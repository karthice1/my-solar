"""
Core Data Models for RENSUN Solar Structural Automation Platform
Package: structural.models

Strict SI units enforced:
- Length: mm (geometry) or m (site/meteorological)
- Force: N (internal force) or kN (external load)
- Stress: MPa (N/mm^2)
- Mass: kg
- Angle: degrees
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import math


class MountingSystemType(str, Enum):
    SYSTEM_A_CANOPY = "System A: Elevated Steel Canopy"
    SYSTEM_B_ALUMINIUM_RAIL = "System B: Low-Height Aluminium Rail"
    SYSTEM_C_METAL_SHEET = "System C: Metal-Sheet Roof Mounting"
    SYSTEM_D_BALLASTED = "System D: Ballasted Non-Penetrating System"


class TerrainCategory(int, Enum):
    CATEGORY_1 = 1  # Exposed open terrain with few or no obstructions
    CATEGORY_2 = 2  # Open terrain with well-scattered obstructions (1.5 m to 10 m)
    CATEGORY_3 = 3  # Terrain with numerous closely spaced obstructions (suburban/industrial)
    CATEGORY_4 = 4  # Terrain with numerous large high-rise obstructions (city centres)


class SeismicZone(str, Enum):
    ZONE_II = "Zone II"   # Zone factor Z = 0.10
    ZONE_III = "Zone III" # Zone factor Z = 0.16
    ZONE_IV = "Zone IV"   # Zone factor Z = 0.24
    ZONE_V = "Zone V"     # Zone factor Z = 0.36


@dataclass
class SiteParameters:
    location_name: str
    latitude: float
    longitude: float
    basic_wind_speed_vb: float  # m/s (IS 875 Part 3 Figure 1)
    terrain_category: TerrainCategory
    building_height_m: float    # m
    rooftop_elevation_m: float  # m
    cyclonic_factor_k4: float = 1.0  # Clause 6.3.4 (1.15 for east coast structures)
    topography_factor_k3: float = 1.0 # Clause 6.3.3
    risk_coefficient_k1: float = 1.0  # Clause 6.3.1 (50-year return period)
    seismic_zone: SeismicZone = SeismicZone.ZONE_III
    importance_factor_I: float = 1.0  # IS 1893 Part 1 Table 8
    response_reduction_R: float = 4.0 # IS 1893 Part 1 Table 9 (OMRF = 4.0, SMRF = 5.0)
    soil_type: int = 2  # 1=Rock, 2=Medium, 3=Soft

    def __post_init__(self):
        # Validation of ranges
        if not (6.0 <= self.latitude <= 38.0):
            raise ValueError(f"Latitude {self.latitude} out of Indian subcontinent bounds [6.0, 38.0].")
        if not (68.0 <= self.longitude <= 98.0):
            raise ValueError(f"Longitude {self.longitude} out of Indian subcontinent bounds [68.0, 98.0].")
        if not (30.0 <= self.basic_wind_speed_vb <= 60.0):
            raise ValueError(f"Basic wind speed {self.basic_wind_speed_vb} m/s out of IS 875 bounds [33, 55].")
        if self.building_height_m <= 0:
            raise ValueError("Building height must be strictly positive.")

    @property
    def zone_factor_z(self) -> float:
        mapping = {
            SeismicZone.ZONE_II: 0.10,
            SeismicZone.ZONE_III: 0.16,
            SeismicZone.ZONE_IV: 0.24,
            SeismicZone.ZONE_V: 0.36,
        }
        return mapping[self.seismic_zone]

    @property
    def is_high_rise_parent_building(self) -> bool:
        """TNCDBR-2019 Rule 2(43) amended by G.O.(Ms.) No. 194: height exceeding 19.50 m."""
        return self.building_height_m > 19.50


@dataclass
class PVModuleSpecification:
    make_model: str
    length_mm: float
    width_mm: float
    thickness_mm: float
    weight_kg: float
    peak_power_w: float
    tilt_deg: float = 10.0
    azimuth_deg: float = 180.0  # Due south = 180 deg in northern hemisphere

    def __post_init__(self):
        if self.length_mm <= 0 or self.width_mm <= 0 or self.thickness_mm <= 0:
            raise ValueError("Module physical dimensions must be strictly positive.")
        if self.weight_kg <= 0:
            raise ValueError("Module weight must be strictly positive.")
        if not (0.0 <= self.tilt_deg <= 60.0):
            raise ValueError(f"Module tilt {self.tilt_deg} deg out of physical bounds [0, 60].")

    @property
    def area_m2(self) -> float:
        return (self.length_mm * self.width_mm) / 1.0e6

    @property
    def dead_load_kn_per_m2(self) -> float:
        """Module dead load per square meter of panel surface."""
        # 1 kg = 9.80665 N = 0.00980665 kN
        return (self.weight_kg * 9.80665 / 1000.0) / self.area_m2


@dataclass
class ArrayGeometry:
    mounting_system: MountingSystemType
    total_modules: int
    rows: int
    columns: int
    module: PVModuleSpecification
    orientation: str = "PORTRAIT"  # "PORTRAIT" or "LANDSCAPE"
    purlin_spacing_mm: float = 1200.0
    rafter_spacing_mm: float = 3000.0
    ground_clearance_mm: float = 800.0
    overhang_top_mm: float = 250.0
    overhang_bottom_mm: float = 250.0

    def __post_init__(self):
        if self.rows * self.columns != self.total_modules:
            raise ValueError(
                f"Module count mismatch: {self.rows} rows x {self.columns} cols != {self.total_modules} total."
            )
        if self.purlin_spacing_mm <= 0 or self.rafter_spacing_mm <= 0:
            raise ValueError("Framing member spacing must be strictly positive.")

    @property
    def total_capacity_kw(self) -> float:
        return (self.total_modules * self.module.peak_power_w) / 1000.0

    @property
    def total_module_area_m2(self) -> float:
        return self.total_modules * self.module.area_m2

    @property
    def total_module_dead_weight_kn(self) -> float:
        return self.total_modules * (self.module.weight_kg * 9.80665 / 1000.0)


@dataclass
class MaterialProperty:
    name: str
    grade: str
    elastic_modulus_mpa: float  # E (MPa)
    yield_strength_mpa: float   # fy (MPa)
    ultimate_strength_mpa: float # fu (MPa)
    density_kg_m3: float
    poisson_ratio: float
    standard_reference: str
    gamma_m0_override: Optional[float] = None
    gamma_m1_override: Optional[float] = None

    @property
    def gamma_m0(self) -> float:
        """Partial safety factor for yielding: 1.10 for steel (IS 800 Table 5), 1.25 for aluminium."""
        if self.gamma_m0_override is not None:
            return self.gamma_m0_override
        return 1.10

    @property
    def gamma_m1(self) -> float:
        """Partial safety factor for ultimate rupture: 1.25 for steel (IS 800 Table 5)."""
        if self.gamma_m1_override is not None:
            return self.gamma_m1_override
        return 1.25


# Canonical materials
STEEL_E250 = MaterialProperty(
    name="Structural Steel",
    grade="E250 Fe 410W",
    elastic_modulus_mpa=205000.0,
    yield_strength_mpa=250.0,
    ultimate_strength_mpa=410.0,
    density_kg_m3=7850.0,
    poisson_ratio=0.30,
    standard_reference="IS 2062: 2011",
    gamma_m0_override=1.10,
    gamma_m1_override=1.25,
)

STEEL_E350 = MaterialProperty(
    name="Structural Steel High Yield",
    grade="E350 Fe 490",
    elastic_modulus_mpa=205000.0,
    yield_strength_mpa=350.0,
    ultimate_strength_mpa=490.0,
    density_kg_m3=7850.0,
    poisson_ratio=0.30,
    standard_reference="IS 2062: 2011",
    gamma_m0_override=1.10,
    gamma_m1_override=1.25,
)

ALUMINIUM_6063_T6 = MaterialProperty(
    name="Extruded Aluminium Alloy",
    grade="6063-T6",
    elastic_modulus_mpa=69000.0,
    yield_strength_mpa=170.0,
    ultimate_strength_mpa=205.0,
    density_kg_m3=2700.0,
    poisson_ratio=0.33,
    standard_reference="IS 733 / IS 8147: 1976",
    gamma_m0_override=1.25,  # IS 8147 / Eurocode 9 yield factor for extruded aluminium
    gamma_m1_override=1.35,
)

STAINLESS_STEEL_A2_70 = MaterialProperty(
    name="Stainless Steel Fastener",
    grade="A2-70 (AISI 304)",
    elastic_modulus_mpa=193000.0,
    yield_strength_mpa=450.0,
    ultimate_strength_mpa=700.0,
    density_kg_m3=7900.0,
    poisson_ratio=0.30,
    standard_reference="ISO 3506-1: 2020",
)


@dataclass
class SectionProperty:
    designation: str
    profile_type: str
    material: MaterialProperty
    area_mm2: float
    Ixx_mm4: float
    Iyy_mm4: float
    Zxx_mm3: float
    Zyy_mm3: float
    rxx_mm: float
    ryy_mm: float
    mass_kg_m: float
    shear_area_mm2: Optional[float] = None

    @property
    def shear_area_effective_mm2(self) -> float:
        """Effective shear area for web shear calculation (IS 800 Clause 8.4.1)."""
        if self.shear_area_mm2 is not None:
            return self.shear_area_mm2
        return 0.50 * self.area_mm2

    @property
    def design_moment_capacity_major_kn_m(self) -> float:
        """Design bending resistance about major axis Md = (Z * fy) / gamma_m0 in kN*m."""
        # N*mm = 1e-6 kN*m
        return (self.Zxx_mm3 * self.material.yield_strength_mpa / self.material.gamma_m0) / 1.0e6

    @property
    def design_moment_capacity_minor_kn_m(self) -> float:
        """Design bending resistance about minor axis in kN*m."""
        return (self.Zyy_mm3 * self.material.yield_strength_mpa / self.material.gamma_m0) / 1.0e6

    @property
    def design_shear_capacity_major_kn(self) -> float:
        """Design shear resistance Vd = (Av * fy) / (sqrt(3) * gamma_m0) in kN per IS 800 Cl 8.4.1."""
        return (self.shear_area_effective_mm2 * self.material.yield_strength_mpa / (math.sqrt(3.0) * self.material.gamma_m0)) / 1000.0


@dataclass
class CalculationResult:
    check_name: str
    demand_value: float
    capacity_value: float
    unity_ratio: float
    units: str
    governing_combination: str
    passed: bool
    clause_reference: str
    notes: str = ""

    def summary_line(self) -> str:
        status_str = "PASS" if self.passed else "FAIL"
        return (
            f"[{status_str}] {self.check_name}: Demand={self.demand_value:.3f} {self.units}, "
            f"Capacity={self.capacity_value:.3f} {self.units}, Unity={self.unity_ratio:.3f} "
            f"({self.governing_combination} per {self.clause_reference})"
        )


@dataclass
class DrawingMetadata:
    project_id: str
    client_name: str
    site_location: str
    system_type: MountingSystemType
    drawing_number: str
    revision: str = "R0"
    date: str = "2026-11-06"
    sheet_format: str = "A3"
    watermark: str = "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION"
    is_approved_for_construction: bool = False
    active_holds_count: int = 12
