import cadquery as cq
import argparse

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_stl

def create_clamp_holder(units=3, rail_height=73.0, num_slots=4, mount_type="groove"):
    width = units * UNIT_WIDTH
    
    slot_spacing = 30.0
    slot_width = 7.0
    slot_depth = 15.0
    brace_thickness = 5.0
    
    shelf_depth = num_slots * slot_spacing
    
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(units, rail_height, mount_type=mount_type, num_rows=2)
    
    shelf_top = top_y - 40.0
    shelf_bot = top_y - 50.0
    
    brace_pts = [
        (bottom_y, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth)
    ]
    brace = (
        cq.Workplane("YZ")
        .polyline(brace_pts).close()
        .extrude(brace_thickness)
        .translate((-width/2, 0, 0)) 
    )
    tool_holder = tool_holder.union(brace)
    
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
    
    brace_inner_x = -width/2 + brace_thickness
    
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
                elif abs(b.xmin - brace_inner_x) < 1 and abs(b.ymin - shelf_bot) < 1 and b.zmax - b.zmin > 10:
                    res.append(o)
                elif abs(b.xmin - brace_inner_x) < 1 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1 and b.ymax - b.ymin > 10:
                    res.append(o)
            return res

    tool_holder = tool_holder.edges(FilletSelector()).fillet(5.0)
    
    cut_length = slot_depth + 5.0
    slot_x = (width/2 - slot_depth) + cut_length / 2.0
    
    slot_centers_z = [-BACKPLATE_THICKNESS - 15 - i*slot_spacing for i in range(num_slots)]
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
            cq.Workplane("XY").workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6/2)
            .extrude(-20) 
        )
        tool_holder = tool_holder.cut(screws)
        
        recesses = (
            cq.Workplane("XY").workplane(offset=-8)
            .pushPoints(screw_pts)
            .circle(8.0/2) 
            .extrude(-200) 
        )
        tool_holder = tool_holder.cut(recesses)
        
    for s in slots_to_cut:
        tool_holder = tool_holder.union(s)
    
    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat clamp holder")
    parser.add_argument("--units", type=int, default=3, help="Number of units wide")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--num-slots", type=int, default=4, help="Number of slots")
    parser.add_argument("--mount", choices=["groove", "multiconnect"], default="groove", help="Mount type")
    args = parser.parse_args()
    
    holder = create_clamp_holder(args.units, rail_height=args.rail_height, num_slots=args.num_slots, mount_type=args.mount)
    filename = f"clamp_holder_{args.units}u_{args.mount}_H{args.rail_height}_{args.num_slots}slots.stl"
    export_stl(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
