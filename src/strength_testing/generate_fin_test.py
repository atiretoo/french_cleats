import cadquery as cq
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import export_stl, support_fin
import math

def create_fin_test():
    # 1. Create the 3cm cube, tipped on its edge
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    
    # Calculate offset to bring the lowest edge to exactly Z=0
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
    # Final test: Single fin at 0.1mm gap with the long needle taper
    fin = support_fin(0.10, is_right=True)
        
    test_obj = cq.Compound.makeCompound([cube.val(), fin.val()])
    
    return test_obj

def main():
    test_obj = create_fin_test()
    filename = "fin_test_cube.stl"
    export_stl(test_obj, filename, print_orientation="face_down", category='strength_testing', export_step=False)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
