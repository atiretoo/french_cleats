import cadquery as cq
import argparse
import math
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import create_baseplate, export_stl, create_nut_slot

def create_saw_bracket(units=1, rail_height=73.0, hypotenuse=300.0, web_side="left"):
    unit_width = 28.0
    width = units * unit_width
    brace_width = 10.0
    flange_thickness = 10.0
    
    if web_side == "left":
        web_x = -width/2
        joint_x = web_x + brace_width
        slot_x_dir = 1  # Slot breaks out to the right (+X)
    else:
        web_x = width/2 - brace_width
        joint_x = web_x
        slot_x_dir = -1 # Slot breaks out to the left (-X)
        
    # Generate the cleat mounting interface
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(units, rail_height, mount_type="groove", num_rows=2)
    
    drop = hypotenuse / math.sqrt(2)
    bracket_bottom = top_y - drop
    
    # Extend the backplate downwards
    if bracket_bottom < bottom_y:
        extra_drop = bottom_y - bracket_bottom
        extension_block = (
            cq.Workplane("XY")
            .box(width, extra_drop, 11.0)
            .translate((0, bottom_y - extra_drop/2.0, -11.0/2.0))
        )
        tool_holder = tool_holder.union(extension_block)
        
    # Create the 10mm thick triangular web
    web_pts = [
        (top_y, 0),
        (bracket_bottom, 0),
        (bracket_bottom, -drop)
    ]
    # Actually wait! Earlier we found the backplate front is Z=-11!
    web_pts = [
        (top_y, -11.0),
        (bracket_bottom, -11.0),
        (bracket_bottom, -11.0 - drop)
    ]
    
    web = (
        cq.Workplane("YZ")
        .polyline(web_pts).close()
        .extrude(brace_width)
        .translate((web_x, 0, 0))
    )
    
    # Create the 28mm wide hypotenuse flange
    dir_inward = cq.Vector(0, -1, 1).normalized()
    p1 = cq.Vector(0, top_y, -11.0)
    p2 = cq.Vector(0, bracket_bottom, -11.0 - drop)
    
    p1_in = p1 + dir_inward * flange_thickness
    p2_in = p2 + dir_inward * flange_thickness
    
    flange_pts = [
        (p1.y, p1.z),
        (p2.y, p2.z),
        (p2_in.y, p2_in.z),
        (p1_in.y, p1_in.z)
    ]
    
    flange = (
        cq.Workplane("YZ")
        .polyline(flange_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    
    body = tool_holder.union(web).union(flange)
    
    # Cut the triangular hole (15mm clearance)
    c1_y = bracket_bottom + 15
    c1_z = -26
    c2_y = top_y - 15 - 25*math.sqrt(2)
    c2_z = -26
    c3_y = bracket_bottom + 15
    c3_z = (bracket_bottom + 15) - top_y - 11 + 25*math.sqrt(2)
    
    cutout_pts = [
        (c1_y, c1_z),
        (c2_y, c2_z),
        (c3_y, c3_z)
    ]
    
    cutout = (
        cq.Workplane("YZ")
        .polyline(cutout_pts).close()
        .extrude(brace_width + 2.0)
        .translate((web_x - 1.0, 0, 0))
    )
    
    body = body.cut(cutout)
    
    class InnerFilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge): continue
                b = o.BoundingBox()
                # 1. Triangle cutout corners (parallel to X)
                if abs(b.xmax - b.xmin) > 5.0 and abs(b.ymax - b.ymin) < 0.1 and abs(b.zmax - b.zmin) < 0.1:
                    if (abs(b.ymin - c1_y) < 1 and abs(b.zmin - c1_z) < 1) or \
                       (abs(b.ymin - c2_y) < 1 and abs(b.zmin - c2_z) < 1) or \
                       (abs(b.ymin - c3_y) < 1 and abs(b.zmin - c3_z) < 1):
                        res.append(o)
                
                # 2. Joint edges are exactly at joint_x
                if abs(b.xmax - b.xmin) < 0.1 and abs(b.xmin - joint_x) < 0.1:
                    # Backplate-web joint (vertical at Z = -11.0)
                    if abs(b.zmax - (-11.0)) < 0.1 and abs(b.zmin - (-11.0)) < 0.1:
                        if o.Length() > 20:
                            res.append(o)
                    # Flange-web joint (diagonal, touches Z = -11.0)
                    elif abs(b.ymax - b.ymin) > 10 and abs(b.zmax - b.zmin) > 10:
                        if abs(b.zmax - (-11.0)) < 0.1:
                            res.append(o)
            return res

    try:
        body = body.edges(InnerFilletSelector()).fillet(4.99)
    except Exception as e:
        print(f"Warning: Could not apply all fillets: {e}")

    # Add captive nut slots
    normal_dir = cq.Vector(0, 1, -1).normalized()
    
    for i in [0.2, 0.5, 0.8]:
        y = top_y - drop * i
        z = -11.0 - drop * i
        pt = cq.Vector(0, y, z)
        
        # M3 clearance hole
        hole_wp = cq.Workplane(cq.Plane(origin=pt, xDir=(1,0,0), normal=normal_dir))
        cutter = hole_wp.circle(1.7).extrude(-15.0)
        body = body.cut(cutter)
        
        # Nut slot 
        nut_center = pt + normal_dir * (-5.0)
        slot_solid = create_nut_slot("M3", depth=14.0, push_hole=True)
        
        # Orient the slot so the bolt is along normal_dir and it slides along the X axis
        x_dir = cq.Vector(0, slot_x_dir, slot_x_dir).normalized()
        plane = cq.Plane(origin=nut_center, xDir=x_dir, normal=normal_dir)
        
        slot_solid = slot_solid.moved(cq.Location(plane))
        body = body.cut(slot_solid)

    # Cut cleat mounting screws
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
        .extrude(-200) 
    )
    body = body.cut(recesses)
    
    return body

def create_drilling_template(hypotenuse=300.0, width=28.0, thickness=0.3):
    hole_pts = []
    for i in [0.2, 0.5, 0.8]:
        y_pos = hypotenuse * i
        hole_pts.append((0, y_pos))
        
    template = (
        cq.Workplane("XY")
        .box(width, hypotenuse, thickness)
        .translate((0, hypotenuse/2, thickness/2))
        .faces(">Z").workplane()
        .pushPoints(hole_pts)
        .circle(4.0 / 2.0)
        .cutThruAll()
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
        export_stl(oriented_bracket, filename, rotate_for_printing=False, category='tool_holders')
        print(f"Exported {filename}")
    
    template = create_drilling_template(
        hypotenuse=args.hypotenuse,
        width=args.units * 28.0
    )
    template_filename = f"circular_saw_template_{args.units}u_L{int(args.hypotenuse)}.stl"
    export_stl(template, template_filename, rotate_for_printing=False, category='tool_holders')
    print(f"Exported {template_filename}")

if __name__ == "__main__":
    main()
