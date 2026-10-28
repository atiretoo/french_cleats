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
"""
generate_magnet_retention_tester.py

Generates physical test coupon plates to evaluate compliant magnet retention
mechanisms for 3D printed tool holders and mounts.

Mechanisms Supported:
  1. Slanted Deformable Ribs:
     - Ribs are solidly rooted into the outside pocket wall.
     - Bottom of each rib is suspended 0.10 mm above the pocket floor (enabling
       unconstrained horizontal deflection in the XY plane).
     - No top edge chamfer on the outer pocket perimeter.
     - 45-degree lead-in chamfer on the inside top corner of each rib tip.
     - Central push-out hole for magnet removal.
     - Matrix: 3, 4, and 6 ribs x Short, Medium, and Long rib lengths.

  2. Spiral Arc Flexures:
     - Curved flexure arms rooted in the outer wall with spiral clearance slots.
     - Tips have an inner diameter slightly smaller than the magnet (active interference).
     - Floor relief undercut (0.10 mm air gap / missing layer) under the tips and arms,
       leaving a solid central shelf that supports the magnet from falling through.
     - 45-degree lead-in chamfer on the inside top corner of each flexure tip.
     - Matrix: 3-arm and 4-arm flexures x Light, Medium, and Deep interference.

Supported Test Magnet Sizes:
  - Small: 10.0 mm diameter x 1.55 mm thickness
  - Large: 19.25 mm diameter x 1.60 mm thickness
"""

import cadquery as cq
import math
import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import export_model

# Standard Test Magnet Dimensions & Parameters
MAGNET_SPECS = {
    "10mm": {
        "dia": 10.0,
        "thick": 1.55,
        "name": "10x1.55mm",
        "cell_size": 20.0,
        "push_dia": 3.0,
        "rib_params": {
            "short":  {"wall_offset": 0.50, "interference": 0.18},
            "medium": {"wall_offset": 0.85, "interference": 0.25},
            "long":   {"wall_offset": 1.30, "interference": 0.35},
        },
        "spiral_cell_size": 24.0,
        "spiral_params": {
            "r_outer_offset": 3.5,
            "slot_w": 0.85,
            "sweep_deg": 80.0,
            "interferences": {
                "lgt": 0.15,
                "med": 0.25,
                "dp":  0.35,
            }
        }
    },
    "19.25mm": {
        "dia": 19.25,
        "thick": 1.60,
        "name": "19.25x1.60mm",
        "cell_size": 30.0,
        "push_dia": 5.0,
        "rib_params": {
            "short":  {"wall_offset": 0.60, "interference": 0.20},
            "medium": {"wall_offset": 1.00, "interference": 0.30},
            "long":   {"wall_offset": 1.50, "interference": 0.40},
        },
        "spiral_cell_size": 34.0,
        "spiral_params": {
            "r_outer_offset": 4.5,
            "slot_w": 1.0,
            "sweep_deg": 80.0,
            "interferences": {
                "lgt": 0.18,
                "med": 0.30,
                "dp":  0.42,
            }
        }
    }
}


