# Copyright (C) 2026 Andrew Tyre
#
# This file is part of french_cleats.
#
# french_cleats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# french_cleats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with french_cleats.  If not, see <https://www.gnu.org/licenses/>.
import cadquery as cq
import argparse
import sys, os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH, BACKPLATE_THICKNESS, DEFAULT_RAIL_HEIGHT,
    create_baseplate, export_model
)

def create_claw_hammer_holder(
    units=2,
    rail_height=DEFAULT_RAIL_HEIGHT,
    head_dia=30.0,
    face_to_handle=59.0,
    handle_size=25.0,
    slot_width=40.0,
    slot_entrance_width=50.0,
    shelf_length=None,
    front_claw_lip=10.0,
    claw_elevation=8.0,
    shelf_thickness=5.0,
    shelf_drop=30.0,
    fillet_radius=4.0,
    fillet_to_dimple=1.0,
    divot_depth=3.0,
    divot_radius=None,
    web_thickness=5.0,
    gusset_bottom_offset=0.0
):
    """
    Creates a French Cleat claw hammer tool holder.
    
    The claw hammer rests with its head parallel to the Z-axis (pointing forward
    from the wall) and its handle extending downwards (-Y).
    The striking face rests at the rear (near the wall), while the claw extends
    towards the user (-Z in CAD coordinates).
    
    Key design features:
    1. Shortened rear shelf arm: The striking head dimple starts exactly ~5mm in front
       of the backplate face (1mm past the 4mm structural fillet), minimizing wall lever arm.
    2. Elevated claw support: The front shelf support arm is elevated UP by claw_elevation
       (default: 8.0mm) relative to the rear shelf arm. This compensates for the upward arch
       on the claw side of the hammer head, ensuring the hammer rests completely level
       instead of tilting backward.
    3. Thinned 5mm shelf: Shelf plate thickness is 5.0mm (2.0mm floor at the bottom of the 3.0mm
       dimple), saving material while retaining full rigidity.
    4. 30mm shelf drop: Lowering the shelf 30mm from the top places the top of the hammer head
       flush with the top edge of the holder, clears the top cleat mounting screws by 12mm,
       and maximizes vertical clearance and brace angle below.
    5. Matching cradles: Both the rear striking shelf and the elevated front claw platform
       feature 30mm diameter cylindrical cradle dimples to prevent side-to-side wobble.
    6. Rounded print-friendly edges: Generous 2.5mm fillets round off the top edges of the
       elevated claw block for printability and smooth tool insertion.
    7. Connection-agnostic tool holder: Uses standard groove backplate to mate with cleats
       and adapters.
    8. Support-free printing: Default right_down print orientation rests the flat left side
       coplanar on the print bed.
    """
    if divot_radius is None:
        divot_radius = head_dia / 2.0 + 0.5  # 15.5mm for 30mm dia head
        
    width = units * UNIT_WIDTH  # e.g. 2 * 28 = 56mm
    
    # 1. Baseplate (standard groove interface)
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        units=units, rail_height=rail_height, mount_type="groove", num_rows=2
    )
    
    # Coordinates in Z:
    # Z = 0 is wall (back of cleat)
    # Z = -BACKPLATE_THICKNESS (-11.0) is front face of baseplate
    back_z = -BACKPLATE_THICKNESS
    
    # Dimple starts exactly fillet_radius + fillet_to_dimple (default: 4.0 + 1.0 = 5.0mm)
    # in front of the backplate face:
    dimple_start_z = back_z - (fillet_radius + fillet_to_dimple)  # -16.0mm
    
    # Handle center position:
    z_handle = dimple_start_z - face_to_handle  # -64.0mm
    
    # Slot front boundary:
    z_slot_front = z_handle - (slot_width / 2.0)  # -77.0mm
    
    # Dynamic shelf depth if not explicitly specified:
    if shelf_length is None:
        shelf_length = abs(z_slot_front - front_claw_lip)  # 77.0 + 15.0 = 92.0mm
        
    front_z = -shelf_length
    shelf_extrude_dist = shelf_length - BACKPLATE_THICKNESS
    
    # Coordinates in Y:
    shelf_top_y = top_y - shelf_drop  # 20.0 - 30.0 = -10.0mm
    shelf_bot_y = shelf_top_y - shelf_thickness  # -15.0mm
    elev_top_y = shelf_top_y + claw_elevation  # -2.0mm
    
    shelf_pts = [
        (shelf_bot_y, back_z),
        (shelf_bot_y, front_z),
        (shelf_top_y, front_z),
        (shelf_top_y, back_z),
    ]
    elev_pts = [
        (shelf_top_y, z_slot_front),
        (shelf_top_y, front_z),
        (elev_top_y, front_z),
        (elev_top_y, z_slot_front),
    ]
    
    body = (
        body
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .end(2)
        .faces(">X")
        .workplane(centerOption="ProjectedOrigin")
        .tag("right_wp")
        .end(2)
        # 2. Main Shelf Block
        .workplaneFromTagged("right_wp")
        .polyline(shelf_pts)
        .close()
        .extrude(-width)
    )
    
    # 3. Structural Fillet at Backplate Junction
    try:
        body = (
            body
            .faces("-Z")
            .faces(">Z")
            .edges("|X")
            .edges("not >Y")
            .edges("not <Y")
            .fillet(fillet_radius)
        )
    except Exception:
        try:
            body = (
                body
                .faces("-Z")
                .faces(">Z")
                .edges("|X")
                .edges("not >Y")
                .edges("not <Y")
                .fillet(2.0)
            )
        except Exception:
            pass

    # 4. Elevated Claw Support Block (in front of handle slot)
    body = (
        body
        .workplaneFromTagged("right_wp")
        .polyline(elev_pts)
        .close()
        .extrude(-width)
    )
    
    # Round off top edges of elevated block (top-front and top-back) for printability & smooth seating
    try:
        body = (
            body
            .faces("+Y")
            .faces("not >Y")
            .faces(">Y")
            .edges("|X")
            .fillet(2.5)
        )
    except Exception:
        pass
        
    # 5. Slim 5mm Triangular Support Brace & 6. Parallel Triangular Cutout
    gusset_y_bottom = bottom_y + gusset_bottom_offset
    brace_pts = [
        (shelf_bot_y, back_z),
        (shelf_bot_y, front_z),
        (gusset_y_bottom, back_z),
    ]
    cutout_sketch = (
        cq.Sketch()
        .polygon(brace_pts)
        .wires()
        .offset(-10.0, mode="r")
        .reset()
        .vertices()
        .fillet(5.0)
    )
    
    # 7. Handle Slot Cutter (cuts through both elevated block and shelf)
    x_dimple = -6.0
    x_slot_back = -20.0  # Stops 3mm before left brace web (at X = -23.0)
    x_mouth = width / 2.0 + 5.0
    x_taper_start = 12.0
    
    w_half_mouth = slot_entrance_width / 2.0
    w_half_slot = slot_width / 2.0
    
    slot_poly_pts = [
        (z_handle - w_half_mouth, x_mouth),
        (z_handle - w_half_slot, x_taper_start),
        (z_handle - w_half_slot, x_slot_back),
        (z_handle + w_half_slot, x_slot_back),
        (z_handle + w_half_slot, x_taper_start),
        (z_handle + w_half_mouth, x_mouth),
    ]
    slot_sketch = cq.Sketch().polygon(slot_poly_pts).reset().vertices("<Y").fillet(5.0)
    slot_cutter_height = claw_elevation + shelf_thickness + 4.0

    # 8. Cylindrical Cradle Dimples
    divot_rear_y = (shelf_top_y - divot_depth) + divot_radius
    divot_rear_len = abs(z_handle - dimple_start_z) + 5.0
    divot_front_y = (elev_top_y - divot_depth) + divot_radius
    divot_front_len = abs(front_z - z_slot_front) + 4.0

    body = (
        body
        .workplaneFromTagged("right_wp")
        .workplane(offset=-width)
        .polyline(brace_pts)
        .close()
        .extrude(web_thickness)
        .workplaneFromTagged("right_wp")
        .workplane(offset=-width)
        .placeSketch(cutout_sketch)
        .cutBlind(web_thickness)
        .copyWorkplane(cq.Workplane("ZX", origin=(0, elev_top_y + 2.0, 0)))
        .placeSketch(slot_sketch)
        .cutBlind(-slot_cutter_height)
        .workplaneFromTagged("back_wp")
        .workplane(offset=dimple_start_z)
        .moveTo(x_dimple, divot_rear_y)
        .circle(divot_radius)
        .cutBlind(-divot_rear_len)
        .workplaneFromTagged("back_wp")
        .workplane(offset=z_slot_front + 2.0)
        .moveTo(x_dimple, divot_front_y)
        .circle(divot_radius)
        .cutBlind(-divot_front_len)
    )

    # 9. Screw Holes
    if screw_pts:
        body = (
            body
            .workplaneFromTagged("back_wp")
            .pushPoints(screw_pts)
            .hole(3.6, 20.0)
            .workplaneFromTagged("back_wp")
            .workplane(offset=-8.0)
            .pushPoints(screw_pts)
            .hole(8.0, 20.0)
        )
        
    return body

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate French Cleat Claw Hammer Tool Holder")
    parser.add_argument("--units", type=int, default=2, help="Width in units (default: 2, 56mm / ~2.2 in)")
    parser.add_argument("--rail-height", type=float, default=DEFAULT_RAIL_HEIGHT, help="Rail height in mm")
    parser.add_argument("--head-dia", type=float, default=30.0, help="Hammer striking head diameter in mm (default: 30mm)")
    parser.add_argument("--face-to-handle", type=float, default=59.0, help="Distance from striking face to handle center in mm (default: 59.0mm)")
    parser.add_argument("--handle-size", type=float, default=25.0, help="Hammer handle neck size in mm")
    parser.add_argument("--slot-width", type=float, default=40.0, help="Handle slot width/depth in mm (default: 40mm)")
    parser.add_argument("--slot-entrance-width", type=float, default=50.0, help="Entrance mouth width in mm (default: 50mm)")
    parser.add_argument("--shelf-length", type=float, default=None, help="Shelf depth from wall in mm (default: auto ~105mm)")
    parser.add_argument("--front-claw-lip", type=float, default=10.0, help="Front claw support platform length in mm (default: 10mm)")
    parser.add_argument("--claw-elevation", type=float, default=8.0, help="Height front claw platform is elevated above rear shelf in mm (default: 8mm)")
    parser.add_argument("--shelf-thickness", type=float, default=5.0, help="Shelf thickness in mm (default: 5.0mm, leaves 2.0mm at dimple floor)")
    parser.add_argument("--shelf-drop", type=float, default=30.0, help="Distance shelf is lowered below top of backplate (default: 30mm)")
    parser.add_argument("--fillet-radius", type=float, default=4.0, help="Structural fillet radius at backplate in mm (default: 4mm)")
    parser.add_argument("--fillet-to-dimple", type=float, default=1.0, help="Clearance between fillet end and head dimple in mm (default: 1mm)")
    parser.add_argument("--divot-depth", type=float, default=3.0, help="Depth of cylindrical cradle dimple in mm (default: 3.0mm)")
    parser.add_argument("--print-orientation", type=str, default="right_down", help="Print orientation for STL export (default: right_down to place flat brace side on bed)")
    parser.add_argument("--gusset-bottom-offset", type=float, default=0.0, help="Offset from bottom of backplate (default: 0.0, extends all the way to bottom)")
    parser.add_argument("--export", type=str, default="both", choices=["both", "stl", "step"], help="Export format")
    
    args = parser.parse_args()
    
    holder = create_claw_hammer_holder(
        units=args.units,
        rail_height=args.rail_height,
        head_dia=args.head_dia,
        face_to_handle=args.face_to_handle,
        handle_size=args.handle_size,
        slot_width=args.slot_width,
        slot_entrance_width=args.slot_entrance_width,
        shelf_length=args.shelf_length,
        front_claw_lip=args.front_claw_lip,
        claw_elevation=args.claw_elevation,
        shelf_thickness=args.shelf_thickness,
        shelf_drop=args.shelf_drop,
        fillet_radius=args.fillet_radius,
        fillet_to_dimple=args.fillet_to_dimple,
        divot_depth=args.divot_depth,
        gusset_bottom_offset=args.gusset_bottom_offset
    )
    
    filename = f"claw_hammer_holder_{args.units}u_groove.stl"
    export_model(
        holder,
        filename,
        category="tool_holders",
        export=args.export,
        print_orientation=args.print_orientation
    )
