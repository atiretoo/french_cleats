import cadquery as cq
import sys
sys.path.append('src')
from core_library import export_stl

def create_test_panel():
    width = 100.0
    height = 100.0
    thickness = 5.3
    
    hole_dia = 6.0525
    pitch = 25.4
    
    panel = cq.Workplane("XY").box(width, height, thickness)
    
    # Create 3x3 grid
    pts = [(i * pitch, j * pitch) for i in [-1, 0, 1] for j in [-1, 0, 1]]
    panel = panel.faces(">Z").workplane().pushPoints(pts).hole(hole_dia)
            
    return panel

def main():
    model = create_test_panel()
    export_stl(model, "pegboard_test_panel_3x3.stl", category="pegboard_tests")
    print("Exported pegboard_test_panel_3x3.stl")

if __name__ == "__main__":
    main()
