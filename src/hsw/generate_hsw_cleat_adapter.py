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
import argparse
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH,
    export_model,
    create_nut_slot,
    HSW_ASSETS_DIR,
    BACKPLATE_TOP_Y,
    TOP_RIDGE_Y,
    RIDGE_DEPTH,
    DEFAULT_RAIL_HEIGHT,
    RAIL_PLAY,
    get_bottom_groove_y,
    get_bottom_edge_y,
    get_backplate_height,
)

def load_hsw_plug(step_path=None, orientation="standard"):
    """
    Loads the official Honeycomb Storage Wall insert (insert-empty.step),
    slices off the 2.0 mm outer flange at Z=8.0 to isolate the 8.0 mm tall plug
    that enters the HSW socket (including snap tabs and lead-in chamfer),
    and orients it so the base sits at Z=0 and the tip points into +Z (into the wall).
    
    If orientation == 'standard':
        Rotates 90 deg around Z so points face up/down (HSW column vertical pitch 40.88 mm).
    If orientation == 'rotated':
        Retains default orientation so flats face up/down (HSW rotated wall pitch 23.6 / 47.2 mm).
    """
    if step_path is None:
        step_path = os.path.join(HSW_ASSETS_DIR, "insert-empty.step")
        
    if not os.path.exists(step_path):
        raise FileNotFoundError(f"HSW insert STEP file not found at: {step_path}")
        
    model = cq.importers.importStep(step_path).val()
    bb = model.BoundingBox()
    cx = (bb.xmin + bb.xmax) / 2.0
    cy = (bb.ymin + bb.ymax) / 2.0
    centered = model.translate((-cx, -cy, -bb.zmin))
    
    # Slice off the outer flange at Z=8.0 (keep Z in [0, 8.0])
    cutter = cq.Workplane("XY").workplane(offset=4.0).box(50.0, 50.0, 8.0).val()
    plug_body = centered.intersect(cutter)
    
    # Rotate 180 degrees around X so base is at Z=0 and tip is at Z=8.0
    plug = plug_body.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, 8.0))
    
    if orientation == "standard":
        plug = plug.rotate((0, 0, 0), (0, 0, 1), 90)
    elif orientation == "rotated":
        pass
    else:
        raise ValueError(f"Unsupported orientation: {orientation}")
        
    return plug

def create_hsw_cleat_adapter(orientation="standard", rotated_pitch=23.6, screw_m="M3", height=None, step_path=None):
    """
    Builds a 1U-wide Honeycomb Storage Wall to French Cleat adapter.
    
    Reference Frame:
      - Top: +Y
      - Bottom: -Y
      - Front: -Z (cleat locking ridges and screw faces)
      - Back: +Z (flush face resting against HSW wall, male plugs protruding into wall)
      - Left: -X
      - Right: +X
    """
    width = UNIT_WIDTH  # Exactly 1U = 28.0 mm
    
    if orientation == "standard":
        pitch = 40.88
        # Standard: points are up/down along Y (radius = 22.55 / 2 = 11.275)
        plug_radius_y = 11.275
    elif orientation == "rotated":
        pitch = float(rotated_pitch)
        # Rotated: flats are up/down along Y (radius = 19.70 / 2 = 9.85)
        plug_radius_y = 9.85
    else:
        raise ValueError(f"Unknown orientation: {orientation}")
        
    if screw_m == "M3":
        screw_d = 3.4
        nut_waf = 5.5
        nut_thick = 2.4
    elif screw_m == "M4":
        screw_d = 4.5
        nut_waf = 7.0
        nut_thick = 3.2
    elif screw_m == "M5":
        screw_d = 5.5
        nut_waf = 8.0
        nut_thick = 4.0
    else:
        raise ValueError(f"Unsupported screw size: {screw_m}")
        
    slot_t = nut_thick + 0.1
    slot_z_center = 4.0 + slot_t / 2.0
    backplate_thickness = max(8.0, 4.0 + slot_t + 1.2)
    
    # Standard heights and ridge locations
    if height is None:
        height = get_backplate_height()  # Default 114.0 mm
        
    y_top = BACKPLATE_TOP_Y  # 20.0 mm
    y_bot = y_top - height    # default: 20.0 - 114.0 = -94.0 mm
    
    top_screw_y = TOP_RIDGE_Y  # 10.0 mm
    bottom_screw_y = y_bot + 10.0  # default: -84.0 mm (matching get_bottom_groove_y())
    
    t = backplate_thickness
    ridge_depth = RIDGE_DEPTH  # 3.0 mm
    
    # Invariant Object Reference Frame & Workplane rules:
    # Use "YZ" workplane (Local X = Global Y, Local Y = Global Z)
    # Profile includes:
    # 1. 45-degree French cleat downward slope at top (+Y)
    # 2. Top shallow trapezoidal locking ridge at top_screw_y (Y=10.0)
    # 3. Bottom shallow trapezoidal locking ridge at bottom_screw_y (Y=-84.0)
    # 4. Flat back face at Z=t resting flush against wall
    pts = [
        (y_top, t),
        (y_top - t, 0.0),
        (top_screw_y + 3.5, 0.0),
        (top_screw_y + 0.5, -ridge_depth),
        (top_screw_y - 0.5, -ridge_depth),
        (top_screw_y - 3.5, 0.0),
        (bottom_screw_y + 3.5, 0.0),
        (bottom_screw_y + 0.5, -ridge_depth),
        (bottom_screw_y - 0.5, -ridge_depth),
        (bottom_screw_y - 3.5, 0.0),
        (y_bot, 0.0),
        (y_bot, t)
    ]
    
    body = (
        cq.Workplane("YZ")
        .polyline(pts).close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )
    
    # Clearance screw holes along Z at X=0
    for sy in [top_screw_y, bottom_screw_y]:
        screw_hole = (
            cq.Workplane("XY")
            .workplane(offset=-ridge_depth - 5.0)
            .center(0, sy)
            .circle(screw_d / 2.0)
            .extrude(backplate_thickness + ridge_depth + 10.0)
        )
        body = body.cut(screw_hole)
    
    # Shortest-path side-entry captive nut slots:
    # Nut slides in from right (+X) side across width/2 (14mm).
    # Pusher hole exits through left (-X) side.
    side_depth = width / 2.0  # 14.0 mm
    for sy in [top_screw_y, bottom_screw_y]:
        slot_solid = create_nut_slot(screw_m, depth=side_depth, push_hole=True)
        # Rotate -90 degrees around Z so +Y (entry) maps to +X (right edge), and -Y (pusher) maps to -X (left edge)
        slot_solid = cq.Workplane(slot_solid).rotate((0, 0, 0), (0, 0, 1), -90).val()
        slot_solid = slot_solid.translate(cq.Vector(0, sy, slot_z_center))
        body = body.cut(cq.Workplane(slot_solid))
    
    # HSW Plugs position:
    # Plugs start 5.0 mm below topmost ridge.
    # Top ridge lower edge is at top_screw_y - 3.5 = 6.5 mm.
    # Plug top boundary starts at 6.5 - 5.0 = 1.5 mm.
    plug_top_bound_y = (top_screw_y - 3.5) - 5.0  # 1.5 mm
    top_plug_y = plug_top_bound_y - plug_radius_y
    bot_plug_y = top_plug_y - pitch
    
    # Load and position HSW male connector plugs on the back face (Z=t)
    plug = load_hsw_plug(step_path=step_path, orientation=orientation)
    
    top_plug = plug.translate((0, top_plug_y, t))
    bot_plug = plug.translate((0, bot_plug_y, t))
    
    adapter = body.union(cq.Workplane(top_plug)).union(cq.Workplane(bot_plug))
    return adapter

