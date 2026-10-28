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

MultiConnect Slit Snap V2 Matrix:
  - 0.25 mm radial clearance (baseline).
  - Strong snap bump (drops down at 45 deg, only on compliant arcs).
  - Flat solid pocket floor with NO undercut bridging (eliminating droop/blobs).
  - 0.20 mm air gap under the compliant arcs (above floor_z).
  - Central push-out hole.
  
  Comparisons Tested (3x3 grid):
    * Columns (Wall & Slit Configuration):
        - 1PN: 1 perimeter arc (0.40 mm), narrow slit (0.20 mm)
        - 1PF: 1 perimeter arc (0.40 mm), full perimeter slit (0.40 mm)
        - 2PF: 2 perimeter arc (0.80 mm), full perimeter slit (0.40 mm)
    * Rows (Pocket Depth):
        - D0: Depth equal to magnet thickness (1.55 mm / 1.60 mm)
        - D2: Depth +0.20 mm deeper (1.75 mm / 1.80 mm)
        - D4: Depth +0.40 mm deeper (1.95 mm / 2.00 mm - magnet settles fully under bump)

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
        "c_radial": 0.25,
        "b_extra": 0.12,  # Strong snap (total bump = 0.37mm)
        "depth_offsets": [0.0, 0.20, 0.40],
        "arc_configs": [
            (0.40, 0.20, "1PN"),
            (0.40, 0.40, "1PF"),
            (0.80, 0.40, "2PF"),
        ],
        "bridge_w": 1.20,
        "gap_floor": 0.20,
    },
    "19.25mm": {
        "dia": 19.25,
        "thick": 1.60,
        "name": "19.25x1.60mm",
        "cell_size": 32.0,
        "push_dia": 5.0,
        "c_radial": 0.25,
        "b_extra": 0.15,  # Strong snap (total bump = 0.40mm)
        "depth_offsets": [0.0, 0.20, 0.40],
        "arc_configs": [
            (0.40, 0.20, "1PN"),
            (0.40, 0.40, "1PF"),
            (0.80, 0.40, "2PF"),
        ],
        "bridge_w": 1.20,
        "gap_floor": 0.20,
    }
}


