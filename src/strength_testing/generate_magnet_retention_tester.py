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
  1. MultiConnect Slit Snap (Recommended):
     - Main pocket has radial clearance so magnet drops in freely.
     - 0.40 mm compliant wall (1 perimeter) with a 0.20 mm slit behind it.
     - 4 arcs separated by 1.20 mm solid bridges (3 perimeters).
     - 0.20 mm air gap under the free arcs at the pocket floor.
     - 45-degree inward-sloping retaining bump at the top edge of the compliant arcs.
     - Central push-out hole for magnet removal.
     - Matrix: Clearance sweep (0.20, 0.25, 0.30 mm) x Bump extra (0.00, 0.06, 0.12 mm).

  2. Slanted Deformable Ribs:
     - Ribs are solidly rooted into the outside pocket wall.
     - Bottom of each rib is suspended 0.10 mm above the pocket floor.
     - 45-degree lead-in chamfer on the inside top corner of each rib tip.
     - Matrix: 3, 4, and 6 ribs x Short, Medium, and Long rib lengths.

  3. Spiral Arc Flexures:
     - Curved flexure arms rooted in the outer wall with spiral clearance slots.
     - 0.10 mm floor relief undercut under the tips and arms.
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
        "cell_size": 22.0,
        "push_dia": 3.0,
        "mc_params": {
            "c_radials": [0.20, 0.25, 0.30],
            "b_extras":  [0.00, 0.06, 0.12],
            "t_wall": 0.40,
            "w_slit": 0.20,
            "bridge_w": 1.20,
            "gap_floor": 0.20,
        },
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
        "cell_size": 32.0,
        "push_dia": 5.0,
        "mc_params": {
            "c_radials": [0.20, 0.25, 0.30],
            "b_extras":  [0.00, 0.08, 0.15],
            "t_wall": 0.40,
            "w_slit": 0.20,
            "bridge_w": 1.20,
            "gap_floor": 0.20,
        },
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


