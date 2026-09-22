import cadquery as cq
import argparse
import math
import sys

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_stl

def create_v_holder(width_units=2, depth_units=4, rail_height=73.0):
    brace_thickness = 5.0
    shelf_thickness = 5.0
    
    width = width_units * UNIT_WIDTH
    shelf_depth = depth_units * UNIT_WIDTH
    
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(width_units, rail_height, mount_type="groove", num_rows=2)
    
    y_drop = width / 2.0
    y_thick = shelf_thickness * math.sqrt(2)
    shelf_top = top_y - 40.0
    
    v_pts = [
        (-width/2, shelf_top),
        (0, shelf_top - y_drop),
        (width/2, shelf_top),
        (width/2, shelf_top - y_thick),
        (0, shelf_top - y_drop - y_thick),
        (-width/2, shelf_top - y_thick)
    ]
    
    shelf = (
        cq.Workplane("XY", origin=(0, 0, -BACKPLATE_THICKNESS))
        .polyline(v_pts).close()
        .extrude(-shelf_depth)
    )
    
    tool_holder = tool_holder.union(shelf)
    
    # The V-shape is structurally rigid enough that it does not need a side brace!
            
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
    export_stl(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
