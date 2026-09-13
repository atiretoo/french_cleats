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
    (-96, -11),
    (10, -11),
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
        cq.selectors.NearestToPointSelector((0, 10, -11))
    ).fillet(5.0)
except Exception as e:
    print("Fillet error:", e)

# Cut holes and slots
cut_tool = (
    cq.Workplane("XZ").workplane(offset=20)
    .pushPoints([(-12.5, -23.5), (12.5, -23.5)])
    .circle(15/2)
    .pushPoints([(-12.5, -29.75), (12.5, -29.75)])
    .rect(10, 12.5)
    .extrude(-15)
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
