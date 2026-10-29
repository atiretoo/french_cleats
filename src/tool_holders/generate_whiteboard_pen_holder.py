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
generate_whiteboard_pen_holder.py

Creates a 1U Whiteboard Pen / Marker Holder designed to mount on the UNIT System
(French Cleat rails, magnetic adapters, MultiConnect, HSW, and pegboard):
  - 1 UNIT wide (28.0 mm).
  - Truncated cone pockets tailored to standard whiteboard marker caps:
      - 10.15 mm at the cap tip
      - 11.80 mm at the cap opening
      - 45.00 mm cap height
  - Pens sit cap-down in a single row centered on the projection.
  - Projection matches the Whiteboard Spray & Eraser Tool Holder:
      - 30.0 mm shelf thickness (elevated from Y = -70.0 to Y = -40.0 for 73mm rail)
      - 111.0 mm projection depth
      - Keeps lower mount screws and groove completely clear and operable from front.
  - 45-degree print orientation with support fins under backplate and shelf projection.
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
    DEFAULT_RAIL_HEIGHT,
    create_baseplate,
    export_model,
    support_fin,
)


def create_whiteboard_pen_holder(
    units=1,
    pen_count=4,
    rail_height=DEFAULT_RAIL_HEIGHT,
    shelf_thickness=30.0,
    shelf_depth=111.0,
    cap_tip_dia=10.15,
    cap_opening_dia=11.80,
    cap_height=45.0,
    pen_clearance=0.6,
    floor_thickness=0.0,
    drain_holes=True,
    fillet_radius=4.0,
    lip_chamfer=1.0,
    print_orientation="none",
    support_fins=True,
):
    """
    Creates a 1U whiteboard pen holder for marker caps matching the whiteboard suite projection.

    Parameters:
      units: Width in 28mm UNITs (default: 1).
      pen_count: Number of pens in the row (default: 4).
      rail_height: Cleat rail height in mm (default: 73.0).
      shelf_thickness: Vertical thickness of projection in mm (default: 30.0).
      shelf_depth: Depth of shelf projection from backplate in mm (default: 111.0, matching inline 2U).
      cap_tip_dia: Diameter of marker cap at the tip in mm (default: 10.15).
      cap_opening_dia: Diameter of marker cap at the opening/collar in mm (default: 11.80).
      cap_height: Height of marker cap in mm (default: 45.0).
      pen_clearance: Radial/diametral clearance added to pocket in mm (default: 0.6).
      floor_thickness: Thickness of bottom shelf floor in mm (default: 0.0 for through-holes).
      drain_holes: If floor_thickness > 0, cut a central cleanout hole through floor (default: True).
      fillet_radius: Radius for front corner and junction fillets in mm (default: 4.0).
      lip_chamfer: Chamfer on top entrance rim of each pocket in mm (default: 1.0).
      print_orientation: '45_deg', 'bottom_down', 'none', etc. (default: 'none').
      support_fins: If True and print_orientation is 45_deg, adds support fins (default: True).
    """
    width = units * UNIT_WIDTH

    # 1. Baseplate with standard UNIT groove
    body, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        units=units,
        rail_height=rail_height,
        mount_type="groove",
    )

    # Elevated shelf: 14mm above bottom groove so lower groove and screws are fully operable
    shelf_bottom_y = bottom_groove_y + 14.0
    shelf_top_y = shelf_bottom_y + shelf_thickness

    # 2. Shelf Solid
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
    class JunctionSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge):
                    continue
                b = o.BoundingBox()
                if (
                    (abs(b.ymin - shelf_top_y) < 0.5 or abs(b.ymin - shelf_bottom_y) < 0.5)
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

    # 4. Truncated Cone Pen Pockets
    # Radial taper of the marker cap cone
    slope_r = ((cap_opening_dia - cap_tip_dia) / 2.0) / cap_height
    r_top = (cap_opening_dia + pen_clearance) / 2.0

    # Margins along Z
    w_rear = 10.0
    w_front = 10.0
    z_start = -BACKPLATE_THICKNESS - w_rear - r_top
    z_end = -BACKPLATE_THICKNESS - shelf_depth + w_front + r_top
    z_span = z_start - z_end

    if pen_count <= 1:
        pen_zs = [(z_start + z_end) / 2.0]
    else:
        pitch = z_span / (pen_count - 1)
        pen_zs = [z_start - i * pitch for i in range(pen_count)]

    # X positions: single row centered per 1U space
    x_positions = [-width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH for i in range(units)]

    is_through = floor_thickness <= 0.0
    cut_base_y = shelf_bottom_y + (0.0 if is_through else floor_thickness) - (1.0 if is_through else 0.0)
    total_cone_h = (shelf_top_y + 1.0) - cut_base_y
    r_base = r_top - slope_r * (shelf_top_y - cut_base_y)
    r_top_cut = r_top + slope_r * 1.0

    for x in x_positions:
        for z in pen_zs:
            pnt = cq.Vector(x, cut_base_y, z)
            cone = cq.Solid.makeCone(r_base, r_top_cut, total_cone_h, pnt=pnt, dir=cq.Vector(0, 1, 0))
            body = body.cut(cq.Workplane(cone))

            # Chamfer top entrance rim
            if lip_chamfer > 0.0:
                chamfer_cone = cq.Solid.makeCone(
                    r_top,
                    r_top + lip_chamfer,
                    lip_chamfer + 0.1,
                    pnt=cq.Vector(x, shelf_top_y - lip_chamfer, z),
                    dir=cq.Vector(0, 1, 0),
                )
                body = body.cut(cq.Workplane(chamfer_cone))

            # Optional drain / cleanout hole if closed floor
            if not is_through and drain_holes:
                drain_dia = 7.0
                drain = cq.Solid.makeCylinder(
                    drain_dia / 2.0,
                    floor_thickness + 2.0,
                    pnt=cq.Vector(x, shelf_bottom_y - 1.0, z),
                    dir=cq.Vector(0, 1, 0),
                )
                body = body.cut(cq.Workplane(drain))

    # 5. Mounting Screws (both top and bottom are fully clear and operable)
    if screw_pts:
        valid_screw_pts = [pt for pt in screw_pts if pt[1] > shelf_top_y or pt[1] < shelf_bottom_y]
        if valid_screw_pts:
            screws = (
                cq.Workplane("XY")
                .workplane(offset=0)
                .pushPoints(valid_screw_pts)
                .circle(3.6 / 2.0)
                .extrude(-20)
            )
            body = body.cut(screws)

            recesses = (
                cq.Workplane("XY")
                .workplane(offset=-8)
                .pushPoints(valid_screw_pts)
                .circle(8.0 / 2.0)
                .extrude(-20)
            )
            body = body.cut(recesses)

    # 6. Optional 45-degree Print Orientation & Support Fins
    if print_orientation == "45_deg":
        # Rotate 180 around X then +45 around Y so chamfered backplate edge sits on build plate
        body = body.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 1, 0), 45)
        bb = body.val().BoundingBox()
        body = body.translate((0, 0, -bb.zmin))

        if support_fins:
            cos45 = math.cos(math.radians(45))
            bed_faces = [
                f for f in body.val().Faces()
                if f.geomType() == "PLANE" and abs(f.Center().z) < 0.05 and f.normalAt().z < -0.9
            ]
            if bed_faces:
                c_bb = bed_faces[0].BoundingBox()
                bed_xmin = c_bb.xmin
                bed_xmax = c_bb.xmax
            else:
                bed_xmin = (width / 2.0 - 2.0) * cos45
                bed_xmax = (width / 2.0) * cos45

            # Backplate underside support fins
            bp_L = width * cos45
            bp_fin = support_fin(z_gap=0.01, is_right=False, length=bp_L, height=bp_L, fin_width=1.6)
            bp_fin = bp_fin.rotate((0, 0, 0), (0, 0, 1), -90).translate((bed_xmin, 0, 0))
            fin_bp_top = bp_fin.translate((0, -top_y + 1.6, 0))
            fin_bp_bot = bp_fin.translate((0, -bottom_y - 1.6, 0))

            # Shelf projection underside support fin
            shelf_max_x = (width / 2.0 * cos45) + (BACKPLATE_THICKNESS + shelf_depth) * cos45
            shelf_fin_L = max(30.0, shelf_max_x - bed_xmax - 2.83)
            shelf_fin = support_fin(z_gap=0.01, is_right=True, length=shelf_fin_L, height=shelf_fin_L, fin_width=1.6)
            shelf_fin = shelf_fin.rotate((0, 0, 0), (0, 0, 1), -90)
            shelf_rot_y = -shelf_bottom_y
            shelf_fin = shelf_fin.translate((bed_xmax, shelf_rot_y - 0.8, 0))

            body = body.union(fin_bp_top).union(fin_bp_bot).union(shelf_fin)

    return body


