"""
Physical Load-Action Register & Codified Load Combination Generator
Package: structural.actions

Strictly implements:
- Physical Load Actions: ACT-DL-01, ACT-IL-01 to 04, ACT-ER-01, ACT-WL-UP, ACT-WL-DOWN, ACT-EQ-H, ACT-EQ-V
- BIS IS 800: 2007 Clause 5.3.3 Table 4 (Page 29)
- BIS IS 1893 (Part 1): 2016 Clauses 6.3.2.1, 6.3.3.1, 6.3.4.1, 6.3.4.2
- Rigorous action-key validation and zero silent factor conversion
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class ActionType(str, Enum):
    DEAD_LOAD = "Dead Load (DL)"
    IMPOSED_POINT = "ACT-IL-01: Technician Point Load (1.0 kN)"
    IMPOSED_DISTRIBUTED = "ACT-IL-02: Array Distributed Maintenance (0.75 kN/m2)"
    IMPOSED_ROOF = "ACT-IL-03: Host Roof Live Load (0.75 kN/m2)"
    IMPOSED_WALKWAY = "ACT-IL-04: Walkway Live Load (3.0 kN/m2)"
    ERECTION_LOAD = "ACT-ER-01: Construction Erection Load (1.0 kN/m2)"
    WIND_UPLIFT = "Wind Suction / Uplift (WL_up)"
    WIND_DOWNWARD = "Wind Pressure Downward (WL_down)"
    SEISMIC_HORIZONTAL = "Horizontal Earthquake (E_h)"
    SEISMIC_VERTICAL = "Vertical Earthquake (E_z)"


# Canonical registered action keys
CANONICAL_ACTION_KEYS: Set[str] = {
    "DL",
    "IL_lead",
    "IL_acc",
    "WL",
    "WL_up",
    "WL_down",
    "ER",
    "EX",
    "EY",
    "EZ",
    "EQ_H",
    "EQ_V",
}


@dataclass
class PhysicalAction:
    action_id: str
    name: str
    category: str
    nominal_value: float
    units: str
    governing_clause: str
    description: str
    applicable_systems: List[str] = field(default_factory=list)
    application_location: str = ""
    load_pattern: str = ""
    load_path_component: str = ""
    combination_behavior: str = "MUTUALLY_EXCLUSIVE_IMPOSED"
    engine_mapping_key: str = ""

    def validate(self) -> None:
        """Validates that action model attributes are fully specified."""
        if not self.action_id or not self.name:
            raise ValueError("Physical action must possess non-empty action_id and name.")
        if self.nominal_value <= 0:
            raise ValueError(f"Action {self.action_id} nominal value must be strictly positive.")
        if not self.units:
            raise ValueError(f"Action {self.action_id} must have specified engineering units.")


class ActionRegister:
    """Canonical registry of physical structural actions across Systems A, B, C, D."""

    ACT_DL_01 = PhysicalAction(
        action_id="ACT-DL-01",
        name="Dead Load (Self-Weight + PV Modules)",
        category="Permanent Action",
        nominal_value=0.15,  # Nominal default kN/m2 (varies with module/framing)
        units="kN/m2",
        governing_clause="IS 875 (Part 1): 1987 Clause 3.1 & IS 800 Table 4",
        description="Permanent gravity action of PV modules, purlins, rails, rafters, columns, and ballast blocks.",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System C: Metal-Sheet Roof Mounting", "System D: Ballasted Non-Penetrating System"],
        application_location="Complete structural array surface and framing members",
        load_pattern="Uniformly distributed gravity body force acting downward along Z-axis",
        load_path_component="Purlin -> Rafter -> Column / Clamp -> Roof -> Host Slab",
        combination_behavior="PERMANENT_DEAD",
        engine_mapping_key="DL",
    )

    ACT_IL_01 = PhysicalAction(
        action_id="ACT-IL-01",
        name="Maintenance Technician Point Load",
        category="Variable Imposed Load",
        nominal_value=1.0,
        units="kN",
        governing_clause="IS 875 (Part 2): 1987 Clause 4.1",
        description="1.0 kN point load placed at midspan or cantilever tip of purlins, rails, or walkway grating.",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System C: Metal-Sheet Roof Mounting", "System D: Ballasted Non-Penetrating System"],
        application_location="Midspan or critical cantilever point on secondary members",
        load_pattern="Single concentrated point load (0.1m x 0.1m contact)",
        load_path_component="Purlin / Rail flexure and shear",
        combination_behavior="MUTUALLY_EXCLUSIVE_IMPOSED",
        engine_mapping_key="IL_lead",
    )

    ACT_IL_02 = PhysicalAction(
        action_id="ACT-IL-02",
        name="Distributed Array Maintenance Load",
        category="Variable Imposed Load",
        nominal_value=0.75,
        units="kN/m2",
        governing_clause="IS 875 (Part 2): 1987 Table 2",
        description="0.75 kN/m2 distributed load across tilted PV surface (or reduced per slope).",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System C: Metal-Sheet Roof Mounting", "System D: Ballasted Non-Penetrating System"],
        application_location="Upper surface of PV modules and primary rafter tributary",
        load_pattern="Uniformly distributed live action on plan area",
        load_path_component="Module -> Rail -> Rafter / Footing",
        combination_behavior="MUTUALLY_EXCLUSIVE_IMPOSED",
        engine_mapping_key="IL_lead",
    )

    ACT_IL_03 = PhysicalAction(
        action_id="ACT-IL-03",
        name="Host Roof Live Load",
        category="Variable Imposed Load",
        nominal_value=0.75,
        units="kN/m2",
        governing_clause="IS 875 (Part 2): 1987 Table 1",
        description="0.75 kN/m2 live load on accessible parent building RCC slab.",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System D: Ballasted Non-Penetrating System"],
        application_location="Exposed host roof slab between and beneath canopy footings",
        load_pattern="Distributed floor live load on host building slab",
        load_path_component="Host Building RCC Slab / Columns",
        combination_behavior="ACCOMPANYING_IMPOSED",
        engine_mapping_key="IL_acc",
    )

    ACT_IL_04 = PhysicalAction(
        action_id="ACT-IL-04",
        name="Walkway & Inverter Platform Live Load",
        category="Variable Imposed Load",
        nominal_value=3.0,
        units="kN/m2",
        governing_clause="IS 875 (Part 2): 1987 Table 1 (Balconies/Walkways)",
        description="3.0 kN/m2 live load on elevated catwalks, cable trays, and inverter maintenance platforms.",
        applicable_systems=["System A: Elevated Steel Canopy"],
        application_location="Dedicated elevated maintenance catwalks and inverter platforms",
        load_pattern="Uniformly distributed live action along walkway corridor",
        load_path_component="Catwalk Grating -> Stringer Beam -> Main Rafter",
        combination_behavior="LEADING_OR_ACCOMPANYING",
        engine_mapping_key="IL_lead",
    )

    ACT_ER_01 = PhysicalAction(
        action_id="ACT-ER-01",
        name="Construction & Erection Transient Load",
        category="Temporary Construction Load",
        nominal_value=1.0,
        units="kN/m2",
        governing_clause="IS 800: 2007 Clause 5.3.3 Table 4 Row 4",
        description="1.0 kN/m2 construction stage loading during framing assembly and module hoisting.",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System C: Metal-Sheet Roof Mounting", "System D: Ballasted Non-Penetrating System"],
        application_location="Unclad bare structural framing members during erection stage",
        load_pattern="Distributed temporary staging and worker load",
        load_path_component="Bare Purlin / Rafter / Column assembly",
        combination_behavior="TRANSIENT_CONSTRUCTION",
        engine_mapping_key="ER",
    )

    ACT_WL_UP = PhysicalAction(
        action_id="ACT-WL-UP",
        name="Wind Uplift Aerodynamic Suction",
        category="Environmental Action",
        nominal_value=1.5,  # Reference value in kPa (computed dynamically by wind engine)
        units="kN/m2",
        governing_clause="IS 875 (Part 3): 2015 Clauses 6.3 & 7.2",
        description="Aerodynamic net uplift pressure normal to tilted PV array surface under design wind speed.",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System C: Metal-Sheet Roof Mounting", "System D: Ballasted Non-Penetrating System"],
        application_location="PV panel surface and overhang edges",
        load_pattern="Normal pressure suction vector directed outward/upward",
        load_path_component="Clamp -> Rail -> Purlin -> Rafter -> Column Baseplate / Ballast",
        combination_behavior="ENVIRONMENTAL_WIND",
        engine_mapping_key="WL_up",
    )

    ACT_WL_DOWN = PhysicalAction(
        action_id="ACT-WL-DOWN",
        name="Wind Downward Aerodynamic Pressure",
        category="Environmental Action",
        nominal_value=1.2,  # Reference value in kPa (computed dynamically by wind engine)
        units="kN/m2",
        governing_clause="IS 875 (Part 3): 2015 Clauses 6.3 & 7.2",
        description="Aerodynamic net downward pressure normal to tilted PV array surface under design wind speed.",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System C: Metal-Sheet Roof Mounting", "System D: Ballasted Non-Penetrating System"],
        application_location="PV panel surface and sheltered zones",
        load_pattern="Normal pressure vector directed downward onto PV surface",
        load_path_component="Module -> Rail -> Purlin -> Rafter -> Footing",
        combination_behavior="ENVIRONMENTAL_WIND",
        engine_mapping_key="WL_down",
    )

    ACT_EQ_H = PhysicalAction(
        action_id="ACT-EQ-H",
        name="Equivalent Static Horizontal Seismic Action",
        category="Environmental Action",
        nominal_value=0.5,  # Reference base shear in kN (computed dynamically by seismic engine)
        units="kN",
        governing_clause="IS 1893 (Part 1): 2016 Clause 6.4.2",
        description="Horizontal lateral earthquake force Ah * W acting at center of mass of the array.",
        applicable_systems=["System A: Elevated Steel Canopy", "System B: Low-Height Aluminium Rail", "System D: Ballasted Non-Penetrating System"],
        application_location="Center of mass of elevated array and structural members",
        load_pattern="Horizontal lateral inertial force along principal X and Y axes",
        load_path_component="Bracing -> Columns -> Base Anchor / Ballast Shear Friction",
        combination_behavior="ENVIRONMENTAL_SEISMIC",
        engine_mapping_key="EX",
    )

    ACT_EQ_V = PhysicalAction(
        action_id="ACT-EQ-V",
        name="Equivalent Static Vertical Seismic Action",
        category="Environmental Action",
        nominal_value=0.33,  # Reference vertical force (2/3 Ah * W)
        units="kN",
        governing_clause="IS 1893 (Part 1): 2016 Clause 6.4.5",
        description="Vertical earthquake force Av * W acting upward or downward along vertical Z-axis.",
        applicable_systems=["System A: Elevated Steel Canopy", "System D: Ballasted Non-Penetrating System"],
        application_location="Center of mass of array and cantilever members",
        load_pattern="Vertical inertial force (+/- Z direction)",
        load_path_component="Rafter -> Column Axial / Ballast Contact Normal",
        combination_behavior="ENVIRONMENTAL_SEISMIC",
        engine_mapping_key="EZ",
    )

    @classmethod
    def get_all_actions(cls) -> List[PhysicalAction]:
        return [
            cls.ACT_DL_01,
            cls.ACT_IL_01,
            cls.ACT_IL_02,
            cls.ACT_IL_03,
            cls.ACT_IL_04,
            cls.ACT_ER_01,
            cls.ACT_WL_UP,
            cls.ACT_WL_DOWN,
            cls.ACT_EQ_H,
            cls.ACT_EQ_V,
        ]

    @classmethod
    def get_action_by_id(cls, action_id: str) -> Optional[PhysicalAction]:
        for act in cls.get_all_actions():
            if act.action_id == action_id:
                return act
        return None


@dataclass
class LoadCombination:
    comb_id: str
    limit_state: str  # "ULS" or "SLS"
    name: str
    table_4_row: str
    factors: Dict[str, float]  # Canonical action factors
    formula_latex: str
    description: str
    leading_action: Optional[str] = None
    accompanying_actions: List[str] = field(default_factory=list)
    excluded_actions: List[str] = field(default_factory=list)
    applicability_conditions: str = ""
    is_provisional: bool = False

    def __post_init__(self):
        # Validate that factors do not contain unknown keys
        for key in self.factors.keys():
            if key not in CANONICAL_ACTION_KEYS:
                raise KeyError(f"Unknown action key '{key}' in combination '{self.comb_id}'. Must be in CANONICAL_ACTION_KEYS.")

    def get_factor(self, action_key: str, default: Optional[float] = None) -> float:
        """
        Retrieves factor for action key with canonical alias mapping and strict validation.
        Rejects unknown keys rather than silently returning 0.0 unless explicit default provided.
        """
        if action_key not in CANONICAL_ACTION_KEYS:
            if default is not None:
                return default
            raise KeyError(f"Action key '{action_key}' is not a registered canonical action key.")

        # Direct match in factors
        if action_key in self.factors:
            return self.factors[action_key]

        # Alias resolution for wind
        if action_key == "WL":
            # If asking for generic WL, return WL_up or WL_down if present
            if "WL_up" in self.factors:
                return self.factors["WL_up"]
            if "WL_down" in self.factors:
                return self.factors["WL_down"]
            return 0.0

        if action_key in ("WL_up", "WL_down") and "WL" in self.factors:
            return self.factors["WL"]

        # Alias resolution for seismic
        if action_key in ("EQ_H", "EX") and "EX" in self.factors:
            return self.factors["EX"]
        if action_key in ("EQ_V", "EZ") and "EZ" in self.factors:
            return self.factors["EZ"]

        # If explicitly excluded or absent from valid combination, factor is 0.0
        return 0.0


class CombinationGenerator:
    """
    Generates ULS and SLS load combinations in strict accordance with
    IS 800: 2007 Table 4 (Page 29) and IS 1893 (Part 1): 2016.
    """

    @classmethod
    def get_action_for_key(cls, key: str) -> Optional[PhysicalAction]:
        """Maps canonical combination action key to its primary PhysicalAction."""
        mapping = {
            "DL": ActionRegister.ACT_DL_01,
            "IL_lead": ActionRegister.ACT_IL_01,  # Leading imposed load: ACT-IL-01 point load (or leading distributed array live ACT-IL-02)
            "IL_acc": ActionRegister.ACT_IL_03,   # Accompanying imposed load: ACT-IL-03 host roof live (or walkway live ACT-IL-04)
            "ER": ActionRegister.ACT_ER_01,
            "WL": ActionRegister.ACT_WL_UP,       # Generic wind alias resolved to aerodynamic uplift action
            "WL_up": ActionRegister.ACT_WL_UP,
            "WL_down": ActionRegister.ACT_WL_DOWN,
            "EX": ActionRegister.ACT_EQ_H,
            "EY": ActionRegister.ACT_EQ_H,
            "EZ": ActionRegister.ACT_EQ_V,
            "EQ_H": ActionRegister.ACT_EQ_H,
            "EQ_V": ActionRegister.ACT_EQ_V,
        }
        return mapping.get(key)

    @classmethod
    def validate_combination_integrity(cls, comb: LoadCombination) -> Tuple[bool, List[str]]:
        """
        Validates that every factor key in a combination belongs to CANONICAL_ACTION_KEYS
        and maps to a registered physical action. Strictly rejects unknown or unmapped non-zero factors.
        """
        errors = []
        for k, factor in comb.factors.items():
            if k not in CANONICAL_ACTION_KEYS:
                errors.append(f"Combination {comb.comb_id} contains uncanonical key: '{k}'")
            action = cls.get_action_for_key(k)
            if action is None:
                errors.append(f"Combination {comb.comb_id} key '{k}' has no registered PhysicalAction.")
            if abs(factor) > 0 and action is None:
                errors.append(f"Combination {comb.comb_id} has non-zero factor for unmapped action key '{k}'.")
        return len(errors) == 0, errors

    @classmethod
    def generate_gravity_and_wind_combinations(cls) -> List[LoadCombination]:
        """
        Generates canonical ULS and SLS combinations with standardized wind keys.
        Supports both unified and directional wind keys with full exclusion logic.
        """
        combs = [
            # ULS-01: Table 4 Row 1 (Maximum Gravity)
            LoadCombination(
                comb_id="ULS-01",
                limit_state="ULS",
                name="Maximum Gravity (Leading Live)",
                table_4_row="Row 1 ($DL + IL + CL$)",
                factors={"DL": 1.5, "IL_lead": 1.5, "IL_acc": 1.05, "WL": 0.0, "WL_up": 0.0, "WL_down": 0.0, "ER": 0.0},
                formula_latex="1.5 DL + 1.5 IL_{lead} + 1.05 IL_{acc}",
                description="Governs primary rafter and purlin sagging flexure under full dead and live actions.",
                leading_action="IL_lead",
                accompanying_actions=["IL_acc"],
                excluded_actions=["WL_up", "WL_down", "ER", "EX", "EY", "EZ"],
                applicability_conditions="Dominant when gravity imposed loads exceed aerodynamic suction.",
            ),
            # ULS-02: Table 4 Row 2 (Wind Uplift / Stress Reversal)
            LoadCombination(
                comb_id="ULS-02",
                limit_state="ULS",
                name="Wind Uplift / Stress Reversal",
                table_4_row="Row 2 ($DL + WL/EL$)",
                factors={"DL": 0.9, "IL_lead": 0.0, "IL_acc": 0.0, "WL": 1.5, "WL_up": 1.5, "WL_down": 0.0, "ER": 0.0},
                formula_latex="0.9 DL + 1.5 WL_{up}",
                description="Governs anchor bolt tension, ballast sliding, and purlin flange uplift buckling.",
                leading_action="WL_up",
                accompanying_actions=[],
                excluded_actions=["IL_lead", "IL_acc", "WL_down", "ER", "EX", "EY", "EZ"],
                applicability_conditions="Strict zero adverse live load (IL=0); stabilizing dead load factor = 0.9.",
            ),
            # ULS-03: Table 4 Row 2 (Maximum Wind Downward)
            LoadCombination(
                comb_id="ULS-03",
                limit_state="ULS",
                name="Maximum Wind Downward",
                table_4_row="Row 2 ($DL + WL/EL$)",
                factors={"DL": 1.5, "IL_lead": 0.0, "IL_acc": 0.0, "WL": 1.5, "WL_up": 0.0, "WL_down": 1.5, "ER": 0.0},
                formula_latex="1.5 DL + 1.5 WL_{down}",
                description="Peak downward wind pressure combined with maximum dead load.",
                leading_action="WL_down",
                accompanying_actions=[],
                excluded_actions=["IL_lead", "IL_acc", "WL_up", "ER", "EX", "EY", "EZ"],
                applicability_conditions="High downward wind on sheltered or positive-pitch slopes.",
            ),
            # ULS-04: Table 4 Row 3b (Combined Wind-Leading)
            LoadCombination(
                comb_id="ULS-04",
                limit_state="ULS",
                name="Combined Wind Leading + Accompanying Live",
                table_4_row="Row 3b ($WL$ Leading)",
                factors={"DL": 1.2, "IL_lead": 0.0, "IL_acc": 0.53, "WL": 1.2, "WL_up": 0.0, "WL_down": 1.2, "ER": 0.0},
                formula_latex="1.2 DL + 1.2 WL_{down} + 0.53 IL_{acc}",
                description="Wind leading with accompanying live load factored at 0.53 per Table 4 Note 2.",
                leading_action="WL_down",
                accompanying_actions=["IL_acc"],
                excluded_actions=["WL_up", "ER", "EX", "EY", "EZ"],
                applicability_conditions="Wind downward leading with maintenance crew on structure.",
            ),
            # ULS-05: Table 4 Row 3a (Combined Live-Leading)
            LoadCombination(
                comb_id="ULS-05",
                limit_state="ULS",
                name="Combined Live Leading + Accompanying Wind",
                table_4_row="Row 3a ($IL$ Leading)",
                factors={"DL": 1.2, "IL_lead": 1.2, "IL_acc": 1.05, "WL": 0.6, "WL_up": 0.0, "WL_down": 0.6, "ER": 0.0},
                formula_latex="1.2 DL + 1.2 IL_{lead} + 1.05 IL_{acc} + 0.6 WL_{down}",
                description="Live load leading with accompanying wind factored at 0.6 per Table 4 Row 3a.",
                leading_action="IL_lead",
                accompanying_actions=["IL_acc", "WL_down"],
                excluded_actions=["WL_up", "ER", "EX", "EY", "EZ"],
                applicability_conditions="Full maintenance team with concurrent moderate wind pressure.",
            ),
            # ULS-06: Table 4 Row 4 (Construction Erection Phase)
            LoadCombination(
                comb_id="ULS-06",
                limit_state="ULS",
                name="Construction Erection Phase",
                table_4_row="Row 4 ($DL + ER$)",
                factors={"DL": 1.2, "IL_lead": 0.0, "IL_acc": 0.0, "WL": 0.0, "WL_up": 0.0, "WL_down": 0.0, "ER": 1.2},
                formula_latex="1.2 DL + 1.2 ER",
                description="Dedicated erection combination reconciling Note 1 with dedicated Row 4.",
                leading_action="ER",
                accompanying_actions=[],
                excluded_actions=["IL_lead", "IL_acc", "WL_up", "WL_down", "EX", "EY", "EZ"],
                applicability_conditions="Temporary construction stage prior to PV module clamping.",
            ),
            # SLS-01: Table 4 Row 1 (Gravity Serviceability Deflection)
            LoadCombination(
                comb_id="SLS-01",
                limit_state="SLS",
                name="Gravity Deflection",
                table_4_row="Row 1 ($DL + IL$)",
                factors={"DL": 1.0, "IL_lead": 1.0, "IL_acc": 1.0, "WL": 0.0, "WL_up": 0.0, "WL_down": 0.0, "ER": 0.0},
                formula_latex="1.0 DL + 1.0 IL",
                description="Checks member vertical deflection under service gravity load (delta <= L/250).",
                leading_action="IL_lead",
                accompanying_actions=["IL_acc"],
                excluded_actions=["WL_up", "WL_down", "ER", "EX", "EY", "EZ"],
                applicability_conditions="Unfactored serviceability deflection check under dead + live.",
            ),
            # SLS-02: Table 4 Row 2 (Wind Uplift Deflection)
            LoadCombination(
                comb_id="SLS-02",
                limit_state="SLS",
                name="Wind Uplift Deflection",
                table_4_row="Row 2 ($DL + WL$)",
                factors={"DL": 1.0, "IL_lead": 0.0, "IL_acc": 0.0, "WL": 1.0, "WL_up": 1.0, "WL_down": 0.0, "ER": 0.0},
                formula_latex="1.0 DL + 1.0 WL_{up}",
                description="Checks dynamic upward rail and cantilever deflection (delta <= L/200).",
                leading_action="WL_up",
                accompanying_actions=[],
                excluded_actions=["IL_lead", "IL_acc", "WL_down", "ER", "EX", "EY", "EZ"],
                applicability_conditions="Serviceability uplift deflection under unfactored wind.",
            ),
            # SLS-03: Table 4 Row 3 (Combined Wind + Live Deflection)
            LoadCombination(
                comb_id="SLS-03",
                limit_state="SLS",
                name="Combined Wind + Live Deflection",
                table_4_row="Row 3 ($DL + IL + WL$)",
                factors={"DL": 1.0, "IL_lead": 0.8, "IL_acc": 0.8, "WL": 0.8, "WL_up": 0.0, "WL_down": 0.8, "ER": 0.0},
                formula_latex="1.0 DL + 0.8 IL + 0.8 WL",
                description="Checks combined serviceability deflection under concurrent wind and live actions.",
                leading_action="WL_down",
                accompanying_actions=["IL_lead", "IL_acc"],
                excluded_actions=["WL_up", "ER", "EX", "EY", "EZ"],
                applicability_conditions="Concurrent serviceability deflection check.",
            ),
        ]
        return combs

    @classmethod
    def generate_seismic_combinations(cls, include_vertical: bool = True) -> List[LoadCombination]:
        """
        Reconstructs the complete codified seismic case matrix per IS 1893: 2016
        Clauses 6.3.2.1, 6.3.3.1, 6.3.4.1, 6.3.4.2 and IS 800: 2007 Table 4.

        When include_vertical=True:
        - 16 Horizontal-dominant combinations (Cases 01-16, r3 = 0.3 -> net 1.5 * 0.3 = 0.45 Ez)
          8 cases with 1.5 DL (gravity combined) + 8 cases with 0.9 DL (uplift reversal)
        - 8 Vertical-dominant combinations (Cases 17-24, r3 = 1.0 -> net 1.5 * 1.0 = 1.50 Ez)
          4 cases with 1.5 DL (downward dominant) + 4 cases with 0.9 DL (contact loss / uplift)
        Total: 24 comprehensive 3D combinations.

        When include_vertical=False:
        - 8 Horizontal-only combinations under Clause 6.3.4.2 (ULS-EQ-H01 to ULS-EQ-H08).
        """
        combs = []
        if not include_vertical:
            # 8 horizontal combinations under Clause 6.3.4.2
            for i, (sx, sy) in enumerate([(1, 0.3), (1, -0.3), (-1, 0.3), (-1, -0.3),
                                          (0.3, 1), (0.3, -1), (-0.3, 1), (-0.3, -1)], start=1):
                combs.append(
                    LoadCombination(
                        comb_id=f"ULS-EQ-H{i:02d}",
                        limit_state="ULS",
                        name=f"2D Seismic Horizontal ({sx:+.1f}EX, {sy:+.1f}EY)",
                        table_4_row="Row 2 ($DL + EL$)",
                        factors={"DL": 1.5, "EX": 1.5 * sx, "EY": 1.5 * sy, "EZ": 0.0},
                        formula_latex=f"1.5 DL {sx:+.1f}(1.5 EX) {sy:+.1f}(1.5 EY)",
                        description="Horizontal 2-component seismic combination per IS 1893 Cl 6.3.4.2.",
                        leading_action="EX" if abs(sx) >= abs(sy) else "EY",
                        accompanying_actions=["EY" if abs(sx) >= abs(sy) else "EX"],
                        excluded_actions=["EZ", "WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                        applicability_conditions="Structures where vertical ground motion is exempted.",
                        is_provisional=False,
                    )
                )
            return combs

        # ---------------------------------------------------------------------
        # Complete 24-Case 3D Seismic Matrix under IS 1893 Cl 6.3.4.1
        # ---------------------------------------------------------------------
        # Directional combination factors:
        # Group 1: EX dominant: (+/- 1.0 EX, +/- 0.3 EY, +/- 0.3 EZ)
        # Group 2: EY dominant: (+/- 0.3 EX, +/- 1.0 EY, +/- 0.3 EZ)
        # Group 3: EZ dominant: (+/- 0.3 EX, +/- 0.3 EY, +/- 1.0 EZ)

        # 1. Horizontal-Dominant Matrix (Cases 01 to 16, r3 = 0.3 -> net 0.45 Ez)
        # Cases 01-08: Gravity Combined (1.5 DL)
        # Cases 09-16: Stabilizing / Reversal (0.9 DL)
        h_patterns = [
            (1.0, 0.3, 0.3),   # Case 1 / 9
            (1.0, 0.3, -0.3),  # Case 2 / 10
            (1.0, -0.3, 0.3),  # Case 3 / 11
            (1.0, -0.3, -0.3), # Case 4 / 12
            (0.3, 1.0, 0.3),   # Case 5 / 13
            (0.3, 1.0, -0.3),  # Case 6 / 14
            (0.3, -1.0, 0.3),  # Case 7 / 15
            (0.3, -1.0, -0.3), # Case 8 / 16
        ]

        # Gravity Combined 1.5 DL
        for idx, (sx, sy, sz) in enumerate(h_patterns, start=1):
            comb_id = f"ULS-EQ-{idx:02d}"
            combs.append(
                LoadCombination(
                    comb_id=comb_id,
                    limit_state="ULS",
                    name=f"Seismic ({sx:+.1f}EX, {sy:+.1f}EY, {sz:+.1f}EZ) Gravity Combined (1.5 DL)",
                    table_4_row="Row 2 ($DL + EL$)",
                    factors={"DL": 1.5, "EX": round(1.5 * sx, 4), "EY": round(1.5 * sy, 4), "EZ": round(1.5 * sz, 4)},
                    formula_latex=f"1.5 DL {sx:+.1f}(1.5 EX) {sy:+.1f}(1.5 EY) {sz:+.1f}(0.45 EZ)",
                    description=f"Horizontal-dominant 3D seismic gravity combination (case {idx}, r3=0.3).",
                    leading_action="EX" if abs(sx) >= abs(sy) else "EY",
                    accompanying_actions=["EZ"],
                    excluded_actions=["WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                    applicability_conditions="Full structural dead load resisting lateral seismic inertial action.",
                    is_provisional=False,
                )
            )

        # Stabilizing Dead Load 0.9 DL (Reversal / Uplift)
        for idx, (sx, sy, sz) in enumerate(h_patterns, start=9):
            comb_id = f"ULS-EQ-{idx:02d}"
            combs.append(
                LoadCombination(
                    comb_id=comb_id,
                    limit_state="ULS",
                    name=f"Seismic ({sx:+.1f}EX, {sy:+.1f}EY, {sz:+.1f}EZ) Uplift Reversal (0.9 DL)",
                    table_4_row="Row 2 ($DL + EL$)",
                    factors={"DL": 0.9, "EX": round(1.5 * sx, 4), "EY": round(1.5 * sy, 4), "EZ": round(1.5 * sz, 4)},
                    formula_latex=f"0.9 DL {sx:+.1f}(1.5 EX) {sy:+.1f}(1.5 EY) {sz:+.1f}(0.45 EZ)",
                    description=f"Horizontal-dominant 3D seismic reversal combination with minimum 0.9 DL (case {idx}).",
                    leading_action="EX" if abs(sx) >= abs(sy) else "EY",
                    accompanying_actions=["EZ"],
                    excluded_actions=["WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                    applicability_conditions="Minimum stabilizing dead load checking overturning and uplift anchorage.",
                    is_provisional=False,
                )
            )

        # 2. Vertical-Dominant Matrix (Cases 17 to 24, r3 = 1.0 -> net 1.50 Ez)
        # Patterns with 1.0 EZ: (+/- 0.3 EX, +/- 0.3 EY, +/- 1.0 EZ)
        v_patterns = [
            (0.3, 0.3, 1.0),   # Case 17 (1.5 DL) / 21 (0.9 DL)
            (0.3, 0.3, -1.0),  # Case 18 (0.9 DL reversal / uplift)
            (-0.3, 0.3, 1.0),  # Case 19
            (-0.3, 0.3, -1.0), # Case 20
        ]

        # Case 17: Vertical Downward Dominant (1.5 DL + 1.5 EZ)
        combs.append(
            LoadCombination(
                comb_id="ULS-EQ-17",
                limit_state="ULS",
                name="Seismic (+0.3EX, +0.3EY, +1.0EZ) Vertical Downward Dominant",
                table_4_row="Row 2 ($DL + EL$)",
                factors={"DL": 1.5, "EX": 0.45, "EY": 0.45, "EZ": 1.5},
                formula_latex="1.5 DL + 0.45 EX + 0.45 EY + 1.5 EZ",
                description="Vertical-dominant peak downward compressive reaction (r3 = 1.0 per Cl 6.3.4.1).",
                leading_action="EZ",
                accompanying_actions=["EX", "EY"],
                excluded_actions=["WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                applicability_conditions="Maximum downward vertical ground shock on cantilever and transfer beams.",
                is_provisional=False,
            )
        )

        # Case 18: Vertical Uplift Dominant (0.9 DL - 1.5 EZ)
        combs.append(
            LoadCombination(
                comb_id="ULS-EQ-18",
                limit_state="ULS",
                name="Seismic (+0.3EX, +0.3EY, -1.0EZ) Vertical Uplift Dominant (Contact Loss Check)",
                table_4_row="Row 2 ($DL + EL$)",
                factors={"DL": 0.9, "EX": 0.45, "EY": 0.45, "EZ": -1.5},
                formula_latex="0.9 DL + 0.45 EX + 0.45 EY - 1.5 EZ",
                description="Vertical-dominant peak uplift combination. Contact loss occurs if 1.5 EZ >= 0.9 DL.",
                leading_action="EZ",
                accompanying_actions=["EX", "EY"],
                excluded_actions=["WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                applicability_conditions="Minimum vertical reaction checking ballast liftoff and anchor tension.",
                is_provisional=False,
            )
        )

        # Cases 19 & 20: Negative horizontal permutations with downward and uplift vertical
        combs.append(
            LoadCombination(
                comb_id="ULS-EQ-19",
                limit_state="ULS",
                name="Seismic (-0.3EX, +0.3EY, +1.0EZ) Vertical Downward Combined",
                table_4_row="Row 2 ($DL + EL$)",
                factors={"DL": 1.5, "EX": -0.45, "EY": 0.45, "EZ": 1.5},
                formula_latex="1.5 DL - 0.45 EX + 0.45 EY + 1.5 EZ",
                description="Vertical downward dominant with reversed X-axis horizontal action.",
                leading_action="EZ",
                accompanying_actions=["EX", "EY"],
                excluded_actions=["WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                applicability_conditions="Vertical shock with adverse diagonal lateral shear.",
                is_provisional=False,
            )
        )

        combs.append(
            LoadCombination(
                comb_id="ULS-EQ-20",
                limit_state="ULS",
                name="Seismic (-0.3EX, +0.3EY, -1.0EZ) Vertical Uplift Combined",
                table_4_row="Row 2 ($DL + EL$)",
                factors={"DL": 0.9, "EX": -0.45, "EY": 0.45, "EZ": -1.5},
                formula_latex="0.9 DL - 0.45 EX + 0.45 EY - 1.5 EZ",
                description="Vertical uplift dominant with reversed X-axis horizontal action.",
                leading_action="EZ",
                accompanying_actions=["EX", "EY"],
                excluded_actions=["WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                applicability_conditions="Uplift reversal with adverse diagonal lateral shear.",
                is_provisional=False,
            )
        )

        # Cases 21 to 24: Completing full 8-pattern vertical-dominant family
        v_ext_patterns = [
            ("ULS-EQ-21", 0.3, -0.3, 1.0, 1.5, "Downward with -EY"),
            ("ULS-EQ-22", 0.3, -0.3, -1.0, 0.9, "Uplift with -EY"),
            ("ULS-EQ-23", -0.3, -0.3, 1.0, 1.5, "Downward with -EX, -EY"),
            ("ULS-EQ-24", -0.3, -0.3, -1.0, 0.9, "Uplift with -EX, -EY"),
        ]
        for cid, sx, sy, sz, dl_fac, note in v_ext_patterns:
            combs.append(
                LoadCombination(
                    comb_id=cid,
                    limit_state="ULS",
                    name=f"Seismic ({sx:+.1f}EX, {sy:+.1f}EY, {sz:+.1f}EZ) Vertical {note}",
                    table_4_row="Row 2 ($DL + EL$)",
                    factors={"DL": dl_fac, "EX": round(1.5 * sx, 4), "EY": round(1.5 * sy, 4), "EZ": round(1.5 * sz, 4)},
                    formula_latex=f"{dl_fac:.1f} DL {sx:+.1f}(0.45 EX) {sy:+.1f}(0.45 EY) {sz:+.1f}(1.5 EZ)",
                    description=f"Vertical-dominant 3D seismic combination ({note}, r3=1.0 per Cl 6.3.4.1).",
                    leading_action="EZ",
                    accompanying_actions=["EX", "EY"],
                    excluded_actions=["WL_up", "WL_down", "IL_lead", "IL_acc", "ER"],
                    applicability_conditions="Directional permutation for vertical seismic ground motion.",
                    is_provisional=False,
                )
            )

        return combs
