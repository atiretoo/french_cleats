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
from core_library import SCREW_SPECS, export_model

def create_nut_pusher(screw_m="M3", layer_thickness=0.28, handle_length=40.0):
    """
    Creates a flat rectangular-handle tool to push captive nuts into tight slots.
    When the handle shoulder hits the cleat face, the V-notched tip seats the nut
    at the exact bolt centerline.
    """
    if screw_m not in SCREW_SPECS:
        raise ValueError(f"Unsupported screw size {screw_m}")
    spec = SCREW_SPECS[screw_m]
    nut_waf, nut_thick = spec["nut_waf"], spec["nut_thick"]

    tool_thickness = nut_thick - 2.0 * layer_thickness
    tool_width = nut_waf * 0.9

    # In generate_cleats.py, the slot depth from the cleat face is:
    # 10.0 + nut_waf / 2.0
    slot_depth = 10.0 + nut_waf / 2.0

    # A hexagon with flats on the side has a point-to-point length of:
    nut_point_to_point = nut_waf * 2.0 / math.sqrt(3)

    # The tool apex (deepest part of the V-notch) must be at this distance
    # from the shoulder so that when the shoulder hits the cleat face,
    # the nut's front point hits the bottom of the slot.
    shaft_length = slot_depth - nut_point_to_point

    # The prongs extend forward from the apex by:
    prong_ext = (tool_width / 2.0) / math.tan(math.radians(60))

    # Coordinates for the base tool profile
    handle_w = tool_width * 2.0

    pts = [
        (0.0, tool_width / 2.0),
        (shaft_length + prong_ext, tool_width / 2.0),
        (shaft_length, 0.0),
        (shaft_length + prong_ext, -tool_width / 2.0),
        (0.0, -tool_width / 2.0),
        (0.0, -handle_w / 2.0),
        (-handle_length, -handle_w / 2.0),
        (-handle_length, handle_w / 2.0),
        (0.0, handle_w / 2.0),
    ]

    handle_pts = [
        (0.0, handle_w / 2.0),
        (0.0, -handle_w / 2.0),
        (-handle_length, -handle_w / 2.0),
        (-handle_length, handle_w / 2.0),
    ]

    tool = (
        cq.Workplane("XY")
        .polyline(pts)
        .close()
        .extrude(tool_thickness)
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .polyline(handle_pts)
        .close()
        .extrude(tool_thickness)
    )

    return tool, tool_thickness, tool_width

def main():
    parser = argparse.ArgumentParser(description="Generate Nut Pusher Tool")
    parser.add_argument("--screw", type=str, default="M3", choices=["M3", "M4", "M5"], help="Screw size (M3, M4, M5)")
    parser.add_argument("--layer-thickness", type=float, default=0.28, help="Layer thickness in mm")
    parser.add_argument("--handle-length", type=float, default=40.0, help="Handle length in mm (default: 40.0)")
    parser.add_argument("--export", type=str, default="both", choices=["stl", "step", "both"], help="Export format")

    args = parser.parse_args()

    tool, t, w = create_nut_pusher(args.screw, args.layer_thickness, args.handle_length)

    filename = f"nut_pusher_{args.screw}_L{args.layer_thickness}.stl"
    export_model(tool, filename, print_orientation="none", category="utilities", export=args.export)
    print(f"Exported {filename} (thickness: {t:.2f}mm, shaft width: {w:.2f}mm)")

if __name__ == "__main__":
    main()
