import math
import sys

import cadquery as cq

sys.path.append('src')
from core_library import export_stl
from pegboard.coupon_utils import create_test_coupon_base

# ---------------------------------------------------------------------------
# Print orientation
# ---------------------------------------------------------------------------
# The coupon is modelled flat (back face at Z = plate_thickness, hooks pointing +Z),
# then rotated 45 deg about -Y so the chamfer lies on the bed. This is the rotation
# that was verified by hand in the slicer.
PRINT_AXIS_END = cq.Vector(0, -1, 0)
PRINT_ANGLE = 45.0

CUP_GAP = 0.25      # clearance between the hook and the support cup
SUP_WIDTH = 6.0     # width of the vertical pillar (print X)
SCOOP_RIM = 0.6     # wall thickness left around the scooped contact patch
SCOOP_DEPTH = 2.0   # vertical depth of the scoop (the "2 mm chamfers")


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


def _make_support(style, gap, hook_dia, plate_thickness, peg1_y, stem_length, bend_r, drop_length, dz):
    """
    Build a breakaway support for the 90-degree hook directly in print space.

    style:
      'square' - vertical pillar, flat base offset `gap` from the back face
      'scoop'  - vertical pillar with a pyramid-style scoop in the base so only a
                 thin rim approaches the back face (all cavity ceilings >= 45 deg)
      'angled' - bar that starts on the build plate (beside the coupon edge) and
                 rises at 45 deg parallel to the back face up to the hook
    """
    r = hook_dia / 2.0
    hook_z = plate_thickness + stem_length + bend_r      # hook drop axis height (model space)
    y_tip = peg1_y - bend_r - drop_length                # centre of the tip sphere
    y0 = y_tip - 1.0                                     # support start (a bit past the tip centre)
    y1 = peg1_y - r - CUP_GAP                            # support end (clear of the stem)

    # Hook clearance cutter (stem + drop + tip, each grown by CUP_GAP)
    cut_r = r + CUP_GAP
    stem_c = cq.Solid.makeCylinder(cut_r, hook_z - plate_thickness + cut_r,
                                   cq.Vector(0, peg1_y, plate_thickness), cq.Vector(0, 0, 1))
    drop_c = cq.Solid.makeCylinder(cut_r, peg1_y - y_tip, cq.Vector(0, peg1_y, hook_z), cq.Vector(0, -1, 0))
    tip_c = cq.Solid.makeSphere(cut_r, cq.Vector(0, y_tip, hook_z), cq.Vector(0, 0, 1), -90, 90, 360)
    hook_cut = _to_print(stem_c.fuse(drop_c).fuse(tip_c), dz)

    # Everything within `gap` of the back face (model space Z < plate_thickness + gap)
    plate_cut = _to_print(cq.Solid.makeBox(400, 400, 400, cq.Vector(-200, -200, plate_thickness + gap - 400)), dz)
    # Everything below the build plate
    bed_cut = cq.Solid.makeBox(400, 400, 400, cq.Vector(-200, -200, -400))

    if style == 'angled':
        # Which model-space X direction points down toward the bed in print space?
        sx = -1.0 if _dir(-1, 0, 0).z < 0 else 1.0
        x_start = -30.0 if sx < 0 else 0.0
        bar = cq.Solid.makeBox(30.0, y1 - y0, hook_z - (plate_thickness + gap),
                               cq.Vector(x_start, y0, plate_thickness + gap))
        return _to_print(bar, dz).cut(bed_cut).cut(hook_cut)

    # Vertical pillar under the hook drop
    hc = _pt(0, 0, hook_z, dz)
    xh, zh = hc.x, hc.z
    z_top = zh - r * math.sin(math.radians(45))          # cup wraps the bottom +/-45 deg of the hook
    w = SUP_WIDTH
    pillar = cq.Solid.makeBox(w, y1 - y0, z_top + 5.0, cq.Vector(xh - w / 2.0, y0, -5.0))
    pillar = pillar.cut(plate_cut).cut(bed_cut).cut(hook_cut)

    if style == 'scoop':
        # Base plane (offset back face) in print space: z = z0 + s * (x - x0)
        n_b = _dir(0, 0, 1)
        s = -n_b.x / n_b.z
        b0 = _pt(0, 0, plate_thickness + gap, dz)
        x0, z0 = b0.x, b0.z

        def base(x):
            return z0 + s * (x - x0)

        t = SCOOP_RIM
        x_hi = xh + s * w / 2.0          # edge where the base is highest
        x_lo = xh - s * w / 2.0          # edge where the base is lowest
        xa, xb = sorted([x_lo + s * t, x_hi - s * t])
        inner = cq.Solid.makeBox(xb - xa, (y1 - y0) - 2 * t, 80.0, cq.Vector(xa, y0 + t, -20.0))

        xr = x_hi - s * t
        roof_hi = _halfspace_below(cq.Vector(xr, 0, base(xr)), cq.Vector(s, 0, 1))        # 45 deg roof
        cap = _halfspace_below(cq.Vector(x0, 0, z0 + SCOOP_DEPTH), n_b)                   # parallel to base
        roof_y0 = _halfspace_below(cq.Vector(x0, y0 + t, z0), cq.Vector(-s, -1, 1))      # ~55 deg roofs
        roof_y1 = _halfspace_below(cq.Vector(x0, y1 - t, z0), cq.Vector(-s, 1, 1))

        cavity = inner.intersect(roof_hi).intersect(cap).intersect(roof_y0).intersect(roof_y1)
        pillar = pillar.cut(cavity)

    return pillar


