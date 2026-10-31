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
    UNIT_WIDTH, BACKPLATE_THICKNESS, TOP_GROOVE_Y, GROOVE_SURFACE_HALF_WIDTH,
    create_baseplate, drill_backplate_screws, export_model, support_fin
)

def add_support_fins(holder, width_units, depth_units, bottom_groove_y, top_y):
    holder = holder.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 1, 0), 45)
    baseplate_width = width_units * UNIT_WIDTH
    cos45 = math.cos(math.radians(45))
    X_right = (baseplate_width / 2.0) * cos45
    X_left = (-baseplate_width / 2.0) * cos45
    length = X_right - X_left
    bb = holder.val().BoundingBox()
    holder = holder.translate((-X_right, 0, -bb.zmin))
    # Because we lowered the holder by the chamfer depth (2.0 * cos45), the holder physically
    # penetrates into the support fins by that amount. We must add this drop to the z_gap
    # to maintain the 0.10mm clearance required for a clean breakaway!
    drop_offset = 2.0 * cos45
    adjusted_z_gap = 0.10 + drop_offset

    fin_width = 1.6
    fin_proto = support_fin(z_gap=adjusted_z_gap, is_right=False, length=length, height=length, fin_width=fin_width).rotate((0, 0, 0), (0, 0, 1), -90)
    orig_top_edge = TOP_GROOVE_Y - GROOVE_SURFACE_HALF_WIDTH
    orig_bot_edge = bottom_groove_y + GROOVE_SURFACE_HALF_WIDTH
    fin1 = fin_proto.translate((0, -orig_top_edge, 0)).val()
    fin2 = fin_proto.translate((0, -orig_bot_edge, 0)).val()

    shelf_length = depth_units * UNIT_WIDTH
    kickstand_length = (shelf_length * cos45) * 0.8
    kickstand_fin = (
        support_fin(z_gap=adjusted_z_gap, is_right=True, length=kickstand_length, height=kickstand_length, fin_width=fin_width)
        .rotate((0, 0, 0), (0, 0, 1), -90)
        .translate((0, -(top_y - 45.0), 0))
        .val()
    )
    return holder.union(cq.Compound.makeCompound([fin1, fin2, kickstand_fin]))

def create_slot_holder(width_units=1, depth_units=2, slot_width=6.25, back_clearance=10.0, rail_height=73.0):
    brace_thickness = 2.5

    width = width_units * UNIT_WIDTH
    shelf_depth = depth_units * UNIT_WIDTH

    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        width_units, rail_height
    )

    shelf_top = top_y - 40.0
    shelf_bot = top_y - 45.0

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
        .polyline(shelf_pts)
        .close()
        .extrude(-width)
    )

    brace_offsets = [(-width, brace_thickness)]
    if width_units > 1:
        brace_offsets.append((0.0, -brace_thickness))

    cutout_sketch = None
    if depth_units > 2:
        try:
            cutout_sketch = (
                cq.Sketch()
                .polygon(brace_pts)
                .wires()
                .offset(-15.0, mode="r")
                .reset()
                .vertices()
                .fillet(8.0)
            )
        except Exception:
            cutout_sketch = None

    for wp_offset, extrude_dist in brace_offsets:
        tool_holder = (
            tool_holder
            .faces(">X")
            .workplane(offset=wp_offset, centerOption="ProjectedOrigin")
            .polyline(brace_pts)
            .close()
            .extrude(extrude_dist)
        )
        if cutout_sketch is not None:
            tool_holder = (
                tool_holder
                .faces(">X")
                .workplane(offset=wp_offset, centerOption="ProjectedOrigin")
                .placeSketch(cutout_sketch)
                .cutBlind(extrude_dist)
            )

    try:
        tool_holder = (
            tool_holder
            .faces("-Z")
            .faces("not <Z")
            .edges("|X")
            .edges("not >Y")
            .edges("not <Y")
            .fillet(5.0)
        )
    except Exception:
        pass

    # Cut the slots (1 per unit width)
    slot_length = shelf_depth - back_clearance + 5.0
    z_center = -BACKPLATE_THICKNESS - back_clearance - slot_length / 2.0
    slot_pts = [
        (z_center, -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH)
        for i in range(width_units)
    ]

    tool_holder = (
        tool_holder
        .copyWorkplane(cq.Workplane("ZX", origin=(0, shelf_top + 10.0, 0)))
        .pushPoints(slot_pts)
        .rect(slot_length, slot_width)
        .cutBlind(-30.0)
    )

    if screw_pts:
        tool_holder = drill_backplate_screws(tool_holder, screw_pts, cbore_depth=200.0)

    return tool_holder, width_units, depth_units, bottom_groove_y, top_y

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat slot holder")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=2, help="Number of units deep (away from wall)")
    parser.add_argument("--slot-width", type=float, default=6.25, help="Width of the slot in mm")
    parser.add_argument("--back-clearance", type=float, default=10.0, help="Distance from backplate to start of slot")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--print-orientation", type=str, default="right_down_45", choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down", "right_down_45"], help="Print orientation for STL export (default: right_down_45)")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")
    args = parser.parse_args()

    cad_holder, fw, fd, bottom_groove_y, top_y = create_slot_holder(
        width_units=args.width_units,
        depth_units=args.depth_units,
        slot_width=args.slot_width,
        back_clearance=args.back_clearance,
        rail_height=args.rail_height,
    )

    if args.print_orientation == "right_down_45":
        print_holder = add_support_fins(cad_holder, fw, fd, bottom_groove_y, top_y)
        filename = f"slot_holder_{fw}x{fd}u_H{args.rail_height}_W{args.slot_width}_45deg.stl"
        export_model(print_holder, filename, category="tool_holders", print_orientation="face_down", export=args.export, step_shape=cad_holder)
    else:
        filename = f"slot_holder_{fw}x{fd}u_H{args.rail_height}_W{args.slot_width}.stl"
        export_model(cad_holder, filename, category="tool_holders", print_orientation=args.print_orientation, export=args.export)

if __name__ == "__main__":
    main()
