import cadquery as cq
import argparse
import sys, os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import create_baseplate, export_stl, create_nut_slot

def create_cam_holder(units=1, mount_type="groove"):
    unit_width = 28.0
    width = units * unit_width
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=2)
    
    # U-channel extending from baseplate
    # Left and right walls sticking out to Z = -25.0
    # But they must leave a 2.5mm slit behind them so a wide saw blade can pass through!
    # Baseplate front is at Z = -11.0. Slit goes from Z = -11.0 to -13.5.
    # The walls start at Z = -13.5 and go to -25.0.
    # To support the walls, they connect to the baseplate at the top (Y = 10 to 20).
    
    gap = 12.0
    wall_thickness = 5.0
    
    # Top support block (connects walls to baseplate)
    # Z from -11.0 to -13.5
    # Y from 10.0 to 20.0
    support = (
        cq.Workplane("XY").workplane(offset=-11.0)
        .center(0, 15.0)
        .rect(width, 10.0)
        .extrude(-2.5) # out to -13.5
    )
    body = body.union(support)
    
    # Left wall (starts from -13.5, goes to -25.0)
    # Y from 20.0 to -20.0
    wall_h = 40.0
    left_wall = (
        cq.Workplane("XY").workplane(offset=-13.5)
        .center(-gap/2.0 - wall_thickness/2.0, top_y - wall_h/2.0)
        .rect(wall_thickness, wall_h)
        .extrude(-11.5)
    )
    # Right wall
    right_wall = (
        cq.Workplane("XY").workplane(offset=-13.5)
        .center(gap/2.0 + wall_thickness/2.0, top_y - wall_h/2.0)
        .rect(wall_thickness, wall_h)
        .extrude(-11.5)
    )
    
    body = body.union(left_wall).union(right_wall)
    
    # Axle hole
    # Across both walls, at Y = 0, Z = -20.0
    # Center is at X=0, Y=0, Z=-20.0
    # We want a 3.4mm clearance hole for M3
    axle_hole = (
        cq.Workplane("YZ").workplane(offset=-20.0) # wait, YZ origin=(0,0,0) offset means X
        # actually, just create a cylinder
    )
    
    axle_hole = (
        cq.Workplane("YZ", origin=(0, 0, -20.0))
        .circle(3.4 / 2.0)
        .extrude(20.0, both=True) # cut through both walls
    )
    body = body.cut(axle_hole)
    
    # Add an M3 captive nut slot on the right wall!
    # The axle goes through the left wall, spans the gap, goes through the right wall, and threads into a nut on the right wall.
    # Wait, it's easier to just tap the plastic, or use a nut slot.
    # If the right wall is from X = 6 to 11. The nut should sit on the outside of the right wall?
    # Actually, the user can just use an M3 nut and washer on the outside.
    # Let's add a nut slot just to be nice.
    # The bolt passes through X axis.
    # Right wall outside is at X = 11.
    slot_solid = create_nut_slot("M3", depth=5.0, push_hole=False)
    # create_nut_slot: Z is bolt axis, Y is slide direction.
    # We want bolt along X. Slide from the top (-Y direction?).
    # If slide is from top (global -Y), we need to map:
    # local Z (bolt) -> global X
    # local Y (slide) -> global -Y
    plane = cq.Plane(origin=(11.0, 0, -20.0), xDir=(0, 0, 1), normal=(1, 0, 0))
    # Wait, Y_dir = normal x xDir = (1, 0, 0) x (0, 0, 1) = (0, -1, 0) (which is global -Y).
    # This means the nut slides in from global +Y (the top)! Perfect!
    slot_solid = slot_solid.moved(cq.Location(plane))
    body = body.cut(slot_solid)
    
    # Cut screws for cleat mounting
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

def create_cam():
    # Gap is 12mm, so make the cam 11mm thick.
    cam_t = 11.0
    
    # Cylinder radius 8mm (16mm diameter)
    # Axle offset 2.5mm
    # So max radius = 10.5mm, min radius = 5.5mm
    cam = (
        cq.Workplane("XY")
        .circle(8.0)
        .extrude(cam_t)
    )
    
    # Cut axle hole at offset (0, 2.5)
    # The axle is 3.4mm clearance, wait, the cam needs to rotate freely on the M3 bolt.
    # 3.4mm is good.
    hole = (
        cq.Workplane("XY")
        .center(0, 2.5)
        .circle(3.4 / 2.0)
        .extrude(cam_t)
    )
    cam = cam.cut(hole)
    
    return cam

if __name__ == "__main__":
    holder = create_cam_holder(units=1, mount_type="groove")
    filename = "cam_saw_holder_1u_groove.stl"
    export_stl(holder, filename, category="tool_holders")
    
    cam = create_cam()
    cam_filename = "cam_saw_holder_cam.stl"
    export_stl(cam, cam_filename, category="tool_holders", rotate_for_printing=False)
