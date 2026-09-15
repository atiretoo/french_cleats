import cadquery as cq
import argparse
import os

def load_mc_block(filename, opengrid_path):
    path = os.path.join(opengrid_path, filename)
    model = cq.importers.importStep(path).val()
    bb = model.BoundingBox()
    dx = - (bb.xmin + bb.xmax) / 2
    dy = - (bb.ymin + bb.ymax) / 2
    # We want the solid back (zmin of original) to be at Z=0
    # And the slot opening to be at Z=6.4 (facing the wall)
    dz = - bb.zmin
    return model.translate((dx, dy, dz))

def create_adapter(units=2, rail_height=73.0, screw_m="M3", opengrid_path=None):
    if opengrid_path is None:
        opengrid_path = os.path.expanduser("~/Desktop/3dp/opengrid/Multiconnect modeling files")
        
    unit_width = 28.0
    width = units * unit_width
    
    if screw_m == "M3":
        screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
    elif screw_m == "M4":
        screw_d, nut_waf, nut_thick = 4.5, 7.0, 3.2
    elif screw_m == "M5":
        screw_d, nut_waf, nut_thick = 5.5, 8.0, 4.0

    top_screw_y = 10.0
    bottom_screw_y = -rail_height - 1.0 - 10.0 # play = 1.0
    
    top_y = 20.0
    bottom_y = bottom_screw_y - 10.0
    
    num_rows = int(rail_height / 28)
    if num_rows < 1:
        num_rows = 1
        
    stack_height = num_rows * 28.0 + 14.0
    stack_center_y = (top_screw_y + bottom_screw_y) / 2.0
    
    try:
        top_block = load_mc_block('top-back.step', opengrid_path)
        mid_block = load_mc_block('raw-slot-back.step', opengrid_path)
        bot_block = load_mc_block('embed-back-end.step', opengrid_path)
        cutter = load_mc_block('slot-opening.step', opengrid_path).translate((0, 0, 6.4 - 4.15))
    except Exception as e:
        print(f"Error loading Multiconnect STEP files from {opengrid_path}: {e}")
        print("Please ensure the path is correct or pass it via --opengrid-path.")
        return cq.Workplane("XY")
    
    adapter = cq.Workplane("XY")
    
    mc_solids = []
    for c in range(units):
        x_center = -width/2 + 14.0 + c*28.0
        
        # Calculate Y positions relative to the stack center
        # The stack goes from y = stack_center_y + stack_height/2 to y = stack_center_y - stack_height/2
        stack_top_y = stack_center_y + stack_height / 2.0
        
        y_top_block = stack_top_y - 14.0
        inst = top_block.translate((x_center, y_top_block, 0))
        mc_solids.append(inst)
        
        for r in range(1, num_rows):
            y_mid_block = stack_top_y - 14.0 - r*28.0
            inst = mid_block.translate((x_center, y_mid_block, 0))
            mc_solids.append(inst)
            
        y_bot_block = stack_top_y - num_rows*28.0 - 7.0
        inst = bot_block.translate((x_center, y_bot_block, 0))
        mc_solids.append(inst)
        
    for solid in mc_solids:
        adapter = adapter.union(cq.Workplane(solid))
        
    # Cut the full circular openings for the middle sections using slot-opening.step
    for c in range(units):
        x_center = -width/2 + 14.0 + c*28.0
        stack_top_y = stack_center_y + stack_height / 2.0
        for r in range(1, num_rows + 1):
            opening_y = stack_top_y - r * 28.0
            cut_inst = cutter.translate((x_center, opening_y, 0))
            adapter = adapter.cut(cq.Workplane(cut_inst))
            
    # Fill the gaps above and below the stack with 6.4mm solid boxes
    stack_top_y = stack_center_y + stack_height / 2.0
    stack_bot_y = stack_center_y - stack_height / 2.0
    
    if top_y > stack_top_y:
        gap_height = top_y - stack_top_y
        gap_center_y = stack_top_y + gap_height / 2.0
        top_filler = cq.Workplane("XY").box(width, gap_height, 6.4).translate((0, gap_center_y, 3.2))
        adapter = adapter.union(top_filler)
        
    if bottom_y < stack_bot_y:
        gap_height = stack_bot_y - bottom_y
        gap_center_y = stack_bot_y - gap_height / 2.0
        bot_filler = cq.Workplane("XY").box(width, gap_height, 6.4).translate((0, gap_center_y, 3.2))
        adapter = adapter.union(bot_filler)
        
    # Ridges on the Z=0 face pointing into -Z
    ridge_depth = 4.0
    
    top_ridge_pts = [
        (top_screw_y + 4, 0),
        (top_screw_y + 2, -ridge_depth),
        (top_screw_y - 2, -ridge_depth),
        (top_screw_y - 4, 0)
    ]
    
    top_ridge = (
        cq.Workplane("YZ")
        .polyline(top_ridge_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    adapter = adapter.union(top_ridge)
    
    bot_ridge_pts = [
        (bottom_screw_y + 4, 0),
        (bottom_screw_y + 2, -ridge_depth),
        (bottom_screw_y - 2, -ridge_depth),
        (bottom_screw_y - 4, 0)
    ]
    
    bot_ridge = (
        cq.Workplane("YZ")
        .polyline(bot_ridge_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    adapter = adapter.union(bot_ridge)
    
    # Nut slots and screw holes
    slot_t = nut_thick + 0.1
    slot_z_center = 2.0 + slot_t / 2.0
    
    for i in range(units):
        x = -width/2 + unit_width/2 + i*unit_width
        
        # Top screw hole
        hole_top = cq.Workplane("XY").workplane(offset=-10).center(x, top_screw_y).circle(screw_d/2).extrude(50)
        adapter = adapter.cut(hole_top)
        
        # Top nut slot
        slot_h_top = top_y - (top_screw_y - nut_waf/2.0)
        slot_y_center_top = top_y - slot_h_top / 2.0
        slot_top = (
            cq.Workplane("XZ", origin=(x, slot_y_center_top, slot_z_center))
            .rect(nut_waf, slot_t)
            .extrude(slot_h_top / 2.0, both=True)
        )
        adapter = adapter.cut(slot_top)
        
        # Bottom screw hole
        hole_bot = cq.Workplane("XY").workplane(offset=-10).center(x, bottom_screw_y).circle(screw_d/2).extrude(50)
        adapter = adapter.cut(hole_bot)
        
        # Bottom nut slot
        slot_h_bot = (bottom_screw_y + nut_waf/2.0) - bottom_y
        slot_y_center_bot = bottom_y + slot_h_bot / 2.0
        slot_bot = (
            cq.Workplane("XZ", origin=(x, slot_y_center_bot, slot_z_center))
            .rect(nut_waf, slot_t)
            .extrude(slot_h_bot / 2.0, both=True)
        )
        adapter = adapter.cut(slot_bot)

    return adapter

def main():
    parser = argparse.ArgumentParser(description="Generate OpenGrid adapter for groove tool holders")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--rail-height", type=float, default=73.0, help="French cleat height in mm")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size")
    parser.add_argument("--opengrid-path", type=str, default=None, help="Path to Multiconnect Modeling Files")
    
    args = parser.parse_args()
    
    adapter = create_adapter(args.units, args.rail_height, args.screw, args.opengrid_path)
    filename = f"opengrid_adapter_{args.units}u_H{args.rail_height}_{args.screw}.stl"
    
    # Save to exports/stl directory relative to the project root
    export_stl(adapter, filename)

if __name__ == "__main__":
    main()
