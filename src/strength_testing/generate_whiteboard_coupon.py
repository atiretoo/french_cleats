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
"""
generate_whiteboard_coupon.py

Generates a compact, fast-printing test coupon (15 mm tall) to verify hole dimensions,
clearances, divider wall spacing, and groove engagement for the Whiteboard Tool Holder:
  - Round hole for spray bottle (35.0 mm dia + clearance).
  - Rectangular hole with rounded corners for eraser (55.0 x 32.0 mm + clearance).
  - Exact divider wall and side margins.
  - Standard 45° shallow groove on the rear backplate face (10 mm from bottom) to test
    mechanical seating against the magnetic mount or French cleat rails.
  - 1.0 mm lead-in chamfers on the top rims.
"""

import cadquery as cq
import argparse
import sys
import os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH,
    BACKPLATE_THICKNESS,
    GROOVE_DEPTH,
    GROOVE_SURFACE_HALF_WIDTH,
    GROOVE_BOTTOM_HALF_WIDTH,
    export_model,
)


def create_whiteboard_test_coupon(
    units=None,
    coupon_height=15.0,
    shelf_depth=None,
    bottle_dia=35.0,
    bottle_clearance=1.5,
    eraser_width=55.0,
    eraser_thickness=32.0,
    eraser_clearance=1.5,
    eraser_corner_radius=2.5,
    layout="auto",
    with_groove=True,
    fillet_radius=4.0,
    lip_chamfer=1.0,
):
    """
    Creates a physical test coupon to calibrate and verify hole clearances and spacing
    for the whiteboard spray bottle and eraser.
    """
    if layout in (None, "auto"):
        if units == 2:
            resolved_layout = "inline_2u"
        elif units == 3:
            resolved_layout = "inline_3u"
        elif units is not None and units >= 4:
            resolved_layout = "bottle_left"
        else:
            resolved_layout = "inline_2u"
    elif layout == "inline":
        resolved_layout = "inline_2u"
    elif layout == "side_by_side":
        resolved_layout = "bottle_left"
    else:
        resolved_layout = layout

    is_inline = resolved_layout in ("inline_2u", "inline_3u")

    if resolved_layout == "inline_2u":
        min_units = 2
        default_depth = 111.0
    elif resolved_layout == "inline_3u":
        min_units = 3
        default_depth = 88.0
    else:
        min_units = 4
        default_depth = 50.0

    if units is None:
        units = min_units
    elif units < min_units:
        units = min_units

    if shelf_depth is None:
        shelf_depth = default_depth

    width = units * UNIT_WIDTH
    bp_thick = BACKPLATE_THICKNESS
    groove_y = 10.0  # 10mm from bottom edge (matching standard bottom groove location)

    effective_bottle_dia = bottle_dia + bottle_clearance
    raw_eraser_w = eraser_width + eraser_clearance
    raw_eraser_d = eraser_thickness + eraser_clearance

    # 1. Profile in YZ plane
    # If with_groove: include standard 45° shallow groove on the back face (Z=0)
    if with_groove and coupon_height >= (groove_y + GROOVE_SURFACE_HALF_WIDTH):
        pts_coupon = [
            (0, 0),
            (groove_y - GROOVE_SURFACE_HALF_WIDTH, 0),
            (groove_y - GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (groove_y + GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (groove_y + GROOVE_SURFACE_HALF_WIDTH, 0),
            (coupon_height, 0),
            (coupon_height, -(bp_thick + shelf_depth)),
            (0, -(bp_thick + shelf_depth)),
            (0, 0),
        ]
    else:
        pts_coupon = [
            (0, 0),
            (coupon_height, 0),
            (coupon_height, -(bp_thick + shelf_depth)),
            (0, -(bp_thick + shelf_depth)),
            (0, 0),
        ]

    coupon = (
        cq.Workplane("YZ")
        .polyline(pts_coupon)
        .close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )

    # 2. Fillet front vertical corners
    class FrontCornerSel(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge):
                    continue
                b = o.BoundingBox()
                if (
                    abs(b.zmin - (-(bp_thick + shelf_depth))) < 0.5
                    and abs(b.zmax - (-(bp_thick + shelf_depth))) < 0.5
                ):
                    if (
                        abs(b.xmin - (-width / 2.0)) < 0.5
                        or abs(b.xmax - (width / 2.0)) < 0.5
                    ):
                        res.append(o)
            return res

    try:
        coupon = coupon.edges(FrontCornerSel()).fillet(fillet_radius)
    except Exception:
        pass

    # 3. Calculate Hole Positions
    if is_inline:
        bottle_x = 0.0
        eraser_x = 0.0

        if resolved_layout == "inline_2u":
            effective_eraser_w = raw_eraser_d
            effective_eraser_d = raw_eraser_w
        else:
            effective_eraser_w = raw_eraser_w
            effective_eraser_d = raw_eraser_d

        w_rear = 6.0
        w_mid = 6.0
        z_bottle = -bp_thick - w_rear - effective_bottle_dia / 2.0
        z_eraser = -bp_thick - w_rear - effective_bottle_dia - w_mid - effective_eraser_d / 2.0

    else:
        effective_eraser_w = raw_eraser_w
        effective_eraser_d = raw_eraser_d
        z_center = -bp_thick - shelf_depth / 2.0
        z_bottle = z_center
        z_eraser = z_center

        rem_width = width - (effective_bottle_dia + effective_eraser_w)
        wall_left = rem_width * (5.5 / 19.0)
        wall_mid = rem_width * (8.0 / 19.0)

        if resolved_layout == "bottle_left":
            bottle_x = -width / 2.0 + wall_left + effective_bottle_dia / 2.0
            eraser_x = -width / 2.0 + wall_left + effective_bottle_dia + wall_mid + effective_eraser_w / 2.0
        else:
            eraser_x = -width / 2.0 + wall_left + effective_eraser_w / 2.0
            bottle_x = -width / 2.0 + wall_left + effective_eraser_w + wall_mid + effective_bottle_dia / 2.0

    # 4. Cut Through-Holes
    bottle_hole = (
        cq.Workplane("ZX", origin=(0, -5.0, 0))
        .center(z_bottle, bottle_x)
        .circle(effective_bottle_dia / 2.0)
        .extrude(coupon_height + 10.0)
    )
    coupon = coupon.cut(bottle_hole)

    eraser_hole = (
        cq.Workplane("ZX", origin=(0, -5.0, 0))
        .center(z_eraser, eraser_x)
        .rect(effective_eraser_d, effective_eraser_w)
        .extrude(coupon_height + 10.0)
    )
    if eraser_corner_radius > 0:
        eraser_hole = eraser_hole.edges("|Y").fillet(eraser_corner_radius)
    coupon = coupon.cut(eraser_hole)

    # 5. Lead-in Chamfer on Top Lips
    if lip_chamfer > 0:
        class TopLipSelector(cq.Selector):
            def filter(self, objectList):
                res = []
                for o in objectList:
                    if not isinstance(o, cq.Edge):
                        continue
                    b = o.BoundingBox()
                    if abs(b.ymin - coupon_height) < 0.1 and abs(b.ymax - coupon_height) < 0.1:
                        if (
                            b.xmin > -width / 2.0 + 1.0
                            and b.xmax < width / 2.0 - 1.0
                            and b.zmax < -bp_thick - 1.0
                            and b.zmin > -bp_thick - shelf_depth + 1.0
                        ):
                            res.append(o)
                return res

        try:
            coupon = coupon.edges(TopLipSelector()).chamfer(lip_chamfer)
        except Exception:
            pass

    return coupon


def main():
    parser = argparse.ArgumentParser(
        description="Generate physical test coupon for whiteboard tool clearances and spacing."
    )
    parser.add_argument(
        "--layout",
        type=str,
        default="inline_2u",
        choices=[
            "inline_2u",
            "inline_3u",
            "inline",
            "bottle_left",
            "eraser_left",
            "side_by_side",
        ],
        help="Arrangement of tools on the shelf (default: inline_2u)",
    )
    parser.add_argument(
        "--units",
        type=int,
        default=None,
        help="Width in 28mm UNITs (default: 2 for inline_2u, 3 for inline_3u, 4 for side_by_side)",
    )
    parser.add_argument(
        "--coupon-height",
        type=float,
        default=15.0,
        help="Height of the test coupon in mm (default: 15.0)",
    )
    parser.add_argument(
        "--shelf-depth",
        type=float,
        default=None,
        help="Shelf depth in mm (default: auto based on layout)",
    )
    parser.add_argument(
        "--bottle-dia",
        type=float,
        default=35.0,
        help="Spray bottle diameter in mm (default: 35.0)",
    )
    parser.add_argument(
        "--bottle-clearance",
        type=float,
        default=1.5,
        help="Clearance added to spray bottle hole diameter in mm (default: 1.5)",
    )
    parser.add_argument(
        "--eraser-width",
        type=float,
        default=55.0,
        help="Eraser cross-section width in mm (default: 55.0)",
    )
    parser.add_argument(
        "--eraser-thickness",
        type=float,
        default=32.0,
        help="Eraser cross-section thickness in mm (default: 32.0)",
    )
    parser.add_argument(
        "--eraser-clearance",
        type=float,
        default=1.5,
        help="Clearance added to eraser hole dimensions in mm (default: 1.5)",
    )
    parser.add_argument(
        "--eraser-corner-radius",
        type=float,
        default=2.5,
        help="Internal corner radius of eraser hole in mm (default: 2.5)",
    )
    parser.add_argument(
        "--no-groove",
        dest="with_groove",
        action="store_false",
        help="Omit the rear mounting groove from the test coupon",
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
        default="bottom_down",
        choices=["bottom_down", "face_down", "none"],
        help="Print orientation for STL export (default: bottom_down)",
    )

    args = parser.parse_args()

    if args.layout in ("inline_2u", "inline"):
        eff_units = 2 if args.units is None else args.units
        eff_layout = "inline_2u"
        layout_tag = f"inline_{eff_units}u"
    elif args.layout == "inline_3u":
        eff_units = 3 if args.units is None else args.units
        eff_layout = "inline_3u"
        layout_tag = f"inline_{eff_units}u"
    else:
        eff_units = 4 if args.units is None else args.units
        eff_layout = args.layout
        layout_tag = f"{eff_units}u"

    coupon = create_whiteboard_test_coupon(
        units=eff_units,
        coupon_height=args.coupon_height,
        shelf_depth=args.shelf_depth,
        bottle_dia=args.bottle_dia,
        bottle_clearance=args.bottle_clearance,
        eraser_width=args.eraser_width,
        eraser_thickness=args.eraser_thickness,
        eraser_clearance=args.eraser_clearance,
        eraser_corner_radius=args.eraser_corner_radius,
        layout=eff_layout,
        with_groove=args.with_groove,
    )

    filename = f"whiteboard_hole_test_coupon_{layout_tag}_H{int(args.coupon_height)}.stl"
    export_model(
        coupon,
        filename,
        category="strength_testing",
        print_orientation=args.print_orientation,
        export=args.export,
    )


if __name__ == "__main__":
    main()
