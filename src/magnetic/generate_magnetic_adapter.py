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
import math

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
    support_fin,
    add_compliant_magnet_pocket,
    LARGE_MAGNET_DIA,
    LARGE_MAGNET_THICK,
    MAGNET_RADIAL_CLEARANCE,
    MAGNET_WALL_THICKNESS,
    MAGNET_SLIT_WIDTH,
)


def compute_magnet_layout(
    rail_height=DEFAULT_RAIL_HEIGHT,
    mag_dia=LARGE_MAGNET_DIA,
    mag_count=None,
    mag_y=None,
    no_screws=False,
    screw_m="M3",
):
    """
    Computes the optimal vertical layout (Y-coordinates) for disc magnets on the mount
    to fit the maximum number of magnets into the specified rail height while maintaining
    clean clearances with captive nut slots and screw clearance holes.

    Returns:
        (count_per_unit, y_positions_list)
    """
    if mag_y is not None:
        return 1, [mag_y]

    top_screw_y = TOP_RIDGE_Y
    bottom_screw_y = get_bottom_groove_y(rail_height, RAIL_PLAY)
    top_y = BACKPLATE_TOP_Y
    bottom_y = get_bottom_edge_y(rail_height, RAIL_PLAY)
    mid_y = (top_screw_y + bottom_screw_y) / 2.0

    r_pocket = (mag_dia / 2.0) + MAGNET_RADIAL_CLEARANCE
    r_slit_out = r_pocket + MAGNET_WALL_THICKNESS + MAGNET_SLIT_WIDTH
    d_slit = 2.0 * r_slit_out

    if no_screws or screw_m.lower() == "none":
        margin = 4.0
        y_max = top_y - margin - r_slit_out
        y_min = bottom_y + margin + r_slit_out
    else:
        nut_waf = 5.5 if screw_m == "M3" else (7.0 if screw_m == "M4" else 8.0)
        nut_point_dist = (nut_waf / 2.0) / math.cos(math.radians(30))
        margin = 4.0
        y_max = (top_screw_y - nut_point_dist) - r_slit_out - margin
        y_min = (bottom_screw_y + nut_point_dist) + r_slit_out + margin

    available_span = y_max - y_min
    min_web = 3.0
    min_pitch = d_slit + min_web

    if mag_count is None:
        if available_span < 0:
            count = 1
        else:
            count = 1 + int(math.floor(available_span / min_pitch))
    else:
        count = mag_count

    if count <= 1:
        return 1, [mid_y]
    else:
        max_spacing = available_span / (count - 1)
        spacing = min(max_spacing, d_slit + 5.0)
        start_y = mid_y + (count - 1) * spacing / 2.0
        return count, [start_y - k * spacing for k in range(count)]


