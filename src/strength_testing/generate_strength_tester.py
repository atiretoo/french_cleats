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

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, create_baseplate, drill_backplate_screws, export_model

def create_strength_tester(shelf_position="top", thickness_mode="full", rail_height=73.0):
    units = 1
    width = units * UNIT_WIDTH
    shelf_u = 6
    shelf_depth = shelf_u * UNIT_WIDTH 
    
    if thickness_mode == "ultra_thin":
        backplate_t = 5.5
        shelf_t = 2.0
        brace_t = 1.0
    elif thickness_mode == "half":
        backplate_t = 5.5
        shelf_t = 5.0
        brace_t = 2.5
    else:
        backplate_t = 11.0
        shelf_t = 10.0
        brace_t = 5.0
        
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(units, rail_height, backplate_thickness=backplate_t)
    
    if shelf_position == "top":
        shelf_top_y = top_y - 14.0 # Keep it below the top edge to allow filleting
    else:
        shelf_top_y = top_y - 40.0
        
    shelf_bottom_y = shelf_top_y - shelf_t
    
    shelf_pts = [
        (shelf_bottom_y, -backplate_t),
        (shelf_bottom_y, -backplate_t - shelf_depth),
        (shelf_top_y, -backplate_t - shelf_depth),
        (shelf_top_y, -backplate_t)
    ]
    brace_pts = [
        (bottom_y, -backplate_t),
        (shelf_bottom_y, -backplate_t),
        (shelf_bottom_y, -backplate_t - shelf_depth)
    ]

    tool_holder = (
        tool_holder
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .end(2)
        .faces(">X")
        .workplane(centerOption="ProjectedOrigin")
        .tag("right_wp")
        .end(2)
        .workplaneFromTagged("right_wp")
        .polyline(shelf_pts)
        .close()
        .extrude(-width)
        .workplaneFromTagged("right_wp")
        .workplane(offset=-width)
        .polyline(brace_pts)
        .close()
        .extrude(brace_t)
    )
    
    # --- TRUSS CUTOUT ---
    strut_width = 15.0 # Using 15mm to ensure it fits nicely in both top and mid models
    try:
        cutout_sketch = (
            cq.Sketch()
            .polygon(brace_pts)
            .wires()
            .offset(-strut_width, mode="r")
            .reset()
            .vertices()
            .fillet(8.0)
        )
        tool_holder = (
            tool_holder
            .workplaneFromTagged("right_wp")
            .workplane(offset=-width)
            .placeSketch(cutout_sketch)
            .cutBlind(brace_t)
        )
    except Exception as e:
        print("Truss cutout failed:", e)
    
    hole_z = -backplate_t - shelf_depth + 10.0 
    tool_holder = (
        tool_holder
        .copyWorkplane(cq.Workplane("ZX", origin=(0, shelf_top_y + 1, 0)))
        .moveTo(hole_z, 0)
        .circle(5.0 / 2.0)
        .cutBlind(-(shelf_t + 2.0))
    )
    
    tool_holder = drill_backplate_screws(tool_holder, screw_pts)
    
    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate strength testers")
    args = parser.parse_args()
        
    for pos in ["top", "mid"]:
        for thick in ["full", "half"]:
            holder = create_strength_tester(pos, thick)
            filename = f"tester_{pos}_{thick}.stl"
            export_model(holder, filename, category='strength_testing', export="stl")
            print(f"Exported {filename}")

if __name__ == "__main__":
    main()