def add_slanted_rib_pocket(
    body,
    center_pt=(0, 0),
    face_z=0.0,
    mag_dia=10.0,
    mag_thick=1.55,
    num_ribs=4,
    wall_offset=0.85,
    interference=0.25,
    slant_angle_deg=40.0,
    rib_thick=0.72,
    push_hole_dia=3.0,
    pocket_depth=None,
    gap_floor=0.10,
    through_depth=10.0
):
    """
    Cuts a cylindrical pocket and unions slanted deformable ribs that are:
      1. Anchored firmly into the outside cylinder wall.
      2. Suspended `gap_floor` (0.1 mm) above the bottom pocket floor.
      3. Chamfered at 45 deg on the inside top corner for smooth magnet entry.
      4. Centered with a push-out hole.
    """
    if pocket_depth is None:
        pocket_depth = mag_thick + 0.20  # slight flush-to-recessed fit
        
    floor_z = face_z - pocket_depth
    r_mag = mag_dia / 2.0
    r_wall = r_mag + wall_offset
    r_tip = r_mag - interference
    
    # 1. Cut cylindrical pocket (sharp outer top rim, no chamfer)
    body = body.cut(
        cq.Workplane("XY")
        .workplane(offset=floor_z)
        .circle(r_wall)
        .extrude(pocket_depth + 0.05)
        .translate((center_pt[0], center_pt[1], 0))
    )
    
    # 2. Cut central push-out hole through the bottom floor
    body = body.cut(
        cq.Workplane("XY")
        .circle(push_hole_dia / 2.0)
        .extrude(through_depth)
        .translate((center_pt[0], center_pt[1], face_z - through_depth))
    )
    
    # 3. Geometric ray-intersection for slanted rib
    beta = math.radians(slant_angle_deg)
    b_c = -2 * r_wall * math.cos(beta)
    c_c = r_wall**2 - r_tip**2
    disc = b_c**2 - 4 * c_c
    if disc < 0:
        s_tip = r_wall - r_tip
    else:
        s_tip = (-b_c - math.sqrt(disc)) / 2.0
        
    tip_x = r_wall - s_tip * math.cos(beta)
    tip_y = s_tip * math.sin(beta)
    
    # Embed rib root 1.2 mm into the outer solid wall
    s_root = -1.20
    L = s_tip - s_root
    
    rib_h = pocket_depth - gap_floor
    chamfer_size = min(0.60, rib_h * 0.45)
    
    # Local profile in X-Z plane:
    # X=0 is inside tip, X=L is root in wall.
    # Z=0 is bottom of rib (gap_floor above pocket floor), Z=rib_h is top of rib (face_z).
    prof_pts = [
        (0, 0),
        (L, 0),
        (L, rib_h),
        (chamfer_size, rib_h),
        (0, rib_h - chamfer_size)
    ]
    
    local_rib = (
        cq.Workplane("XZ")
        .polyline(prof_pts).close()
        .extrude(rib_thick / 2.0, both=True)
    )
    
    # Union the ribs symmetrically around the center
    for i in range(num_ribs):
        rot_angle = i * (360.0 / num_ribs)
        r_sol = (
            local_rib
            .rotate((0, 0, 0), (0, 0, 1), -slant_angle_deg)
            .translate((tip_x, tip_y, floor_z + gap_floor))
            .rotate((0, 0, 0), (0, 0, 1), rot_angle)
            .translate((center_pt[0], center_pt[1], 0))
        )
        body = body.union(r_sol)
        
    return body


