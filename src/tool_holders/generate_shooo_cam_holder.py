import cadquery as cq
import argparse
import sys, os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import create_baseplate, export_stl, create_nut_slot

def create_shooo_cam_holder(num_tools=1, mount_type="groove"):
    # === Shooo's Mechanism Dimensions ===
    block_h = 47.65        # Height protruding from backplate
    block_y = 40.113       # Length along wall
    block_x = 12.7         # Width
    block_r = 3.81         # Vertical edge fillet radius
    gap = 26.241           # Distance between the two blocks
    
    mech_width = (num_tools + 1) * block_x + num_tools * gap
    units = math.ceil(mech_width / 28.0)
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=2)
    
    # Holes on top face
    reg_hole_dia = 4.508
    reg_hole_depth = 6.0
    m3_hole_dia = 3.4
    
    # Distances from bottom edge of the block
    reg_hole_1_y = 9.176 + (reg_hole_dia / 2.0)  # 11.43
    m3_hole_y = 18.587
    reg_hole_2_y = reg_hole_1_y + 14.015 + reg_hole_dia  # 29.953
    
    # Cam Post
    post_h = 10.160
    post_r = 4.5 / 2.0
    boss_r = 5.5 / 2.0
    boss_h = 1.5
    
    # Post position within the gap (from left block inner face)
    post_x_from_left = 6.24
    
    # Center the mechanism on the baseplate
    block_y_bot = -40.113
    block_y_top = 0.0
    post_y = block_y_bot + (block_y / 2.0)
    
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
        for y_offset in [reg_hole_1_y, reg_hole_2_y]:
            y_pos = block_y_bot + y_offset
            reg_hole = (
                cq.Workplane("XY").workplane(offset=top_z)
                .center(x_pos, y_pos)
                .circle(reg_hole_dia / 2.0)
                .extrude(reg_hole_depth)
            )
            body = body.cut(reg_hole)
            
        # M3 Bolt hole
        m3_y_pos = block_y_bot + m3_hole_y
        m3_hole = (
            cq.Workplane("XY").workplane(offset=top_z)
            .center(x_pos, m3_y_pos)
            .circle(m3_hole_dia / 2.0)
            .extrude(20.0)
        )
        body = body.cut(m3_hole)
        
        # M3 Captive Nut Slot
        slot_z = top_z + 15.0
        # Determine slide direction: if i == num_tools, it's the rightmost block, slide from +X.
        # Otherwise, slide from -X (so it slides from inside the gap, or from far left).
        # Wait, if we slide from inside the gap, the tool handle might interfere?
        # A screwdriver or paperclip goes in from the outside. 
        # For the first block (i=0), outside is -X.
        # For the last block (i=num_tools), outside is +X.
        # For middle blocks, it doesn't matter much, let's slide from -X.
        slide_dir = -1.0 if i == num_tools else 1.0
        
        slot_solid = create_nut_slot("M3", depth=(block_x / 2.0) + 0.5, push_hole=True)
        plane = cq.Plane(origin=(x_pos, m3_y_pos, slot_z), xDir=(0, -slide_dir, 0), normal=(0, 0, 1))
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Shooo cam mechanism holder.")
    parser.add_argument("--tools", type=int, default=1, help="Number of tools to hold")
    parser.add_argument("--mount", type=str, default="groove", choices=["groove", "multiconnect", "hybrid"], help="Mount type")
    args = parser.parse_args()

    holder = create_shooo_cam_holder(num_tools=args.tools, mount_type=args.mount)
    units = math.ceil(((args.tools + 1) * 12.7 + args.tools * 26.241) / 28.0)
    
    filename = f"shooo_cam_holder_{args.tools}tools_{units}u_{args.mount}.stl"
    export_stl(holder, filename, category="tool_holders")
