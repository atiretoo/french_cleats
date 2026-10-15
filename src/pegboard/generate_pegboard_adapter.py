import argparse
import os
import sys
import math
import cadquery as cq

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import export_stl, create_nut_slot, create_snap_fit_peg_parameterized, NUT_SLOT_TOLERANCE

def create_adapter(units=2, rail_height=73.0, screw_m="M3", top_hook="arc", top_hook_dia=6.5, bot_peg="snap", snap_dia=7.65):
    unit_width = 28.0
    width = units * unit_width
    
    if screw_m == "M3":
        screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
    elif screw_m == "M4":
        screw_d, nut_waf, nut_thick = 4.5, 7.0, 3.2
    elif screw_m == "M5":
        screw_d, nut_waf, nut_thick = 5.5, 8.0, 4.0
    else:
        raise ValueError(f"Unsupported screw size: {screw_m}")

    top_screw_y = 10.0
    bottom_screw_y = -rail_height - 1.0 - 10.0 # play = 1.0
    
    top_y = 20.0
    bottom_y = bottom_screw_y - 10.0
    
    plate_thickness = 6.0
    
    # Base Plate
    adapter = (
        cq.Workplane("XY")
        .box(width, top_y - bottom_y, plate_thickness)
        .translate((0, (top_y + bottom_y) / 2.0, plate_thickness / 2.0))
    )
    
    # Ridges on the Z=0 face pointing into -Z
    ridge_depth = 4.0
    
    def add_ridge(adapter_obj, y_center):
        pts = [
            (y_center + 4, 0),
            (y_center + 2, -ridge_depth),
            (y_center - 2, -ridge_depth),
            (y_center - 4, 0)
        ]
        ridge = (
            cq.Workplane("YZ")
            .polyline(pts).close()
            .extrude(width)
            .translate((-width/2, 0, 0))
        )
        return adapter_obj.union(ridge)
        
    adapter = add_ridge(adapter, top_screw_y)
    adapter = add_ridge(adapter, bottom_screw_y)
    

        
    # Pegboard Hooks
    # Top screw hole is at top_screw_y (10.0).
    # Bolt hole bottom is roughly at 10.0 - 1.5 = 8.5.
    # We place the hook right below the bolt hole to minimize the plate above it.
    top_hook_y = 5.5
    
    # Calculate how many 1-inch (25.4mm) spaces fit between top hook and bottom screw safe zone
    # Bottom screw hole is at bottom_screw_y. Its push hole extends upwards (+Y) by ~10mm.
    clear_bottom = bottom_screw_y + 15.0
    
    available_space = top_hook_y - clear_bottom
    num_spaces = max(1, int(available_space / 25.4))
    peg_vertical_spacing = num_spaces * 25.4
    
    bottom_peg_y = top_hook_y - peg_vertical_spacing
    
    bot_peg_dia = 6.5
    num_hooks = units
    hook_span = (num_hooks - 1) * 25.4
    
    # Embed the hooks into the baseplate so the angled cylinder doesn't leave a gap
    embed_z = plate_thickness / 2.0
    
    for i in range(num_hooks):
        x = -hook_span/2 + i*25.4
        
        # ----------------
        # Top Hook or Peg
        # ----------------
        import math
        
        if top_hook == "arc":
            R = 17.5
            end_y = R - R * math.cos(math.radians(45))
            end_z = R * math.sin(math.radians(45))
            path = cq.Workplane("YZ").center(top_hook_y, plate_thickness).moveTo(0, 0).radiusArc((end_y, end_z), R)
            arc_hook = cq.Workplane("XY").workplane(offset=plate_thickness).center(x, top_hook_y).circle(top_hook_dia/2).sweep(path)
            embed_cyl = cq.Solid.makeCylinder(top_hook_dia/2, plate_thickness - embed_z, cq.Vector(x, top_hook_y, embed_z), cq.Vector(0,0,1))
            sph = cq.Solid.makeSphere(top_hook_dia/2, cq.Vector(x, top_hook_y + end_y, plate_thickness + end_z), cq.Vector(0,0,1), -90)
            adapter = adapter.union(arc_hook).union(cq.Workplane(embed_cyl)).union(cq.Workplane(sph))
            
        elif top_hook == "snap":
            p0 = cq.Vector(x, top_hook_y, plate_thickness)
            snap_peg = create_snap_fit_peg_parameterized(p0, num_petals=3, band_dia=snap_dia)
            snap_embed = cq.Solid.makeCylinder(bot_peg_dia/2, plate_thickness - embed_z, cq.Vector(x, top_hook_y, embed_z), cq.Vector(0,0,1))
            adapter = adapter.union(snap_peg).union(cq.Workplane(snap_embed))
        
        # ----------------
        # Bottom Peg
        # ----------------
        if bot_peg == "solid":
            bot_p0 = cq.Vector(x, bottom_peg_y, embed_z)
            bot_dir = cq.Vector(0, 0, 1)
            bot_L = (plate_thickness - embed_z) + 5.0
            bot_p1 = bot_p0 + bot_dir * bot_L
            bot_cyl = cq.Solid.makeCylinder(bot_peg_dia/2, bot_L, bot_p0, bot_dir)
            bot_sph = cq.Solid.makeSphere(bot_peg_dia/2, bot_p1, cq.Vector(0,0,1), -90)
            adapter = adapter.union(cq.Workplane(bot_cyl)).union(cq.Workplane(bot_sph))
            
        elif bot_peg == "snap":
            p0 = cq.Vector(x, bottom_peg_y, plate_thickness)
            snap_peg = create_snap_fit_peg_parameterized(p0, num_petals=3, band_dia=snap_dia)
            snap_embed = cq.Solid.makeCylinder(bot_peg_dia/2, plate_thickness - embed_z, cq.Vector(x, bottom_peg_y, embed_z), cq.Vector(0,0,1))
            adapter = adapter.union(snap_peg).union(cq.Workplane(snap_embed))
        
    # Nut slots and screw holes
    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    slot_z_center = 2.0 + slot_t / 2.0
    
    for i in range(units):
        x = -width/2 + unit_width/2 + i*unit_width
        
        screw_hole_len = 10.0 + plate_thickness - 0.8
        
        # Top screw hole
        hole_top = cq.Workplane("XY").workplane(offset=-10).center(x, top_screw_y).circle(screw_d/2).extrude(screw_hole_len)
        adapter = adapter.cut(hole_top)
        
        # Top nut slot
        depth_top = top_y - top_screw_y
        slot_top_solid = create_nut_slot(screw_m, depth=depth_top, push_hole=True, push_hole_angle=30.0)
        slot_top_solid = slot_top_solid.translate(cq.Vector(x, top_screw_y, slot_z_center))
        adapter = adapter.cut(cq.Workplane(slot_top_solid))
        
        # Bottom screw hole
        hole_bot = cq.Workplane("XY").workplane(offset=-10).center(x, bottom_screw_y).circle(screw_d/2).extrude(screw_hole_len)
        adapter = adapter.cut(hole_bot)
        
        # Bottom nut slot
        depth_bot = bottom_screw_y - bottom_y
        slot_bot_solid = create_nut_slot(screw_m, depth=depth_bot, push_hole=True, push_hole_angle=30.0)
        slot_bot_solid = cq.Workplane(slot_bot_solid).rotate(cq.Vector(0,0,0), cq.Vector(0,0,1), 180).val()
        slot_bot_solid = slot_bot_solid.translate(cq.Vector(x, bottom_screw_y, slot_z_center))
        adapter = adapter.cut(cq.Workplane(slot_bot_solid))

    # Add 45 degree chamfer to left and right sides for printability
    # The back face is at Z = plate_thickness.
    # We want to cut off everything outside the 45 degree planes.
    # Right cutter:
    right_cut_pts = [
        (width/2, plate_thickness),                  # start at back right corner
        (width/2 - 50, plate_thickness - 50),        # go 45 deg down-left
        (width/2 + 50, plate_thickness - 50),        # go far right
        (width/2 + 50, plate_thickness)              # go up to complete the cut zone
    ]
    
    right_cutter = (
        cq.Workplane("XZ")
        .polyline(right_cut_pts).close()
        .extrude(1000, both=True)
    )
    
    # Left cutter:
    left_cut_pts = [
        (-width/2, plate_thickness),                 # start at back left corner
        (-width/2 + 50, plate_thickness - 50),       # go 45 deg down-right
        (-width/2 - 50, plate_thickness - 50),       # go far left
        (-width/2 - 50, plate_thickness)             # go up to complete the cut zone
    ]
    
    left_cutter = (
        cq.Workplane("XZ")
        .polyline(left_cut_pts).close()
        .extrude(1000, both=True)
    )
    
    adapter = adapter.cut(right_cutter).cut(left_cutter)
    
    # Rotate 45 degrees around Y so the right chamfered face lies flat on the -Z plane
    # The normal of the right face is (1, 0, -1). We want it to be (0, 0, -1).
    # A positive 45 deg rotation around Y achieves this.
    adapter = adapter.rotate((0,0,0), (0,1,0), 45)

    import math
    sin45 = math.sin(math.radians(45))
    
    # Calculate exactly how far to shift the right chamfered face down to Z=0
    # The right chamfer passes through (width/2, plate_thickness). After 45deg Y-rotation, 
    # its Z coordinate is (-width/2 + plate_thickness) * sin45.
    # Therefore we must shift it UP by (width/2 - plate_thickness) * sin45.
    z_shift = (width/2.0 - plate_thickness) * sin45
    adapter = adapter.translate((0, 0, z_shift))
    
    if units >= 2:
        from core_library import support_fin
        
        # The bottom face spans from X = (width/2 - plate_thickness)*sin45 to X = -(width/2 - plate_thickness)*sin45
        # The width of the fin is the difference, and the height is the same because of 45deg slope.
        fin_H = (width - 2.0 * plate_thickness) * sin45
        fin = support_fin(z_gap=0.0, is_right=True, length=fin_H, height=fin_H, fin_width=1.6)
        fin = fin.rotate((0,0,0), (0,0,1), 90)
        
        # The fin starts precisely at the front right edge (now at Z=0)
        fin_base_x = (width/2.0 - plate_thickness) * sin45
        
        # Place fins so the edge of the 0.4mm tip is flush with the end faces
        # tip_width is 0.4, so offset by 0.2 to make the tip flush with the edge
        fin_top = fin.translate((fin_base_x, top_y - 0.2, 0))
        fin_bot = fin.translate((fin_base_x, bottom_y + 0.2, 0))
        
        adapter = adapter.union(fin_top).union(fin_bot)

    return adapter

