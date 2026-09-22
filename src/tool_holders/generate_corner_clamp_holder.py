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
from core_library import create_baseplate, export_stl

def create_corner_clamp_holder(width_units=1, depth_units=5, num_slots=4, slot_width=10.0, 
                               slot_spacing=30.0, start_clearance=15.0, groove_depth=15.0, 
                               chord=134.9375, arc_height=19.05, rail_height=73.0):
    
    unit_width = 28.0
    width = width_units * unit_width
    shelf_depth = depth_units * unit_width
    
    # Calculate arc radius from measured chord and height
    arc_radius = (chord**2 / (8 * arc_height)) + (arc_height / 2)
    
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(
        width_units, rail_height, mount_type="groove", num_rows=2
    )
    
    shelf_top = top_y - 40.0
    
    # V-trough geometry
    y_drop = width / 2.0  # 90-degree inner V means slope is 1, so drop is half width
    v_inner_bottom = shelf_top - y_drop
    
    # The groove dips below the inner V by groove_depth
    arc_bottom_y = v_inner_bottom - groove_depth
    
    # Ensure there is 5mm of solid plastic spine below the deepest part of the groove
    # Now that the bottom is full-width, this provides massive strength!
    v_outer_bottom = arc_bottom_y - 5.0
    
    v_pts = [
        (-width/2, shelf_top),
        (0, v_inner_bottom),
        (width/2, shelf_top),
        (width/2, v_outer_bottom),
        (-width/2, v_outer_bottom)
    ]
    
    # Baseplate face is at Z = -11
    shelf = (
        cq.Workplane("XY", origin=(0, 0, -11))
        .polyline(v_pts).close()
        .extrude(-shelf_depth)
    )
    
    tool_holder = tool_holder.union(shelf)
    
    # Calculate the points for the curved cutout
    # Make the cutout slightly wider than the shelf (e.g. 30mm for a 28mm half-width)
    cutout_half_width = width/2 + 2.0
    
    # Circle equation to find the rise at the edges
    rise = arc_radius - math.sqrt(arc_radius**2 - cutout_half_width**2)
    
    p1 = (-cutout_half_width, arc_bottom_y + rise)
    p2 = (0.0, arc_bottom_y)
    p3 = (cutout_half_width, arc_bottom_y + rise)
    p4 = (cutout_half_width, shelf_top + 10.0)
    p5 = (-cutout_half_width, shelf_top + 10.0)
    
    # Cut the slots
    start_z = -11.0 - start_clearance
    
    for i in range(num_slots):
        z_center = start_z - i * slot_spacing
        
        slot_cut = (
            cq.Workplane("XY", origin=(0, 0, z_center))
            .moveTo(p1[0], p1[1])
            .threePointArc(p2, p3)
            .lineTo(p4[0], p4[1])
            .lineTo(p5[0], p5[1])
            .close()
            .extrude(slot_width / 2.0, both=True)
        )
        tool_holder = tool_holder.cut(slot_cut)
    
    # Cut mounting holes
    screws = (
        cq.Workplane("XY").workplane(offset=0)
        .pushPoints(screw_pts)
        .circle(3.6/2.0)
        .extrude(-20) 
    )
    tool_holder = tool_holder.cut(screws)
    
    recesses = (
        cq.Workplane("XY").workplane(offset=-8)
        .pushPoints(screw_pts)
        .circle(8.0/2.0) 
        .extrude(-200) 
    )
    tool_holder = tool_holder.cut(recesses)
    
    return tool_holder, width_units, depth_units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Corner Clamp Holder")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=5, help="Number of units deep")
    parser.add_argument("--num-slots", type=int, default=4, help="Number of clamps to hold")
    parser.add_argument("--slot-width", type=float, default=10.0, help="Width of each slot")
    parser.add_argument("--slot-spacing", type=float, default=30.0, help="Center-to-center spacing of slots")
    parser.add_argument("--start-clearance", type=float, default=15.0, help="Distance from backplate to first slot center")
    parser.add_argument("--groove-depth", type=float, default=15.0, help="Depth of groove below the inner V bottom")
    parser.add_argument("--chord", type=float, default=134.9375, help="Chord length of the clamp curve in mm")
    parser.add_argument("--arc-height", type=float, default=19.05, help="Height of the arc from chord in mm")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    args = parser.parse_args()
    
    holder, fw, fd = create_corner_clamp_holder(
        width_units=args.width_units, 
        depth_units=args.depth_units,
        num_slots=args.num_slots,
        slot_width=args.slot_width,
        slot_spacing=args.slot_spacing,
        start_clearance=args.start_clearance,
        groove_depth=args.groove_depth,
        chord=args.chord,
        arc_height=args.arc_height,
        rail_height=args.rail_height
    )
    
    filename = f"corner_clamp_holder_{fw}x{fd}u_groove_H{args.rail_height}.stl"
    export_stl(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