def create_whiteboard_pen_coupon(
    units=1,
    pen_count=4,
    coupon_height=15.0,
    shelf_depth=111.0,
    cap_tip_dia=10.15,
    cap_opening_dia=11.80,
    cap_height=45.0,
    pen_clearance=0.6,
    fillet_radius=4.0,
    lip_chamfer=1.0,
    with_groove=True,
):
    """
    Creates a compact 15mm tall test coupon to check truncated cone pen fit and hole pitch.
    """
    from core_library import (
        GROOVE_DEPTH,
        GROOVE_SURFACE_HALF_WIDTH,
        GROOVE_BOTTOM_HALF_WIDTH,
    )

    width = units * UNIT_WIDTH
    total_depth = BACKPLATE_THICKNESS + shelf_depth

    # Base block
    body = (
        cq.Workplane("XY")
        .box(width, coupon_height, total_depth)
        .translate((0, coupon_height / 2.0, -total_depth / 2.0))
    )

    # Standard shallow groove on backplate face (Z=0) at Y=10.0
    if with_groove:
        groove_y = 10.0
        groove_pts = [
            (groove_y + GROOVE_SURFACE_HALF_WIDTH, 0),
            (groove_y + GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (groove_y - GROOVE_BOTTOM_HALF_WIDTH, -GROOVE_DEPTH),
            (groove_y - GROOVE_SURFACE_HALF_WIDTH, 0),
        ]
        groove = (
            cq.Workplane("YZ")
            .polyline(groove_pts)
            .close()
            .extrude(width + 20.0)
            .translate((-width / 2.0 - 10.0, 0, 0))
        )
        body = body.cut(groove)

    # Front corner fillets
    class FrontCornerSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge):
                    continue
                b = o.BoundingBox()
                if (
                    abs(b.zmin - (-total_depth)) < 0.5
                    and abs(b.zmax - (-total_depth)) < 0.5
                ):
                    if (
                        abs(b.xmin - (-width / 2.0)) < 0.5
                        or abs(b.xmax - (width / 2.0)) < 0.5
                    ) and abs(b.ymax - b.ymin - coupon_height) < 0.5:
                        res.append(o)
            return res

    try:
        body = body.edges(FrontCornerSelector()).fillet(fillet_radius)
    except Exception:
        pass

    # Truncated cone cuts
    slope_r = ((cap_opening_dia - cap_tip_dia) / 2.0) / cap_height
    r_top = (cap_opening_dia + pen_clearance) / 2.0

    w_rear = 10.0
    w_front = 10.0
    z_start = -BACKPLATE_THICKNESS - w_rear - r_top
    z_end = -BACKPLATE_THICKNESS - shelf_depth + w_front + r_top
    z_span = z_start - z_end

    if pen_count <= 1:
        pen_zs = [(z_start + z_end) / 2.0]
    else:
        pitch = z_span / (pen_count - 1)
        pen_zs = [z_start - i * pitch for i in range(pen_count)]

    x_positions = [-width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH for i in range(units)]

    h_cut = coupon_height + 2.0
    cut_base_y = -1.0
    r_base = r_top - slope_r * (coupon_height + 1.0)
    r_top_cut = r_top + slope_r * 1.0

    for x in x_positions:
        for z in pen_zs:
            pnt = cq.Vector(x, cut_base_y, z)
            cone = cq.Solid.makeCone(r_base, r_top_cut, h_cut, pnt=pnt, dir=cq.Vector(0, 1, 0))
            body = body.cut(cq.Workplane(cone))

            if lip_chamfer > 0.0:
                chamfer_cone = cq.Solid.makeCone(
                    r_top,
                    r_top + lip_chamfer,
                    lip_chamfer + 0.1,
                    pnt=cq.Vector(x, coupon_height - lip_chamfer, z),
                    dir=cq.Vector(0, 1, 0),
                )
                body = body.cut(cq.Workplane(chamfer_cone))

    return body


