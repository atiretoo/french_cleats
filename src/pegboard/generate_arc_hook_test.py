import cadquery as cq
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_library import export_stl

def create_arc_hook_test():
    width = 20.0
    plate_thickness = 6.0
    
    top_y = 20.0
    top_hook_y = 5.5
    bottom_peg_y = 5.5 - 25.4
    bottom_y = bottom_peg_y - 10.0
    
    from pegboard.coupon_utils import create_test_coupon_base
    base = create_test_coupon_base(width=20.0, plate_thickness=6.0, top_y=top_y, bottom_y=bottom_y)
    
    top_hook_dia = 5.0
    bot_peg_dia = 6.5
    embed_z = plate_thickness / 2.0
    
    # ARC Top Hook
    # We want a continuous arc with radius R=17.5mm sweeping 45 degrees.
    # The center of the arc is at Y = top_hook_y + 17.5, Z = plate_thickness.
    # We will build it by sweeping a circle along a wire.
    R = 17.5
    
    # Path in YZ plane
    # Start at (Y=0, Z=0) relative to hook center at plate back
    # Center of arc is at (Y=R, Z=0)
    # End of arc is at 45 degrees
    import math
    end_y = R - R * math.cos(math.radians(45))
    end_z = R * math.sin(math.radians(45))
    
    path = cq.Workplane("YZ").center(top_hook_y, plate_thickness).moveTo(0, 0).radiusArc((end_y, end_z), R)
    
    # The sweep
    arc_hook = cq.Workplane("XY").workplane(offset=plate_thickness).center(0, top_hook_y).circle(top_hook_dia/2).sweep(path)
    
    # Embed cylinder (straight Z from embed_z to plate_thickness)
    embed_cyl = cq.Solid.makeCylinder(top_hook_dia/2, plate_thickness - embed_z, cq.Vector(0, top_hook_y, embed_z), cq.Vector(0,0,1))
    
    # Sphere cap at the end of the arc
    # The tangent at the end of the arc is at 45 degrees.
    # makeSphere generates a full sphere so tangent doesn't matter.
    sph = cq.Solid.makeSphere(top_hook_dia/2, cq.Vector(0, top_hook_y + end_y, plate_thickness + end_z), cq.Vector(0,0,1), -90)
    
    top_hook = arc_hook.union(cq.Workplane(embed_cyl)).union(cq.Workplane(sph))
    
    # 6.5mm Bottom Peg
    bot_p0 = cq.Vector(0, bottom_peg_y, embed_z)
    bot_dir = cq.Vector(0, 0, 1)
    bot_L = (plate_thickness - embed_z) + 5.0
    bot_p1 = bot_p0 + bot_dir * bot_L
    
    bot_cyl = cq.Solid.makeCylinder(bot_peg_dia/2, bot_L, bot_p0, bot_dir)
    bot_sph = cq.Solid.makeSphere(bot_peg_dia/2, bot_p1, cq.Vector(0,0,1), -90)
    
    bottom_peg = cq.Workplane(bot_cyl).union(cq.Workplane(bot_sph))
    
    result = base.union(top_hook).union(bottom_peg)
    
    result = result.rotate((0,0,0), (0,1,0), 45)
    
    return result

def main():
    model = create_arc_hook_test()
    filename = "arc_hook_test_coupon.stl"
    export_stl(model, filename, category='pegboard_tests', print_orientation='face_down')
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
