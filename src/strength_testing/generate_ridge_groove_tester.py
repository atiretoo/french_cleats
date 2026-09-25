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
generate_ridge_groove_tester.py

Generates 1U physical test coupons to evaluate self-centering and impingement
between the French cleat shallow trapezoidal ridge and backplate groove:
  1. Universal Backplate Reference Coupon:
     - 1U wide, 25mm tall, 11mm thick, with standard 45-degree groove and M3 clearance hole.
     - Serves as the fixed gauge printed once.
  2. 1U Bottom Cleat Test Coupons:
     - Compact (20mm high), quick-print coupons (~15 min each).
     - Standard M3 nut capture slot and push hole.
     - Parametric sidewall clearance (c_side) and ridge draft angle (theta_r).
     - Embossed/debossed identification labels on top print layer (+X face).
"""

import cadquery as cq
import math
import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH,
    GROOVE_DEPTH,
    GROOVE_SURFACE_HALF_WIDTH,
    GROOVE_BOTTOM_HALF_WIDTH,
    create_nut_slot,
    export_model
)

# Standard Test Coupon Definitions
TEST_VARIANTS = {
    # Control
    "C0.45_45": {"clearance": 0.45, "angle": 45.0, "desc": "Baseline parallel walls (0.45mm clearance)"},
    # Series A: Clearance sweep at nominal 45.0 deg
    "C0.30_45": {"clearance": 0.30, "angle": 45.0, "desc": "Parallel walls (0.30mm clearance)"},
    "C0.20_45": {"clearance": 0.20, "angle": 45.0, "desc": "Parallel walls (0.20mm clearance)"},
    "C0.10_45": {"clearance": 0.10, "angle": 45.0, "desc": "Parallel walls (0.10mm clearance)"},
    "C0.05_45": {"clearance": 0.05, "angle": 45.0, "desc": "Parallel walls (0.05mm tight fit)"},
    # Series B: Angle variation / self-centering wedge
    "A43_W0.20": {"clearance": 0.20, "angle": 43.0, "desc": "43 deg shallower wedge (0.20mm base clearance)"},
    "A47_W0.20": {"clearance": 0.20, "angle": 47.0, "desc": "47 deg steeper wedge (0.20mm base clearance)"},
    "A48_W0.15": {"clearance": 0.15, "angle": 48.0, "desc": "48 deg steeper wedge (0.15mm base clearance)"},
}


def create_backplate_coupon(label="BP_REF_45"):
    """
    Creates a 1U reference backplate test coupon with standard 45-degree groove.
    - Width: 1U (28.0 mm)
    - Height: 25.0 mm (Y from -12.5 to +12.5 mm)
    - Thickness: 11.0 mm (Z from 0 to -11.0 mm)
    - Standard Groove: 3.0 mm deep, 7.0 mm surface opening, 1.0 mm flat bottom at 45 deg.
    - M3 clearance hole (dia 3.4 mm) and counterbore (dia 6.5 mm x 4.5 mm depth).
    - 2.0 mm chamfers on back edges (Slant3D standard).
    - Debossed identification label.
    """
    width = UNIT_WIDTH
    bp_height = 25.0
    bp_thick = 11.0
    
    # 45-degree trapezoidal groove geometry
    g_depth = GROOVE_DEPTH
    g_surf_hw = GROOVE_SURFACE_HALF_WIDTH
    g_bot_hw = GROOVE_BOTTOM_HALF_WIDTH
    
    pts_bp = [
        (bp_height / 2.0 - 2.0, 0),
        (g_surf_hw, 0),
        (g_bot_hw, -g_depth),
        (-g_bot_hw, -g_depth),
        (-g_surf_hw, 0),
        (-bp_height / 2.0 + 2.0, 0),
        (-bp_height / 2.0, -2.0),
        (-bp_height / 2.0, -bp_thick),
        (bp_height / 2.0, -bp_thick),
        (bp_height / 2.0, -2.0),
        (bp_height / 2.0 - 2.0, 0)
    ]
    
    bp = (
        cq.Workplane("YZ")
        .polyline(pts_bp).close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )
    
    # 2.0mm fillet on top-front edge (matches Slant3D standard)
    try:
        bp = bp.edges('>Y and <Z').fillet(2.0)
    except Exception:
        pass
        
    # M3 through-hole (dia 3.4 mm) centered at (0, 0)
    hole = cq.Workplane("XY").circle(3.4 / 2.0).extrude(100).translate((0, 0, -50))
    bp = bp.cut(hole)
    
    # M3 socket head counterbore on front face (Z = -bp_thick)
    cbore = cq.Workplane("XY").circle(6.5 / 2.0).extrude(4.5).translate((0, 0, -bp_thick))
    bp = bp.cut(cbore)
    
    # Debossed label on top print face (+X side face when printed left_down)
    try:
        txt_side = (
            cq.Workplane("YZ", origin=(width / 2.0, 0, -bp_thick / 2.0))
            .text(label, fontsize=3.2, distance=-0.5)
        )
        bp = bp.cut(txt_side)
    except Exception as e:
        print(f"Warning: could not deboss backplate label: {e}")
        
    return bp


def create_cleat_coupon(label="C0.10_45", side_clearance=0.10, ridge_angle_deg=45.0):
    """
    Creates a 1U bottom cleat test coupon with parametric ridge geometry.
    - Width: 1U (28.0 mm)
    - Height: 20.0 mm (Y from -10.0 to +10.0 mm)
    - Rail Thickness: 19.0 mm (Z from 0 to +19.0 mm)
    - Ridge: Projects into -Z (depth 2.20 mm, ensuring 0.80 mm crest clearance).
    - M3 bolt hole and bottom-entry nut capture slot with push hole.
    - Debossed identification label on +X side face (top layer during left_down print).
    """
    width = UNIT_WIDTH
    rail_thickness = 19.0
    screw_m = "M3"
    screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
    
    height = 20.0
    screw_y = 0.0
    
    # Fixed ridge height ensures 0.80 mm crest clearance inside 3.0 mm groove
    ridge_height = 2.20
    
    # Calculate ridge half-widths based on side_clearance and ridge_angle_deg
    ridge_surf_hw = GROOVE_SURFACE_HALF_WIDTH - side_clearance
    taper = ridge_height * math.tan(math.radians(ridge_angle_deg))
    ridge_peak_hw = ridge_surf_hw - taper
    if ridge_peak_hw < 0.20:
        ridge_peak_hw = 0.20
        
    p1 = (-height / 2.0, 0)
    p2 = (-height / 2.0, rail_thickness)
    p3 = (-5.0, rail_thickness)
    p3b = (height / 2.0, 4.0)
    p4 = (height / 2.0, 0)
    p5 = (screw_y + ridge_surf_hw, 0)
    p6 = (screw_y + ridge_peak_hw, -ridge_height)
    p7 = (screw_y - ridge_peak_hw, -ridge_height)
    p8 = (screw_y - ridge_surf_hw, 0)
    
    pts = [p1, p2, p3, p3b, p4, p5, p6, p7, p8]
    
    cleat = (
        cq.Workplane("YZ")
        .polyline(pts).close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )
    
    # M3 bolt clearance hole
    hole = cq.Workplane("XY").workplane(offset=-10).center(0, screw_y).circle(screw_d / 2.0).extrude(50)
    cleat = cleat.cut(hole)
    
    # Bottom-entry nut slot with push hole
    slot_t = nut_thick + 0.1
    slot_z_center = 4.0 + slot_t / 2.0
    depth = screw_y - (-height / 2.0)
    slot_solid = create_nut_slot(screw_m, depth=depth, push_hole=True)
    slot_solid = cq.Workplane(slot_solid).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180).val()
    slot_solid = slot_solid.translate(cq.Vector(0, screw_y, slot_z_center))
    cleat = cleat.cut(cq.Workplane(slot_solid))
    
    # Deboss label on +X side face (top surface during left_down print)
    try:
        txt_side = (
            cq.Workplane("YZ", origin=(width / 2.0, 0, 9.5))
            .text(label, fontsize=3.0, distance=-0.5)
        )
        cleat = cleat.cut(txt_side)
    except Exception as e:
        print(f"Warning: could not deboss cleat label: {e}")
        
    return cleat


def main():
    parser = argparse.ArgumentParser(description="Generate 1U Ridge/Groove Test Coupons")
    parser.add_argument("--part", choices=["backplate", "cleats", "all"], default="all",
                        help="Which parts to generate (default: all)")
    parser.add_argument("--variant", type=str, default=None,
                        help="Specific cleat variant ID to generate (e.g. C0.10_45, A47_W0.20)")
    parser.add_argument("--clearance", type=float, default=None,
                        help="Custom sidewall clearance in mm (used with --custom)")
    parser.add_argument("--angle", type=float, default=None,
                        help="Custom ridge wall angle in degrees (used with --custom)")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both",
                        help="Export format (default: both)")
    parser.add_argument("--bed-chamfer", type=float, default=2.0,
                        help="Bed-contact perimeter chamfer in mm (default: 2.0)")
                        
    args = parser.parse_args()
    
    # 1. Backplate Reference Coupon
    if args.part in ["backplate", "all"]:
        print("Generating Universal Backplate Reference Coupon (BP_REF_45)...")
        bp = create_backplate_coupon("BP_REF_45")
        export_model(
            bp,
            "backplate_coupon_1u_REF_45.stl",
            category="strength_testing",
            export=args.export,
            print_orientation="left_down",
            bed_chamfer=args.bed_chamfer
        )
        
    # 2. Cleat Test Coupons
    if args.part in ["cleats", "all"]:
        if args.variant:
            # Single variant requested
            if args.variant in TEST_VARIANTS:
                cfg = TEST_VARIANTS[args.variant]
                c_side = cfg["clearance"]
                ang = cfg["angle"]
            else:
                c_side = args.clearance if args.clearance is not None else 0.10
                ang = args.angle if args.angle is not None else 45.0
            v_name = args.variant
            print(f"Generating Cleat Coupon {v_name} (clearance={c_side}mm, angle={ang} deg)...")
            cleat = create_cleat_coupon(v_name, side_clearance=c_side, ridge_angle_deg=ang)
            export_model(
                cleat,
                f"cleat_coupon_{v_name}.stl",
                category="strength_testing",
                export=args.export,
                print_orientation="left_down",
                bed_chamfer=args.bed_chamfer
            )
        else:
            # Generate all standard test matrix variants
            print("Generating full suite of cleat test coupons...")
            for v_name, cfg in TEST_VARIANTS.items():
                c_side = cfg["clearance"]
                ang = cfg["angle"]
                print(f"  -> Generating {v_name}: clearance={c_side}mm, angle={ang} deg ({cfg['desc']})")
                cleat = create_cleat_coupon(v_name, side_clearance=c_side, ridge_angle_deg=ang)
                export_model(
                    cleat,
                    f"cleat_coupon_{v_name}.stl",
                    category="strength_testing",
                    export=args.export,
                    print_orientation="left_down",
                    bed_chamfer=args.bed_chamfer
                )
                
    print("\nAll requested test coupons successfully generated and exported to exports/*/strength_testing/")


if __name__ == "__main__":
    main()
