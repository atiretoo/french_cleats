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
from core_library import create_baseplate, export_model, create_nut_slot, BACKPLATE_THICKNESS

def create_shooo_cam_holder(num_tools=1):
    # === Shooo's Mechanism Dimensions ===
    block_h = 47.63        # Height protruding from backplate
    block_y = 47.6         # Length along wall
    block_x = 12.6         # Width
    block_r = 3.81         # Vertical edge fillet radius
    gap = 26.241           # Distance between the two blocks
    
    mech_width = (num_tools + 1) * block_x + num_tools * gap
    units = max(1, math.ceil(mech_width / 28.0))
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(units=units)
    
    # Holes on top face
    reg_hole_dia = 4.508
    reg_hole_depth = 6.0
    m3_hole_dia = 3.4
    
    # Distances from bottom edge of the block (the side closest to the groove)
    # The user's original measurements were correctly anchored to the bottom edge!
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
    for i, x_pos in enumerate(block_xs):
        slide_dir = -1.0 if i == num_tools else 1.0
        slot_solid = create_nut_slot("M3", depth=(block_x / 2.0) + 0.5, push_hole=True)
        plane = cq.Plane(origin=(x_pos, m3_hole_y, slot_z), xDir=(0, -slide_dir, 0), normal=(0, 0, 1))
        body = body.cut(slot_solid.moved(cq.Location(plane)))

    # Cut cleat mounting screws
    if screw_pts:
        body = (
            body
            .workplaneFromTagged("back_wp")
            .pushPoints(screw_pts)
            .hole(3.6, 20.0)
            .workplaneFromTagged("back_wp")
            .workplane(offset=-8.0)
            .pushPoints(screw_pts)
            .hole(8.0, 20.0)
        )
        
    return body

def add_support_fin(holder, units):
    from core_library import support_fin
    import math
    
    # 1. Rotate to back_down
    holder = holder.rotate((0,0,0), (1,0,0), 180)
    
    # 2. Tilt 45 degrees around Y-axis (stands on left edge -X)
    holder = holder.rotate((0,0,0), (0,1,0), -45)
    
    bb = holder.val().BoundingBox()
    
    # Calculate exact X boundaries of the baseplate after -45 deg Y rotation
    baseplate_width = units * 28.0
    cos45 = math.cos(math.radians(-45))
    X_min = (-baseplate_width / 2.0) * cos45
    X_max = (baseplate_width / 2.0) * cos45
    
    length = X_max - X_min
    
    # 3. Shift holder so X_min is at X=0, and Z_min is at Z=0.
    # Since backplate is at Z=X, to keep it at Z=X after translation, we must shift Z by the same amount as X.
    holder = holder.translate((-X_min, 0, -X_min))
    
    # 4. Generate the fin from core_library
    # support_fin generates a fin for Z=Y, starting at Y=0, Z=0.
    fin = support_fin(z_gap=0.2, is_right=True, length=length, height=length)
    
    # 5. Rotate fin to support Z=X instead of Z=Y.
    # support_fin is on YZ plane, extruded along X.
    # If we rotate it -90 around Z, Y goes to X, X goes to -Y.
    fin = fin.rotate((0,0,0), (0,0,1), -90)
    
    # 6. Translate fin to the Y-center of the holder
    y_center = (bb.ymin + bb.ymax) / 2.0
    fin = fin.translate((0, y_center, 0))
    
    # 7. Group into an assembly/compound so they remain separate objects in the STEP file
    holder = cq.Compound.makeCompound([holder.val(), fin.val()])
    
    return holder

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Shooo cam mechanism holder.")
    parser.add_argument("--tools", type=int, default=1, help="Number of tools to hold")
    parser.add_argument("--tilt-fin", action="store_true", help="Rotate 45 degrees and model a support fin (avoids horizontal bridge sagging in nut slots)")
    args = parser.parse_args()

    holder = create_shooo_cam_holder(num_tools=args.tools)
    
    # mech_width calculation is the same as inside create_shooo_cam_holder
    mech_width = (args.tools + 1) * 12.6 + args.tools * 26.241
    units = math.ceil(mech_width / 28.0)
    
    if args.tilt_fin:
        holder = add_support_fin(holder, units)
        filename = f"shooo_cam_holder_{args.tools}tools_{units}u_45deg.stl"
        export_model(holder, filename, print_orientation="face_down", category="tool_holders")
    else:
        filename = f"shooo_cam_holder_{args.tools}tools_{units}u.stl"
        export_model(holder, filename, print_orientation="back_down", category="tool_holders")
