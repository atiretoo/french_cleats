# Universal Cleats (V1.1.0)

All cleats (top and bottom) have been redesigned to use **slide-in captive nut slots**. 

## Features
- **Friction Fit:** Instead of a hexagonal pocket that the nut just sits in, there is now a rectangular slot driving in from the flat side of the cleat (the top side for top cleats, the bottom side for bottom cleats). 
- **Auto-Alignment:** The slot's width exactly matches the distance across the flats of an M3/M4/M5 nut, and its thickness gives exactly 0.1mm clearance to the nut. This ensures you can push the nut into the slot and it stays securely friction-fit in place when inverted, remaining perfectly aligned along the screw axis!
- **Positioning:** The slot is precisely 4.0mm deep from the ridge face, leaving plenty of plastic for a strong clamp.

![Top Cleat with Slide-In Slot (2U)](file:///C:/Users/atyre/.gemini/antigravity/brain/6f123139-a880-4905-af43-bcb69787dd1f/top_cleat_render.png)

---

# V-Holder (Tape Measures)

A new module `generate_v_holder.py` creates an open-faced 90-degree V-shaped trough perfect for storing bulky items like tape measures!

## Features
- **V-Profile:** The trough angles upwards at a perfect 90 degrees (45 degrees off horizontal on each side) spanning the full width of the unit.
- **Completely Braceless:** The angled geometry acts like an I-beam, giving the shelf incredible rigidity on its own. By removing the braces entirely, it saves filament and means you can print it perfectly flat on *either* of the V's vertical side edges without any supports!

![V-Holder (2x4U)](file:///C:/Users/atyre/.gemini/antigravity/brain/6f123139-a880-4905-af43-bcb69787dd1f/v_holder_render.png)

---

# Z-Axis Screwdriver Holder

I have completely refactored the screwdriver holder! It now acts exclusively as a projecting shelf (normal to the wall) as requested.

## Features
- **Projecting Shelf:** The holder is defined by `--width-units` (usually 1U to fit on a single track) and `--depth-units` (how far it extends away from the wall).
- **Asymmetric Bracing:** If the holder is 1U wide, it automatically only places a structural brace on the **left side**. This frees up crucial millimeters on the right side, ensuring that thick screwdriver handles won't rub against the braces.
- **Variable Hole Sizes:** You can now pass exactly what diameter you want for each slot using a comma separated list via `--hole-sizes`.
- **Handle Recesses:** Recesses can be carved into the top of each hole using `--recess-size` and `--recess-depth`.

## Example: Custom Nut Driver Rack
Using `--hole-sizes 20,18,15.5,15,14,10 --recess-size 23 --recess-depth 1`, the script creates perfectly tailored holes that accommodate the 1mm clearance around each shaft, while nesting the 22.3mm handles beautifully into their own individual seats:

![Screwdriver Rack (Variable Holes & Recesses)](file:///C:/Users/atyre/.gemini/antigravity/brain/6f123139-a880-4905-af43-bcb69787dd1f/screwdriver_var_render.png)

---

# Chisel Holder

A new module `generate_chisel_holder.py` creates a 1U-deep, braceless shelf along the width of the wall for chisels. 

## Features
- **Composite Cutouts:** perfectly matches your sketch! Each cutout combines a 15mm circular drop-in for the handle ferrule with a 26mm x 4mm rectangular slot to fit the wide chisel blade.
- **Braceless:** The shelf projects out by just 28mm (1U), so it is completely self-supporting. A 5mm fillet merges it securely into the backplate.
- **Spacing:** The default `4U` (112mm) variant spaces 4 slots perfectly with exactly 2mm of plastic web between the 26mm slots!

![Chisel Holder (4U)](file:///C:/Users/atyre/.gemini/antigravity/brain/6f123139-a880-4905-af43-bcb69787dd1f/chisel_render.png)

---

# Slot Holder

A new module `generate_slot_holder.py` creates a 1x2U shelf with a single continuous front-facing slot for holding files, squares, saws, or anything else flat.

## Features
- **Dynamic Array:** Easily create wide multi-slot shelves by changing the width units. A 4U wide holder perfectly spaces 4 parallel slots across its width.
- **Fillet Clearance:** The slot perfectly stops 10mm away from the backplate to ensure inserted tools never catch on the 5mm strengthening fillet.

![Slot Holder (1x2U)](file:///C:/Users/atyre/.gemini/antigravity/brain/6f123139-a880-4905-af43-bcb69787dd1f/slot_render.png)
