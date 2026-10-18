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
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_power_tool_holder(units=2, length=140.0, slot_width=45.0, slot_length=120.0, web_thickness=5.5):
    width = units * UNIT_WIDTH
    backplate_thickness = 11.0
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(units=units)
    
    # Shelf thickness
    shelf_t = 5.0  # Reduced for clearance of screw holes
    front_z = -backplate_thickness - length
    back_z = -backplate_thickness
    
    # YZ Workplane maps Local X = Global Y, Local Y = Global Z.
    shelf_pts = [
        (top_y - shelf_t, back_z),
        (top_y - shelf_t, front_z),
        (top_y, front_z),
        (top_y, back_z),
    ]
    brace_pts = [
        (top_y - shelf_t, back_z),         # Top back
        (top_y - shelf_t, front_z),        # Front tip
        (bottom_y, back_z),                # Bottom back
    ]
    
    body = (
        body
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
        .extrude(web_thickness)
        .workplaneFromTagged("right_wp")
        .polyline(brace_pts)
        .close()
        .extrude(-web_thickness)
    )
    
    # Cut the U-slot through the shelf vertically
    # Workplane("ZX") maps Local X = Global Z, Local Y = Global X
    slot_back_z = front_z + slot_length
    body = (
        body
        .copyWorkplane(cq.Workplane("ZX", origin=(0, top_y + 10.0, 0)))
        .moveTo(front_z, -slot_width / 2.0)
        .lineTo(front_z, slot_width / 2.0)
        .lineTo(slot_back_z - slot_width / 2.0, slot_width / 2.0)
        .threePointArc((slot_back_z, 0), (slot_back_z - slot_width / 2.0, -slot_width / 2.0))
        .close()
        .cutBlind(-50.0)
    )
    
    # Add triangular cutouts to the braces via 2D Sketch with filleted vertices
    try:
        cutout_sketch = (
            cq.Sketch()
            .polygon(brace_pts)
            .wires()
            .offset(-15.0, mode="r")
            .reset()
            .vertices()
            .fillet(5.0)
        )
        body = (
            body
            .workplaneFromTagged("right_wp")
            .placeSketch(cutout_sketch)
            .cutBlind(-width)
        )
    except Exception:
        pass
        
    # Add fillets to the inside edges of the braces and shelf where they meet the backplate
    body = (
        body
        .faces("-Z")
        .faces(">Z")
        .edges("not <Y")
        .fillet(4.0)
    )
        
    # Cut screws
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
        
    # Rotate 180 degrees around X so it prints upside down
    body = body.rotate((0, 0, 0), (1, 0, 0), 180)
    
    return body

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--units", type=int, default=2)
    parser.add_argument("--length", type=float, default=140.0)
    parser.add_argument("--slot-width", type=float, default=45.0)
    parser.add_argument("--slot-length", type=float, default=120.0)
    
    args = parser.parse_args()
    
    holder = create_power_tool_holder(
        units=args.units,
        length=args.length,
        slot_width=args.slot_width,
        slot_length=args.slot_length
    )
    
    filename = f"power_tool_holder_{args.units}u_L{args.length}.stl"
    export_model(holder, filename, print_orientation="top_down", category="tool_holders")
