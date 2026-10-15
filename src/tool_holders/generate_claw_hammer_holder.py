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
    face_to_handle=60.0,
    handle_size=25.0,
    slot_width=40.0,
    slot_entrance_width=50.0,
    shelf_length=None,
    front_claw_lip=15.0,
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
    
    # 2. Main Shelf Block
    shelf = (
        cq.Workplane("ZX", origin=(0, shelf_bot_y, 0))
        .moveTo(back_z - shelf_extrude_dist / 2.0, 0)
        .rect(shelf_extrude_dist, width)
        .extrude(shelf_thickness)
    )
    body = body.union(shelf)
    
    # 3. Structural Fillet at Backplate Junction
    fillet_edges = []
    for e in body.edges().vals():
        b = e.BoundingBox()
        if abs(b.zmin - back_z) < 0.1 and abs(b.zmax - back_z) < 0.1:
            if abs(b.ymin - shelf_top_y) < 0.1 or abs(b.ymin - shelf_bot_y) < 0.1:
                if (b.xmax - b.xmin) > 10.0:
                    fillet_edges.append(e)
    if fillet_edges:
        try:
            body = body.newObject(fillet_edges).fillet(fillet_radius)
        except Exception:
            try:
                body = body.newObject(fillet_edges).fillet(2.0)
            except Exception:
                pass

    # 4. Elevated Claw Support Block (in front of handle slot)
    elev_len = abs(front_z - z_slot_front)
    elev_center_z = (z_slot_front + front_z) / 2.0
    
    elev_block = (
        cq.Workplane("ZX", origin=(0, shelf_top_y, 0))
        .moveTo(elev_center_z, 0)
        .rect(elev_len, width)
        .extrude(claw_elevation)
    )
    body = body.union(elev_block)
    
    # Round off top edges of elevated block (top-front and top-back) for printability & smooth seating
    top_edges = []
    for e in body.edges().vals():
        b = e.BoundingBox()
        if abs(b.ymin - elev_top_y) < 0.1 and abs(b.ymax - elev_top_y) < 0.1:
            if abs(b.zmin - front_z) < 0.1 or abs(b.zmin - z_slot_front) < 0.1:
                if (b.xmax - b.xmin) > 10.0:
                    top_edges.append(e)
    if top_edges:
        try:
            body = body.newObject(top_edges).fillet(2.5)
        except Exception:
            pass
        
    # 5. Slim 5mm Triangular Support Brace
    gusset_y_bottom = bottom_y + gusset_bottom_offset
    brace_pts = [
        (shelf_bot_y, back_z),
        (shelf_bot_y, front_z),
        (gusset_y_bottom, back_z),
    ]
    
    brace = (
        cq.Workplane("YZ", origin=(-width / 2.0, 0, 0))
        .polyline(brace_pts).close()
        .extrude(web_thickness)
    )
    body = body.union(brace)
    
    # 6. Parallel Triangular Cutout
    dy = gusset_y_bottom - shelf_bot_y
    dz = back_z - front_z
    m = dy / dz
    b0 = gusset_y_bottom - m * back_z

    W_top = 10.0
    W_back = 10.0
    W_diag = 10.0

    b = b0 + W_diag * math.sqrt(1 + m**2)

    v1 = (shelf_bot_y - W_top, back_z - W_back)
    v2 = (shelf_bot_y - W_top, (shelf_bot_y - W_top - b) / m)
    v3 = (m * (back_z - W_back) + b, back_z - W_back)

    cutout_pts = [v1, v2, v3]
    gusset_cutout = (
        cq.Workplane("YZ", origin=(-width / 2.0 - 2.0, 0, 0))
        .polyline(cutout_pts).close()
        .extrude(web_thickness + 4.0)
    )
    gusset_cutout = gusset_cutout.edges("|X").fillet(5.0)
    body = body.cut(gusset_cutout)

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
    
    slot_cutter_height = claw_elevation + shelf_thickness + 4.0
    slot_cutter = (
        cq.Workplane("ZX", origin=(0, elev_top_y + 2.0, 0))
        .polyline(slot_poly_pts).close()
        .extrude(-slot_cutter_height)
    )
    back_edges = [e for e in slot_cutter.edges("|Y").vals() if abs(e.BoundingBox().xmin - x_slot_back) < 0.1]
    if back_edges:
        try:
            slot_cutter = slot_cutter.newObject(back_edges).fillet(5.0)
        except Exception:
            pass
    body = body.cut(slot_cutter)
    
    # 8. Cylindrical Cradle Dimples
    # Rear dimple for striking face neck: starts at dimple_start_z, extends to slot
    divot_rear_y = (shelf_top_y - divot_depth) + divot_radius
    divot_rear_len = abs(z_handle - dimple_start_z) + 5.0
    divot_rear = (
        cq.Workplane("XY")
        .workplane(offset=dimple_start_z)
        .moveTo(x_dimple, divot_rear_y)
        .circle(divot_radius)
        .extrude(-divot_rear_len)
    )
    body = body.cut(divot_rear)

    # Front dimple on top of elevated claw platform:
    divot_front_y = (elev_top_y - divot_depth) + divot_radius
    divot_front_len = abs(front_z - z_slot_front) + 4.0
    divot_front = (
        cq.Workplane("XY")
        .workplane(offset=z_slot_front + 2.0)
        .moveTo(x_dimple, divot_front_y)
        .circle(divot_radius)
        .extrude(-divot_front_len)
    )
    body = body.cut(divot_front)

    # 9. Screw Holes
    if screw_pts:
        screws = (
            cq.Workplane("XY").workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6 / 2.0)
            .extrude(-20)
        )
        body = body.cut(screws)
        
        recesses = (
            cq.Workplane("XY").workplane(offset=-8)
            .pushPoints(screw_pts)
            .circle(8.0 / 2.0)
            .extrude(-20)
        )
        body = body.cut(recesses)
        
    return body

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate French Cleat Claw Hammer Tool Holder")
    parser.add_argument("--units", type=int, default=2, help="Width in units (default: 2, 56mm / ~2.2 in)")
    parser.add_argument("--rail-height", type=float, default=DEFAULT_RAIL_HEIGHT, help="Rail height in mm")
    parser.add_argument("--head-dia", type=float, default=30.0, help="Hammer striking head diameter in mm (default: 30mm)")
    parser.add_argument("--face-to-handle", type=float, default=60.0, help="Distance from striking face to handle center in mm (default: 60.0mm)")
    parser.add_argument("--handle-size", type=float, default=25.0, help="Hammer handle neck size in mm")
    parser.add_argument("--slot-width", type=float, default=40.0, help="Handle slot width/depth in mm (default: 40mm)")
    parser.add_argument("--slot-entrance-width", type=float, default=50.0, help="Entrance mouth width in mm (default: 50mm)")
    parser.add_argument("--shelf-length", type=float, default=None, help="Shelf depth from wall in mm (default: auto ~111mm)")
    parser.add_argument("--front-claw-lip", type=float, default=15.0, help="Front claw support platform length in mm (default: 15mm)")
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
