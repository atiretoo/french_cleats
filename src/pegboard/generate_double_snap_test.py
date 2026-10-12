import cadquery as cq
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_library import export_stl

def create_snap_fit_peg(bot_p0, bot_dir):
    # This creates the snap fit peg AT the specified location and direction.
    solid_cyl = cq.Solid.makeCylinder(3.25, 2.0, cq.Vector(0,0,0), cq.Vector(0,0,1))
    inner_solid = cq.Solid.makeCylinder(1.75, 6.25, cq.Vector(0,0,2), cq.Vector(0,0,1))
    
    tube_b_out = cq.Solid.makeCylinder(3.25, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b_in = cq.Solid.makeCylinder(2.45, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b = cq.Workplane(tube_b_out).cut(cq.Workplane(tube_b_in)).val()
    
    band_bs_out = cq.Solid.makeCone(3.25, 4.05, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs_in = cq.Solid.makeCylinder(2.45, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs = cq.Workplane(band_bs_out).cut(cq.Workplane(band_bs_in)).val()
    
    band_f_out = cq.Solid.makeCylinder(4.05, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f_in = cq.Solid.makeCylinder(2.45, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f = cq.Workplane(band_f_out).cut(cq.Workplane(band_f_in)).val()
    
    band_ts_out = cq.Solid.makeCone(4.05, 3.25, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts_in = cq.Solid.makeCylinder(2.45, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts = cq.Workplane(band_ts_out).cut(cq.Workplane(band_ts_in)).val()
    
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
    snap_peg = snap_peg.translate(bot_p0)
    
    return snap_peg

def create_double_snap_test():
    width = 20.0
    plate_thickness = 6.0
    
    # 2 snaps spaced 25.4mm apart
    peg1_y = 12.7
    peg2_y = -12.7
    
    top_y = peg1_y + 10.0
    bottom_y = peg2_y - 10.0
    
    plate_h = top_y - bottom_y
    plate_center_y = bottom_y + plate_h/2
    base = cq.Workplane("XY").center(0, plate_center_y).box(width, plate_h, plate_thickness, centered=(True, True, False))
    
    embed_z = plate_thickness / 2.0
    
    # Peg 1
    bot_p0_1 = cq.Vector(0, peg1_y, plate_thickness)
    snap_peg1 = create_snap_fit_peg(bot_p0_1, cq.Vector(0,0,1))
    bridge1 = cq.Solid.makeCylinder(6.5/2, plate_thickness - embed_z, cq.Vector(0, peg1_y, embed_z), cq.Vector(0,0,1))
    
    # Peg 2
    bot_p0_2 = cq.Vector(0, peg2_y, plate_thickness)
    snap_peg2 = create_snap_fit_peg(bot_p0_2, cq.Vector(0,0,1))
    bridge2 = cq.Solid.makeCylinder(6.5/2, plate_thickness - embed_z, cq.Vector(0, peg2_y, embed_z), cq.Vector(0,0,1))
    
    result = base.union(snap_peg1).union(cq.Workplane(bridge1)).union(snap_peg2).union(cq.Workplane(bridge2))
    
    return result

def main():
    model = create_double_snap_test()
    filename = "double_snap_test_coupon.stl"
    export_stl(model, filename, category='pegboard_tests', print_orientation='face_down')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