def main():
    parser = argparse.ArgumentParser(description="Generate Pegboard adapter for groove tool holders")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--rail-height", type=float, default=73.0, help="French cleat height in mm")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size")
    parser.add_argument("--generate-all", action="store_true", help="Generate all requested configurations (1U-4U, Arc+Snap & Snap+Snap)")
    
    args = parser.parse_args()
    
    if args.generate_all:
        configs = [
            ("arc", 6.5, "snap", 7.65),
            ("snap", 7.65, "snap", 7.65)
        ]
        for units in [1, 2, 3, 4]:
            for th_type, th_dia, bp_type, bp_dia in configs:
                adapter = create_adapter(units, args.rail_height, args.screw, top_hook=th_type, top_hook_dia=th_dia, bot_peg=bp_type, snap_dia=bp_dia)
                
                # Naming convention to distinguish
                if th_type == "arc":
                    name_modifier = "arc_snap"
                else:
                    name_modifier = "snap_snap"
                    
                filename = f"pegboard_adapter_{units}u_H{args.rail_height}_{args.screw}_{name_modifier}.stl"
                export_stl(adapter, filename, print_orientation='face_down', category='pegboard')
                print(f"Exported {filename}")
                
    else:
        # Default single generation
        adapter = create_adapter(args.units, args.rail_height, args.screw, top_hook="arc", top_hook_dia=6.5, bot_peg="snap", snap_dia=7.65)
        filename = f"pegboard_adapter_{args.units}u_H{args.rail_height}_{args.screw}_arc_snap.stl"
        export_stl(adapter, filename, print_orientation='face_down', category='pegboard')
        print(f"Exported {filename}")

if __name__ == "__main__":
    main()
