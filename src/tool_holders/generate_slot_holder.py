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
import sys

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_slot_holder(width_units=1, depth_units=2, slot_width=6.25, back_clearance=10.0, rail_height=73.0):
    brace_thickness = 2.5
    
    width = width_units * UNIT_WIDTH
    shelf_depth = depth_units * UNIT_WIDTH
    
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(width_units, rail_height, mount_type="groove", num_rows=2)
    
    shelf_top = top_y - 40.0
    shelf_bot = top_y - 45.0
    
    shelf_pts = [
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS)
    ]
    shelf = (
        cq.Workplane("YZ")
        .polyline(shelf_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    try:
        shelf = shelf.edges('>Y and <Z').fillet(2.0)
    except Exception:
        pass
    try:
        if width_units == 1:
            shelf = shelf.edges('>X and >Y and |Z').fillet(2.0)
    except Exception:
        pass
    tool_holder = tool_holder.union(shelf)
    
    # Braces
    brace_pts = [
        (bottom_y, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth)
    ]
    brace_x_positions = [-width/2 + brace_thickness/2]
    if width_units > 1:
        brace_x_positions.append(width/2 - brace_thickness/2)
                    
    for x_pos in brace_x_positions:
        brace = (
            cq.Workplane("YZ")
            .polyline(brace_pts).close()
            .extrude(brace_thickness)
            .translate((x_pos - brace_thickness/2.0, 0, 0))
        )
        tool_holder = tool_holder.union(brace)
        if depth_units > 2:
            try:
                cutout = (
                    cq.Workplane("YZ")
                    .polyline(brace_pts).close()
                    .offset2D(-15.0)
                    .extrude(brace_thickness + 2.0)
                    .translate((x_pos - brace_thickness/2.0 - 1.0, 0, 0))
                )
                cutout = cutout.edges('|X').fillet(8.0)
                tool_holder = tool_holder.cut(cutout)
            except Exception as e:
                pass
        
    class FilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge): continue
                b = o.BoundingBox()
                if abs(b.ymin - shelf_top) < 1 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
                elif abs(b.ymin - shelf_bot) < 1 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
            return res

    try:
        tool_holder = tool_holder.edges(FilletSelector()).fillet(5.0)
    except:
        pass
        
    # Cut the slots (1 per unit width)
    slot_length = shelf_depth - back_clearance + 5.0 # extra length to break through front edge safely
    z_center = -BACKPLATE_THICKNESS - back_clearance - slot_length / 2.0
    
    slot_pts = []
    for i in range(width_units):
        x = -width/2 + UNIT_WIDTH/2.0 + i * UNIT_WIDTH
        slot_pts.append((z_center, x))
        
    slots = (
        cq.Workplane("ZX", origin=(0, shelf_bot - 10.0, 0))
        .pushPoints(slot_pts)
        .rect(slot_length, slot_width)
        .extrude(40.0)
    )
    tool_holder = tool_holder.cut(slots)
    
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
    parser = argparse.ArgumentParser(description="Generate French Cleat slot holder")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=2, help="Number of units deep (away from wall)")
    parser.add_argument("--slot-width", type=float, default=6.25, help="Width of the slot in mm")
    parser.add_argument("--back-clearance", type=float, default=10.0, help="Distance from backplate to start of slot")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--print-orientation", type=str, default="right_down", choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down"], help="Print orientation for STL export")
    args = parser.parse_args()
    
    holder, fw, fd = create_slot_holder(
        width_units=args.width_units, 
        depth_units=args.depth_units,
        slot_width=args.slot_width,
        back_clearance=args.back_clearance,
        rail_height=args.rail_height
    )
    
    filename = f"slot_holder_{fw}x{fd}u_groove_H{args.rail_height}_W{args.slot_width}.stl"
    export_model(holder, filename, category='tool_holders', print_orientation=args.print_orientation)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