def add_spiral_flexure_pocket(
    body,
    center_pt=(0, 0),
    face_z=0.0,
    mag_dia=10.0,
    mag_thick=1.55,
    num_arms=3,
    r_outer_offset=3.5,
    interference=0.25,
    slot_w=0.85,
    sweep_deg=80.0,
    push_hole_dia=3.0,
    pocket_depth=None,
    gap_floor=0.10,
    through_depth=10.0
):
    """
    Cuts a spiral arc flexure pocket where:
      1. Flexure tips have diameter smaller than the magnet (active interference).
      2. Floor relief undercut (0.10 mm air gap) is cut beneath the flexure arms and tips,
         leaving a solid central shelf that supports the bottom of the magnet.
      3. Inside top edge of flexure tips has a 45-degree lead-in chamfer.
      4. Central push-out hole is provided.
    """
    if pocket_depth is None:
        pocket_depth = mag_thick + 0.20
        
    floor_z = face_z - pocket_depth
    r_mag = mag_dia / 2.0
    r_tip = r_mag - interference
    r_outer = r_mag + r_outer_offset
    r_shelf = max(push_hole_dia / 2.0 + 0.8, r_tip - 0.5)
    
    # 1. Push-out hole in center
    body = body.cut(
        cq.Workplane("XY")
        .circle(push_hole_dia / 2.0)
        .extrude(through_depth)
        .translate((center_pt[0], center_pt[1], face_z - through_depth))
    )
    
    # 2. Main pocket bore to r_tip
    body = body.cut(
        cq.Workplane("XY")
        .workplane(offset=floor_z)
        .circle(r_tip)
        .extrude(pocket_depth + 0.05)
        .translate((center_pt[0], center_pt[1], 0))
    )
    
    # 3. Floor relief undercut (0.10 mm missing layer under flexure tips and arms)
    undercut = (
        cq.Workplane("XY")
        .workplane(offset=floor_z - gap_floor)
        .circle(r_outer + 0.5)
        .circle(r_shelf)
        .extrude(gap_floor + 0.001)
        .translate((center_pt[0], center_pt[1], 0))
    )
    body = body.cut(undercut)
    
    # 4. Spiral clearance slots
    n_steps = 25
    inner_pts = []
    outer_pts = []
    for j in range(n_steps + 1):
        t = j / float(n_steps)
        theta = math.radians(t * sweep_deg)
        r = r_tip + (r_outer - r_tip) * t
        cx = r * math.cos(theta)
        cy = r * math.sin(theta)
        
        dr = (r_outer - r_tip) / math.radians(sweep_deg)
        tx = dr * math.cos(theta) - r * math.sin(theta)
        ty = dr * math.sin(theta) + r * math.cos(theta)
        t_len = math.hypot(tx, ty)
        nx = -ty / t_len
        ny = tx / t_len
        
        inner_pts.append((cx - nx * slot_w / 2.0, cy - ny * slot_w / 2.0))
        outer_pts.append((cx + nx * slot_w / 2.0, cy + ny * slot_w / 2.0))
        
    slot_poly = inner_pts + outer_pts[::-1]
    slot_depth = pocket_depth + gap_floor
    
    for i in range(num_arms):
        angle = i * (360.0 / num_arms)
        sw = (
            cq.Workplane("XY")
            .workplane(offset=floor_z - gap_floor)
            .polyline(slot_poly)
            .close()
            .extrude(slot_depth + 0.05)
            .rotate((0, 0, 0), (0, 0, 1), angle)
            .translate((center_pt[0], center_pt[1], 0))
        )
        body = body.cut(sw)
        
    # 5. Lead-in chamfer at inside top edge of flexure tips (45 deg)
    chamfer_h = min(0.60, pocket_depth * 0.35)
    cone = cq.Solid.makeCone(
        r_tip, r_tip + chamfer_h, chamfer_h + 0.05,
        cq.Vector(center_pt[0], center_pt[1], face_z - chamfer_h),
        cq.Vector(0, 0, 1)
    )
    body = body.cut(cq.Workplane(cone))
    
    return body


def create_ribs_coupon_plate(size_key="10mm", plate_thick=4.0):
    """
    Creates a 3x3 test coupon plate for Slanted Deformable Ribs.
      Rows: 3 ribs, 4 ribs, 6 ribs
      Cols: Short (S), Medium (M), Long (L)
    """
    spec = MAGNET_SPECS[size_key]
    mag_dia = spec["dia"]
    mag_thick = spec["thick"]
    cell = spec["cell_size"]
    push_dia = spec["push_dia"]
    rib_params = spec["rib_params"]
    
    cols = 3
    rows = 3
    margin_top = cell * 0.4
    plate_w = cols * cell
    plate_h = rows * cell + margin_top
    
    plate = cq.Workplane("XY").box(plate_w, plate_h, plate_thick)
    face_z = plate_thick / 2.0
    
    try:
        plate = plate.edges("<Z").chamfer(0.8)
    except Exception:
        pass
        
    x0 = -plate_w / 2.0 + cell / 2.0
    y0 = plate_h / 2.0 - margin_top - cell / 2.0
    
    rib_counts = [3, 4, 6]
    len_keys = ["short", "medium", "long"]
    
    for r_idx, n_ribs in enumerate(rib_counts):
        for c_idx, l_key in enumerate(len_keys):
            cx = x0 + c_idx * cell
            cy = y0 - r_idx * cell
            p = rib_params[l_key]
            
            plate = add_slanted_rib_pocket(
                plate,
                center_pt=(cx, cy),
                face_z=face_z,
                mag_dia=mag_dia,
                mag_thick=mag_thick,
                num_ribs=n_ribs,
                wall_offset=p["wall_offset"],
                interference=p["interference"],
                push_hole_dia=push_dia,
                through_depth=plate_thick + 2.0
            )
            
            lbl = f"{n_ribs}{l_key[0].upper()}"
            try:
                txt = (
                    cq.Workplane("XY", origin=(cx, cy + cell * 0.38, face_z))
                    .text(lbl, fontsize=cell * 0.12, distance=-0.4)
                )
                plate = plate.cut(txt)
            except Exception:
                pass
                
    try:
        hdr_txt = f"SLANTED RIBS - {spec['name']}"
        txt = (
            cq.Workplane("XY", origin=(0, plate_h / 2.0 - margin_top / 2.0, face_z))
            .text(hdr_txt, fontsize=cell * 0.12, distance=-0.4)
        )
        plate = plate.cut(txt)
    except Exception:
        pass
        
    return plate


