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

def create_versorium_needle():
    # Layer thickness
    h1 = 0.28
    h2 = 0.28
    
    # Polygon points for the main body
    pts = [
        (24.8, 0.2),       # start of right tip
        (20.0, 0.4),       # start of right taper
        (2.5, 0.4),        # end of right shaft, start of center flare
        (0.5, 0.866),      # tangent point to center circle
        (-0.5, 0.866),     # tangent point to center circle
        (-2.5, 0.4),       # start of left shaft
        (-20.0, 0.4),      # start of left taper
        (-24.8, 0.2),      # start of left tip
        (-24.8, -0.2),     # bottom of left tip
        (-20.0, -0.4),
        (-2.5, -0.4),
        (-0.5, -0.866),
        (0.5, -0.866),
        (2.5, -0.4),
        (20.0, -0.4),
        (24.8, -0.2)
    ]
    
    # Base polygon
    body = cq.Workplane("XY").polyline(pts).close().extrude(h1)
    
    # Center circle (Diameter 2.0mm -> Radius 1.0mm)
    center_circle = cq.Workplane("XY").circle(1.0).extrude(h1)
    
    # Right tip (Diameter 0.4mm -> Radius 0.2mm)
    right_tip = cq.Workplane("XY").center(24.8, 0).circle(0.2).extrude(h1)
    
    # Left tip (Diameter 0.4mm -> Radius 0.2mm)
    left_tip = cq.Workplane("XY").center(-24.8, 0).circle(0.2).extrude(h1)
    
    # Combine layer 1 parts
    layer1 = body.union(center_circle).union(right_tip).union(left_tip)
    
    # Cut the 0.4mm diameter center hole
    hole = cq.Workplane("XY").circle(0.2).extrude(h1)
    layer1 = layer1.cut(hole)
    
    # Layer 2: 1.2mm diameter cap
    cap = cq.Workplane("XY").workplane(offset=h1).circle(0.6).extrude(h2)
    
    # Final assembly
    needle = layer1.union(cap)
    
    return needle

def main():
    needle = create_versorium_needle()
    filename = "versorium_needle.stl"
    cq.exporters.export(needle, filename)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
