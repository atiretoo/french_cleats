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

width = 50.0
t = 0.2
pts = [
    (20, 0),
    (14+t, 0),
    (12+t, -4-t),
    (8-t, -4-t),
    (6-t, 0),
    (-82+t, 0),
    (-84+t, -4-t),
    (-88-t, -4-t),
    (-90-t, 0),
    (-96, 0),
    (-96, -BACKPLATE_THICKNESS),
    (10, -BACKPLATE_THICKNESS),
    (10, -36),
    (20, -36),
    (20, 0)
]

# Create base profile
tool_holder = (
    cq.Workplane("YZ")
    .polyline(pts).close()
    .extrude(width)
    .translate((-width/2, 0, 0))
)

# Fillet the inner corner
try:
    tool_holder = tool_holder.edges(
        cq.selectors.ParallelDirSelector(cq.Vector(1, 0, 0)) &
        cq.selectors.NearestToPointSelector((0, 10, -BACKPLATE_THICKNESS))
    ).fillet(5.0)
except Exception as e:
    print("Fillet error:", e)

# Cut holes and slots
cut_tool = (
    cq.Workplane("ZX").workplane(offset=-20)
    .pushPoints([(-12.5, -23.5), (12.5, -23.5)])
    .circle(15/2)
    .pushPoints([(-12.5, -29.75), (12.5, -29.75)])
    .rect(10, 12.5)
    .extrude(15)
)

tool_holder = tool_holder.cut(cut_tool)

# Chamfer the top edges of the holes and slots
try:
    tool_holder = tool_holder.edges(">Y").edges(cq.selectors.BoxSelector((-20, 19.9, -36.1), (20, 20.1, -15.1))).chamfer(1.0)
    print("Chamfer successful")
except Exception as e:
    print("Chamfer error:", e)

cq.exporters.export(tool_holder, "test.stl")
print("Exported test.stl")
