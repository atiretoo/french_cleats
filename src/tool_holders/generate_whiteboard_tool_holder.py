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
    BACKPLATE_THICKNESS,
    DEFAULT_RAIL_HEIGHT,
    create_baseplate,
    export_model,
)


def create_whiteboard_tool_holder(
    units=4,
    rail_height=DEFAULT_RAIL_HEIGHT,
    shelf_thickness=30.0,
    shelf_depth=50.0,
    floor_thickness=3.0,
    drain_holes=True,
    bottle_dia=35.0,
    bottle_clearance=1.5,
    eraser_width=55.0,
    eraser_thickness=32.0,
    eraser_clearance=1.5,
    eraser_corner_radius=2.5,
    layout="bottle_left",
    fillet_radius=4.0,
    lip_chamfer=1.0,
):
    """
    Creates a French Cleat / UNIT whiteboard tool holder designed to store a whiteboard
    spray bottle (35 mm dia x 125 mm high) and an eraser (55 mm x 32 mm cross section x 125 mm long).

    Features:
      - Standard UNIT shallow groove backplate compatible with all cleat rails,
        as well as magnetic, Multiconnect, HSW, and pegboard adapters.
      - 30 mm thick low shelf positioned at the bottom of the baseplate, providing
        deep pockets that securely prevent tall 125 mm tools from tipping over.
      - Backplate extends 84 mm above the shelf up to Y = 20.0, providing tall,
        rigid backing support for the spray bottle and eraser.
      - Centered drain / cleanout holes in the pocket floor to prevent dust accumulation
        and eliminate suction when inserting snug tools.
      - Chamfered top entrance rims for smooth, effortless insertion.
    """
    effective_bottle_dia = bottle_dia + bottle_clearance
    effective_eraser_w = eraser_width + eraser_clearance
    effective_eraser_d = eraser_thickness + eraser_clearance

    min_required_width = effective_bottle_dia + effective_eraser_w + 16.0
    min_units = int(math.ceil(min_required_width / UNIT_WIDTH))
    if units < min_units:
        print(f"Warning: {units} units ({units * UNIT_WIDTH}mm) is too narrow to fit both tools.")
        print(f"Automatically expanding to {min_units} units ({min_units * UNIT_WIDTH}mm).")
        units = min_units

    width = units * UNIT_WIDTH

    # 1. Baseplate with standard UNIT groove
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        units=units,
        rail_height=rail_height,
        mount_type="groove",
    )

    shelf_bottom_y = bottom_y
    shelf_top_y = shelf_bottom_y + shelf_thickness

    # 2. Shelf Solid
    # In YZ plane: Local X = Global Y, Local Y = Global Z, Normal = +Global X
    shelf_pts = [
        (shelf_bottom_y, -BACKPLATE_THICKNESS),
        (shelf_bottom_y, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top_y, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top_y, -BACKPLATE_THICKNESS),
    ]

    shelf = (
        cq.Workplane("YZ")
        .polyline(shelf_pts)
        .close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )
    body = body.union(shelf)

    # 3. Fillets
    # Junction fillet where shelf top meets backplate front face
    class JunctionSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge):
                    continue
                b = o.BoundingBox()
                if (
                    abs(b.ymin - shelf_top_y) < 0.5
                    and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 0.5
                    and abs(b.zmax - (-BACKPLATE_THICKNESS)) < 0.5
                    and (b.xmax - b.xmin) > (width - 1.0)
                ):
                    res.append(o)
            return res

    try:
        body = body.edges(JunctionSelector()).fillet(fillet_radius)
    except Exception:
        pass

    # Front vertical corners of shelf
    class FrontCornerSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge):
                    continue
                b = o.BoundingBox()
                if (
                    abs(b.zmin - (-BACKPLATE_THICKNESS - shelf_depth)) < 0.5
                    and abs(b.zmax - (-BACKPLATE_THICKNESS - shelf_depth)) < 0.5
                ):
                    if (
                        abs(b.xmin - (-width / 2.0)) < 0.5
                        or abs(b.xmax - (width / 2.0)) < 0.5
                    ) and abs(b.ymax - b.ymin - shelf_thickness) < 0.5:
                        res.append(o)
            return res

    try:
        body = body.edges(FrontCornerSelector()).fillet(fillet_radius)
    except Exception:
        pass

    # 4. Pocket Positions
    z_center = -BACKPLATE_THICKNESS - shelf_depth / 2.0

    rem_width = width - (effective_bottle_dia + effective_eraser_w)
    wall_left = rem_width * (5.5 / 19.0)
    wall_mid = rem_width * (8.0 / 19.0)
    wall_right = rem_width * (5.5 / 19.0)

    if layout == "bottle_left":
        bottle_x = -width / 2.0 + wall_left + effective_bottle_dia / 2.0
        eraser_x = -width / 2.0 + wall_left + effective_bottle_dia + wall_mid + effective_eraser_w / 2.0
    else:
        eraser_x = -width / 2.0 + wall_left + effective_eraser_w / 2.0
        bottle_x = -width / 2.0 + wall_left + effective_eraser_w + wall_mid + effective_bottle_dia / 2.0

    cut_start_y = shelf_bottom_y + max(0.0, floor_thickness)
    cut_height = shelf_thickness + 15.0

    # In Workplane("ZX", origin=(0, y, 0)): Local X = Global Z, Local Y = Global X, Normal = +Global Y
    # 5. Bottle Pocket
    bottle_cutter = (
        cq.Workplane("ZX", origin=(0, cut_start_y, 0))
        .center(z_center, bottle_x)
        .circle(effective_bottle_dia / 2.0)
        .extrude(cut_height)
    )
    body = body.cut(bottle_cutter)

    # 6. Eraser Pocket (with rounded internal corners)
    eraser_cutter = (
        cq.Workplane("ZX", origin=(0, cut_start_y, 0))
        .center(z_center, eraser_x)
        .rect(effective_eraser_d, effective_eraser_w)
        .extrude(cut_height)
    )
    if eraser_corner_radius > 0:
        eraser_cutter = eraser_cutter.edges("|Y").fillet(eraser_corner_radius)
    body = body.cut(eraser_cutter)

    # 7. Drain / Cleanout Holes in Floor
    if drain_holes and floor_thickness > 0:
        drain_depth = floor_thickness + 4.0
        drain_bottle = (
            cq.Workplane("ZX", origin=(0, shelf_bottom_y - 2.0, 0))
            .center(z_center, bottle_x)
            .circle(min(16.0, effective_bottle_dia - 10.0) / 2.0)
            .extrude(drain_depth)
        )
        body = body.cut(drain_bottle)

        drain_eraser_w = max(10.0, effective_eraser_w - 20.0)
        drain_eraser_d = max(8.0, effective_eraser_d - 16.0)
        drain_eraser = (
            cq.Workplane("ZX", origin=(0, shelf_bottom_y - 2.0, 0))
            .center(z_center, eraser_x)
            .rect(drain_eraser_d, drain_eraser_w)
            .extrude(drain_depth)
        )
        if eraser_corner_radius > 0:
            drain_eraser = drain_eraser.edges("|Y").fillet(min(eraser_corner_radius, 2.0))
        body = body.cut(drain_eraser)

    # 8. Top Entrance Chamfer
    if lip_chamfer > 0:
        class TopLipSelector(cq.Selector):
            def filter(self, objectList):
                res = []
                for o in objectList:
                    if not isinstance(o, cq.Edge):
                        continue
                    b = o.BoundingBox()
                    if abs(b.ymin - shelf_top_y) < 0.1 and abs(b.ymax - shelf_top_y) < 0.1:
                        if (
                            b.xmin > -width / 2.0 + 1.0
                            and b.xmax < width / 2.0 - 1.0
                            and b.zmax < -BACKPLATE_THICKNESS - 1.0
                            and b.zmin > -BACKPLATE_THICKNESS - shelf_depth + 1.0
                        ):
                            res.append(o)
                return res

        try:
            body = body.edges(TopLipSelector()).chamfer(lip_chamfer)
        except Exception:
            pass

    # 9. Top Screws
    if screw_pts:
        top_screw_pts = [pt for pt in screw_pts if pt[1] > shelf_top_y]
        if top_screw_pts:
            screws = (
                cq.Workplane("XY")
                .workplane(offset=0)
                .pushPoints(top_screw_pts)
                .circle(3.6 / 2.0)
                .extrude(-20)
            )
            body = body.cut(screws)

            recesses = (
                cq.Workplane("XY")
                .workplane(offset=-8)
                .pushPoints(top_screw_pts)
                .circle(8.0 / 2.0)
                .extrude(-20)
            )
            body = body.cut(recesses)

    return body


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate whiteboard tool holder with low 30mm shelf."
    )
    parser.add_argument(
        "--units",
        type=int,
        default=4,
        help="Width in 28mm UNITs (default: 4 for 112mm width)",
    )
    parser.add_argument(
        "--rail-height",
        type=float,
        default=DEFAULT_RAIL_HEIGHT,
        help="Standard cleat rail height (default: 73.0)",
    )
    parser.add_argument(
        "--shelf-thickness",
        type=float,
        default=30.0,
        help="Vertical thickness of the low shelf in mm (default: 30.0)",
    )
    parser.add_argument(
        "--shelf-depth",
        type=float,
        default=50.0,
        help="Projection depth of the shelf in mm (default: 50.0)",
    )
    parser.add_argument(
        "--floor-thickness",
        type=float,
        default=3.0,
        help="Thickness of the bottom floor in mm (default: 3.0, set 0 for through-holes)",
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
        "--layout",
        type=str,
        default="bottle_left",
        choices=["bottle_left", "eraser_left"],
        help="Arrangement of tools on the shelf (default: bottle_left)",
    )
    parser.add_argument(
        "--no-drain",
        dest="drain_holes",
        action="store_false",
        help="Disable cleanout / drain holes in pocket floor",
    )
    parser.add_argument(
        "--coupon",
        action="store_true",
        help="Generate a compact 15mm tall test coupon to check hole spacing and clearances",
    )
    parser.add_argument(
        "--coupon-height",
        type=float,
        default=15.0,
        help="Height of the test coupon in mm if --coupon is set (default: 15.0)",
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
        choices=[
            "bottom_down",
            "back_down",
            "left_down",
            "right_down",
            "top_down",
            "face_down",
            "none",
        ],
        help="Print orientation for STL export (default: bottom_down)",
    )

    args = parser.parse_args()

    if args.coupon:
        from strength_testing.generate_whiteboard_coupon import create_whiteboard_test_coupon
        model = create_whiteboard_test_coupon(
            units=args.units,
            coupon_height=args.coupon_height,
            shelf_depth=args.shelf_depth,
            bottle_dia=args.bottle_dia,
            bottle_clearance=args.bottle_clearance,
            eraser_width=args.eraser_width,
            eraser_thickness=args.eraser_thickness,
            eraser_clearance=args.eraser_clearance,
            eraser_corner_radius=args.eraser_corner_radius,
            layout=args.layout,
        )
        filename = f"whiteboard_tool_holder_{args.units}u_coupon.stl"
    else:
        model = create_whiteboard_tool_holder(
            units=args.units,
            rail_height=args.rail_height,
            shelf_thickness=args.shelf_thickness,
            shelf_depth=args.shelf_depth,
            floor_thickness=args.floor_thickness,
            drain_holes=args.drain_holes,
            bottle_dia=args.bottle_dia,
            bottle_clearance=args.bottle_clearance,
            eraser_width=args.eraser_width,
            eraser_thickness=args.eraser_thickness,
            eraser_clearance=args.eraser_clearance,
            eraser_corner_radius=args.eraser_corner_radius,
            layout=args.layout,
        )
        filename = f"whiteboard_tool_holder_{args.units}u.stl"

    export_model(
        model,
        filename,
        category="tool_holders",
        print_orientation=args.print_orientation,
        export=args.export,
    )
