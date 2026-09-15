import os
import sys

# Add src to path to import generate_strength_tester
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from generate_strength_tester import create_strength_tester
import cadquery as cq

def export_step_for_fea():
    print("Generating top thin strength tester...")
    # top position, thin (0.5 thickness factor)
    tester = create_strength_tester(position="top", thickness_factor=0.5)
    
    os.makedirs("strength_testing", exist_ok=True)
    filename = "strength_testing/tester_top_half_FEA.step"
    
    # Exporting as STEP is the most reliable way to pass CadQuery objects to FEA meshers like Gmsh
    cq.exporters.export(tester, filename)
    print(f"Exported STEP file for FEA to {filename}")

if __name__ == '__main__':
    export_step_for_fea()
