import cadquery as cq
import argparse
import math
from holder_base import create_baseplate, export_stl

def create_saw_bracket(units=1, rail_height=73.0, hypotenuse=300.0):
    unit_width = 28.0
    width = units * unit_width
    brace_width = 10.0
    flange_thickness = 10.0
    
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
        (top_y, -11.0),
        (bracket_bottom, -11.0),
        (bracket_bottom, -11.0 - drop)
    ]
    web = (
        cq.Workplane("YZ")
        .polyline(web_pts).close()
        .extrude(brace_width)
        .translate((-brace_width/2, 0, 0))
    )
    
    # Create the 28mm wide hypotenuse flange (10mm thick, inwards)
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
    c2_y = top_y - 11 - 15 - 15*math.sqrt(2)
    c2_z = -26
    c3_y = bracket_bottom + 15
    c3_z = (bracket_bottom + 15) - top_y - 11 + 15*math.sqrt(2)
    
    cutout_pts = [
        (c1_y, c1_z),
        (c2_y, c2_z),
        (c3_y, c3_z)
    ]
    
    cutout = (
        cq.Workplane("YZ")
        .polyline(cutout_pts).close()
        .extrude(brace_width + 2.0)
        .translate((-(brace_width + 2.0)/2, 0, 0))
    )
    
    body = body.cut(cutout)
    
    class InnerFilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge): continue
                b = o.BoundingBox()
                if abs(b.xmax - b.xmin) > 5.0 and abs(b.ymax - b.ymin) < 0.1 and abs(b.zmax - b.zmin) < 0.1:
                    if (abs(b.ymin - c1_y) < 1 and abs(b.zmin - c1_z) < 1) or \
                       (abs(b.ymin - c2_y) < 1 and abs(b.zmin - c2_z) < 1) or \
                       (abs(b.ymin - c3_y) < 1 and abs(b.zmin - c3_z) < 1):
                        res.append(o)
                
                if abs(b.xmax - b.xmin) < 0.1 and (abs(b.xmin - brace_width/2) < 0.1 or abs(b.xmin - (-brace_width/2)) < 0.1):
                    if abs(b.zmax - (-11.0)) < 0.1 and abs(b.zmin - (-11.0)) < 0.1:
                        if o.Length() > 20:
                            res.append(o)
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
        
        # M3 clearance hole (3.4mm diameter)
        hole_wp = cq.Workplane(cq.Plane(origin=pt, xDir=(1,0,0), normal=normal_dir))
        cutter = hole_wp.circle(1.7).extrude(-15.0)
        body = body.cut(cutter)
        
        # Nut slot
        slot_center = pt + normal_dir * (-5.0) 
        slot_center.x = 7.0 
        
        slot = cq.Solid.makeBox(15.0, 6.0, 3.0)
        slot = slot.translate((-7.5, -3.0, -1.5)) 
        slot = slot.rotate(cq.Vector(0,0,0), cq.Vector(1,0,0), -45)
        slot = slot.translate((7.5, slot_center.y, slot_center.z))
        
        body = body.cut(slot)

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
    """
    Creates a thin template strip to mark hole positions on the wooden plate.
    Holes are slightly larger than M3 clearance (4.0mm) for easy marking.
    """
    hole_pts = []
    # In the template, we'll lay it flat on the XY plane.
    # The length goes along Y (from 0 to hypotenuse).
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
    args = parser.parse_args()
    
    bracket = create_saw_bracket(
        units=args.units,
        rail_height=args.rail_height,
        hypotenuse=args.hypotenuse
    )
    
    template = create_drilling_template(
        hypotenuse=args.hypotenuse,
        width=args.units * 28.0
    )
    
    bracket_filename = f"circular_saw_bracket_{args.units}u_L{int(args.hypotenuse)}_thinned.stl"
    export_stl(bracket, bracket_filename)
    print(f"Exported {bracket_filename}")
    
    # Export template (don't rotate it, it's already flat on XY)
    template_filename = f"circular_saw_template_{args.units}u_L{int(args.hypotenuse)}.stl"
    export_stl(template, template_filename, rotate_for_printing=False)
    print(f"Exported {template_filename}")

if __name__ == "__main__":
    main()
