# Copyright (C) 2026 Andrew Tyre
#
# This file is part of french_cleats.
#
# french_cleats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# french_cleats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with french_cleats.  If not, see <https://www.gnu.org/licenses/>.
import cadquery as cq
import os
import math

UNIT_WIDTH = 28.0
BACKPLATE_THICKNESS = 11.0

# Repository Asset Paths
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(REPO_ROOT, "assets")
MULTICONNECT_ASSETS_DIR = os.path.join(ASSETS_DIR, "multiconnect")
HSW_ASSETS_DIR = os.path.join(ASSETS_DIR, "hsw")

# Standard Wall & Ridge Spacing Constants
DEFAULT_RAIL_HEIGHT = 73.0
RAIL_PLAY = 1.0
BACKPLATE_TOP_Y = 20.0
TOP_RIDGE_Y = 10.0          # 10.0mm below top edge (Y = 20.0)
TOP_GROOVE_Y = 10.0

# Shallow Groove & Ridge Standard Constants (v2.0)
# Groove geometry (cut into backplate):
GROOVE_DEPTH = 3.0                     # Depth of groove cut into backplate (mm)
GROOVE_SURFACE_HALF_WIDTH = 3.5         # Half-width of groove at Z=0 (7.0mm surface opening)
GROOVE_BOTTOM_HALF_WIDTH = 0.5          # Half-width of flat bottom (1.0mm flat bottom at 45 deg)

# Ridge clearance standards:
RIDGE_SIDE_CLEARANCE = 0.45             # Sidewall clearance along Y on each 45-degree slope (mm)
RIDGE_DEPTH_CLEARANCE = 0.70            # Tip clearance along Z between ridge crest and groove bottom (mm)

# Derived Ridge geometry (raised projection on cleat):
RIDGE_HEIGHT = GROOVE_DEPTH - RIDGE_DEPTH_CLEARANCE                   # 2.30mm
RIDGE_SURFACE_HALF_WIDTH = GROOVE_SURFACE_HALF_WIDTH - RIDGE_SIDE_CLEARANCE  # 3.05mm (6.10mm base width)
RIDGE_PEAK_HALF_WIDTH = RIDGE_SURFACE_HALF_WIDTH - RIDGE_HEIGHT       # 0.75mm (1.50mm flat crest at 45 deg)

# Backward compatibility aliases
RIDGE_DEPTH = RIDGE_HEIGHT
RIDGE_CLEARANCE = RIDGE_DEPTH_CLEARANCE

def get_bottom_groove_y(rail_height=DEFAULT_RAIL_HEIGHT, play=RAIL_PLAY):
    return -rail_height - play - 10.0

def get_bottom_edge_y(rail_height=DEFAULT_RAIL_HEIGHT, play=RAIL_PLAY):
    return get_bottom_groove_y(rail_height, play) - 10.0

def get_backplate_height(rail_height=DEFAULT_RAIL_HEIGHT, play=RAIL_PLAY):
    return BACKPLATE_TOP_Y - get_bottom_edge_y(rail_height, play)

def load_mc_block(filename, base_dir=None):
    if base_dir is None:
        base_dir = MULTICONNECT_ASSETS_DIR
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Multiconnect asset not found: {path}")
    model = cq.importers.importStep(path).val()
    bb = model.BoundingBox()
    dx = - (bb.xmin + bb.xmax) / 2
    dy = - (bb.ymin + bb.ymax) / 2
    # We want the slot opening (zmax of original) to be at Z=0
    # And the solid back (zmin of original) to be at Z=-6.4
    dz = - bb.zmax
    return model.translate((dx, dy, dz))

