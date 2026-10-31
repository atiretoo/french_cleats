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
    UNIT_WIDTH, export_model, create_nut_slot, MULTICONNECT_ASSETS_DIR,
    get_ridge_points, get_screw_points, get_bottom_ridge_y, get_bottom_edge_y,
    BACKPLATE_TOP_Y, TOP_RIDGE_Y, NUT_SLOT_TOLERANCE, SCREW_SPECS
)

def load_mc_block(filename, opengrid_path=None):
    if opengrid_path is None:
        opengrid_path = MULTICONNECT_ASSETS_DIR
    path = os.path.join(opengrid_path, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Multiconnect asset not found at: {path}")
    model = cq.importers.importStep(path).val()
    bb = model.BoundingBox()
    dx = -(bb.xmin + bb.xmax) / 2.0
    dy = -(bb.ymin + bb.ymax) / 2.0
    # We want the solid back (zmin of original) to be at Z=0
    # And the slot opening to be at Z=6.4 (facing the wall)
    dz = -bb.zmin
    return model.translate((dx, dy, dz))

def create_adapter(units=2, rail_height=73.0, screw_m="M3", opengrid_path=None):
    if opengrid_path is None:
        opengrid_path = MULTICONNECT_ASSETS_DIR

    if screw_m not in SCREW_SPECS:
        raise ValueError(f"Unsupported screw size: {screw_m}")
    spec = SCREW_SPECS[screw_m]
    screw_d, nut_thick = spec["clear"], spec["nut_thick"]

    width = units * UNIT_WIDTH
    top_screw_y = TOP_RIDGE_Y
    bottom_screw_y = get_bottom_ridge_y(rail_height)
    top_y = BACKPLATE_TOP_Y
    bottom_y = get_bottom_edge_y(rail_height)

    num_rows = max(1, int(rail_height / 28))
    stack_height = num_rows * 28.0 + 14.0
    stack_center_y = (top_screw_y + bottom_screw_y) / 2.0
    stack_top_y = stack_center_y + stack_height / 2.0
    stack_bot_y = stack_center_y - stack_height / 2.0

    try:
        top_block = load_mc_block("top-back.step", opengrid_path)
        mid_block = load_mc_block("raw-slot-back.step", opengrid_path)
        bot_block = load_mc_block("embed-back-end.step", opengrid_path)
        cutter = load_mc_block("slot-opening.step", opengrid_path).translate((0, 0, 6.4 - 4.15))
    except Exception as e:
        print(f"Error loading Multiconnect STEP files from {opengrid_path}: {e}")
        print("Please ensure the path is correct or pass it via --opengrid-path.")
        return cq.Workplane("XY")

    mc_solids = []
    cut_solids = []
    for c in range(units):
        x_center = -width / 2.0 + 14.0 + c * 28.0

        y_top_block = stack_top_y - 14.0
        mc_solids.append(top_block.moved(cq.Location(cq.Vector(x_center, y_top_block, 0))))

        for r in range(1, num_rows):
            y_mid_block = stack_top_y - 14.0 - r * 28.0
            mc_solids.append(mid_block.moved(cq.Location(cq.Vector(x_center, y_mid_block, 0))))

        y_bot_block = stack_top_y - num_rows * 28.0 - 7.0
        mc_solids.append(bot_block.moved(cq.Location(cq.Vector(x_center, y_bot_block, 0))))

        for r in range(1, num_rows + 1):
            opening_y = stack_top_y - r * 28.0
            cut_solids.append(cutter.moved(cq.Location(cq.Vector(x_center, opening_y, 0))))

    # Fuse the multiconnect column blocks and cut the slot openings
    adapter = cq.Workplane("XY")
    for solid in mc_solids:
        adapter = adapter.union(cq.Workplane(solid))
    if cut_solids:
        adapter = adapter.cut(cq.Compound.makeCompound(cut_solids))

    # Fill the gaps above and below the stack and add v2.0 locking ridges on YZ
    extra_solids = []
    if top_y > stack_top_y:
        gap_height = top_y - stack_top_y
        gap_center_y = stack_top_y + gap_height / 2.0
        extra_solids.append(cq.Workplane("XY", origin=(0, gap_center_y, 3.2)).box(width, gap_height, 6.4).val())

    if bottom_y < stack_bot_y:
        gap_height = stack_bot_y - bottom_y
        gap_center_y = stack_bot_y - gap_height / 2.0
        extra_solids.append(cq.Workplane("XY", origin=(0, gap_center_y, 3.2)).box(width, gap_height, 6.4).val())

    top_ridge = cq.Workplane("YZ").polyline(get_ridge_points(top_screw_y)).close().extrude(width / 2.0, both=True).val()
    bot_ridge = cq.Workplane("YZ").polyline(get_ridge_points(bottom_screw_y)).close().extrude(width / 2.0, both=True).val()
    extra_solids.extend([top_ridge, bot_ridge])

    adapter = adapter.union(cq.Compound.makeCompound(extra_solids))

    # Drill clearance screw holes through the adapter
    screw_pts = get_screw_points(units, rail_height)
    adapter = adapter.faces(">Z").workplane(centerOption="ProjectedOrigin").pushPoints(screw_pts).hole(screw_d)

    # Nut slots
    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    slot_z_center = 2.0 + slot_t / 2.0

    nut_cutters = []
    if units == 1:
        side_depth = width / 2.0
        slot_side_proto = create_nut_slot(screw_m, depth=side_depth, push_hole=True).moved(
            cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), -90)
        )
        nut_cutters.append(slot_side_proto.moved(cq.Location(cq.Vector(0, top_screw_y, slot_z_center))))
        nut_cutters.append(slot_side_proto.moved(cq.Location(cq.Vector(0, bottom_screw_y, slot_z_center))))
    else:
        depth_top = top_y - top_screw_y
        depth_bot = bottom_screw_y - bottom_y
        slot_top_proto = create_nut_slot(screw_m, depth=depth_top, push_hole=True, push_hole_angle=-30.0)
        slot_bot_proto = create_nut_slot(screw_m, depth=depth_bot, push_hole=True, push_hole_angle=-30.0).moved(
            cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180)
        )
        for i in range(units):
            x = -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH
            nut_cutters.append(slot_top_proto.moved(cq.Location(cq.Vector(x, top_screw_y, slot_z_center))))
            nut_cutters.append(slot_bot_proto.moved(cq.Location(cq.Vector(x, bottom_screw_y, slot_z_center))))

    if nut_cutters:
        adapter = adapter.cut(cq.Compound.makeCompound(nut_cutters))

    return adapter

def main():
    parser = argparse.ArgumentParser(description="Generate OpenGrid adapter for groove tool holders")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--rail-height", type=float, default=73.0, help="French cleat height in mm")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size")
    parser.add_argument("--opengrid-path", type=str, default=None, help="Path to Multiconnect Modeling Files (optional)")
    parser.add_argument("--export", choices=["both", "stl", "step"], default="both", help="Export format (default: both)")

    args = parser.parse_args()

    adapter = create_adapter(args.units, args.rail_height, args.screw, args.opengrid_path)
    filename = f"opengrid_adapter_{args.units}u_H{args.rail_height}_{args.screw}.stl"

    export_model(adapter, filename, print_orientation="bottom_down", category="multiconnect", export=args.export)

if __name__ == "__main__":
    main()
