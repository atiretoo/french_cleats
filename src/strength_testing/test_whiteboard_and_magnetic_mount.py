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
import unittest
import cadquery as cq
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import (
    UNIT_WIDTH,
    BACKPLATE_THICKNESS,
    BACKPLATE_TOP_Y,
    get_bottom_edge_y,
    RAIL_PLAY,
    RIDGE_HEIGHT,
)
from magnetic.generate_magnetic_adapter import create_magnetic_adapter
from tool_holders.generate_whiteboard_tool_holder import create_whiteboard_tool_holder
from tool_holders.generate_whiteboard_pen_holder import (
    create_whiteboard_pen_holder,
    create_whiteboard_pen_coupon,
)
from strength_testing.generate_whiteboard_coupon import create_whiteboard_test_coupon


class TestMagneticAdapter(unittest.TestCase):
    def test_magnetic_adapter_geometry(self):
        units = 4
        adapter = create_magnetic_adapter(units=units)
        solid = adapter.val()

        # Must be a single solid
        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        expected_width = units * UNIT_WIDTH  # 112.0 mm
        expected_bottom_y = get_bottom_edge_y(73.0, RAIL_PLAY)  # -94.0 mm
        expected_z_len = 6.0 + RIDGE_HEIGHT  # 6.0 mm plate + 2.2 mm ridge = 8.2 mm

        self.assertAlmostEqual(bb.xlen, expected_width, delta=0.2)
        self.assertAlmostEqual(bb.ymin, expected_bottom_y, delta=0.2)
        self.assertAlmostEqual(bb.ymax, BACKPLATE_TOP_Y, delta=0.2)
        self.assertAlmostEqual(bb.zlen, expected_z_len, delta=0.2)

        # Front ridges should protrude into -Z down to Z = -2.2 mm
        self.assertAlmostEqual(bb.zmin, -RIDGE_HEIGHT, delta=0.2)
        # Back face rests at Z = 6.0 mm
        self.assertAlmostEqual(bb.zmax, 6.0, delta=0.2)

    def test_magnet_pockets_and_push_holes(self):
        units = 2
        adapter = create_magnetic_adapter(units=units)
        solid = adapter.val()

        # Check for circular edges: 19.25 mm dia compliant pocket bore (r=9.78 with clearance), 5.0 mm dia (r=2.5) push holes
        circle_radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]

        pocket_edges = circle_radii.count(9.78)
        push_edges = circle_radii.count(2.5)

        # Default auto layout fits 3 magnets per unit = 6 pockets total for 2U
        self.assertGreaterEqual(pocket_edges, 6)
        self.assertGreaterEqual(push_edges, 6)

    def test_single_unit_adapter(self):
        adapter = create_magnetic_adapter(units=1)
        solid = adapter.val()
        self.assertEqual(len(solid.Solids()), 1)
        self.assertAlmostEqual(solid.BoundingBox().xlen, 28.0, delta=0.1)

    def test_magnetic_adapter_2u_4mags(self):
        adapter = create_magnetic_adapter(units=2, mag_count=2, rail_height=73.0)
        solid = adapter.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.xlen, 56.0, delta=0.2)
        self.assertAlmostEqual(bb.ylen, 114.0, delta=0.2)
        self.assertAlmostEqual(bb.ymin, -94.0, delta=0.2)
        self.assertAlmostEqual(bb.ymax, 20.0, delta=0.2)

        circle_radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        pocket_edges = circle_radii.count(9.78)
        push_edges = circle_radii.count(2.5)

        # Explicit mag_count=2 = 4 pockets total for 2U
        self.assertGreaterEqual(pocket_edges, 4)
        self.assertGreaterEqual(push_edges, 4)

    def test_magnetic_adapter_auto_packing(self):
        from magnetic.generate_magnetic_adapter import compute_magnet_layout
        from core_library import LARGE_MAGNET_DIA

        # At 73mm rail height, exactly 3 large magnets fit per 1U space
        count_73, ys_73 = compute_magnet_layout(rail_height=73.0, mag_dia=LARGE_MAGNET_DIA)
        self.assertEqual(count_73, 3)
        self.assertEqual(len(ys_73), 3)

        # At 50mm rail height, 2 large magnets fit per 1U space
        count_50, ys_50 = compute_magnet_layout(rail_height=50.0, mag_dia=LARGE_MAGNET_DIA)
        self.assertEqual(count_50, 2)
        self.assertEqual(len(ys_50), 2)

        # At 100mm rail height, 4 large magnets fit per 1U space
        count_100, ys_100 = compute_magnet_layout(rail_height=100.0, mag_dia=LARGE_MAGNET_DIA)
        self.assertEqual(count_100, 4)
        self.assertEqual(len(ys_100), 4)

    def test_magnetic_adapter_45deg_print_orientation(self):
        adapter = create_magnetic_adapter(units=2, mag_count=2, print_orientation="45_deg", support_fins=True)
        solid = adapter.val()
        self.assertGreaterEqual(len(solid.Solids()), 1)

        # Build plate should be at zmin = 0
        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.zmin, 0.0, delta=0.1)

        # Support fins should be aligned with the first convex edge of each ridge:
        # Top ridge first convex edge: Y = 10.0 - 1.1 = 8.90
        # Bottom ridge first convex edge: Y = -84.0 + 1.1 = -82.90
        fin_faces_top = [
            f for f in solid.Faces()
            if abs(f.Center().y - 8.90) < 0.2 and f.geomType() == "PLANE"
        ]
        fin_faces_bot = [
            f for f in solid.Faces()
            if abs(f.Center().y - (-82.90)) < 0.2 and f.geomType() == "PLANE"
        ]
        self.assertTrue(len(fin_faces_top) > 0, "Top fin not found at convex edge Y=8.90")
        self.assertTrue(len(fin_faces_bot) > 0, "Bottom fin not found at convex edge Y=-82.90")

    def test_magnetic_adapter_nut_slots_push_hole(self):
        adapter = create_magnetic_adapter(units=2, mag_count=2, print_orientation="none", support_fins=False)
        solid = adapter.val()

        # At the top nut slot end wall (Y = 10.0 - 3.175 = 6.825), the push out hole must be
        # fully open with a single continuous ellipse wire, without obstructing shelf faces.
        end_wall_faces = [
            f for f in solid.Faces()
            if abs(f.Center().y - 6.825) < 0.2 and f.geomType() == "PLANE"
        ]
        self.assertTrue(len(end_wall_faces) > 0, "Top nut slot end wall face not found")
        top_end_wall = end_wall_faces[0]
        # Should contain slot outer boundary wire and hole ellipse wire (exactly 2 wires, 1 ellipse)
        hole_wires = [w for w in top_end_wall.Wires() if len(w.Edges()) == 1 and w.Edges()[0].geomType() == "ELLIPSE"]
        self.assertEqual(len(hole_wires), 1, "Push hole through nut slot end wall should be a clean, single ellipse")


