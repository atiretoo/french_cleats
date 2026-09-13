import cadquery as cq
import argparse

from holder_base import create_baseplate

def create_chisel_holder(units=4, hole_size=15.0, slot_width=26.0, slot_depth=4.0, rail_height=73.0, shelf_pos="mid"):
    unit_width = 28.0
    width = units * unit_width
    shelf_depth = 28.0 # 1U deep
    
    # Create Baseplate
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(units, rail_height, mount_type="groove", num_rows=2)
    
    if shelf_pos == "top":
        shelf_top = top_y
    else:
        shelf_top = top_y - 40.0
        
    shelf_bot = shelf_top - 5.0
    
    # Add Shelf
    shelf_pts = [
        (shelf_bot, -11),
        (shelf_bot, -11 - shelf_depth),
        (shelf_top, -11 - shelf_depth),
        (shelf_top, -11)
    ]
    shelf = (
        cq.Workplane("YZ")
        .polyline(shelf_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    tool_holder = tool_holder.union(shelf)
    
    # Fillet only the top and bottom edges of the shelf where it meets the backplate
    class FilletSelector(cq.Selector):
        def filter(self, objectList):
            res = []
            for o in objectList:
                if not isinstance(o, cq.Edge): continue
                b = o.BoundingBox()
                if abs(b.ymin - shelf_top) < 1 and abs(b.zmin - (-11)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
                elif abs(b.ymin - shelf_bot) < 1 and abs(b.zmin - (-11)) < 1 and b.xmax - b.xmin > 10:
                    res.append(o)
            return res

    try:
        tool_holder = tool_holder.edges(FilletSelector()).fillet(5.0)
    except:
        pass # fallback if filleting fails
    
    # Cut holes and slots independently to avoid self-intersection boolean bugs
    hole_pts = []
    z_center = -11.0 - shelf_depth / 2.0
    for i in range(units):
        x = -width/2 + unit_width/2 + i * unit_width
        hole_pts.append((x, z_center))
        
    holes = (
        cq.Workplane("XZ", origin=(0, shelf_bot - 10.0, 0))
        .pushPoints(hole_pts)
        .circle(hole_size / 2.0)
        .extrude(-40.0)
    )
    tool_holder = tool_holder.cut(holes)
    
    slots = (
        cq.Workplane("XZ", origin=(0, shelf_bot - 10.0, 0))
        .pushPoints(hole_pts)
        .rect(slot_width, slot_depth)
        .extrude(-40.0)
    )
    tool_holder = tool_holder.cut(slots)
    
    # Cut screws
    screws = (
        cq.Workplane("XY").workplane(offset=0)
        .pushPoints(screw_pts)
        .circle(3.6/2.0)
        .extrude(-20) 
    )
    tool_holder = tool_holder.cut(screws)
    
    recesses = (
        cq.Workplane("XY").workplane(offset=-8)
        .pushPoints(screw_pts)
        .circle(8.0/2.0) 
        .extrude(-200) 
    )
    tool_holder = tool_holder.cut(recesses)
    
    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat chisel holder")
    parser.add_argument("--units", type=int, default=4, help="Number of units wide")
    parser.add_argument("--hole-size", type=float, default=15.0, help="Diameter of the central hole in mm")
    parser.add_argument("--slot-width", type=float, default=26.0, help="Width of the slot in mm")
    parser.add_argument("--slot-depth", type=float, default=4.0, help="Depth of the slot in mm")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--shelf-pos", choices=["mid", "top"], default="mid", help="Position of the shelf on the backplate")
    args = parser.parse_args()
    
    holder = create_chisel_holder(
        units=args.units, 
        hole_size=args.hole_size, 
        slot_width=args.slot_width,
        slot_depth=args.slot_depth,
        rail_height=args.rail_height,
        shelf_pos=args.shelf_pos
    )
    
    filename = f"chisel_holder_{args.units}u_{args.shelf_pos}_groove_H{args.rail_height}.stl"
    cq.exporters.export(holder, filename)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
