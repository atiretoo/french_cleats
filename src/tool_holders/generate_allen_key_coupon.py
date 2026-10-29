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
    BACKPLATE_THICKNESS,
    export_model,
)

def create_allen_key_coupon(
    units=2,
    shelf_depth=30.0,
    shelf_thickness=2.0,
    backplate_thickness=2.0,
    hook_width=2.0,
    hook_height_above_shelf=48.0,
    hook_lip_height=8.0,
    slot_across=42.0,
    slot_deep=17.0,
    slot_corner_radius=2.5,
):
    """
    Creates a lightweight test coupon for the Allen Key Holder to verify
    critical fit dimensions (slot size, shelf depth, hook height and lip).

    Coupon specifications:
    - Shelf: thinned to 2.0mm, unfilleted, full 2U width (56mm), 30mm depth.
    - Slot: flat ends with small corner radius fillets to preserve full depth
      across the entire width (default 42.0mm across x 17.0mm deep with 2.5mm corner fillets).
    - Hook: thinned to 2.0mm width on the left side, top surface 48.0mm above shelf top.
    - Backplate: thinned to 2.0mm, spans full 56mm width at the shelf, and reduces to
      the hook width (2.0mm) for the vertical spine joining the shelf to the hook.
    - Rotated -90 degrees around Y-axis so the left face rests flat on the print bed.
    """
    width = units * UNIT_WIDTH

    # Coordinate references matching full holder:
    # Front face of backplate at Z = -BACKPLATE_THICKNESS (-11.0mm)
    back_z = -BACKPLATE_THICKNESS
    back_rear_z = back_z + backplate_thickness

    shelf_bot = -56.0
    shelf_top = shelf_bot + shelf_thickness
    hook_top = shelf_top + hook_height_above_shelf

    # 1. Shelf (2mm thick, no fillet)
    shelf_pts = [
        (shelf_bot, back_z),
        (shelf_bot, back_z - shelf_depth),
        (shelf_top, back_z - shelf_depth),
        (shelf_top, back_z),
    ]
    shelf = (
        cq.Workplane("YZ", origin=(-width / 2.0, 0, 0))
        .polyline(shelf_pts).close()
        .extrude(width)
    )

    # 2. Backplate:
    # Full width at the shelf (spanning shelf_bot to shelf_top + 3mm for stiffness)
    bp_shelf_pts = [
        (shelf_bot - 2.0, back_rear_z),
        (shelf_bot - 2.0, back_z),
        (shelf_top + 3.0, back_z),
        (shelf_top + 3.0, back_rear_z),
    ]
    bp_shelf = (
        cq.Workplane("YZ", origin=(-width / 2.0, 0, 0))
        .polyline(bp_shelf_pts).close()
        .extrude(width)
    )

    # Vertical spine: width of hook (2mm) connecting shelf to hook
    bp_spine_pts = [
        (shelf_top, back_rear_z),
        (shelf_top, back_z),
        (hook_top + hook_lip_height, back_z),
        (hook_top + hook_lip_height, back_rear_z),
    ]
    bp_spine = (
        cq.Workplane("YZ", origin=(-width / 2.0, 0, 0))
        .polyline(bp_spine_pts).close()
        .extrude(hook_width)
    )

    # 3. Hook on the left side (2mm wide)
    hook_front_z = back_z - shelf_depth + 2.0
    hook_cradle_front_z = hook_front_z + 4.0
    hook_arm_thickness = 2.5
    hook_pts = [
        (hook_top - 10.0, back_z),
        (hook_top - hook_arm_thickness, hook_front_z),
        (hook_top + hook_lip_height, hook_front_z),
        (hook_top + hook_lip_height, hook_cradle_front_z),
        (hook_top, hook_cradle_front_z),
        (hook_top, back_z),
    ]
    hook = (
        cq.Workplane("YZ", origin=(-width / 2.0, 0, 0))
        .polyline(hook_pts).close()
        .extrude(hook_width)
    )
    front_edges = [
        e for e in hook.edges("|X").vals() if e.BoundingBox().zmax < (back_z - 0.5)
    ]
    if front_edges:
        hook = hook.newObject(front_edges).fillet(1.0)

    coupon = shelf.union(bp_shelf).union(bp_spine).union(hook)

    # 4. Rectangular slot with flat ends and small corner radius fillets
    z_center = back_z - shelf_depth / 2.0
    slot = (
        cq.Workplane("ZX", origin=(0, shelf_bot - 4.0, 0))
        .center(z_center, 0.0)
        .rect(slot_deep, slot_across)
        .extrude(shelf_thickness + 8.0)
    )
    if slot_corner_radius > 0:
        slot = slot.edges("|Y").fillet(slot_corner_radius)
    coupon = coupon.cut(slot)

    # 5. Rotate -90 degrees around Y axis (same orientation as full tool holder)
    coupon = coupon.rotate((0, 0, 0), (0, 1, 0), -90)

    return coupon, units

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat Allen Key Tool Holder Test Coupon")
    parser.add_argument("--units", type=int, default=2, help="Width in units (default: 2, 56mm)")
    parser.add_argument("--shelf-depth", type=float, default=30.0, help="Shelf depth in mm (default: 30.0)")
    parser.add_argument("--shelf-thickness", type=float, default=2.0, help="Coupon shelf thickness in mm (default: 2.0)")
    parser.add_argument("--backplate-thickness", type=float, default=2.0, help="Coupon backplate thickness in mm (default: 2.0)")
    parser.add_argument("--hook-width", type=float, default=2.0, help="Coupon hook width in mm (default: 2.0)")
    parser.add_argument("--hook-height", type=float, default=48.0, help="Hook top surface height above shelf top in mm (default: 48.0)")
    parser.add_argument("--slot-across", type=float, default=42.0, help="Slot width across X in mm (default: 42.0)")
    parser.add_argument("--slot-deep", type=float, default=17.0, help="Slot depth along Z in mm (default: 17.0)")
    parser.add_argument("--slot-corner-radius", type=float, default=2.5, help="Corner radius of slot fillets in mm (default: 2.5)")
    parser.add_argument(
        "--print-orientation",
        type=str,
        default="none",
        choices=["none", "left_down", "right_down", "top_down", "bottom_down", "back_down", "face_down"],
        help="Print orientation for STL export (default: none, already rotated)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default="both",
        choices=["both", "stl", "step"],
        help="Export format (default: both)",
    )
    args = parser.parse_args()

    coupon, units = create_allen_key_coupon(
        units=args.units,
        shelf_depth=args.shelf_depth,
        shelf_thickness=args.shelf_thickness,
        backplate_thickness=args.backplate_thickness,
        hook_width=args.hook_width,
        hook_height_above_shelf=args.hook_height,
        slot_across=args.slot_across,
        slot_deep=args.slot_deep,
        slot_corner_radius=args.slot_corner_radius,
    )

    filename = f"allen_key_holder_{units}u_coupon.stl"
    export_model(
        coupon,
        filename,
        category="tool_holders",
        export=args.export,
        print_orientation=args.print_orientation,
    )

if __name__ == "__main__":
    main()
