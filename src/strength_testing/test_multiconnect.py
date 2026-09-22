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
import os
import pyvista as pv

def load_mc_block(filename):
    path = os.path.join('../../opengrid/Multiconnect Modeling Files', filename)
    model = cq.importers.importStep(path).val()
    
    # We want the opening (which is at Z=6.4) to face -Z.
    # So we rotate 180 around X.
    model = model.rotate((0,0,0), (1,0,0), 180)
    
    bb = model.BoundingBox()
    dx = - (bb.xmin + bb.xmax) / 2
    dy = - (bb.ymin + bb.ymax) / 2
    dz = - bb.zmin # now zmin is -6.4, so dz is +6.4. model will go from Z=0 to Z=6.4
    
    # Wait, if we rotated around X, the Y axis is flipped!
    # top_block is now at the bottom, etc.
    # To avoid flipping Y, let's rotate 180 around Y instead!
    return cq.importers.importStep(path).val().rotate((0,0,0), (0,1,0), 180)

def load_and_center(filename):
    model = load_mc_block(filename)
    bb = model.BoundingBox()
    dx = - (bb.xmin + bb.xmax) / 2
    dy = - (bb.ymin + bb.ymax) / 2
    # we want the opening (zmin) to be at 0, and solid part at 6.4
    dz = - bb.zmin
    return model.translate((dx, dy, dz))

top_block = load_and_center('top-back.step')
mid_block = load_and_center('opening-raw-slot-back.step')
bot_block = load_and_center('embed-back-end.step')

num_rows = 2
units = 2
width = units * 28.0
height = num_rows * 28.0 + 14.0
backplate_thickness = 11.0

solid_thickness = backplate_thickness - 6.4
solid_box = (
    cq.Workplane('XY')
    .box(width, height, solid_thickness)
    .translate((0, 28.0 - height/2, -solid_thickness/2))
)

result = solid_box

for c in range(units):
    x_center = -width/2 + 14.0 + c*28.0
    
    y_top = 28.0 - 14.0
    inst = top_block.translate((x_center, y_top, -backplate_thickness))
    result = result.union(cq.Workplane(inst))
    
    for r in range(1, num_rows):
        y_mid = 28.0 - 14.0 - r*28.0
        inst = mid_block.translate((x_center, y_mid, -backplate_thickness))
        result = result.union(cq.Workplane(inst))
        
    y_bot = 28.0 - num_rows*28.0 - 7.0
    inst = bot_block.translate((x_center, y_bot, -backplate_thickness))
    result = result.union(cq.Workplane(inst))

cq.exporters.export(result, 'test_mc_solid.stl')
mesh = pv.read('test_mc_solid.stl')
plotter = pv.Plotter(off_screen=True)
plotter.add_mesh(mesh, color='orange', show_edges=True)
plotter.camera_position = 'xy'
plotter.screenshot('test_mc_solid_front.png')
plotter.camera.azimuth = 180
plotter.screenshot('test_mc_solid_back.png')