def create_spiral_coupon_plate(size_key="10mm", plate_thick=4.0):
    """
    Creates a 2x3 test coupon plate for Spiral Arc Flexures.
      Rows: 3-arm, 4-arm
      Cols: Light (Lgt), Medium (Med), Deep (Dp) interference
    """
    spec = MAGNET_SPECS[size_key]
    mag_dia = spec["dia"]
    mag_thick = spec["thick"]
    cell = spec["spiral_cell_size"]
    push_dia = spec["push_dia"]
    sparams = spec["spiral_params"]
    interfs = sparams["interferences"]
    
    cols = 3
    rows = 2
    margin_top = cell * 0.35
    plate_w = cols * cell
    plate_h = rows * cell + margin_top
    
    plate = cq.Workplane("XY").box(plate_w, plate_h, plate_thick)
    face_z = plate_thick / 2.0
    
    try:
        plate = plate.edges("<Z").chamfer(0.8)
    except Exception:
        pass
        
    x0 = -plate_w / 2.0 + cell / 2.0
    y0 = plate_h / 2.0 - margin_top - cell / 2.0
    
    arm_counts = [3, 4]
    int_keys = ["lgt", "med", "dp"]
    
    for r_idx, n_arms in enumerate(arm_counts):
        for c_idx, ikey in enumerate(int_keys):
            cx = x0 + c_idx * cell
            cy = y0 - r_idx * cell
            interf = interfs[ikey]
            
            plate = add_spiral_flexure_pocket(
                plate,
                center_pt=(cx, cy),
                face_z=face_z,
                mag_dia=mag_dia,
                mag_thick=mag_thick,
                num_arms=n_arms,
                r_outer_offset=sparams["r_outer_offset"],
                interference=interf,
                slot_w=sparams["slot_w"],
                sweep_deg=sparams["sweep_deg"],
                push_hole_dia=push_dia,
                through_depth=plate_thick + 2.0
            )
            
            lbl = f"SP{n_arms}_{ikey.upper()}"
            try:
                txt = (
                    cq.Workplane("XY", origin=(cx, cy + cell * 0.40, face_z))
                    .text(lbl, fontsize=cell * 0.10, distance=-0.4)
                )
                plate = plate.cut(txt)
            except Exception:
                pass
                
    try:
        hdr_txt = f"SPIRAL FLEX - {spec['name']}"
        txt = (
            cq.Workplane("XY", origin=(0, plate_h / 2.0 - margin_top / 2.0, face_z))
            .text(hdr_txt, fontsize=cell * 0.10, distance=-0.4)
        )
        plate = plate.cut(txt)
    except Exception:
        pass
        
    return plate


def main():
    parser = argparse.ArgumentParser(description="Generate compliant magnet retention test coupons.")
    parser.add_argument("--size", choices=["10mm", "19.25mm", "both"], default="both", help="Magnet size to generate")
    parser.add_argument("--type", choices=["ribs", "spiral", "all"], default="all", help="Mechanism type to generate")
    args = parser.parse_args()
    
    sizes = ["10mm", "19.25mm"] if args.size == "both" else [args.size]
    types = ["ribs", "spiral"] if args.type == "all" else [args.type]
    
    for s in sizes:
        for t in types:
            if t == "ribs":
                plate = create_ribs_coupon_plate(size_key=s)
                filename = f"magnet_retention_coupon_{s}.stl"
            else:
                plate = create_spiral_coupon_plate(size_key=s)
                filename = f"magnet_spiral_coupon_{s}.stl"
                
            export_model(
                plate,
                filename,
                category="strength_testing",
                export="both",
                print_orientation="face_down",
                bed_chamfer=0.0
            )
            print(f"Exported {filename} and STEP to exports/strength_testing")


if __name__ == "__main__":
    main()
