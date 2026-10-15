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
    BACKPLATE_TOP_Y,
    TOP_RIDGE_Y,
    RIDGE_HEIGHT,
    RIDGE_SURFACE_HALF_WIDTH,
    RIDGE_PEAK_HALF_WIDTH,
    DEFAULT_RAIL_HEIGHT,
    RAIL_PLAY,
    get_bottom_groove_y,
    get_bottom_edge_y,
    create_nut_slot,
    export_model,
    NUT_SLOT_TOLERANCE,
)

# Default dimensions for the shelf-edge dovetail pocket
DEFAULT_DOVETAIL_HEIGHT = 25.0
DEFAULT_TOP_NECK_W = 29.0
DEFAULT_BOT_NECK_W = 25.0
DEFAULT_TOP_FLANGE_W = 39.5
DEFAULT_BOT_FLANGE_W = 35.5
DEFAULT_NECK_DEPTH = 6.5
DEFAULT_FLANGE_THICK_BOT = 6.0  # Flange thickness at bottom of dovetail
DEFAULT_FLANGE_DELTA_TOP = 0.2  # Top thickness delta (+0.2 mm over bottom thickness: 6.2 mm top)
DEFAULT_DRAFT_ANGLE = 0.0  # Angle in degrees matching shelf rim flare (0.0 = vertical / parallel to dovetail)
DEFAULT_LOBE_FILLET = 2.5
DEFAULT_INSIDE_FILLET = 0.6
DEFAULT_LEAD_IN_CHAMFER = 1.2
DEFAULT_SIDE_CHAMFER = 6.0
DEFAULT_SLOT_SPACING = 152.5

# Shelf front rim profile features
DEFAULT_LIP_DIST = 38.0      # Distance from dovetail top face to chamfered lip (42 mm shelf top - 3 mm mount recess - 1 mm margin)
DEFAULT_LIP_DEPTH = 2.0     # Step depth (shelf sticks out 2 mm further forward below the lip)
DEFAULT_LIP_CHAMFER = 2.0   # Vertical height of the 45-degree chamfer transition
# Push-out hole defaults (angled toward front ridge face)
DEFAULT_PUSH_HOLE_ANGLE = 15.0  # degrees tilted toward front face
DEFAULT_PUSH_HOLE_DIA = 2.0    # mm bore diameter (easily fits paper clip, nut cannot drop through)

def orient_for_export(model, orientation="top_down"):
    """
    Applies rotation for 3D printing so the specified side sits flat on the print bed.

    For 'top_down':
      The top surface of the dovetail and mount plate (+Y in CAD) is rotated +90 deg around X,
      then flipped 180 deg around the print Y axis. This places the flat top surface
      at Z_min = -20.0 (sitting directly flat on the build plate at Z=0 in the slicer),
      printing upwards with zero overhangs or supports.
    """
    if orientation == "top_down":
        return model.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 1, 0), 180)
    elif orientation == "bottom_down":
        return model.rotate((0, 0, 0), (1, 0, 0), -90)
    elif orientation == "back_down":
        return model.rotate((0, 0, 0), (1, 0, 0), 180)
    elif orientation == "face_down":
        return model
    elif orientation == "left_down":
        return model.rotate((0, 0, 0), (0, 1, 0), 90)
    elif orientation == "right_down":
        return model.rotate((0, 0, 0), (0, 1, 0), -90)
    return model


