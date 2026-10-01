# Copyright (C) 2026 Andrew Tyre
#
# This file is part of french_cleats.
#
# french_cleats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# french_cleats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with french_cleats.  If not, see <https://www.gnu.org/licenses/>.
import cadquery as cq
import argparse
import math

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model, support_fin

def add_support_fins(holder, width_units, bottom_groove_y):
    # 1. Rotate to back_down (backplate at Z=0, hook points to +Z)
    holder = holder.rotate((0,0,0), (1,0,0), 180)
    
    # 2. Tilt 45 degrees around Y-axis to the right (stands on right edge +X)
    holder = holder.rotate((0,0,0), (0,1,0), 45)
    
    baseplate_width = width_units * 28.0
    cos45 = math.cos(math.radians(45))
    
    # Right edge is at +W/2 before rotation.
    X_right = (baseplate_width / 2.0) * cos45
    Z_right = -(baseplate_width / 2.0) * cos45
    
    # Left edge is at -W/2 before rotation.
    X_left = (-baseplate_width / 2.0) * cos45
    
    length_total = X_right - X_left
    
    # 3. Shift holder so theoretical sharp right edge is at X=0 and Z=0
    holder = holder.translate((-X_right, 0, -Z_right))
    
    # 4. Generate Back Fins (supporting Z = -X plane)
    fin_width = 1.6
    chamfer = 2.0
    offset = chamfer * cos45 # 1.414
    
    # The physical right edge is chamfered, so it sits at X = -1.414, Z = +1.414
    # The back fin should start here and end before the left chamfer
    fin_back_len = length_total - 2 * offset
    fin_back = support_fin(z_gap=0.10, is_right=False, length=fin_back_len, height=fin_back_len, fin_width=fin_width)
    fin_back = fin_back.rotate((0,0,0), (0,0,1), -90)
    # Translate fin to match the chamfered face: UP by offset, LEFT by offset
    fin_back = fin_back.translate((-offset, 0, offset))
    
    # 5. Generate Front Fins (supporting Z = X right face) to act as kickstands for the CoG
    # The right face of the baseplate is a 45-degree angle going up and right: Z = X.
    # The fin needs to have its hypotenuse touching this face, and its vertical edge on the far right.
    # support_fin(is_right=True) provides exactly this.
    fin_front_len = 16.0 # Long enough to catch the CoG
    fin_front = support_fin(z_gap=0.10, is_right=True, length=fin_front_len, height=fin_front_len, fin_width=fin_width)
    fin_front = fin_front.rotate((0,0,0), (0,0,1), -90)
    # Translate fin UP by offset to match the flat chamfer bottom, and RIGHT by offset to stay on Z=X.
    fin_front = fin_front.translate((offset, 0, offset))
    
    # 6. Translate fins to the exact groove edges
    TOP_GROOVE_Y = 10.0
    GROOVE_SURFACE_HALF_WIDTH = 3.5
    
    # After 180 deg X rotation, Y is inverted
    flipped_top_edge = -(TOP_GROOVE_Y - GROOVE_SURFACE_HALF_WIDTH) # -6.5
    flipped_bot_edge = -(bottom_groove_y + GROOVE_SURFACE_HALF_WIDTH) # e.g. +59.5
    
    # Fin spans from Y - fin_width/2 to Y + fin_width/2. Place them just inside the flat region.
    y_target_1 = flipped_top_edge + (fin_width / 2.0)
    y_target_2 = flipped_bot_edge - (fin_width / 2.0)
    
    # Apply Y translations and Union
    holder = holder.union(fin_back.val().translate((0, y_target_1, 0)))
    holder = holder.union(fin_back.val().translate((0, y_target_2, 0)))
    holder = holder.union(fin_front.val().translate((0, y_target_1, 0)))
    holder = holder.union(fin_front.val().translate((0, y_target_2, 0)))
    
    # Drop the entire model by `offset` (1.414) so the physical chamfered bottom touches Z=0!
    holder = holder.translate((0, 0, -offset))
    
    return holder

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
    
    # 1. Fillet where hook cylinder meets the backplate front face (Z = -BACKPLATE_THICKNESS)
    # The user rule specifies 5.0 mm fillet for edges joining to the backplate.
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
            # Change from 3.0 to 5.0 to match the 5mm load-bearing fillet rule
            tool_holder = tool_holder.edges(BaseIntersectionSelector()).fillet(5.0)
        except Exception as e:
            print(f"Warning: Fillet at hook base could not be applied ({e})")
            
    # 2. Fillet the exposed front edges of the backplate (Z = -BACKPLATE_THICKNESS) with 2.5mm
    class FrontEdgeSel(cq.Selector):
        def filter(self, ol):
            res = []
            for o in ol:
                if isinstance(o, cq.Edge):
                    b = o.BoundingBox()
                    if abs(b.zmax - (-BACKPLATE_THICKNESS)) < 1e-2 and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 1e-2:
                        if abs(b.xmax - width/2) < 1e-2 or abs(b.xmin - -width/2) < 1e-2 or abs(b.ymax - top_y) < 1e-2 or abs(b.ymin - bottom_y) < 1e-2:
                            res.append(o)
            return res

    try:
        tool_holder = tool_holder.edges(FrontEdgeSel()).fillet(2.5)
    except Exception as e:
        print(f"Warning: Front edge fillets could not be applied ({e})")
            
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
    
    return tool_holder, width_units, length_units, bottom_groove_y

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Hook")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide (default: 1)")
    parser.add_argument("--length-units", type=int, default=4, help="Number of units long (default: 4)")
    parser.add_argument("--diameter", type=float, default=10.0, help="Diameter of the hook in mm (default: 10.0)")
    parser.add_argument("--slope", type=float, default=5.0, help="Upward slope angle in degrees (default: 5.0)")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail (default: 73.0)")
    parser.add_argument("--fillet-radius", type=float, default=3.0, help="Base fillet radius (default: 3.0)")
    parser.add_argument("--print-orientation", type=str, default="right_down_45", choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down", "right_down_45"], help="Print orientation for STL export (default: right_down_45)")
    args = parser.parse_args()
    
    holder, wu, lu, bottom_groove_y = create_hook(
        width_units=args.width_units,
        length_units=args.length_units,
        diameter=args.diameter,
        slope_deg=args.slope,
        rail_height=args.rail_height,
        fillet_radius=args.fillet_radius
    )
    
    if args.print_orientation == "right_down_45":
        holder = add_support_fins(holder, wu, bottom_groove_y)
        filename = f"hook_{wu}x{lu}u_D{int(args.diameter)}mm_{int(args.slope)}deg_groove_H{args.rail_height}_45deg.stl"
        export_model(holder, filename, category='tool_holders', print_orientation="face_down")
    else:
        filename = f"hook_{wu}x{lu}u_D{int(args.diameter)}mm_{int(args.slope)}deg_groove_H{args.rail_height}.stl"
        export_model(holder, filename, category='tool_holders', print_orientation=args.print_orientation)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