class TestWhiteboardToolHolder(unittest.TestCase):
    def test_whiteboard_holder_groove_default(self):
        holder = create_whiteboard_tool_holder(units=4)
        solid = holder.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        expected_width = 4 * UNIT_WIDTH  # 112.0 mm
        expected_depth = 50.0 + BACKPLATE_THICKNESS  # 61.0 mm
        expected_bottom_y = get_bottom_edge_y(73.0, RAIL_PLAY)  # -94.0 mm

        self.assertAlmostEqual(bb.xlen, expected_width, delta=0.2)
        self.assertAlmostEqual(bb.ymin, expected_bottom_y, delta=0.2)
        self.assertAlmostEqual(bb.ymax, BACKPLATE_TOP_Y, delta=0.2)
        self.assertAlmostEqual(bb.zlen, expected_depth, delta=0.2)

        # Shelf thickness check: elevated shelf is from Y=-70.0 to Y=-40.0 (30.0 mm thick)
        shelf_faces = [
            f for f in solid.Faces()
            if f.geomType() == "PLANE" and abs(f.Center().y - (-40.0)) < 0.2
        ]
        self.assertTrue(len(shelf_faces) > 0, "Shelf top face should be at Y = -40.0")

    def test_whiteboard_holder_both_screw_rows(self):
        holder = create_whiteboard_tool_holder(units=2, layout="inline_2u")
        solid = holder.val()

        # Both top screws (Y=10.0) and bottom screws (Y=-84.0) should have holes
        # 3.6mm dia hole edges (radius 1.8)
        radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        screw_hole_edges = radii.count(1.8)
        # 2 units * 2 rows = 4 screw holes -> each cylinder has at least 2 circular edges
        self.assertGreaterEqual(screw_hole_edges, 4)

    def test_whiteboard_holder_inline_2u(self):
        holder = create_whiteboard_tool_holder(layout="inline_2u")
        solid = holder.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        expected_width = 2 * UNIT_WIDTH  # 56.0 mm
        expected_depth = 111.0 + BACKPLATE_THICKNESS  # 122.0 mm
        expected_bottom_y = get_bottom_edge_y(73.0, RAIL_PLAY)  # -94.0 mm

        self.assertAlmostEqual(bb.xlen, expected_width, delta=0.2)
        self.assertAlmostEqual(bb.ymin, expected_bottom_y, delta=0.2)
        self.assertAlmostEqual(bb.ymax, BACKPLATE_TOP_Y, delta=0.2)
        self.assertAlmostEqual(bb.zlen, expected_depth, delta=0.2)

    def test_whiteboard_holder_inline_3u(self):
        holder = create_whiteboard_tool_holder(layout="inline_3u")
        solid = holder.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        expected_width = 3 * UNIT_WIDTH  # 84.0 mm
        expected_depth = 88.0 + BACKPLATE_THICKNESS  # 99.0 mm
        expected_bottom_y = get_bottom_edge_y(73.0, RAIL_PLAY)  # -94.0 mm

        self.assertAlmostEqual(bb.xlen, expected_width, delta=0.2)
        self.assertAlmostEqual(bb.ymin, expected_bottom_y, delta=0.2)
        self.assertAlmostEqual(bb.ymax, BACKPLATE_TOP_Y, delta=0.2)
        self.assertAlmostEqual(bb.zlen, expected_depth, delta=0.2)

    def test_whiteboard_holder_45deg_print_orientation(self):
        holder = create_whiteboard_tool_holder(layout="inline_2u", print_orientation="45_deg", support_fins=True)
        solid = holder.val()
        self.assertGreaterEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.zmin, 0.0, delta=0.1)

        # Fin tapered edges should be aligned directly with the edges:
        # Top chamfer convex edge at Y = -18.0
        # Bottom chamfer convex edge at Y = 92.0
        # Shelf projection edge at Y = 70.0
        tip_faces = [
            f.Center().y for f in solid.Faces()
            if f.geomType() == "PLANE" and abs(abs(f.normalAt().x) - 0.707) < 0.05 and abs(abs(f.normalAt().z) - 0.707) < 0.05 and f.Area() < 50.0
        ]
        self.assertTrue(any(abs(y - (-18.0)) < 0.2 for y in tip_faces), "Top backplate fin tip not aligned at Y=-18.0")
        self.assertTrue(any(abs(y - 92.0) < 0.2 for y in tip_faces), "Bottom backplate fin tip not aligned at Y=92.0")
        self.assertTrue(any(abs(y - 70.0) < 0.2 for y in tip_faces), "Shelf fin tip not aligned at Y=70.0")

    def test_whiteboard_holder_layout_swap(self):
        holder_left = create_whiteboard_tool_holder(units=4, layout="bottle_left")
        holder_right = create_whiteboard_tool_holder(units=4, layout="eraser_left")

        self.assertEqual(len(holder_left.val().Solids()), 1)
        self.assertEqual(len(holder_right.val().Solids()), 1)

    def test_whiteboard_holder_through_holes(self):
        holder = create_whiteboard_tool_holder(units=4, floor_thickness=0.0)
        solid = holder.val()
        self.assertEqual(len(solid.Solids()), 1)


