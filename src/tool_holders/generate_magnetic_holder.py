import cadquery as cq
import argparse
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_magnetic_holder(units=1, mount_type="groove", mag_count=2, mag_dia=10.2, mag_depth=2.0):
    width = units * UNIT_WIDTH
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=2)
    

    # Calculate magnet positions
    mag_pts = []
    if mag_count == 1:
        mag_pts.append((0, -37.0))
    elif mag_count > 1:
        start_y = -17.0
        end_y = -57.0
        step = (end_y - start_y) / (mag_count - 1)
        for i in range(mag_count):
            mag_pts.append((0, start_y + i * step))
    
    if mag_count > 0:
        mags = (
            cq.Workplane("XY").workplane(offset=-BACKPLATE_THICKNESS) # Front face of baseplate
            .pushPoints(mag_pts)
            .circle(mag_dia / 2.0)
            .extrude(mag_depth) # Cut into the block (+Z)
        )
        body = body.cut(mags)
        
        # Push holes
        # 2mm diameter, all the way through to the back
        push_holes = (
            cq.Workplane("XY").workplane(offset=-BACKPLATE_THICKNESS)
            .pushPoints(mag_pts)
            .circle(2.0 / 2.0)
            .extrude(20.0) # All the way to +Z
        )
        body = body.cut(push_holes)
    
    # Cut screws
    if screw_pts:
        screws = (
            cq.Workplane("XY").workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6/2.0)
            .extrude(-20) 
        )
        body = body.cut(screws)
        
        recesses = (
            cq.Workplane("XY").workplane(offset=-8)
            .pushPoints(screw_pts)
            .circle(8.0/2.0) 
            .extrude(-20) 
        )
        body = body.cut(recesses)
        
    if mc_solids:
        for solid in mc_solids:
            body = body.union(cq.Workplane(solid))
            
    return body

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate magnetic tool holder.")
    parser.add_argument("--units", type=int, default=1, help="Number of units wide")
    parser.add_argument("--mount", type=str, default="groove", choices=["groove", "multiconnect", "hybrid"], help="Mount type")
    parser.add_argument("--mag-count", type=int, default=2, help="Number of magnets")
    parser.add_argument("--mag-dia", type=float, default=10.2, help="Diameter of magnet hole (including tolerance)")
    parser.add_argument("--mag-depth", type=float, default=2.0, help="Depth of magnet hole")
    args = parser.parse_args()

    holder = create_magnetic_holder(
        units=args.units, 
        mount_type=args.mount,
        mag_count=args.mag_count,
        mag_dia=args.mag_dia,
        mag_depth=args.mag_depth
    )
    
    filename = f"magnetic_saw_holder_{args.units}u_{args.mag_count}Mags_D{args.mag_dia}x{args.mag_depth}_{args.mount}.stl"
    export_model(holder, filename, category="tool_holders")
