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
from core_library import UNIT_WIDTH, BACKPLATE_THICKNESS, create_baseplate, export_model

def create_magnetic_holder(
    units=1,
    mount_type="groove",
    mag_count=2,
    mag_dia=10.2,
    mag_depth=2.0,
    style="flat",
    shelf_depth=70.0,
    shelf_thickness=None,
    shelf_height=30.0,
    shelf_side="right",
    mag_margin=15.0,
    mag_spacing=None,
    mag_y=None,
):
    """
    Creates a magnetic tool holder.
    
    Supports two styles:
      - 'flat': Magnets embedded on the front face of the baseplate (XY plane).
      - 'perpendicular': A vertical projection ('shelf') extends forward into -Z
        on the side of the holder (default right side) with a full triangular brace
        underneath connecting from the bottom of the baseplate up to the front tip.
        Magnets and 2mm push-holes are embedded on the side face of this projection,
        allowing tools to hang vertically, perpendicular to the wall.
    """
    width = units * UNIT_WIDTH
    
    # Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, mc_solids = create_baseplate(units=units, mount_type=mount_type, num_rows=2)
    
    if style == "flat":
        # Calculate magnet positions on baseplate front face
        mag_pts = []
        if mag_count == 1:
            mag_pts.append((0, -37.0))
        elif mag_count > 1:
            start_y = -17.0
            end_y = -57.0
            step = (end_y - start_y) / (mag_count - 1)
            for i in range(mag_count):
                mag_pts.append((0, start_y + i * step))
        
        if mag_count > 0:
            mags = (
                cq.Workplane("XY").workplane(offset=-BACKPLATE_THICKNESS) # Front face of baseplate
                .pushPoints(mag_pts)
                .circle(mag_dia / 2.0)
                .extrude(mag_depth) # Cut into the block (+Z)
            )
            body = body.cut(mags)
            
            # Push holes: 2mm diameter, all the way through to the back
            push_holes = (
                cq.Workplane("XY").workplane(offset=-BACKPLATE_THICKNESS)
                .pushPoints(mag_pts)
                .circle(2.0 / 2.0)
                .extrude(20.0) # All the way to +Z
            )
            body = body.cut(push_holes)
            
    elif style == "perpendicular":
        if shelf_thickness is None:
            shelf_thickness = max(4.0, 2.0 * mag_depth)
            
        back_z = -BACKPLATE_THICKNESS
        front_z = -BACKPLATE_THICKNESS - shelf_depth
        tip_bottom_y = top_y - shelf_height
        
        # Position the vertical shelf plate (default right side)
        if shelf_side == "right":
            shelf_origin_x = width / 2.0 - shelf_thickness
            extrude_dir = 1
            face_x = shelf_origin_x  # Inner side face
        else:
            shelf_origin_x = -width / 2.0
            extrude_dir = -1
            face_x = -width / 2.0 + shelf_thickness  # Inner side face
            
        # Draw the vertical projection + triangular brace on the YZ plane
        # In cq.Workplane("YZ"): Local X = Global Y, Local Y = Global Z, Normal = +Global X.
        shelf_pts = [
            (top_y, back_z),
            (top_y, front_z),
            (tip_bottom_y, front_z),
            (bottom_y, back_z),
        ]
        
        shelf = (
            cq.Workplane("YZ", origin=(shelf_origin_x, 0, 0))
            .polyline(shelf_pts).close()
            .extrude(shelf_thickness)
        )
        body = body.union(shelf)
        
        # Center the column of magnets on the projection along the Z-axis
        z_center = (back_z + front_z) / 2.0
        
        # Center magnets along the Y-axis according to how deep (top to bottom) the brace is at z_center
        # At z_center (halfway along depth), the brace bottom edge is at:
        y_brace_at_z = (bottom_y + tip_bottom_y) / 2.0
        y_mid = (top_y + y_brace_at_z) / 2.0
        
        spacing = mag_spacing if mag_spacing is not None else max(mag_dia + 6.0, 18.0)
        
        mag_pts = []
        if mag_count == 1:
            mag_pts.append((y_mid, z_center))
        elif mag_count > 1:
            for i in range(mag_count):
                y_pos = y_mid - ((mag_count - 1) / 2.0 - i) * spacing
                mag_pts.append((y_pos, z_center))
                
        if mag_count > 0:
            extrude_depth = extrude_dir * mag_depth
            push_extrude = extrude_dir * (shelf_thickness + 5.0)
            
            mags = (
                cq.Workplane("YZ", origin=(face_x, 0, 0))
                .pushPoints(mag_pts)
                .circle(mag_dia / 2.0)
                .extrude(extrude_depth)
            )
            body = body.cut(mags)
            
            # Push holes: 2mm diameter, all the way through to the opposite face
            push_holes = (
                cq.Workplane("YZ", origin=(face_x, 0, 0))
                .pushPoints(mag_pts)
                .circle(2.0 / 2.0)
                .extrude(push_extrude)
            )
            body = body.cut(push_holes)
    else:
        raise ValueError(f"Unsupported style: {style}. Must be 'flat' or 'perpendicular'.")
    
    # Cut screws
    if screw_pts:
        screws = (
            cq.Workplane("XY").workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6 / 2.0)
            .extrude(-20) 
        )
        body = body.cut(screws)
        
        recesses = (
            cq.Workplane("XY").workplane(offset=-8)
            .pushPoints(screw_pts)
            .circle(8.0 / 2.0) 
            .extrude(-20) 
        )
        body = body.cut(recesses)
        
    if mc_solids:
        for solid in mc_solids:
            body = body.union(cq.Workplane(solid))
            
    return body

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate magnetic tool holder.")
    parser.add_argument("--units", type=int, default=1, help="Number of units wide")
    parser.add_argument("--mount", type=str, default="groove", choices=["groove", "multiconnect", "hybrid"], help="Mount type")
    parser.add_argument("--mag-count", type=int, default=2, help="Number of magnets")
    parser.add_argument("--mag-dia", type=float, default=10.2, help="Diameter of magnet hole (including tolerance)")
    parser.add_argument("--mag-depth", type=float, default=2.0, help="Depth of magnet hole")
    parser.add_argument(
        "--style", "--orientation", 
        dest="style", 
        type=str, 
        default="flat", 
        choices=["flat", "perpendicular"], 
        help="Holder style: flat against wall or perpendicular projection"
    )
    parser.add_argument("--shelf-depth", type=float, default=70.0, help="Depth of perpendicular shelf projection in mm (default 70.0)")
    parser.add_argument("--shelf-thickness", type=float, default=None, help="Thickness of perpendicular shelf plate in mm (default 2x magnet depth)")
    parser.add_argument("--shelf-height", type=float, default=30.0, help="Vertical height of shelf front face before triangular brace in mm (default 30.0)")
    parser.add_argument("--shelf-side", type=str, default="right", choices=["right", "left"], help="Side of tool holder for shelf projection (default right)")
    parser.add_argument("--mag-spacing", type=float, default=None, help="Vertical spacing between magnets in column in mm (default: mag_dia + 6.0)")
    parser.add_argument("--mag-y", type=float, default=None, help="Optional Y-coordinate override for magnets in perpendicular style")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")
    parser.add_argument("--print-orientation", type=str, default=None, choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down", "none"], help="Print orientation for STL export")
    args = parser.parse_args()

    holder = create_magnetic_holder(
        units=args.units, 
        mount_type=args.mount,
        mag_count=args.mag_count,
        mag_dia=args.mag_dia,
        mag_depth=args.mag_depth,
        style=args.style,
        shelf_depth=args.shelf_depth,
        shelf_thickness=args.shelf_thickness,
        shelf_height=args.shelf_height,
        shelf_side=args.shelf_side,
        mag_spacing=args.mag_spacing,
        mag_y=args.mag_y,
    )
    
    if args.style == "perpendicular":
        filename = f"magnetic_saw_holder_perp_{args.units}u_{args.mag_count}Mags_D{args.mag_dia}x{args.mag_depth}_{int(args.shelf_depth)}mm_{args.mount}.stl"
        default_orient = "right_down" if args.shelf_side == "right" else "left_down"
    else:
        filename = f"magnetic_saw_holder_{args.units}u_{args.mag_count}Mags_D{args.mag_dia}x{args.mag_depth}_{args.mount}.stl"
        default_orient = "left_down"
        
    orient = args.print_orientation if args.print_orientation is not None else default_orient
    export_model(holder, filename, category="tool_holders", print_orientation=orient, export=args.export)
