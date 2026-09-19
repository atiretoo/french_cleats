import cadquery as cq
import os

def load_mc_block(filename):
    path = os.path.join(os.path.dirname(__file__), '../../opengrid/Multiconnect Modeling Files', filename)
    model = cq.importers.importStep(path).val()
    bb = model.BoundingBox()
    dx = - (bb.xmin + bb.xmax) / 2
    dy = - (bb.ymin + bb.ymax) / 2
    # We want the slot opening (zmax of original) to be at Z=0
    # And the solid back (zmin of original) to be at Z=-6.4
    dz = - bb.zmax
    return model.translate((dx, dy, dz))

def create_baseplate(units=2, rail_height=73.0, backplate_thickness=11.0, mount_type="groove", num_rows=2):
    unit_width = 28.0 
    width = units * unit_width
    
    if mount_type == "groove":
        t = 0.1
        ridge_depth = 4.0
        ridge_clearance = 0.5 
        play = 1.0
        
        bottom_groove_y = -rail_height - play - 10.0
        bottom_y = bottom_groove_y - 10.0
        
        pts = [
            (20, 0),
            (14+t, 0),
            (12+t, -ridge_depth - ridge_clearance),
            (8-t,  -ridge_depth - ridge_clearance),
            (6-t,  0),
            (bottom_groove_y + 4 + t, 0),
            (bottom_groove_y + 2 + t, -ridge_depth - ridge_clearance),
            (bottom_groove_y - 2 - t, -ridge_depth - ridge_clearance),
            (bottom_groove_y - 4 - t, 0),
            (bottom_y, 0),
            (bottom_y, -backplate_thickness),
            (20, -backplate_thickness),
            (20, 0)
        ]
        
        baseplate = (
            cq.Workplane("YZ")
            .polyline(pts).close()
            .extrude(width)
            .translate((-width/2, 0, 0))
        )
        
        screw_pts = []
        for i in range(units):
            x = -width/2 + unit_width/2 + i*unit_width
            screw_pts.extend([(x, 10), (x, bottom_groove_y)])
            
        return baseplate, 20.0, bottom_y, bottom_groove_y, screw_pts, []
        
    elif mount_type == "multiconnect":
        top_y = 28.0
        height = num_rows * 28.0 + 14.0
        bottom_y = top_y - height
        
        # OpenGrid multiconnect blocks are 6.4mm thick. 
        solid_thickness = max(0.01, backplate_thickness - 6.4)
        
        # solid box goes from Z=-6.4 down to Z=-backplate_thickness
        baseplate = (
            cq.Workplane("XY")
            .box(width, height, solid_thickness)
            .translate((0, top_y - height/2, -6.4 - solid_thickness/2))
        )
        
        top_block = load_mc_block('top-back.step')
        mid_block = load_mc_block('opening-raw-slot-back.step')
        bot_block = load_mc_block('embed-back-end.step')
        
        mc_solids = []
        for c in range(units):
            x_center = -width/2 + 14.0 + c*28.0
            
            y_top = 28.0 - 14.0
            inst = top_block.translate((x_center, y_top, 0))
            mc_solids.append(inst)
            
            for r in range(1, num_rows):
                y_mid = 28.0 - 14.0 - r*28.0
                inst = mid_block.translate((x_center, y_mid, 0))
                mc_solids.append(inst)
                
            y_bot = 28.0 - num_rows*28.0 - 7.0
            inst = bot_block.translate((x_center, y_bot, 0))
            mc_solids.append(inst)
                
        screw_pts = [] 
        bottom_groove_y = bottom_y + 10.0
        return baseplate, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids

def get_main_repo_root(current_dir):
    import subprocess
    try:
        common_git_dir = subprocess.check_output(
            ['git', 'rev-parse', '--git-common-dir'], 
            cwd=current_dir, 
            text=True, 
            stderr=subprocess.DEVNULL
        ).strip()
        abs_git_dir = os.path.abspath(os.path.join(current_dir, common_git_dir))
        return os.path.dirname(abs_git_dir)
    except Exception:
        # Fallback if git fails for some reason
        return os.path.join(current_dir, '..')

