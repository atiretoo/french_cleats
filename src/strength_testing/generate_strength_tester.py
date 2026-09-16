import cadquery as cq
import argparse

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import create_baseplate, export_stl

def create_strength_tester(shelf_position="top", thickness_mode="full", rail_height=73.0, mount_type="groove"):
    units = 1
    unit_width = 28.0 
    width = units * unit_width
    shelf_u = 6
    shelf_depth = shelf_u * unit_width 
    
    if thickness_mode == "ultra_thin":
        backplate_t = 5.5
        shelf_t = 2.0
        brace_t = 1.0
    elif thickness_mode == "half":
        backplate_t = 5.5
        shelf_t = 5.0
        brace_t = 2.5
    else:
        backplate_t = 11.0
        shelf_t = 10.0
        brace_t = 5.0
        
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(units, rail_height, backplate_thickness=backplate_t, mount_type=mount_type, num_rows=5)
    
    if shelf_position == "top":
        shelf_top_y = top_y - 14.0 # Keep it below the top edge to allow filleting
    else:
        shelf_top_y = top_y - 40.0
        
    shelf_bottom_y = shelf_top_y - shelf_t
    
    shelf_pts = [
        (shelf_bottom_y, -backplate_t),
        (shelf_bottom_y, -backplate_t - shelf_depth),
        (shelf_top_y, -backplate_t - shelf_depth),
        (shelf_top_y, -backplate_t)
    ]
    shelf = (
        cq.Workplane("YZ")
        .polyline(shelf_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    tool_holder = tool_holder.union(shelf)
    
    brace_height = shelf_bottom_y - bottom_y
    brace_bottom_y = bottom_y
    
    brace_pts = [
        (brace_bottom_y, -backplate_t),
        (shelf_bottom_y, -backplate_t),
        (shelf_bottom_y, -backplate_t - shelf_depth)
    ]
    brace = (
        cq.Workplane("YZ")
        .polyline(brace_pts).close()
        .extrude(brace_t)
        .translate((-width/2, 0, 0)) 
    )
    tool_holder = tool_holder.union(brace)
    
    # --- TRUSS CUTOUT ---
    strut_width = 15.0 # Using 15mm to ensure it fits nicely in both top and mid models
    try:
        cutout = (
            cq.Workplane("YZ")
            .polyline(brace_pts).close()
            .offset2D(-strut_width)
            .extrude(brace_t + 2.0)
            .translate((-width/2 - 1.0, 0, 0))
        )
        cutout = cutout.edges('|X').fillet(8.0)
        tool_holder = tool_holder.cut(cutout)
    except Exception as e:
        print("Truss cutout failed:", e)
    
    brace_inner_x = -width/2 + brace_t
    
    class FilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge): continue
                b = o.BoundingBox()
                if abs(b.ymin - shelf_top_y) < 1 and abs(b.zmin - (-backplate_t)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
                elif abs(b.ymin - shelf_bottom_y) < 1 and abs(b.zmin - (-backplate_t)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
                elif abs(b.xmin - brace_inner_x) < 1 and abs(b.ymin - shelf_bottom_y) < 1 and b.zmax - b.zmin > 10:
                    res.append(o)
                elif abs(b.xmin - brace_inner_x) < 1 and abs(b.zmin - (-backplate_t)) < 1 and b.ymax - b.ymin > 10:
                    res.append(o)
            return res

    # Fillet removed to prevent gmsh artifacts
    
    hole_z = -backplate_t - shelf_depth + 10.0 
    hole = (
        cq.Workplane("XZ", origin=(0, shelf_top_y + 1, 0))
        .center(0, hole_z) 
        .circle(5.0/2)
        .extrude(shelf_t + 2) 
    )
    tool_holder = tool_holder.cut(hole)
    
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
            .extrude(-(backplate_t - 8 + 20.0)) 
        )
        tool_holder = tool_holder.cut(recesses)
        
    for s in slots_to_cut:
        tool_holder = tool_holder.union(s)
    
    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate strength testers")
    parser.add_argument("--mount", choices=["groove", "multiconnect"], default="groove", help="Mount type")
    args = parser.parse_args()
    
    import os
    if not os.path.exists("strength_testing"):
        os.makedirs("strength_testing")
        
    for pos in ["top", "mid"]:
        for thick in ["full", "half"]:
            holder = create_strength_tester(pos, thick, mount_type=args.mount)
            filename = f"tester_{pos}_{thick}_{args.mount}.stl"
            export_stl(holder, filename, category='strength_testing', export_step=False)
            print(f"Exported {filename}")

if __name__ == "__main__":
    main()
