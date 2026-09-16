import cadquery as cq
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import export_stl
import argparse
import math

def create_nut_pusher(screw_m="M3", layer_thickness=0.28):
    if screw_m == "M3":
        nut_waf, nut_thick = 5.5, 2.4
    elif screw_m == "M4":
        nut_waf, nut_thick = 7.0, 3.2
    elif screw_m == "M5":
        nut_waf, nut_thick = 8.0, 4.0
    else:
        raise ValueError(f"Unsupported screw size {screw_m}")
        
    tool_thickness = nut_thick - 2 * layer_thickness
    tool_width = nut_waf * 0.9
    
    # In generate_cleats.py, the slot depth from the cleat face is:
    # 10.0 + nut_waf / 2.0
    slot_depth = 10.0 + nut_waf / 2.0
    
    # A hexagon with flats on the side has a point-to-point length of:
    nut_point_to_point = nut_waf * 2 / math.sqrt(3)
    
    # The tool apex (deepest part of the V-notch) must be at this distance 
    # from the shoulder so that when the shoulder hits the cleat face, 
    # the nut's front point hits the bottom of the slot.
    shaft_length = slot_depth - nut_point_to_point
    
    # The prongs extend forward from the apex by:
    prong_ext = (tool_width / 2.0) / math.tan(math.radians(60))
    
    # Coordinates for the base tool profile
    handle_len = 40.0
    handle_w = tool_width * 2.0
    
    pts = [
        (0, tool_width/2),
        (shaft_length + prong_ext, tool_width/2),
        (shaft_length, 0),
        (shaft_length + prong_ext, -tool_width/2),
        (0, -tool_width/2),
        (0, -handle_w/2),
        (-handle_len, -handle_w/2),
        (-handle_len, handle_w/2),
        (0, handle_w/2)
    ]
    
    base_tool = (
        cq.Workplane("XY")
        .polyline(pts).close()
        .extrude(tool_thickness)
    )
    
    handle_pts = [
        (0, handle_w/2),
        (0, -handle_w/2),
        (-handle_len, -handle_w/2),
        (-handle_len, handle_w/2)
    ]
    
    handle = (
        cq.Workplane("XY").workplane(offset=tool_thickness)
        .polyline(handle_pts).close()
        .extrude(tool_thickness)
    )
    
    tool = base_tool.union(handle)
    
    return tool, tool_thickness, tool_width

def main():
    parser = argparse.ArgumentParser(description="Generate Nut Pusher Tool")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size (M3, M4, M5)")
    parser.add_argument("--layer-thickness", type=float, default=0.28, help="Layer thickness in mm")
    
    args = parser.parse_args()
    
    tool, t, w = create_nut_pusher(args.screw, args.layer_thickness)
    
    filename = f"nut_pusher_{args.screw}_L{args.layer_thickness}.stl"
    export_stl(tool, filename, rotate_for_printing=False, category='utilities')
    print(f"Exported {filename} (thickness: {t:.2f}mm, shaft width: {w:.2f}mm)")

if __name__ == "__main__":
    main()
