import numpy as np
from stl import mesh

def analyze_stl(filename):
    m = mesh.Mesh.from_file(filename)
    points = m.vectors.reshape(-1, 3)
    # Get unique YZ coordinates assuming X is the extrusion axis
    # We will slice near x=0
    x_mid = (np.min(points[:,0]) + np.max(points[:,0])) / 2
    
    print(f"--- Analysis of {filename} ---")
    print(f"X range: {np.min(points[:,0]):.2f} to {np.max(points[:,0]):.2f}")
    print(f"Y range: {np.min(points[:,1]):.2f} to {np.max(points[:,1]):.2f}")
    print(f"Z range: {np.min(points[:,2]):.2f} to {np.max(points[:,2]):.2f}")
    
    # Let's project all points to YZ plane and find the convex hull or unique points
    yz_points = np.unique(points[:, 1:], axis=0)
    # Round to 1 decimal place to group close points
    yz_rounded = np.unique(np.round(yz_points, 1), axis=0)
    
    # Sort by Y then Z to easily read them
    # But better to trace the perimeter. Let's just print the unique YZ points.
    print("Unique Y,Z pairs (cross-section):")
    for pt in yz_rounded:
        print(f"  Y: {pt[0]:.1f}, Z: {pt[1]:.1f}")

analyze_stl("saw-and-thin-tool-holder-with-french-cleat-backer/top cleat attachent.stl")
analyze_stl("saw-and-thin-tool-holder-with-french-cleat-backer/bottom cleat attachment.stl")
