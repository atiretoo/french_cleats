# French Cleat Tool System: Design Rationale & History

This document outlines the evolutionary design choices, dimensional assumptions, and geometric rationale that shaped the V1.x generation of the parametric tool holder project.

## 1. The Core "U" System & Grid
All components in this system are built upon a universal grid where **1U = 28.0 mm**.
- **Width:** Holder widths perfectly span intervals of 28mm to match rail slots.
- **Depth:** Shelves extend outward along the Z-axis in increments of 28mm (e.g., a 6U screwdriver rack projects 168mm from the wall).
- **Modularity:** Adhering strictly to the 1U grid ensures holders can be tessellated perfectly on the wall without awkward gaps.

## 2. Structural Thicknesses & FEA (Finite Element Analysis)
Early iterations of the project used conservatively thick walls (10mm shelves, 5mm side braces). 
Following FEA simulations in the `strength_tester.py` pipeline, the models were proven to be drastically over-engineered. We instituted global thickness reductions:
- **Shelf Thickness:** Reduced to **5.0 mm**.
- **Brace Thickness:** Reduced to **2.5 mm**.
- **Truss Cutouts:** For deep, highly-leveraged shelves (depth > 2U, or > 56mm), the side braces automatically receive a triangular truss cutout. The cutout offsets exactly 15mm from the structural edges and utilizes 8.0mm inner corner fillets. This minimizes filament use without sacrificing the structurally validated rigidity.

## 3. Clearances & The 5mm Fillet Rule
To ensure plastic components fuse strongly and do not snap under shear loads, a standard **5.0mm fillet** is applied wherever a projecting shelf meets the flat backplate. 
This structural requirement drove several mathematical spacing rules:
- **Tool Handle Clearance:** To prevent tool handles (like screwdrivers) from resting against or catching on the 5mm fillet, the center of the first hole on any projecting shelf is mathematically driven by `fillet_size + (tool_radius)`. This ensures a perfectly vertical hang.
- **Slot Clearances:** Continuous slots (like the 1x2U saw/file holder) stop precisely 10mm from the backplate to completely clear the fillet radius.

## 4. Printability & Asymmetric Bracing
A major design goal was to avoid generating G-Code supports. This led to specific choices regarding side braces:
- **Asymmetric Side Braces:** On a 1U-wide projecting holder (like the screwdrivers), a brace is only generated on the left side. This provides the structural load path needed while freeing up the right side so wide tool handles do not rub against the plastic truss.
- **Print-On-Side Mechanics:** Removing the right brace entirely (or removing braces altogether, as seen on the Tape Measure V-Holder) means the right edge of the shelf is perfectly co-planar with the right edge of the backplate. The user can orient the model perfectly flat on its side on the print bed.
- **I-Beam Rigidity:** The Tape Measure holder features a 5.0mm thick, 90-degree V-trough. Because an angled V-profile intrinsically acts as a deep I-beam flange, it resists vertical deflection independently. We removed its side braces entirely for a cleaner print and sleeker aesthetic.

## 5. Captive Nut Cleat Assembly (V1.1.0)
The mounting cleats were completely overhauled in V1.1.0 to eliminate the annoyance of hex nuts falling out during inverted rail assembly.
- **Slide-in Pockets:** Hex nuts are inserted from the flat horizontal faces (top face for top cleats, bottom face for bottom cleats) perpendicular to the screw axis.
- **Friction Fit:** The pocket width uses the exact distance across the flats of standard metric nuts (e.g., 5.5mm for M3, 7.0mm for M4) while the thickness is `nut_thickness + 0.1mm`. This 0.1mm clearance generates a firm friction fit in FDM prints.
- **Bite Depth:** The front edge of the captive slot sits exactly 4.0mm deep from the ridge face, leaving a sturdy 4mm wall of plastic for the screw to clamp against.

## 6. OpenCASCADE Boolean Quirks
During the generation of complex tool sockets (like the chisel holder which marries a 15mm round ferrule hole to a 26x4mm rectangular blade slot), we avoided drawing overlapping 2D wires in CadQuery. 
- **Rationale:** OpenCASCADE often fails to resolve 2D intersecting boundary wires, silently dropping one of the profiles in an XOR fashion. 
- **Solution:** Complex composite cuts are executed as sequential, independent 3D boolean subtractions (e.g. `holder.cut(cylinder).cut(box)`).

## 7. Customization Mechanics (Recesses and Offsets)
- **Variable Hole Scaling:** For tailored fits (like the nut driver rack), the hole generation logic utilizes a 1mm radius (2mm diameter) shaft clearance.
- **Nesting Recesses:** To prevent top-heavy tools from tipping, the system supports independent recess generation. For example, a 22.3mm nut driver handle utilizes a 23.0mm diameter pocket, precisely cut 1.0mm deep into the top surface of the 5.0mm shelf.