def build_dovetail_wedge_solid(
    dovetail_height=DEFAULT_DOVETAIL_HEIGHT,
    top_neck_w=DEFAULT_TOP_NECK_W,
    bot_neck_w=DEFAULT_BOT_NECK_W,
    top_flange_w=DEFAULT_TOP_FLANGE_W,
    bot_flange_w=DEFAULT_BOT_FLANGE_W,
    neck_depth=DEFAULT_NECK_DEPTH,
    flange_thick_bot=DEFAULT_FLANGE_THICK_BOT,
    flange_delta_top=DEFAULT_FLANGE_DELTA_TOP,
    draft_angle=DEFAULT_DRAFT_ANGLE,
    lobe_fillet=DEFAULT_LOBE_FILLET,
    inside_fillet=DEFAULT_INSIDE_FILLET,
    lead_in_chamfer=DEFAULT_LEAD_IN_CHAMFER,
    no_wings=False,
    y_top=BACKPLATE_TOP_Y,
    z_base_top=15.974,
    z_base_bot=14.664,
):
    """
    Builds the tapered dovetail wedge that slides into the shelf edge socket.

    Reference Frame:
      - Top: +Y (flush with mount plate top surface at y_top)
      - Bottom: -Y (narrower end of the dovetail taper)
      - Depth into shelf: +Z (protrudes into socket from mount plate back face)
      - Width: X (centered at X=0)

    Draft Angles & Pocket Slope:
      - Flange front shoulder stays at constant Z = z_base_top + neck_depth for all Y (vertical).
      - Flange rear face:
          At bottom (y = y_bot): flange thickness = flange_thick_bot (6.0 mm).
          At top (y = y_top): flange thickness = flange_thick_bot + flange_delta_top
          (or dovetail_height * tan(draft_angle) if flange_delta_top is None).
      - Clearance gap to mount plate:
          At top (y = y_top): z_shoulder - z_base_top = neck_depth (8.0 mm).
          At bottom (y = y_bot): z_shoulder - z_base_bot widens by the 3-degree draft angle (9.31 mm).
      - Neck connects forward into the sloped mount plate at Z <= z_base(y) - 0.2.

    no_wings:
      If True, builds a pure tapered dovetail wedge of width bot_neck_w to top_neck_w
      without stepped-out retention lobes, allowing isolated calibration of the socket taper.
    """
    y_bot = y_top - dovetail_height
    draft_rad = math.radians(draft_angle) if draft_angle else 0.0

    z_shoulder = z_base_top + neck_depth
    if flange_delta_top is not None:
        flange_thick_top = flange_thick_bot + flange_delta_top
    else:
        flange_thick_top = flange_thick_bot + dovetail_height * math.tan(draft_rad)
    z_rear_bot = z_shoulder + flange_thick_bot
    z_rear_top = z_shoulder + flange_thick_top

    def get_profile_pts(z_front, w_neck, w_flange, z_rear):
        if no_wings:
            return [
                (z_front, -w_neck / 2.0),
                (z_front, w_neck / 2.0),
                (z_rear, w_neck / 2.0),
                (z_rear, -w_neck / 2.0),
            ]
        # On ZX plane: Local X is Global Z (depth), Local Y is Global X (width).
        # Front shoulder is at constant z_shoulder; rear face is at z_rear.
        return [
            (z_front, -w_neck / 2.0),
            (z_front, w_neck / 2.0),
            (z_shoulder, w_neck / 2.0),
            (z_shoulder, w_flange / 2.0),
            (z_rear, w_flange / 2.0),
            (z_rear, -w_flange / 2.0),
            (z_shoulder, -w_flange / 2.0),
            (z_shoulder, -w_neck / 2.0),
        ]

    pts_bot = get_profile_pts(z_base_bot - 0.2, bot_neck_w, bot_flange_w, z_rear_bot)
    pts_top = get_profile_pts(z_base_top - 0.2, top_neck_w, top_flange_w, z_rear_top)

    wedge = (
        cq.Workplane("ZX", origin=(0.0, y_bot, 0.0))
        .polyline(pts_bot)
        .close()
        .workplane(offset=dovetail_height)
        .polyline(pts_top)
        .close()
        .loft()
    )

    lateral_edges = [
        e
        for e in wedge.edges().vals()
        if abs(e.BoundingBox().ymin - y_bot) < 0.02
        and abs(e.BoundingBox().ymax - y_top) < 0.02
    ]

    # Rear outer corners: fillet blending the sloped rear face
    rear_edges = [
        e
        for e in lateral_edges
        if e.BoundingBox().zmin > (z_rear_bot - 0.5)
    ]
    rear_radius = min(3.0, flange_thick_bot / 2.0)
    if rear_edges and rear_radius > 0:
        try:
            wedge = wedge.newObject(rear_edges).fillet(rear_radius)
        except Exception:
            pass

    if not no_wings:
        mid_x_cutoff = (
            (bot_neck_w + top_neck_w) / 4.0 + (bot_flange_w + top_flange_w) / 4.0
        ) / 2.0

        # Outer shoulder corners at Z = z_shoulder
        lateral_edges = [
            e
            for e in wedge.edges().vals()
            if abs(e.BoundingBox().ymin - y_bot) < 0.02
            and abs(e.BoundingBox().ymax - y_top) < 0.02
        ]
        shoulder_edges = [
            e
            for e in lateral_edges
            if abs(e.BoundingBox().zmin - z_shoulder) < 0.5
        ]
        outer_shoulder = [
            e
            for e in shoulder_edges
            if (abs(e.BoundingBox().xmin) + abs(e.BoundingBox().xmax)) / 2.0
            > mid_x_cutoff
        ]
        if outer_shoulder and lobe_fillet > 0:
            try:
                wedge = wedge.newObject(outer_shoulder).fillet(lobe_fillet)
            except Exception:
                pass

        # Inside re-entrant corners at Z = z_shoulder
        lateral_edges = [
            e
            for e in wedge.edges().vals()
            if abs(e.BoundingBox().ymin - y_bot) < 0.02
            and abs(e.BoundingBox().ymax - y_top) < 0.02
        ]
        shoulder_edges = [
            e
            for e in lateral_edges
            if abs(e.BoundingBox().zmin - z_shoulder) < 0.5
        ]
        inside_corners = [
            e
            for e in shoulder_edges
            if (abs(e.BoundingBox().xmin) + abs(e.BoundingBox().xmax)) / 2.0
            < mid_x_cutoff
        ]
        if inside_corners and inside_fillet > 0:
            try:
                wedge = wedge.newObject(inside_corners).fillet(inside_fillet)
            except Exception:
                pass

    # Chamfer bottom outer edges for smooth lead-in into socket
    if lead_in_chamfer > 0:
        try:
            bot_outer_edges = [
                e
                for e in wedge.edges("<Y").vals()
                if e.BoundingBox().zmin > (z_shoulder - 0.2)
            ]
            if bot_outer_edges:
                wedge = wedge.newObject(bot_outer_edges).chamfer(lead_in_chamfer)
        except Exception:
            pass

    return wedge


def create_shelf_dovetail_test_wedge(
    dovetail_height=DEFAULT_DOVETAIL_HEIGHT,
    top_neck_w=DEFAULT_TOP_NECK_W,
    bot_neck_w=DEFAULT_BOT_NECK_W,
    top_flange_w=DEFAULT_TOP_FLANGE_W,
    bot_flange_w=DEFAULT_BOT_FLANGE_W,
    neck_depth=DEFAULT_NECK_DEPTH,
    flange_thick_bot=DEFAULT_FLANGE_THICK_BOT,
    flange_delta_top=DEFAULT_FLANGE_DELTA_TOP,
    draft_angle=DEFAULT_DRAFT_ANGLE,
    lobe_fillet=DEFAULT_LOBE_FILLET,
    inside_fillet=DEFAULT_INSIDE_FILLET,
    lead_in_chamfer=DEFAULT_LEAD_IN_CHAMFER,
    mount_wings=True,
    no_wings=False,
    handle_extension=0.0,
    lip_dist=DEFAULT_LIP_DIST,
    lip_depth=DEFAULT_LIP_DEPTH,
    lip_chamfer=DEFAULT_LIP_CHAMFER,
    label=None,
    label_fontsize=11.0,
):
    """
    Creates a standalone test wedge with a flat backing plate
    for quick calibration printing to verify fit in the shelf pocket.

    The mating front surface is strictly vertical (at Z=0).
    The back face of the plate slopes at draft_angle (3 deg) matching the shelf rim.
    If handle_extension extends below the lip (backing_h > lip_dist), the backing plate
    incorporates the 2 mm chamfered shelf lip for verifying rim engagement.
    The top of the dovetail and backing plate are completely flush and flat at Y = BACKPLATE_TOP_Y.

    mount_wings:
      If True (default), includes the wide backing plate (48 mm wide).
      If False, the backing plate width matches the neck (no wings on the mount),
      allowing the full-width dovetail to drop in without mount interference.

    label:
      Optional text string (e.g. '1A', 'LIP', 'WEDGE', '+0.3') to deboss onto the
      front handle face of the coupon.
    """
    backing_t = 3.0
    y_top = BACKPLATE_TOP_Y
    backing_h = dovetail_height + handle_extension
    y_bot = y_top - backing_h
    draft_rad = math.radians(draft_angle) if draft_angle else 0.0

    y_lip_top = y_top - lip_dist
    y_lip_bot = y_lip_top - lip_chamfer

    if backing_h > lip_dist:
        z_lip_bot = backing_t + (y_lip_bot - y_bot) * math.tan(draft_rad)
        z_lip_top = z_lip_bot + lip_depth + lip_chamfer * math.tan(draft_rad)
        t_top = z_lip_top + (y_top - y_lip_top) * math.tan(draft_rad)
        z_base_bot_dt = z_lip_top + (y_top - dovetail_height - y_lip_top) * math.tan(draft_rad)
        pts_backing = [
            (y_top, t_top),
            (y_top, 0.0),
            (y_bot, 0.0),
            (y_bot, backing_t),
            (y_lip_bot, z_lip_bot),
            (y_lip_top, z_lip_top),
        ]
    else:
        t_top = backing_t + backing_h * math.tan(draft_rad)
        z_base_bot_dt = backing_t
        pts_backing = [
            (y_top, t_top),
            (y_top, 0.0),
            (y_bot, 0.0),
            (y_bot, backing_t),
        ]

    if mount_wings:
        w_mount = max(top_flange_w + 6.0, 48.0)
    else:
        w_mount = top_neck_w

    backing = (
        cq.Workplane("YZ")
        .polyline(pts_backing)
        .close()
        .extrude(w_mount)
        .translate((-w_mount / 2.0, 0, 0))
    )

    wedge = build_dovetail_wedge_solid(
        dovetail_height=dovetail_height,
        top_neck_w=top_neck_w,
        bot_neck_w=bot_neck_w,
        top_flange_w=top_flange_w,
        bot_flange_w=bot_flange_w,
        neck_depth=neck_depth,
        flange_thick_bot=flange_thick_bot,
        flange_delta_top=flange_delta_top,
        draft_angle=draft_angle,
        lobe_fillet=lobe_fillet,
        inside_fillet=inside_fillet,
        lead_in_chamfer=lead_in_chamfer,
        no_wings=no_wings,
        y_top=y_top,
        z_base_top=t_top,
        z_base_bot=z_base_bot_dt,
    )

    res = backing.union(wedge)

    if label:
        mid_y = y_top - dovetail_height / 2.0
        cut_tool = (
            cq.Workplane("XY")
            .workplane(offset=1.0)
            .transformed(rotate=(0, 180, 0))
            .center(0.0, mid_y)
            .text(str(label), label_fontsize, 1.1, combine=False, kind="bold")
        )
        res = res.cut(cut_tool)

    return res


