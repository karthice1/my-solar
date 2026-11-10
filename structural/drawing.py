"""
DXF Drawing Generation Engine via ezdxf
Package: structural.drawing

Strictly implements:
- Core independent headless DXF generation via ezdxf
- Explicit drawing classification:
  * Preliminary module arrangement
  * Preliminary framing concept
  * Calculated structural layout
  * Independently reviewed engineering drawing
- Clear disclaimer labels for unverified structural details (connections, baseplates, anchors)
- Mandatory prominent preliminary watermark:
  "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION"
- Non-negotiable hold gate: Forbids marking any drawing as APPROVED or FOR CONSTRUCTION
  while applicable verification holds remain active.
"""

import os
from enum import Enum
from typing import Optional
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment

from structural.models import (
    MountingSystemType,
    ArrayGeometry,
    DrawingMetadata,
)
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
)


class DrawingClassification(str, Enum):
    PRELIMINARY_MODULE_ARRANGEMENT = "PRELIMINARY MODULE ARRANGEMENT"
    PRELIMINARY_FRAMING_CONCEPT = "PRELIMINARY FRAMING CONCEPT (NOT FOR CONSTRUCTION)"
    CALCULATED_STRUCTURAL_LAYOUT = "CALCULATED STRUCTURAL LAYOUT"
    INDEPENDENTLY_REVIEWED_DRAWING = "INDEPENDENTLY REVIEWED ENGINEERING DRAWING"


