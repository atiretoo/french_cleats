import cadquery as cq
from holder_base import export_stl
import math

def create_fin_test():
    # 1. Create the 3cm cube, tipped on its edge
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    
    # Calculate offset to bring the lowest edge to exactly Z=0
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
def create_fin_half(normal_gap, is_right=True):
    Z_gap = normal_gap * math.sqrt(2)
    L = 30.0 / math.sqrt(2)
    
    start_y = max(0, Z_gap)
    end_y = L + min(0, Z_gap)
    
    start_z = start_y - Z_gap
    end_z = end_y - Z_gap
    
    if is_right:
        pts = [(start_y, 0), (start_y, start_z), (end_y, end_z), (end_y, 0)]
    else:
        pts = [(-start_y, 0), (-start_y, start_z), (-end_y, end_z), (-end_y, 0)]
        
    unique_pts = [pts[0]]
    for p in pts[1:]:
        if p != unique_pts[-1]:
            unique_pts.append(p)
    if len(unique_pts) > 1 and unique_pts[-1] == unique_pts[0]:
        unique_pts.pop()
        
    wedge = (
        cq.Workplane("YZ")
        .polyline(unique_pts).close()
        .extrude(0.8)
        .translate((-0.4, 0, 0))
    )
    
    prof_p = [(0.5, 0.1), (0.2, 0.1), (0.5, -2.0)]
    prof_n = [(-0.5, 0.1), (-0.2, 0.1), (-0.5, -2.0)]
    
    if is_right:
        cut_p = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_p).close()
            .transformed(offset=(0, 30, 30))
            .polyline(prof_p).close()
            .loft()
        )
        cut_n = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_n).close()
            .transformed(offset=(0, 30, 30))
            .polyline(prof_n).close()
            .loft()
        )
    else:
        cut_p = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_p).close()
            .transformed(offset=(0, 30, -30))
            .polyline(prof_p).close()
            .loft()
        )
        cut_n = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_n).close()
            .transformed(offset=(0, 30, -30))
            .polyline(prof_n).close()
            .loft()
        )
        
    return wedge.cut(cut_p).cut(cut_n)

def create_fin_test():
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
    # The winning gap is 0.07mm. We generate just one fin on one side (Y > 0)
    fin = create_fin_half(0.07, is_right=True)
    
    test_obj = cq.Compound.makeCompound([cube.val(), fin.val()])
    
    return test_obj

def main():
    test_obj = create_fin_test()
    filename = "fin_test_cube.stl"
    export_stl(test_obj, filename, rotate_for_printing=False)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
