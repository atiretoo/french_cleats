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
RIDGE_SIDE_CLEARANCE = 0.20             # Sidewall clearance along Y on each 45-degree slope (mm) - physically verified v2.0 standard
RIDGE_DEPTH_CLEARANCE = 0.80            # Tip clearance along Z between ridge crest and groove bottom (mm)

# Derived Ridge geometry (raised projection on cleat):
RIDGE_HEIGHT = GROOVE_DEPTH - RIDGE_DEPTH_CLEARANCE                   # 2.20mm
RIDGE_SURFACE_HALF_WIDTH = GROOVE_SURFACE_HALF_WIDTH - RIDGE_SIDE_CLEARANCE  # 3.30mm (6.60mm base width)
RIDGE_PEAK_HALF_WIDTH = RIDGE_SURFACE_HALF_WIDTH - RIDGE_HEIGHT       # 1.10mm (2.20mm flat crest at 45 deg)

# Metric Captive Nut Slot Tolerances
NUT_SLOT_TOLERANCE = 0.3                # +0.3mm tolerance along both axes (5.80mm x 2.70mm for M3)

# Backward compatibility aliases
RIDGE_DEPTH = RIDGE_HEIGHT
RIDGE_CLEARANCE = RIDGE_DEPTH_CLEARANCE

