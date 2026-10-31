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
import argparse
import os
import sys
import math
import cadquery as cq

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH, BACKPLATE_TOP_Y, TOP_RIDGE_Y, RIDGE_HEIGHT, NUT_SLOT_TOLERANCE,
    SCREW_SPECS, get_ridge_points, get_bottom_ridge_y, get_bottom_edge_y,
    get_screw_points, export_model, create_nut_slot, support_fin,
    create_snap_fit_peg_parameterized
)

def create_adapter(units=2, rail_height=73.0, screw_m="M3", top_hook="arc", top_hook_dia=6.5, bot_peg="snap", snap_dia=7.65, for_printing=True):
    if screw_m not in SCREW_SPECS:
        raise ValueError(f"Unsupported screw size: {screw_m}")
    spec = SCREW_SPECS[screw_m]
    screw_d, nut_thick = spec["clear"], spec["nut_thick"]

    width = units * UNIT_WIDTH
    top_screw_y = TOP_RIDGE_Y
    bottom_screw_y = get_bottom_ridge_y(rail_height)
    top_y = BACKPLATE_TOP_Y
    bottom_y = get_bottom_edge_y(rail_height)
    plate_thickness = 6.0

    # 1. Baseplate + v2.0 shallow ridges extruded in one BRep operation on YZ
    pts = (
        [(top_y, 0.0)]
        + get_ridge_points(top_screw_y)
        + get_ridge_points(bottom_screw_y)
        + [
            (bottom_y, 0.0),
            (bottom_y, plate_thickness),
            (top_y, plate_thickness),
        ]
    )

    # 45-degree side chamfer profiles on >Y face (Local X = ±Global X, Local Y = Global Z)
    right_cut_pts = [
        (width / 2.0, plate_thickness),
        (width / 2.0 - 20.0, plate_thickness - 20.0),
        (width / 2.0 + 20.0, plate_thickness - 20.0),
        (width / 2.0 + 20.0, plate_thickness),
    ]
    left_cut_pts = [
        (-width / 2.0, plate_thickness),
        (-width / 2.0 + 20.0, plate_thickness - 20.0),
        (-width / 2.0 - 20.0, plate_thickness - 20.0),
        (-width / 2.0 - 20.0, plate_thickness),
    ]

    screw_pts = get_screw_points(units, rail_height)
    screw_hole_depth = RIDGE_HEIGHT + plate_thickness - 0.8

    adapter = (
        cq.Workplane("YZ")
        .polyline(pts)
        .close()
        .extrude(width / 2.0, both=True)
        # Cut 45-degree printability chamfers on left and right edges
        .faces(">Y")
        .workplane(centerOption="ProjectedOrigin")
        .polyline(right_cut_pts)
        .close()
        .polyline(left_cut_pts)
        .close()
        .cutThruAll()
        # Drill blind screw holes from the ridge crest plane (-RIDGE_HEIGHT) into +Z
        .faces("<Z")
        .workplane(centerOption="ProjectedOrigin")
        .pushPoints([(-x, y) for x, y in screw_pts])
        .hole(screw_d, screw_hole_depth)
    )

    # 2. Pegboard Hooks
    top_hook_y = 5.5
    clear_bottom = bottom_screw_y + 15.0
    available_space = top_hook_y - clear_bottom
    num_spaces = max(1, int(available_space / 25.4))
    peg_vertical_spacing = num_spaces * 25.4
    bottom_peg_y = top_hook_y - peg_vertical_spacing

    bot_peg_dia = 6.5
    num_hooks = units
    hook_span = (num_hooks - 1) * 25.4
    embed_z = plate_thickness / 2.0

    for i in range(num_hooks):
        x = -hook_span / 2.0 + i * 25.4

        if top_hook == "arc":
            R = 17.5
            end_y = R - R * math.cos(math.radians(45))
            end_z = R * math.sin(math.radians(45))
            path = cq.Workplane("YZ").center(top_hook_y, plate_thickness).moveTo(0, 0).radiusArc((end_y, end_z), R)
            arc_hook = cq.Workplane("XY").workplane(offset=plate_thickness).center(x, top_hook_y).circle(top_hook_dia / 2.0).sweep(path)
            embed_cyl = cq.Solid.makeCylinder(top_hook_dia / 2.0, plate_thickness - embed_z, cq.Vector(x, top_hook_y, embed_z), cq.Vector(0, 0, 1))
            sph = cq.Solid.makeSphere(top_hook_dia / 2.0, cq.Vector(x, top_hook_y + end_y, plate_thickness + end_z), cq.Vector(0, 0, 1), -90)
            adapter = adapter.union(arc_hook).union(cq.Workplane(embed_cyl)).union(cq.Workplane(sph))
        elif top_hook == "snap":
            p0 = cq.Vector(x, top_hook_y, plate_thickness)
            snap_peg = create_snap_fit_peg_parameterized(p0, num_petals=3, band_dia=snap_dia)
            snap_embed = cq.Solid.makeCylinder(bot_peg_dia / 2.0, plate_thickness - embed_z, cq.Vector(x, top_hook_y, embed_z), cq.Vector(0, 0, 1))
            adapter = adapter.union(snap_peg).union(cq.Workplane(snap_embed))

        if bot_peg == "solid":
            bot_p0 = cq.Vector(x, bottom_peg_y, embed_z)
            bot_dir = cq.Vector(0, 0, 1)
            bot_L = (plate_thickness - embed_z) + 5.0
            bot_p1 = bot_p0 + bot_dir * bot_L
            bot_cyl = cq.Solid.makeCylinder(bot_peg_dia / 2.0, bot_L, bot_p0, bot_dir)
            bot_sph = cq.Solid.makeSphere(bot_peg_dia / 2.0, bot_p1, cq.Vector(0, 0, 1), -90)
            adapter = adapter.union(cq.Workplane(bot_cyl)).union(cq.Workplane(bot_sph))
        elif bot_peg == "snap":
            p0 = cq.Vector(x, bottom_peg_y, plate_thickness)
            snap_peg = create_snap_fit_peg_parameterized(p0, num_petals=3, band_dia=snap_dia)
            snap_embed = cq.Solid.makeCylinder(bot_peg_dia / 2.0, plate_thickness - embed_z, cq.Vector(x, bottom_peg_y, embed_z), cq.Vector(0, 0, 1))
            adapter = adapter.union(snap_peg).union(cq.Workplane(snap_embed))

    # 3. Nut slots
    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    slot_z_center = 2.0 + slot_t / 2.0
    depth_top = top_y - top_screw_y
    depth_bot = bottom_screw_y - bottom_y

    slot_top_proto = create_nut_slot(screw_m, depth=depth_top, push_hole=True, push_hole_angle=30.0)
    slot_bot_proto = create_nut_slot(screw_m, depth=depth_bot, push_hole=True, push_hole_angle=30.0).moved(
        cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180)
    )

    nut_cutters = []
    for i in range(units):
        x = -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH
        nut_cutters.append(slot_top_proto.moved(cq.Location(cq.Vector(x, top_screw_y, slot_z_center))))
        nut_cutters.append(slot_bot_proto.moved(cq.Location(cq.Vector(x, bottom_screw_y, slot_z_center))))

    if nut_cutters:
        adapter = adapter.cut(cq.Compound.makeCompound(nut_cutters))

    if not for_printing:
        return adapter

    # 4. Orient 45 degrees around Y for printing on the right chamfered edge
    sin45 = math.sin(math.radians(45))
    z_shift = (width / 2.0 - plate_thickness) * sin45
    adapter = adapter.rotate((0, 0, 0), (0, 1, 0), 45).translate((0, 0, z_shift))

    if units >= 2:
        fin_H = (width - 2.0 * plate_thickness) * sin45
        fin = support_fin(z_gap=0.0, is_right=True, length=fin_H, height=fin_H, fin_width=1.6).rotate((0, 0, 0), (0, 0, 1), 90)
        fin_base_x = (width / 2.0 - plate_thickness) * sin45
        fin_top = fin.translate((fin_base_x, top_y - 0.2, 0)).val()
        fin_bot = fin.translate((fin_base_x, bottom_y + 0.2, 0)).val()
        adapter = adapter.union(cq.Compound.makeCompound([fin_top, fin_bot]))

    return adapter

