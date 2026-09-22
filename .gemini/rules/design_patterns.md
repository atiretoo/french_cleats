# French Cleats Project Rules

## 1. Dynamic Baseplate Sizing vs Fixed Units
*   **Pattern:** Do not force a strict "1U per tool" constraint or make the user guess the required baseplate width for multi-tool holders.
*   **Implementation:** Tool holder scripts should accept --tools (count) and --spacing (center-to-center distance). The script must calculate the total mechanical width required, and dynamically snap the baseplate to the next standard U size using `units = max(1, math.ceil(mech_width / 28.0))`. Center the tool mechanisms on that baseplate.

## 2. Captive Nut Slots & Push Holes
*   **Pattern:** Always use the universal `create_nut_slot()` function from `holder_base.py` rather than manually modeling slots. Use `cq.Location(plane)` to map the slot solid onto complex or tilted angles.
*   **Dimensions:** Push holes used to eject captive nuts must be at least **1.5mm in diameter**. Smaller 1.0mm holes fail to print reliably at 0.28mm layer heights and cause standard paperclips to crumple.

## 3. CadQuery Cyclic Coordinate Systems
*   **Pattern:** Always use positive forward cyclic loops (`"XY"`, `"YZ"`, `"ZX"`) when defining CadQuery workplanes to ensure local extrusions map cleanly to positive global axes. Do NOT use `"XZ"` as it reverses the normal to `-Y`.

## 4. Invariant Object Reference Frame & Terminology
*   **Physical Invariance:** For this project, the English terms **Top**, **Bottom**, **Left**, **Right**, **Front**, and **Back** are **intrinsic physical features of the object itself**, defined by how the tool holder hangs on the wall from the perspective of a user facing the wall:
    *   **Top:** The end of the backplate closest to the ceiling.
    *   **Bottom:** The end of the backplate closest to the floor.
    *   **Left:** The left side/edge of the holder as seen by a user standing in front of the wall looking at it.
    *   **Right:** The right side/edge of the holder as seen by a user standing in front of the wall looking at it.
    *   **Back:** The surface with the cleat grooves that rests flat against the wall.
    *   **Front:** The side facing into the room towards the user, where tool mechanisms, slots, and shelves protrude.
*   **Rotation Invariance:** These feature names **never change**, regardless of how the model is pitched, rolled, or oriented in CAD or on the 3D printer bed. When communicating or implementing transformations:
    *   Always use these terms to identify the physical features (e.g., *"resting on its right edge"*, *"supports under the top of the backplate"*).
    *   Distinguish between the intrinsic feature and its current global coordinates (e.g., *"In construction, Top is at +Y; after the 180° X-rotation, the Top is now oriented towards -Y"*).

## 5. Print Orientation & Export
*   **Pattern:** The `export_model()` function handles exporting STL and STEP files and supports `print_orientation` to position the part for slicing:
    *   `print_orientation="none"` (or `None`): Leaves the model in raw CAD construction coordinates.
    *   `print_orientation="left_down"` or `"right_down"`: Rests the holder on its physical Left or Right side edge (parallel to the Top-Bottom axis).
    *   `print_orientation="back_down"`: Rotates the model so its physical Back rests flat on the print bed.
    *   `print_orientation="top_down"` or `"bottom_down"`: Stands the holder on its physical Top or Bottom edge.
