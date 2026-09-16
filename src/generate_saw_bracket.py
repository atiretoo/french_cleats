import cadquery as cq
import argparse
import math
from holder_base import create_baseplate, export_stl

def create_saw_bracket(units=1, rail_height=73.0, hypotenuse=300.0, slope_dir="down-out"):
    unit_width = 28.0
    width = units * unit_width
    
    # Generate the cleat mounting interface
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(units, rail_height, mount_type="groove", num_rows=2)
    
    # Calculate vertical and horizontal drop for 45 degrees
    # sin(45) = cos(45) = 1 / sqrt(2)
    drop = hypotenuse / math.sqrt(2)
    
    bracket_bottom = top_y - drop
    
    # Extend the backplate downwards to support the large bracket
    if bracket_bottom < bottom_y:
        extra_drop = bottom_y - bracket_bottom
        extension_block = (
            cq.Workplane("XY")
            .box(width, extra_drop, 11.0)
            .translate((0, bottom_y - extra_drop/2.0, -11.0/2.0))
        )
        tool_holder = tool_holder.union(extension_block)
    
    # Create the 45-degree triangular arm
    if slope_dir == "down-out":
        # Slopes from the wall at the top, down and out to the front at the bottom
        pts = [
            (top_y, -11.0),
            (bracket_bottom, -11.0),
            (bracket_bottom, -11.0 - drop)
        ]
        # Normal vector for the slanted face is UP and OUT (+Y, -Z)
        normal_dir = cq.Vector(0, 1, -1)
    else:
        # Slopes from the front at the top, down and in to the wall at the bottom
        pts = [
            (top_y, -11.0),
            (top_y, -11.0 - drop),
            (bracket_bottom, -11.0)
        ]
        # Normal vector for the slanted face is UP and IN (+Y, +Z)
        normal_dir = cq.Vector(0, 1, 1)
        
    arm = (
        cq.Workplane("YZ")
        .polyline(pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    
    tool_holder = tool_holder.union(arm)
    
    # Add screw holes for attaching the wood plate
    class SlantedFaceSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Face): continue
                if o.geomType() == "PLANE":
                    n = o.normalAt()
                    # Check if normal roughly matches expected direction
                    expected = normal_dir.normalized()
                    if n.dot(expected) > 0.99:
                        res.append(o)
            return res

    # Create holes in the slanted face
    # We want to put 3 holes evenly spaced along the hypotenuse
    try:
        # Center of the face
        face_wp = cq.Workplane(tool_holder.faces(SlantedFaceSelector()).val())
        # The local coordinates of the face might be arbitrary. We can just cut simple cylinders 
        # using 3D coordinates.
        # Let's manually calculate the 3 points in global space and cut cylinders.
        hole_pts = []
        for i in [0.2, 0.5, 0.8]:
            if slope_dir == "down-out":
                y = top_y - drop * i
                z = -11.0 - drop * i
            else:
                y = top_y - drop * i
                z = -11.0 - drop * (1 - i)
            hole_pts.append((0, y, z))
            
        # Cut 4mm pilot holes for wood screws
        for pt in hole_pts:
            # We want to extrude into the body. The normal points OUT.
            # We can create a workplane at 'pt' with normal matching the face, and cut inwards.
            # normal_dir is pointing OUT. So we orient the workplane with normal_dir as Z.
            hole_wp = cq.Workplane(cq.Plane(origin=pt, xDir=(1,0,0), normal=normal_dir))
            
            # Pilot hole
            cutter = hole_wp.circle(2.0).extrude(-30.0) 
            # Countersink
            csink = hole_wp.circle(4.0).extrude(-5.0)
            
            tool_holder = tool_holder.cut(cutter).cut(csink)
    except Exception as e:
        print(f"Warning: Could not create screw holes: {e}")

    # Standard mounting screw cuts
    screws = (
        cq.Workplane("XY").workplane(offset=0)
        .pushPoints(screw_pts)
        .circle(3.6/2.0)
        .extrude(-20) 
    )
    tool_holder = tool_holder.cut(screws)
    
    recesses = (
        cq.Workplane("XY").workplane(offset=-8)
        .pushPoints(screw_pts)
        .circle(8.0/2.0) 
        .extrude(-200) 
    )
    tool_holder = tool_holder.cut(recesses)
    
    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Circular Saw Bracket")
    parser.add_argument("--units", type=int, default=1, help="Width of bracket in 28mm units")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--hypotenuse", type=float, default=300.0, help="Length of the 45-degree sloping face")
    parser.add_argument("--slope-dir", choices=["down-out", "down-in"], default="down-out", help="Slope direction")
    args = parser.parse_args()
    
    bracket = create_saw_bracket(
        units=args.units,
        rail_height=args.rail_height,
        hypotenuse=args.hypotenuse,
        slope_dir=args.slope_dir
    )
    
    filename = f"circular_saw_bracket_{args.units}u_L{int(args.hypotenuse)}_{args.slope_dir}.stl"
    export_stl(bracket, filename)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
