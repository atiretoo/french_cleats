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
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH,
    BACKPLATE_THICKNESS,
    DEFAULT_RAIL_HEIGHT,
    TOP_GROOVE_Y,
    get_bottom_groove_y,
    get_groove_points,
    get_screw_points,
    drill_backplate_screws,
    export_model,
)


def create_hose_holder(
    units=7,
    depth=150.0,
    rail_height=DEFAULT_RAIL_HEIGHT,
    wall_thickness=9.0,
    lip_height=50.0,
    handle_slot_height=20.0,
    handle_slot_width=110.0,
):
    """
    Creates a pure 60-degree swept UNIT system hose and extension cord holder (Option A).
    - units: Width in 28mm UNITs (default: 7U = 196mm)
    - depth: Usable cradle projection depth in mm (default: 150mm for pneumatic air hose)
    - wall_thickness: Structural wall thickness in mm (default: 9.0mm)
    - lip_height: Height of the front retaining lip pointing UPWARDS to retain coils (default: 50.0mm)
    - handle_slot_height: Height of the central handle cutout slot (default: 20.0mm)
    - handle_slot_width: Width of the central handle cutout slot (default: 110.0mm)

    Note: When mounting to shelf edge adapters, use 16 mm long screws so the top screws
    do not protrude and prevent the mount from seating all the way down.
    """
    width = units * UNIT_WIDTH
    backplate_thickness = BACKPLATE_THICKNESS  # 11.0 mm

    # 1. Sweep Geometry
    # 60-degree arc chord length equals outer radius R_outer:
    R_outer = width  # 196.0 mm for 7U
    R_inner = 65.0   # Inner radius giving full engagement with bottom groove
    sweep_angle_deg = 60.0

    # Center of rotation Y0
    # Top groove at Y = 10.0, bottom groove at Y = -84.0
    Y0 = -154.74

    z_back = 0.0
    z_flange = -backplate_thickness
    z_saddle_front = z_flange - depth
    z_lip_front = z_saddle_front - wall_thickness

    # Radial positions of the saddle and lip
    r_saddle = 135.0
    r_saddle_bot = r_saddle - wall_thickness  # 126.0 mm
    r_lip_top = r_saddle + lip_height        # 185.0 mm (rises UPWARDS to retain hose!)

    bottom_groove_y = get_bottom_groove_y(rail_height)
    top_groove_pts = get_groove_points(TOP_GROOVE_Y)
    bot_groove_pts = get_groove_points(bottom_groove_y)
    screw_pts = get_screw_points(units, rail_height)

    lip_mid_r = (r_saddle + r_lip_top) / 2.0
    effective_slot_w = min(handle_slot_width, width - 40.0)

    # 2. Draw smooth 2D cross-section profile on YZ plane, revolve 60 degrees,
    #    center symmetrically, cut grooves, drill mounting screws, and cut handle slot.
    body = (
        cq.Workplane("YZ")
        .moveTo(Y0 + R_inner, z_back)
        .lineTo(Y0 + R_outer, z_back)
        .lineTo(Y0 + R_outer, z_flange)
        # Blend upper back flange into saddle floor:
        .lineTo(Y0 + r_saddle + 20.0, z_flange)
        .threePointArc(
            (Y0 + r_saddle + 5.8, z_flange - 5.8),
            (Y0 + r_saddle, z_flange - 20.0),
        )
        # Along saddle floor to front inside corner:
        .lineTo(Y0 + r_saddle, z_saddle_front + 15.0)
        # Inside corner curving UP into front lip:
        .threePointArc(
            (Y0 + r_saddle + 4.4, z_saddle_front + 4.4),
            (Y0 + r_saddle + 15.0, z_saddle_front),
        )
        # Up inside face of front lip:
        .lineTo(Y0 + r_lip_top - 5.0, z_saddle_front)
        # Rounded top of front lip:
        .threePointArc(
            (Y0 + r_lip_top, (z_saddle_front + z_lip_front) / 2.0),
            (Y0 + r_lip_top - 5.0, z_lip_front),
        )
        # Down outer face of front lip:
        .lineTo(Y0 + r_saddle_bot + 15.0, z_lip_front)
        # Outside corner curving into underside of saddle:
        .threePointArc(
            (Y0 + r_saddle_bot + 4.4, z_lip_front + 4.4),
            (Y0 + r_saddle_bot, z_lip_front + 15.0),
        )
        # Along underside of saddle to back gusset:
        .lineTo(Y0 + r_saddle_bot, z_flange - 25.0)
        # Gusset blend into lower back flange:
        .threePointArc(
            (Y0 + r_saddle_bot - 7.3, z_flange - 7.3),
            (Y0 + r_saddle_bot - 25.0, z_flange),
        )
        # Down lower back flange:
        .lineTo(Y0 + R_inner, z_flange)
        .close()
        .revolve(sweep_angle_deg, (Y0, 0), (Y0, 1))
        .rotate((0, Y0, 0), (0, Y0, 1), -30.0)
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .tag("back_wp")
        .end(2)
        # Cut standard UNIT shallow 45-degree grooves into the flat back at Z = 0
        .copyWorkplane(cq.Workplane("YZ", origin=(width / 2.0 + 10.0, 0, 0)))
        .polyline(top_groove_pts)
        .close()
        .polyline(bot_groove_pts)
        .close()
        .cutBlind(-(width + 20.0))
        # Central handle slot in the front lip
        .copyWorkplane(cq.Workplane("XY", origin=(0, Y0 + lip_mid_r, z_lip_front - 5.0)))
        .slot2D(effective_slot_w, handle_slot_height)
        .cutBlind(wall_thickness + 10.0)
    )

    if screw_pts:
        body = drill_backplate_screws(body, screw_pts, cbore_depth=10.0)

    return body


