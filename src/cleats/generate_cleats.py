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
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH, export_model, create_nut_slot, MULTICONNECT_ASSETS_DIR,
    get_ridge_points, NUT_SLOT_TOLERANCE
)
import argparse
import os

def load_round_button(path=None):
    if path is None:
        path = os.path.join(MULTICONNECT_ASSETS_DIR, 'round.step')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Multiconnect round button asset not found: {path}")
    model = cq.importers.importStep(path)
    model = model.rotate((0, 0, 0), (1, 0, 0), 180)
    return model

def create_top_cleat(units=2, rail_thickness=19.0, mount_type="groove", screw_m="M3"):
    width = units * UNIT_WIDTH
    tip_clearance = 2.0
    
    if mount_type == "groove":
        screw_y = 10.0
        top_y = 20.0
    else:
        screw_y = 14.0 
        top_y = 28.0   
    
    p1 = (0, 0)
    p2a = (-rail_thickness + tip_clearance, rail_thickness - tip_clearance)
    p2b = (-rail_thickness + tip_clearance, rail_thickness)
    p3 = (top_y, rail_thickness)
    p4 = (top_y, 0)
    
    pts = [p1, p2a, p2b, p3, p4]
    if mount_type == "groove":
        pts.extend(get_ridge_points(screw_y))
    
    cleat = (
        cq.Workplane("YZ")
        .polyline(pts).close()
        .extrude(width / 2.0, both=True)
    )
    
    if mount_type == "groove":
        if screw_m == "M3":
            screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
        elif screw_m == "M4":
            screw_d, nut_waf, nut_thick = 4.5, 7.0, 3.2
        elif screw_m == "M5":
            screw_d, nut_waf, nut_thick = 5.5, 8.0, 4.0
        else:
            raise ValueError(f"Unsupported screw size: {screw_m}")
            
        slot_t = nut_thick + NUT_SLOT_TOLERANCE
        slot_z_center = 4.0 + slot_t / 2.0
        
        screw_pts = [(-width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH, screw_y) for i in range(units)]
        cleat = cleat.faces(">Z").workplane().pushPoints(screw_pts).hole(screw_d)
        
        # Nut slot slides from top down to screw_y
        depth = top_y - screw_y
        slot_solid = create_nut_slot(screw_m, depth=depth, push_hole=True)
        for x, y in screw_pts:
            s_inst = cq.Workplane(slot_solid).translate((x, y, slot_z_center))
            cleat = cleat.cut(s_inst)
    else:
        button = load_round_button()
        for i in range(units):
            x = -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH
            btn_inst = button.translate((x, screw_y, rail_thickness + 4.0))
            cleat = cleat.union(btn_inst)
            
    return cleat


def create_bottom_cleat(units=2, rail_thickness=19.0, screw_m="M3"):
    width = units * UNIT_WIDTH
    
    if screw_m == "M3":
        screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
    elif screw_m == "M4":
        screw_d, nut_waf, nut_thick = 4.5, 7.0, 3.2
    elif screw_m == "M5":
        screw_d, nut_waf, nut_thick = 5.5, 8.0, 4.0
    else:
        raise ValueError(f"Unsupported screw size: {screw_m}")
        
    height = 20.0
    screw_y = 0.0
    
    pts = [
        (-height / 2.0, 0),
        (-height / 2.0, rail_thickness),
        (-5.0, rail_thickness),
        (height / 2.0, 4.0),
        (height / 2.0, 0),
    ] + get_ridge_points(screw_y)
    
    cleat = (
        cq.Workplane("YZ")
        .polyline(pts).close()
        .extrude(width / 2.0, both=True)
    )
    
    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    slot_z_center = 4.0 + slot_t / 2.0
    
    screw_pts = [(-width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH, screw_y) for i in range(units)]
    cleat = cleat.faces(">Z").workplane().pushPoints(screw_pts).hole(screw_d)
    
    depth = screw_y - (-height / 2.0)
    slot_solid = create_nut_slot(screw_m, depth=depth, push_hole=True)
    slot_solid_rot = cq.Workplane(slot_solid).rotate((0, 0, 0), (0, 0, 1), 180).val()
    for x, y in screw_pts:
        s_inst = cq.Workplane(slot_solid_rot).translate((x, y, slot_z_center))
        cleat = cleat.cut(s_inst)
        
    return cleat


def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat attachments")
    parser.add_argument("--type", choices=["top", "bottom", "both"], default="both", help="Type of cleat to generate")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--rail-thickness", type=float, default=19.0, help="Thickness of the rail in mm")
    parser.add_argument("--mount", choices=["groove", "multiconnect"], default="groove", help="Mount type")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")
    
    args = parser.parse_args()
    
    if args.type in ["top", "both"]:
        top = create_top_cleat(args.units, args.rail_thickness, args.mount, args.screw)
        filename = f"top_cleat_{args.units}u_{args.mount}_T{args.rail_thickness}_{args.screw}.stl"
        export_model(top, filename, category='cleats', export=args.export)
        print(f"Exported {filename}")
        
    if args.type in ["bottom", "both"] and args.mount == "groove":
        bot = create_bottom_cleat(args.units, args.rail_thickness, args.screw)
        filename = f"bottom_cleat_{args.units}u_groove_T{args.rail_thickness}_{args.screw}.stl"
        export_model(bot, filename, category='cleats', export=args.export)
        print(f"Exported {filename}")

if __name__ == "__main__":
    main()
