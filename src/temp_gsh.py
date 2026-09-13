import cadquery as cq
import argparse

from holder_base import create_baseplate

def create_screwdriver_holder(units=2, num_screwdrivers=2, rail_height=73.0, mount_type="groove"):
    unit_width = 28.0
    width = units * unit_width
    
    hole_spacing = width / num_screwdrivers
    hole_diameter = 15.0
    slot_width = 10.0
    
    tool_holder, top_y, bottom_y, bottom_groove_y, screw_pts, slots_to_cut = create_baseplate(units, rail_height, mount_type=mount_type, num_rows=2)
    
    shelf_top = top_y - 40.0
    shelf_bot = top_y - 50.0
    
    shelf_pts = [
        (shelf_top, -11),
        (shelf_top, -46),
        (shelf_bot, -46),
        (shelf_bot, -11)
    ]
    shelf = (
        cq.Workplane("YZ")
        .polyline(shelf_pts).close()
        .extrude(width)
        .translate((-width/2, 0, 0))
    )
    tool_holder = tool_holder.union(shelf)
    
    brace_pts = [
        (bottom_y, -11),
        (shelf_bot, -11),
        (shelf_bot, -46)
    ]
    
    num_braces = num_screwdrivers + 1
    brace_thickness = 4.0
    
    for i in range(num_braces):
        x_pos = -width/2 + i * hole_spacing
        
        if i == 0:
            x_pos = -width/2 + brace_thickness/2
        elif i == num_braces - 1:
            x_pos = width/2 - brace_thickness/2
            
        brace = (
            cq.Workplane("YZ")
            .polyline(brace_pts).close()
            .extrude(brace_thickness)
            .translate((x_pos - brace_thickness/2, 0, 0))
        )
        tool_holder = tool_holder.union(brace)
        
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

    # skipped fillet
    
    hole_centers_x = [-width/2 + hole_spacing/2 + i*hole_spacing for i in range(num_screwdrivers)]
    hole_pts = [(x, -28) for x in hole_centers_x]
    
    holes = (
        cq.Workplane("XZ", origin=(0, shelf_top + 1, 0))
        .pushPoints(hole_pts)
        .circle(hole_diameter/2)
        .extrude(20) 
    )
    tool_holder = tool_holder.cut(holes)
    
    slot_pts = [(x, -28 - 20/2) for x in hole_centers_x]
    
    slots = (
        cq.Workplane("XZ", origin=(0, shelf_top + 1, 0))
        .pushPoints(slot_pts)
        .rect(slot_width, 20)
        .extrude(20) 
    )
    tool_holder = tool_holder.cut(slots)
    
    if mount_type == "groove":
        screws = (
            cq.Workplane("XY").workplane(offset=0)
            .pushPoints(screw_pts)
            .circle(3.6/2)
            .extrude(-20) 
        )
        tool_holder = tool_holder.cut(screws)
        
        recesses = (
            cq.Workplane("XY").workplane(offset=-8)
            .pushPoints(screw_pts)
            .circle(8.0/2) 
            .extrude(-200) 
        )
        tool_holder = tool_holder.cut(recesses)
    
    for s in slots_to_cut:
        tool_holder = tool_holder.union(s)
    
    return tool_holder

def main():
    parser = argparse.ArgumentParser(description="Generate French Cleat screwdriver holder")
    parser.add_argument("--units", type=int, default=2, help="Number of units wide")
    parser.add_argument("--screwdrivers", type=int, default=0, help="Number of screwdrivers")
    parser.add_argument("--rail-height", type=float, default=73.0, help="Height of rail")
    parser.add_argument("--mount", choices=["groove", "multiconnect"], default="groove", help="Mount type")
    args = parser.parse_args()
    
    screwdrivers = args.screwdrivers if args.screwdrivers > 0 else args.units
    holder = create_screwdriver_holder(args.units, screwdrivers, rail_height=args.rail_height, mount_type=args.mount)
    filename = f"screwdriver_holder_{args.units}u_{args.mount}_H{args.rail_height}.stl"
    cq.exporters.export(holder, filename)
    print(f"Exported {filename}")

if __name__ == "__main__":
    main()
