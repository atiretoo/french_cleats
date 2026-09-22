import cadquery as cq
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import export_model, support_fin
import math

def create_fin_test():
    cube = cq.Workplane("XY").box(30, 30, 30).rotate((0,0,0), (1,0,0), 45)
    lowest_z = -15 * math.sqrt(2)
    cube = cube.translate((0, 0, -lowest_z))
    
    L = 30.0 / math.sqrt(2)
    
    fin1 = support_fin(z_gap=0.025, is_right=True, length=L, height=L).translate((-14.8, 0, 0))
    fin2 = support_fin(z_gap=0.02, is_right=True, length=L, height=L).translate((-5.0, 0, 0))
    fin3 = support_fin(z_gap=0.01, is_right=True, length=L, height=L).translate((5.0, 0, 0))
    fin4 = support_fin(z_gap=0.0, is_right=True, length=L, height=L).translate((14.8, 0, 0))
        
    assy = cq.Assembly()
    assy.add(cube.val(), name="Test_Cube", color=cq.Color(0.8, 0.8, 0.8, 1.0))
    assy.add(fin1.val(), name="Fin_0.025mm", color=cq.Color(1.0, 0.5, 0.0, 1.0))
    assy.add(fin2.val(), name="Fin_0.020mm", color=cq.Color(1.0, 0.5, 0.0, 1.0))
    assy.add(fin3.val(), name="Fin_0.010mm", color=cq.Color(1.0, 0.5, 0.0, 1.0))
    assy.add(fin4.val(), name="Fin_0.000mm", color=cq.Color(1.0, 0.5, 0.0, 1.0))
    
    return assy

def main():
    test_obj = create_fin_test()
    filename = "fin_test_cube.stl"
    export_model(test_obj, filename, print_orientation="face_down", category='strength_testing', export="both")
    print(f"Exported {filename} and fin_test_cube.step")

if __name__ == "__main__":
    main()
