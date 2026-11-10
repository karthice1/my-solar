"""
Verification Hold Register & Governance Gate Architecture
Package: structural.holds

Preserves all 12 original canonical verification holds with immutable identifiers.
Provides both human-readable and machine-readable data structures for gate enforcement.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Set
import json


class HoldCategory(str, Enum):
    STATUTORY_REQUIREMENT = "Statutory Requirement"
    PROJECT_ENGINEERING_PREREQUISITE = "Project Engineering Prerequisite"
    INTERNAL_QUALITY_CONTROL_REQUIREMENT = "Internal Quality-Control Requirement"
    PROFESSIONAL_APPROVAL_REQUIREMENT = "Professional Approval Requirement"


class HoldStatus(str, Enum):
    ACTIVE_ENFORCED = "ACTIVE / ENFORCED"
    BLOCKED_PENDING_EVIDENCE = "BLOCKED PENDING EVIDENCE"
    RELEASED_WITH_CERTIFICATE = "RELEASED WITH SIGNED CERTIFICATE"


CANONICAL_SYSTEM_TOKENS = {
    "SYSTEM_A": {
        "A",
        "SYSTEM A",
        "SYSTEM_A",
        "SYSTEM A: ELEVATED STEEL CANOPY",
        "ELEVATED STEEL CANOPY",
    },
    "SYSTEM_B": {
        "B",
        "SYSTEM B",
        "SYSTEM_B",
        "SYSTEM B: LOW-HEIGHT ALUMINIUM RAIL",
        "LOW-HEIGHT ALUMINIUM RAIL",
    },
    "SYSTEM_C": {
        "C",
        "SYSTEM C",
        "SYSTEM_C",
        "SYSTEM C: METAL-SHEET ROOF MOUNTING",
        "METAL-SHEET ROOF MOUNTING",
    },
    "SYSTEM_D": {
        "D",
        "SYSTEM D",
        "SYSTEM_D",
        "SYSTEM D: BALLASTED NON-PENETRATING SYSTEM",
        "BALLASTED NON-PENETRATING SYSTEM",
    },
}


def resolve_system_token(system_input: str) -> Optional[str]:
    """
    Deterministically resolves a mounting system string or enum to its canonical token:
    'SYSTEM_A', 'SYSTEM_B', 'SYSTEM_C', or 'SYSTEM_D'.
    Strictly rejects partial substrings, prefixes, suffixes, empty, or unknown strings.
    """
    if not system_input or not isinstance(system_input, str):
        return None
    cleaned = system_input.strip().upper()
    for token, aliases in CANONICAL_SYSTEM_TOKENS.items():
        if cleaned == token or cleaned in aliases:
            return token
    return None


@dataclass
class HoldRecord:
    hold_id: str
    category: HoldCategory
    engineering_risk: str
    affected_systems: List[str]  # e.g. ["System A", "System B", "System C", "System D"]
    required_evidence: str
    verification_method: str
    responsible_reviewer: str
    release_criteria: str
    title: str = ""
    standard: str = "Reference pending verification"
    description: str = ""
    status: HoldStatus = HoldStatus.ACTIVE_ENFORCED
    applicability_rationale: Dict[str, str] = field(default_factory=dict)

    def is_active(self) -> bool:
        return self.status != HoldStatus.RELEASED_WITH_CERTIFICATE

    def applies_to(self, system_name: str) -> bool:
        """
        Determines deterministic applicability of this verification hold to a mounting system.
        Replaces ambiguous substring matching with exact canonical token resolution.
        Rejects partial, prefix, suffix, or unrelated identifier matches.
        """
        target_token = resolve_system_token(system_name)
        if not target_token:
            return False
        affected_tokens = {resolve_system_token(s) for s in self.affected_systems}
        affected_tokens.discard(None)
        return target_token in affected_tokens

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["category"] = self.category.value
        d["status"] = self.status.value
        if not d.get("standard") or str(d.get("standard")).strip() == "":
            d["standard"] = "Reference pending verification"
        if not d.get("title") or str(d.get("title")).strip() == "":
            d["title"] = self.hold_id.replace("_", " ").title()
        if not d.get("description") or str(d.get("description")).strip() == "":
            d["description"] = self.engineering_risk
        return d


class VerificationRegister:
    """
    Central Verification Register managing the 12 immutable canonical holds.
    Guarantees that no drawing or calculation can be marked APPROVED or FOR CONSTRUCTION
    while applicable verification holds remain active.
    """

    def __init__(self):
        self._holds: Dict[str, HoldRecord] = {}
        self._initialize_canonical_holds()

    def _initialize_canonical_holds(self):
        # 1. INSPECTION_REQUIRED_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="INSPECTION_REQUIRED_HOLD",
                category=HoldCategory.PROFESSIONAL_APPROVAL_REQUIREMENT,
                title="Host Building Structural Adequacy & Physical Inspection",
                standard="TNCDBR-2019 Rule 35 / IS 13311 (NDT) / IS 456:2000",
                description="Verifies existing RCC slab, column framing, and structural adequacy before adding solar canopy/stanchion reactions.",
                engineering_risk=(
                    "Parent building structural failure, slab punching shear under concentrated stanchion reactions, "
                    "or hidden concrete distress caused by unaccounted array dead and wind loads."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Signed physical structural inspection report, crack mapping, and NDT rebound hammer/UPV logs.",
                verification_method="Visual inspection, non-destructive testing (IS 13311), and slab structural integrity certification.",
                responsible_reviewer="Registered Structural Engineer (RSE Grade-I / Grade-II under TNCDBR-2019 Rule 35).",
                release_criteria="Written certification that existing RCC slab/columns have structural reserve capacity for solar reactions.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "High concentrated moment and shear reactions at stanchion anchorages require verification of slab/column load paths.",
                    "System B": "Anchor penetrations into RCC roof require verification of rebar cover and water-tightness integrity.",
                    "System C": "Rooftop purlin and sheet capacity require verification against added module uplift and downward load.",
                    "System D": "Concentrated dead weight of concrete ballast blocks requires verification against host slab bending and shear capacity.",
                },
            )
        )

        # 2. AERODYNAMIC_UNSUPPORTED_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="AERODYNAMIC_UNSUPPORTED_HOLD",
                category=HoldCategory.PROJECT_ENGINEERING_PREREQUISITE,
                title="Aerodynamic Wind Tunnel & CFD Pressure Calibration",
                standard="IS 875 (Part 3): 2015 Clause 8.3 / ASCE 49-21 / SEAOC PV2",
                description="Validates local aerodynamic peak suction and shielding coefficients where array tilt or geometry exceeds codal tables.",
                engineering_risk=(
                    "Unpredicted wind suction, module tear-off, micro-turbulent parapet wake interactions, or multi-row "
                    "shielding effects not covered by simplified codal pressure coefficients."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Boundary layer wind tunnel (BLWT) test report or peer-reviewed CFD matching full-scale array geometry.",
                verification_method="Comparative aerodynamic review against ASCE 7-16 Chapter 29, SEAOC PV2-2017, and IS 875 (Part 3) Table 8.",
                responsible_reviewer="Senior Wind / Aerodynamic Engineering Specialist.",
                release_criteria="Aerodynamic peak net pressure coefficient distribution verified across all wind approach azimuths.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Elevated canopies are governed by IS 875 (Part 3) Table 8 net pressure; wake turbulence requires BLWT if tilt > 15 deg.",
                    "System B": "Multi-row low-tilt array on rooftop requires verification of wind shielding reduction factors.",
                    "System C": "Flush-mounted panels on pitched metal roofs must verify pressure distribution near eaves and ridges.",
                    "System D": "Ballasted arrays depend critically on aerodynamic uplift coefficients to prevent blow-off without anchorage.",
                },
            )
        )

        # 3. WIND_COORD_UNVERIFIED_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="WIND_COORD_UNVERIFIED_HOLD",
                category=HoldCategory.PROJECT_ENGINEERING_PREREQUISITE,
                title="Geographic Coordinates & Regional Wind Zone Verification",
                standard="IS 875 (Part 3): 2015 Figure 1 & Annex A",
                description="Verifies site latitude, longitude, municipal boundary, and basic wind speed (Vb) against statutory wind contours.",
                engineering_risk=(
                    "Under-design of structural members due to incorrect basic wind speed (Vb) lookup or erroneous cyclonic "
                    "factor (k4) near administrative boundaries and coastal strips."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Official municipal survey records or verified geocoding report matching IS 875 (Part 3) Appendix A and Figure 1.",
                verification_method="Geospatial polygon boundary containment check and 5 km coastal buffer verification.",
                responsible_reviewer="Geotechnical / Engineering Systems Auditor.",
                release_criteria="Site coordinates resolved to official district boundary and cyclonic factor k4 correctly assigned.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Elevated canopy wind design speed governs column foundation design and flexure.",
                    "System B": "Rail design directly scales with velocity pressure qz.",
                    "System C": "Fastener tear-out capacity must resist peak regional wind speed.",
                    "System D": "Ballast weight calculation is quadratically sensitive to basic wind speed Vb.",
                },
            )
        )

        # 4. WIND_TRANSFORM_UNVERIFIED_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="WIND_TRANSFORM_UNVERIFIED_HOLD",
                category=HoldCategory.INTERNAL_QUALITY_CONTROL_REQUIREMENT,
                title="3D Wind Vector Transformation & Accidental Torsion Gate",
                standard="REFERENCE PENDING VERIFICATION",
                description="Ensures normal panel wind pressures are accurately resolved into 3D Cartesian frame with accidental torsion (e = 0.1b).",
                engineering_risk=(
                    "Incorrect transformation of normal module aerodynamic pressures into global Cartesian components, "
                    "or omission of accidental torsional moment resulting from non-coincident center of pressure."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Direction cosine transformation verification report and accidental torsion (e = 0.10*b) design checks.",
                verification_method="Analytical vector equilibrium check and cross-element force balance.",
                responsible_reviewer="Structural Engineering Software Lead.",
                release_criteria="Mathematically validated coordinate transformation engine with panel torsion checks implemented.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Canopy rafter biaxial bending and column torsion depend on accurate spatial component transformation.",
                    "System B": "Purlin and rail asymmetric torsion under yawed wind flow.",
                    "System C": "Sheet clamp eccentric shear and pull-out components.",
                    "System D": "Overturning moment about diagonal ballast footings under yawed wind.",
                },
            )
        )

        # 5. VERTICAL_SEISMIC_APPLICABILITY_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="VERTICAL_SEISMIC_APPLICABILITY_HOLD",
                category=HoldCategory.STATUTORY_REQUIREMENT,
                title="Vertical Seismic Screening & 24 Permutations Determination",
                standard="IS 1893 (Part 1): 2016 Clause 6.3.3.1 (Amd 2)",
                description="Screens the 7 statutory trigger conditions of IS 1893:2016 to determine if 24 spatial permutations apply.",
                engineering_risk=(
                    "Misapplication of vertical seismic combinations in low-seismicity zones or omission in triggered high-seismicity "
                    "zones leading to non-conservative uplift or unnecessary structural over-design."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Documented classification under IS 1893 (Part 1): 2016 Clause 6.3.3.1 (incorporating Amendment No. 2, Nov 2020).",
                verification_method="Codal trigger evaluation (Zone IV/V, span > 20 m, cantilever > 5 m) vs voluntary project conservatism.",
                responsible_reviewer="Senior Structural Reviewer.",
                release_criteria="Formal classification determining whether 24 spatial permutations are statutory or project-conservatism.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Elevated canopies in Zone IV/V or with large cantilevers require vertical seismic analysis (Cases 17-24).",
                    "System B": "Low-height rooftop rails in Zone II/III do not statutorily trigger vertical seismic unless requested.",
                    "System C": "Direct sheet mount in Zone II/III governed by 8 horizontal combinations under Clause 6.3.4.2.",
                    "System D": "Ballasted arrays require vertical seismic uplift check to ensure contact normal force Neff > 0.",
                },
            )
        )

        # 6. LOAD_COMBINATION_PROVISIONAL_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="LOAD_COMBINATION_PROVISIONAL_HOLD",
                category=HoldCategory.STATUTORY_REQUIREMENT,
                title="Limit State Load Combinations Dual-Gate Check",
                standard="IS 800: 2007 Table 4 / IS 1893: 2016 Clause 6.3.2.1",
                description="Verifies partial safety factors across all ULS/SLS rows including simultaneous array live and erection combinations.",
                engineering_risk=(
                    "Over-stress or catastrophic collapse caused by incorrect partial safety factors, invalid live-load accompanying factors, "
                    "or omission of the dedicated construction-stage erection combination."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Traceability matrix verifying all ULS and SLS combinations against IS 800: 2007 Table 4 (Page 29).",
                verification_method="Clause-by-clause automated combination audit distinguishing leading (1.5/1.2) vs accompanying (1.05/0.53) live loads.",
                responsible_reviewer="Lead Indian Structural Code Specialist.",
                release_criteria="Complete IS 800: 2007 Table 4 combination generator verified with dedicated erection row (1.2 DL + 1.2 ER).",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Primary rafters carry simultaneous array live load (ACT-IL-02) and walkway live load (ACT-IL-04).",
                    "System B": "Local rails governed by max(ACT-IL-01, ACT-IL-02); erection phase governed by ACT-ER-01.",
                    "System C": "Sheet fixings governed by wind uplift combinations (Row 2, 0.9 DL + 1.5 WL).",
                    "System D": "Sliding stability governed by Row 2 (0.9 DL + 1.5 WL) with adverse live load strictly zero.",
                },
            )
        )

        # 7. FRICTION_UNVERIFIED_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="FRICTION_UNVERIFIED_HOLD",
                category=HoldCategory.PROJECT_ENGINEERING_PREREQUISITE,
                title="Membrane Sliding Friction Testing & Calibration",
                standard="REFERENCE PENDING VERIFICATION",
                description="Requires certified static pull-slip friction testing on actual roof waterproofing membrane under dry and wet conditions.",
                engineering_risk=(
                    "Ballast array sliding across roof membrane during design wind gusts, tearing waterproofing, and severing "
                    "high-voltage DC cabling due to unverified friction coefficient."
                ),
                affected_systems=["System D"],
                required_evidence="Laboratory or in-situ pull/slip test report conducted in strict accordance with EN 1990:2002 Annex D.",
                verification_method="Statistical evaluation of 95% confidence characteristic and design friction coefficients (mu_d).",
                responsible_reviewer="Geotechnical & Materials Testing Laboratory Engineer.",
                release_criteria="Certified friction coefficient mu_d established for the specific contact interface under wet and dry conditions.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Not applicable — System A uses mechanical post-installed anchor bolts into host columns/slab.",
                    "System B": "Not applicable — System B uses mechanical anchors or roof penetration brackets.",
                    "System C": "Not applicable — System C uses standing-seam or purlin-anchored sheet clamps.",
                    "System D": "MANDATORY HOLD — System D relies exclusively on friction to resist horizontal wind shear forces.",
                },
            )
        )

        # 8. ALUMINIUM_DERIVATION_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="ALUMINIUM_DERIVATION_HOLD",
                category=HoldCategory.STATUTORY_REQUIREMENT,
                title="Aluminium Section Modulus & Coupon Tensile Testing",
                standard="IS 8147: 1976 / ASTM B221 / AA ADM",
                description="Validates custom extruded aluminium rail section modulus, plastic moment, and tensile coupon mechanical properties.",
                engineering_risk=(
                    "Premature buckling, flange distortion, web crippling, or connection failure of custom extruded aluminium "
                    "rail profiles designed without verified statutory formulation."
                ),
                affected_systems=["System B", "System C", "System D"],
                required_evidence="Section capacity derivation report matching IS 8147: 1976 or physical mechanical testing per ASTM B221.",
                verification_method="Independent section modulus calculation and coupon tensile testing (IS 1608 / ASTM E8).",
                responsible_reviewer="Metallurgical / Structural Materials Specialist.",
                release_criteria="Certified design moment (Md), shear (Vd), and web bearing (Pwb) capacities per IS 8147.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Structural canopy members are hot-rolled/hollow structural steel (IS 800), not aluminium rails.",
                    "System B": "Primary mounting rails and splice connections are extruded aluminium (6063-T6 / 6005-T5).",
                    "System C": "Short-rail or continuous rail attachments are extruded aluminium profiles.",
                    "System D": "Ballast chassis and mounting rails are extruded aluminium profiles.",
                },
            )
        )

        # 9. FASTENER_TORQUE_UNVERIFIED_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="FASTENER_TORQUE_UNVERIFIED_HOLD",
                category=HoldCategory.INTERNAL_QUALITY_CONTROL_REQUIREMENT,
                title="Fastener Installation Torque & Clamping Integrity",
                standard="IS 1367 / ISO 3506 (Grade A2-70 / A4-70)",
                description="Requires calibrated torque-wrench procedures and clamp slip-resistance curves for stainless steel module clamps.",
                engineering_risk=(
                    "Module dislodgement, clamp slippage, or bolt fatigue rupture under cyclical thermal expansion and dynamic "
                    "wind buffeting caused by improper fastener torque specification."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Manufacturer-certified torque-tension test curves for stainless steel (A2/A4-70) module clamps.",
                verification_method="Calibrated torque-wrench validation and clamp slip-resistance testing.",
                responsible_reviewer="Quality Assurance / Connection Engineer.",
                release_criteria="Certified tightening torque table (Nm) specifying pretension force and anti-loosening hardware.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Module mid-clamps, end-clamps, and purlin-to-rafter bolt torque specifications.",
                    "System B": "Rail-to-bracket bolts and module clamp torque specifications.",
                    "System C": "Sheet seam clamp grub screws and module clamp torque specifications.",
                    "System D": "Chassis-to-ballast clamp bolts and module clamp torque specifications.",
                },
            )
        )

        # 10. NUMERICAL_INSTABILITY_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="NUMERICAL_INSTABILITY_HOLD",
                category=HoldCategory.INTERNAL_QUALITY_CONTROL_REQUIREMENT,
                title="FEA Solver Matrix Conditioning & Kinematic Mechanism Gate",
                standard="REFERENCE PENDING VERIFICATION",
                description="Audits stiffness matrix conditioning, suppresses unconstrained kinematic mechanisms, and checks convergence.",
                engineering_risk=(
                    "Undetected kinematic mechanisms, singular matrix pencils, ill-conditioned stiffness matrices (kappa > 10^8), "
                    "or erroneous modal frequencies leading to fictitious structural safety indices."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Multi-scale solver benchmark report comparing analytical closed-form solutions against OpenSees / OpenRadioss.",
                verification_method="Matrix condition number audit, rigid-body subspace suppression check, and MacNeal-Harder patch tests.",
                responsible_reviewer="Computational Mechanics & Numerical Methods Specialist.",
                release_criteria="Satisfactory completion of multi-scale solver validation benchmarks across all structural topologies.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "3D space frame rafter-column stability, lateral sway, and base fixity require matrix stability checks.",
                    "System B": "Multi-span continuous rail on flexible supports requires ill-conditioning checks.",
                    "System C": "Roof sheeting flexibility and clamp rotational stiffness modeling.",
                    "System D": "Non-linear contact and friction interface requires numerical convergence verification.",
                },
            )
        )

        # 11. ASSUMED_DATA_CERTIFICATION_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="ASSUMED_DATA_CERTIFICATION_HOLD",
                category=HoldCategory.PROFESSIONAL_APPROVAL_REQUIREMENT,
                title="Client Data & Host Building Assumption Sign-Off",
                standard="TNCDBR-2019 Annexure XVII / SEOR Assumption Sign-Off",
                description="Mandates formal sign-off on unmeasured host building dimensions, slab thickness, and assumed material strengths.",
                engineering_risk=(
                    "Design failure caused by reliance on uncertified customer inputs, assumed concrete grades, unverified slab thicknesses, "
                    "or unknown existing reinforcement layouts."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Signed client data certification form and verified as-built structural drawing records.",
                verification_method="Data provenance validation ensuring zero inputs are classified as unverified assumptions.",
                responsible_reviewer="Lead Project Structural Engineer.",
                release_criteria="All critical host building and site parameters verified with Level 1 (Measured) or Level 2 (Certified) provenance.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Host building column spacing, slab thickness, and concrete compressive strength must be certified.",
                    "System B": "Roof waterproofing membrane type and slab thickness must be certified.",
                    "System C": "Roof sheet gauge (BMT), profile, and purlin spacing must be certified.",
                    "System D": "Roof parapet height, surface roughness, and slab live-load reserve must be certified.",
                },
            )
        )

        # 12. DRAWING_UNVERIFIED_HOLD
        self.register_hold(
            HoldRecord(
                hold_id="DRAWING_UNVERIFIED_HOLD",
                category=HoldCategory.PROFESSIONAL_APPROVAL_REQUIREMENT,
                title="4-Gate Verification & Registered Structural Engineer Stamping",
                standard="TNCDBR-2019 Rule 38 / National Building Code (NBC 2016)",
                description="Enforces mandatory 4-gate verification across Prep, Check, RSE Approval, and Statutory Review before AFC issuance.",
                engineering_risk=(
                    "Issuance of preliminary automated drawings to contractors or fabricators without statutory Registered Structural "
                    "Engineer sign-off, violating TNCDBR-2019 legal licensing mandates."
                ),
                affected_systems=["System A", "System B", "System C", "System D"],
                required_evidence="Registered Structural Engineer (RSE) seal, signature, and structural stability certificate per TNCDBR-2019 Annexure XVII.",
                verification_method="Professional credential audit against CMDA / DTCP registration registers and peer review.",
                responsible_reviewer="Registered Structural Engineer (RSE Grade-I / Grade-II per Annexure XVII competence).",
                release_criteria="Formal RSE endorsement and issuance of AFC (Approved for Construction) structural drawing package.",
                status=HoldStatus.ACTIVE_ENFORCED,
                applicability_rationale={
                    "System A": "Mandatory RSE approval before any structural steel fabrication or foundation coring.",
                    "System B": "Mandatory RSE approval before rail installation.",
                    "System C": "Mandatory RSE approval before roof clamp fixing.",
                    "System D": "Mandatory RSE approval before ballast casting and placement.",
                },
            )
        )

    def register_hold(self, record: HoldRecord):
        self._holds[record.hold_id] = record

    def get_hold(self, hold_id: str) -> Optional[HoldRecord]:
        return self._holds.get(hold_id)

    def get_all_holds(self) -> List[HoldRecord]:
        return list(self._holds.values())

    def get_active_holds(self) -> List[HoldRecord]:
        return [h for h in self._holds.values() if h.is_active()]

    def get_active_holds_for_system(self, system_name: str) -> List[HoldRecord]:
        return [h for h in self._holds.values() if h.is_active() and h.applies_to(system_name)]

    def can_label_approved_for_construction(self, system_name: str) -> bool:
        """
        Non-negotiable safety gate: Returns True ONLY if ZERO active holds apply to this system.
        In Phase 1, all 12 holds are active, so this will ALWAYS return False.
        """
        active_holds = self.get_active_holds_for_system(system_name)
        return len(active_holds) == 0

    def get_drawing_watermark(self, system_name: str) -> str:
        """
        Returns mandatory preliminary watermark if any holds apply.
        """
        if not self.can_label_approved_for_construction(system_name):
            return "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION"
        return "APPROVED FOR CONSTRUCTION"

    def to_json(self, indent: int = 2) -> str:
        data = {h_id: h.to_dict() for h_id, h in self._holds.items()}
        return json.dumps(data, indent=indent)


# Global singleton instance
MASTER_VERIFICATION_REGISTER = VerificationRegister()
