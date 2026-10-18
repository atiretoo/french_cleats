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
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_hook(width_units=1, length_units=4, diameter=10.0, slope_deg=5.0, rail_height=73.0, fillet_radius=3.0, tip_fillet=3.0):
    """
    Creates a French Cleat hook tool holder.
    - width_units: Width of the backplate in 28mm units (default: 1U)
    - length_units: Length of the hook in 28mm units (default: 4U = 112mm)
    - diameter: Diameter of the cylindrical hook rod (default: 10mm)
    - slope_deg: Angle in degrees sloping upwards from horizontal (default: 5 deg)
    - rail_height: Cleat rail height (default: 73.0mm)
    - fillet_radius: Radius of fillet connecting the hook rod to the backplate (default: 3.0mm)
    - tip_fillet: Radius of fillet on the tip of the hook (default: 3.0mm)
    """
    length = length_units * UNIT_WIDTH
    radius = diameter / 2.0

    # Create the standard baseplate
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        width_units, rail_height
    )

    # Position hook at 1/3 of the distance from bottom_y to top_y
    total_height = top_y - bottom_y
    hook_y = bottom_y + total_height / 3.0

    # To slope upwards (+Y) by slope_deg while projecting outwards into -Z,
    # rotate the workplane around local X-axis by -(180 - slope_deg).
    rot_angle = -(180.0 - slope_deg)

    # Start the hook cylinder slightly inside the backplate so the intersection with
    # the front face (Z = -BACKPLATE_THICKNESS) forms a clean elliptical loop edge.
    embed_depth = 4.0
    total_rod_len = length + embed_depth

    tool_holder = (
        tool_holder
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .transformed(
            offset=(0.0, hook_y, -BACKPLATE_THICKNESS + embed_depth),
            rotate=(rot_angle, 0.0, 0.0),
        )
        .circle(radius)
        .extrude(total_rod_len)
    )

    if tip_fillet > 0:
        try:
            tool_holder = tool_holder.faces("<Z").edges().fillet(tip_fillet)
        except Exception:
            pass

    if fillet_radius > 0:
        try:
            tool_holder = tool_holder.faces("-Z").edges("not %Line").fillet(fillet_radius)
        except Exception as e:
            print(f"Warning: Fillet at hook base could not be applied ({e})")

    tool_holder = (
        tool_holder
        .workplaneFromTagged("back_wp")
        .pushPoints(screw_pts)
        .hole(3.6, 20.0)
        .workplaneFromTagged("back_wp")
        .workplane(offset=-8.0)
        .pushPoints(screw_pts)
        .hole(8.0, 200.0)
    )

    return tool_holder, width_units, length_units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Hook")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide (default: 1)")
    parser.add_argument("--length-units", type=int, default=4, help="Number of units long (default: 4)")
    parser.add_argument("--diameter", type=float, default=10.0, help="Diameter of the hook in mm (default: 10.0)")
    parser.add_argument("--slope", type=float, default=5.0, help="Upward slope angle in degrees (default: 5.0)")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail (default: 73.0)")
    parser.add_argument("--fillet-radius", type=float, default=3.0, help="Base fillet radius (default: 3.0)")
    parser.add_argument("--print-orientation", type=str, default="back_down", choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down"], help="Print orientation for STL export (default: back_down)")
    args = parser.parse_args()
    
    holder, wu, lu = create_hook(
        width_units=args.width_units,
        length_units=args.length_units,
        diameter=args.diameter,
        slope_deg=args.slope,
        rail_height=args.rail_height,
        fillet_radius=args.fillet_radius
    )
    
    filename = f"hook_{wu}x{lu}u_D{int(args.diameter)}mm_{int(args.slope)}deg_H{args.rail_height}.stl"
    export_model(holder, filename, category='tool_holders', print_orientation=args.print_orientation)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
