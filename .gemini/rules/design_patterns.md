# French Cleats Project Rules

## 1. Dynamic Baseplate Sizing vs Fixed Units
*   **Pattern:** Do not force a strict "1U per tool" constraint or make the user guess the required baseplate width for multi-tool holders.
*   **Implementation:** Tool holder scripts should accept --tools (count) and --spacing (center-to-center distance). The script must calculate the total mechanical width required, and dynamically snap the baseplate to the next standard U size using `units = max(1, math.ceil(mech_width / 28.0))`. Center the tool mechanisms on that baseplate.

## 2. Captive Nut Slots & Push Holes
*   **Pattern:** Always use the universal `create_nut_slot()` function from `holder_base.py` rather than manually modeling slots. Use `cq.Location(plane)` to map the slot solid onto complex or tilted angles.
*   **Dimensions:** Push holes used to eject captive nuts must be at least **1.5mm in diameter**. Smaller 1.0mm holes fail to print reliably at 0.28mm layer heights and cause standard paperclips to crumple.

## 3. CadQuery Cyclic Coordinate Systems
*   **Pattern:** Always use positive forward cyclic loops (`"XY"`, `"YZ"`, `"ZX"`) when defining CadQuery workplanes to ensure local extrusions map cleanly to positive global axes. Do NOT use `"XZ"` as it reverses the normal to `-Y`.

## 4. Coordinate System & Terminology
*   **Pattern:** Always use consistent terminology and CAD axes to avoid orientation bugs:
    *   **Y-Axis (Vertical):** `+Y` is **TOP** (towards the ceiling, the cleat overhang). `-Y` is **BOTTOM** (towards the floor, the cleat groove).
    *   **X-Axis (Horizontal):** `+X` is **RIGHT**. `-X` is **LEFT** (when facing the wall).
    *   **Z-Axis (Depth):** `Z=0` is the **BACK** (the face touching the wall). **`-Z` is the FRONT** (the direction coming out of the wall towards the user). All mechanisms build into negative Z space.

## 5. Print Orientation Overrides
*   **Pattern:** By default, tool holders exported to STL will lay flat on their backs (Z-axis becomes bed height). The `export_stl()` function supports a `print_orientation` argument to explicitly position the part for optimal slicing.
*   **Implementation:** 
    *   Use `print_orientation="left_down"` or `"right_down"` to stand the holder on its side edge. (Default behavior). This is ideal for empty baseplates or simple holders to maximize French cleat overhang strength.
    *   Use `print_orientation="back_down"` to lay the holder flat on its backplate. Ideal for complex mechanisms (Shooo Cam Holder) to avoid massive supports and strengthen Z-axis pins.
    *   Use `print_orientation="top_down"` or `"bottom_down"` to stand the holder on its cleat or groove edge. (Used for the Power Tool Holder to print the hook without supports).
