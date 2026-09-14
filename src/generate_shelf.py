import cadquery as cq
import argparse

from holder_base import create_baseplate

def make_gridfinity_cutout():
    """
    Creates a single Gridfinity baseplate cutout (negative geometry).
    """
    cutout = (
        cq.Workplane("XY")
        .rect(42.0, 42.0)
        .extrude(2.15, taper=45)
        .faces(">Z")
        .extrude(1.8)
        .faces(">Z")
        .extrude(0.7, taper=45)
    )
    return cutout

def create_shelf(width_units=3, depth_units=3, gridfinity=True, rail_height=73.0):
    unit_width = 28.0
    width = width_units * unit_width
    shelf_depth = depth_units * unit_width
    shelf_thickness = 7.0
    brace_thickness = 5.0
    
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(
        width_units, rail_height, mount_type="groove", num_rows=2
    )
    
    # Position shelf 1/3 of the way from the bottom to the top
    # Total height from bottom_y to top_y
    total_height = top_y - bottom_y
    shelf_top = bottom_y + total_height / 3.0
    shelf_bot = shelf_top - shelf_thickness
    
    # 1. Add the main shelf slab
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
    
    # 2. Add the triangular braces underneath
    # Brace goes from the bottom of the baseplate to the bottom of the shelf,
    # and extends to the front of the shelf.
    brace_pts = [
        (bottom_y, -11),
        (shelf_bot, -11),
        (shelf_bot, -11 - shelf_depth)
    ]
    
    # Left brace
    left_brace = (
        cq.Workplane("YZ")
        .polyline(brace_pts).close()
        .extrude(brace_thickness)
        .translate((-width/2, 0, 0))
    )
    # Right brace
    right_brace = (
        cq.Workplane("YZ")
        .polyline(brace_pts).close()
        .extrude(brace_thickness)
        .translate((width/2 - brace_thickness, 0, 0))
    )
    
    tool_holder = tool_holder.union(left_brace).union(right_brace)
    
    # 3. Add Gridfinity Baseplate geometry on top of the shelf
    if gridfinity:
        gf_cutout = make_gridfinity_cutout()
        
        num_x = int(width / 42.0)
        num_z = int(shelf_depth / 42.0)
        
        for ix in range(num_x):
            for iz in range(num_z):
                # Calculate center positions
                cx = (ix - num_x / 2.0 + 0.5) * 42.0
                cz = -11.0 - shelf_depth / 2.0 + (iz - num_z / 2.0 + 0.5) * 42.0
                
                # The GF cutout is built in +Z. We want to cut DOWN into the shelf (-Y).
                # Rotate around X-axis by 90 degrees maps +Z to -Y.
                inst = (
                    gf_cutout
                    .rotate((0,0,0), (1,0,0), 90)
                    .translate((cx, shelf_top, cz))
                )
                tool_holder = tool_holder.cut(inst)
                
    # Cut screws
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
    parser = argparse.ArgumentParser(description="Generate French Cleat Shelf")
    parser.add_argument("--width-units", type=int, default=3, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=3, help="Number of units deep")
    parser.add_argument("--no-gridfinity", action="store_true", help="Disable Gridfinity baseplate geometry")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    args = parser.parse_args()
    
    holder, fw, fd = create_shelf(
        width_units=args.width_units, 
        depth_units=args.depth_units,
        gridfinity=not args.no_gridfinity,
        rail_height=args.rail_height
    )
    
    gf_str = "_GF" if not args.no_gridfinity else ""
    filename = f"shelf_{fw}x{fd}u{gf_str}_groove_H{args.rail_height}.stl"
    cq.exporters.export(holder, filename)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
