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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_clamp_holder(
    units=4,
    rail_height=73.0,
    num_slots=4,
    slot_width=8.0,
    slot_spacing=30.0,
    bump_height=10.0,
    bump_width=14.0,
    brace_thickness=5.0,
    mount_type="groove",
):
    width = units * UNIT_WIDTH
    shelf_depth = num_slots * slot_spacing

    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(
        units, rail_height, mount_type=mount_type, num_rows=2
    )

    shelf_top = top_y - 40.0
    shelf_bot = top_y - 50.0

    brace_pts = [
        (bottom_y + 2.5, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
    ]
    brace = (
        cq.Workplane("YZ")
        .polyline(brace_pts)
        .close()
        .extrude(brace_thickness)
        .translate((-width / 2, 0, 0))
    )
    tool_holder = tool_holder.union(brace)

    shelf_pts = [
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS),
    ]
    shelf = (
        cq.Workplane("YZ")
        .polyline(shelf_pts)
        .close()
        .extrude(width)
        .translate((-width / 2, 0, 0))
    )
    tool_holder = tool_holder.union(shelf)

    # Bump along the left edge of the shelf to support the back of the clamp head
    bump_pts = [
        (shelf_top, -BACKPLATE_THICKNESS),
        (shelf_top, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top + bump_height, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top + bump_height, -BACKPLATE_THICKNESS),
    ]
    bump = (
        cq.Workplane("YZ")
        .polyline(bump_pts)
        .close()
        .extrude(bump_width)
        .translate((-width / 2, 0, 0))
    )
    tool_holder = tool_holder.union(bump)

    brace_inner_x = -width / 2 + brace_thickness
    bump_inner_x = -width / 2 + bump_width

    class FilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge):
                    continue
                b = o.BoundingBox()
                if abs(b.ymin - shelf_top) < 1 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
                elif abs(b.ymin - shelf_bot) < 1 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
                elif abs(b.xmin - brace_inner_x) < 1 and abs(b.ymin - shelf_bot) < 1 and b.zmax - b.zmin > 10:
                    res.append(o)
                elif abs(b.xmin - brace_inner_x) < 1 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1 and b.ymax - b.ymin > 10:
                    res.append(o)
            return res

    try:
        tool_holder = tool_holder.edges(FilletSelector()).fillet(5.0)
    except Exception:
        pass

    # Cut the slots: from bump_inner_x through the right edge (plus 5mm extra overhang)
    cut_length = (width / 2 + 5.0) - bump_inner_x
    slot_x = bump_inner_x + cut_length / 2.0

    slot_centers_z = [-BACKPLATE_THICKNESS - 15 - i * slot_spacing for i in range(num_slots)]
    slot_pts = [(z, slot_x) for z in slot_centers_z]

    slots = (
        cq.Workplane("ZX", origin=(0, shelf_top + 1, 0))
        .pushPoints(slot_pts)
        .rect(slot_width, cut_length)
        .extrude(-20)
    )
    tool_holder = tool_holder.cut(slots)

    if mount_type == "groove":
        screws = (
            cq.Workplane("XY")
            .workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6 / 2)
            .extrude(-20)
        )
        tool_holder = tool_holder.cut(screws)

        recesses = (
            cq.Workplane("XY")
            .workplane(offset=-8)
            .pushPoints(screw_pts)
            .circle(8.0 / 2)
            .extrude(-200)
        )
        tool_holder = tool_holder.cut(recesses)

    for s in slots_to_cut:
        tool_holder = tool_holder.union(s)

    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat clamp holder")
    parser.add_argument("--units", type=int, default=4, help="Number of units wide (default: 4)")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--num-slots", type=int, default=4, help="Number of slots")
    parser.add_argument("--slot-width", type=float, default=8.0, help="Width of slots for clamp bars in mm (default: 8.0)")
    parser.add_argument("--slot-spacing", type=float, default=30.0, help="Center-to-center spacing of slots in mm (default: 30.0)")
    parser.add_argument("--bump-height", type=float, default=10.0, help="Height of bump above shelf in mm (default: 10.0)")
    parser.add_argument("--bump-width", type=float, default=14.0, help="Width of bump along left shelf edge in mm (default: 14.0)")
    parser.add_argument("--mount", choices=["groove", "multiconnect"], default="groove", help="Mount type")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format")
    parser.add_argument("--print-orientation", type=str, default="left_down", choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down", "none"], help="Print orientation for STL export")
    args = parser.parse_args()

    holder = create_clamp_holder(
        units=args.units,
        rail_height=args.rail_height,
        num_slots=args.num_slots,
        slot_width=args.slot_width,
        slot_spacing=args.slot_spacing,
        bump_height=args.bump_height,
        bump_width=args.bump_width,
        mount_type=args.mount,
    )
    filename = f"clamp_holder_{args.units}u_{args.mount}_H{args.rail_height}_{args.num_slots}slots.stl"
    export_model(holder, filename, category="tool_holders", print_orientation=args.print_orientation, export=args.export)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
