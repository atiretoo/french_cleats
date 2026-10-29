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

MultiConnect Slit Snap V4 Matrix:
  - Baseline winner from V3: 2-perimeter wall (0.80 mm), wide slit (0.50 mm),
    pocket depth equal to magnet thickness (magnet flush/slightly proud).
  - 0.20 mm air gap under free arcs above flat solid pocket floor.
  - Central push-out hole for magnet removal.
  - Dedicated margins for column & row headers, keeping the area around
    compliant arcs completely flat and clean (zero text-induced stringing/blobs).

  Comparisons Tested (3x4 grid):
    * Columns (Arc Count):
        - 2 ARCS (2A): 2 long flexible arcs (higher compliance, lower insertion force)
        - 3 ARCS (3A): 3 medium arcs (balanced compliance & tri-point centration)
        - 4 ARCS (4A): 4 arcs (V3 baseline configuration)
    * Rows (Clearance & Bump Variations):
        - C20 B18 / C20 B22: Baseline winner (0.20 mm clearance, +0.18 mm / +0.22 mm bump)
        - C15 B18 / C15 B22: Tighter clearance (0.15 mm clearance, +0.18 mm / +0.22 mm bump)
        - C20 B23 / C20 B27: Larger bump (0.20 mm clearance, +0.23 mm / +0.27 mm bump, +0.05 mm)
        - C15 B23 / C15 B27: Tighter clearance + Larger bump (0.15 mm clearance, +0.23 mm / +0.27 mm bump)

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
from core_library import export_model, add_compliant_magnet_pocket

# Standard Test Magnet Dimensions & Parameters
MAGNET_SPECS = {
    "10mm": {
        "dia": 10.0,
        "thick": 1.55,
        "name": "10x1.55mm",
        "cell_size": 24.0,
        "push_dia": 3.0,
        "row_params": [
            {"c_radial": 0.20, "b_extra": 0.18, "label": "C20 B18"},
            {"c_radial": 0.15, "b_extra": 0.18, "label": "C15 B18"},
            {"c_radial": 0.20, "b_extra": 0.23, "label": "C20 B23"},
            {"c_radial": 0.15, "b_extra": 0.23, "label": "C15 B23"},
        ],
        "col_params": [
            {"num_arcs": 2, "label": "2 ARCS"},
            {"num_arcs": 3, "label": "3 ARCS"},
            {"num_arcs": 4, "label": "4 ARCS"},
        ],
        "t_wall": 0.80,
        "w_slit": 0.50,
        "bridge_w": 1.20,
        "gap_floor": 0.20,
        "margin_left": 20.0,
        "margin_right": 8.0,
        "margin_top": 20.0,
        "margin_bottom": 8.0,
    },
    "19.25mm": {
        "dia": 19.25,
        "thick": 1.60,
        "name": "19.25x1.60mm",
        "cell_size": 34.0,
        "push_dia": 5.0,
        "row_params": [
            {"c_radial": 0.20, "b_extra": 0.22, "label": "C20 B22"},
            {"c_radial": 0.15, "b_extra": 0.22, "label": "C15 B22"},
            {"c_radial": 0.20, "b_extra": 0.27, "label": "C20 B27"},
            {"c_radial": 0.15, "b_extra": 0.27, "label": "C15 B27"},
        ],
        "col_params": [
            {"num_arcs": 2, "label": "2 ARCS"},
            {"num_arcs": 3, "label": "3 ARCS"},
            {"num_arcs": 4, "label": "4 ARCS"},
        ],
        "t_wall": 0.80,
        "w_slit": 0.50,
        "bridge_w": 1.20,
        "gap_floor": 0.20,
        "margin_left": 24.0,
        "margin_right": 10.0,
        "margin_top": 24.0,
        "margin_bottom": 10.0,
    }
}


def add_multiconnect_snap_pocket(
    body,
    center_pt=(0, 0),
    face_z=2.0,
    mag_dia=10.0,
    mag_thick=1.55,
    c_radial=0.20,
    b_extra=0.18,
    t_wall=0.80,
    w_slit=0.50,
    bridge_w=1.20,
    num_arcs=3,
    gap_floor=0.20,
    push_hole_dia=3.0,
    pocket_depth=None,
    through_depth=10.0
):
    """
    Wrapper around core_library.add_compliant_magnet_pocket for coupon testing.
    """
    return add_compliant_magnet_pocket(
        body=body,
        center_pt=center_pt,
        face_z=face_z,
        mag_dia=mag_dia,
        mag_thick=mag_thick,
        c_radial=c_radial,
        b_extra=b_extra,
        t_wall=t_wall,
        w_slit=w_slit,
        bridge_w=bridge_w,
        num_arcs=num_arcs,
        gap_floor=gap_floor,
        push_hole_dia=push_hole_dia,
        pocket_depth=pocket_depth,
        through_depth=through_depth,
        normal_dir="+Z"
    )