class DXFDrawingEngine:
    """Headless DXF generation engine producing standards-compliant structural layout drawings."""

    def __init__(
        self,
        geometry: ArrayGeometry,
        metadata: DrawingMetadata,
        classification: DrawingClassification = DrawingClassification.PRELIMINARY_FRAMING_CONCEPT,
    ):
        self.geometry = geometry
        self.metadata = metadata
        self.classification = classification

    def generate_dxf(self, output_path: str, require_approved: bool = False) -> str:
        """
        Creates a complete multi-layer DXF drawing file.
        Enforces preliminary watermark and hold status check.
        Raises PermissionError if require_approved=True or metadata.is_approved_for_construction=True
        while active holds remain enforced.
        """
        # Non-negotiable Governance Gate Check
        can_approve = MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction(
            self.geometry.mounting_system.value
        )
        active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(
            self.geometry.mounting_system.value
        )

        if (require_approved or self.metadata.is_approved_for_construction) and not can_approve:
            raise PermissionError(
                f"Cannot generate approved drawing: {len(active_holds)} active verification hold(s) remain "
                f"enforced for {self.geometry.mounting_system.value}! Preliminary watermark cannot be removed."
            )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        doc = ezdxf.new("R2010", setup=True)
        msp = doc.modelspace()

        # 1. Setup Layer Architecture
        layers = doc.layers
        layers.add("MODULES", color=4)          # Cyan
        layers.add("FRAMING_PURLINS", color=3)  # Green
        layers.add("FRAMING_RAFTERS", color=2)  # Yellow
        layers.add("COLUMNS_FOOTINGS", color=1) # Red
        layers.add("DIMENSIONS", color=7)       # White
        layers.add("TITLE_BLOCK", color=7)      # White
        layers.add("NOTES_BLOCK", color=7)      # White
        layers.add("WATERMARK", color=6)        # Magenta

        # 2. Draw Plan View of Module Array
        mod_len = self.geometry.module.length_mm
        mod_wid = self.geometry.module.width_mm
        rows = self.geometry.rows
        cols = self.geometry.columns
        gap_mm = 25.0

        origin_x = 1000.0
        origin_y = 1000.0

        for r in range(rows):
            for c in range(cols):
                x0 = origin_x + c * (mod_wid + gap_mm)
                y0 = origin_y + r * (mod_len + gap_mm)
                # Draw module rectangle
                points = [
                    (x0, y0),
                    (x0 + mod_wid, y0),
                    (x0 + mod_wid, y0 + mod_len),
                    (x0, y0 + mod_len),
                    (x0, y0),
                ]
                msp.add_lwpolyline(points, dxfattribs={"layer": "MODULES"})

        array_width_total = cols * mod_wid + (cols - 1) * gap_mm
        array_length_total = rows * mod_len + (rows - 1) * gap_mm

        # 3. Draw Framing Purlins / Rails underneath modules
        # Two rails per module row based on configured purlin spacing
        for r in range(rows):
            rail1_y = origin_y + r * (mod_len + gap_mm) + (0.25 * mod_len)
            rail2_y = origin_y + r * (mod_len + gap_mm) + (0.75 * mod_len)
            msp.add_line(
                (origin_x - 100.0, rail1_y),
                (origin_x + array_width_total + 100.0, rail1_y),
                dxfattribs={"layer": "FRAMING_PURLINS"},
            )
            msp.add_line(
                (origin_x - 100.0, rail2_y),
                (origin_x + array_width_total + 100.0, rail2_y),
                dxfattribs={"layer": "FRAMING_PURLINS"},
            )

        # Draw Primary Rafter / Stanchion lines if spacing configured
        rafter_sp = self.geometry.rafter_spacing_mm
        num_rafters = max(2, int(math.ceil(array_width_total / rafter_sp)) + 1)
        for i in range(num_rafters):
            rx = origin_x + min(i * rafter_sp, array_width_total)
            msp.add_line(
                (rx, origin_y - 150.0),
                (rx, origin_y + array_length_total + 150.0),
                dxfattribs={"layer": "FRAMING_RAFTERS"},
            )

        # 3b. Draw Linear Dimensions on DIMENSIONS layer
        dim_offset = 400.0
        # Horizontal width dimension below array
        dim_w_y = origin_y - dim_offset
        msp.add_line((origin_x, dim_w_y), (origin_x + array_width_total, dim_w_y), dxfattribs={"layer": "DIMENSIONS"})
        msp.add_line((origin_x, dim_w_y - 80.0), (origin_x, dim_w_y + 80.0), dxfattribs={"layer": "DIMENSIONS"})
        msp.add_line((origin_x + array_width_total, dim_w_y - 80.0), (origin_x + array_width_total, dim_w_y + 80.0), dxfattribs={"layer": "DIMENSIONS"})
        msp.add_text(
            f"OVERALL ARRAY WIDTH = {array_width_total:.0f} mm",
            dxfattribs={"layer": "DIMENSIONS", "height": 100.0},
        ).set_placement((origin_x + array_width_total / 2.0 - 600.0, dim_w_y - 140.0))

        # Vertical length dimension to left of array
        dim_l_x = origin_x - dim_offset
        msp.add_line((dim_l_x, origin_y), (dim_l_x, origin_y + array_length_total), dxfattribs={"layer": "DIMENSIONS"})
        msp.add_line((dim_l_x - 80.0, origin_y), (dim_l_x + 80.0, origin_y), dxfattribs={"layer": "DIMENSIONS"})
        msp.add_line((dim_l_x - 80.0, origin_y + array_length_total), (dim_l_x + 80.0, origin_y + array_length_total), dxfattribs={"layer": "DIMENSIONS"})
        msp.add_text(
            f"OVERALL ARRAY LENGTH = {array_length_total:.0f} mm",
            dxfattribs={"layer": "DIMENSIONS", "height": 100.0, "rotation": 90.0},
        ).set_placement((dim_l_x - 140.0, origin_y + array_length_total / 2.0 - 600.0))

        # Purlin & Rafter annotation dimension
        msp.add_text(
            f"PURLIN SPACING: {self.geometry.purlin_spacing_mm:.0f} mm | RAFTER SPACING: {self.geometry.rafter_spacing_mm:.0f} mm",
            dxfattribs={"layer": "DIMENSIONS", "height": 80.0},
        ).set_placement((origin_x, origin_y - dim_offset - 250.0))

        # 4. Draw Title Block Border (A3 Format: scaled)
        sheet_w = max(array_width_total + 4500.0, 11000.0)
        sheet_h = max(array_length_total + 4500.0, 8000.0)
        border_pts = [
            (0, 0),
            (sheet_w, 0),
            (sheet_w, sheet_h),
            (0, sheet_h),
            (0, 0),
        ]
        msp.add_lwpolyline(border_pts, dxfattribs={"layer": "TITLE_BLOCK"})

        # Engineering Notes Box (Left bottom)
        nb_w = 4500.0
        nb_h = 2200.0
        nb_x = 300.0
        nb_y = 200.0
        msp.add_lwpolyline([
            (nb_x, nb_y),
            (nb_x + nb_w, nb_y),
            (nb_x + nb_w, nb_y + nb_h),
            (nb_x, nb_y + nb_h),
            (nb_x, nb_y),
        ], dxfattribs={"layer": "NOTES_BLOCK"})

        note_size = 85.0
        msp.add_text("STATUTORY ENGINEERING NOTES & CAVEATS:", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size * 1.1}).set_placement((nb_x + 100.0, nb_y + nb_h - 130.0))
        msp.add_text("1. DRAWING TYPE: " + self.classification.value, dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 280.0))
        msp.add_text("2. STATUS: PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 430.0))
        msp.add_text("3. STRUCTURAL CONNECTIONS: NOT DEFINED / CONCEPTUAL SCHEMATIC ONLY", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 580.0))
        msp.add_text("4. BASEPLATES & ANCHORS: NOT VERIFIED / REQUIRES RSE SITE AUDIT", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 730.0))
        msp.add_text("5. GOVERNANCE: AFC STRICTLY LOCKED UNDER 12 CANONICAL VERIFICATION HOLDS", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 880.0))
        msp.add_text("6. FRAMING POSITIONS: SCHEMATIC INDICATIONS — NOT A SURVEYED LAYOUT", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 1030.0))
        msp.add_text("7. ROOF CLASHES: PENETRATIONS, VENTS, AND PARAPET SHADOWS NOT SURVEYED", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 1180.0))
        msp.add_text("8. DO NOT PROCURE, FABRICATE OR ERECT FROM THIS PRELIMINARY DRAWING", dxfattribs={"layer": "NOTES_BLOCK", "height": note_size}).set_placement((nb_x + 100.0, nb_y + nb_h - 1330.0))

        # Title Block Box in lower right corner
        tb_w = 4500.0
        tb_h = 2200.0
        tb_x = sheet_w - tb_w - 200.0
        tb_y = 200.0
        tb_box = [
            (tb_x, tb_y),
            (tb_x + tb_w, tb_y),
            (tb_x + tb_w, tb_y + tb_h),
            (tb_x, tb_y + tb_h),
            (tb_x, tb_y),
        ]
        msp.add_lwpolyline(tb_box, dxfattribs={"layer": "TITLE_BLOCK"})

        # Title Block Texts
        text_size = 110.0
        msp.add_text(
            f"PROJECT: {self.metadata.project_id}",
            dxfattribs={"layer": "TITLE_BLOCK", "height": text_size},
        ).set_placement((tb_x + 100.0, tb_y + tb_h - 200.0))
        msp.add_text(
            f"SYSTEM: {self.geometry.mounting_system.value}",
            dxfattribs={"layer": "TITLE_BLOCK", "height": text_size},
        ).set_placement((tb_x + 100.0, tb_y + tb_h - 400.0))
        msp.add_text(
            f"CLIENT: {self.metadata.client_name} | SITE: {self.metadata.site_location}",
            dxfattribs={"layer": "TITLE_BLOCK", "height": text_size},
        ).set_placement((tb_x + 100.0, tb_y + tb_h - 600.0))
        msp.add_text(
            f"DWG NO: {self.metadata.drawing_number}  REV: {self.metadata.revision}  DATE: {self.metadata.date}",
            dxfattribs={"layer": "TITLE_BLOCK", "height": text_size},
        ).set_placement((tb_x + 100.0, tb_y + tb_h - 800.0))
        msp.add_text(
            f"CLASSIFICATION: {self.classification.value}",
            dxfattribs={"layer": "TITLE_BLOCK", "height": text_size * 0.9},
        ).set_placement((tb_x + 100.0, tb_y + tb_h - 1000.0))

        # Check Active Holds Gate
        can_approve = MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction(
            self.geometry.mounting_system.value
        )
        status_label = "APPROVED FOR CONSTRUCTION" if can_approve else "STATUS: UNAPPROVED — ACTIVE HOLDS ENFORCED"
        msp.add_text(
            status_label,
            dxfattribs={"layer": "TITLE_BLOCK", "height": text_size * 1.05},
        ).set_placement((tb_x + 100.0, tb_y + tb_h - 1300.0))

        # 5. Mandatory Preliminary Watermark
        # Placed both inside the title block and stamped diagonally across the sheet
        watermark_text = MASTER_VERIFICATION_REGISTER.get_drawing_watermark(self.geometry.mounting_system.value)

        # In title block warning cell
        msp.add_text(
            watermark_text,
            dxfattribs={"layer": "WATERMARK", "height": text_size * 0.95},
        ).set_placement((tb_x + 100.0, tb_y + 150.0))

        # Diagonal watermark across the sheet
        wm_center_x = sheet_w / 2.0
        wm_center_y = sheet_h / 2.0
        msp.add_text(
            watermark_text,
            dxfattribs={
                "layer": "WATERMARK",
                "height": 450.0,
                "rotation": 30.0,
            },
        ).set_placement(
            (wm_center_x - 3000.0, wm_center_y - 1000.0),
            align=TextEntityAlignment.CENTER,
        )

        # Save DXF
        doc.saveas(output_path)
        return output_path
