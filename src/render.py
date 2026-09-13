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