def main():
    parser = argparse.ArgumentParser(
        description="Generate 1U Whiteboard Pen Holder matching Whiteboard Tool suite projection"
    )
    parser.add_argument(
        "--units",
        type=int,
        default=1,
        help="Width in 28mm UNITs (default: 1)",
    )
    parser.add_argument(
        "--pen-count",
        type=int,
        default=4,
        help="Number of pens in the row (default: 4)",
    )
    parser.add_argument(
        "--rail-height",
        type=float,
        default=DEFAULT_RAIL_HEIGHT,
        help="Standard cleat rail height in mm (default: 73.0)",
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
        default=111.0,
        help="Projection depth of the shelf in mm (default: 111.0, matching inline 2U)",
    )
    parser.add_argument(
        "--cap-tip-dia",
        type=float,
        default=10.15,
        help="Diameter of marker cap at the tip in mm (default: 10.15)",
    )
    parser.add_argument(
        "--cap-opening-dia",
        type=float,
        default=11.80,
        help="Diameter of marker cap at opening/collar in mm (default: 11.80)",
    )
    parser.add_argument(
        "--cap-height",
        type=float,
        default=45.0,
        help="Height of marker cap in mm (default: 45.0)",
    )
    parser.add_argument(
        "--pen-clearance",
        type=float,
        default=0.6,
        help="Clearance added to marker cap hole diameter in mm (default: 0.6)",
    )
    parser.add_argument(
        "--floor-thickness",
        type=float,
        default=0.0,
        help="Thickness of shelf floor in mm (default: 0.0 for through-holes)",
    )
    parser.add_argument(
        "--print-orientation",
        type=str,
        default="45_deg",
        choices=[
            "45_deg",
            "bottom_down",
            "back_down",
            "left_down",
            "right_down",
            "top_down",
            "face_down",
            "none",
        ],
        help="Print orientation for STL export (default: 45_deg with support fins)",
    )
    parser.add_argument(
        "--no-support-fins",
        action="store_true",
        help="Disable support fins in 45_deg orientation",
    )
    parser.add_argument(
        "--coupon",
        action="store_true",
        help="Generate a compact 15mm tall test coupon to check pen cap fit and pitch",
    )
    parser.add_argument(
        "--export",
        choices=["both", "stl", "step"],
        default="both",
        help="Export format (default: both)",
    )

    args = parser.parse_args()

    holder_orient = "45_deg" if args.print_orientation == "45_deg" else "none"
    export_orient = "none" if args.print_orientation == "45_deg" else args.print_orientation

    if args.coupon:
        model = create_whiteboard_pen_coupon(
            units=args.units,
            pen_count=args.pen_count,
            coupon_height=15.0,
            shelf_depth=args.shelf_depth,
            cap_tip_dia=args.cap_tip_dia,
            cap_opening_dia=args.cap_opening_dia,
            cap_height=args.cap_height,
            pen_clearance=args.pen_clearance,
        )
        filename = f"whiteboard_pen_holder_{args.units}u_{args.pen_count}pen_coupon.stl"
        export_orient = args.print_orientation if args.print_orientation != "45_deg" else "bottom_down"
    else:
        model = create_whiteboard_pen_holder(
            units=args.units,
            pen_count=args.pen_count,
            rail_height=args.rail_height,
            shelf_thickness=args.shelf_thickness,
            shelf_depth=args.shelf_depth,
            cap_tip_dia=args.cap_tip_dia,
            cap_opening_dia=args.cap_opening_dia,
            cap_height=args.cap_height,
            pen_clearance=args.pen_clearance,
            floor_thickness=args.floor_thickness,
            print_orientation=holder_orient,
            support_fins=not args.no_support_fins,
        )
        filename = f"whiteboard_pen_holder_{args.units}u.stl" if args.pen_count == 4 else f"whiteboard_pen_holder_{args.units}u_{args.pen_count}pen.stl"

    export_model(
        model,
        filename,
        category="",
        print_orientation=export_orient,
        export=args.export,
    )


if __name__ == "__main__":
    main()
