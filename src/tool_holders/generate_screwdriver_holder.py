import cadquery as cq
import argparse
import math
import sys

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_screwdriver_holder(width_units=1, depth_units=3, hole_size=10.0, hole_spacing=25.0, num_holes=None, rail_height=73.0, hole_sizes=None, recess_size=0.0, recess_depth=1.0):
    brace_thickness = 2.5
    x_margin = 3.0
    front_margin = 3.0
    fillet_size = 5.0
    backplate_thickness = 11.0
    
    width = width_units * UNIT_WIDTH
    shelf_depth = depth_units * UNIT_WIDTH
    
    has_right_brace = width_units > 1
    
    if hole_sizes:
        actual_hole_sizes = hole_sizes
        num_holes = len(actual_hole_sizes)
        effective_max_size = max(max(actual_hole_sizes), recess_size)
    else:
        effective_max_size = max(hole_size, recess_size)
        actual_hole_sizes = [hole_size] * (num_holes if num_holes else 0)
        
    back_clearance = fillet_size + (max(actual_hole_sizes[0], recess_size) if hole_sizes else effective_max_size) / 2.0
    Z_start = -BACKPLATE_THICKNESS - back_clearance
    
    x_min = -width/2 + brace_thickness + x_margin + effective_max_size/2
    x_max = width/2 - (brace_thickness if has_right_brace else 0) - x_margin - effective_max_size/2
    dx_stagger = max(0, x_max - x_min)
    
    dz_straight = hole_spacing
    dz_stagger_diag = math.sqrt(max(0, hole_spacing**2 - dx_stagger**2)) if dx_stagger > 0 else hole_spacing
    dz_stagger = max(dz_stagger_diag, effective_max_size/2.0 + 1.0)
    
    layout = "straight"
    dz = dz_straight
    
    if not hole_sizes and num_holes is None:
        Z_end = -BACKPLATE_THICKNESS - shelf_depth + front_margin + effective_max_size / 2.0
        D_avail = abs(Z_end - Z_start) if Z_start >= Z_end else 0
        
        n_straight = int(D_avail / dz_straight) + 1 if D_avail >= 0 else 0
        n_stagger = int(D_avail / dz_stagger) + 1 if D_avail >= 0 and dx_stagger > 0 else 0
        
        if n_stagger > n_straight and dx_stagger > 0:
            layout = "staggered"
            num_holes = n_stagger
            dz = dz_stagger
        else:
            layout = "straight"
            num_holes = n_straight
            dz = dz_straight
            
        actual_hole_sizes = [hole_size] * num_holes
    else:
        # User forced num_holes or hole_sizes, calculate depth needed
        def req_depth(n, dz):
            if n <= 0: return 0
            return (n - 1) * dz + back_clearance + front_margin + effective_max_size / 2.0
            
        d_straight = req_depth(num_holes, dz_straight)
        d_stagger = req_depth(num_holes, dz_stagger) if dx_stagger > 0 else float('inf')
        
        if d_stagger <= d_straight and dx_stagger > 0:
            layout = "staggered"
            d_req = d_stagger
            dz = dz_stagger
        else:
            layout = "straight"
            d_req = d_straight
            dz = dz_straight
            
        required_depth_units = int(math.ceil(d_req / UNIT_WIDTH, BACKPLATE_THICKNESS))
        if required_depth_units > depth_units:
            print(f"Warning: {num_holes} holes would overflow the {depth_units}U depth.")
            print(f"Automatically increasing depth to {required_depth_units}U.")
            depth_units = required_depth_units
            shelf_depth = depth_units * UNIT_WIDTH

    if num_holes == 0:
        print(f"Error: Not enough depth to fit even 1 hole.")
        sys.exit(1)

    # Create Baseplate
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(width_units, rail_height, mount_type="groove", num_rows=2)
    
    shelf_top = top_y - 40.0
    shelf_bot = top_y - 45.0
    
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
    
    hole_pts = []
    
    for i in range(num_holes):
        z = Z_start - i * dz
        if layout == "staggered":
            x = x_min if i % 2 == 0 else x_max
        else:
            x = (x_min + x_max) / 2.0  
        hole_pts.append((x, z))
        
    # Add Braces
    brace_pts = [
        (bottom_y, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth)
    ]
    
    brace_x_positions = [-width/2 + brace_thickness/2]
    if has_right_brace:
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
    
    # Cut variable holes one by one
    for pt, sz in zip(hole_pts, actual_hole_sizes):
        hole = (
            cq.Workplane("ZX", origin=(0, shelf_bot - 10.0, 0))
            .center(pt[1], pt[0])
            .circle(sz/2.0)
            .extrude(40.0) 
        )
        tool_holder = tool_holder.cut(hole)
        
    # Cut recesses
    if recess_size > 0 and recess_depth > 0:
        for pt in hole_pts:
            recess = (
                cq.Workplane("ZX", origin=(0, shelf_top, 0))
                .center(pt[1], pt[0])
                .circle(recess_size/2.0)
                .extrude(-recess_depth)
            )
            tool_holder = tool_holder.cut(recess)
    
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
    parser = argparse.ArgumentParser(description="Generate French Cleat screwdriver holder")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=3, help="Number of units deep (away from wall)")
    parser.add_argument("--hole-size", type=float, default=10.0, help="Diameter of the holes in mm")
    parser.add_argument("--hole-spacing", type=float, default=25.0, help="Minimum spacing between hole centers in mm")
    parser.add_argument("--num-holes", type=int, default=None, help="Force a specific number of holes (will increase depth if needed)")
    parser.add_argument("--hole-sizes", type=str, default=None, help="Comma separated list of precise hole sizes (overrides hole-size and num-holes)")
    parser.add_argument("--recess-size", type=float, default=0.0, help="Diameter of recess at top of hole")
    parser.add_argument("--recess-depth", type=float, default=1.0, help="Depth of recess at top of hole")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    args = parser.parse_args()
    
    hole_sizes_list = None
    if args.hole_sizes:
        hole_sizes_list = [float(x.strip()) for x in args.hole_sizes.split(",")]
        
    holder, fw, fd = create_screwdriver_holder(
        width_units=args.width_units, 
        depth_units=args.depth_units,
        hole_size=args.hole_size, 
        hole_spacing=args.hole_spacing,
        num_holes=args.num_holes,
        rail_height=args.rail_height,
        hole_sizes=hole_sizes_list,
        recess_size=args.recess_size,
        recess_depth=args.recess_depth
    )
    
    if hole_sizes_list:
        filename = f"screwdriver_holder_{fw}x{fd}u_groove_H{args.rail_height}_VAR_S{args.hole_spacing}.stl"
    else:
        layout_str = f"_N{args.num_holes}" if args.num_holes is not None else ""
        filename = f"screwdriver_holder_{fw}x{fd}u_groove_H{args.rail_height}_D{args.hole_size}_S{args.hole_spacing}{layout_str}.stl"
        
    export_model(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
