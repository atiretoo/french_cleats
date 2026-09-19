import cadquery as cq
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import export_stl, support_fin
import math

def create_fin_test():
    # 1. Create the 3cm cube, tipped on its edge
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    
    # Calculate offset to bring the lowest edge to exactly Z=0
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
    # 2. Create 3 fins with different z_gaps
    L = 30.0 / math.sqrt(2)
    
    fin1 = support_fin(z_gap=0.05, is_right=True, length=L, height=L).translate((-10, 0, 0))
    fin2 = support_fin(z_gap=0.08, is_right=True, length=L, height=L).translate((0, 0, 0))
    fin3 = support_fin(z_gap=0.10, is_right=True, length=L, height=L).translate((10, 0, 0))
    
    # Add text labels on top of the cube so we know which is which?
    # The cube face is at Z=Y. The top face is angled. 
    # Just keeping track: Left(-10)=0.05, Center(0)=0.07, Right(10)=0.10
        
    test_obj = cq.Compound.makeCompound([cube.val(), fin1.val(), fin2.val(), fin3.val()])
    
    return test_obj

def main():
    test_obj = create_fin_test()
    filename = "fin_test_cube.stl"
    export_stl(test_obj, filename, print_orientation="face_down", category='strength_testing', export_step=False)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
