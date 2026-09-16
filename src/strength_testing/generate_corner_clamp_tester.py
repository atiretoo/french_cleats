import cadquery as cq
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import export_stl
import math

def create_depth_tester():
    unit_width = 28.0
    width = unit_width # 1U
    
    # Depths to test
    depths = [10.0, 15.0, 20.0, 25.0]
    num_slots = len(depths)
    
    slot_width = 10.0
    slot_spacing = 30.0
    start_clearance = 15.0
    
    # Calculate required length of the tester
    tester_length = start_clearance + (num_slots - 1) * slot_spacing + 15.0
    
    # Top of the tester
    shelf_top = 40.0
    y_drop = width / 2.0 # 14.0 mm
    v_inner_bottom = shelf_top - y_drop # 26.0 mm
    
    # Deepest groove is 25.0
    max_depth = max(depths)
    min_y = v_inner_bottom - max_depth # 1.0 mm
    
    # Flat bottom to stabilize it on the desk (spans the full 1U width)
    bottom_y = min_y - 5.0 # -4.0 mm
    
    # Profile of the tester (V-trough on top, flat on bottom for stability)
    pts = [
        (-width/2, shelf_top),
        (0, v_inner_bottom),
        (width/2, shelf_top),
        (width/2, bottom_y),
        (-width/2, bottom_y)
    ]
    
    tester = (
        cq.Workplane("XY")
        .polyline(pts).close()
        .extrude(-tester_length)
    )
    
    # Arc parameters (same as the holder)
    chord = 134.9375
    arc_height = 19.05
    arc_radius = (chord**2 / (8 * arc_height)) + (arc_height / 2)
    
    cutout_half_width = width/2 + 2.0
    rise = arc_radius - math.sqrt(arc_radius**2 - cutout_half_width**2)
    
    start_z = -start_clearance
    
    for i, d in enumerate(depths):
        z_center = start_z - i * slot_spacing
        arc_bottom_y = v_inner_bottom - d
        
        p1 = (-cutout_half_width, arc_bottom_y + rise)
        p2 = (0.0, arc_bottom_y)
        p3 = (cutout_half_width, arc_bottom_y + rise)
        p4 = (cutout_half_width, shelf_top + 10.0)
        p5 = (-cutout_half_width, shelf_top + 10.0)
        
        slot_cut = (
            cq.Workplane("XY", origin=(0, 0, z_center))
            .moveTo(p1[0], p1[1])
            .threePointArc(p2, p3)
            .lineTo(p4[0], p4[1])
            .lineTo(p5[0], p5[1])
            .close()
            .extrude(slot_width / 2.0, both=True)
        )
        tester = tester.cut(slot_cut)
        
    return tester

def main():
    tester = create_depth_tester()
    filename = "corner_clamp_tester_1u.stl"
    export_stl(tester, filename, category='strength_testing', export_step=False)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
