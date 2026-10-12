import cadquery as cq
import os
import sys

# Add the src directory to the path so we can import core_library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_library import export_stl

def create_snap_test():
    # 1. Base square 20x20x5 (Z from -5 to 0)
    base = cq.Workplane("XY").workplane(offset=-5).box(20, 20, 5, centered=(True, True, False)).val()
    
    # 2. Solid cylinder bottom 3mm (Z from 0 to 3)
    solid_cyl = cq.Solid.makeCylinder(3.25, 3.0, cq.Vector(0,0,0), cq.Vector(0,0,1))
    
    # 3. Inner solid 3.5mm dia (R=1.75), Z from 3 to 9.25 (length 6.25)
    inner_solid = cq.Solid.makeCylinder(1.75, 6.25, cq.Vector(0,0,3), cq.Vector(0,0,1))
    
    # 4. Outer tube with band
    # Tube base part: Z=3 to Z=6 (length 3.0). R_out=3.25, R_in=2.45
    tube_b_out = cq.Solid.makeCylinder(3.25, 3.0, cq.Vector(0,0,3), cq.Vector(0,0,1))
    tube_b_in = cq.Solid.makeCylinder(2.45, 3.0, cq.Vector(0,0,3), cq.Vector(0,0,1))
    tube_b = cq.Workplane(tube_b_out).cut(cq.Workplane(tube_b_in)).val()
    
    # Band bottom slope: Z=6 to Z=6.8 (length 0.8). R_out goes 3.25 to 4.05
    band_bs_out = cq.Solid.makeCone(3.25, 4.05, 0.8, cq.Vector(0,0,6), cq.Vector(0,0,1))
    band_bs_in = cq.Solid.makeCylinder(2.45, 0.8, cq.Vector(0,0,6), cq.Vector(0,0,1))
    band_bs = cq.Workplane(band_bs_out).cut(cq.Workplane(band_bs_in)).val()
    
    # Band flat: Z=6.8 to Z=8.2 (length 1.4). R_out=4.05
    band_f_out = cq.Solid.makeCylinder(4.05, 1.4, cq.Vector(0,0,6.8), cq.Vector(0,0,1))
    band_f_in = cq.Solid.makeCylinder(2.45, 1.4, cq.Vector(0,0,6.8), cq.Vector(0,0,1))
    band_f = cq.Workplane(band_f_out).cut(cq.Workplane(band_f_in)).val()
    
    # Band top slope: Z=8.2 to Z=9.0 (length 0.8). R_out goes 4.05 to 3.25
    band_ts_out = cq.Solid.makeCone(4.05, 3.25, 0.8, cq.Vector(0,0,8.2), cq.Vector(0,0,1))
    band_ts_in = cq.Solid.makeCylinder(2.45, 0.8, cq.Vector(0,0,8.2), cq.Vector(0,0,1))
    band_ts = cq.Workplane(band_ts_out).cut(cq.Workplane(band_ts_in)).val()
    
    # Tube top part: Z=9.0 to Z=9.25 (length 0.25). R_out=3.25
    tube_t_out = cq.Solid.makeCylinder(3.25, 0.25, cq.Vector(0,0,9.0), cq.Vector(0,0,1))
    tube_t_in = cq.Solid.makeCylinder(2.45, 0.25, cq.Vector(0,0,9.0), cq.Vector(0,0,1))
    tube_t = cq.Workplane(tube_t_out).cut(cq.Workplane(tube_t_in)).val()
    
    outer_tube = cq.Workplane(tube_b).union(cq.Workplane(band_bs)).union(cq.Workplane(band_f)).union(cq.Workplane(band_ts)).union(cq.Workplane(tube_t))
    
    # 5. Split the tube portion into 6 pieces
    # Create 3 independent box cutters
    # Slits go from Z=3.0 up to past Z=9.25. We'll use Z=3.0 to Z=10.0
    c1 = cq.Workplane("XY").workplane(offset=3.0).box(0.6, 20, 7.0, centered=(True, True, False))
    c2 = cq.Workplane("XY").workplane(offset=3.0).box(0.6, 20, 7.0, centered=(True, True, False)).rotate((0,0,0), (0,0,1), 60)
    c3 = cq.Workplane("XY").workplane(offset=3.0).box(0.6, 20, 7.0, centered=(True, True, False)).rotate((0,0,0), (0,0,1), 120)
    
    outer_tube = outer_tube.cut(c1).cut(c2).cut(c3)
    
    # Combine everything
    result = cq.Workplane(base).union(cq.Workplane(solid_cyl)).union(cq.Workplane(inner_solid)).union(outer_tube)
    
    return result

def main():
    model = create_snap_test()
    filename = "snap_fit_test_coupon.stl"
    export_stl(model, filename, category='pegboard_tests')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
