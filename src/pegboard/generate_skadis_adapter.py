import argparse
import os
import sys
import math
import cadquery as cq

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import export_stl, create_nut_slot

# Print orientation constants:
# Modeled flat: back face at Z = plate_thickness, hooks pointing into +Z.
# Rotated 45 degrees about (0, -1, 0) so the chamfered side face lies flat on Z = 0.
PRINT_AXIS_END = cq.Vector(0, -1, 0)
PRINT_ANGLE = 45.0

CUP_GAP = 0.25      # Clearance between the hook and the support cup
SUP_WIDTH = 6.0     # Width of vertical pillar along print X
SCOOP_RIM = 0.6     # Wall thickness around scooped contact patch
SCOOP_DEPTH = 2.0   # Vertical depth of the pyramid cutout scoop


def _to_print(shape, dz):
    """Apply the print-orientation transform to a cq.Shape."""
    return shape.rotate(cq.Vector(0, 0, 0), PRINT_AXIS_END, PRINT_ANGLE).translate(cq.Vector(0, 0, dz))


def _pt(x, y, z, dz):
    """Transform a model-space point into print space."""
    return _to_print(cq.Vertex.makeVertex(x, y, z), dz).Center()


def _dir(x, y, z):
    """Transform a model-space direction into print space."""
    return _pt(x, y, z, 0) - _pt(0, 0, 0, 0)


def _halfspace_below(point, normal, size=400.0):
    """Solid occupying the side of the plane opposite to `normal`."""
    n = normal.normalized()
    a = cq.Vector(0, 1, 0) if abs(n.y) < 0.9 else cq.Vector(1, 0, 0)
    xdir = a.cross(n).normalized()
    plane = cq.Plane(origin=point, xDir=xdir, normal=n)
    return cq.Workplane(plane).rect(size, size).extrude(-size).val()


def _make_hook_support(hook_x, hook_y, hook_dia, plate_thickness, stem_length, bend_r, drop_length, dz, gap=0.2):
    """
    Build a pyramid-scooped breakaway support for a single 90-degree hook in print space.
    """
    r = hook_dia / 2.0
    hook_z = plate_thickness + stem_length + bend_r
    y_tip = hook_y - bend_r - drop_length
    y0 = y_tip - 1.0
    y1 = hook_y - r - CUP_GAP

    # Hook clearance cutter (stem + drop + tip, grown by CUP_GAP)
    cut_r = r + CUP_GAP
    stem_c = cq.Solid.makeCylinder(cut_r, hook_z - plate_thickness + cut_r,
                                   cq.Vector(hook_x, hook_y, plate_thickness), cq.Vector(0, 0, 1))
    drop_c = cq.Solid.makeCylinder(cut_r, hook_y - y_tip, cq.Vector(hook_x, hook_y, hook_z), cq.Vector(0, -1, 0))
    tip_c = cq.Solid.makeSphere(cut_r, cq.Vector(hook_x, y_tip, hook_z), cq.Vector(0, 0, 1), -90, 90, 360)
    hook_cut = _to_print(stem_c.fuse(drop_c).fuse(tip_c), dz)

    # Everything within `gap` of the back face (model space Z < plate_thickness + gap)
    plate_cut = _to_print(cq.Solid.makeBox(400, 400, 400, cq.Vector(-200, -200, plate_thickness + gap - 400)), dz)
    # Everything below the build plate
    bed_cut = cq.Solid.makeBox(400, 400, 400, cq.Vector(-200, -200, -400))

    # Vertical pillar under the hook drop
    hc = _pt(hook_x, 0, hook_z, dz)
    xh, zh = hc.x, hc.z
    z_top = zh - r * math.sin(math.radians(45))
    w = SUP_WIDTH
    pillar = cq.Solid.makeBox(w, y1 - y0, z_top + 5.0, cq.Vector(xh - w / 2.0, y0, -5.0))
    pillar = pillar.cut(plate_cut).cut(bed_cut).cut(hook_cut)

    # Base plane (offset back face) in print space
    n_b = _dir(0, 0, 1)
    s = -n_b.x / n_b.z
    b0 = _pt(hook_x, 0, plate_thickness + gap, dz)
    x0, z0 = b0.x, b0.z

    def base(x):
        return z0 + s * (x - x0)

    t = SCOOP_RIM
    x_hi = xh + s * w / 2.0
    x_lo = xh - s * w / 2.0
    xa, xb = sorted([x_lo + s * t, x_hi - s * t])
    inner = cq.Solid.makeBox(xb - xa, (y1 - y0) - 2 * t, 80.0, cq.Vector(xa, y0 + t, -20.0))

    xr = x_hi - s * t
    roof_hi = _halfspace_below(cq.Vector(xr, 0, base(xr)), cq.Vector(s, 0, 1))
    cap = _halfspace_below(cq.Vector(x0, 0, z0 + SCOOP_DEPTH), n_b)
    roof_y0 = _halfspace_below(cq.Vector(x0, y0 + t, z0), cq.Vector(-s, -1, 1))
    roof_y1 = _halfspace_below(cq.Vector(x0, y1 - t, z0), cq.Vector(-s, 1, 1))

    cavity = inner.intersect(roof_hi).intersect(cap).intersect(roof_y0).intersect(roof_y1)
    pillar = pillar.cut(cavity)

    return pillar


