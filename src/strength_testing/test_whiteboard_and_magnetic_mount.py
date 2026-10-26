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
    create_baseplate,
)
from tool_holders.generate_whiteboard_tool_holder import create_whiteboard_tool_holder


class TestMagneticMount(unittest.TestCase):
    def test_magnetic_baseplate_geometry(self):
        units = 4
        bp, top_y, bottom_y, bottom_groove_y, screw_pts, _ = create_baseplate(
            units=units, mount_type="magnetic"
        )
        solid = bp.val()

        # Must be a single solid
        self.assertEqual(len(bp.val().Solids()), 1)

        # Screw points must be empty for magnetic mount
        self.assertEqual(screw_pts, [])

        bb = solid.BoundingBox()
        expected_width = units * UNIT_WIDTH  # 112.0 mm
        expected_bottom_y = get_bottom_edge_y(73.0, RAIL_PLAY)  # -94.0 mm

        self.assertAlmostEqual(bb.xlen, expected_width, delta=0.1)
        self.assertAlmostEqual(bb.ymin, expected_bottom_y, delta=0.1)
        self.assertAlmostEqual(bb.ymax, BACKPLATE_TOP_Y, delta=0.1)
        self.assertAlmostEqual(bb.zlen, BACKPLATE_THICKNESS, delta=0.1)

    def test_magnet_pockets_and_push_holes(self):
        units = 2
        bp, _, _, _, _, _ = create_baseplate(units=units, mount_type="magnetic")
        solid = bp.val()

        # Verify circular edges exist for the magnet pockets (radius 19.2/2 = 9.6)
        # and push holes (radius 2.0/2 = 1.0)
        circle_radii = [round(e.radius(), 2) for e in solid.Edges() if e.geomType() == "CIRCLE"]

        # Each cylinder pocket has 2 circular edges (top and bottom rim)
        pocket_edges = circle_radii.count(9.6)
        push_edges = circle_radii.count(1.0)

        self.assertEqual(pocket_edges, units * 2, f"Expected {units * 2} circular edges for dia 19.2mm pockets")
        self.assertEqual(push_edges, units * 2, f"Expected {units * 2} circular edges for dia 2.0mm push holes")


class TestWhiteboardToolHolder(unittest.TestCase):
    def test_whiteboard_holder_magnetic_default(self):
        holder = create_whiteboard_tool_holder(units=4, mount_type="magnetic")
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
        # Check that geometry extends forward (-Z) up to Y = -64.0
        shelf_faces = [
            f for f in solid.Faces()
            if f.geomType() == "PLANE" and abs(f.Center().y - (-64.0)) < 0.2
        ]
        self.assertTrue(len(shelf_faces) > 0, "Shelf top face should be at Y = -64.0")

    def test_whiteboard_holder_groove_mount(self):
        holder = create_whiteboard_tool_holder(units=4, mount_type="groove")
        solid = holder.val()

        self.assertEqual(len(solid.Solids()), 1)
        bb = solid.BoundingBox()
        self.assertAlmostEqual(bb.xlen, 4 * UNIT_WIDTH, delta=0.2)

    def test_whiteboard_holder_layout_swap(self):
        holder_left = create_whiteboard_tool_holder(units=4, layout="bottle_left")
        holder_right = create_whiteboard_tool_holder(units=4, layout="eraser_left")

        self.assertEqual(len(holder_left.val().Solids()), 1)
        self.assertEqual(len(holder_right.val().Solids()), 1)

    def test_whiteboard_holder_through_holes(self):
        holder = create_whiteboard_tool_holder(units=4, floor_thickness=0.0)
        solid = holder.val()
        self.assertEqual(len(solid.Solids()), 1)


if __name__ == "__main__":
    unittest.main()