def get_groove_points(center_y):
    """
    Returns the 4 2D (Y, Z) points defining the standard shallow 45-degree groove cut into the backplate.
    Profile runs along +Y to -Y at Z=0, dipping to -GROOVE_DEPTH.
    """
    return [
        (center_y + GROOVE_SURFACE_HALF_WIDTH, 0.0),
        (center_y + GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
        (center_y - GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
        (center_y - GROOVE_SURFACE_HALF_WIDTH, 0.0),
    ]

def get_ridge_points(center_y):
    """
    Returns the 4 2D (Y, Z) points defining the standard shallow 45-degree locking ridge on cleats/adapters.
    Profile runs along +Y to -Y at Z=0, protruding to -RIDGE_HEIGHT into the groove.
    """
    return [
        (center_y + RIDGE_SURFACE_HALF_WIDTH, 0.0),
        (center_y + RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (center_y - RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (center_y - RIDGE_SURFACE_HALF_WIDTH, 0.0),
    ]

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
        play = RAIL_PLAY
        
        bottom_groove_y = get_bottom_groove_y(rail_height, play)
        bottom_y = get_bottom_edge_y(rail_height, play)
        
        pts = (
            [(BACKPLATE_TOP_Y, 0.0)]
            + get_groove_points(TOP_GROOVE_Y)
            + get_groove_points(bottom_groove_y)
            + [
                (bottom_y, 0.0),
                (bottom_y, -backplate_thickness),
                (BACKPLATE_TOP_Y, -backplate_thickness),
                (BACKPLATE_TOP_Y, 0.0),
            ]
        )
        
        baseplate = (
            cq.Workplane("YZ")
            .polyline(pts).close()
            .extrude(width / 2.0, both=True)
        )
        
        # Chamfer the 4 outer back edges (on the >Z face at Z=0)
        try:
            baseplate = baseplate.faces(">Z").edges(">X or <X or >Y or <Y").chamfer(2.0)
        except Exception:
            pass
        
        screw_pts = []
        for i in range(units):
            x = -width / 2.0 + unit_width / 2.0 + i * unit_width
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
            cq.Workplane("XY", origin=(0, top_y - height / 2.0, -6.4 - solid_thickness / 2.0))
            .box(width, height, solid_thickness)
        )
        
        top_block = load_mc_block('top-back.step')
        mid_block = load_mc_block('opening-raw-slot-back.step')
        bot_block = load_mc_block('embed-back-end.step')
        
        mc_solids = []
        for c in range(units):
            x_center = -width / 2.0 + 14.0 + c * 28.0
            
            y_top = 28.0 - 14.0
            inst = top_block.translate((x_center, y_top, 0))
            mc_solids.append(inst)
            
            for r in range(1, num_rows):
                y_mid = 28.0 - 14.0 - r * 28.0
                inst = mid_block.translate((x_center, y_mid, 0))
                mc_solids.append(inst)
                
            y_bot = 28.0 - num_rows * 28.0 - 7.0
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

# Backward compatibility alias
def export_stl(shape, filename, rotate_for_printing=None, category="", export_step=True, print_orientation="left_down"):
    export_val = "both" if export_step else "stl"
    return export_model(shape, filename, category=category, export=export_val, print_orientation=print_orientation, rotate_for_printing=rotate_for_printing)


def create_nut_slot(screw_m="M3", depth=10.0, push_hole=True, push_hole_angle=0.0, push_hole_dia=2.0):
    """
    Creates a nut capture slot (and optional push hole) centered at (0,0,0) using BRep modeling.
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
        
    slot_w = nut_waf + NUT_SLOT_TOLERANCE
    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    
    # Distance from center to point of hexagon
    nut_point_dist = (nut_waf / 2.0) / math.cos(math.radians(30))
    
    slot_length = depth + nut_point_dist
    center_y = (depth - nut_point_dist) / 2.0
    
    b = (
        cq.Workplane("XY")
        .workplane(offset=-slot_t / 2.0)
        .center(0, center_y)
        .rect(slot_w, slot_length)
        .extrude(slot_t)
    )
    
    if push_hole:
        push_wp = b.faces("<Y").workplane(centerOption="CenterOfMass")
        if push_hole_angle != 0.0:
            push_wp = push_wp.transformed(rotate=(push_hole_angle, 0, 0))
        b = push_wp.circle(push_hole_dia / 2.0).extrude(100.0)
        
    return b.val()

def support_fin(z_gap=0.01, is_right=True, length=30.0, height=30.0, fin_width=1.6, tip_width=0.4, taper_z_drop=4.0, cutoff_top=True):
    """
    Generates a 45-degree support fin using BRep modeling.
    Note: For the cleanest breakaway, use z_gap=0.0 mm if the fin tip is perfectly aligned 
    flush with an outer corner of the part. If placing the fin in the middle of a face, 
    default to z_gap=0.01 mm to ensure it lightly fuses with the perimeter.
    """
    y_sign = 1.0 if is_right else -1.0
    start_y = max(0, z_gap)
    end_y = length + min(0, z_gap)
    start_z = start_y - z_gap
    cutoff_z = height - taper_z_drop if cutoff_top else height
    cutoff_y = cutoff_z + z_gap

    raw_pts = [
        (y_sign * start_y, 0),
        (y_sign * start_y, start_z),
        (y_sign * cutoff_y, cutoff_z),
        (y_sign * end_y, cutoff_z),
        (y_sign * end_y, 0),
    ]
    pts = []
    for p in raw_pts:
        if not pts or (abs(p[0] - pts[-1][0]) > 1e-5 or abs(p[1] - pts[-1][1]) > 1e-5):
            pts.append(p)

    wedge = cq.Workplane("YZ", origin=(-fin_width / 2.0, 0, 0)).polyline(pts).close().extrude(fin_width)
    path = cq.Workplane("YZ").moveTo(0, -z_gap).lineTo(y_sign * (height + 10.0), height + 10.0 - z_gap)

    prof_x1 = tip_width / 2.0
    prof_x2 = fin_width / 2.0
    prof_p = [(1.0, fin_width), (1.0, prof_x1), (0.0, prof_x1), (-taper_z_drop, prof_x2), (-taper_z_drop, fin_width)]
    prof_n = [(1.0, -fin_width), (1.0, -prof_x1), (0.0, -prof_x1), (-taper_z_drop, -prof_x2), (-taper_z_drop, -fin_width)]

    cutter = cq.Workplane("ZX", origin=(0, 0, -z_gap)).polyline(prof_p).close().polyline(prof_n).close().sweep(path)
    return wedge.cut(cutter)

def create_snap_fit_peg_parameterized(bot_p0, num_petals=3, band_dia=8.1):
    delta = (band_dia / 2.0) - 4.05
    
    # This creates the snap fit peg AT the specified location.
    solid_cyl = cq.Solid.makeCylinder(3.25 + delta, 2.0, cq.Vector(0,0,0), cq.Vector(0,0,1))
    inner_solid = cq.Solid.makeCylinder(1.75 + delta, 6.25, cq.Vector(0,0,2), cq.Vector(0,0,1))
    
    tube_b_out = cq.Solid.makeCylinder(3.25 + delta, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b_in = cq.Solid.makeCylinder(2.45 + delta, 3.0, cq.Vector(0,0,2), cq.Vector(0,0,1))
    tube_b = cq.Workplane(tube_b_out).cut(cq.Workplane(tube_b_in)).val()
    
    band_bs_out = cq.Solid.makeCone(3.25 + delta, 4.05 + delta, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs_in = cq.Solid.makeCylinder(2.45 + delta, 0.8, cq.Vector(0,0,5), cq.Vector(0,0,1))
    band_bs = cq.Workplane(band_bs_out).cut(cq.Workplane(band_bs_in)).val()
    
    band_f_out = cq.Solid.makeCylinder(4.05 + delta, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f_in = cq.Solid.makeCylinder(2.45 + delta, 1.4, cq.Vector(0,0,5.8), cq.Vector(0,0,1))
    band_f = cq.Workplane(band_f_out).cut(cq.Workplane(band_f_in)).val()
    
    band_ts_out = cq.Solid.makeCone(4.05 + delta, 3.25 + delta, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts_in = cq.Solid.makeCylinder(2.45 + delta, 0.8, cq.Vector(0,0,7.2), cq.Vector(0,0,1))
    band_ts = cq.Workplane(band_ts_out).cut(cq.Workplane(band_ts_in)).val()
    
    tube_t_out = cq.Solid.makeCylinder(3.25 + delta, 0.25, cq.Vector(0,0,8.0), cq.Vector(0,0,1))
    tube_t_in = cq.Solid.makeCylinder(2.45 + delta, 0.25, cq.Vector(0,0,8.0), cq.Vector(0,0,1))
    tube_t = cq.Workplane(tube_t_out).cut(cq.Workplane(tube_t_in)).val()
    
    outer_tube = cq.Workplane(tube_b).union(cq.Workplane(band_bs)).union(cq.Workplane(band_f)).union(cq.Workplane(band_ts)).union(cq.Workplane(tube_t))
    
    # Slit thickness
    slit_w = 0.8
    # Create N independent slits. We use a cutter that only goes in +Y direction from center so it cuts exactly 1 slit at a time.
    for i in range(num_petals):
        angle = i * (360.0 / num_petals)
        cutter = cq.Workplane("XY").workplane(offset=2.0).center(0, 5.0).box(slit_w, 10.0, 8.0, centered=(True, True, False))
        cutter = cutter.rotate((0,0,0), (0,0,1), angle)
        outer_tube = outer_tube.cut(cutter)
    
    snap_peg = cq.Workplane(solid_cyl).union(cq.Workplane(inner_solid)).union(outer_tube)
    snap_peg = snap_peg.translate(bot_p0)
    
    return snap_peg