def orient_for_printing(model, orientation="side_down"):
    """
    Applies rotation to place the part in the optimal print orientation.
    'side_down':
      Places the planar 60-degree cut end face flat on the build plate (Z=0).
      Continuous extrusion perimeters run around the bracket on every layer,
      giving maximum tensile strength along the cantilever arm with zero supports.
    'back_down':
      Places the flat backplate on the print bed.
    """
    if orientation == "side_down":
        rot = model.rotate((0, 0, 0), (0, 0, 1), 30.0).rotate((0, 0, 0), (0, 1, 0), 90.0)
        bb = rot.val().BoundingBox()
        dx = -(bb.xmin + bb.xmax) / 2.0
        dy = -(bb.ymin + bb.ymax) / 2.0
        dz = -bb.zmin
        return rot.translate((dx, dy, dz))
    elif orientation == "back_down":
        rot = model.rotate((0, 0, 0), (1, 0, 0), 180.0)
        bb = rot.val().BoundingBox()
        dx = -(bb.xmin + bb.xmax) / 2.0
        dy = -(bb.ymin + bb.ymax) / 2.0
        dz = -bb.zmin
        return rot.translate((dx, dy, dz))
    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate UNIT Hose / Extension Cord Holder (Option A)")
    parser.add_argument("--units", type=int, default=7, help="Width in 28mm UNITs (default: 7)")
    parser.add_argument("--depth", type=float, default=150.0, help="Usable cradle depth in mm (default: 150.0)")
    parser.add_argument("--rail-height", type=float, default=DEFAULT_RAIL_HEIGHT, help="Cleat rail height in mm (default: 73.0)")
    parser.add_argument("--lip-height", type=float, default=50.0, help="Front retaining lip height in mm (default: 50.0)")
    parser.add_argument("--export", type=str, default="both", choices=["both", "stl", "step"], help="Export format (default: both)")
    parser.add_argument(
        "--print-orientation",
        type=str,
        default="side_down",
        choices=["side_down", "back_down", "none"],
        help="Print orientation for STL export (default: side_down)",
    )

    args = parser.parse_args()

    cad_model = create_hose_holder(
        units=args.units,
        depth=args.depth,
        rail_height=args.rail_height,
        lip_height=args.lip_height,
    )
    print_model = orient_for_printing(cad_model, args.print_orientation)

    filename = f"hose_holder_{args.units}u_D{int(args.depth)}.stl"
    export_model(
        print_model,
        filename,
        category="tool_holders",
        print_orientation="none",
        export=args.export,
        step_shape=cad_model,
    )
