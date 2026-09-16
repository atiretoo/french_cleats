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

def export_stl(shape, filename, rotate_for_printing=True):
    import os
    import cadquery as cq
    
    export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports', 'stl')
    step_dir = os.path.join(os.path.dirname(__file__), '..', 'exports', 'step')
    
    out_path_stl = os.path.abspath(os.path.join(export_dir, filename))
    out_path_step = os.path.abspath(os.path.join(step_dir, filename.replace('.stl', '.step')))
    
    os.makedirs(os.path.dirname(out_path_stl), exist_ok=True)
    os.makedirs(os.path.dirname(out_path_step), exist_ok=True)
    
    export_shape = shape
    if rotate_for_printing:
        # Rotate around Y axis by 90 degrees to lay it on its side for optimal layer strength
        export_shape = export_shape.rotate((0, 0, 0), (0, 1, 0), 90)
        
    cq.exporters.export(export_shape, out_path_stl)
    cq.exporters.export(export_shape, out_path_step)
    print(f"Exported {out_path_stl} and {out_path_step}")
