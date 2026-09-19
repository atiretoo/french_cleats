import cadquery as cq
import argparse
import sys, os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import create_baseplate, export_stl, create_nut_slot

def create_shooo_cam_holder(num_tools=1, mount_type="groove"):
    # === Shooo's Mechanism Dimensions ===
    block_h = 47.63        # Height protruding from backplate
    block_y = 47.6         # Length along wall
    block_x = 12.6         # Width
    block_r = 3.81         # Vertical edge fillet radius
    gap = 26.241           # Distance between the two blocks
    
    mech_width = (num_tools + 1) * block_x + num_tools * gap
    units = max(1, math.ceil(mech_width / 28.0))
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=2)
    
    # Holes on top face
    reg_hole_dia = 4.508
    reg_hole_depth = 6.0
    m3_hole_dia = 3.4
    
    # Distances from bottom edge of the block (the side closest to the groove)
    # The user's original measurements were correctly anchored to the bottom edge!
    reg_hole_1_y_offset = 11.43
    m3_hole_y_offset = 18.587
    reg_hole_2_y_offset = 29.953
    
    # Cam Post
    post_h = 10.160
    post_r = 4.5 / 2.0
    boss_r = 5.5 / 2.0
    boss_h = 1.5
    
    # User measured 19.83mm from the "top" (groove-side) edge to the edge of the pin.
    post_y_offset = 19.83 + post_r
    
    # Post position within the gap (from left block inner face)
    post_x_from_left = 6.24
    
    # Center the mechanism on the baseplate (Between Y=0 and Y=-74 is 74mm. Center is -37)
    block_y_bot = -37.0 - (block_y / 2.0)
    
    # Calculate absolute Y positions anchored from the bottom edge
    reg_hole_1_y = block_y_bot + reg_hole_1_y_offset
    m3_hole_y = block_y_bot + m3_hole_y_offset
    reg_hole_2_y = block_y_bot + reg_hole_2_y_offset
    post_y = block_y_bot + post_y_offset
    
    start_x = - (mech_width / 2.0)
    
    top_z = -11.0 - block_h
    
    for i in range(num_tools + 1):
        x_pos = start_x + (block_x / 2.0) + i * (block_x + gap)
        
        # Block
        block = (
            cq.Workplane("XY").workplane(offset=-11.0)
            .center(x_pos, block_y_bot + block_y/2.0)
            .rect(block_x, block_y)
            .extrude(-block_h)
            .edges("|Z").fillet(block_r)
        )
        body = body.union(block)
        
        # Registration holes
        for y_pos in [reg_hole_1_y, reg_hole_2_y]:
            reg_hole = (
                cq.Workplane("XY").workplane(offset=top_z)
                .center(x_pos, y_pos)
                .circle(reg_hole_dia / 2.0)
                .extrude(reg_hole_depth)
            )
            body = body.cut(reg_hole)
            
        # M3 Bolt hole (clearance for the bolt threads to pass through)
        m3_hole = (
            cq.Workplane("XY").workplane(offset=top_z)
            .center(x_pos, m3_hole_y)
            .circle(m3_hole_dia / 2.0)
            .extrude(35.0) # Extended deep into the block for long bolts
        )
        body = body.cut(m3_hole)
        
        # M3 Captive Nut Slot (moved to 5mm from the front face)
        slot_z = top_z + 5.0
        
        slide_dir = -1.0 if i == num_tools else 1.0
        
        slot_solid = create_nut_slot("M3", depth=(block_x / 2.0) + 0.5, push_hole=True)
        plane = cq.Plane(origin=(x_pos, m3_hole_y, slot_z), xDir=(0, -slide_dir, 0), normal=(0, 0, 1))
        slot_solid = slot_solid.moved(cq.Location(plane))
        body = body.cut(slot_solid)
        
        # Add the post (except for the last iteration)
        if i < num_tools:
            post_center_x = x_pos + (block_x / 2.0) + post_x_from_left
            
            # Boss (base)
            boss = (
                cq.Workplane("XY").workplane(offset=-11.0)
                .center(post_center_x, post_y)
                .circle(boss_r)
                .extrude(-boss_h)
            )
            body = body.union(boss)
            
            # Main pin
            pin = (
                cq.Workplane("XY").workplane(offset=-11.0 - boss_h)
                .center(post_center_x, post_y)
                .circle(post_r)
                .extrude(-(post_h - boss_h))
            )
            body = body.union(pin)

    # Cut cleat mounting screws
    if screw_pts:
        screws = (
            cq.Workplane("XY").workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6/2.0)
            .extrude(-20) 
        )
        body = body.cut(screws)
        
        recesses = (
            cq.Workplane("XY").workplane(offset=-8)
            .pushPoints(screw_pts)
            .circle(8.0/2.0) 
            .extrude(-20) 
        )
        body = body.cut(recesses)
        
    if mc_solids:
        for solid in mc_solids:
            body = body.union(cq.Workplane(solid))
            
    return body

