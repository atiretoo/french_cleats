import cadquery as cq
import argparse
import sys
import math
sys.path.append('src')

from core_library import export_stl
from pegboard.coupon_utils import create_test_coupon_base
from pegboard.generate_snap_petal_tests import create_snap_fit_peg_parameterized

def create_combo_test(top_hook_dia, band_dia):
    peg1_y = 12.7
    peg2_y = -12.7
    top_y = peg1_y + 10.0
    bottom_y = peg2_y - 10.0
    
    base = create_test_coupon_base(width=20.0, plate_thickness=6.0, top_y=top_y, bottom_y=bottom_y)
    
    # Emboss (engrave) the labels onto the back surface (Z = 6.0)
    center_y = (top_y + bottom_y) / 2.0
    txt_solid = (cq.Workplane("XY")
                 .workplane(offset=6.0)
                 .center(0, center_y)
                 .transformed(rotate=(0,0,90))
                 .text(f"H{top_hook_dia} S{band_dia}", 4, -0.6, combine=False))
    base = base.cut(txt_solid)
    
    embed_z = 3.0
    plate_thickness = 6.0
    
    # 1. Top Hook (Arc)
    R = 17.5
    end_y = R - R * math.cos(math.radians(45))
    end_z = R * math.sin(math.radians(45))
    
    path = cq.Workplane("YZ").center(peg1_y, plate_thickness).moveTo(0, 0).radiusArc((end_y, end_z), R)
    arc_hook = cq.Workplane("XY").workplane(offset=plate_thickness).center(0, peg1_y).circle(top_hook_dia/2).sweep(path)
    
    embed_cyl = cq.Solid.makeCylinder(top_hook_dia/2, plate_thickness - embed_z, cq.Vector(0, peg1_y, embed_z), cq.Vector(0,0,1))
    
    # We must explicitly rotate the sphere cap -90 degrees around Z because makeSphere starts pointing up and we need it to point correctly based on the hook orientation.
    # Actually wait. In generate_pegboard_adapter, we have:
    # sph = cq.Solid.makeSphere(top_hook_dia/2, cq.Vector(x, top_hook_y + end_y, plate_thickness + end_z), cq.Vector(0,0,1), -90)
    # So we use the same here.
    sph = cq.Solid.makeSphere(top_hook_dia/2, cq.Vector(0, peg1_y + end_y, plate_thickness + end_z), cq.Vector(0,0,1), -90)
    
    top_hook = arc_hook.union(cq.Workplane(embed_cyl)).union(cq.Workplane(sph))
    
    # 2. Bottom Snap Fit Peg
    bot_p0 = cq.Vector(0, peg2_y, plate_thickness)
    snap_peg = create_snap_fit_peg_parameterized(bot_p0, num_petals=3, band_dia=band_dia)
    snap_embed = cq.Solid.makeCylinder(6.5/2, plate_thickness - embed_z, cq.Vector(0, peg2_y, embed_z), cq.Vector(0,0,1))
    
    result = base.union(top_hook).union(snap_peg).union(cq.Workplane(snap_embed))
    result = result.rotate((0,0,0), (0,1,0), 45)
    
    return result

def main():
    combos = [
        (5.0, 7.65),
        (6.5, 7.65)
    ]
    
    for hook_dia, snap_dia in combos:
        model = create_combo_test(hook_dia, snap_dia)
        filename = f"hook_{hook_dia}mm_snap_{snap_dia}mm_coupon.stl"
        export_stl(model, filename, category='pegboard_tests', print_orientation='face_down')
        print(f"Exported {filename}")

if __name__ == "__main__":
    main()