class TestWhiteboardTestCoupon(unittest.TestCase):
    def test_coupon_geometry_and_holes(self):
        coupon = create_whiteboard_test_coupon(units=4, coupon_height=15.0)
        solid = coupon.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.xlen, 4 * UNIT_WIDTH, delta=0.2)
        self.assertAlmostEqual(bb.ylen, 15.0, delta=0.2)
        self.assertAlmostEqual(bb.zlen, 50.0 + BACKPLATE_THICKNESS, delta=0.2)

        radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        self.assertIn(18.25, radii, "Spray bottle circular edge not found in test coupon")

    def test_coupon_inline_2u(self):
        coupon = create_whiteboard_test_coupon(layout="inline_2u", coupon_height=15.0)
        solid = coupon.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.xlen, 2 * UNIT_WIDTH, delta=0.2)
        self.assertAlmostEqual(bb.ylen, 15.0, delta=0.2)
        self.assertAlmostEqual(bb.zlen, 111.0 + BACKPLATE_THICKNESS, delta=0.2)

        radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        self.assertIn(18.25, radii, "Spray bottle circular edge not found in inline coupon")

    def test_coupon_without_groove(self):
        coupon = create_whiteboard_test_coupon(units=4, coupon_height=15.0, with_groove=False)
        solid = coupon.val()
        self.assertEqual(len(solid.Solids()), 1)


