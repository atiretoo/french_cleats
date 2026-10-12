import cadquery as cq
import os
import sys

# Add the src directory to the path so we can import core_library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_library import export_stl

def create_snap_fit_peg(bot_p0, bot_dir):
    # This creates the snap fit peg AT the specified location and direction.
    # We will build it at origin and then translate/rotate it.
    
    # Solid cylinder bottom 2mm (Z from 0 to 2)
    solid_cyl = cq.Solid.makeCylinder(3.25, 2.0, cq.Vector(0,0,0), cq.Vector(0,0,1))
    
    # Inner solid (R=1.75), Z from 2 to 8.25 (length 6.25)
    inner_solid = cq.Solid.makeCylinder(1.75, 6.25, cq.Vector(0,0,2), cq.Vector(0,0,1))
    
    # Tube base part: Z=2 to Z=5 (length 3.0). R_out=3.25, R_in=2.45
    tube_b_out = cq.Solid.makeCylinder(3.25, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b_in = cq.Solid.makeCylinder(2.45, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b = cq.Workplane(tube_b_out).cut(cq.Workplane(tube_b_in)).val()
    
    # Band bottom slope: Z=5 to Z=5.8 (length 0.8). R_out goes 3.25 to 4.05
    band_bs_out = cq.Solid.makeCone(3.25, 4.05, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs_in = cq.Solid.makeCylinder(2.45, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs = cq.Workplane(band_bs_out).cut(cq.Workplane(band_bs_in)).val()
    
    # Band flat: Z=5.8 to Z=7.2 (length 1.4). R_out=4.05
    band_f_out = cq.Solid.makeCylinder(4.05, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f_in = cq.Solid.makeCylinder(2.45, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f = cq.Workplane(band_f_out).cut(cq.Workplane(band_f_in)).val()
    
    # Band top slope: Z=7.2 to Z=8.0 (length 0.8). R_out goes 4.05 to 3.25
    band_ts_out = cq.Solid.makeCone(4.05, 3.25, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts_in = cq.Solid.makeCylinder(2.45, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts = cq.Workplane(band_ts_out).cut(cq.Workplane(band_ts_in)).val()
    
    # Tube top part: Z=8.0 to Z=8.25 (length 0.25). R_out=3.25
    tube_t_out = cq.Solid.makeCylinder(3.25, 0.25, cq.Vector(0,0,8.0), cq.Vector(0,0,1))
    tube_t_in = cq.Solid.makeCylinder(2.45, 0.25, cq.Vector(0,0,8.0), cq.Vector(0,0,1))
    tube_t = cq.Workplane(tube_t_out).cut(cq.Workplane(tube_t_in)).val()
    
    outer_tube = cq.Workplane(tube_b).union(cq.Workplane(band_bs)).union(cq.Workplane(band_f)).union(cq.Workplane(band_ts)).union(cq.Workplane(tube_t))
    
    # Split the tube portion into 6 pieces
    # Slits go from Z=2.0 to Z=10.0. Width 0.8mm for better clearance against blobbing
    c1 = cq.Workplane("XY").workplane(offset=2.0).box(0.8, 20, 8.0, centered=(True, True, False))
    c2 = cq.Workplane("XY").workplane(offset=2.0).box(0.8, 20, 8.0, centered=(True, True, False)).rotate((0,0,0), (0,0,1), 60)
    c3 = cq.Workplane("XY").workplane(offset=2.0).box(0.8, 20, 8.0, centered=(True, True, False)).rotate((0,0,0), (0,0,1), 120)
    
    outer_tube = outer_tube.cut(c1).cut(c2).cut(c3)
    
    snap_peg = cq.Workplane(solid_cyl).union(cq.Workplane(inner_solid)).union(outer_tube)
    
    # Move it to the requested location
    # Note: the test coupons all point in +Z, so bot_dir is always (0,0,1)
    # We just need to translate it to bot_p0
    snap_peg = snap_peg.translate(bot_p0)
    
    return snap_peg

def create_base_plate():
    width = 20.0
    plate_thickness = 6.0
    top_y = 20.0
    bottom_peg_y = 5.5 - 25.4
    bottom_y = bottom_peg_y - 10.0
    
    from pegboard.coupon_utils import create_test_coupon_base
    return create_test_coupon_base(width, plate_thickness, top_y, bottom_y)

def create_v1_full_snap():
    base = create_base_plate()
    plate_thickness = 6.0
    embed_z = plate_thickness / 2.0
    top_hook_y = 5.5
    bottom_peg_y = 5.5 - 25.4
    
    # Top Hook: V1 Full Size
    L1 = (plate_thickness - embed_z) + 5.0  # 5mm straight section
    dir1 = cq.Vector(0, 0, 1)
    p0 = cq.Vector(0, top_hook_y, embed_z)
    p1 = p0 + dir1 * L1
    
    cyl1 = cq.Solid.makeCylinder(6.5/2, L1, p0, dir1)
    
    L2 = 8.0 # shorter 45 degree end
    dir2 = cq.Vector(0, 1, 1).normalized()
    p2 = p1 + dir2 * L2
    
    cyl2 = cq.Solid.makeCylinder(6.5/2, L2, p1, dir2)
    
    sph1 = cq.Solid.makeSphere(6.5/2, p1, cq.Vector(0,0,1), -90)
    sph2 = cq.Solid.makeSphere(6.5/2, p2, cq.Vector(0,0,1), -90)
    
    top_hook = cq.Workplane(cyl1).union(cq.Workplane(cyl2)).union(cq.Workplane(sph1)).union(cq.Workplane(sph2))
    
    # Bottom Peg: Snap Fit
    bot_p0 = cq.Vector(0, bottom_peg_y, plate_thickness) # Starts at the back of the plate!
    snap_peg = create_snap_fit_peg(bot_p0, cq.Vector(0,0,1))
    
    # To embed it, we also need a solid cylinder bridging embed_z to plate_thickness
    bridge = cq.Solid.makeCylinder(6.5/2, plate_thickness - embed_z, cq.Vector(0, bottom_peg_y, embed_z), cq.Vector(0,0,1))
    
    result = base.union(top_hook).union(snap_peg).union(cq.Workplane(bridge))
    result = result.rotate((0,0,0), (0,1,0), 45)
    return result

def create_v2_cone():
    base = create_base_plate()
    plate_thickness = 6.0
    embed_z = plate_thickness / 2.0
    top_hook_y = 5.5
    bottom_peg_y = 5.5 - 25.4
    
    # Top Hook: V2 Truncated Cone
    L1 = (plate_thickness - embed_z) + 5.0
    dir1 = cq.Vector(0, 0, 1)
    p0 = cq.Vector(0, top_hook_y, embed_z)
    p1 = p0 + dir1 * L1
    
    cyl1 = cq.Solid.makeCylinder(6.5/2, L1, p0, dir1)
    sph1 = cq.Solid.makeSphere(6.5/2, p1, cq.Vector(0,0,1), -90)
    
    dir2 = cq.Vector(0, 1, 1).normalized()
    
    # Truncated cone from 6.5 to 4.5 over 2mm
    L2a = 2.0
    p2 = p1 + dir2 * L2a
    cone = cq.Solid.makeCone(6.5/2, 4.5/2, L2a, p1, dir2)
    
    # Straight cylinder 4.5 over 4mm
    L2b = 4.0
    p3 = p2 + dir2 * L2b
    cyl2 = cq.Solid.makeCylinder(4.5/2, L2b, p2, dir2)
    sph2 = cq.Solid.makeSphere(4.5/2, p3, cq.Vector(0,0,1), -90)
    
    top_hook = cq.Workplane(cyl1).union(cq.Workplane(sph1)).union(cq.Workplane(cone)).union(cq.Workplane(cyl2)).union(cq.Workplane(sph2))
    
    # Bottom Peg: Standard
    bot_p0 = cq.Vector(0, bottom_peg_y, embed_z)
    bot_dir = cq.Vector(0, 0, 1)
    bot_L = (plate_thickness - embed_z) + 5.0
    bot_p1 = bot_p0 + bot_dir * bot_L
    
    bot_cyl = cq.Solid.makeCylinder(5.5/2, bot_L, bot_p0, bot_dir)
    bot_sph = cq.Solid.makeSphere(5.5/2, bot_p1, cq.Vector(0,0,1), -90)
    
    bottom_peg = cq.Workplane(bot_cyl).union(cq.Workplane(bot_sph))
    
    result = base.union(top_hook).union(bottom_peg)
    result = result.rotate((0,0,0), (0,1,0), 45)
    return result

def main():
    model1 = create_v1_full_snap()
    export_stl(model1, "classic_hook_v1_full_snap.stl", category='pegboard_tests', print_orientation='face_down')
    print("Exported classic_hook_v1_full_snap.stl")
    
    model2 = create_v2_cone()
    export_stl(model2, "classic_hook_v2_cone.stl", category='pegboard_tests', print_orientation='face_down')
    print("Exported classic_hook_v2_cone.stl")

if __name__ == "__main__":
    main()
