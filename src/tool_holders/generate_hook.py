import cadquery as cq
import argparse
import math

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_hook(width_units=1, length_units=4, diameter=10.0, slope_deg=5.0, rail_height=73.0, fillet_radius=3.0, tip_fillet=3.0):
    """
    Creates a French Cleat hook tool holder.
    - width_units: Width of the backplate in 28mm units (default: 1U)
    - length_units: Length of the hook in 28mm units (default: 4U = 112mm)
    - diameter: Diameter of the cylindrical hook rod (default: 10mm)
    - slope_deg: Angle in degrees sloping upwards from horizontal (default: 5 deg)
    - rail_height: Cleat rail height (default: 73.0mm)
    - fillet_radius: Radius of fillet connecting the hook rod to the backplate (default: 3.0mm)
    - tip_fillet: Radius of fillet on the tip of the hook (default: 3.0mm)
    """
    width = width_units * UNIT_WIDTH
    length = length_units * UNIT_WIDTH
    radius = diameter / 2.0
    
    # Create the standard groove-mount baseplate
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(
        width_units, rail_height, mount_type="groove", num_rows=2
    )
    
    # Position hook at 1/3 of the distance from bottom_y to top_y
    total_height = top_y - bottom_y
    hook_y = bottom_y + total_height / 3.0
    
    # The front face of the backplate is at Z = -BACKPLATE_THICKNESS, facing in -Z direction.
    # We extrude a cylinder along +Z, fillet its tip, then rotate and translate.
    # To slope upwards (+Y) by slope_deg while projecting outwards into -Z,
    # we rotate around X-axis by -(180 - slope_deg) = -(180 - 5) = -175 deg.
    rot_angle = -(180.0 - slope_deg)
    
    # Embed the cylinder slightly inside the backplate so the intersection with
    # the front face (Z = -BACKPLATE_THICKNESS) is a single, clean planar closed loop edge
    # which CadQuery's OpenCASCADE BRepFillet engine can easily and reliably fillet.
    embed_depth = 4.0
    total_rod_len = length + embed_depth
    
    hook_rod = (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(total_rod_len)
    )
    
    if tip_fillet > 0:
        try:
            hook_rod = hook_rod.faces(">Z").fillet(tip_fillet)
        except Exception:
            pass
            
    hook_rod = (
        hook_rod
        .rotate((0, 0, 0), (1, 0, 0), rot_angle)
        .translate((0, hook_y, -BACKPLATE_THICKNESS + embed_depth))
    )
    
    tool_holder = tool_holder.union(hook_rod)
    
    # Fillet where hook cylinder meets the backplate front face (Z = -BACKPLATE_THICKNESS)
    if fillet_radius > 0:
        class BaseIntersectionSelector(cq.Selector):
            def filter(self, objectList):
                res = []
                for o in objectList:
                    if not isinstance(o, cq.Edge):
                        continue
                    b = o.BoundingBox()
                    if abs(b.zmax - (-BACKPLATE_THICKNESS)) < 1e-3 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1e-3:
                        if abs(b.ymin - hook_y) < (diameter + 2.0) and (b.xmax - b.xmin) > (radius):
                            res.append(o)
                return res

        try:
            tool_holder = tool_holder.edges(BaseIntersectionSelector()).fillet(fillet_radius)
        except Exception as e:
            print(f"Warning: Fillet at hook base could not be applied ({e})")
            
    # Cut screw holes
    screws = (
        cq.Workplane("XY").workplane(offset=0)
        .pushPoints(screw_pts)
        .circle(3.6 / 2.0)
        .extrude(-20)
    )
    tool_holder = tool_holder.cut(screws)
    
    # Cut screw head recesses / counterbores
    recesses = (
        cq.Workplane("XY").workplane(offset=-8)
        .pushPoints(screw_pts)
        .circle(8.0 / 2.0)
        .extrude(-200)
    )
    tool_holder = tool_holder.cut(recesses)
    
    return tool_holder, width_units, length_units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Hook")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide (default: 1)")
    parser.add_argument("--length-units", type=int, default=4, help="Number of units long (default: 4)")
    parser.add_argument("--diameter", type=float, default=10.0, help="Diameter of the hook in mm (default: 10.0)")
    parser.add_argument("--slope", type=float, default=5.0, help="Upward slope angle in degrees (default: 5.0)")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail (default: 73.0)")
    parser.add_argument("--fillet-radius", type=float, default=3.0, help="Base fillet radius (default: 3.0)")
    args = parser.parse_args()
    
    holder, wu, lu = create_hook(
        width_units=args.width_units,
        length_units=args.length_units,
        diameter=args.diameter,
        slope_deg=args.slope,
        rail_height=args.rail_height,
        fillet_radius=args.fillet_radius
    )
    
    filename = f"hook_{wu}x{lu}u_D{int(args.diameter)}mm_{int(args.slope)}deg_groove_H{args.rail_height}.stl"
    export_model(holder, filename, category='tool_holders')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
