import cadquery as cq
import argparse
import sys, os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import create_baseplate, export_stl

def create_power_tool_holder(units=2, length=140.0, slot_width=45.0, slot_length=120.0, mount_type="groove", web_thickness=5.5):
    unit_width = 28.0
    width = units * unit_width
    backplate_thickness = 11.0
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=4) # Power tools are heavy, maybe 4 rows for multiconnect
    
    # Shelf thickness
    shelf_t = 5.0 # Reduced for clearance of screw holes
    
    # Create the main shelf block
    shelf = (
        cq.Workplane("XY")
        .workplane(offset=-backplate_thickness)
        .center(0, top_y - shelf_t/2)
        .box(width, shelf_t, length, centered=(True, True, False))
    )
    # The box is centered on XY, and goes into Z. Wait, box(..., centered=(True, True, False)) 
    # means it grows in positive Z from the workplane.
    # But we want it to grow in negative Z!
    # Workplane normal is +Z. So we need to extrude in -Z.
    # It's easier to use a sketch and extrude.
    shelf = (
        cq.Workplane("XY")
        .workplane(offset=-backplate_thickness)
        .center(0, top_y - shelf_t/2)
        .rect(width, shelf_t)
        .extrude(-length)
    )
    body = body.union(shelf)
    
    # Create the triangular side braces
    # They go from the front of the shelf (Z = -backplate_thickness - length, Y = top_y - shelf_t)
    # down to the bottom of the baseplate (Z = -backplate_thickness, Y = bottom_y)
    
    front_z = -backplate_thickness - length
    back_z = -backplate_thickness
    
    # Let's draw the brace profile on the YZ plane and extrude it across X.
    # YZ Workplane maps Local X = Global Y, Local Y = Global Z.
    brace_pts = [
        (top_y - shelf_t, back_z),         # Top back
        (top_y - shelf_t, front_z),        # Front tip
        (bottom_y, back_z),                # Bottom back
    ]
    
    # We have two braces, one on the left, one on the right.
    # Left brace (X goes from -width/2 to -width/2 + web_thickness)
    left_brace = (
        cq.Workplane("YZ", origin=(-width/2, 0, 0))
        .polyline(brace_pts).close()
        .extrude(web_thickness)
    )
    # Right brace (X goes from width/2 - web_thickness to width/2)
    right_brace = (
        cq.Workplane("YZ", origin=(width/2 - web_thickness, 0, 0))
        .polyline(brace_pts).close()
        .extrude(web_thickness)
    )
    
    body = body.union(left_brace).union(right_brace)
    
    # Now cut the U-slot
    # The slot starts at the front (Z = front_z) and goes back by slot_length.
    # Back of the slot is at Z = front_z + slot_length.
    slot_back_z = front_z + slot_length
    
    # The slot is a rectangle with a semi-circle at the back.
    # It cuts all the way through the shelf vertically.
    
    # We can use cq.Workplane("ZX")
    # Z is from front_z to slot_back_z
    slot_cutter = (
        cq.Workplane("ZX", origin=(0, top_y + 10, 0))
        .moveTo(-slot_width/2, front_z)
        .lineTo(slot_width/2, front_z)
        .lineTo(slot_width/2, slot_back_z - slot_width/2)
        .threePointArc((0, slot_back_z), (-slot_width/2, slot_back_z - slot_width/2))
        .close()
        .extrude(-50) # Cut downwards
    )
    
    body = body.cut(slot_cutter)
    
    # Add triangular cutouts to the braces
    z1, y1 = front_z, top_y - shelf_t
    z2, y2 = back_z, bottom_y
    
    dz = z2 - z1
    dy = y2 - y1
    L = math.hypot(dz, dy)
    
    nx = -dy / L
    ny = dz / L
    
    offset = 15.0
    pz = z1 + nx * offset
    py = y1 + ny * offset
    
    m = dy / dz
    b = py - m * pz
    
    c1_z = z2 - 15
    c1_y = y1 - 15
    
    c2_z = (y1 - 15 - b) / m
    c2_y = y1 - 15
    
    c3_z = z2 - 15
    c3_y = m * (z2 - 15) + b
    
    if c2_z < c1_z and c3_y < c1_y:
        # Use (Y, Z) for YZ workplane
        cutout_pts = [
            (c1_y, c1_z),
            (c2_y, c2_z),
            (c3_y, c3_z)
        ]
        cutout = (
            cq.Workplane("YZ", origin=(0,0,0))
            .polyline(cutout_pts).close()
            .extrude(width, both=True)
        )
        
        cutout = cutout.edges("|X").fillet(5.0)
        body = body.cut(cutout)
        
    # Add fillets to the inside edges of the braces and shelf where they meet the backplate
    class InnerFilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if o.ShapeType() == 'Edge':
                    b = o.BoundingBox()
                    # Vertical inner corners of braces (parallel to Y, at Z=-11, |X| = 28 - 5.5 = 22.5)
                    if abs(b.ymax - b.ymin) > 1.0 and abs(b.xmax - b.xmin) < 0.1 and abs(b.zmax - b.zmin) < 0.1:
                        if abs(b.zmin - back_z) < 0.1 and abs(abs(b.xmin) - (width/2.0 - web_thickness)) < 0.1:
                            res.append(o)
                    # Horizontal corner of shelf (parallel to X, at Z=-11, Y = 15.0)
                    if abs(b.xmax - b.xmin) > 1.0 and abs(b.ymax - b.ymin) < 0.1 and abs(b.zmax - b.zmin) < 0.1:
                        if abs(b.zmin - back_z) < 0.1 and abs(b.ymin - (top_y - shelf_t)) < 0.1:
                            res.append(o)
            return res
            
    body = body.edges(InnerFilletSelector()).fillet(4.0)
        
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
    
    # Finally, rotate it 180 degrees around X so it prints upside down!
    # Baseplate is normally facing Y. If we rotate 180 around X, Y becomes -Y, Z becomes -Z.
    body = body.rotate((0,0,0), (1,0,0), 180)
    
    return body

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--units", type=int, default=2)
    parser.add_argument("--length", type=float, default=140.0)
    parser.add_argument("--slot-width", type=float, default=45.0)
    parser.add_argument("--slot-length", type=float, default=120.0)
    parser.add_argument("--mount", type=str, default="groove")
    
    args = parser.parse_args()
    
    holder = create_power_tool_holder(
        units=args.units,
        length=args.length,
        slot_width=args.slot_width,
        slot_length=args.slot_length,
        mount_type=args.mount
    )
    
    filename = f"power_tool_holder_{args.units}u_L{args.length}_{args.mount}.stl"
    export_stl(holder, filename, print_orientation="top_down", category="tool_holders")
