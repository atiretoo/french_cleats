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
import sys

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_v_holder(width_units=2, depth_units=4, rail_height=73.0):
    shelf_thickness = 5.0

    width = width_units * UNIT_WIDTH
    shelf_depth = depth_units * UNIT_WIDTH

    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        width_units, rail_height, mount_type="groove", num_rows=2
    )

    y_drop = width / 2.0
    y_thick = shelf_thickness * math.sqrt(2)
    shelf_top = top_y - 40.0

    v_pts = [
        (-width / 2.0, shelf_top),
        (0.0, shelf_top - y_drop),
        (width / 2.0, shelf_top),
        (width / 2.0, shelf_top - y_thick),
        (0.0, shelf_top - y_drop - y_thick),
        (-width / 2.0, shelf_top - y_thick),
    ]

    # Extrude V-shelf directly from the backplate front plane and drill mounting holes
    tool_holder = (
        tool_holder
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .workplane(offset=-BACKPLATE_THICKNESS)
        .polyline(v_pts)
        .close()
        .extrude(-shelf_depth)
        .workplaneFromTagged("back_wp")
        .pushPoints(screw_pts)
        .hole(3.6, 20.0)
        .workplaneFromTagged("back_wp")
        .workplane(offset=-8.0)
        .pushPoints(screw_pts)
        .hole(8.0, 200.0)
    )

    return tool_holder, width_units, depth_units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat V-Holder")
    parser.add_argument("--width-units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=4, help="Number of units deep (away from wall)")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    args = parser.parse_args()
    
    holder, fw, fd = create_v_holder(
        width_units=args.width_units, 
        depth_units=args.depth_units,
        rail_height=args.rail_height
    )
    
    filename = f"v_holder_{fw}x{fd}u_groove_H{args.rail_height}.stl"
    export_model(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
