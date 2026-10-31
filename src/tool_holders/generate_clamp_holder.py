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
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, drill_backplate_screws, export_model

def create_clamp_holder(
    units=4,
    rail_height=73.0,
    num_slots=4,
    slot_width=8.0,
    slot_depth=55.0,
    slot_spacing=30.0,
    bump_height=10.0,
    bump_flat_width=24.0,
    brace_thickness=5.0,
):
    width = units * UNIT_WIDTH
    shelf_depth = num_slots * slot_spacing

    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        units, rail_height
    )
    shelf_top = top_y - 40.0
    shelf_bot = top_y - 50.0

    brace_pts = [
        (bottom_y + 2.5, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
    ]
    shelf_pts = [
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS),
    ]

    # Bump along the right edge of the shelf where the slots open.
    # The side facing towards the left side angles up at 45 degrees so no supports are needed when printed left_down.
    x_right = width / 2.0
    x_flat_start = x_right - bump_flat_width
    x_slope_start = x_flat_start - bump_height  # 45-degree angle: rise == run

    bump_profile = [
        (x_slope_start, shelf_top),
        (x_flat_start, shelf_top + bump_height),
        (x_right, shelf_top + bump_height),
        (x_right, shelf_top),
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
        .workplane(offset=-width)
        .polyline(brace_pts)
        .close()
        .extrude(brace_thickness)
        .workplaneFromTagged("right_wp")
        .polyline(shelf_pts)
        .close()
        .extrude(-width)
        .workplaneFromTagged("back_wp")
        .workplane(offset=-BACKPLATE_THICKNESS)
        .polyline(bump_profile)
        .close()
        .extrude(-shelf_depth)
    )

    try:
        tool_holder = (
            tool_holder
            .faces("+X or -Y")
            .faces("not >X")
            .faces("not <Y")
            .edges("not <Z")
            .edges("not >X")
            .edges("|X or |Y or |Z")
            .fillet(5.0)
            .faces("+Y")
            .faces("not >Y")
            .faces("<Y")
            .edges(">Z")
            .fillet(5.0)
        )
    except Exception:
        pass

    # Cut the slots on the right side where the bump and slot openings are located
    cut_length = slot_depth + 5.0
    slot_x = (x_right - slot_depth) + cut_length / 2.0

    slot_centers_z = [-BACKPLATE_THICKNESS - 15 - i * slot_spacing for i in range(num_slots)]
    slot_pts = [(z, slot_x) for z in slot_centers_z]

    tool_holder = (
        tool_holder
        .copyWorkplane(cq.Workplane("ZX", origin=(0, shelf_top + bump_height + 2.0, 0)))
        .pushPoints(slot_pts)
        .rect(slot_width, cut_length)
        .cutBlind(-35.0)
    )

    tool_holder = drill_backplate_screws(tool_holder, screw_pts)

    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat clamp holder")
    parser.add_argument("--units", type=int, default=4, help="Number of units wide (default: 4)")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--num-slots", type=int, default=4, help="Number of slots")
    parser.add_argument("--slot-width", type=float, default=8.0, help="Width of slots for clamp bars in mm (default: 8.0)")
    parser.add_argument("--slot-depth", type=float, default=55.0, help="Depth of slots from open edge in mm (default: 55.0)")
    parser.add_argument("--slot-spacing", type=float, default=30.0, help="Center-to-center spacing of slots in mm (default: 30.0)")
    parser.add_argument("--bump-height", type=float, default=10.0, help="Height of bump above shelf in mm (default: 10.0)")
    parser.add_argument("--bump-flat-width", type=float, default=24.0, help="Width of flat top of bump in mm (default: 24.0)")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format")
    parser.add_argument("--print-orientation", type=str, default="left_down", choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down", "none"], help="Print orientation for STL export")
    args = parser.parse_args()

    holder = create_clamp_holder(
        units=args.units,
        rail_height=args.rail_height,
        num_slots=args.num_slots,
        slot_width=args.slot_width,
        slot_depth=args.slot_depth,
        slot_spacing=args.slot_spacing,
        bump_height=args.bump_height,
        bump_flat_width=args.bump_flat_width,
    )
    filename = f"clamp_holder_{args.units}u_H{args.rail_height}_{args.num_slots}slots.stl"
    export_model(holder, filename, category="tool_holders", print_orientation=args.print_orientation, export=args.export)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
