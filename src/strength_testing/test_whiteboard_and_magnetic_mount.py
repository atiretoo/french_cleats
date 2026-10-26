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

        # Check for circular edges: 19.2 mm dia (r=9.6) magnet pockets, 2.0 mm dia (r=1.0) push holes
        circle_radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]

        pocket_edges = circle_radii.count(9.6)
        push_edges = circle_radii.count(1.0)

        # 1 pocket per unit = 2 pockets (each cylinder feature has circular rims)
        self.assertGreaterEqual(pocket_edges, units)
        self.assertGreaterEqual(push_edges, units)

    def test_single_unit_adapter(self):
        adapter = create_magnetic_adapter(units=1)
        solid = adapter.val()
        self.assertEqual(len(solid.Solids()), 1)
        self.assertAlmostEqual(solid.BoundingBox().xlen, 28.0, delta=0.1)

    def test_magnetic_adapter_2u_4mags(self):
        adapter = create_magnetic_adapter(units=2, mag_count=2, rail_height=73.0)
        solid = adapter.val()

        # Single solid
        self.assertEqual(len(solid.Solids()), 1)

        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.xlen, 56.0, delta=0.2)
        self.assertAlmostEqual(bb.ylen, 114.0, delta=0.2)
        self.assertAlmostEqual(bb.ymin, -94.0, delta=0.2)
        self.assertAlmostEqual(bb.ymax, 20.0, delta=0.2)

        # Check for 4 magnet pockets (2 vertically aligned per 1U space)
        circle_radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]
        pocket_edges = circle_radii.count(9.6)
        push_edges = circle_radii.count(1.0)

        # 4 pockets total: at least 4 edges of r=9.6 and r=1.0
        self.assertGreaterEqual(pocket_edges, 4)
        self.assertGreaterEqual(push_edges, 4)


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

        # Shelf thickness check: shelf is from Y=-94.0 to Y=-64.0 (30.0 mm thick)
        shelf_faces = [
            f for f in solid.Faces()
            if f.geomType() == "PLANE" and abs(f.Center().y - (-64.0)) < 0.2
        ]
        self.assertTrue(len(shelf_faces) > 0, "Shelf top face should be at Y = -64.0")

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

    def test_print_orientation_bottom_down(self):
        holder = create_whiteboard_tool_holder(units=4)
        # Apply the bottom_down rotation: rotate around (1, 0, 0) by +90 deg
        rotated = holder.rotate((0, 0, 0), (1, 0, 0), 90)
        bb = rotated.val().BoundingBox()

        # In bottom_down orientation, the bottom face (Y=-94 in CAD) should be at zmin
        # and the top (Y=20 in CAD) should be at zmax
        self.assertAlmostEqual(bb.zmin, -94.0, delta=0.2)
        self.assertAlmostEqual(bb.zmax, 20.0, delta=0.2)

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

        # Check for circular edge with bottle radius = 36.5 / 2 = 18.25
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


if __name__ == "__main__":
    unittest.main()
