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

def create_mallet_holder(
    units=3,
    mount_type="groove",
    rail_height=DEFAULT_RAIL_HEIGHT,
    head_length=95.0,
    head_dia=60.0,
    handle_size=26.0,
    slot_width=28.0,
    slot_entrance_width=50.0,
    shelf_length=135.0,
    shelf_thickness=8.0,
    shelf_drop=60.0,
    head_clearance=18.0,
    divot_depth=3.0,
    divot_radius=None,
    web_thickness=5.0,
    gusset_bottom_offset=0.0
):
    """
    Creates a French Cleat mallet tool holder.
    
    The mallet rests with its cylindrical head parallel to the Z-axis (pointing forward
    from the wall) and its handle extending downwards (-Y).
    The shelf is lowered 60mm down from the top of the backplate so the mallet head sits
    below the top edge of the holder, leaving the top cleat mounting screws completely clear.
    The handle slot and divot are shifted towards the user (Z) to clear the backplate and fillet,
    and positioned across X so the mallet head sits entirely within the holder bounds.
    30mm radius cylindrical divots on the front and rear shelf support arms cradle the
    60mm diameter mallet head securely.
    A slim 5mm triangular brace with a rounded lightening cutout supports the holder,
    and generous 5mm structural fillets reinforce the top and bottom junctions where
    the shelf connects to the backplate.
    """
    if divot_radius is None:
        divot_radius = head_dia / 2.0 + 0.5  # 30.5mm for clean clearance
        
    width = units * UNIT_WIDTH  # e.g. 3 * 28 = 84mm (~3.3 inches)
    
    # 1. Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(
        units=units, rail_height=rail_height, mount_type=mount_type, num_rows=2
    )
    
    # Coordinates in Z:
    # Z = 0 is wall (back of cleat)
    # Z = -BACKPLATE_THICKNESS (-11.0) is front face of baseplate
    # Shelf extends forward to Z = -shelf_length
    front_z = -shelf_length
    back_z = -BACKPLATE_THICKNESS
    shelf_extrude_dist = shelf_length - BACKPLATE_THICKNESS
    
    # Coordinates in Y:
    # Shelf lowered 60mm from top so mallet is below top of holder and clear of screw holes
    shelf_top_y = top_y - shelf_drop  # 20.0 - 60.0 = -40.0mm
    shelf_bot_y = shelf_top_y - shelf_thickness  # -48.0mm
    
    # 2. Main Shelf Block
    # ZX plane normal is +Y. Local X = Z, Local Y = X.
    # Note: no fillets on the Z edges to ensure solid, gap-free fusion with the backplate.
    shelf = (
        cq.Workplane("ZX", origin=(0, shelf_bot_y, 0))
        .moveTo(back_z - shelf_extrude_dist / 2.0, 0)
        .rect(shelf_extrude_dist, width)
        .extrude(shelf_thickness)
    )
    body = body.union(shelf)
    
    # 3. Big Structural Fillets on Top and Bottom Edges where Shelf Meets Backplate
    fillet_edges = []
    for e in body.edges().vals():
        b = e.BoundingBox()
        if abs(b.zmin - back_z) < 0.1 and abs(b.zmax - back_z) < 0.1:
            if abs(b.ymin - shelf_top_y) < 0.1 or abs(b.ymin - shelf_bot_y) < 0.1:
                if (b.xmax - b.xmin) > 10.0:
                    fillet_edges.append(e)
    if fillet_edges:
        body = body.newObject(fillet_edges).fillet(5.0)
        
    # 4. Slim 5mm Triangular Support Brace
    # Comes all the way down to the bottom of the backplate (bottom_y)
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
    
    # 5. Exactly Parallel Triangular Cutout
    # The bottom edge of the cutout is exactly parallel with the diagonal hypotenuse of the brace.
    dy = gusset_y_bottom - shelf_bot_y
    dz = back_z - front_z
    m = dy / dz
    b0 = gusset_y_bottom - m * back_z

    W_top = 10.0   # 10mm wall below shelf
    W_back = 10.0  # 10mm wall in front of backplate
    W_diag = 10.0  # 10mm uniform perpendicular wall thickness along diagonal

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

    
    # 6. Handle Slot Cutter
    # Mallet head position:
    # Moved towards user in Z (head_clearance = 18.0) so rear of head (Z = -29.0) clears backplate & 5mm fillet
    z_handle = back_z - head_clearance - (head_length / 2.0)
    # Moved across X so mallet head (60mm dia) is entirely within holder bounds (X = -42 to +42)
    x_seat = -width / 2.0 + (head_dia / 2.0) + 2.0  # -10.0mm (spans X = -40 to +20)
    x_mouth = width / 2.0 + 5.0  # Opens at +X
    x_taper_start = 15.0
    
    w_half_mouth = slot_entrance_width / 2.0
    w_half_slot = slot_width / 2.0
    
    # Slot profile on ZX plane (Local X = Z, Local Y = X)
    slot_poly_pts = [
        (z_handle - w_half_mouth, x_mouth),
        (z_handle - w_half_slot, x_taper_start),
        (z_handle - w_half_slot, x_seat),
        (z_handle + w_half_slot, x_seat),
        (z_handle + w_half_slot, x_taper_start),
        (z_handle + w_half_mouth, x_mouth),
    ]
    
    slot_cutter = (
        cq.Workplane("ZX", origin=(0, shelf_top_y + 2.0, 0))
        .polyline(slot_poly_pts).close()
        .extrude(-(shelf_thickness + 4.0))
    )
    seat_cutter = (
        cq.Workplane("ZX", origin=(0, shelf_top_y + 2.0, 0))
        .moveTo(z_handle, x_seat)
        .circle(w_half_slot)
        .extrude(-(shelf_thickness + 4.0))
    )
    body = body.cut(slot_cutter).cut(seat_cutter)
    
    # 7. 30mm Radius Divots for the Mallet Head (Cylindrical Cradle)
    divot_center_y = (shelf_top_y - divot_depth) + divot_radius
    
    # Start the cradle divot clear of the 5mm backplate fillet
    # (back_z is -11.0, 5mm fillet ends at -16.0; starting at -22.0 leaves 6mm flat clearance)
    divot_start_z = back_z - 11.0
    divot_extrude_len = abs(front_z - divot_start_z) + 4.0
    
    divot_cylinder = (
        cq.Workplane("XY")
        .workplane(offset=divot_start_z)
        .moveTo(x_seat, divot_center_y)
        .circle(divot_radius)
        .extrude(-divot_extrude_len)
    )
    body = body.cut(divot_cylinder)

    
    # 8. Screw Holes (if groove mount)
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
        
    # 9. Multiconnect solids (if multiconnect mount)
    if mc_solids:
        for solid in mc_solids:
            body = body.union(cq.Workplane(solid))
            
    return body

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate French Cleat Mallet Tool Holder")
    parser.add_argument("--units", type=int, default=3, help="Width in units (default: 3, 84mm / ~3.3 in)")
    parser.add_argument("--mount", type=str, default="groove", choices=["groove", "multiconnect"], help="Mount type")
    parser.add_argument("--rail-height", type=float, default=DEFAULT_RAIL_HEIGHT, help="Rail height in mm")
    parser.add_argument("--head-length", type=float, default=95.0, help="Mallet head length in mm")
    parser.add_argument("--head-dia", type=float, default=60.0, help="Mallet head diameter in mm")
    parser.add_argument("--handle-size", type=float, default=26.0, help="Mallet handle size in mm")
    parser.add_argument("--slot-width", type=float, default=28.0, help="Handle slot width in mm")
    parser.add_argument("--shelf-length", type=float, default=135.0, help="Shelf depth from wall in mm (default: 135mm)")
    parser.add_argument("--shelf-drop", type=float, default=60.0, help="Distance shelf is lowered below top of backplate (default: 60mm)")
    parser.add_argument("--head-clearance", type=float, default=18.0, help="Clearance between backplate and mallet head (default: 18mm)")
    parser.add_argument("--print-orientation", type=str, default="right_down", help="Print orientation for STL export (default: right_down to place flat brace side on bed)")
    parser.add_argument("--gusset-bottom-offset", type=float, default=0.0, help="Offset from bottom of backplate (default: 0.0, extends all the way to bottom)")
    parser.add_argument("--export", type=str, default="both", choices=["both", "stl", "step"], help="Export format")
    
    args = parser.parse_args()
    
    holder = create_mallet_holder(
        units=args.units,
        mount_type=args.mount,
        rail_height=args.rail_height,
        head_length=args.head_length,
        head_dia=args.head_dia,
        handle_size=args.handle_size,
        slot_width=args.slot_width,
        shelf_length=args.shelf_length,
        shelf_drop=args.shelf_drop,
        head_clearance=args.head_clearance,
        gusset_bottom_offset=args.gusset_bottom_offset
    )

    
    filename = f"mallet_holder_{args.units}u_{args.mount}.stl"
    export_model(
        holder,
        filename,
        category="tool_holders",
        export=args.export,
        print_orientation=args.print_orientation
    )
