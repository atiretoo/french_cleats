import cadquery as cq
import argparse
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import create_baseplate, export_stl, create_nut_slot

def create_shooo_prototype(units=2, mount_type="groove"):
    unit_width = 28.0
    width = units * unit_width
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=2)
    
    # === Shooo's Mechanism Dimensions ===
    block_h = 47.65        # Height protruding from backplate
    block_y = 40.113       # Length along wall
    block_x = 12.7         # Width (derived from 4.096 edge to hole boundary + 2.254 hole radius)
    block_r = 3.81         # Vertical edge fillet radius
    gap = 26.221           # Distance between the two blocks
    
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
    post_r = 1.892
    # User needs to tune this position!
    post_y_from_bottom = 20.0
    
    # === Placement ===
    # Center the mechanism on the baseplate
    block_y_bot = -40.113
    block_y_top = 0.0
    
    left_x = - (gap / 2.0) - (block_x / 2.0)
    right_x = (gap / 2.0) + (block_x / 2.0)
    
    # Create the two blocks
    blocks = (
        cq.Workplane("XY").workplane(offset=-11.0)
        .pushPoints([(left_x, block_y_bot + block_y/2.0), (right_x, block_y_bot + block_y/2.0)])
        .rect(block_x, block_y)
        .extrude(-block_h)
    )
    # Fillet the vertical edges of the blocks
    # We can select the edges parallel to Z within the blocks' bounding boxes
    blocks = blocks.edges("|Z").fillet(block_r)
    body = body.union(blocks)
    
    # Cut the holes in the top faces
    top_z = -11.0 - block_h
    
    for x_pos in [left_x, right_x]:
        # Registration holes
        for y_offset in [reg_hole_1_y, reg_hole_2_y]:
            y_pos = block_y_bot + y_offset
            reg_hole = (
                cq.Workplane("XY").workplane(offset=top_z)
                .center(x_pos, y_pos)
                .circle(reg_hole_dia / 2.0)
                .extrude(reg_hole_depth) # Extrude into the block (+Z direction relative to top_z)
            )
            body = body.cut(reg_hole)
            
        # M3 Bolt hole (goes down 20mm to meet the nut slot)
        m3_y_pos = block_y_bot + m3_hole_y
        m3_hole = (
            cq.Workplane("XY").workplane(offset=top_z)
            .center(x_pos, m3_y_pos)
            .circle(m3_hole_dia / 2.0)
            .extrude(20.0)
        )
        body = body.cut(m3_hole)
        
        # M3 Captive Nut Slot
        # We put it 15mm down from the top face -> Z = top_z + 15.0
        slot_z = top_z + 15.0
        
        # We want the slot to slide in from the outside.
        # Left block: slides in from -X towards +X. So slide direction is +X.
        # Right block: slides in from +X towards -X. So slide direction is -X.
        slide_dir = 1.0 if x_pos < 0 else -1.0
        
        slot_solid = create_nut_slot("M3", depth=(block_x / 2.0) + 0.5, push_hole=True)
        
        # slot_solid has bolt along Z, slide along Y.
        # We want bolt along Z, slide along `slide_dir * X`.
        # Y_dir of plane = slide_dir * X.
        # normal = Z (0,0,1).
        # x_dir = Y_dir x normal = (slide_dir, 0, 0) x (0, 0, 1) = (0, -slide_dir, 0)
        plane = cq.Plane(origin=(x_pos, m3_y_pos, slot_z), xDir=(0, -slide_dir, 0), normal=(0, 0, 1))
        
        slot_solid = slot_solid.moved(cq.Location(plane))
        body = body.cut(slot_solid)

    # Create the cam post
    post_y = block_y_bot + post_y_from_bottom
    post = (
        cq.Workplane("XY").workplane(offset=-11.0)
        .center(0, post_y)
        .circle(post_r)
        .extrude(-post_h)
    )
    body = body.union(post)

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
    holder = create_shooo_prototype(units=2, mount_type="groove")
    filename = "shooo_cam_prototype_2u_groove.stl"
    export_stl(holder, filename, category="tool_holders")
