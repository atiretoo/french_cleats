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
    

    # Magnets
    # 10.2mm diameter, 2.0mm depth.
    # Center vertically between top_y (20) and bottom_y (-94). Center is -37.0.
    mag_y1 = -17.0
    mag_y2 = -57.0
    
    mags = (
        cq.Workplane("XY").workplane(offset=-11.0) # Front face of baseplate
        .pushPoints([(0, mag_y1), (0, mag_y2)])
        .circle(10.2 / 2.0)
        .extrude(2.0) # Cut into the block (+Z)
    )
    body = body.cut(mags)
    
    # Push holes
    # 2mm diameter, all the way through to the back
    push_holes = (
        cq.Workplane("XY").workplane(offset=-11.0)
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