def create_skadis_adapter(units=2, rail_height=73.0, screw_m="M3", hook_dia=4.8, stem_length=5.0, drop_length=5.0):
    unit_width = 28.0
    width = units * unit_width

    if screw_m == "M3":
        screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
    elif screw_m == "M4":
        screw_d, nut_waf, nut_thick = 4.5, 7.0, 3.2
    elif screw_m == "M5":
        screw_d, nut_waf, nut_thick = 5.5, 8.0, 4.0
    else:
        raise ValueError(f"Unsupported screw size: {screw_m}")

    top_screw_y = 10.0
    bottom_screw_y = -rail_height - 1.0 - 10.0  # play = 1.0

    top_y = 20.0
    bottom_y = bottom_screw_y - 10.0

    plate_thickness = 6.0

    # Base Plate
    adapter = (
        cq.Workplane("XY")
        .box(width, top_y - bottom_y, plate_thickness)
        .translate((0, (top_y + bottom_y) / 2.0, plate_thickness / 2.0))
    )

    # Ridges on the Z=0 face pointing into -Z
    ridge_depth = 4.0

    def add_ridge(adapter_obj, y_center):
        pts = [
            (y_center + 4, 0),
            (y_center + 2, -ridge_depth),
            (y_center - 2, -ridge_depth),
            (y_center - 4, 0)
        ]
        ridge = (
            cq.Workplane("YZ")
            .polyline(pts).close()
            .extrude(width)
            .translate((-width / 2, 0, 0))
        )
        return adapter_obj.union(ridge)

    adapter = add_ridge(adapter, top_screw_y)
    adapter = add_ridge(adapter, bottom_screw_y)

    # Skadis Vertical Coordinates:
    # Top hook at 5.5. Skadis vertical pitch between slots is 40.0mm.
    # 2 slots down = 80mm spacing.
    top_hook_y = 5.5
    bottom_peg_y = top_hook_y - 80.0

    # Skadis Horizontal Placement:
    # 1u (28mm): 1 hook at x=0
    # 2u (56mm): 2 hooks at x = [-20.0, 20.0] (40mm pitch)
    # 3u (84mm): 3 hooks at x = [-40.0, 0.0, 40.0] (40mm pitch)
    # 4u (112mm): 3 hooks centered at x = [-40.0, 0.0, 40.0]
    if units == 1:
        hook_x_positions = [0.0]
    elif units == 2:
        hook_x_positions = [-20.0, 20.0]
    elif units == 3:
        hook_x_positions = [-40.0, 0.0, 40.0]
    elif units == 4:
        hook_x_positions = [-40.0, 0.0, 40.0]
    else:
        num_hooks = max(1, int(width / 40.0))
        hook_span = (num_hooks - 1) * 40.0
        hook_x_positions = [-hook_span / 2.0 + i * 40.0 for i in range(num_hooks)]

    embed_z = plate_thickness / 2.0
    bend_r = 2.5

    for x in hook_x_positions:
        # Top 90-degree hook (pointing down into -Y)
        stem = cq.Solid.makeCylinder(hook_dia / 2.0, stem_length, cq.Vector(x, top_hook_y, plate_thickness), cq.Vector(0, 0, 1))
        circle_90 = cq.Workplane("XY").center(x, top_hook_y).workplane(offset=plate_thickness + stem_length).circle(hook_dia / 2.0)
        bend = circle_90.revolve(90, (0, -bend_r, 0), (1, -bend_r, 0))
        drop = cq.Solid.makeCylinder(hook_dia / 2.0, drop_length,
                                     cq.Vector(x, top_hook_y - bend_r, plate_thickness + stem_length + bend_r), cq.Vector(0, -1, 0))
        end_sph = cq.Solid.makeSphere(hook_dia / 2.0,
                                      cq.Vector(x, top_hook_y - bend_r - drop_length, plate_thickness + stem_length + bend_r),
                                      cq.Vector(0, 0, 1), -90, 90, 360)
        top_embed = cq.Solid.makeCylinder(hook_dia / 2.0, plate_thickness - embed_z + 0.1, cq.Vector(x, top_hook_y, embed_z), cq.Vector(0, 0, 1))
        top_hook = (cq.Workplane(stem).union(bend).union(cq.Workplane(drop))
                    .union(cq.Workplane(end_sph)).union(cq.Workplane(top_embed)))

        # Bottom alignment peg (straight standoff cylinder)
        bot_peg_L = (plate_thickness - embed_z) + 5.0
        bot_peg = cq.Solid.makeCylinder(hook_dia / 2.0, bot_peg_L, cq.Vector(x, bottom_peg_y, embed_z), cq.Vector(0, 0, 1))
        bot_sph = cq.Solid.makeSphere(hook_dia / 2.0, cq.Vector(x, bottom_peg_y, plate_thickness + 5.0), cq.Vector(0, 0, 1), -90, 90, 360)
        bot_peg_full = cq.Workplane(bot_peg).union(cq.Workplane(bot_sph))

        adapter = adapter.union(top_hook).union(bot_peg_full)

    # Nut slots and screw holes
    slot_t = nut_thick + 0.1
    slot_z_center = 2.0 + slot_t / 2.0

    for i in range(units):
        x = -width / 2 + unit_width / 2 + i * unit_width
        screw_hole_len = 10.0 + plate_thickness - 0.8

        # Top screw hole
        hole_top = cq.Workplane("XY").workplane(offset=-10).center(x, top_screw_y).circle(screw_d / 2).extrude(screw_hole_len)
        adapter = adapter.cut(hole_top)

        # Top nut slot
        depth_top = top_y - top_screw_y
        slot_top_solid = create_nut_slot(screw_m, depth=depth_top, push_hole=True, push_hole_angle=30.0)
        slot_top_solid = slot_top_solid.translate(cq.Vector(x, top_screw_y, slot_z_center))
        adapter = adapter.cut(cq.Workplane(slot_top_solid))

        # Bottom screw hole
        hole_bot = cq.Workplane("XY").workplane(offset=-10).center(x, bottom_screw_y).circle(screw_d / 2).extrude(screw_hole_len)
        adapter = adapter.cut(hole_bot)

        # Bottom nut slot
        depth_bot = bottom_screw_y - bottom_y
        slot_bot_solid = create_nut_slot(screw_m, depth=depth_bot, push_hole=True, push_hole_angle=30.0)
        slot_bot_solid = cq.Workplane(slot_bot_solid).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180).val()
        slot_bot_solid = slot_bot_solid.translate(cq.Vector(x, bottom_screw_y, slot_z_center))
        adapter = adapter.cut(cq.Workplane(slot_bot_solid))

    # Add 45 degree chamfer to left and right sides for printability
    right_cut_pts = [
        (width / 2, plate_thickness),
        (width / 2 - 50, plate_thickness - 50),
        (width / 2 + 50, plate_thickness - 50),
        (width / 2 + 50, plate_thickness)
    ]
    right_cutter = cq.Workplane("XZ").polyline(right_cut_pts).close().extrude(1000, both=True)

    left_cut_pts = [
        (-width / 2, plate_thickness),
        (-width / 2 + 50, plate_thickness - 50),
        (-width / 2 - 50, plate_thickness - 50),
        (-width / 2 - 50, plate_thickness)
    ]
    left_cutter = cq.Workplane("XZ").polyline(left_cut_pts).close().extrude(1000, both=True)

    adapter = adapter.cut(right_cutter).cut(left_cutter).val()

    # Transform into final print orientation resting flat on Z=0
    rotated = _to_print(adapter, 0.0)
    dz = -rotated.BoundingBox().zmin
    adapter_p = rotated.translate(cq.Vector(0, 0, dz))

    # Generate 0.2mm pyramid-scoop supports for each hook
    supports = []
    for x in hook_x_positions:
        sup = _make_hook_support(x, top_hook_y, hook_dia, plate_thickness, stem_length, bend_r, drop_length, dz, gap=0.2)
        supports.append(sup)

    # Return as compound so slicer handles supports as separate bodies
    all_solids = [adapter_p] + supports
    return cq.Workplane(cq.Compound.makeCompound(all_solids))


def main():
    parser = argparse.ArgumentParser(description="Generate IKEA Skadis adapter for groove tool holders")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide (1 to 4)")
    parser.add_argument("--rail-height", type=float, default=73.0, help="French cleat height in mm")
    parser.add_argument("--screw", type=str, default="M3", help="Screw size")
    parser.add_argument("--generate-all", action="store_true", help="Generate 1U through 4U mounts")

    args = parser.parse_args()

    if args.generate_all:
        for u in [1, 2, 3, 4]:
            adapter = create_skadis_adapter(units=u, rail_height=args.rail_height, screw_m=args.screw)
            filename = f"skadis_adapter_{u}u_H{args.rail_height}_{args.screw}.stl"
            export_stl(adapter, filename, print_orientation='face_down', category='pegboard')
            print(f"Exported {filename}")
    else:
        adapter = create_skadis_adapter(units=args.units, rail_height=args.rail_height, screw_m=args.screw)
        filename = f"skadis_adapter_{args.units}u_H{args.rail_height}_{args.screw}.stl"
        export_stl(adapter, filename, print_orientation='face_down', category='pegboard')
        print(f"Exported {filename}")


if __name__ == "__main__":
    main()
