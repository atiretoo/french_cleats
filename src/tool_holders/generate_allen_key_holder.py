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
    create_baseplate,
    export_model,
)

def create_allen_key_holder(
    units=2,
    rail_height=DEFAULT_RAIL_HEIGHT,
    shelf_depth=30.0,
    shelf_thickness=5.0,
    slot_across=42.0,
    slot_deep=17.0,
    slot_corner_radius=2.5,
    hook_height_above_shelf=48.0,
    hook_width=6.0,
    hook_lip_height=8.0,
    hook_lip_thickness=5.0,
    brace_thickness=2.5,
    fillet_shelf=3.0,
):
    """
    Creates a French Cleat allen key holder (2U standard).

    Parameters:
    - units: Width in 28mm units (default: 2 -> 56mm wide)
    - rail_height: French cleat rail height (default: 73.0mm)
    - shelf_depth: Shelf depth projecting out from the front face (default: 30.0mm)
    - shelf_thickness: Vertical thickness of the shelf (default: 5.0mm)
    - slot_across: Slot width across X-axis (default: 42.0mm)
    - slot_deep: Slot depth along Z-axis (default: 17.0mm)
    - slot_corner_radius: Corner radius for flat-end rounded slot (default: 2.5mm)
    - hook_height_above_shelf: Vertical distance from shelf top to hook top surface (default: 48.0mm)
    - hook_width: Width of the hook along X-axis (default: 6.0mm)
    - hook_lip_height: Height of the retaining lip on the front of the hook (default: 8.0mm)
    - hook_lip_thickness: Thickness of the retaining lip along Z-axis (default: 5.0mm)
    - brace_thickness: Thickness of the triangular shelf support brace on the left side (default: 2.5mm)
    - fillet_shelf: Structural fillet radius at shelf-backplate junction (default: 3.0mm)
    """
    width = units * UNIT_WIDTH

    # 1. Baseplate with standard v2.0 shallow groove interface
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
        units=units, rail_height=rail_height, mount_type="groove", num_rows=2
    )

    # Shelf vertical placement: 1/3 up from the bottom of the baseplate
    total_height = top_y - bottom_y
    shelf_bot = bottom_y + total_height / 3.0
    shelf_top = shelf_bot + shelf_thickness

    # 2. Shelf: extruded along +X using the forward cyclic named plane "YZ"
    shelf_pts = [
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS - shelf_depth),
        (shelf_top, -BACKPLATE_THICKNESS),
    ]
    shelf = (
        cq.Workplane("YZ", origin=(-width / 2.0, 0, 0))
        .polyline(shelf_pts).close()
        .extrude(width)
    )
    tool_holder = tool_holder.union(shelf)

    # 3. Structural triangular brace on the LEFT side ONLY
    brace_pts = [
        (bottom_y, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS),
        (shelf_bot, -BACKPLATE_THICKNESS - shelf_depth),
    ]
    left_brace = (
        cq.Workplane("YZ", origin=(-width / 2.0, 0, 0))
        .polyline(brace_pts).close()
        .extrude(brace_thickness)
    )
    tool_holder = tool_holder.union(left_brace)

    # Fillet at the top junction where shelf meets the backplate
    if fillet_shelf > 0:
        class ShelfFilletSelector(cq.Selector):
            def filter(self, objectList):
                res = []
                for o in objectList:
                    if not isinstance(o, cq.Edge):
                        continue
                    b = o.BoundingBox()
                    if (
                        abs(b.ymin - shelf_top) < 0.5
                        and abs(b.zmin - (-BACKPLATE_THICKNESS)) < 0.5
                        and (b.xmax - b.xmin) > 10.0
                    ):
                        res.append(o)
                return res

        try:
            tool_holder = tool_holder.edges(ShelfFilletSelector()).fillet(fillet_shelf)
        except Exception:
            pass

    # 4. Hook on the LEFT side: top surface is exactly 48mm above the shelf top
    # The hook projects forward in -Z with an upward retaining lip to catch keys.
    hook_top = shelf_top + hook_height_above_shelf
    back_z = -BACKPLATE_THICKNESS
    hook_front_z = back_z - shelf_depth + 2.0  # e.g. -39.0mm
    hook_cradle_front_z = hook_front_z + hook_lip_thickness  # e.g. -34.0mm
    hook_arm_thickness = 5.0
    hook_gusset_drop = 15.0

    hook_pts = [
        (hook_top - hook_gusset_drop, back_z),
        (hook_top - hook_arm_thickness, hook_front_z),
        (hook_top + hook_lip_height, hook_front_z),
        (hook_top + hook_lip_height, hook_cradle_front_z),
        (hook_top, hook_cradle_front_z),
        (hook_top, back_z),
    ]

    hook_x_origin = -width / 2.0
    hook = (
        cq.Workplane("YZ", origin=(hook_x_origin, 0, 0))
        .polyline(hook_pts).close()
        .extrude(hook_width)
    )

    # Fillet front outer edges of the hook for smooth handling
    front_hook_edges = [
        e for e in hook.edges("|X").vals() if e.BoundingBox().zmax < (back_z - 0.5)
    ]
    if front_hook_edges:
        try:
            hook = hook.newObject(front_hook_edges).fillet(2.0)
        except Exception:
            pass

    tool_holder = tool_holder.union(hook)

    # 5. Rectangular slot with flat ends and small corner radius fillets:
    # Preserves full depth across the entire width so side-by-side tools on the ends fit.
    z_center = -BACKPLATE_THICKNESS - shelf_depth / 2.0
    slot = (
        cq.Workplane("ZX", origin=(0, shelf_bot - 2.0, 0))
        .center(z_center, 0.0)
        .rect(slot_deep, slot_across)
        .extrude(shelf_thickness + 4.0)
    )
    if slot_corner_radius > 0:
        slot = slot.edges("|Y").fillet(slot_corner_radius)
    tool_holder = tool_holder.cut(slot)

    # 6. Cleat mounting screw holes & counterbores
    if screw_pts:
        screws = (
            cq.Workplane("XY").workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6 / 2.0)
            .extrude(-20.0)
        )
        tool_holder = tool_holder.cut(screws)

        recesses = (
            cq.Workplane("XY").workplane(offset=-8.0)
            .pushPoints(screw_pts)
            .circle(8.0 / 2.0)
            .extrude(-20.0)
        )
        tool_holder = tool_holder.cut(recesses)

    # 7. Rotate -90 degrees around Y axis so the left face (with triangular brace and hook)
    # is the lowest on the Z axis (ready for printing on its flat side).
    tool_holder = tool_holder.rotate((0, 0, 0), (0, 1, 0), -90)

    return tool_holder, units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Allen Key Tool Holder")
    parser.add_argument("--units", type=int, default=2, help="Width in units (default: 2, 56mm)")
    parser.add_argument("--rail-height", type=float, default=DEFAULT_RAIL_HEIGHT, help="Rail height in mm (default: 73.0)")
    parser.add_argument("--shelf-depth", type=float, default=30.0, help="Shelf depth projecting out in mm (default: 30.0)")
    parser.add_argument("--shelf-thickness", type=float, default=5.0, help="Shelf thickness in mm (default: 5.0)")
    parser.add_argument("--slot-across", type=float, default=42.0, help="Slot width across X in mm (default: 42.0)")
    parser.add_argument("--slot-deep", type=float, default=17.0, help="Slot depth along Z in mm (default: 17.0)")
    parser.add_argument("--slot-corner-radius", type=float, default=2.5, help="Corner radius of slot fillets in mm (default: 2.5)")
    parser.add_argument("--hook-height", type=float, default=48.0, help="Hook top surface height above shelf top in mm (default: 48.0)")
    parser.add_argument("--hook-width", type=float, default=6.0, help="Hook width along X in mm (default: 6.0)")
    parser.add_argument(
        "--print-orientation",
        type=str,
        default="none",
        choices=["none", "left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down"],
        help="Print orientation for STL export (default: none, already rotated with left side on bottom)",
    )
    parser.add_argument(
        "--coupon",
        action="store_true",
        help="Generate lightweight test coupon to test critical dimensions (shelf slot, hook height)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default="both",
        choices=["both", "stl", "step"],
        help="Export format (default: both)",
    )
    args = parser.parse_args()

    if args.coupon:
        from tool_holders.generate_allen_key_coupon import create_allen_key_coupon
        model, units = create_allen_key_coupon(
            units=args.units,
            shelf_depth=args.shelf_depth,
            hook_height_above_shelf=args.hook_height,
            slot_across=args.slot_across,
            slot_deep=args.slot_deep,
            slot_corner_radius=args.slot_corner_radius,
        )
        filename = f"allen_key_holder_{units}u_coupon.stl"
    else:
        model, units = create_allen_key_holder(
            units=args.units,
            rail_height=args.rail_height,
            shelf_depth=args.shelf_depth,
            shelf_thickness=args.shelf_thickness,
            slot_across=args.slot_across,
            slot_deep=args.slot_deep,
            slot_corner_radius=args.slot_corner_radius,
            hook_height_above_shelf=args.hook_height,
            hook_width=args.hook_width,
        )
        filename = f"allen_key_holder_{units}u_groove_H{int(args.rail_height)}.stl"

    export_model(
        model,
        filename,
        category="tool_holders",
        export=args.export,
        print_orientation=args.print_orientation,
    )

if __name__ == "__main__":
    main()
