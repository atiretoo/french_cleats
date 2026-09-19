import cadquery as cq
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import export_stl, support_fin
import math

def create_fin_test():
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
    L = 30.0 / math.sqrt(2)
    
    fin = support_fin(z_gap=0.2, is_right=True, length=L, height=L)
        
    test_obj = cq.Compound.makeCompound([cube.val(), fin.val()])
    return test_obj

def main():
    test_obj = create_fin_test()
    filename = "fin_test_cube.stl"
    export_stl(test_obj, filename, print_orientation="face_down", category='strength_testing', export_step=True)
    print(f"Exported {filename} and fin_test_cube.step")

if __name__ == "__main__":
    main()
