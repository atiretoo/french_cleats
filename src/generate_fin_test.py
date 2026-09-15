import cadquery as cq
import math

def create_fin_test():
    # 1. Create the 3cm cube, tipped on its edge
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    
    # Calculate offset to bring the lowest edge to exactly Z=0
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
    # 2. Create the 0.8mm thick wedge that fills the space under the cube.
    # To avoid zero-thickness non-manifold errors during union, we extend the top
    # of the fin 0.1mm into the cube.
    wedge = (
        cq.Workplane("YZ")
        .polyline([(0, 0.1), (30, 30.1), (30, 0), (-30, 0), (-30, 30.1)])
        .close()
        .extrude(0.8)
        .translate((-0.4, 0, 0))
    )
    
    # 3. Create cutting bodies for the tapers
    # The taper reduces the width from 0.8 to 0.4 over the last 2mm vertically.
    # Since we shifted the top up by 0.1mm, we shift the cutting profiles up by 0.1mm (Local Y).
    prof_rp = [(0.5, 0.2), (0.2, 0.2), (0.5, -1.9)]
    prof_lp = [(-0.5, 0.2), (-0.2, 0.2), (-0.5, -1.9)]
    
    # Right taper, Y > 0
    cut_rp = (
        cq.Workplane("XZ")
        .polyline(prof_rp).close()
        .transformed(offset=(0, 30, 30))
        .polyline(prof_rp).close()
        .loft()
    )
    
    # Left taper, Y > 0
    cut_lp = (
        cq.Workplane("XZ")
        .polyline(prof_lp).close()
        .transformed(offset=(0, 30, 30))
        .polyline(prof_lp).close()
        .loft()
    )
    
    # Right taper, Y < 0
    # transformed offset: Local Y=30 -> Global Z=30. Local Z=-30 -> Global Y=-30.
    cut_rn = (
        cq.Workplane("XZ")
        .polyline(prof_rp).close()
        .transformed(offset=(0, 30, -30))
        .polyline(prof_rp).close()
        .loft()
    )
    
    # Left taper, Y < 0
    cut_ln = (
        cq.Workplane("XZ")
        .polyline(prof_lp).close()
        .transformed(offset=(0, 30, -30))
        .polyline(prof_lp).close()
        .loft()
    )
    
    # Cut tapers out of the wedge
    fin = wedge.cut(cut_rp).cut(cut_lp).cut(cut_rn).cut(cut_ln)
    
    # 4. Combine the cube and the fin
    test_obj = cube.union(fin)
    
    return test_obj

def main():
    test_obj = create_fin_test()
    filename = "fin_test_cube.stl"
    cq.exporters.export(test_obj, filename)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
