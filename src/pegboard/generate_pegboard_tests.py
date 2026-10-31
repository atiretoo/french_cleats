import os
import sys
import math
import cadquery as cq

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import export_stl

def create_test_block(mount_type="classic"):
    # 1U dimensions
    width = 28.0
    top_y = 20.0
    bottom_y = -33.0 # Compact 1U block
    plate_thickness = 6.0
    
    adapter = (
        cq.Workplane("XY")
        .box(width, top_y - bottom_y, plate_thickness)
        .translate((0, (top_y + bottom_y) / 2.0, plate_thickness / 2.0))
    )
    
    # We won't cut nut slots, just provide a solid block with the pegboard mount on the back
    # so the user can print it quickly to test the physical fit.
    
    # Label the front
    adapter = (
        adapter.faces("<Z").workplane()
        .text(mount_type, 6, -1.0) # Engrave text 1mm deep
    )
    
    # Back face is at Z = plate_thickness = 6.0
    # Top hook at Y = 10.0
    # Bottom hook at Y = 10.0 - 25.4 = -15.4
    top_y_pos = 10.0
    bot_y_pos = 10.0 - 25.4
    
    embed_z = 3.0
    peg_dia = 5.2 # Slightly looser for easier fit
    
    x = 0.0
    
    if mount_type == "classic":
        # Swept circular hook
        path_pts = [
            (top_y_pos, embed_z),
            (top_y_pos, embed_z + 3), # straight for 3mm
            (top_y_pos + 6, embed_z + 9), # 45 deg up
            (top_y_pos + 12, embed_z + 9) # straight up
        ]
        path = cq.Workplane("YZ").polyline(path_pts)
        
        # We need the profile normal to the path start.
        # Start is along Z axis, so profile is in XY plane
        hook = cq.Workplane("XY").workplane(offset=embed_z).center(x, top_y_pos).circle(peg_dia/2).sweep(path)
        adapter = adapter.union(hook)
        
        # Bottom peg
        bot = cq.Workplane("XY").workplane(offset=embed_z).center(x, bot_y_pos).circle(peg_dia/2).extrude(10.0 + (6.0 - embed_z))
        adapter = adapter.union(bot)
        
    elif mount_type == "slide_wedge":
        # Straight peg with a downward notch
        # Peg is 5.2mm dia, goes straight back for 12mm
        peg = cq.Workplane("XY").workplane(offset=embed_z).center(x, top_y_pos).circle(peg_dia/2).extrude(12.0 + (6.0 - embed_z))
        
        # Notch cut from the top to allow wedge
        notch = cq.Workplane("XY").workplane(offset=6.0 + 3.0).center(x, top_y_pos).rect(6, 6).extrude(5.0)
        # Wait, wedge slides in from front? The research doc says:
        # "A separate printed vertical locking pin or sliding clip is pushed down into the remaining gap from the front"
        # If it's pushed down from the front, the pegboard hole is round.
        # The peg is a half-cylinder (bottom half of the hole).
        
        # Let's make a D-shaped peg (flat on top)
        # Actually, simpler: draw D shape
        
        # Just use a smaller cylinder placed at the bottom of the hole
        # Hole is 6.35. Bottom of hole is Y = top_y_pos - 6.35/2 = top_y_pos - 3.175
        # If peg is 4.0 dia, center it at Y = top_y_pos - 3.175 + 2.0 = top_y_pos - 1.175
        small_peg = cq.Workplane("XY").workplane(offset=embed_z).center(x, top_y_pos - 1.0).circle(4.0/2).extrude(12.0 + (6.0 - embed_z))
        adapter = adapter.union(small_peg)
        
        # Bottom peg same
        bot = cq.Workplane("XY").workplane(offset=embed_z).center(x, bot_y_pos).circle(peg_dia/2).extrude(10.0 + (6.0 - embed_z))
        adapter = adapter.union(bot)
        
    elif mount_type == "snap_fit":
        # Split barb rivet
        # Outer diameter 6.0mm. Inner slit 2.0mm.
        # Length 6.35 (board) + 3.0 (barb) = 9.35
        l_total = 9.5 + (6.0 - embed_z)
        
        # We can extrude a circle, then cut a slot, then add barbs
        rivet = cq.Workplane("XY").workplane(offset=embed_z).center(x, top_y_pos).circle(6.0/2).extrude(l_total)
        
        # Barbs at the end (Z = embed_z + l_total)
        # A cone that tapers back
        cone_base = cq.Vector(x, top_y_pos, embed_z + l_total - 3.0)
        cone_dir = cq.Vector(0, 0, 1)
        barb_solid = cq.Solid.makeCone(3.5, 3.0, 3.0, cone_base, cone_dir)
        rivet = rivet.union(cq.Workplane(barb_solid))
        
        # Cut vertical slit
        slit = cq.Workplane("XZ").workplane(offset=top_y_pos).center(x, embed_z + 4.0).rect(2.0, l_total * 2).extrude(10.0, both=True)
        rivet = rivet.cut(slit)
        
        adapter = adapter.union(rivet)
        
        # Same for bottom peg (snap fit too)
        rivet_bot = cq.Workplane("XY").workplane(offset=embed_z).center(x, bot_y_pos).circle(6.0/2).extrude(l_total)
        
        bot_cone_base = cq.Vector(x, bot_y_pos, embed_z + l_total - 3.0)
        barb_bot_solid = cq.Solid.makeCone(3.5, 3.0, 3.0, bot_cone_base, cone_dir)
        rivet_bot = rivet_bot.union(cq.Workplane(barb_bot_solid))
        
        slit_bot = cq.Workplane("XZ").workplane(offset=bot_y_pos).center(x, embed_z + 4.0).rect(2.0, l_total * 2).extrude(10.0, both=True)
        rivet_bot = rivet_bot.cut(slit_bot)
        
        adapter = adapter.union(rivet_bot)
        
    elif mount_type == "bolt":
        # Through-hole for M4 bolt
        # Just a hole through the adapter
        hole = cq.Workplane("XY").workplane(offset=-10).center(x, top_y_pos).circle(4.5/2).extrude(50)
        hole_bot = cq.Workplane("XY").workplane(offset=-10).center(x, bot_y_pos).circle(4.5/2).extrude(50)
        adapter = adapter.cut(hole).cut(hole_bot)
        
    return adapter

def main():
    types = ["classic", "slide_wedge", "snap_fit", "bolt"]
    for t in types:
        print(f"Generating {t}...")
        adapter = create_test_block(t)
        filename = f"pegboard_test_{t}.stl"
        export_stl(adapter, filename, print_orientation='face_down', category='pegboard_tests')

if __name__ == "__main__":
    main()
