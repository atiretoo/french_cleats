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
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model, create_nut_slot

def create_saw_bracket(units=1, rail_height=73.0, hypotenuse=300.0, web_side="left"):
    width = units * UNIT_WIDTH
    brace_width = 10.0
    flange_thickness = 10.0
    
    if web_side == "left":
        web_offset_x = -width
        web_extrude = brace_width
        slot_x_dir = 1   # Slot breaks out to the right (+X)
    else:
        web_offset_x = 0.0
        web_extrude = -brace_width
        slot_x_dir = -1  # Slot breaks out to the left (-X)
        
    # Generate the cleat mounting interface
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(units, rail_height)
    
    drop = hypotenuse / math.sqrt(2)
    bracket_bottom = top_y - drop
    
    body = (
        body
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .end(2)
        .faces(">X")
        .workplane(centerOption="ProjectedOrigin")
        .tag("right_wp")
        .end(2)
    )
    
    # Extend the backplate downwards
    if bracket_bottom < bottom_y:
        ext_pts = [
            (bracket_bottom, 0.0),
            (bracket_bottom, -BACKPLATE_THICKNESS),
            (bottom_y, -BACKPLATE_THICKNESS),
            (bottom_y, 0.0),
        ]
        body = (
            body
            .workplaneFromTagged("right_wp")
            .polyline(ext_pts)
            .close()
            .extrude(-width)
        )
        
    # Create the 10mm thick triangular web
    web_pts = [
        (top_y, -BACKPLATE_THICKNESS),
        (bracket_bottom, -BACKPLATE_THICKNESS),
        (bracket_bottom, -BACKPLATE_THICKNESS - drop),
    ]
    
    # Create the 28mm wide hypotenuse flange
    dir_inward = cq.Vector(0, -1, 1).normalized()
    p1 = cq.Vector(0, top_y, -BACKPLATE_THICKNESS)
    p2 = cq.Vector(0, bracket_bottom, -BACKPLATE_THICKNESS - drop)
    
    p1_in = p1 + dir_inward * flange_thickness
    p2_in = p2 + dir_inward * flange_thickness
    
    flange_pts = [
        (p1.y, p1.z),
        (p2.y, p2.z),
        (p2_in.y, p2_in.z),
        (p1_in.y, p1_in.z),
    ]
    
    # Triangular lightening cutout with filleted corners (15mm clearance)
    c1_y = bracket_bottom + 15.0
    c1_z = -26.0
    c2_y = top_y - 15.0 - 25.0 * math.sqrt(2)
    c2_z = -26.0
    c3_y = bracket_bottom + 15.0
    c3_z = (bracket_bottom + 15.0) - top_y - 11.0 + 25.0 * math.sqrt(2)
    
    cutout_sketch = (
        cq.Sketch()
        .polygon([(c1_y, c1_z), (c2_y, c2_z), (c3_y, c3_z)])
        .reset()
        .vertices()
        .fillet(4.99)
    )
    
    body = (
        body
        .workplaneFromTagged("right_wp")
        .workplane(offset=web_offset_x)
        .polyline(web_pts)
        .close()
        .extrude(web_extrude)
        .workplaneFromTagged("right_wp")
        .polyline(flange_pts)
        .close()
        .extrude(-width)
    )
    
    try:
        body = (
            body
            .faces("+X or -X")
            .faces("not >X")
            .faces("not <X")
            .edges("not <Y")
            .fillet(4.99)
        )
    except Exception as e:
        print(f"Warning: Could not apply all fillets: {e}")

    body = (
        body
        .workplaneFromTagged("right_wp")
        .workplane(offset=web_offset_x)
        .placeSketch(cutout_sketch)
        .cutBlind(web_extrude)
    )

    # Add M3 clearance holes and captive nut slots along the hypotenuse flange
    normal_dir = cq.Vector(0, 1, -1).normalized()
    
    for i in [0.2, 0.5, 0.8]:
        y = top_y - drop * i
        z = -BACKPLATE_THICKNESS - drop * i
        pt = cq.Vector(0, y, z)
        
        # M3 clearance hole (3.4mm dia, 15mm deep)
        body = (
            body
            .copyWorkplane(cq.Workplane(cq.Plane(origin=pt, xDir=(1, 0, 0), normal=normal_dir)))
            .hole(3.4, 15.0)
        )
        
        # Nut slot 
        nut_center = pt + normal_dir * (-5.0)
        slot_solid = create_nut_slot("M3", depth=14.0, push_hole=True)
        
        # Orient the slot so the bolt is along normal_dir and it slides along the X axis
        x_dir = cq.Vector(0, slot_x_dir, slot_x_dir).normalized()
        plane = cq.Plane(origin=nut_center, xDir=x_dir, normal=normal_dir)
        
        body = body.cut(slot_solid.moved(cq.Location(plane)))

    # Cut cleat mounting screws
    if screw_pts:
        body = (
            body
            .workplaneFromTagged("back_wp")
            .pushPoints(screw_pts)
            .hole(3.6, 20.0)
            .workplaneFromTagged("back_wp")
            .workplane(offset=-8.0)
            .pushPoints(screw_pts)
            .hole(8.0, 200.0)
        )
    
    return body

def create_drilling_template(hypotenuse=300.0, width=28.0, thickness=0.3):
    hole_pts = [(0, hypotenuse * i) for i in [0.2, 0.5, 0.8]]
        
    template = (
        cq.Workplane("XY")
        .moveTo(0, hypotenuse / 2.0)
        .rect(width, hypotenuse)
        .extrude(thickness)
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .pushPoints(hole_pts)
        .hole(4.0)
    )
    return template

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Circular Saw Bracket")
    parser.add_argument("--units", type=int, default=1, help="Width of bracket in 28mm units")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--hypotenuse", type=float, default=300.0, help="Length of the 45-degree sloping face")
    parser.add_argument("--web-side", choices=["left", "right", "both"], default="both", help="Side of the bracket the web is flush with")
    args = parser.parse_args()
    
    sides = ["left", "right"] if args.web_side == "both" else [args.web_side]
    
    for side in sides:
        bracket = create_saw_bracket(
            units=args.units,
            rail_height=args.rail_height,
            hypotenuse=args.hypotenuse,
            web_side=side
        )
        
        # We need to bypass export_stl's auto-rotator to perfectly orient each handed side
        # so they both lay flat with slots facing up.
        # If side is left, the web is at -14. We want X=-14 to be Z=0.
        # So we rotate -90 around Y. (Z_new = X, -14 becomes -14, slicer drops it to 0).
        # If side is right, the web is at +14. We want X=+14 to be Z=0.
        # So we rotate 90 around Y. (Z_new = -X, 14 becomes -14, slicer drops it to 0).
        rot_angle = -90 if side == "left" else 90
        
        oriented_bracket = bracket.rotate((0,0,0), (0,1,0), rot_angle)
        
        filename = f"circular_saw_bracket_{args.units}u_L{int(args.hypotenuse)}_{side}.stl"
        # pass rotate_for_printing=False since we already rotated it
        export_model(oriented_bracket, filename, rotate_for_printing=False, category='tool_holders')
        print(f"Exported {filename}")
    
    template = create_drilling_template(
        hypotenuse=args.hypotenuse,
        width=args.units * 28.0
    )
    template_filename = f"circular_saw_template_{args.units}u_L{int(args.hypotenuse)}.stl"
    export_model(template, template_filename, rotate_for_printing=False, category='tool_holders')
    print(f"Exported {template_filename}")

if __name__ == "__main__":
    main()
