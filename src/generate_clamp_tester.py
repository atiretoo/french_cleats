import cadquery as cq

def create_tester():
    # A simple flat slab to test slot depths and spacings
    # X is width (depth of slot), Y is thickness, Z is length
    
    slab_width = 70.0 # Enough to accommodate a 50mm deep slot and leave 20mm spine
    slab_length = 150.0
    slab_thickness = 10.0
    slot_width = 10.0
    
    # Create the main slab
    # X from 0 to 70, Y from 0 to 10, Z from 0 to 150
    tester = cq.Workplane("XY").box(slab_width, slab_length, slab_thickness, centered=False)
    
    # We will cut slots into the X=70 edge (so slots go from 70 inwards)
    # The slots have depths 30, 40, 50.
    # The spacings (center to center) are 30, 40, 50.
    
    # Slot 1
    depth1 = 30.0
    z1 = 20.0 # Center of first slot
    
    # Slot 2 (spacing 30 from slot 1)
    spacing1 = 30.0
    depth2 = 40.0
    z2 = z1 + spacing1
    
    # Slot 3 (spacing 40 from slot 2)
    spacing2 = 40.0
    depth3 = 50.0
    z3 = z2 + spacing2
    
    # Cut Slot 1
    tester = cq.Workplane("XY").workplane(offset=10).center(70 - depth1/2, z1).rect(depth1, slot_width).extrude(-15)
    tester_body = cq.Workplane("XY").box(slab_width, slab_length, slab_thickness, centered=(False, False, False))
    tester_body = tester_body.cut(tester)
    
    # Let's do it much simpler: create the slab, then cut using absolute XY workplane
    tester = cq.Workplane("XY").box(slab_width, slab_length, slab_thickness, centered=(False, False, False))
    
    slots = (
        cq.Workplane("XY").workplane(offset=15)
        .center(70 - depth1/2, z1).rect(depth1, slot_width)
        .center(-(70 - depth1/2), -z1) # reset
        .center(70 - depth2/2, z2).rect(depth2, slot_width)
        .center(-(70 - depth2/2), -z2) # reset
        .center(70 - depth3/2, z3).rect(depth3, slot_width)
        .extrude(-20)
    )
    tester = tester.cut(slots)
    
    return tester

def main():
    tester = create_tester()
    cq.exporters.export(tester, "clamp_tester.stl")
    print("Exported clamp_tester.stl")

if __name__ == "__main__":
    main()
