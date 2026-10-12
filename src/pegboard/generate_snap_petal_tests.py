import cadquery as cq
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_library import export_stl
from pegboard.coupon_utils import create_test_coupon_base

def create_snap_fit_peg_parameterized(bot_p0, num_petals=3, band_dia=8.1):
    delta = (band_dia / 2.0) - 4.05
    
    # This creates the snap fit peg AT the specified location.
    solid_cyl = cq.Solid.makeCylinder(3.25 + delta, 2.0, cq.Vector(0,0,0), cq.Vector(0,0,1))
    inner_solid = cq.Solid.makeCylinder(1.75 + delta, 6.25, cq.Vector(0,0,2), cq.Vector(0,0,1))
    
    tube_b_out = cq.Solid.makeCylinder(3.25 + delta, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b_in = cq.Solid.makeCylinder(2.45 + delta, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b = cq.Workplane(tube_b_out).cut(cq.Workplane(tube_b_in)).val()
    
    band_bs_out = cq.Solid.makeCone(3.25 + delta, 4.05 + delta, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs_in = cq.Solid.makeCylinder(2.45 + delta, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs = cq.Workplane(band_bs_out).cut(cq.Workplane(band_bs_in)).val()
    
    band_f_out = cq.Solid.makeCylinder(4.05 + delta, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f_in = cq.Solid.makeCylinder(2.45 + delta, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f = cq.Workplane(band_f_out).cut(cq.Workplane(band_f_in)).val()
    
    band_ts_out = cq.Solid.makeCone(4.05 + delta, 3.25 + delta, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts_in = cq.Solid.makeCylinder(2.45 + delta, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts = cq.Workplane(band_ts_out).cut(cq.Workplane(band_ts_in)).val()
    
    tube_t_out = cq.Solid.makeCylinder(3.25 + delta, 0.25, cq.Vector(0,0,8.0), cq.Vector(0,0,1))
    tube_t_in = cq.Solid.makeCylinder(2.45 + delta, 0.25, cq.Vector(0,0,8.0), cq.Vector(0,0,1))
    tube_t = cq.Workplane(tube_t_out).cut(cq.Workplane(tube_t_in)).val()
    
    outer_tube = cq.Workplane(tube_b).union(cq.Workplane(band_bs)).union(cq.Workplane(band_f)).union(cq.Workplane(band_ts)).union(cq.Workplane(tube_t))
    
    # Slit thickness
    slit_w = 0.8
    # Create N independent slits. We use a cutter that only goes in +Y direction from center so it cuts exactly 1 slit at a time.
    for i in range(num_petals):
        angle = i * (360.0 / num_petals)
        cutter = cq.Workplane("XY").workplane(offset=2.0).center(0, 5.0).box(slit_w, 10.0, 8.0, centered=(True, True, False))
        cutter = cutter.rotate((0,0,0), (0,0,1), angle)
        outer_tube = outer_tube.cut(cutter)
    
    snap_peg = cq.Workplane(solid_cyl).union(cq.Workplane(inner_solid)).union(outer_tube)
    snap_peg = snap_peg.translate(bot_p0)
    
    return snap_peg

def create_snap_dia_test(band_dia):
    peg1_y = 12.7
    peg2_y = -12.7
    top_y = peg1_y + 10.0
    bottom_y = peg2_y - 10.0
    
    base = create_test_coupon_base(width=20.0, plate_thickness=6.0, top_y=top_y, bottom_y=bottom_y)
    
    # Emboss (engrave) the diameter onto the back surface (Z = 6.0)
    # We transform rotate by 90 so it runs vertically along the long axis
    center_y = (top_y + bottom_y) / 2.0
    txt_solid = (cq.Workplane("XY")
                 .workplane(offset=6.0)
                 .center(0, center_y)
                 .transformed(rotate=(0,0,90))
                 .text(f"{band_dia}", 8, -0.6, combine=False))
    base = base.cut(txt_solid)
    
    embed_z = 3.0
    plate_thickness = 6.0
    
    bot_p0_1 = cq.Vector(0, peg1_y, plate_thickness)
    snap_peg1 = create_snap_fit_peg_parameterized(bot_p0_1, num_petals=3, band_dia=band_dia)
    bridge1 = cq.Solid.makeCylinder(6.5/2, plate_thickness - embed_z, cq.Vector(0, peg1_y, embed_z), cq.Vector(0,0,1))
    
    bot_p0_2 = cq.Vector(0, peg2_y, plate_thickness)
    snap_peg2 = create_snap_fit_peg_parameterized(bot_p0_2, num_petals=3, band_dia=band_dia)
    bridge2 = cq.Solid.makeCylinder(6.5/2, plate_thickness - embed_z, cq.Vector(0, peg2_y, embed_z), cq.Vector(0,0,1))
    
    result = base.union(snap_peg1).union(cq.Workplane(bridge1)).union(snap_peg2).union(cq.Workplane(bridge2))
    result = result.rotate((0,0,0), (0,1,0), 45)
    
    return result

def main():
    for dia in [7.825]:
        model = create_snap_dia_test(dia)
        filename = f"snap_fit_dia_{dia}mm_coupon.stl"
        export_stl(model, filename, category='pegboard_tests', print_orientation='face_down')
        print(f"Exported {filename}")

if __name__ == "__main__":
    main()
