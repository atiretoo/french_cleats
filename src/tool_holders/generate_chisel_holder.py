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

import math

def create_chisel_holder(num_tools=4, spacing=35.0, hole_size=15.0, hole_sizes=None, slot_width=26.0, slot_widths=None, slot_depth=4.0, slot_depths=None, rail_height=73.0, shelf_pos="mid", shelf_depth=38.0, chamfer_depth=2.0, chamfer_angle=60.0):
    mech_width = num_tools * spacing
    units = max(1, math.ceil(mech_width / 28.0))
    width = units * UNIT_WIDTH
    
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
    tool_holder = tool_holder.union(shelf)
    
    # Fillet only the top and bottom edges of the shelf where it meets the backplate
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
        pass # fallback if filleting fails
    
    # Cut holes and slots independently to avoid self-intersection boolean bugs
    z_center = -BACKPLATE_THICKNESS - shelf_depth / 2.0
    start_x = - (mech_width / 2.0) + (spacing / 2.0)
    
    for i in range(num_tools):
        x = start_x + i * spacing
        
        hole = (
            cq.Workplane("ZX", origin=(0, shelf_bot - 10.0, 0))
            .center(z_center, x)
            .circle(hole_sizes[i] / 2.0)
            .extrude(40.0)
        )
        tool_holder = tool_holder.cut(hole)
        
        slot = (
            cq.Workplane("ZX", origin=(0, shelf_bot - 10.0, 0))
            .center(z_center, x)
            .rect(slot_depths[i], slot_widths[i])
            .extrude(40.0)
        )
        tool_holder = tool_holder.cut(slot)
        
        if chamfer_depth > 0:
            extra = 1.0
            r_bot = hole_sizes[i] / 2.0
            half_angle = chamfer_angle / 2.0
            r_top = r_bot + chamfer_depth * math.tan(math.radians(half_angle))
            r_extra = r_top + extra * math.tan(math.radians(half_angle))
            
            chamfer_cone = cq.Solid.makeCone(
                radius1=r_bot,
                radius2=r_extra,
                height=chamfer_depth + extra,
                pnt=(x, shelf_top - chamfer_depth, z_center),
                dir=(0, 1, 0)
            )
            tool_holder = tool_holder.cut(chamfer_cone)
    
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
    parser.add_argument("--shelf-depth", type=float, default=38.0, help="Depth of the shelf in mm")
    parser.add_argument("--chamfer-depth", type=float, default=2.0, help="Depth of the hole chamfer in mm")
    parser.add_argument("--chamfer-angle", type=float, default=60.0, help="Angle of the hole chamfer in degrees")
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
        shelf_pos=args.shelf_pos,
        shelf_depth=args.shelf_depth,
        chamfer_depth=args.chamfer_depth,
        chamfer_angle=args.chamfer_angle
    )
    
    sd_str = "_VAR" if args.slot_depths else ""
    sw_str = "_VAR" if args.slot_widths else ""
    hs_str = "_VAR" if args.hole_sizes else ""
    
    mech_width = args.tools * args.spacing
    units = max(1, math.ceil(mech_width / 28.0))
    
    filename = f"chisel_holder_{args.tools}tools_{units}u_{args.shelf_pos}_groove_H{args.rail_height}{sd_str}{sw_str}{hs_str}.stl"
    export_model(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