def create_multiconnect_coupon_plate(size_key="10mm", plate_thick=4.0):
    """
    Creates a 3x4 test coupon plate for MultiConnect-style compliant slit snaps:
      - Fixed: 2-perimeter wall (0.80 mm), wide slit (0.50 mm), flush depth.
      - Columns: Number of Arcs (2, 3, 4 arcs).
      - Rows: Clearance & Bump Variations (C20 vs C15, Baseline bump vs +0.05 mm bump).
      - Clean matrix header layout with labels isolated in dedicated margins.
    """
    spec = MAGNET_SPECS[size_key]
    mag_dia = spec["dia"]
    mag_thick = spec["thick"]
    cell = spec["cell_size"]
    push_dia = spec["push_dia"]
    row_params = spec["row_params"]
    col_params = spec["col_params"]
    t_wall = spec["t_wall"]
    w_slit = spec["w_slit"]
    bridge_w = spec["bridge_w"]
    gap_floor = spec["gap_floor"]
    
    margin_left = spec["margin_left"]
    margin_right = spec["margin_right"]
    margin_top = spec["margin_top"]
    margin_bottom = spec["margin_bottom"]
    
    cols = len(col_params)
    rows = len(row_params)
    plate_w = margin_left + cols * cell + margin_right
    plate_h = margin_bottom + rows * cell + margin_top
    
    plate = cq.Workplane("XY").box(plate_w, plate_h, plate_thick)
    face_z = plate_thick / 2.0
    
    try:
        plate = plate.edges("<Z").chamfer(0.8)
    except Exception:
        pass
        
    grid_left_x = -plate_w / 2.0 + margin_left
    grid_top_y = plate_h / 2.0 - margin_top
    
    for r_idx, r_item in enumerate(row_params):
        c_val = r_item["c_radial"]
        b_ext = r_item["b_extra"]
        cy = grid_top_y - r_idx * cell - cell / 2.0
        
        for c_idx, c_item in enumerate(col_params):
            n_arcs = c_item["num_arcs"]
            cx = grid_left_x + c_idx * cell + cell / 2.0
            
            plate = add_multiconnect_snap_pocket(
                plate,
                center_pt=(cx, cy),
                face_z=face_z,
                mag_dia=mag_dia,
                mag_thick=mag_thick,
                c_radial=c_val,
                b_extra=b_ext,
                t_wall=t_wall,
                w_slit=w_slit,
                bridge_w=bridge_w,
                num_arcs=n_arcs,
                gap_floor=gap_floor,
                push_hole_dia=push_dia,
                pocket_depth=mag_thick,
                through_depth=plate_thick + 2.0
            )
            
    # 1. Title Header centered above column grid
    try:
        grid_center_x = grid_left_x + (cols * cell) / 2.0
        title_y = plate_h / 2.0 - margin_top * 0.28
        hdr_txt = f"SNAP V4 - {spec['name']} (DEPTH {mag_thick:.2f}mm)"
        txt_title = (
            cq.Workplane("XY", origin=(grid_center_x, title_y, face_z))
            .text(hdr_txt, fontsize=cell * 0.12, distance=-0.35)
        )
        plate = plate.cut(txt_title)
    except Exception:
        pass

    # 2. Column Headers (Arc Counts) above each column
    col_header_y = plate_h / 2.0 - margin_top * 0.72
    for c_idx, c_item in enumerate(col_params):
        cx = grid_left_x + c_idx * cell + cell / 2.0
        try:
            txt_col = (
                cq.Workplane("XY", origin=(cx, col_header_y, face_z))
                .text(c_item["label"], fontsize=cell * 0.11, distance=-0.35)
            )
            plate = plate.cut(txt_col)
        except Exception:
            pass

    # 3. Row Headers (Clearance & Bump) in left margin
    row_header_x = -plate_w / 2.0 + margin_left * 0.48
    for r_idx, r_item in enumerate(row_params):
        cy = grid_top_y - r_idx * cell - cell / 2.0
        try:
            txt_row = (
                cq.Workplane("XY", origin=(row_header_x, cy, face_z))
                .text(r_item["label"], fontsize=cell * 0.10, distance=-0.35)
            )
            plate = plate.cut(txt_row)
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