def export_stl(shape, filename, rotate_for_printing=None, category="", export_step=True, print_orientation="left_down"):
    import os
    import cadquery as cq
    
    current_dir = os.path.dirname(__file__)
    main_repo_root = get_main_repo_root(current_dir)
    
    export_dir = os.path.join(main_repo_root, 'exports', 'stl')
    step_dir = os.path.join(main_repo_root, 'exports', 'step')
    
    if category:
        export_dir = os.path.join(export_dir, category)
        step_dir = os.path.join(step_dir, category)
        
    out_path_stl = os.path.abspath(os.path.join(export_dir, filename))
    out_path_step = os.path.abspath(os.path.join(step_dir, filename.replace('.stl', '.step')))
    
    os.makedirs(os.path.dirname(out_path_stl), exist_ok=True)
    os.makedirs(os.path.dirname(out_path_step), exist_ok=True)
    
    # Backward compatibility for old boolean flag
    if rotate_for_printing is not None:
        if rotate_for_printing:
            print_orientation = "left_down"
        else:
            print_orientation = "back_down"
            
    export_shape = shape
    
    # Apply rotation based on desired print orientation
    # In CAD: Z=0 is back, -Z is front. +Y is top, -Y is bottom. +X is right, -X is left.
    if print_orientation == "left_down":
        # Rotate -X to point down (-Z)
        export_shape = export_shape.rotate((0, 0, 0), (0, 1, 0), 90)
    elif print_orientation == "right_down":
        # Rotate +X to point down (-Z)
        export_shape = export_shape.rotate((0, 0, 0), (0, 1, 0), -90)
    elif print_orientation == "top_down":
        # Rotate +Y to point down (-Z)
        export_shape = export_shape.rotate((0, 0, 0), (1, 0, 0), 90)
    elif print_orientation == "bottom_down":
        # Rotate -Y to point down (-Z)
        export_shape = export_shape.rotate((0, 0, 0), (1, 0, 0), -90)
    elif print_orientation == "back_down":
        # Rotate +Z to point down (-Z)
        export_shape = export_shape.rotate((0, 0, 0), (1, 0, 0), 180)
    elif print_orientation == "face_down":
        # -Z is already down. No rotation needed.
        pass
        
    cq.exporters.export(export_shape, out_path_stl)
    if export_step:
        cq.exporters.export(export_shape, out_path_step)
    if export_step:
        print(f"Exported {out_path_stl} and {out_path_step}")
    else:
        print(f"Exported {out_path_stl}")
import cadquery as cq
import math

def create_nut_slot(screw_m="M3", depth=10.0, push_hole=True, push_hole_angle=0.0):
    """
    Creates a nut capture slot (and optional push hole) centered at (0,0,0).
    - The bolt passes through the Z-axis.
    - The nut slides in from the +Y direction.
    - The slot width spans the X-axis.
    """
    if screw_m == "M3":
        nut_waf, nut_thick = 5.5, 2.4
    elif screw_m == "M4":
        nut_waf, nut_thick = 7.0, 3.2
    elif screw_m == "M5":
        nut_waf, nut_thick = 8.0, 4.0
    else:
        raise ValueError(f"Unsupported screw size: {screw_m}")
        
    slot_w = nut_waf + 0.1
    slot_t = nut_thick + 0.1
    
    # Distance from center to point of hexagon
    nut_point_dist = (nut_waf / 2.0) / math.cos(math.radians(30))
    
    slot_length = depth + nut_point_dist
    center_y = (depth - nut_point_dist) / 2.0
    
    slot = cq.Solid.makeBox(slot_w, slot_length, slot_t)
    slot = slot.translate((-slot_w/2.0, -slot_length/2.0, -slot_t/2.0))
    slot = slot.translate((0, center_y, 0))
    
    result = cq.Workplane(slot)
    
    if push_hole:
        # Create a 1.5mm cylinder starting at Y = -nut_point_dist and extending downwards (negative Y)
        # We will make it 100mm long to ensure it pierces the outer wall.
        cyl = cq.Solid.makeCylinder(0.75, 100.0, cq.Vector(0, 0, 0), cq.Vector(0, -1, 0))
        cyl = cyl.translate((0, -nut_point_dist, 0))
        
        if push_hole_angle != 0.0:
            # Rotate around X axis. 
            # If angle > 0, it rotates towards +Z.
            cyl = cyl.rotate(cq.Vector(0, -nut_point_dist, 0), cq.Vector(1, 0, 0), push_hole_angle)
            
        result = result.union(cq.Workplane(cyl))
        
    return result.val()