def create_shelf_edge_spacing_test_coupon(
    slot_spacing=DEFAULT_SLOT_SPACING,
    dovetail_height=DEFAULT_DOVETAIL_HEIGHT,
    top_neck_w=DEFAULT_TOP_NECK_W,
    bot_neck_w=DEFAULT_BOT_NECK_W,
    top_flange_w=DEFAULT_TOP_FLANGE_W,
    bot_flange_w=DEFAULT_BOT_FLANGE_W,
    neck_depth=DEFAULT_NECK_DEPTH,
    flange_thick_bot=DEFAULT_FLANGE_THICK_BOT,
    flange_delta_top=DEFAULT_FLANGE_DELTA_TOP,
    draft_angle=DEFAULT_DRAFT_ANGLE,
    lobe_fillet=DEFAULT_LOBE_FILLET,
    inside_fillet=DEFAULT_INSIDE_FILLET,
    lead_in_chamfer=DEFAULT_LEAD_IN_CHAMFER,
    bridge_thickness=4.0,
    pad_extra_w=8.5,
    side_chamfer=4.0,
    label=None,
    label_fontsize=9.0,
):
    """
    Creates a dual-dovetail spacing calibration test coupon.

    Features:
      - Two full-geometry dovetail wedges positioned at X = +/- slot_spacing / 2.
      - A rigid horizontal bridge bar (bridge_thickness thick, dovetail_height tall)
        connecting them across the front.
      - Top surface is flat and coplanar at Y = BACKPLATE_TOP_Y for direct top_down printability.
      - Debossed center-to-center measurement text on the front face.
      - Centerline triangle notches at X = +/- slot_spacing/2 and X = 0 for visual alignment.
    """
    y_top = BACKPLATE_TOP_Y
    h = dovetail_height
    y_bot = y_top - h
    half_s = slot_spacing / 2.0
    total_w = slot_spacing + top_flange_w + pad_extra_w * 2.0

    # 1. Rigid connecting bridge bar
    bridge = (
        cq.Workplane("XY")
        .box(total_w, h, bridge_thickness, centered=(True, True, False))
        .translate((0, y_top - h / 2.0, 0))
    )

    if side_chamfer > 0:
        try:
            bridge = bridge.edges("|Z and ( <X or >X )").chamfer(side_chamfer)
        except Exception:
            pass

    # 2. Dovetails at +/- half_s
    dt = build_dovetail_wedge_solid(
        dovetail_height=h,
        top_neck_w=top_neck_w,
        bot_neck_w=bot_neck_w,
        top_flange_w=top_flange_w,
        bot_flange_w=bot_flange_w,
        neck_depth=neck_depth,
        flange_thick_bot=flange_thick_bot,
        flange_delta_top=flange_delta_top,
        draft_angle=draft_angle,
        lobe_fillet=lobe_fillet,
        inside_fillet=inside_fillet,
        lead_in_chamfer=lead_in_chamfer,
        no_wings=False,
        y_top=y_top,
        z_base_top=bridge_thickness,
        z_base_bot=bridge_thickness,
    )

    res = bridge.union(dt.translate((-half_s, 0, 0))).union(dt.translate((half_s, 0, 0)))

    # 3. Debossed label and alignment notches
    lbl_text = label if label else f"{slot_spacing:.1f} mm C-C"
    mid_y = y_top - h / 2.0
    try:
        text_solid = (
            cq.Workplane("XY")
            .workplane(offset=-0.1)
            .transformed(rotate=(0, 0, 180))
            .center(0.0, -mid_y)
            .text(str(lbl_text), label_fontsize, 0.7, combine=False, kind="bold")
            .val()
        )
        text_solid = text_solid.mirror("YZ")
        res = res.cut(cq.Workplane(text_solid))
    except Exception:
        pass

    # Alignment notches on the bottom edge (Y = y_bot)
    try:
        notch_tool = (
            cq.Workplane("XY")
            .workplane(offset=-0.1)
            .polyline([(-1.5, y_bot - 0.1), (0, y_bot + 2.5), (1.5, y_bot - 0.1)])
            .close()
            .extrude(bridge_thickness + 0.2)
        )
        res = res.cut(notch_tool.translate((-half_s, 0, 0)))
        res = res.cut(notch_tool.translate((half_s, 0, 0)))
        res = res.cut(notch_tool.translate((0, 0, 0)))
    except Exception:
        pass

    return res