def add_multiconnect_snap_pocket(
    body,
    center_pt=(0, 0),
    face_z=2.0,
    mag_dia=10.0,
    mag_thick=1.55,
    c_radial=0.25,
    b_extra=0.06,
    t_wall=0.40,
    w_slit=0.20,
    bridge_w=1.20,
    num_arcs=4,
    gap_floor=0.20,
    push_hole_dia=3.0,
    pocket_depth=None,
    through_depth=10.0
):
    """
    Cuts a MultiConnect-style compliant snap pocket into `body`:
      - Main pocket bore has radius r_pocket = r_mag + c_radial.
      - 0.40 mm compliant wall with a 0.20 mm slit behind it.
      - 4 arcs separated by 1.20 mm solid bridges.
      - 0.20 mm air gap under the free arcs at the floor.
      - 45-degree inward bump at the top edge of each compliant arc.
      - Central push-out hole.
    """
    if pocket_depth is None:
        pocket_depth = mag_thick + 0.25  # slight flush-to-recessed fit
        
    floor_z = face_z - pocket_depth
    r_mag = mag_dia / 2.0
    r_pocket = r_mag + c_radial
    r_slit_in = r_pocket + t_wall
    r_slit_out = r_slit_in + w_slit
    
    b_radial = c_radial + b_extra
    r_bump_top = r_pocket - b_radial
    bump_h = b_radial
    
    # 1. Central push-out hole
    body = body.cut(
        cq.Workplane("XY")
        .circle(push_hole_dia / 2.0)
        .extrude(through_depth)
        .translate((center_pt[0], center_pt[1], face_z - through_depth))
    )
    
    # 2. Main pocket bore (full clearance cylinder)
    body = body.cut(
        cq.Workplane("XY")
        .workplane(offset=floor_z)
        .circle(r_pocket)
        .extrude(pocket_depth + 0.05)
        .translate((center_pt[0], center_pt[1], 0))
    )
    
    # 3. Slit, Undercut, and Bump Profiles
    r_mid = (r_slit_in + r_slit_out) / 2.0
    d_theta_bridge = math.degrees(bridge_w / r_mid)
    arc_sweep = (360.0 / num_arcs) - d_theta_bridge
    
    slit_z_bot = floor_z - gap_floor
    slit_h = face_z - slit_z_bot
    r_shelf = max(push_hole_dia / 2.0 + 0.6, r_mag - 0.5)
    
    slit_prof = [
        (r_slit_in, slit_z_bot),
        (r_slit_out, slit_z_bot),
        (r_slit_out, face_z),
        (r_slit_in, face_z)
    ]
    undercut_prof = [
        (r_shelf, slit_z_bot),
        (r_slit_out, slit_z_bot),
        (r_slit_out, floor_z),
        (r_shelf, floor_z)
    ]
    bump_prof = [
        (r_pocket, face_z - bump_h),
        (r_bump_top, face_z),
        (r_pocket, face_z)
    ]
    
    for i in range(num_arcs):
        center_angle = i * (360.0 / num_arcs)
        start_angle = center_angle - arc_sweep / 2.0
        
        # 3a. Concentric 0.20 mm slit behind the 0.40 mm wall
        slit_arc = (
            cq.Workplane("XZ")
            .polyline(slit_prof).close()
            .revolve(arc_sweep, (0, 0, 0), (0, 1, 0))
            .rotate((0, 0, 0), (0, 0, 1), start_angle)
            .translate((center_pt[0], center_pt[1], 0))
        )
        body = body.cut(slit_arc)
        
        # 3b. 0.20 mm undercut beneath the compliant arc
        undercut_arc = (
            cq.Workplane("XZ")
            .polyline(undercut_prof).close()
            .revolve(arc_sweep, (0, 0, 0), (0, 1, 0))
            .rotate((0, 0, 0), (0, 0, 1), start_angle)
            .translate((center_pt[0], center_pt[1], 0))
        )
        body = body.cut(undercut_arc)
        
        # 3c. 45-degree bump at the top of this compliant arc
        if bump_h > 0.001:
            bump_arc = (
                cq.Workplane("XZ")
                .polyline(bump_prof).close()
                .revolve(arc_sweep, (0, 0, 0), (0, 1, 0))
                .rotate((0, 0, 0), (0, 0, 1), start_angle)
                .translate((center_pt[0], center_pt[1], 0))
            )
            body = body.union(bump_arc)
            
    return body


def create_multiconnect_coupon_plate(size_key="10mm", plate_thick=4.0):
    """
    Creates a 3x3 test coupon plate for MultiConnect-style compliant slit snaps.
      Rows: Clearance sweep (0.20, 0.25, 0.30 mm)
      Cols: Bump extra (0.00 = Flush/zero snap, 0.06/0.08 = Light, 0.12/0.15 = Firm)
    """
    spec = MAGNET_SPECS[size_key]
    mag_dia = spec["dia"]
    mag_thick = spec["thick"]
    cell = spec["cell_size"]
    push_dia = spec["push_dia"]
    mc_params = spec["mc_params"]
    
    cols = 3
    rows = 3
    margin_top = cell * 0.40
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
    
    c_radials = mc_params["c_radials"]
    b_extras = mc_params["b_extras"]
    
    for r_idx, c_val in enumerate(c_radials):
        for c_idx, b_ext in enumerate(b_extras):
            cx = x0 + c_idx * cell
            cy = y0 - r_idx * cell
            
            plate = add_multiconnect_snap_pocket(
                plate,
                center_pt=(cx, cy),
                face_z=face_z,
                mag_dia=mag_dia,
                mag_thick=mag_thick,
                c_radial=c_val,
                b_extra=b_ext,
                t_wall=mc_params["t_wall"],
                w_slit=mc_params["w_slit"],
                bridge_w=mc_params["bridge_w"],
                gap_floor=mc_params["gap_floor"],
                push_hole_dia=push_dia,
                through_depth=plate_thick + 2.0
            )
            
            lbl = f"C{int(c_val*100)}_B{int(b_ext*100)}"
            try:
                txt = (
                    cq.Workplane("XY", origin=(cx, cy + cell * 0.40, face_z))
                    .text(lbl, fontsize=cell * 0.09, distance=-0.4)
                )
                plate = plate.cut(txt)
            except Exception:
                pass
                
    try:
        hdr_txt = f"MULTICONNECT SNAP - {spec['name']}"
        txt = (
            cq.Workplane("XY", origin=(0, plate_h / 2.0 - margin_top / 2.0, face_z))
            .text(hdr_txt, fontsize=cell * 0.10, distance=-0.4)
        )
        plate = plate.cut(txt)
    except Exception:
        pass
        
    return plate


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
        pocket_depth = mag_thick + 0.20
        
    floor_z = face_z - pocket_depth
    r_mag = mag_dia / 2.0
    r_wall = r_mag + wall_offset
    r_tip = r_mag - interference
    
    body = body.cut(
        cq.Workplane("XY")
        .workplane(offset=floor_z)
        .circle(r_wall)
        .extrude(pocket_depth + 0.05)
        .translate((center_pt[0], center_pt[1], 0))
    )
    
    body = body.cut(
        cq.Workplane("XY")
        .circle(push_hole_dia / 2.0)
        .extrude(through_depth)
        .translate((center_pt[0], center_pt[1], face_z - through_depth))
    )
    
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
    
    s_root = -1.20
    L = s_tip - s_root
    
    rib_h = pocket_depth - gap_floor
    chamfer_size = min(0.60, rib_h * 0.45)
    
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


