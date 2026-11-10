"""
RENSUN Solar Structural Automation Platform — Phase 1 Foundation
Package: structural

Authorised Scope:
- Phase 1A: Structural engineering architecture & data models
- Phase 1B: Independent calculation engine (strict SI units & traceability)
- Phase 1C: Four mounting-system workflows (Systems A, B, C, D)
- Phase 1D: DXF drawing generation foundation via ezdxf
- Phase 1E: Testing, validation & regression protection framework

Governance:
PHASE_0_GOVERNANCE_STATUS: CLOSED_WITH_RETAINED_ENGINEERING_HOLDS
PHASE_1_GOVERNANCE_STATUS: AUTHORISED_FOR_CONTROLLED_IMPLEMENTATION
"""

__version__ = "1.0.0-phase1-alpha"
__author__ = "RENSUN Solar Structural Engineering Automation Team"

from structural.models import (
    MountingSystemType,
    SiteParameters,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    CalculationResult,
    DrawingMetadata,
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
from structural.drawing import (
    DXFDrawingEngine,
)
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

__all__ = [
    "MountingSystemType",
    "SiteParameters",
    "PVModuleSpecification",
    "ArrayGeometry",
    "MaterialProperty",
    "SectionProperty",
    "CalculationResult",
    "DrawingMetadata",
    "HoldCategory",
    "HoldStatus",
    "HoldRecord",
    "VerificationRegister",
    "MASTER_VERIFICATION_REGISTER",
    "ActionRegister",
    "CombinationGenerator",
    "LoadCombination",
    "ProvenanceLevel",
    "ProvenanceRecord",
    "ProvenanceTracker",
    "StructuralCalculationEngine",
    "CalculationReport",
    "DXFDrawingEngine",
    "SurveyMethod",
    "CoordinateVerificationStatus",
    "ApprovalStatus",
    "SiteCoordinateRecord",
    "WindParameterCategory",
    "WindParameterItem",
    "WindVerificationRecord",
    "RoofType",
    "RoofConditionRating",
    "CorrosionLevel",
    "InputClassification",
    "RoofInspectionField",
    "RoofInspectionRegister",
    "SiteInputValidator",
]
