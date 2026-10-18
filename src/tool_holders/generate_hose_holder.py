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
    BACKPLATE_THICKNESS,
    DEFAULT_RAIL_HEIGHT,
    TOP_GROOVE_Y,
    get_bottom_groove_y,
    GROOVE_DEPTH,
    GROOVE_SURFACE_HALF_WIDTH,
    GROOVE_BOTTOM_HALF_WIDTH,
    get_main_repo_root,
)


def create_hose_holder(
    units=7,
    depth=150.0,
    rail_height=DEFAULT_RAIL_HEIGHT,
    mount_type="groove",
    wall_thickness=9.0,
    lip_height=50.0,
    handle_slot_height=20.0,
    handle_slot_width=110.0,
):
    """
    Creates a pure 60-degree swept UNIT system hose and extension cord holder (Option A).
    - units: Width in 28mm UNITs (default: 7U = 196mm)
    - depth: Usable cradle projection depth in mm (default: 150mm for pneumatic air hose)
    - mount_type: 'groove' standard UNIT mounting interface
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

    top_groove_pts = [
        (TOP_GROOVE_Y + GROOVE_SURFACE_HALF_WIDTH, 1.0),
        (TOP_GROOVE_Y + GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
        (TOP_GROOVE_Y - GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
        (TOP_GROOVE_Y - GROOVE_SURFACE_HALF_WIDTH, 1.0),
    ]
    bot_groove_pts = [
        (bottom_groove_y + GROOVE_SURFACE_HALF_WIDTH, 1.0),
        (bottom_groove_y + GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
        (bottom_groove_y - GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
        (bottom_groove_y - GROOVE_SURFACE_HALF_WIDTH, 1.0),
    ]

    screw_pts = [
        (-width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH, y)
        for i in range(units)
        for y in (TOP_GROOVE_Y, bottom_groove_y)
    ]

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
        # Cut standard UNIT shallow 45-degree grooves into the flat back at Z = 0
        .copyWorkplane(cq.Workplane("YZ", origin=(width / 2.0 + 10.0, 0, 0)))
        .polyline(top_groove_pts)
        .close()
        .polyline(bot_groove_pts)
        .close()
        .cutBlind(-(width + 20.0))
        # Drill standard UNIT screw holes and counterbores
        .copyWorkplane(cq.Workplane("XY", origin=(0, 0, 1.0)))
        .pushPoints(screw_pts)
        .hole(3.6, backplate_thickness + 2.0)
        .copyWorkplane(cq.Workplane("XY", origin=(0, 0, -backplate_thickness + 4.0)))
        .pushPoints(screw_pts)
        .hole(8.0, 10.0)
        # Central handle slot in the front lip
        .copyWorkplane(cq.Workplane("XY", origin=(0, Y0 + lip_mid_r, z_lip_front - 5.0)))
        .slot2D(effective_slot_w, handle_slot_height)
        .cutBlind(wall_thickness + 10.0)
    )

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
        # Rotate so the +X 60-degree flat end face lies on the XY bed at Z=0
        # Normal is (cos(-30), sin(-30), 0) = (0.866, -0.500, 0).
        # Rotate around Z by +30 deg to align normal with +X:
        rot = model.rotate((0, 0, 0), (0, 0, 1), 30.0)
        # Rotate around Y by +90 deg to align normal with -Z (pointing down onto bed):
        rot = rot.rotate((0, 0, 0), (0, 1, 0), 90.0)
        bb = rot.val().BoundingBox()
        # Drop flat face exactly to Z=0 and center on the build plate:
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
    parser.add_argument("--mount", type=str, default="groove", choices=["groove"], help="Mount type (default: groove)")
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

    holder = create_hose_holder(
        units=args.units,
        depth=args.depth,
        rail_height=args.rail_height,
        mount_type=args.mount,
        lip_height=args.lip_height,
    )

    # CAD model in User Space (as mounted)
    cad_model = holder

    # Export
    current_dir = os.path.dirname(__file__)
    main_repo_root = get_main_repo_root(current_dir)
    export_dir_stl = os.path.join(main_repo_root, "exports", "stl", "tool_holders")
    export_dir_step = os.path.join(main_repo_root, "exports", "step", "tool_holders")
    os.makedirs(export_dir_stl, exist_ok=True)
    os.makedirs(export_dir_step, exist_ok=True)

    filename_base = f"hose_holder_{args.units}u_D{int(args.depth)}_{args.mount}"
    out_stl = os.path.join(export_dir_stl, f"{filename_base}.stl")
    out_step = os.path.join(export_dir_step, f"{filename_base}.step")

    # STEP export always in User Space (as mounted)
    if args.export in ["both", "step"]:
        cq.exporters.export(cad_model, out_step)
        print(f"Exported {out_step}")

    # STL export rotated for printing
    if args.export in ["both", "stl"]:
        print_model = orient_for_printing(cad_model, args.print_orientation)
        cq.exporters.export(print_model, out_stl)
        print(f"Exported {out_stl} (orientation: {args.print_orientation})")