def main():
    parser = argparse.ArgumentParser(
        description="Generate Honeycomb Storage Wall (HSW) to French Cleat Adapter"
    )
    parser.add_argument(
        "--step-path",
        type=str,
        default=None,
        help="Path to official HSW insert-empty.step (optional, defaults to assets/hsw/insert-empty.step)"
    )
    parser.add_argument(
        "--hsw-orientation",
        choices=["standard", "rotated"],
        default="standard",
        help="HSW grid wall orientation: 'standard' (points up/down, 40.88mm pitch) or 'rotated' (flats up/down, 23.6/47.2mm pitch)"
    )
    parser.add_argument(
        "--rotated-pitch",
        type=float,
        default=23.6,
        help="Vertical center-to-center pitch in mm for rotated grid (default: 23.6, supports 47.2)"
    )
    parser.add_argument(
        "--screw",
        choices=["M3", "M4", "M5"],
        default="M3",
        help="Captive nut and clearance screw size (default: M3)"
    )
    parser.add_argument(
        "--height",
        type=float,
        default=None,
        help="Total adapter height in mm (default: matches standard backplate height 114.0 mm)"
    )
    parser.add_argument(
        "--export",
        choices=["both", "stl", "step"],
        default="both",
        help="Export format (default: both)"
    )
    parser.add_argument(
        "--print-orientation",
        choices=["right_down", "left_down", "face_down", "back_down", "top_down", "bottom_down", "none"],
        default="right_down",
        help="Print orientation for export (default: right_down for flat side printing without supports)"
    )
    
    args = parser.parse_args()
    
    adapter = create_hsw_cleat_adapter(
        orientation=args.hsw_orientation,
        rotated_pitch=args.rotated_pitch,
        screw_m=args.screw,
        height=args.height,
        step_path=args.step_path
    )
    
    if args.hsw_orientation == "standard":
        filename = f"hsw_cleat_adapter_1u_standard_{args.screw}.stl"
    else:
        pitch_str = f"P{args.rotated_pitch:.1f}".replace(".0", "")
        filename = f"hsw_cleat_adapter_1u_rotated_{pitch_str}_{args.screw}.stl"
        
    export_model(
        adapter,
        filename,
        category="hsw",
        export=args.export,
        print_orientation=args.print_orientation
    )

if __name__ == "__main__":
    main()
