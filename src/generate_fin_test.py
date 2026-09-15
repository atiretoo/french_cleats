import cadquery as cq
import math

def create_fin_test():
    # 1. Create the 3cm cube, tipped on its edge
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    
    # Calculate offset to bring the lowest edge to exactly Z=0
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
    # 2. Calculate the exact length on the XY plane for a 30mm hypotenuse
    L = 30.0 / math.sqrt(2) # 21.2132 mm
    
    # 3. Create the two fins. 
    # Right fin: overlaps by 0.1mm normal (0.141mm vertical) to merge with the cube.
    wedge_right = (
        cq.Workplane("YZ")
        .polyline([(0,0), (0, 0.141), (L - 0.141, L), (L - 0.141, 0)])
        .close()
        .extrude(0.8)
        .translate((-0.4, 0, 0))
    )
    
    # Left fin: pulled back by 0.1mm normal (0.141mm vertical) to act as a breakaway support.
    wedge_left = (
        cq.Workplane("YZ")
        .polyline([(-0.141, 0), (-L, L - 0.141), (-L, 0)])
        .close()
        .extrude(0.8)
        .translate((-0.4, 0, 0))
    )
    
    # 4. Create cutting bodies for the tapers
    prof_p = [(0.5, 0.1), (0.2, 0.1), (0.5, -2.0)]
    prof_n = [(-0.5, 0.1), (-0.2, 0.1), (-0.5, -2.0)]
    
    # Tapers for Right Fin (Shifted UP by 0.141 in Z)
    cut_rp = (
        cq.Workplane("XZ", origin=(0, 0, 0.141))
        .polyline(prof_p).close()
        .transformed(offset=(0, 25, 25))
        .polyline(prof_p).close()
        .loft()
    )
    cut_rn = (
        cq.Workplane("XZ", origin=(0, 0, 0.141))
        .polyline(prof_n).close()
        .transformed(offset=(0, 25, 25))
        .polyline(prof_n).close()
        .loft()
    )
    fin_right = wedge_right.cut(cut_rp).cut(cut_rn)
    
    # Tapers for Left Fin (Shifted DOWN by 0.141 in Z)
    cut_lp = (
        cq.Workplane("XZ", origin=(0, 0, -0.141))
        .polyline(prof_p).close()
        .transformed(offset=(0, 25, -25))
        .polyline(prof_p).close()
        .loft()
    )
    cut_ln = (
        cq.Workplane("XZ", origin=(0, 0, -0.141))
        .polyline(prof_n).close()
        .transformed(offset=(0, 25, -25))
        .polyline(prof_n).close()
        .loft()
    )
    fin_left = wedge_left.cut(cut_lp).cut(cut_ln)
    
    # 5. Combine everything into a single compound (handles disjoint shells safely)
    test_obj = cq.Compound.makeCompound([cube.val(), fin_right.val(), fin_left.val()])
    
    return test_obj

def main():
    test_obj = create_fin_test()
    filename = "fin_test_cube.stl"
    cq.exporters.export(test_obj, filename)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