def create_ribs_coupon_plate(size_key="10mm", plate_thick=4.0):
    """
    Creates a 3x3 test coupon plate for Slanted Deformable Ribs.
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
    Cuts a spiral arc flexure pocket.
    """
    if pocket_depth is None:
        pocket_depth = mag_thick + 0.20
        
    floor_z = face_z - pocket_depth
    r_mag = mag_dia / 2.0
    r_tip = r_mag - interference
    r_outer = r_mag + r_outer_offset
    r_shelf = max(push_hole_dia / 2.0 + 0.8, r_tip - 0.5)
    
    body = body.cut(
        cq.Workplane("XY")
        .circle(push_hole_dia / 2.0)
        .extrude(through_depth)
        .translate((center_pt[0], center_pt[1], face_z - through_depth))
    )
    
    body = body.cut(
        cq.Workplane("XY")
        .workplane(offset=floor_z)
        .circle(r_tip)
        .extrude(pocket_depth + 0.05)
        .translate((center_pt[0], center_pt[1], 0))
    )
    
    undercut = (
        cq.Workplane("XY")
        .workplane(offset=floor_z - gap_floor)
        .circle(r_outer + 0.5)
        .circle(r_shelf)
        .extrude(gap_floor + 0.001)
        .translate((center_pt[0], center_pt[1], 0))
    )
    body = body.cut(undercut)
    
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
        
    chamfer_h = min(0.60, pocket_depth * 0.35)
    cone = cq.Solid.makeCone(
        r_tip, r_tip + chamfer_h, chamfer_h + 0.05,
        cq.Vector(center_pt[0], center_pt[1], face_z - chamfer_h),
        cq.Vector(0, 0, 1)
    )
    body = body.cut(cq.Workplane(cone))
    
    return body


def create_spiral_coupon_plate(size_key="10mm", plate_thick=4.0):
    """
    Creates a 2x3 test coupon plate for Spiral Arc Flexures.
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
    parser.add_argument("--type", choices=["multiconnect", "ribs", "spiral", "all"], default="multiconnect", help="Mechanism type to generate")
    args = parser.parse_args()
    
    sizes = ["10mm", "19.25mm"] if args.size == "both" else [args.size]
    types = ["multiconnect"] if args.type == "multiconnect" else (["multiconnect", "ribs", "spiral"] if args.type == "all" else [args.type])
    
    for s in sizes:
        for t in types:
            if t == "multiconnect":
                plate = create_multiconnect_coupon_plate(size_key=s)
                filename = f"magnet_multiconnect_coupon_{s}.stl"
            elif t == "ribs":
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
