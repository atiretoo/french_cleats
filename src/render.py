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
import glob
import pyvista as pv
import os

pv.global_theme.background = 'white'
pv.global_theme.color = 'cyan'
pv.global_theme.show_edges = True

files = glob.glob("screwdriver*.stl") + glob.glob("top_cleat*.stl") + glob.glob("bottom_cleat*.stl") + glob.glob("clamp_holder*.stl") + glob.glob("clamp_tester*.stl")
for f in files:
    print(f"Rendering {f}...")
    mesh = pv.read(f)
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(mesh)
    plotter.camera_position = 'iso'
    png_name = f.replace('.stl', '.png')
    plotter.screenshot(png_name)
    print(f"Saved {png_name}")
