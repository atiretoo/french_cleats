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
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        units=units, rail_height=rail_height, mount_type="groove", num_rows=2
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
    
    shelf_pts = [
        (shelf_bot_y, back_z),
        (shelf_bot_y, front_z),
        (shelf_top_y, front_z),
        (shelf_top_y, back_z),
    ]
    
    # 4. Slim 5mm Triangular Support Brace & Parallel Triangular Cutout
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
    
    # 6. Handle Slot & Cradle Divot Parameters
    z_handle = back_z - head_clearance - (head_length / 2.0)
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
    
    divot_center_y = (shelf_top_y - divot_depth) + divot_radius
    divot_start_z = back_z - 11.0
    divot_extrude_len = abs(front_z - divot_start_z) + 4.0

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
        # Main shelf block
        .workplaneFromTagged("right_wp")
        .polyline(shelf_pts)
        .close()
        .extrude(-width)
        # Structural fillets where shelf meets backplate
        .faces("-Z")
        .faces(">Z")
        .edges("|X")
        .edges("not >Y")
        .edges("not <Y")
        .fillet(5.0)
        # Triangular support brace and filleted lightening cutout
        .workplaneFromTagged("right_wp")
        .workplane(offset=-width)
        .polyline(brace_pts)
        .close()
        .extrude(web_thickness)
        .workplaneFromTagged("right_wp")
        .workplane(offset=-width)
        .placeSketch(cutout_sketch)
        .cutBlind(web_thickness)
        # Handle slot and circular seat
        .copyWorkplane(cq.Workplane("ZX", origin=(0, shelf_top_y + 2.0, 0)))
        .polyline(slot_poly_pts)
        .close()
        .cutBlind(-(shelf_thickness + 4.0))
        .copyWorkplane(cq.Workplane("ZX", origin=(0, shelf_top_y + 2.0, 0)))
        .moveTo(z_handle, x_seat)
        .circle(w_half_slot)
        .cutBlind(-(shelf_thickness + 4.0))
        # Cylindrical cradle divots for mallet head
        .workplaneFromTagged("back_wp")
        .workplane(offset=divot_start_z)
        .moveTo(x_seat, divot_center_y)
        .circle(divot_radius)
        .cutBlind(-divot_extrude_len)
    )
    
    # 8. Screw Holes (if groove mount)
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
    parser = argparse.ArgumentParser(description="Generate French Cleat Mallet Tool Holder")
    parser.add_argument("--units", type=int, default=3, help="Width in units (default: 3, 84mm / ~3.3 in)")
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

    filename = f"mallet_holder_{args.units}u_groove.stl"
    export_model(
        holder,
        filename,
        category="tool_holders",
        export=args.export,
        print_orientation=args.print_orientation
    )