def add_support_fin(holder, mech_width):
    # Rotate to back_down
    holder = holder.rotate((0,0,0), (1,0,0), 180)
    
    # Tilt 45 degrees around Y-axis (stands on left edge -X)
    holder = holder.rotate((0,0,0), (0,1,0), -45)
    
    bb = holder.val().BoundingBox()
    z_bed = bb.zmin
    
    # Calculate exact X boundaries of the baseplate after -45 deg Y rotation
    import math
    cos45 = math.cos(math.radians(-45))
    X_min = (-mech_width / 2.0) * cos45 + 1.0 # 1mm buffer from left edge
    X_max = (mech_width / 2.0) * cos45 - 1.0  # 1mm buffer from right edge
    
    # The fin profile matches Z = X plane (where the backplate is after rotation)
    # We leave a 0.2mm gap for breakaway support.
    # Using 'ZX' workplane (Local X = Global Z, Local Y = Global X). Extrusion goes to +Y.
    pts = [
        (z_bed, X_min),
        (z_bed, X_max),
        (X_max - 0.2, X_max),
        (X_min - 0.2, X_min)
    ]
    
    # We will put 3 fins along the Y axis to keep it stable
    fins = []
    # Baseplate Y spans roughly -74 to +20. Center is around -27.
    y_positions = [-60.0, -27.0, 6.0]
    
    for y in y_positions:
        fin = (
            cq.Workplane("ZX")
            .polyline(pts).close()
            .extrude(0.8)
            .translate((0, y, 0))
        )
        fins.append(fin)
        
    for fin in fins:
        holder = holder.union(fin)
        
    return holder

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Shooo cam mechanism holder.")
    parser.add_argument("--tools", type=int, default=1, help="Number of tools to hold")
    parser.add_argument("--mount", type=str, default="groove", choices=["groove", "multiconnect", "hybrid"], help="Mount type")
    parser.add_argument("--tilt-fin", action="store_true", help="Rotate 45 degrees and model a support fin (avoids horizontal bridge sagging in nut slots)")
    args = parser.parse_args()

    holder = create_shooo_cam_holder(num_tools=args.tools, mount_type=args.mount)
    
    # mech_width calculation is the same as inside create_shooo_cam_holder
    mech_width = (args.tools + 1) * 12.6 + args.tools * 26.241
    units = math.ceil(mech_width / 28.0)
    
    if args.tilt_fin:
        holder = add_support_fin(holder, mech_width)
        filename = f"shooo_cam_holder_{args.tools}tools_{units}u_{args.mount}_45deg.stl"
        export_stl(holder, filename, print_orientation="face_down", category="tool_holders")
    else:
        filename = f"shooo_cam_holder_{args.tools}tools_{units}u_{args.mount}.stl"
        export_stl(holder, filename, print_orientation="back_down", category="tool_holders")