def create_magnetic_adapter(
    units=2,
    rail_height=DEFAULT_RAIL_HEIGHT,
    screw_m="M3",
    plate_thickness=6.0,
    mag_dia=LARGE_MAGNET_DIA,
    mag_depth=LARGE_MAGNET_THICK,
    mag_count=None,
    mag_y=None,
    no_screws=False,
    print_orientation="none",
    support_fins=True,
    fin_z_gap=0.10,
):
    """
    Creates a magnetic mount adapter that attaches to a steel surface (such as a
    whiteboard, tool cabinet, or machine tool) via disc magnets on the back, and
    provides standard UNIT shallow ridges on the front to seat into tool holder grooves.

    Reference Frame (unrotated CAD):
      - Top: +Y
      - Bottom: -Y
      - Front: -Z (standard 45° locking ridges seat into tool holder grooves)
      - Back: +Z (flush face resting against magnetic whiteboard, containing magnet pockets)
      - Left: -X
      - Right: +X

    Features:
      - Compliant slit-snap disc magnet pockets (default 19.25 mm x 1.60 mm standard large disc)
        with 3-arc flexure, 45° retaining bumps, and central push-out hole for easy removal.
      - Maximized magnet packing strategy: automatically fits the maximum number of magnets
        for the given rail height (e.g. 3 magnets per 1U space = 6 magnets for 2U at 73mm rail).
      - Dual standard shallow locking ridges (top at Y=10.0, bottom at Y=-84.0)
        with 0.20 mm side clearance and 0.80 mm crest clearance.
      - Metric captive nut slots and clearance holes for M3 clamping bolts.
      - 2.0 mm chamfered outer back edges for flush contact against flat steel surfaces.
      - 45-degree print orientation support: chamfers the long back edge to sit flat
        on the build plate and adds 2 support fins under the back face (side without ridges).
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

    # 3. Outer Edge Chamfers on Ridge Side (Z=0 face) matching tool holder backplates
    # Long right edge (X = +width/2)
    cut_pts_r = [
        (width / 2.0 - 2.0 - RIDGE_HEIGHT - 1.0, -RIDGE_HEIGHT - 1.0),
        (width / 2.0 + 10.0, -RIDGE_HEIGHT - 1.0),
        (width / 2.0 + 10.0, 10.0),
        (width / 2.0, 2.0),
    ]
    cutter_r = (
        cq.Workplane("XZ")
        .polyline(cut_pts_r).close()
        .extrude(height + 100.0, both=True)
        .translate((0, (top_y + bottom_y) / 2.0, 0))
    )
    adapter = adapter.cut(cutter_r)

    # Long left edge (X = -width/2)
    cut_pts_l = [
        (-width / 2.0 + 2.0 + RIDGE_HEIGHT + 1.0, -RIDGE_HEIGHT - 1.0),
        (-width / 2.0 - 10.0, -RIDGE_HEIGHT - 1.0),
        (-width / 2.0 - 10.0, 10.0),
        (-width / 2.0, 2.0),
    ]
    cutter_l = (
        cq.Workplane("XZ")
        .polyline(cut_pts_l).close()
        .extrude(height + 100.0, both=True)
        .translate((0, (top_y + bottom_y) / 2.0, 0))
    )
    adapter = adapter.cut(cutter_l)

    # Top edge (Y = top_y)
    cut_pts_top = [
        (top_y - 2.0, 0.0),
        (top_y + 10.0, 0.0),
        (top_y + 10.0, 10.0),
        (top_y, 2.0),
    ]
    cutter_top = cq.Workplane("YZ").polyline(cut_pts_top).close().extrude(width + 100.0, both=True)
    adapter = adapter.cut(cutter_top)

    # Bottom edge (Y = bottom_y)
    cut_pts_bot = [
        (bottom_y + 2.0, 0.0),
        (bottom_y - 10.0, 0.0),
        (bottom_y - 10.0, 10.0),
        (bottom_y, 2.0),
    ]
    cutter_bot = cq.Workplane("YZ").polyline(cut_pts_bot).close().extrude(width + 100.0, both=True)
    adapter = adapter.cut(cutter_bot)

    # Outer Back Edge Chamfers (on >Z face at Z=plate_thickness)
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

    # 4. Compliant Magnet Retention Pockets (MultiConnect-style slit-snap on back face Z=plate_thickness)
    if mag_dia > 0 and mag_depth > 0:
        count_per_unit, mag_ys = compute_magnet_layout(
            rail_height=rail_height,
            mag_dia=mag_dia,
            mag_count=mag_count,
            mag_y=mag_y,
            no_screws=no_screws,
            screw_m=screw_m,
        )

        for i in range(units):
            x = -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH
            for y in mag_ys:
                adapter = add_compliant_magnet_pocket(
                    adapter,
                    center_pt=(x, y),
                    face_z=plate_thickness,
                    mag_dia=mag_dia,
                    mag_thick=mag_depth,
                    normal_dir="+Z",
                )

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
                screw_m, depth=depth_top, push_hole=True, push_hole_angle=15.0
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
                screw_m, depth=depth_bot, push_hole=True, push_hole_angle=15.0
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

    # 6. Optional 45-degree Print Orientation & Support Fins
    if print_orientation == "45_deg":
        # Rotate 45 deg around Y so the ridge-side 2mm chamfer lies flat on build plate (Z=0).
        # Ridges face down, magnet pockets face up.
        adapter = adapter.rotate((0, 0, 0), (0, 1, 0), 45)
        bb = adapter.val().BoundingBox()
        adapter = adapter.translate((0, 0, -bb.zmin))

        if support_fins:
            # The first convex edge of the ridges (crest) is at Z = -RIDGE_HEIGHT.
            # At this Z depth, the 45-degree edge chamfers reduce the width to
            # width - 2*(2.0 + RIDGE_HEIGHT). When rotated 45 deg around Y:
            plate_bed_x = (width / 2.0 - 2.0 - 2 * RIDGE_HEIGHT) * math.cos(math.radians(45))
            fin_L = (width - 4.0 - 2 * RIDGE_HEIGHT) * math.cos(math.radians(45))

            # Fin supporting 45-degree underside (ridge side facing down)
            fin = support_fin(z_gap=fin_z_gap, is_right=False, length=fin_L, height=fin_L, fin_width=1.6)
            fin = fin.rotate((0, 0, 0), (0, 0, 1), -90).translate((plate_bed_x, 0, 0))

            # Support fins aligned with the first convex edge of each ridge:
            # Top ridge first convex edge: Y = top_screw_y - RIDGE_PEAK_HALF_WIDTH (crest inner edge)
            # Bottom ridge first convex edge: Y = bottom_screw_y + RIDGE_PEAK_HALF_WIDTH (crest inner edge)
            # The fin tapered tip is centered at Y=0, so this directly aligns the tip center with the edge.
            fin_top = fin.translate((0, top_screw_y - RIDGE_PEAK_HALF_WIDTH, 0))
            fin_bot = fin.translate((0, bottom_screw_y + RIDGE_PEAK_HALF_WIDTH, 0))

            adapter = adapter.union(fin_top).union(fin_bot)

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
        default=LARGE_MAGNET_DIA,
        help=f"Diameter of disc magnet in mm (default: {LARGE_MAGNET_DIA} for standard large disc)",
    )
    parser.add_argument(
        "--mag-depth",
        type=float,
        default=LARGE_MAGNET_THICK,
        help=f"Depth of disc magnet pocket in mm (default: {LARGE_MAGNET_THICK})",
    )
    parser.add_argument(
        "--mag-count",
        type=int,
        default=None,
        help="Number of disc magnets per unit space (default: auto, maximizes magnets for rail height, e.g. 3 per 1U / 6 for 2U at 73mm)",
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
        "--no-support-fins",
        action="store_true",
        help="Disable support fins in 45_deg orientation",
    )
    parser.add_argument(
        "--fin-z-gap",
        type=float,
        default=0.10,
        help="Z gap between support fin tip and model face in mm for separate perimeters (default: 0.10)",
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
        default="45_deg",
        choices=["45_deg", "back_down", "face_down", "left_down", "right_down", "top_down", "bottom_down", "none"],
        help="Print orientation for STL export (default: 45_deg)",
    )

    args = parser.parse_args()

    # Pass 45_deg to create_magnetic_adapter if chosen, otherwise pass none and let export_model rotate
    adapter_orient = "45_deg" if args.print_orientation == "45_deg" else "none"
    export_orient = "none" if args.print_orientation == "45_deg" else args.print_orientation

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
        print_orientation=adapter_orient,
        support_fins=not args.no_support_fins,
        fin_z_gap=args.fin_z_gap,
    )

    count_per_unit, _ = compute_magnet_layout(
        rail_height=args.rail_height,
        mag_dia=args.mag_dia,
        mag_count=args.mag_count,
        mag_y=args.mag_y,
        no_screws=args.no_screws,
        screw_m=args.screw,
    )
    total_mags = args.units * count_per_unit

    if total_mags > 1:
        filename = f"magnetic_adapter_{args.units}u_H{int(args.rail_height)}_{total_mags}mag_{args.screw}.stl"
    else:
        filename = f"magnetic_adapter_{args.units}u_H{int(args.rail_height)}_{args.screw}.stl"

    export_model(
        adapter,
        filename,
        category="magnetic",
        print_orientation=export_orient,
        export=args.export,
    )


if __name__ == "__main__":
    main()
