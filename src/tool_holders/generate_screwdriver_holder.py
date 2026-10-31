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

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, drill_backplate_screws, export_model

def create_screwdriver_holder(width_units=1, depth_units=3, hole_size=10.0, hole_spacing=25.0, num_holes=None, rail_height=73.0, hole_sizes=None, recess_size=0.0, recess_depth=1.0):
    brace_thickness = 2.5
    x_margin = 3.0
    front_margin = 3.0
    fillet_size = 5.0
    
    width = width_units * UNIT_WIDTH
    shelf_depth = depth_units * UNIT_WIDTH
    
    has_right_brace = width_units > 1
    
    if hole_sizes:
        actual_hole_sizes = hole_sizes
        num_holes = len(actual_hole_sizes)
        effective_max_size = max(max(actual_hole_sizes), recess_size)
    else:
        effective_max_size = max(hole_size, recess_size)
        actual_hole_sizes = [hole_size] * (num_holes if num_holes else 0)
        
    back_clearance = fillet_size + (max(actual_hole_sizes[0], recess_size) if hole_sizes else effective_max_size) / 2.0
    Z_start = -BACKPLATE_THICKNESS - back_clearance
    
    x_min = -width/2 + brace_thickness + x_margin + effective_max_size/2
    x_max = width/2 - (brace_thickness if has_right_brace else 0) - x_margin - effective_max_size/2
    dx_stagger = max(0, x_max - x_min)
    
    dz_straight = hole_spacing
    dz_stagger_diag = math.sqrt(max(0, hole_spacing**2 - dx_stagger**2)) if dx_stagger > 0 else hole_spacing
    dz_stagger = max(dz_stagger_diag, effective_max_size/2.0 + 1.0)
    
    layout = "straight"
    dz = dz_straight
    
    if not hole_sizes and num_holes is None:
        Z_end = -BACKPLATE_THICKNESS - shelf_depth + front_margin + effective_max_size / 2.0
        D_avail = abs(Z_end - Z_start) if Z_start >= Z_end else 0
        
        n_straight = int(D_avail / dz_straight) + 1 if D_avail >= 0 else 0
        n_stagger = int(D_avail / dz_stagger) + 1 if D_avail >= 0 and dx_stagger > 0 else 0
        
        if n_stagger > n_straight and dx_stagger > 0:
            layout = "staggered"
            num_holes = n_stagger
            dz = dz_stagger
        else:
            layout = "straight"
            num_holes = n_straight
            dz = dz_straight
            
        actual_hole_sizes = [hole_size] * num_holes
    else:
        # User forced num_holes or hole_sizes, calculate depth needed
        def req_depth(n, dz):
            if n <= 0: return 0
            return (n - 1) * dz + back_clearance + front_margin + effective_max_size / 2.0
            
        d_straight = req_depth(num_holes, dz_straight)
        d_stagger = req_depth(num_holes, dz_stagger) if dx_stagger > 0 else float('inf')
        
        if d_stagger <= d_straight and dx_stagger > 0:
            layout = "staggered"
            d_req = d_stagger
            dz = dz_stagger
        else:
            layout = "straight"
            d_req = d_straight
            dz = dz_straight
            
        required_depth_units = int(math.ceil(d_req / UNIT_WIDTH))
        if required_depth_units > depth_units:
            print(f"Warning: {num_holes} holes would overflow the {depth_units}U depth.")
            print(f"Automatically increasing depth to {required_depth_units}U.")
            depth_units = required_depth_units
            shelf_depth = depth_units * UNIT_WIDTH

    if num_holes == 0:
        print(f"Error: Not enough depth to fit even 1 hole.")
        sys.exit(1)

    # Create Baseplate
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        width_units, rail_height
    )

    shelf_top = top_y - 40.0
    shelf_bot = top_y - 45.0

    shelf_pts = [
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS),
    ]
    brace_pts = [
        (bottom_y, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
    ]

    tool_holder = (
        tool_holder
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .end(2)
        .faces(">X")
        .workplane(centerOption="ProjectedOrigin")
        .polyline(shelf_pts)
        .close()
        .extrude(-width)
    )

    brace_offsets = [(-width, brace_thickness)]
    if has_right_brace:
        brace_offsets.append((0.0, -brace_thickness))

    cutout_sketch = None
    if depth_units > 2:
        try:
            cutout_sketch = (
                cq.Sketch()
                .polygon(brace_pts)
                .wires()
                .offset(-15.0, mode="r")
                .reset()
                .vertices()
                .fillet(8.0)
            )
        except Exception:
            cutout_sketch = None

    for wp_offset, extrude_dist in brace_offsets:
        tool_holder = (
            tool_holder
            .faces(">X")
            .workplane(offset=wp_offset, centerOption="ProjectedOrigin")
            .polyline(brace_pts)
            .close()
            .extrude(extrude_dist)
        )
        if cutout_sketch is not None:
            tool_holder = (
                tool_holder
                .faces(">X")
                .workplane(offset=wp_offset, centerOption="ProjectedOrigin")
                .placeSketch(cutout_sketch)
                .cutBlind(extrude_dist)
            )

    try:
        tool_holder = (
            tool_holder
            .faces("-Z")
            .faces("not <Z")
            .edges("|X")
            .edges("not >Y")
            .edges("not <Y")
            .fillet(5.0)
        )
    except Exception:
        pass

    # Coordinates in ZX plane: (z, x)
    hole_zx_pts = []
    for i in range(num_holes):
        z = Z_start - i * dz
        if layout == "staggered":
            x = x_min if i % 2 == 0 else x_max
        else:
            x = (x_min + x_max) / 2.0
        hole_zx_pts.append((z, x))

    if not hole_sizes:
        wp = tool_holder.copyWorkplane(cq.Workplane("ZX", origin=(0, shelf_top, 0))).pushPoints(hole_zx_pts)
        if recess_size > 0 and recess_depth > 0:
            tool_holder = wp.cboreHole(hole_size, recess_size, recess_depth, depth=20.0)
        else:
            tool_holder = wp.hole(hole_size, 20.0)
    else:
        for zx_pt, sz in zip(hole_zx_pts, actual_hole_sizes):
            wp = tool_holder.copyWorkplane(cq.Workplane("ZX", origin=(0, shelf_top, 0))).pushPoints([zx_pt])
            if recess_size > 0 and recess_depth > 0:
                tool_holder = wp.cboreHole(sz, recess_size, recess_depth, depth=20.0)
            else:
                tool_holder = wp.hole(sz, 20.0)

    tool_holder = drill_backplate_screws(tool_holder, screw_pts)

    return tool_holder, width_units, depth_units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat screwdriver holder")
    parser.add_argument("--width-units", type=int, default=1, help="Number of units wide")
    parser.add_argument("--depth-units", type=int, default=3, help="Number of units deep (away from wall)")
    parser.add_argument("--hole-size", type=float, default=10.0, help="Diameter of the holes in mm")
    parser.add_argument("--hole-spacing", type=float, default=25.0, help="Minimum spacing between hole centers in mm")
    parser.add_argument("--num-holes", type=int, default=None, help="Force a specific number of holes (will increase depth if needed)")
    parser.add_argument("--hole-sizes", type=str, default=None, help="Comma separated list of precise hole sizes (overrides hole-size and num-holes)")
    parser.add_argument("--recess-size", type=float, default=0.0, help="Diameter of recess at top of hole")
    parser.add_argument("--recess-depth", type=float, default=1.0, help="Depth of recess at top of hole")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--print-orientation", type=str, default="right_down", choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down"], help="Print orientation for STL export")
    args = parser.parse_args()
    
    hole_sizes_list = None
    if args.hole_sizes:
        hole_sizes_list = [float(x.strip()) for x in args.hole_sizes.split(",")]
        
    holder, fw, fd = create_screwdriver_holder(
        width_units=args.width_units, 
        depth_units=args.depth_units,
        hole_size=args.hole_size, 
        hole_spacing=args.hole_spacing,
        num_holes=args.num_holes,
        rail_height=args.rail_height,
        hole_sizes=hole_sizes_list,
        recess_size=args.recess_size,
        recess_depth=args.recess_depth
    )
    
    if hole_sizes_list:
        filename = f"screwdriver_holder_{fw}x{fd}u_H{args.rail_height}_VAR_S{args.hole_spacing}.stl"
    else:
        layout_str = f"_N{args.num_holes}" if args.num_holes is not None else ""
        filename = f"screwdriver_holder_{fw}x{fd}u_H{args.rail_height}_D{args.hole_size}_S{args.hole_spacing}{layout_str}.stl"
        
    export_model(holder, filename, category='tool_holders', print_orientation=args.print_orientation)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