def add_multiconnect_snap_pocket(
    body,
    center_pt=(0, 0),
    face_z=2.0,
    mag_dia=10.0,
    mag_thick=1.55,
    c_radial=0.25,
    b_extra=0.12,
    t_wall=0.80,
    w_slit=0.40,
    bridge_w=1.20,
    num_arcs=4,
    gap_floor=0.20,
    push_hole_dia=3.0,
    pocket_depth=None,
    through_depth=10.0
):
    """
    Cuts a MultiConnect-style compliant snap pocket into `body`:
      - Main pocket bore has radius r_pocket = r_mag + c_radial with a flat floor at floor_z.
      - Compliant wall has thickness t_wall with parallel slit of width w_slit.
      - 4 arcs separated by bridge_w (1.20 mm) solid bridges.
      - gap_floor (0.20 mm) air gap under the free arcs above floor_z (NO undercut below floor).
      - 45-degree inward bump at the top edge of each compliant arc (drops down at 45 deg).
      - Central push-out hole.
    """
    if pocket_depth is None:
        pocket_depth = mag_thick + 0.20
        
    floor_z = face_z - pocket_depth
    r_mag = mag_dia / 2.0
    r_pocket = r_mag + c_radial
    r_slit_in = r_pocket + t_wall
    r_slit_out = r_slit_in + w_slit
    
    b_radial = c_radial + b_extra
    r_bump_top = r_pocket - b_radial
    bump_h = b_radial
    
    # 1. Central push-out hole through the bottom
    body = body.cut(
        cq.Workplane("XY")
        .circle(push_hole_dia / 2.0)
        .extrude(through_depth)
        .translate((center_pt[0], center_pt[1], face_z - through_depth))
    )
    
    # 2. Main pocket bore (flat floor at floor_z, radius r_pocket)
    body = body.cut(
        cq.Workplane("XY")
        .workplane(offset=floor_z)
        .circle(r_pocket)
        .extrude(pocket_depth + 0.05)
        .translate((center_pt[0], center_pt[1], 0))
    )
    
    # 3. Arcs geometry (Slits, Under-arc gap, and Top bump)
    r_mid = (r_slit_in + r_slit_out) / 2.0
    d_theta_bridge = math.degrees(bridge_w / r_mid)
    arc_sweep = (360.0 / num_arcs) - d_theta_bridge
    
    # Slit runs from floor_z up to face_z
    slit_prof = [
        (r_slit_in, floor_z),
        (r_slit_out, floor_z),
        (r_slit_out, face_z),
        (r_slit_in, face_z)
    ]
    
    # Gap runs from r_pocket to r_slit_out, between floor_z and floor_z + gap_floor
    gap_prof = [
        (r_pocket, floor_z),
        (r_slit_out, floor_z),
        (r_slit_out, floor_z + gap_floor),
        (r_pocket, floor_z + gap_floor)
    ]
    
    # 45-degree bump at the top edge of the arc
    bump_prof = [
        (r_pocket, face_z - bump_h),
        (r_bump_top, face_z),
        (r_pocket, face_z)
    ]
    
    for i in range(num_arcs):
        center_angle = i * (360.0 / num_arcs)
        start_angle = center_angle - arc_sweep / 2.0
        
        # 3a. Concentric slit behind wall
        slit_arc = (
            cq.Workplane("XZ")
            .polyline(slit_prof).close()
            .revolve(arc_sweep, (0, 0, 0), (0, 1, 0))
            .rotate((0, 0, 0), (0, 0, 1), start_angle)
            .translate((center_pt[0], center_pt[1], 0))
        )
        body = body.cut(slit_arc)
        
        # 3b. 0.20 mm air gap under the compliant arc
        gap_arc = (
            cq.Workplane("XZ")
            .polyline(gap_prof).close()
            .revolve(arc_sweep, (0, 0, 0), (0, 1, 0))
            .rotate((0, 0, 0), (0, 0, 1), start_angle)
            .translate((center_pt[0], center_pt[1], 0))
        )
        body = body.cut(gap_arc)
        
        # 3c. 45-degree bump on the top of this compliant arc
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
    Creates a 3x3 test coupon plate for MultiConnect-style compliant slit snaps:
      - Clearance: 0.25 mm (fixed baseline)
      - Bump: Strong snap (+0.12 mm for 10mm / +0.15 mm for 19.25mm)
      - Rows: Pocket Depths (D0: magnet thick, D2: +0.2mm, D4: +0.4mm)
      - Cols: Wall & Slit (1PN: 0.4mm wall / 0.2mm slit, 1PF: 0.4mm wall / 0.4mm slit, 2PF: 0.8mm wall / 0.4mm slit)
    """
    spec = MAGNET_SPECS[size_key]
    mag_dia = spec["dia"]
    mag_thick = spec["thick"]
    cell = spec["cell_size"]
    push_dia = spec["push_dia"]
    c_radial = spec["c_radial"]
    b_extra = spec["b_extra"]
    depth_offsets = spec["depth_offsets"]
    arc_configs = spec["arc_configs"]
    bridge_w = spec["bridge_w"]
    gap_floor = spec["gap_floor"]
    
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
    
    depth_labels = ["D0", "D2", "D4"]
    
    for r_idx, d_off in enumerate(depth_offsets):
        d_val = mag_thick + d_off
        for c_idx, (t_w, w_s, c_lbl) in enumerate(arc_configs):
            cx = x0 + c_idx * cell
            cy = y0 - r_idx * cell
            
            plate = add_multiconnect_snap_pocket(
                plate,
                center_pt=(cx, cy),
                face_z=face_z,
                mag_dia=mag_dia,
                mag_thick=mag_thick,
                c_radial=c_radial,
                b_extra=b_extra,
                t_wall=t_w,
                w_slit=w_s,
                bridge_w=bridge_w,
                gap_floor=gap_floor,
                push_hole_dia=push_dia,
                pocket_depth=d_val,
                through_depth=plate_thick + 2.0
            )
            
            lbl = f"{c_lbl}_{depth_labels[r_idx]}"
            try:
                txt = (
                    cq.Workplane("XY", origin=(cx, cy + cell * 0.40, face_z))
                    .text(lbl, fontsize=cell * 0.09, distance=-0.4)
                )
                plate = plate.cut(txt)
            except Exception:
                pass
                
    try:
        hdr_txt = f"SNAP V2 - {spec['name']}"
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
    args = parser.parse_args()
    
    sizes = ["10mm", "19.25mm"] if args.size == "both" else [args.size]
    
    for s in sizes:
        plate = create_multiconnect_coupon_plate(size_key=s)
        filename = f"magnet_multiconnect_coupon_{s}.stl"
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