def create_shelf_edge_adapter(
    units=2,
    rail_height=DEFAULT_RAIL_HEIGHT,
    screw_m="M3",
    with_screws=True,
    dovetail_height=DEFAULT_DOVETAIL_HEIGHT,
    top_neck_w=DEFAULT_TOP_NECK_W,
    bot_neck_w=DEFAULT_BOT_NECK_W,
    top_flange_w=DEFAULT_TOP_FLANGE_W,
    bot_flange_w=DEFAULT_BOT_FLANGE_W,
    neck_depth=DEFAULT_NECK_DEPTH,
    flange_thick_bot=DEFAULT_FLANGE_THICK_BOT,
    flange_delta_top=DEFAULT_FLANGE_DELTA_TOP,
    draft_angle=DEFAULT_DRAFT_ANGLE,
    lobe_fillet=DEFAULT_LOBE_FILLET,
    inside_fillet=DEFAULT_INSIDE_FILLET,
    lead_in_chamfer=DEFAULT_LEAD_IN_CHAMFER,
    side_chamfer=DEFAULT_SIDE_CHAMFER,
    slot_spacing=DEFAULT_SLOT_SPACING,
    lip_dist=DEFAULT_LIP_DIST,
    lip_depth=DEFAULT_LIP_DEPTH,
    lip_chamfer=DEFAULT_LIP_CHAMFER,
    push_hole_angle=DEFAULT_PUSH_HOLE_ANGLE,
    push_hole_dia=DEFAULT_PUSH_HOLE_DIA,
    dovetail_count="auto",
):
    """
    Builds a shelf-edge French Cleat adapter with tapered dovetail mount.

    Both the top and bottom ridges are on this single monolithic piece.

    Reference Frame:
      - Top: +Y (flush with dovetail top face at y_top)
      - Bottom: -Y
      - Front: -Z (cleat locking ridges and screw holes, strictly vertical at Z=0)
      - Back: +Z (vertical dovetail wedge enters pocket)
      - Left: -X
      - Right: +X

    Mating Face & Taper:
      - The front mating surface is strictly vertical (at Z=0), ensuring tool holders hang plumb.
      - The back face incorporates the shelf rim geometry:
          * Upper section (y in [y_lip_top, y_top]): slopes backward at draft_angle (3 deg).
          * 2 mm Chamfered Lip (y in [y_lip_bot, y_lip_top]): 45-degree chamfer stepping 2 mm deeper into the upper recess.
          * Lower section (y in [y_bot, y_lip_bot]): slopes at draft_angle down to 8.0 mm thickness at the bottom edge.
      - The top edge is flat and flush across the entire width and dovetail.
      - The vertical sides feature a 45-degree chamfer (side_chamfer) for smooth lead-in and clean aesthetics.

    Multi-Dovetail Logic:
      Adjacent shelf slots are spaced slot_spacing mm (152.5 mm) center-to-center.
      Outer span across two dovetails = slot_spacing + top_flange_w = 152.5 + 39.5 = 192.0 mm.
      Calculated threshold X = ceil(192.0 / 28.0) = 7U (196.0 mm).
      Mounts up to 6U have 1 centered dovetail (X = 0).
      Mounts 7U and up have 2 dovetails at X = +/- slot_spacing / 2 (+/- 76.25 mm).
    """
    width = units * UNIT_WIDTH

    # Determine dovetail positioning
    span_2dovetails = slot_spacing + top_flange_w
    min_units_for_2 = math.ceil(span_2dovetails / UNIT_WIDTH)  # 7U

    if dovetail_count == "2" or (dovetail_count == "auto" and units >= min_units_for_2):
        dovetail_x_positions = [-slot_spacing / 2.0, slot_spacing / 2.0]
    else:
        dovetail_x_positions = [0.0]

    if screw_m == "M3":
        screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4
    elif screw_m == "M4":
        screw_d, nut_waf, nut_thick = 4.5, 7.0, 3.2
    elif screw_m == "M5":
        screw_d, nut_waf, nut_thick = 5.5, 8.0, 4.0
    else:
        with_screws = False
        screw_d, nut_waf, nut_thick = 3.4, 5.5, 2.4

    slot_t = nut_thick + NUT_SLOT_TOLERANCE
    slot_z_center = 4.0 + slot_t / 2.0

    y_top = BACKPLATE_TOP_Y
    play = RAIL_PLAY
    top_screw_y = TOP_RIDGE_Y
    bottom_screw_y = get_bottom_groove_y(rail_height, play)
    y_bot = get_bottom_edge_y(rail_height, play)

    draft_rad = math.radians(draft_angle) if draft_angle else 0.0

    # Thickness of mount plate:
    # 8.0 mm minimum thickness at bottom edge.
    t_bot = max(8.0, 4.0 + slot_t + 1.2)

    # Shelf lip transition positions
    y_lip_top = y_top - lip_dist
    y_lip_bot = y_lip_top - lip_chamfer

    z_lip_bot = t_bot + (y_lip_bot - y_bot) * math.tan(draft_rad)
    z_lip_top = z_lip_bot + lip_depth + lip_chamfer * math.tan(draft_rad)
    t_top = z_lip_top + (y_top - y_lip_top) * math.tan(draft_rad)

    # 1. Front mounting plate profile:
    # Front face is strictly vertical at Z = 0 (ridges protrude to -RIDGE_HEIGHT).
    # Back face incorporates the lower 3-degree slope, 45-degree chamfered 2mm lip, and upper 3-degree slope.
    # Top edge is flat at y_top from (y_top, t_top) to (y_top, 0.0).
    plate_pts = [
        (y_top, t_top),
        (y_top, 0.0),
        (top_screw_y + RIDGE_SURFACE_HALF_WIDTH, 0.0),
        (top_screw_y + RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (top_screw_y - RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (top_screw_y - RIDGE_SURFACE_HALF_WIDTH, 0.0),
        (bottom_screw_y + RIDGE_SURFACE_HALF_WIDTH, 0.0),
        (bottom_screw_y + RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (bottom_screw_y - RIDGE_PEAK_HALF_WIDTH, -RIDGE_HEIGHT),
        (bottom_screw_y - RIDGE_SURFACE_HALF_WIDTH, 0.0),
        (y_bot, 0.0),
        (y_bot, t_bot),
        (y_lip_bot, z_lip_bot),
        (y_lip_top, z_lip_top),
    ]

    plate = (
        cq.Workplane("YZ")
        .polyline(plate_pts)
        .close()
        .extrude(width)
        .translate((-width / 2.0, 0, 0))
    )

    # 2. 45-degree chamfers on the vertical sides (lateral ends at X = +/- width/2)
    if side_chamfer and side_chamfer > 0:
        c = side_chamfer
        h_cut = (y_top - y_bot) + 20.0
        z_min = -RIDGE_HEIGHT - 1.5
        z_max = c + 1.0

        # Exact 45-degree slope on the right (+X) side
        x_min_r = width / 2.0 - c + z_min
        x_max_r = width / 2.0 + 1.0
        pts_r = [
            (z_min, x_min_r),
            (z_min, width / 2.0 + 5.0),
            (z_max, width / 2.0 + 5.0),
            (z_max, x_max_r),
        ]
        cutter_r = (
            cq.Workplane("ZX", origin=(0.0, y_bot - 10.0, 0.0))
            .polyline(pts_r)
            .close()
            .extrude(h_cut)
        )

        # Exact 45-degree slope on the left (-X) side
        pts_l = [
            (z_min, -x_min_r),
            (z_min, -width / 2.0 - 5.0),
            (z_max, -width / 2.0 - 5.0),
            (z_max, -x_max_r),
        ]
        cutter_l = (
            cq.Workplane("ZX", origin=(0.0, y_bot - 10.0, 0.0))
            .polyline(pts_l)
            .close()
            .extrude(h_cut)
        )
        plate = plate.cut(cutter_r).cut(cutter_l)

    # 3. Male tapered dovetail wedge(s) on the rear face (protruding into +Z)
    y_bot_dt = y_top - dovetail_height
    z_base_top = t_top
    z_base_bot = z_lip_top + (y_bot_dt - y_lip_top) * math.tan(draft_rad)

    wedge_proto = build_dovetail_wedge_solid(
        dovetail_height=dovetail_height,
        top_neck_w=top_neck_w,
        bot_neck_w=bot_neck_w,
        top_flange_w=top_flange_w,
        bot_flange_w=bot_flange_w,
        neck_depth=neck_depth,
        flange_thick_bot=flange_thick_bot,
        flange_delta_top=flange_delta_top,
        draft_angle=draft_angle,
        lobe_fillet=lobe_fillet,
        inside_fillet=inside_fillet,
        lead_in_chamfer=lead_in_chamfer,
        no_wings=False,
        y_top=y_top,
        z_base_top=z_base_top,
        z_base_bot=z_base_bot,
    )

    adapter = plate
    for wx in dovetail_x_positions:
        adapter = adapter.union(wedge_proto.translate((wx, 0, 0)))

    # 4. Screw clearance holes and captive nut slots (if enabled)
    if with_screws and screw_m.lower() != "none":
        for i in range(units):
            x = -width / 2.0 + UNIT_WIDTH / 2.0 + i * UNIT_WIDTH

            for sy in [top_screw_y, bottom_screw_y]:
                hole = (
                    cq.Workplane("XY")
                    .workplane(offset=-RIDGE_HEIGHT - 5.0)
                    .center(x, sy)
                    .circle(screw_d / 2.0)
                    .extrude(t_top + 10.0)
                )
                adapter = adapter.cut(hole)

            # Top nut slot (entry from top face along Y)
            depth_top = y_top - top_screw_y
            slot_top = create_nut_slot(
                screw_m,
                depth=depth_top,
                push_hole=True,
                push_hole_angle=push_hole_angle,
                push_hole_dia=push_hole_dia,
            )
            slot_top = (
                cq.Workplane(slot_top)
                .translate(cq.Vector(x, top_screw_y, slot_z_center))
                .val()
            )
            adapter = adapter.cut(cq.Workplane(slot_top))

            # Bottom nut slot (entry from bottom face along Y)
            depth_bot = bottom_screw_y - y_bot
            slot_bot = create_nut_slot(
                screw_m,
                depth=depth_bot,
                push_hole=True,
                push_hole_angle=push_hole_angle,
                push_hole_dia=push_hole_dia,
            )
            slot_bot = (
                cq.Workplane(slot_bot)
                .rotate((0, 0, 0), (0, 0, 1), 180)
                .translate(cq.Vector(x, bottom_screw_y, slot_z_center))
                .val()
            )
            adapter = adapter.cut(cq.Workplane(slot_bot))

    return adapter


def main():
    parser = argparse.ArgumentParser(
        description="Generate Shelf-Edge Dovetail to French Cleat Adapter"
    )
    parser.add_argument(
        "--units",
        type=int,
        default=2,
        help="Number of units wide (default: 2, 56.0 mm wide)",
    )
    parser.add_argument(
        "--rail-height",
        type=float,
        default=DEFAULT_RAIL_HEIGHT,
        help=f"Height of French Cleat rail spacing in mm (default: {DEFAULT_RAIL_HEIGHT})",
    )
    parser.add_argument(
        "--screw",
        choices=["M3", "M4", "M5", "none"],
        default="M3",
        help="Captive nut and screw size (default: M3, use 'none' for solid ridges)",
    )
    parser.add_argument(
        "--no-screws",
        action="store_true",
        help="Disable captive nut slots and screw holes (ridges only)",
    )
    parser.add_argument(
        "--draft-angle",
        type=float,
        default=DEFAULT_DRAFT_ANGLE,
        help=f"Angle in degrees matching the shelf rim flare (default: {DEFAULT_DRAFT_ANGLE})",
    )
    parser.add_argument(
        "--side-chamfer",
        type=float,
        default=DEFAULT_SIDE_CHAMFER,
        help=f"45-degree chamfer size on the vertical sides in mm (default: {DEFAULT_SIDE_CHAMFER})",
    )
    parser.add_argument(
        "--lip-dist",
        type=float,
        default=DEFAULT_LIP_DIST,
        help=f"Distance in mm from top of dovetail to start of shelf chamfered lip (default: {DEFAULT_LIP_DIST})",
    )
    parser.add_argument(
        "--lip-depth",
        type=float,
        default=DEFAULT_LIP_DEPTH,
        help=f"Step depth in mm of the shelf lip (default: {DEFAULT_LIP_DEPTH})",
    )
    parser.add_argument(
        "--lip-chamfer",
        type=float,
        default=DEFAULT_LIP_CHAMFER,
        help=f"Vertical height in mm of the lip transition chamfer (default: {DEFAULT_LIP_CHAMFER})",
    )
    parser.add_argument(
        "--test-wedge",
        action="store_true",
        help="Generate the male dovetail test wedge with retention wings and draft angle",
    )
    parser.add_argument(
        "--test-taper",
        action="store_true",
        help="Generate test wedge with full dovetail width but no wings on the mount plate",
    )
    parser.add_argument(
        "--dovetail-height",
        type=float,
        default=DEFAULT_DOVETAIL_HEIGHT,
        help=f"Height of the dovetail pocket in mm (default: {DEFAULT_DOVETAIL_HEIGHT})",
    )
    parser.add_argument(
        "--top-neck-w",
        type=float,
        default=DEFAULT_TOP_NECK_W,
        help=f"Top neck width in mm (default: {DEFAULT_TOP_NECK_W})",
    )
    parser.add_argument(
        "--bot-neck-w",
        type=float,
        default=DEFAULT_BOT_NECK_W,
        help=f"Bottom neck width in mm (default: {DEFAULT_BOT_NECK_W})",
    )
    parser.add_argument(
        "--top-flange-w",
        type=float,
        default=DEFAULT_TOP_FLANGE_W,
        help=f"Top flange outer width in mm (default: {DEFAULT_TOP_FLANGE_W})",
    )
    parser.add_argument(
        "--bot-flange-w",
        type=float,
        default=DEFAULT_BOT_FLANGE_W,
        help=f"Bottom flange outer width in mm (default: {DEFAULT_BOT_FLANGE_W})",
    )
    parser.add_argument(
        "--neck-depth",
        type=float,
        default=DEFAULT_NECK_DEPTH,
        help=f"Depth of neck before side lobes in mm (default: {DEFAULT_NECK_DEPTH})",
    )
    parser.add_argument(
        "--flange-thick-bot",
        type=float,
        default=DEFAULT_FLANGE_THICK_BOT,
        help=f"Flange thickness at bottom of dovetail in mm (default: {DEFAULT_FLANGE_THICK_BOT})",
    )
    parser.add_argument(
        "--flange-delta-top",
        type=float,
        default=DEFAULT_FLANGE_DELTA_TOP,
        help=f"Delta thickness added to dovetail top flange in mm (default: {DEFAULT_FLANGE_DELTA_TOP}, overrides draft_angle slope on dovetail)",
    )
    parser.add_argument(
        "--inside-fillet",
        type=float,
        default=DEFAULT_INSIDE_FILLET,
        help=f"Radius of inside neck corner fillet in mm (default: {DEFAULT_INSIDE_FILLET})",
    )
    parser.add_argument(
        "--slot-spacing",
        type=float,
        default=DEFAULT_SLOT_SPACING,
        help=f"Center-to-center spacing between shelf dovetail slots in mm (default: {DEFAULT_SLOT_SPACING})",
    )
    parser.add_argument(
        "--dovetails",
        choices=["auto", "1", "2"],
        default="auto",
        help="Number of dovetails: 'auto' (1 for <7U, 2 for >=7U), '1', or '2' (default: auto)",
    )
    parser.add_argument(
        "--push-hole-angle",
        type=float,
        default=DEFAULT_PUSH_HOLE_ANGLE,
        help=f"Angle in degrees of nut push-out holes towards ridge side (default: {DEFAULT_PUSH_HOLE_ANGLE})",
    )
    parser.add_argument(
        "--push-hole-dia",
        type=float,
        default=DEFAULT_PUSH_HOLE_DIA,
        help=f"Bore diameter of nut push-out holes in mm (default: {DEFAULT_PUSH_HOLE_DIA})",
    )
    parser.add_argument(
        "--handle-extension",
        type=float,
        default=0.0,
        help="Extra length in mm extending below the test wedge as a finger handle (default: 0.0, top remains flush)",
    )
    parser.add_argument(
        "--test-spacing",
        action="store_true",
        help="Generate the dual-dovetail spacing calibration test coupon",
    )
    parser.add_argument(
        "--tester",
        choices=[
            "all",
            "spacing",
            "wedge",
            "lip",
            "lip_0.5deg",
            "calib",
            "calib_0.1",
            "calib_0.2",
            "calib_0.3",
            "calib_0.6",
            "calib_0.9",
            "top_trim2mm",
            "width_minus2mm",
            "taper_plus2deg",
            "top39_plus2deg",
        ],
        default="all",
        help="Which test coupon to generate when testing (default: all)",
    )
    parser.add_argument(
        "--print-orientation",
        choices=[
            "top_down",
            "bottom_down",
            "back_down",
            "face_down",
            "left_down",
            "right_down",
            "none",
        ],
        default="top_down",
        help="Print orientation for export (default: top_down)",
    )
    parser.add_argument(
        "--export",
        choices=["both", "stl", "step"],
        default="both",
        help="Export format (default: both)",
    )

    args = parser.parse_args()
    with_screws = not args.no_screws and args.screw.lower() != "none"

    if args.test_wedge or args.test_taper or args.test_spacing or args.tester == "spacing":
        # 0. Dual-dovetail spacing calibration test coupon
        if args.test_spacing or args.tester in ["all", "spacing"]:
            model_spacing = create_shelf_edge_spacing_test_coupon(
                slot_spacing=args.slot_spacing,
                dovetail_height=args.dovetail_height,
                top_neck_w=args.top_neck_w,
                bot_neck_w=args.bot_neck_w,
                top_flange_w=args.top_flange_w,
                bot_flange_w=args.bot_flange_w,
                neck_depth=args.neck_depth,
                flange_thick_bot=args.flange_thick_bot,
                flange_delta_top=args.flange_delta_top,
                draft_angle=args.draft_angle,
                inside_fillet=args.inside_fillet,
                side_chamfer=args.side_chamfer,
            )
            filename_spacing = f"shelf_edge_dovetail_spacing_test_{args.slot_spacing:.1f}mm.stl"
            oriented_spacing = orient_for_export(model_spacing, args.print_orientation)
            export_model(
                oriented_spacing,
                filename_spacing,
                category="shelf",
                export=args.export,
                print_orientation="none",
            )
            # Also export convenient alias shelf_edge_dovetail_spacing_test.stl
            export_model(
                oriented_spacing,
                "shelf_edge_dovetail_spacing_test.stl",
                category="shelf",
                export=args.export,
                print_orientation="none",
            )
            print(
                f"Exported dual-dovetail spacing test coupon ({args.slot_spacing:.1f} mm C-C): "
                f"{filename_spacing} (and alias shelf_edge_dovetail_spacing_test.stl)"
            )

        # 1. Standard test wedge with mount wings and sloped dovetail
        if (args.test_wedge or args.test_taper) and args.tester in ["all", "wedge"]:
            model_wedge = create_shelf_dovetail_test_wedge(
                dovetail_height=args.dovetail_height,
                top_neck_w=args.top_neck_w,
                bot_neck_w=args.bot_neck_w,
                top_flange_w=args.top_flange_w,
                bot_flange_w=args.bot_flange_w,
                neck_depth=args.neck_depth,
                flange_thick_bot=args.flange_thick_bot,
                flange_delta_top=args.flange_delta_top,
                draft_angle=args.draft_angle,
                inside_fillet=args.inside_fillet,
                mount_wings=True,
                no_wings=False,
                handle_extension=args.handle_extension,
                lip_dist=args.lip_dist,
                lip_depth=args.lip_depth,
                lip_chamfer=args.lip_chamfer,
                label="+0.2",
            )
            filename_wedge = "shelf_edge_dovetail_test_wedge.stl"
            oriented_wedge = orient_for_export(model_wedge, args.print_orientation)
            export_model(
                oriented_wedge,
                filename_wedge,
                category="shelf",
                export=args.export,
                print_orientation="none",
            )
            print(f"Exported test wedge (with mount wings): {filename_wedge}")

        # 2. Extended test wedge specifically verifying the 2mm chamfered shelf lip
        if args.test_wedge and args.tester in ["all", "lip"]:
            model_lip = create_shelf_dovetail_test_wedge(
                dovetail_height=args.dovetail_height,
                top_neck_w=args.top_neck_w,
                bot_neck_w=args.bot_neck_w,
                top_flange_w=args.top_flange_w,
                bot_flange_w=args.bot_flange_w,
                neck_depth=args.neck_depth,
                flange_thick_bot=args.flange_thick_bot,
                flange_delta_top=args.flange_delta_top,
                draft_angle=args.draft_angle,
                inside_fillet=args.inside_fillet,
                mount_wings=True,
                no_wings=False,
                handle_extension=max(args.handle_extension, 22.0),
                lip_dist=args.lip_dist,
                lip_depth=args.lip_depth,
                lip_chamfer=args.lip_chamfer,
                label="LIP",
            )
            filename_lip = "shelf_edge_dovetail_lip_test.stl"
            oriented_lip = orient_for_export(model_lip, args.print_orientation)
            export_model(
                oriented_lip,
                filename_lip,
                category="shelf",
                export=args.export,
                print_orientation="none",
            )
            print(f"Exported extended lip test coupon (with 2mm chamfered step): {filename_lip}")

        # 2b. Optional 0.5-degree test coupon for verifying subtle rim draft angle
        if args.test_wedge and args.tester in ["all", "lip_0.5deg"]:
            model_lip_05 = create_shelf_dovetail_test_wedge(
                dovetail_height=args.dovetail_height,
                top_neck_w=args.top_neck_w,
                bot_neck_w=args.bot_neck_w,
                top_flange_w=args.top_flange_w,
                bot_flange_w=args.bot_flange_w,
                neck_depth=args.neck_depth,
                flange_thick_bot=args.flange_thick_bot,
                flange_delta_top=args.flange_delta_top,
                draft_angle=0.5,
                inside_fillet=args.inside_fillet,
                mount_wings=True,
                no_wings=False,
                handle_extension=max(args.handle_extension, 22.0),
                lip_dist=args.lip_dist,
                lip_depth=args.lip_depth,
                lip_chamfer=args.lip_chamfer,
                label="LIP .5",
            )
            filename_lip_05 = "shelf_edge_dovetail_lip_test_0.5deg.stl"
            oriented_lip_05 = orient_for_export(model_lip_05, args.print_orientation)
            export_model(
                oriented_lip_05,
                filename_lip_05,
                category="shelf",
                export=args.export,
                print_orientation="none",
            )
            print(f"Exported extended lip test coupon (0.5 deg draft comparison): {filename_lip_05}")

        # 3. Thickness Calibration Coupons (+0.1, +0.2, +0.3 mm)
        calib_steps = [
            ("shelf_edge_test_plus0.1mm.stl", 0.1, "+0.1", "calib_0.1"),
            ("shelf_edge_test_plus0.2mm.stl", 0.2, "+0.2", "calib_0.2"),
            ("shelf_edge_test_plus0.3mm.stl", 0.3, "+0.3", "calib_0.3"),
        ]
        for filename_cal, delta, lbl, cal_choice in calib_steps:
            if args.test_wedge and args.tester in ["all", "calib", cal_choice]:
                model_cal = create_shelf_dovetail_test_wedge(
                    dovetail_height=args.dovetail_height,
                    top_neck_w=args.top_neck_w,
                    bot_neck_w=args.bot_neck_w,
                    top_flange_w=args.top_flange_w,
                    bot_flange_w=args.bot_flange_w,
                    neck_depth=args.neck_depth,
                    flange_thick_bot=args.flange_thick_bot,
                    flange_delta_top=delta,
                    draft_angle=args.draft_angle,
                    inside_fillet=args.inside_fillet,
                    mount_wings=True,
                    no_wings=False,
                    handle_extension=args.handle_extension,
                    lip_dist=args.lip_dist,
                    lip_depth=args.lip_depth,
                    lip_chamfer=args.lip_chamfer,
                    label=lbl,
                )
                oriented_cal = orient_for_export(model_cal, args.print_orientation)
                export_model(
                    oriented_cal,
                    filename_cal,
                    category="shelf",
                    export=args.export,
                    print_orientation="none",
                )
                print(f"Exported calibration test coupon ({lbl} mm top delta): {filename_cal}")

        if args.test_taper:
            # Compute taper parameters for pure taper coupons (NO mount wings):
            cur_half_angle_deg = math.degrees(
                math.atan((args.top_flange_w - args.bot_flange_w) / 2.0 / args.dovetail_height)
            )
            new_half_angle_deg = cur_half_angle_deg + 2.0
            delta_w_plus2deg = 2.0 * args.dovetail_height * math.tan(math.radians(new_half_angle_deg))

            taper_testers = []

            # Tester 1A: Trim width at top by 2 mm (top 39, bottom 35)
            if args.tester in ["all", "top_trim2mm"]:
                taper_testers.append((
                    "shelf_edge_dovetail_taper_test_top_trim2mm.stl",
                    args.top_neck_w - 2.0,
                    args.bot_neck_w,
                    args.top_flange_w - 2.0,
                    args.bot_flange_w,
                    "Tester 1A (top trimmed 2mm: 39mm top / 35mm bottom)",
                    "1A",
                ))

            # Tester 1B: Trim overall width by 2 mm (top 39, bottom 33, preserving original taper rate)
            if args.tester in ["all", "width_minus2mm"]:
                taper_testers.append((
                    "shelf_edge_dovetail_taper_test_width_minus2mm.stl",
                    args.top_neck_w - 2.0,
                    args.bot_neck_w - 2.0,
                    args.top_flange_w - 2.0,
                    args.bot_flange_w - 2.0,
                    "Tester 1B (overall width -2mm: 39mm top / 33mm bottom)",
                    "1B",
                ))

            # Tester 2: Increase taper by 2 degrees per side (top 41, bottom 33.2)
            if args.tester in ["all", "taper_plus2deg"]:
                bot_flange_2deg = round(args.top_flange_w - delta_w_plus2deg, 1)
                bot_neck_2deg = round(args.top_neck_w - delta_w_plus2deg, 1)
                taper_testers.append((
                    "shelf_edge_dovetail_taper_test_taper_plus2deg.stl",
                    args.top_neck_w,
                    bot_neck_2deg,
                    args.top_flange_w,
                    bot_flange_2deg,
                    f"Tester 2 (taper +2 deg/side: 41mm top / {bot_flange_2deg}mm bottom)",
                    "2",
                ))

            # Tester 1A+2: Top trimmed to 39 mm AND taper increased by 2 degrees (top 39, bottom 31.2)
            if args.tester in ["all", "top39_plus2deg"]:
                bot_flange_combo = round((args.top_flange_w - 2.0) - delta_w_plus2deg, 1)
                bot_neck_combo = round((args.top_neck_w - 2.0) - delta_w_plus2deg, 1)
                taper_testers.append((
                    "shelf_edge_dovetail_taper_test_top39_plus2deg.stl",
                    args.top_neck_w - 2.0,
                    bot_neck_combo,
                    args.top_flange_w - 2.0,
                    bot_flange_combo,
                    f"Tester 1A+2 (top 39mm & taper +2 deg/side: 39mm top / {bot_flange_combo}mm bottom)",
                    "1A+2",
                ))

            for filename_t, t_neck, b_neck, t_flange, b_flange, desc, lbl in taper_testers:
                m_taper = create_shelf_dovetail_test_wedge(
                    dovetail_height=args.dovetail_height,
                    top_neck_w=t_neck,
                    bot_neck_w=b_neck,
                    top_flange_w=t_flange,
                    bot_flange_w=b_flange,
                    neck_depth=args.neck_depth,
                    flange_thick_bot=args.flange_thick_bot,
                    draft_angle=args.draft_angle,
                    inside_fillet=args.inside_fillet,
                    mount_wings=False,
                    no_wings=False,
                    handle_extension=args.handle_extension,
                    lip_dist=args.lip_dist,
                    lip_depth=args.lip_depth,
                    lip_chamfer=args.lip_chamfer,
                    label=lbl,
                )
                oriented_t = orient_for_export(m_taper, args.print_orientation)
                export_model(
                    oriented_t,
                    filename_t,
                    category="shelf",
                    export=args.export,
                    print_orientation="none",
                )
                print(f"Exported {desc} with label '{lbl}': {filename_t}")

            # Also update standard alias shelf_edge_dovetail_taper_test.stl to winning 1A dimensions
            if args.tester in ["all", "top_trim2mm"]:
                m_alias = create_shelf_dovetail_test_wedge(
                    dovetail_height=args.dovetail_height,
                    top_neck_w=args.top_neck_w,
                    bot_neck_w=args.bot_neck_w,
                    top_flange_w=args.top_flange_w,
                    bot_flange_w=args.bot_flange_w,
                    neck_depth=args.neck_depth,
                    flange_thick_bot=args.flange_thick_bot,
                    draft_angle=args.draft_angle,
                    inside_fillet=args.inside_fillet,
                    mount_wings=False,
                    no_wings=False,
                    handle_extension=args.handle_extension,
                    lip_dist=args.lip_dist,
                    lip_depth=args.lip_depth,
                    lip_chamfer=args.lip_chamfer,
                    label="1A",
                )
                oriented_alias = orient_for_export(m_alias, args.print_orientation)
                export_model(
                    oriented_alias,
                    "shelf_edge_dovetail_taper_test.stl",
                    category="shelf",
                    export=args.export,
                    print_orientation="none",
                )
                print("Exported default taper test alias with label '1A': shelf_edge_dovetail_taper_test.stl")
    else:
        if args.units > 7:
            print(
                f"Note: Mount width ({args.units}U, {args.units * UNIT_WIDTH}mm) "
                f"exceeds the recommended maximum printable width (7U, 196.0mm)."
            )
        model = create_shelf_edge_adapter(
            units=args.units,
            rail_height=args.rail_height,
            screw_m=args.screw,
            with_screws=with_screws,
            dovetail_height=args.dovetail_height,
            top_neck_w=args.top_neck_w,
            bot_neck_w=args.bot_neck_w,
            top_flange_w=args.top_flange_w,
            bot_flange_w=args.bot_flange_w,
            neck_depth=args.neck_depth,
            flange_thick_bot=args.flange_thick_bot,
            flange_delta_top=args.flange_delta_top,
            draft_angle=args.draft_angle,
            lobe_fillet=DEFAULT_LOBE_FILLET,
            inside_fillet=args.inside_fillet,
            side_chamfer=args.side_chamfer,
            slot_spacing=args.slot_spacing,
            lip_dist=args.lip_dist,
            lip_depth=args.lip_depth,
            lip_chamfer=args.lip_chamfer,
            push_hole_angle=args.push_hole_angle,
            push_hole_dia=args.push_hole_dia,
            dovetail_count=args.dovetails,
        )
        screw_tag = args.screw if with_screws else "no_screws"
        filename = f"shelf_edge_adapter_{args.units}u_H{int(args.rail_height)}_{screw_tag}.stl"
        oriented_model = orient_for_export(model, args.print_orientation)
        export_model(
            oriented_model,
            filename,
            category="shelf",
            export=args.export,
            print_orientation="none",
        )
        print(f"Exported adapter: {filename}")


if __name__ == "__main__":
    main()
