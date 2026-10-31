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
from core_library import (
    UNIT_WIDTH, export_model, create_nut_slot,
    get_ridge_points, NUT_SLOT_TOLERANCE, SCREW_SPECS,
    BACKPLATE_TOP_Y, TOP_RIDGE_Y
)

def create_top_cleat(units=2, rail_thickness=19.0, screw_m="M3"):
    if screw_m not in SCREW_SPECS:
        raise ValueError(f"Unsupported screw size: {screw_m}")
    spec = SCREW_SPECS[screw_m]
    screw_d, nut_thick = spec["clear"], spec["nut_thick"]

    width = units * UNIT_WIDTH
    tip_clearance = 2.0
    screw_y = TOP_RIDGE_Y
    top_y = BACKPLATE_TOP_Y

    pts = [
        (0, 0),
        (-rail_thickness + tip_clearance, rail_thickness - tip_clearance),
        (-rail_thickness + tip_clearance, rail_thickness),
        (top_y, rail_thickness),
        (top_y, 0),
    ] + get_ridge_points(screw_y)

    screw_pts = [(-width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH, screw_y) for i in range(units)]

    cleat = (
        cq.Workplane("YZ")
        .polyline(pts)
        .close()
        .extrude(width / 2.0, both=True)
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .pushPoints(screw_pts)
        .hole(screw_d)
    )

    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    slot_z_center = 4.0 + slot_t / 2.0
    depth = top_y - screw_y
    slot_solid = create_nut_slot(screw_m, depth=depth, push_hole=True)

    cutters = [slot_solid.moved(cq.Location(cq.Vector(x, y, slot_z_center))) for x, y in screw_pts]
    if cutters:
        cleat = cleat.cut(cq.Compound.makeCompound(cutters))

    return cleat


def create_bottom_cleat(units=2, rail_thickness=19.0, screw_m="M3"):
    if screw_m not in SCREW_SPECS:
        raise ValueError(f"Unsupported screw size: {screw_m}")
    spec = SCREW_SPECS[screw_m]
    screw_d, nut_thick = spec["clear"], spec["nut_thick"]

    width = units * UNIT_WIDTH
    height = 20.0
    screw_y = 0.0

    pts = [
        (-height / 2.0, 0),
        (-height / 2.0, rail_thickness),
        (-5.0, rail_thickness),
        (height / 2.0, 4.0),
        (height / 2.0, 0),
    ] + get_ridge_points(screw_y)

    screw_pts = [(-width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH, screw_y) for i in range(units)]

    cleat = (
        cq.Workplane("YZ")
        .polyline(pts)
        .close()
        .extrude(width / 2.0, both=True)
        .faces(">Z")
        .workplane(centerOption="ProjectedOrigin")
        .pushPoints(screw_pts)
        .hole(screw_d)
    )

    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    slot_z_center = 4.0 + slot_t / 2.0
    depth = screw_y - (-height / 2.0)
    slot_solid = create_nut_slot(screw_m, depth=depth, push_hole=True)
    slot_solid_rot = slot_solid.moved(cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180))

    cutters = [slot_solid_rot.moved(cq.Location(cq.Vector(x, y, slot_z_center))) for x, y in screw_pts]
    if cutters:
        cleat = cleat.cut(cq.Compound.makeCompound(cutters))

    return cleat


def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat attachments")
    parser.add_argument("--type", choices=["top", "bottom", "both"], default="both", help="Type of cleat to generate")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--rail-thickness", type=float, default=19.0, help="Thickness of the rail in mm")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")

    args = parser.parse_args()

    if args.type in ["top", "both"]:
        top = create_top_cleat(args.units, args.rail_thickness, args.screw)
        filename = f"top_cleat_{args.units}u_T{args.rail_thickness}_{args.screw}.stl"
        export_model(top, filename, category="cleats", export=args.export)

    if args.type in ["bottom", "both"]:
        bot = create_bottom_cleat(args.units, args.rail_thickness, args.screw)
        filename = f"bottom_cleat_{args.units}u_T{args.rail_thickness}_{args.screw}.stl"
        export_model(bot, filename, category="cleats", export=args.export)

if __name__ == "__main__":
    main()