def create_baseplate(units=2, rail_height=DEFAULT_RAIL_HEIGHT, backplate_thickness=11.0, mount_type="groove", num_rows=2):
    unit_width = UNIT_WIDTH
    width = units * unit_width
    
    if mount_type == "groove":
        t = 0.1
        ridge_depth = RIDGE_DEPTH
        ridge_clearance = RIDGE_CLEARANCE
        play = RAIL_PLAY
        
        bottom_groove_y = get_bottom_groove_y(rail_height, play)
        bottom_y = get_bottom_edge_y(rail_height, play)
        
        pts = [
            (BACKPLATE_TOP_Y - 2.0, 0),
            (TOP_GROOVE_Y + GROOVE_SURFACE_HALF_WIDTH, 0),
            (TOP_GROOVE_Y + GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (TOP_GROOVE_Y - GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (TOP_GROOVE_Y - GROOVE_SURFACE_HALF_WIDTH, 0),
            (bottom_groove_y + GROOVE_SURFACE_HALF_WIDTH, 0),
            (bottom_groove_y + GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (bottom_groove_y - GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (bottom_groove_y - GROOVE_SURFACE_HALF_WIDTH, 0),
            (bottom_y + 2.0, 0),
            (bottom_y, -2.0),
            (bottom_y, -backplate_thickness),
            (BACKPLATE_TOP_Y, -backplate_thickness),
            (BACKPLATE_TOP_Y, -2.0),
            (BACKPLATE_TOP_Y - 2.0, 0)
        ]
        
        baseplate = (
            cq.Workplane("YZ")
            .polyline(pts).close()
            .extrude(width)
            .translate((-width/2, 0, 0))
        )
        
        try:
            baseplate = baseplate.edges('>Y and <Z').fillet(min(2.5, backplate_thickness / 3.0))
        except Exception:
            pass
        
        screw_pts = []
        for i in range(units):
            x = -width/2 + unit_width/2 + i*unit_width
            screw_pts.extend([(x, TOP_GROOVE_Y), (x, bottom_groove_y)])
            
        return baseplate, BACKPLATE_TOP_Y, bottom_y, bottom_groove_y, screw_pts, []
        
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

class OuterFaceEdgesSelector(cq.Selector):
    def __init__(self, axis, val, tol=0.01):
        self.axis = axis
        self.val = val
        self.tol = tol
    def filter(self, objectList):
        res = []
        for o in objectList:
            if not isinstance(o, cq.Edge): continue
            bb = o.BoundingBox()
            if self.axis == 'X':
                at_face = abs(bb.xmin - self.val) < self.tol and abs(bb.xmax - self.val) < self.tol
            elif self.axis == 'Z':
                at_face = abs(bb.zmin - self.val) < self.tol and abs(bb.zmax - self.val) < self.tol
            elif self.axis == 'Y':
                at_face = abs(bb.ymin - self.val) < self.tol and abs(bb.ymax - self.val) < self.tol
            else:
                at_face = False
            if at_face and (o.geomType() != 'CIRCLE' or o.Length() > 20.0):
                res.append(o)
        return res

def apply_bed_chamfer(shape, print_orientation, dist=2.0):
    if shape is None or isinstance(shape, cq.Assembly) or print_orientation in ['none', None] or dist <= 0:
        return shape
    try:
        bb = shape.val().BoundingBox()
        if print_orientation == 'right_down':
            sel = OuterFaceEdgesSelector('X', bb.xmin)
        elif print_orientation == 'left_down':
            sel = OuterFaceEdgesSelector('X', bb.xmax)
        elif print_orientation == 'back_down':
            sel = OuterFaceEdgesSelector('Z', bb.zmax)
        elif print_orientation == 'face_down':
            sel = OuterFaceEdgesSelector('Z', bb.zmin)
        elif print_orientation == 'top_down':
            sel = OuterFaceEdgesSelector('Y', bb.ymax)
        elif print_orientation == 'bottom_down':
            sel = OuterFaceEdgesSelector('Y', bb.ymin)
        else:
            return shape
            
        edges = shape.edges(sel).vals()
        if edges:
            return shape.edges(sel).chamfer(dist)
    except Exception:
        pass
    return shape

def export_model(shape, filename, category="", export="both", print_orientation="left_down", rotate_for_printing=None, bed_chamfer=2.0):
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
            print_orientation = "none"
            
    export_shape = shape
    
    # Apply build plate perimeter chamfer if requested
    if bed_chamfer and bed_chamfer > 0:
        export_shape = apply_bed_chamfer(export_shape, print_orientation, dist=bed_chamfer)
    
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
    elif print_orientation in ["face_down", "none", None]:
        # -Z is already down (or raw orientation requested). No rotation needed.
        pass
        
    if isinstance(export_shape, cq.Assembly):
        export_shape.save(out_path_stl, exportType='STL')
        if export in ["both", "step"]:
            export_shape.save(out_path_step, exportType='STEP')
    else:
        cq.exporters.export(export_shape, out_path_stl)
        if export in ["both", "step"]:
            cq.exporters.export(export_shape, out_path_step)
    if export == "both":
        print(f"Exported {out_path_stl} and {out_path_step}")
    else:
        print(f"Exported {out_path_stl}")


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

def support_fin(z_gap=0.01, is_right=True, length=30.0, height=30.0, fin_width=1.6, tip_width=0.4, taper_z_drop=4.0, cutoff_top=True):
    """
    Generates a 45-degree support fin.
    Note: For the cleanest breakaway, use z_gap=0.0 mm if the fin tip is perfectly aligned 
    flush with an outer corner of the part. If placing the fin in the middle of a face, 
    default to z_gap=0.01 mm to ensure it lightly fuses with the perimeter.
    """
    import cadquery as cq
    Z_gap = z_gap
    
    start_y = max(0, Z_gap)
    end_y = length + min(0, Z_gap)
    
    start_z = start_y - Z_gap
    end_z = end_y - Z_gap
    
    if is_right:
        pts = [(start_y, 0), (start_y, start_z), (end_y, end_z), (end_y, 0)]
    else:
        pts = [(-start_y, 0), (-start_y, start_z), (-end_y, end_z), (-end_y, 0)]
        
    unique_pts = [pts[0]]
    for p in pts[1:]:
        if p != unique_pts[-1]:
            unique_pts.append(p)
    if len(unique_pts) > 1 and unique_pts[-1] == unique_pts[0]:
        unique_pts.pop()
        
    wedge = (
        cq.Workplane("YZ")
        .polyline(unique_pts).close()
        .extrude(fin_width)
        .translate((-fin_width/2.0, 0, 0))
    )
    
    prof_x1 = tip_width / 2.0
    prof_x2 = fin_width / 2.0
    
    prof_p = [(fin_width, 1.0), (prof_x1, 1.0), (prof_x1, 0.0), (prof_x2, -taper_z_drop), (fin_width, -taper_z_drop)]
    prof_n = [(-fin_width, 1.0), (-prof_x1, 1.0), (-prof_x1, 0.0), (-prof_x2, -taper_z_drop), (-fin_width, -taper_z_drop)]
    
    # We use XZ to map Local X = Global X, Local Y = Global Z
    if is_right:
        cut_p = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_p).close()
            .transformed(offset=(0, height+10, -(height+10)))
            .polyline(prof_p).close()
            .loft()
        )
        cut_n = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_n).close()
            .transformed(offset=(0, height+10, -(height+10)))
            .polyline(prof_n).close()
            .loft()
        )
    else:
        cut_p = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_p).close()
            .transformed(offset=(0, height+10, height+10))
            .polyline(prof_p).close()
            .loft()
        )
        cut_n = (
            cq.Workplane("XZ", origin=(0, 0, -Z_gap))
            .polyline(prof_n).close()
            .transformed(offset=(0, height+10, height+10))
            .polyline(prof_n).close()
            .loft()
        )
        
    # Prevent cutting below the print bed (Z < 0)
    box_size = max(500.0, height * 4, length * 4)
    bbox = cq.Workplane("XY").box(box_size, box_size, box_size).translate((0, 0, box_size / 2.0))
    cut_p = cut_p.intersect(bbox)
    cut_n = cut_n.intersect(bbox)
        
    fin = wedge.cut(cut_p).cut(cut_n)
    
    # Chop off the top of the fin where it gets too narrow in Y (prevents tiny tip blobs)
    if cutoff_top:
        cutoff_z = height - taper_z_drop
        fin = fin.cut(cq.Workplane("XY").box(box_size, box_size, box_size).translate((0, 0, cutoff_z + box_size / 2.0)))
        
    return fin
