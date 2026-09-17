import cadquery as cq
import argparse
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import create_baseplate, export_stl

def create_magnetic_holder(units=1, mount_type="groove"):
    unit_width = 28.0
    width = units * unit_width
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=2)
    
    # Block extending from baseplate
    # From Z = -11.0 to Z = -20.0
    # From Y = top_y (20) to Y = -40
    block_h = 60.0
    block_t = 9.0
    block = (
        cq.Workplane("XY").workplane(offset=-11.0)
        .center(0, top_y - block_h/2.0)
        .box(width, block_h, block_t, centered=(True, True, False))
    )
    # The box extrudes in +Z if centered=(..., False). We want -Z.
    # Actually, .extrude is easier.
    block = (
        cq.Workplane("XY").workplane(offset=-11.0)
        .center(0, top_y - block_h/2.0)
        .rect(width, block_h)
        .extrude(-block_t)
    )
    body = body.union(block)
    
    # Trench for the blade
    # 20mm wide, 1mm deep (from Z = -20.0 to Z = -19.0)
    trench = (
        cq.Workplane("XY").workplane(offset=-20.0)
        .center(0, top_y - block_h/2.0)
        .rect(20.0, block_h)
        .extrude(1.0) # Extrude into the block (+Z)
    )
    body = body.cut(trench)
    
    # Magnets
    # 10.2mm diameter, 2.0mm depth.
    # Placed at Y = 10 and Y = -10 (or top_y - 15, top_y - 45)
    mag_y1 = top_y - 15.0
    mag_y2 = top_y - 45.0
    
    mags = (
        cq.Workplane("XY").workplane(offset=-19.0) # Base of the trench
        .pushPoints([(0, mag_y1), (0, mag_y2)])
        .circle(10.2 / 2.0)
        .extrude(2.0) # Cut into the block (+Z)
    )
    body = body.cut(mags)
    
    # Push holes
    # 2mm diameter, all the way through to the back
    push_holes = (
        cq.Workplane("XY").workplane(offset=-19.0)
        .pushPoints([(0, mag_y1), (0, mag_y2)])
        .circle(2.0 / 2.0)
        .extrude(20.0) # All the way to +Z
    )
    body = body.cut(push_holes)
    
    # Cut screws
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
    holder = create_magnetic_holder(units=1, mount_type="groove")
    filename = "magnetic_saw_holder_1u_groove.stl"
    export_stl(holder, filename, category="tool_holders")