class TestWhiteboardPenHolder(unittest.TestCase):
    def test_whiteboard_pen_holder_1u_geometry(self):
        holder = create_whiteboard_pen_holder(units=1, pen_count=4)
        solid = holder.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        expected_width = 1 * UNIT_WIDTH  # 28.0 mm
        expected_depth = 111.0 + BACKPLATE_THICKNESS  # 122.0 mm
        expected_bottom_y = get_bottom_edge_y(73.0, RAIL_PLAY)  # -94.0 mm

        self.assertAlmostEqual(bb.xlen, expected_width, delta=0.2)
        self.assertAlmostEqual(bb.ymin, expected_bottom_y, delta=0.2)
        self.assertAlmostEqual(bb.ymax, BACKPLATE_TOP_Y, delta=0.2)
        self.assertAlmostEqual(bb.zlen, expected_depth, delta=0.2)

        # Shelf thickness check: elevated shelf is from Y=-70.0 to Y=-40.0 (30.0 mm thick)
        shelf_faces = [
            f for f in solid.Faces()
            if f.geomType() == "PLANE" and abs(f.Center().y - (-40.0)) < 0.2
        ]
        self.assertTrue(len(shelf_faces) > 0, "Shelf top face should be at Y = -40.0")

        shelf_bot_faces = [
            f for f in solid.Faces()
            if f.geomType() == "PLANE" and abs(f.Center().y - (-70.0)) < 0.2
        ]
        self.assertTrue(len(shelf_bot_faces) > 0, "Shelf bottom face should be at Y = -70.0")

        # Circular edges for truncated cone pen pockets:
        # Top opening: cap_opening_dia (11.8) + clearance (0.6) = 12.4 mm dia -> r = 6.2 mm
        # Bottom opening: r_base = 6.2 - (1.65/90) * 30 = 5.65 mm -> dia 11.3 mm
        radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        self.assertGreaterEqual(radii.count(6.2), 4, "Top opening circles missing")
        self.assertGreaterEqual(radii.count(5.65), 4, "Bottom opening circles missing")

    def test_whiteboard_pen_holder_both_screw_rows(self):
        holder = create_whiteboard_pen_holder(units=1, pen_count=4)
        solid = holder.val()

        # Both top screws (Y=10.0) and bottom screws (Y=-84.0) should have holes
        radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        screw_hole_edges = radii.count(1.8)
        self.assertGreaterEqual(screw_hole_edges, 2)

    def test_whiteboard_pen_holder_45deg_print_orientation(self):
        holder = create_whiteboard_pen_holder(units=1, pen_count=4, print_orientation="45_deg", support_fins=True)
        solid = holder.val()
        self.assertGreaterEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.zmin, 0.0, delta=0.1)

        # Fin tapered edges should be aligned directly with the edges:
        tip_faces = [
            f.Center().y for f in solid.Faces()
            if f.geomType() == "PLANE" and abs(abs(f.normalAt().x) - 0.707) < 0.05 and abs(abs(f.normalAt().z) - 0.707) < 0.05 and f.Area() < 50.0
        ]
        self.assertTrue(any(abs(y - (-18.0)) < 0.2 for y in tip_faces), "Pen holder top fin not aligned at Y=-18.0")
        self.assertTrue(any(abs(y - 92.0) < 0.2 for y in tip_faces), "Pen holder bottom fin not aligned at Y=92.0")
        self.assertTrue(any(abs(y - 70.0) < 0.2 for y in tip_faces), "Pen holder shelf fin not aligned at Y=70.0")

    def test_whiteboard_pen_coupon(self):
        coupon = create_whiteboard_pen_coupon(units=1, pen_count=4, coupon_height=15.0)
        solid = coupon.val()

        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.xlen, 1 * UNIT_WIDTH, delta=0.2)
        self.assertAlmostEqual(bb.ylen, 15.0, delta=0.2)
        self.assertAlmostEqual(bb.zlen, 111.0 + BACKPLATE_THICKNESS, delta=0.2)

        radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        self.assertGreaterEqual(radii.count(6.2), 4, "Top opening circles missing in pen coupon")


if __name__ == "__main__":
    unittest.main()
