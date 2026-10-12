import cadquery as cq

def create_test_coupon_base(width=20.0, plate_thickness=6.0, top_y=20.0, bottom_y=-35.4):
    """
    Creates a standardized base plate for test coupons.
    Includes 45-degree chamfers on the sides for diagonal printing.
    Includes grip ears at the top and bottom.
    """
    plate_h = top_y - bottom_y
    plate_center_y = bottom_y + plate_h/2
    base = cq.Workplane("XY").center(0, plate_center_y).box(width, plate_h, plate_thickness, centered=(True, True, False))
    
    # Add ears at top and bottom using the provided grip logic
    # Ear width should be narrower than the plate. Let's make ear_span = 14.0 mm
    ear_span = 14.0
    x_half = ear_span / 2.0
    y_wall = plate_h / 2.0
    ear_overhang = 2.0
    
    # We will attach the ears to the base, which is centered at (0, plate_center_y).
    # To use the exact logic, it's easier to create the ears around (0,0) with plate_h,
    # and then translate them to plate_center_y.
    
    # Top ear (+Y)
    w1_t = (
        cq.Workplane("XY")
        .workplane(offset=0) # Base profile at Z=0 (Front of coupon, facing user)
        .moveTo(-x_half, y_wall - 2.0)
        .lineTo(-x_half, y_wall)
        .threePointArc((0.0, y_wall + ear_overhang), (x_half, y_wall))
        .lineTo(x_half, y_wall - 2.0)
        .close()
    )
    w2_t = (
        w1_t.workplane(offset=plate_thickness) # Top profile at Z=plate_thickness (Back, touching pegboard)
        .moveTo(-x_half + 2.0, y_wall - 2.0)
        .lineTo(-x_half + 2.0, y_wall)
        .lineTo(x_half - 2.0, y_wall)
        .lineTo(x_half - 2.0, y_wall - 2.0)
        .close()
    )
    ear_top = w2_t.loft().translate((0, plate_center_y, 0))
    
    # Bottom ear (-Y)
    w1_b = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .moveTo(-x_half, -(y_wall - 2.0))
        .lineTo(-x_half, -y_wall)
        .threePointArc((0.0, -(y_wall + ear_overhang)), (x_half, -y_wall))
        .lineTo(x_half, -(y_wall - 2.0))
        .close()
    )
    w2_b = (
        w1_b.workplane(offset=plate_thickness)
        .moveTo(-x_half + 2.0, -(y_wall - 2.0))
        .lineTo(-x_half + 2.0, -y_wall)
        .lineTo(x_half - 2.0, -y_wall)
        .lineTo(x_half - 2.0, -(y_wall - 2.0))
        .close()
    )
    ear_bot = w2_b.loft().translate((0, plate_center_y, 0))
    
    base = base.union(ear_top).union(ear_bot)
    
    # 45 degree chamfers for printing (cuts the ears too!)
    right_cut_pts = [(width/2, plate_thickness), (width/2 - 50, plate_thickness - 50), (width/2 + 50, plate_thickness - 50), (width/2 + 50, plate_thickness)]
    right_cutter = cq.Workplane("XZ").polyline(right_cut_pts).close().extrude(1000, both=True)
    
    left_cut_pts = [(-width/2, plate_thickness), (-width/2 + 50, plate_thickness - 50), (-width/2 - 50, plate_thickness - 50), (-width/2 - 50, plate_thickness)]
    left_cutter = cq.Workplane("XZ").polyline(left_cut_pts).close().extrude(1000, both=True)
    
    base = base.cut(right_cutter).cut(left_cutter)
    return base
