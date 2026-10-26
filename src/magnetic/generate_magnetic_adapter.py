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
    BACKPLATE_TOP_Y,
    TOP_RIDGE_Y,
    RIDGE_HEIGHT,
    RIDGE_SURFACE_HALF_WIDTH,
    RIDGE_PEAK_HALF_WIDTH,
    DEFAULT_RAIL_HEIGHT,
    RAIL_PLAY,
    NUT_SLOT_TOLERANCE,
    get_bottom_groove_y,
    get_bottom_edge_y,
    create_nut_slot,
    export_model,
)


def create_magnetic_adapter(
    units=2,
    rail_height=DEFAULT_RAIL_HEIGHT,
    screw_m="M3",
    plate_thickness=6.0,
    mag_dia=19.2,
    mag_depth=2.0,
    mag_count=1,
    mag_y=None,
    no_screws=False,
):
    """
    Creates a magnetic mount adapter that attaches to a steel surface (such as a
    whiteboard, tool cabinet, or machine tool) via disc magnets on the back, and
    provides standard UNIT shallow ridges on the front to seat into tool holder grooves.

    Reference Frame:
      - Top: +Y
      - Bottom: -Y
      - Front: -Z (standard 45° locking ridges seat into tool holder grooves)
      - Back: +Z (flush face resting against magnetic whiteboard, containing magnet pockets)
      - Left: -X
      - Right: +X

    Features:
      - 1 19.2 mm x 2.0 mm disc magnet pocket per unit (matching thin tool holder dimensions).
      - 2.0 mm through push-holes extending to the front face for easy magnet release.
      - Dual standard shallow locking ridges (top at Y=10.0, bottom at Y=-84.0)
        with 0.20 mm side clearance and 0.80 mm crest clearance.
      - Metric captive nut slots and clearance holes for M3 clamping bolts.
      - 2.0 mm chamfered outer back edges for flush contact against flat steel surfaces.
    """
    width = units * UNIT_WIDTH

    top_screw_y = TOP_RIDGE_Y
    bottom_screw_y = get_bottom_groove_y(rail_height, RAIL_PLAY)
    top_y = BACKPLATE_TOP_Y
    bottom_y = get_bottom_edge_y(rail_height, RAIL_PLAY)
    height = top_y - bottom_y

    # 1. Base Plate: spans Z=0 (front) to Z=plate_thickness (back)
    adapter = (
        cq.Workplane("XY")
        .box(width, height, plate_thickness)
        .translate((0, (top_y + bottom_y) / 2.0, plate_thickness / 2.0))
    )

    # 2. Standard Locking Ridges on Z=0 face (protruding into -Z by RIDGE_HEIGHT = 2.2 mm)
    top_pts = [
        (top_screw_y + RIDGE_SURFACE_HALF_WIDTH, 0),
        (top_screw_y + RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (top_screw_y - RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (top_screw_y - RIDGE_SURFACE_HALF_WIDTH, 0),
    ]
    top_ridge = (
        cq.Workplane("YZ")
        .polyline(top_pts)
        .close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )
    adapter = adapter.union(top_ridge)

    bot_pts = [
        (bottom_screw_y + RIDGE_SURFACE_HALF_WIDTH, 0),
        (bottom_screw_y + RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (bottom_screw_y - RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (bottom_screw_y - RIDGE_SURFACE_HALF_WIDTH, 0),
    ]
    bot_ridge = (
        cq.Workplane("YZ")
        .polyline(bot_pts)
        .close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )
    adapter = adapter.union(bot_ridge)

    # 3. Outer Back Edge Chamfers (on >Z face at Z=plate_thickness)
    try:
        outer_edges = []
        for e in adapter.edges(">Z").vals():
            c = e.Center()
            if (
                abs(c.x) > (width / 2.0 - 0.1)
                or c.y > (top_y - 0.1)
                or c.y < (bottom_y + 0.1)
            ):
                outer_edges.append(e)
        if outer_edges:
            adapter = adapter.newObject(outer_edges).chamfer(2.0)
    except Exception:
        pass

    # 4. Magnet Pockets & Push Holes (on back face Z=plate_thickness, cutting into -Z)
    mag_pts = []
    for i in range(units):
        x = -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH
        if mag_y is not None:
            mag_pts.append((x, mag_y))
        elif mag_count == 1:
            # Centered between top and bottom ridges: (10.0 + (-84.0)) / 2 = -37.0
            mid_y = (top_screw_y + bottom_screw_y) / 2.0
            mag_pts.append((x, mid_y))
        else:
            # Two magnets per unit: matches perpendicular saw holder pattern
            mag_pts.append((x, -17.0))
            mag_pts.append((x, -57.0))

    if mag_pts and mag_dia > 0 and mag_depth > 0:
        # Pockets cut from Z=plate_thickness towards front (-Z)
        mags = (
            cq.Workplane("XY")
            .workplane(offset=plate_thickness)
            .pushPoints(mag_pts)
            .circle(mag_dia / 2.0)
            .extrude(-mag_depth)
        )
        adapter = adapter.cut(mags)

        # 2.0 mm push-through holes to front face
        push_holes = (
            cq.Workplane("XY")
            .workplane(offset=plate_thickness)
            .pushPoints(mag_pts)
            .circle(2.0 / 2.0)
            .extrude(-plate_thickness - 2.0)
        )
        adapter = adapter.cut(push_holes)

    # 5. Captive Nut Slots & Screw Clearance Holes
    if not no_screws and screw_m.lower() != "none":
        if screw_m == "M3":
            screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
        elif screw_m == "M4":
            screw_d, nut_waf, nut_thick = 4.5, 7.0, 3.2
        elif screw_m == "M5":
            screw_d, nut_waf, nut_thick = 5.5, 8.0, 4.0
        else:
            raise ValueError(f"Unsupported screw size: {screw_m}")

        slot_t = nut_thick + NUT_SLOT_TOLERANCE
        slot_z_center = 2.0 + slot_t / 2.0
        screw_hole_len = 10.0 + plate_thickness + 2.0

        for i in range(units):
            x = -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH

            # Top screw clearance hole
            hole_top = (
                cq.Workplane("XY")
                .workplane(offset=-10)
                .center(x, top_screw_y)
                .circle(screw_d / 2.0)
                .extrude(screw_hole_len)
            )
            adapter = adapter.cut(hole_top)

            # Top captive nut slot (slides in from +Y top edge)
            depth_top = top_y - top_screw_y
            slot_top_solid = create_nut_slot(
                screw_m, depth=depth_top, push_hole=True, push_hole_angle=30.0
            )
            slot_top_solid = slot_top_solid.translate(
                cq.Vector(x, top_screw_y, slot_z_center)
            )
            adapter = adapter.cut(cq.Workplane(slot_top_solid))

            # Bottom screw clearance hole
            hole_bot = (
                cq.Workplane("XY")
                .workplane(offset=-10)
                .center(x, bottom_screw_y)
                .circle(screw_d / 2.0)
                .extrude(screw_hole_len)
            )
            adapter = adapter.cut(hole_bot)

            # Bottom captive nut slot (slides in from -Y bottom edge)
            depth_bot = bottom_screw_y - bottom_y
            slot_bot_solid = create_nut_slot(
                screw_m, depth=depth_bot, push_hole=True, push_hole_angle=30.0
            )
            slot_bot_solid = (
                cq.Workplane(slot_bot_solid)
                .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180)
                .val()
            )
            slot_bot_solid = slot_bot_solid.translate(
                cq.Vector(x, bottom_screw_y, slot_z_center)
            )
            adapter = adapter.cut(cq.Workplane(slot_bot_solid))

    return adapter


def main():
    parser = argparse.ArgumentParser(
        description="Generate Magnetic Mount Adapter for UNIT groove tool holders"
    )
    parser.add_argument(
        "--units", type=int, default=2, help="Number of 28mm units wide (default: 2)"
    )
    parser.add_argument(
        "--rail-height",
        type=float,
        default=DEFAULT_RAIL_HEIGHT,
        help="Standard cleat rail height in mm (default: 73.0)",
    )
    parser.add_argument(
        "--screw",
        type=str,
        default="M3",
        choices=["M3", "M4", "M5", "none"],
        help="Clamping screw size (default: M3)",
    )
    parser.add_argument(
        "--plate-thickness",
        type=float,
        default=6.0,
        help="Backplate thickness in mm (default: 6.0)",
    )
    parser.add_argument(
        "--mag-dia",
        type=float,
        default=19.2,
        help="Diameter of disc magnet pocket in mm (default: 19.2 for 19mm disc)",
    )
    parser.add_argument(
        "--mag-depth",
        type=float,
        default=2.0,
        help="Depth of disc magnet pocket in mm (default: 2.0)",
    )
    parser.add_argument(
        "--mag-count",
        type=int,
        default=1,
        help="Number of disc magnets per unit (default: 1)",
    )
    parser.add_argument(
        "--mag-y",
        type=float,
        default=None,
        help="Optional Y-coordinate override for magnet center",
    )
    parser.add_argument(
        "--no-screws",
        action="store_true",
        help="Omit screw holes and nut slots",
    )
    parser.add_argument(
        "--export",
        choices=["both", "stl", "step"],
        default="both",
        help="Export format (default: both)",
    )
    parser.add_argument(
        "--print-orientation",
        type=str,
        default="back_down",
        choices=["back_down", "face_down", "left_down", "right_down", "top_down", "bottom_down", "none"],
        help="Print orientation for STL export (default: back_down)",
    )

    args = parser.parse_args()

    adapter = create_magnetic_adapter(
        units=args.units,
        rail_height=args.rail_height,
        screw_m=args.screw,
        plate_thickness=args.plate_thickness,
        mag_dia=args.mag_dia,
        mag_depth=args.mag_depth,
        mag_count=args.mag_count,
        mag_y=args.mag_y,
        no_screws=args.no_screws,
    )

    filename = f"magnetic_adapter_{args.units}u_H{int(args.rail_height)}_{args.screw}.stl"
    export_model(
        adapter,
        filename,
        category="magnetic",
        print_orientation=args.print_orientation,
        export=args.export,
    )


if __name__ == "__main__":
    main()
