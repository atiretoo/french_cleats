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
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate,
    drill_backplate_screws, export_model, create_nut_slot, support_fin
)

def create_shooo_cam_holder(num_tools=1):
    # === Shooo's Mechanism Dimensions ===
    block_h = 47.63        # Height protruding from backplate
    block_y = 47.6         # Length along wall
    block_x = 12.6         # Width
    block_r = 3.81         # Vertical edge fillet radius
    gap = 26.241           # Distance between the two blocks

    mech_width = (num_tools + 1) * block_x + num_tools * gap
    units = max(1, math.ceil(mech_width / UNIT_WIDTH))

    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(units=units)

    # Holes on top face
    reg_hole_dia = 4.508
    reg_hole_depth = 6.0
    m3_hole_dia = 3.4

    # Distances from bottom edge of the block (the side closest to the groove)
    reg_hole_1_y_offset = 11.43
    m3_hole_y_offset = 16.087
    reg_hole_2_y_offset = 29.953

    # Cam Post
    post_h = 10.160
    post_r = 4.5 / 2.0
    boss_r = 5.5 / 2.0
    boss_h = 1.5

    # User measured 19.83mm from the "top" (groove-side) edge to the edge of the pin.
    post_y_offset = 19.83 + post_r

    # Post position within the gap (from left block inner face)
    post_x_from_left = 6.24

    # Center the mechanism on the baseplate (Between Y=0 and Y=-74 is 74mm. Center is -37)
    block_y_bot = -37.0 - (block_y / 2.0)

    # Calculate absolute Y positions anchored from the bottom edge
    reg_hole_1_y = block_y_bot + reg_hole_1_y_offset
    m3_hole_y = block_y_bot + m3_hole_y_offset
    reg_hole_2_y = block_y_bot + reg_hole_2_y_offset
    post_y = block_y_bot + post_y_offset

    start_x = -(mech_width / 2.0)
    top_z = -BACKPLATE_THICKNESS - block_h

    block_xs = [start_x + (block_x / 2.0) + i * (block_x + gap) for i in range(num_tools + 1)]
    block_pts = [(x, block_y_bot + block_y / 2.0) for x in block_xs]
    reg_pts = [(x, y) for x in block_xs for y in (reg_hole_1_y, reg_hole_2_y)]
    m3_pts = [(x, m3_hole_y) for x in block_xs]
    post_pts = [(block_xs[i] + (block_x / 2.0) + post_x_from_left, post_y) for i in range(num_tools)]

    block_sketch = (
        cq.Sketch()
        .push(block_pts)
        .rect(block_x, block_y)
        .reset()
        .vertices()
        .fillet(block_r)
    )

    body = (
        body
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .end(2)
        .workplaneFromTagged("back_wp")
        .workplane(offset=-BACKPLATE_THICKNESS)
        .placeSketch(block_sketch)
        .extrude(-block_h)
        .workplaneFromTagged("back_wp")
        .workplane(offset=top_z)
        .pushPoints(reg_pts)
        .circle(reg_hole_dia / 2.0)
        .cutBlind(reg_hole_depth)
        .workplaneFromTagged("back_wp")
        .workplane(offset=top_z)
        .pushPoints(m3_pts)
        .circle(m3_hole_dia / 2.0)
        .cutBlind(35.0)
        .workplaneFromTagged("back_wp")
        .workplane(offset=-BACKPLATE_THICKNESS)
        .pushPoints(post_pts)
        .circle(boss_r)
        .extrude(-boss_h)
        .workplaneFromTagged("back_wp")
        .workplane(offset=-BACKPLATE_THICKNESS - boss_h)
        .pushPoints(post_pts)
        .circle(post_r)
        .extrude(-(post_h - boss_h))
    )

    # M3 Captive Nut Slots (5mm from the front face)
    slot_z = top_z + 5.0
    slot_proto = create_nut_slot("M3", depth=(block_x / 2.0) + 0.5, push_hole=True)
    nut_cutters = []
    for i, x_pos in enumerate(block_xs):
        slide_dir = -1.0 if i == num_tools else 1.0
        plane = cq.Plane(origin=(x_pos, m3_hole_y, slot_z), xDir=(0, -slide_dir, 0), normal=(0, 0, 1))
        nut_cutters.append(slot_proto.moved(cq.Location(plane)))
    if nut_cutters:
        body = body.cut(cq.Compound.makeCompound(nut_cutters))

    # Cut cleat mounting screws
    if screw_pts:
        body = drill_backplate_screws(body, screw_pts, cbore_depth=20.0)

    return body

def add_support_fin(holder, units):
    # 1. Rotate to back_down then tilt -45 degrees around Y-axis (stands on left edge -X)
    holder = holder.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 1, 0), -45)
    bb = holder.val().BoundingBox()

    baseplate_width = units * UNIT_WIDTH
    cos45 = math.cos(math.radians(-45))
    X_min = (-baseplate_width / 2.0) * cos45
    X_max = (baseplate_width / 2.0) * cos45
    length = X_max - X_min

    # Shift holder so X_min is at X=0 and Z_min is at Z=0
    holder = holder.translate((-X_min, 0, -X_min))

    fin = support_fin(z_gap=0.2, is_right=True, length=length, height=length).rotate((0, 0, 0), (0, 0, 1), -90)
    y_center = (bb.ymin + bb.ymax) / 2.0
    fin = fin.translate((0, y_center, 0))

    return cq.Compound.makeCompound([holder.val(), fin.val()])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Shooo cam mechanism holder.")
    parser.add_argument("--tools", type=int, default=1, help="Number of tools to hold")
    parser.add_argument("--tilt-fin", action="store_true", help="Rotate 45 degrees and model a support fin (avoids horizontal bridge sagging in nut slots)")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")
    args = parser.parse_args()

    cad_holder = create_shooo_cam_holder(num_tools=args.tools)

    mech_width = (args.tools + 1) * 12.6 + args.tools * 26.241
    units = math.ceil(mech_width / UNIT_WIDTH)

    if args.tilt_fin:
        print_holder = add_support_fin(cad_holder, units)
        filename = f"shooo_cam_holder_{args.tools}tools_{units}u_45deg.stl"
        export_model(print_holder, filename, print_orientation="face_down", category="tool_holders", export=args.export, step_shape=cad_holder)
    else:
        filename = f"shooo_cam_holder_{args.tools}tools_{units}u.stl"
        export_model(cad_holder, filename, print_orientation="back_down", category="tool_holders", export=args.export)
