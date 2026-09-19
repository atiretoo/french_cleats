import cadquery as cq
import argparse

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import create_baseplate, export_stl

import math

def create_chisel_holder(num_tools=4, spacing=35.0, hole_size=15.0, hole_sizes=None, slot_width=26.0, slot_widths=None, slot_depth=4.0, slot_depths=None, rail_height=73.0, shelf_pos="mid"):
    mech_width = num_tools * spacing
    units = max(1, math.ceil(mech_width / 28.0))
    unit_width = 28.0
    width = units * unit_width
    shelf_depth = 28.0 # 1U deep
    
    if not hole_sizes: hole_sizes = [hole_size] * num_tools
    if not slot_widths: slot_widths = [slot_width] * num_tools
    if not slot_depths: slot_depths = [slot_depth] * num_tools
    
    while len(hole_sizes) < num_tools: hole_sizes.append(hole_sizes[-1])
    while len(slot_widths) < num_tools: slot_widths.append(slot_widths[-1])
    while len(slot_depths) < num_tools: slot_depths.append(slot_depths[-1])
    
    # Create Baseplate
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units, rail_height, mount_type="groove", num_rows=2)
    
    if shelf_pos == "top":
        shelf_top = top_y
    else:
        shelf_top = top_y - 40.0
        
    shelf_bot = shelf_top - 5.0
    
    # Add Shelf
    shelf_pts = [
        (shelf_bot, -11),
        (shelf_bot, -11 - shelf_depth),
        (shelf_top, -11 - shelf_depth),
        (shelf_top, -11)
    ]
    shelf = (
        cq.Workplane("YZ")
        .polyline(shelf_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    tool_holder = tool_holder.union(shelf)
    
    # Fillet only the top and bottom edges of the shelf where it meets the backplate
    class FilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge): continue
                b = o.BoundingBox()
                if abs(b.ymin - shelf_top) < 1 and abs(b.zmin - (-11)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
                elif abs(b.ymin - shelf_bot) < 1 and abs(b.zmin - (-11)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
            return res

    try:
        tool_holder = tool_holder.edges(FilletSelector()).fillet(5.0)
    except:
        pass # fallback if filleting fails
    
    # Cut holes and slots independently to avoid self-intersection boolean bugs
    z_center = -11.0 - shelf_depth / 2.0
    start_x = - (mech_width / 2.0) + (spacing / 2.0)
    
    for i in range(num_tools):
        x = start_x + i * spacing
        
        hole = (
            cq.Workplane("ZX", origin=(0, shelf_bot - 10.0, 0))
            .center(x, z_center)
            .circle(hole_sizes[i] / 2.0)
            .extrude(40.0)
        )
        tool_holder = tool_holder.cut(hole)
        
        slot = (
            cq.Workplane("ZX", origin=(0, shelf_bot - 10.0, 0))
            .center(x, z_center)
            .rect(slot_widths[i], slot_depths[i])
            .extrude(40.0)
        )
        tool_holder = tool_holder.cut(slot)
    
    # Cut screws
    if screw_pts:
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
        
    if mc_solids:
        for solid in mc_solids:
            tool_holder = tool_holder.union(cq.Workplane(solid))
            
    return tool_holder

def parse_list(s):
    if not s:
        return None
    return [float(x.strip()) for x in s.split(',')]

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat chisel holder")
    parser.add_argument("--tools", type=int, default=4, help="Number of chisels to hold")
    parser.add_argument("--spacing", type=float, default=35.0, help="Spacing between slot centers in mm")
    parser.add_argument("--hole-size", type=float, default=15.0, help="Diameter of the central hole in mm")
    parser.add_argument("--hole-sizes", type=parse_list, default=None, help="Comma separated hole diameters in mm")
    parser.add_argument("--slot-width", type=float, default=26.0, help="Width of the slot in mm")
    parser.add_argument("--slot-widths", type=parse_list, default=None, help="Comma separated slot widths in mm")
    parser.add_argument("--slot-depth", type=float, default=4.0, help="Depth of the slot in mm")
    parser.add_argument("--slot-depths", type=parse_list, default=None, help="Comma separated slot depths in mm")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--shelf-pos", choices=["mid", "top"], default="mid", help="Position of the shelf on the backplate")
    args = parser.parse_args()
    
    holder = create_chisel_holder(
        num_tools=args.tools, 
        spacing=args.spacing,
        hole_size=args.hole_size, 
        hole_sizes=args.hole_sizes,
        slot_width=args.slot_width,
        slot_widths=args.slot_widths,
        slot_depth=args.slot_depth,
        slot_depths=args.slot_depths,
        rail_height=args.rail_height,
        shelf_pos=args.shelf_pos
    )
    
    sd_str = "_VAR" if args.slot_depths else ""
    sw_str = "_VAR" if args.slot_widths else ""
    hs_str = "_VAR" if args.hole_sizes else ""
    
    mech_width = args.tools * args.spacing
    units = max(1, math.ceil(mech_width / 28.0))
    
    filename = f"chisel_holder_{args.tools}tools_{units}u_{args.shelf_pos}_groove_H{args.rail_height}{sd_str}{sw_str}{hs_str}.stl"
    export_stl(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
