import cadquery as cq
import os
import sys

# Add the src directory to the path so we can import core_library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_library import export_stl

def create_classic_hook_test():
    width = 20.0
    plate_thickness = 6.0
    
    top_y = 20.0
    top_hook_y = 5.5
    bottom_peg_y = 5.5 - 25.4
    bottom_y = bottom_peg_y - 10.0
    
    # 1. Base plate
    plate_h = top_y - bottom_y
    plate_center_y = bottom_y + plate_h/2
    base = cq.Workplane("XY").center(0, plate_center_y).box(width, plate_h, plate_thickness, centered=(True, True, False))
    
    # Top hook dia = 4.2 ensures that even at a 45 degree tilt during insertion, 
    # its vertical footprint (4.2 * 1.414 = 5.94mm) easily clears a 6.35mm hole.
    top_hook_dia = 4.2
    bot_peg_dia = 5.5
    
    embed_z = plate_thickness / 2.0
    
    # 2. Top Hook
    # Segment 1: Straight Z out to 6.0mm past the back of the plate
    L1 = (plate_thickness - embed_z) + 6.0
    dir1 = cq.Vector(0, 0, 1)
    p0 = cq.Vector(0, top_hook_y, embed_z)
    p1 = p0 + dir1 * L1
    
    cyl1 = cq.Solid.makeCylinder(top_hook_dia/2, L1, p0, dir1)
    
    # Segment 2: 45 degrees up (+Y, +Z)
    L2 = 12.0
    dir2 = cq.Vector(0, 1, 1).normalized()
    p2 = p1 + dir2 * L2
    
    cyl2 = cq.Solid.makeCylinder(top_hook_dia/2, L2, p1, dir2)
    
    sph1 = cq.Solid.makeSphere(top_hook_dia/2, p1, cq.Vector(0,0,1), -90)
    sph2 = cq.Solid.makeSphere(top_hook_dia/2, p2, cq.Vector(0,0,1), -90)
    
    top_hook = cq.Workplane(cyl1).union(cq.Workplane(cyl2)).union(cq.Workplane(sph1)).union(cq.Workplane(sph2))
    
    # 3. Bottom Peg
    bot_p0 = cq.Vector(0, bottom_peg_y, embed_z)
    bot_dir = cq.Vector(0, 0, 1)
    bot_L = (plate_thickness - embed_z) + 5.0
    bot_p1 = bot_p0 + bot_dir * bot_L
    
    bot_cyl = cq.Solid.makeCylinder(bot_peg_dia/2, bot_L, bot_p0, bot_dir)
    bot_sph = cq.Solid.makeSphere(bot_peg_dia/2, bot_p1, cq.Vector(0,0,1), -90)
    
    bottom_peg = cq.Workplane(bot_cyl).union(cq.Workplane(bot_sph))
    
    result = base.union(top_hook).union(bottom_peg)
    
    # Add the 45 degree chamfer so it prints like the final one!
    right_cut_pts = [
        (width/2, plate_thickness),                  
        (width/2 - 50, plate_thickness - 50),        
        (width/2 + 50, plate_thickness - 50),        
        (width/2 + 50, plate_thickness)              
    ]
    right_cutter = cq.Workplane("XZ").polyline(right_cut_pts).close().extrude(1000, both=True)
    
    left_cut_pts = [
        (-width/2, plate_thickness),                 
        (-width/2 + 50, plate_thickness - 50),       
        (-width/2 - 50, plate_thickness - 50),       
        (-width/2 - 50, plate_thickness)             
    ]
    left_cutter = cq.Workplane("XZ").polyline(left_cut_pts).close().extrude(1000, both=True)
    
    result = result.cut(right_cutter).cut(left_cutter)
    
    # Rotate for face_down export
    result = result.rotate((0,0,0), (0,1,0), 45)
    
    return result

def main():
    model = create_classic_hook_test()
    filename = "classic_hook_test_coupon.stl"
    export_stl(model, filename, category='pegboard_tests', print_orientation='face_down')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
