# French Cleats Project Rules

## 1. Dynamic Baseplate Sizing vs Fixed Units
*   **Pattern:** Do not force a strict "1U per tool" constraint or make the user guess the required baseplate width for multi-tool holders.
*   **Implementation:** Tool holder scripts should accept --tools (count) and --spacing (center-to-center distance). The script must calculate the total mechanical width required, and dynamically snap the baseplate to the next standard U size using `units = max(1, math.ceil(mech_width / 28.0))`. Center the tool mechanisms on that baseplate.

## 2. Captive Nut Slots & Push Holes
*   **Pattern:** Always use the universal `create_nut_slot()` function from `holder_base.py` rather than manually modeling slots. Use `cq.Location(plane)` to map the slot solid onto complex or tilted angles.
*   **Dimensions:** Push holes used to eject captive nuts must be at least **1.5mm in diameter**. Smaller 1.0mm holes fail to print reliably at 0.28mm layer heights and cause standard paperclips to crumple.

## 3. CadQuery Cyclic Coordinate Systems
*   **Pattern:** Always use positive forward cyclic loops (`"XY"`, `"YZ"`, `"ZX"`) when defining CadQuery workplanes to ensure local extrusions map cleanly to positive global axes. Do NOT use `"XZ"` as it reverses the normal to `-Y`.

## 4. Baseplate Orientation & Terminology
*   **Pattern:** `+Y` is the "Top" of the wall (featuring the 45-degree French cleat overhang). `-Y` is the "Bottom" of the wall (featuring the interlocking groove). Always explicitly anchor geometry to `block_y_bot` or `block_y_top`.
