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
import math
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    create_baseplate, export_model, support_fin, drill_backplate_screws,
    UNIT_WIDTH, BACKPLATE_THICKNESS
)

def make_gridfinity_cutout():
    """
    Creates a single Gridfinity baseplate cutout (negative geometry).
    """
    w1 = 42.0 - 2.0 * 2.15
    cutout = (
        cq.Workplane("XY")
        .rect(42.0, 42.0)
        .extrude(2.15, taper=45)
        .faces(">Z")
        .workplane()
        .rect(w1, w1)
        .extrude(1.8)
        .faces(">Z")
        .workplane()
        .rect(w1, w1)
        .extrude(0.7, taper=45)
    )
    return cutout

def create_shelf(width_units=3, depth_units=3, gridfinity=True, rail_height=73.0):
    width = width_units * UNIT_WIDTH
    shelf_depth = depth_units * UNIT_WIDTH
    shelf_thickness = 7.0
    brace_thickness = 5.0

    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        width_units, rail_height
    )

    # Position shelf 1/3 of the way from the bottom to the top
    total_height = top_y - bottom_y
    shelf_top = bottom_y + total_height / 3.0
    shelf_bot = shelf_top - shelf_thickness

    # 1. Shelf slab and triangular braces
    shelf_pts = [
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS),
    ]
    brace_pts = [
        (bottom_y, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
    ]

    tool_holder = (
        tool_holder
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .end(2)
        .faces(">X")
        .workplane(centerOption="ProjectedOrigin")
        .tag("right_wp")
        .end(2)
        .workplaneFromTagged("right_wp")
        .polyline(shelf_pts)
        .close()
        .extrude(-width)
        .workplaneFromTagged("right_wp")
        .workplane(offset=-width)
        .polyline(brace_pts)
        .close()
        .extrude(brace_thickness)
        .workplaneFromTagged("right_wp")
        .polyline(brace_pts)
        .close()
        .extrude(-brace_thickness)
    )

    # 2. Add Gridfinity Baseplate geometry on top of the shelf
    if gridfinity:
        # The GF cutout is built in +Z. Rotate around X-axis by +90 degrees to map +Z to -Y.
        gf_cutout_rot = make_gridfinity_cutout().val().moved(
            cq.Location(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 90)
        )

        num_x = int(width / 42.0)
        num_z = int(shelf_depth / 42.0)

        # Cut each cell individually because adjacent 42x42 cutouts share knife-edge
        # boundaries at Y=shelf_top, which would make a single Compound non-manifold.
        for ix in range(num_x):
            for iz in range(num_z):
                cx = (ix - num_x / 2.0 + 0.5) * 42.0
                cz = -BACKPLATE_THICKNESS - shelf_depth / 2.0 + (iz - num_z / 2.0 + 0.5) * 42.0
                tool_holder = tool_holder.cut(
                    gf_cutout_rot.moved(cq.Location(cq.Vector(cx, shelf_top, cz)))
                )

    # 3. Cut screw clearance holes and recesses
    if screw_pts:
        tool_holder = drill_backplate_screws(tool_holder, screw_pts, cbore_depth=20.0)

    return tool_holder, width_units, depth_units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Shelf")
    parser.add_argument("--width-units", type=int, default=3, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=3, help="Number of units deep")
    parser.add_argument("--no-gridfinity", action="store_true", help="Disable Gridfinity baseplate geometry")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--print-orientation", type=str, default="45_deg", choices=["45_deg", "back_down", "left_down"], help="Print orientation (default: 45_deg with support fins)")
    parser.add_argument("--no-support-fins", action="store_true", help="Disable support fins")
    parser.add_argument("--export", type=str, default="both", choices=["stl", "step", "both"], help="Export format")
    args = parser.parse_args()

    cad_holder, fw, fd = create_shelf(
        width_units=args.width_units,
        depth_units=args.depth_units,
        gridfinity=not args.no_gridfinity,
        rail_height=args.rail_height,
    )

    if args.print_orientation == "45_deg":
        # Rotate holder: back_down (180 around X) then +45 around Y
        holder = cad_holder.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 1, 0), 45)
        z_min = holder.val().BoundingBox().zmin
        holder = holder.translate((0, 0, -z_min))

        if not args.no_support_fins:
            width = fw * UNIT_WIDTH
            L = width / math.sqrt(2)
            fin_w = 1.6
            tip_w = 0.4

            fin_proto = support_fin(z_gap=0.0, is_right=False, length=L, height=L, fin_width=fin_w, tip_width=tip_w, cutoff_top=True)
            fin_proto = fin_proto.rotate((0, 0, 0), (0, 0, 1), -90).translate((L / 2, 0, 0))

            bb = holder.val().BoundingBox()
            top_y = bb.ymin
            bot_y = bb.ymax

            # Line up the outside edge of the taper tip with the corner of the backplate
            fin_top = fin_proto.translate((0, top_y + tip_w / 2, 0))
            fin_bot = fin_proto.translate((0, bot_y - tip_w / 2, 0))

            assy = cq.Assembly()
            assy.add(holder.val(), name="Shelf", color=cq.Color(0.8, 0.5, 0.1, 1.0))
            assy.add(fin_top.val(), name="Fin_Top", color=cq.Color(0.2, 0.7, 0.2, 1.0))
            assy.add(fin_bot.val(), name="Fin_Bottom", color=cq.Color(0.2, 0.7, 0.2, 1.0))
            export_shape = assy
        else:
            export_shape = holder
        print_orient = "none"
    else:
        export_shape = cad_holder
        print_orient = args.print_orientation

    gf_str = "_GF" if not args.no_gridfinity else ""
    filename = f"shelf_{fw}x{fd}u{gf_str}_H{args.rail_height}.stl"
    export_model(export_shape, filename, category="gridfinity", print_orientation=print_orient, export=args.export, step_shape=cad_holder)

if __name__ == "__main__":
    main()
