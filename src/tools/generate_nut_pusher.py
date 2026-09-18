import cadquery as cq
import argparse
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from holder_base import export_stl

def create_nut_pusher(screw_m="M3", handle_length=11.0):
    """
    Creates a small tool to push captive nuts into tight slots.
    The handle provides grip, and the head is sized perfectly for the slot.
    """
    if screw_m == "M3":
        head_w, head_t = 5.2, 2.1  # slightly undersized from slot (5.6x2.5)
        head_l = 8.0               # depth of push
    elif screw_m == "M4":
        head_w, head_t = 6.7, 2.9
        head_l = 10.0
    elif screw_m == "M5":
        head_w, head_t = 7.7, 3.7
        head_l = 12.0
    else:
        raise ValueError(f"Unsupported screw size: {screw_m}")
        
    handle_dia = max(10.0, head_w + 4.0)
    
    # Handle (Extrudes into +Z)
    handle = (
        cq.Workplane("XY")
        .circle(handle_dia / 2.0)
        .extrude(handle_length)
        .edges(">Z").fillet(1.0)
    )
    
    # Head (Extrudes into -Z)
    head = (
        cq.Workplane("XY")
        .rect(head_w, head_t)
        .extrude(-head_l)
        .edges("<Z").chamfer(0.5) # Chamfer to easily slide into slot
    )
    
    return handle.union(head)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a captive nut pusher.")
    parser.add_argument("--screw", default="M3", choices=["M3", "M4", "M5"], help="Screw size")
    parser.add_argument("--handle-length", type=float, default=11.0, help="Length of the thumb handle")
    args = parser.parse_args()
    
    pusher = create_nut_pusher(args.screw, args.handle_length)
    filename = f"nut_pusher_{args.screw}_L{args.handle_length}.stl"
    
    # back_down rotates +Z (the handle) to touch the print bed, so it stands tall.
    export_stl(pusher, filename, print_orientation="back_down", category="tools")