def main():
    parser = argparse.ArgumentParser(description="Generate Pegboard adapter for groove tool holders")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--rail-height", type=float, default=73.0, help="French cleat height in mm")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size")
    parser.add_argument("--generate-all", action="store_true", help="Generate all requested configurations (1U-4U, Arc+Snap & Snap+Snap)")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")

    args = parser.parse_args()

    if args.generate_all:
        configs = [
            ("arc", 6.5, "snap", 7.65),
            ("snap", 7.65, "snap", 7.65),
        ]
        for units in [1, 2, 3, 4]:
            for th_type, th_dia, bp_type, bp_dia in configs:
                cad_adapter = create_adapter(units, args.rail_height, args.screw, top_hook=th_type, top_hook_dia=th_dia, bot_peg=bp_type, snap_dia=bp_dia, for_printing=False)
                print_adapter = create_adapter(units, args.rail_height, args.screw, top_hook=th_type, top_hook_dia=th_dia, bot_peg=bp_type, snap_dia=bp_dia, for_printing=True)
                name_modifier = "arc_snap" if th_type == "arc" else "snap_snap"
                filename = f"pegboard_adapter_{units}u_H{args.rail_height}_{args.screw}_{name_modifier}.stl"
                export_model(print_adapter, filename, print_orientation="face_down", category="pegboard", export=args.export, step_shape=cad_adapter)
    else:
        cad_adapter = create_adapter(args.units, args.rail_height, args.screw, top_hook="arc", top_hook_dia=6.5, bot_peg="snap", snap_dia=7.65, for_printing=False)
        print_adapter = create_adapter(args.units, args.rail_height, args.screw, top_hook="arc", top_hook_dia=6.5, bot_peg="snap", snap_dia=7.65, for_printing=True)
        filename = f"pegboard_adapter_{args.units}u_H{args.rail_height}_{args.screw}_arc_snap.stl"
        export_model(print_adapter, filename, print_orientation="face_down", category="pegboard", export=args.export, step_shape=cad_adapter)

if __name__ == "__main__":
    main()
