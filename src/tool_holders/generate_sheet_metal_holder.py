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

def create_sheet_metal_holder(
    units=1,
    shelf_thickness=4.0,
    shelf_side="right",
    metal_width=25.0,
    pocket_floor_width=26.0,
    metal_length=None,
    vert_depth=0.25,
    pocket_depth=1.25,
    v_width=None,
    clearance=0.0,
    lead_in=0.8,
    back_clearance=9.0,
    front_overhang=5.0,
    rim_thickness=1.0,
    bottom_retention=1.0,
    lip_cutout_width=None,
    fillet_radius=4.0,
):
    """
    Creates a French Cleat tool holder designed to capture a strip of ferromagnetic
    sheet metal (e.g. 26 gauge steel, ~0.6 mm actual thickness) behind 45-degree V-groove retaining lips.

    The metal strip is inserted vertically from the top opening (Y = top_y), with its
    bottom edge cut at a 45-degree angle.

    Key Features:
      - 26 mm pocket floor width with a 0.25 mm vertical section at the bottom,
        leaving 0.3 mm clearance at the top edge of a 0.6 mm thick 25 mm sheet metal strip.
      - 45-degree inward retaining lips from depth 0.25 mm to 1.25 mm (0.5 mm overhang per side at face).
      - Projection extends all the way to the bottom of the tool holder (bottom_y),
        with the 45-degree bottom edge starting right at the bottom edge of the backplate
        and sloping up from there to maximize sheet metal strip holding area.
      - Pocket goes all the way to the bottom edge of the projecting brace with a 1.0 mm rim.
      - Shortened retention tabs at the 45-degree bottom edge: only 1.0 mm at each corner,
        leaving the middle 24 mm completely open for flush tool seating and easy ejection.
      - 4.0 mm structural fillet along the backplate junction.
      - 100% support-free printing in side-down orientation (right_down).
    """
    width = units * UNIT_WIDTH

    if v_width is None:
        v_width = pocket_depth - vert_depth

    # 1. Baseplate
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        units=units, mount_type="groove", num_rows=2
    )

    back_z = -BACKPLATE_THICKNESS # -11.0

    # 2. Position the vertical projection
    # Default right side (-width / 2.0) matches standard tool holder orientation
    if shelf_side == "right":
        shelf_offset_x = -width
        shelf_thickness_extrude = shelf_thickness
        cut_dir = -1
        face_x = -width / 2.0 + shelf_thickness  # Inner side face
    else:
        shelf_offset_x = 0.0
        shelf_thickness_extrude = -shelf_thickness
        cut_dir = 1
        face_x = width / 2.0 - shelf_thickness  # Inner side face

    # 3. Z Bounds of pocket and trimmed shelf projection
    # Rear edge of pocket is back_clearance (9 mm) in front of the backplate
    effective_pocket_width = pocket_floor_width if pocket_floor_width is not None else (metal_width + clearance)
    z_rear = back_z - back_clearance
    z_front = z_rear - effective_pocket_width
    # Trim projection so there is exactly front_overhang (5 mm) beyond front edge of pocket
    front_z = z_front - front_overhang

    # 4. Y Bounds of pocket and 45-degree projecting brace
    # The retaining rim below the pocket bottom is a couple perimeters thick (1.0 mm perpendicular)
    rim_y = rim_thickness * 1.41421356

    # If metal_length is None, the 45-degree edge starts right at the bottom of the tool holder (bottom_y)
    if metal_length is None:
        brace_bottom_back = bottom_y
    else:
        # User explicitly specified metal strip length at rear edge
        y_bot_rear_target = top_y - metal_length
        brace_bottom_back = y_bot_rear_target + (z_rear - back_z) - rim_y

    # The bottom edge of the projecting brace slopes up at 45 degrees towards the front tip
    brace_bottom_front = brace_bottom_back - (front_z - back_z)

    # Pocket bottom is exactly parallel to the brace bottom, offset upward by rim_y
    y_bot_rear = brace_bottom_back - (z_rear - back_z) + rim_y
    y_bot_front = brace_bottom_back - (z_front - back_z) + rim_y

    shelf_pts = [
        (top_y, back_z),
        (top_y, front_z),
        (brace_bottom_front, front_z),
        (brace_bottom_back, back_z),
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
        .workplane(offset=shelf_offset_x)
        .polyline(shelf_pts)
        .close()
        .extrude(shelf_thickness_extrude)
    )

    # 5. Add structural fillet between backplate and projection
    if fillet_radius and fillet_radius > 0:
        body = (
            body
            .faces("+X or -X")
            .faces("not >X")
            .faces("not <X")
            .edges(">Z")
            .fillet(fillet_radius)
        )

    # 6. Cut Sheet Metal Pocket with 0.25 mm vertical section and 45-degree V-groove lips
    y_top_open = top_y + 2.0
    y_leadin_end = top_y - 2.0
    x_floor = face_x + cut_dir * pocket_depth
    floor_offset_x = x_floor - width / 2.0

    pts_floor = [
        (y_top_open, z_front - lead_in),
        (y_leadin_end, z_front),
        (y_bot_front, z_front),
        (y_bot_rear, z_rear),
        (y_leadin_end, z_rear),
        (y_top_open, z_rear + lead_in),
    ]

    sqrt2 = 1.41421356
    y_face_front = y_bot_front + v_width * (sqrt2 - 1.0)
    y_face_rear = y_bot_rear + v_width * (sqrt2 + 1.0)

    pts_face = [
        (y_top_open, z_front + v_width - lead_in),
        (y_leadin_end, z_front + v_width),
        (y_face_front, z_front + v_width),
        (y_face_rear, z_rear - v_width),
        (y_leadin_end, z_rear - v_width),
        (y_top_open, z_rear - v_width + lead_in),
    ]

    offset_floor_to_vert = -cut_dir * vert_depth
    offset_vert_to_face = -cut_dir * (pocket_depth - vert_depth)
    offset_face_to_out = -cut_dir * 1.0

    body = (
        body
        .workplaneFromTagged("right_wp")
        .workplane(offset=floor_offset_x)
        .polyline(pts_floor)
        .close()
        .workplane(offset=offset_floor_to_vert)
        .polyline(pts_floor)
        .close()
        .workplane(offset=offset_vert_to_face)
        .polyline(pts_face)
        .close()
        .workplane(offset=offset_face_to_out)
        .polyline(pts_face)
        .close()
        .loft(ruled=True, combine="cut")
    )

    # 7. Cutout of the bottom retaining lip
    # Leaves bottom_retention (1.0 mm) at each corner along the 45-degree edge
    if bottom_retention is not None:
        z_cut_start = z_front + bottom_retention
        z_cut_end = z_rear - bottom_retention
    elif lip_cutout_width and lip_cutout_width > 0:
        z_cut_start = z_front + 5.0
        z_cut_end = z_cut_start + lip_cutout_width
    else:
        z_cut_start = None

    if z_cut_start is not None and z_cut_end > z_cut_start:
        y_pocket_start = y_bot_front - (z_cut_start - z_front)
        y_pocket_end = y_bot_front - (z_cut_end - z_front)

        y_cut_start_top = y_pocket_start + v_width * sqrt2 + 1.0
        y_cut_end_top = y_pocket_end + v_width * sqrt2 + 1.0

        cutout_poly = [
            (y_cut_start_top, z_cut_start),
            (y_cut_end_top, z_cut_end),
            (y_cut_end_top - 25.0, z_cut_end),
            (y_cut_start_top - 25.0, z_cut_start),
        ]

        body = (
            body
            .workplaneFromTagged("right_wp")
            .workplane(offset=floor_offset_x)
            .polyline(cutout_poly)
            .close()
            .cutBlind(-cut_dir * (pocket_depth + 2.0))
        )

    # 8. Screw holes and recesses
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate French Cleat tool holder with top slide-in 45-degree V-grooves for 26 gauge sheet metal."
    )
    parser.add_argument("--units", type=int, default=1, help="Number of units wide (default: 1)")
    parser.add_argument("--shelf-thickness", type=float, default=4.0, help="Thickness of perpendicular shelf plate in mm (default: 4.0)")
    parser.add_argument("--shelf-side", type=str, default="right", choices=["right", "left"], help="Side of tool holder for shelf projection (default: right)")
    parser.add_argument("--metal-width", type=float, default=25.0, help="Nominal width of sheet metal strip in mm (default: 25.0)")
    parser.add_argument("--pocket-floor-width", type=float, default=26.0, help="Width of pocket at the bottom/floor in mm (default: 26.0)")
    parser.add_argument("--metal-length", type=float, default=None, help="Rear length of sheet metal strip in mm (default: extends full length to bottom of tool holder)")
    parser.add_argument("--pocket-depth", type=float, default=1.25, help="Total depth of sheet metal pocket in mm (default: 1.25)")
    parser.add_argument("--vert-depth", type=float, default=0.25, help="Depth of vertical section at bottom of pocket in mm (default: 0.25)")
    parser.add_argument("--v-width", type=float, default=None, help="Width of 45-degree retaining lip in mm (default: pocket_depth - vert_depth)")
    parser.add_argument("--clearance", type=float, default=0.0, help="Width clearance for sliding sheet metal in mm (default: 0.0)")
    parser.add_argument("--lead-in", type=float, default=0.8, help="Top entry lead-in flare in mm (default: 0.8)")
    parser.add_argument("--back-clearance", type=float, default=9.0, help="Clearance between backplate and rear edge of pocket in mm (default: 9.0)")
    parser.add_argument("--front-overhang", type=float, default=5.0, help="Shelf overhang beyond front edge of pocket in mm (default: 5.0)")
    parser.add_argument("--rim-thickness", type=float, default=1.0, help="Thickness of retaining edge at bottom of pocket in mm (default: 1.0)")
    parser.add_argument("--bottom-retention", type=float, default=1.0, help="Length of retention tabs at corners of 45-degree bottom edge in mm (default: 1.0)")
    parser.add_argument("--fillet-radius", type=float, default=4.0, help="Radius of structural fillet between backplate and projection in mm (default: 4.0)")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")
    parser.add_argument(
        "--print-orientation",
        type=str,
        default=None,
        choices=["left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down", "none"],
        help="Print orientation for STL export (default: right_down for right shelf, left_down for left shelf)"
    )
    args = parser.parse_args()

    holder = create_sheet_metal_holder(
        units=args.units,
        shelf_thickness=args.shelf_thickness,
        shelf_side=args.shelf_side,
        metal_width=args.metal_width,
        pocket_floor_width=args.pocket_floor_width,
        metal_length=args.metal_length,
        vert_depth=args.vert_depth,
        pocket_depth=args.pocket_depth,
        v_width=args.v_width,
        clearance=args.clearance,
        lead_in=args.lead_in,
        back_clearance=args.back_clearance,
        front_overhang=args.front_overhang,
        rim_thickness=args.rim_thickness,
        bottom_retention=args.bottom_retention,
        fillet_radius=args.fillet_radius,
    )

    v_w = (args.pocket_depth - args.vert_depth) if args.v_width is None else args.v_width
    side_suffix = "_left" if args.shelf_side == "left" else ""
    filename = (
        f"sheet_metal_tool_holder_{args.units}u_"
        f"{int(args.metal_width)}mm_top_insert_"
        f"D{args.pocket_depth:.2f}xV{v_w:.1f}{side_suffix}_groove.stl"
    )

    # In default right_down print orientation, the outer face of the projection rests flat on the print bed
    # and the inner face with the pocket points straight upward (+Z in print coordinates) for support-free printing.
    default_orient = "right_down" if args.shelf_side == "right" else "left_down"
    orient = args.print_orientation if args.print_orientation is not None else default_orient

    export_model(holder, filename, category="tool_holders", print_orientation=orient, export=args.export)