def create_skadis_coupon(hook_dia, hook_type, stem_length=5.0, drop_length=5.0, arc_radius=None,
                         support=None, support_gap=0.2, label=None):
    peg1_y = 20.0
    peg2_y = -20.0
    top_y = peg1_y + 10.0
    bottom_y = peg2_y - 10.0
    plate_thickness = 6.0
    embed_z = 3.0
    bend_r = 2.5

    base = create_test_coupon_base(width=20.0, plate_thickness=plate_thickness, top_y=top_y, bottom_y=bottom_y)

    # Engrave label
    center_y = (top_y + bottom_y) / 2.0
    if label is None:
        label = f"SK {hook_dia} {hook_type[:3].upper()}"
        if hook_type == "90deg":
            label += f" S{stem_length}"
        elif hook_type == "arc":
            label += f" R{arc_radius}"
    txt_solid = (cq.Workplane("XY")
                 .workplane(offset=plate_thickness)
                 .center(0, center_y)
                 .transformed(rotate=(0, 0, 90))
                 .text(label, 3.5, -0.6, combine=False))
    base = base.cut(txt_solid)

    top_embed = cq.Solid.makeCylinder(hook_dia / 2.0, plate_thickness - embed_z + 0.1,
                                      cq.Vector(0, peg1_y, embed_z), cq.Vector(0, 0, 1))

    if hook_type == "arc":
        circle_arc = cq.Workplane("XY").center(0, peg1_y).workplane(offset=plate_thickness).circle(hook_dia / 2.0)
        bend = circle_arc.revolve(90, (0, -arc_radius, 0), (1, -arc_radius, 0))
        end_sph = cq.Solid.makeSphere(hook_dia / 2.0, cq.Vector(0, peg1_y - arc_radius, plate_thickness + arc_radius),
                                      cq.Vector(0, 0, 1), -90, 90, 360)
        top_hook = bend.union(cq.Workplane(end_sph)).union(cq.Workplane(top_embed))
    else:  # 90deg
        stem = cq.Solid.makeCylinder(hook_dia / 2.0, stem_length, cq.Vector(0, peg1_y, plate_thickness), cq.Vector(0, 0, 1))
        circle_90 = cq.Workplane("XY").center(0, peg1_y).workplane(offset=plate_thickness + stem_length).circle(hook_dia / 2.0)
        bend = circle_90.revolve(90, (0, -bend_r, 0), (1, -bend_r, 0))
        drop = cq.Solid.makeCylinder(hook_dia / 2.0, drop_length,
                                     cq.Vector(0, peg1_y - bend_r, plate_thickness + stem_length + bend_r), cq.Vector(0, -1, 0))
        end_sph = cq.Solid.makeSphere(hook_dia / 2.0,
                                      cq.Vector(0, peg1_y - bend_r - drop_length, plate_thickness + stem_length + bend_r),
                                      cq.Vector(0, 0, 1), -90, 90, 360)
        top_hook = (cq.Workplane(stem).union(bend).union(cq.Workplane(drop))
                    .union(cq.Workplane(end_sph)).union(cq.Workplane(top_embed)))

    # Bottom alignment peg
    bot_peg = cq.Solid.makeCylinder(hook_dia / 2.0, 5.0 + (plate_thickness - embed_z), cq.Vector(0, peg2_y, embed_z), cq.Vector(0, 0, 1))
    bot_sph = cq.Solid.makeSphere(hook_dia / 2.0, cq.Vector(0, peg2_y, plate_thickness + 5.0), cq.Vector(0, 0, 1), -90, 90, 360)
    bot_peg_full = cq.Workplane(bot_peg).union(cq.Workplane(bot_sph))

    coupon = base.union(top_hook).union(bot_peg_full).val()

    # Rotate into print orientation and drop onto the bed (Z = 0)
    rotated = _to_print(coupon, 0.0)
    dz = -rotated.BoundingBox().zmin
    coupon_p = rotated.translate(cq.Vector(0, 0, dz))

    if hook_type != "90deg" or support is None:
        return cq.Workplane(coupon_p)

    sup = _make_support(support, support_gap, hook_dia, plate_thickness, peg1_y,
                        stem_length, bend_r, drop_length, dz)
    # Separate shells in one STL so the slicer treats them as two parts
    return cq.Workplane(cq.Compound.makeCompound([coupon_p, sup]))


VARIANTS = [
    # (support style, gap, label)
    ('square', 0.2, "4.8 SQ .2"),
    ('scoop', 0.1, "4.8 SC .1"),
    ('scoop', 0.2, "4.8 SC .2"),
    ('angled', 0.2, "4.8 AN .2"),
]


def main():
    d = 4.8
    for style, gap, label in VARIANTS:
        model = create_skadis_coupon(hook_dia=d, hook_type="90deg", stem_length=5.0, drop_length=5.0,
                                     support=style, support_gap=gap, label=label)
        export_stl(model, f"skadis_{d}mm_90deg_S5_{style}_g{gap}_coupon.stl", category='pegboard_tests')


if __name__ == "__main__":
    main()
