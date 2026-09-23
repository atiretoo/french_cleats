# Open Source Modular French Cleat System (Parametric, Heavy-Duty, 28mm Grid Compatible)

> **A fully parametric, modular 3D-printed French cleat tool organization system designed for standard 73 mm rails, featuring rigid trapezoidal locking grooves, OpenGrid/Gridfinity compatibility, and M3 hardware mounting.**

---

## Overview

This project provides a robust, standardized, and fully parametric French cleat tool organization ecosystem for workshops, maker spaces, and garages. 

Most French cleat models available online suffer from two key problems:
1. They integrate the cleat directly into the tool holder, forcing awkward print orientations that lead to weak layer lines across the load-bearing cleat bevel.
2. Friction-fit slide connections frequently bind or jam when printed across different machines and tolerances.

This system solves both issues by utilizing a **two-part modular design**:
* **Cleat Bases (Top & Bottom):** Print on their sides with continuous filament strands running along the load-bearing $45^\circ$ bevel, maximizing shear strength.
* **Tool Holders & Adaptors:** Fasten securely to the cleats using standard M3 machine screws into heat-set inserts or standard M3 hex nuts.
* **Trapezoidal Locking Grooves:** Self-aligning $45^\circ$ angled grooves lock the backplate firmly against the cleats, eliminating wobble, rotation, and sagging even under heavy loads.
* **28 mm Grid Standard:** Built upon the 28 mm pitch shared with **OpenGrid** (by David D) and seamlessly compatible with **Gridfinity** (by Zack Freedman).

---

## IMPORTANT: French Cleat Rail Height Requirement

> ### Critical Sizing Note
> The pre-rendered STL and STEP files provided in this release are dimensioned specifically for **French cleat wall strips that are 73 mm (approx. 2-7/8") high**, with a standard $45^\circ$ top bevel and nominal 19 mm (3/4") thickness.
>
> If your workshop French cleat rails are **any height other than 73 mm**:
> 1. **Best & Fastest Option — Custom Generation via GitHub:**  
>    Visit the open-source repository at [https://github.com/atiretoo/french_cleats](https://github.com/atiretoo/french_cleats). The entire ecosystem is generated programmatically using Python and CadQuery. You can simply specify your rail height (e.g. `--rail-height 65.0` or `--rail-height 89.0`) and generate perfectly customized cleats and tool holders for your exact walls in seconds.
> 2. **Alternative — Message Me:**  
>    You can send me a message here on Printables with your cleat dimensions. I will do my best to render and upload models for other common rail sizes when time permits, but please be aware that responses may be slow.

---

## Included Components (Release v1.2.1)

### 1. Modular Cleat Mounts
* **Top Cleats (1U, 2U, 3U, 4U):** Grips the wall rail's $45^\circ$ top bevel. Incorporates the self-aligning trapezoidal ridge and rear slots for standard M3 hex nuts.
* **Bottom Cleats (1U, 2U, 3U, 4U):** Rests against the bottom edge of the rail to keep tools perfectly plumb and eliminate peel-away torque.

### 2. Tool Holders
* **Screwdriver Holders (1x6U):**
  * `D10.0_S25.0`: 10 mm diameter holes at 25 mm spacing (small/precision screwdrivers, punches, hex keys).
  * `D14.0_S30.0`: 14 mm diameter holes at 30 mm spacing (standard medium screwdrivers).
  * `VAR_S26.0`: Stepped set (20, 18, 15.5, 15, 14, 10 mm holes) with 23 mm counterbores for large mechanic handles and insulated drivers.
* **Chisel Holder (4-Tool, 5U, Mid-Shelf):** Holds four bench chisels (up to 26 mm blade width) with central tool holes, blade retention slots, and reinforced side gussets.
* **Slot Holder (1x2U):** 6.25 mm slot width with 10 mm backplate clearance. Perfect for Japanese pull saws (Dozuki, Ryoba), steel rules, scrapers, squares, and calipers.
* **Heavy-Duty Power Tool Holder (2U, 140 mm Depth):** Dual angled prongs with radius cradles to securely hang cordless drills, impact drivers, nailers, and angle grinders.
* **Thin Tool / Magnetic Saw Holder (1U):** Flush-mount tool plate with embedded magnet pockets for quick-draw magnetic tool retention:
  * 2x 10.2 mm dia x 2.0 mm depth
  * 3x 10.2 mm dia x 2.0 mm depth
  * 2x 19.2 mm dia x 2.0 mm depth
* **Hook Holder (1x4U, 10 mm Dia, 5° Slope):** 112 mm cylindrical hook with a $5^\circ$ upward retention angle and filleted tip for extension cords, tape rolls, air hoses, and hanging tools.
* **V-Holder (2x4U):** Dual angled V-jaws for pliers, wire strippers, aviation snips, hand clamps, and irregularly shaped tools.

### 3. Gridfinity & System Adapters
* **Gridfinity Shelves (3x3U, 6x3U, 6x6U):** Mounts Zack Freedman's Gridfinity storage bins directly to your French cleat walls.
* **OpenGrid Adapters (1U, 2U, 3U, 4U):** Converts any standard OpenGrid or Multiconnect accessory for use on your French cleats.

### 4. Auxiliary Assembly Tools
* **Nut Pushers (M3 & M4):** Ergonomic 3D-printed hex driver handles designed to seat M3 and M4 hex nuts into deep cleat retention slots effortlessly without scratching the parts.

---

## Recommended Print Settings

All exported STL models have been audited and pre-oriented for optimal slicing:

* **Print Orientations:**
  * **Braced Holders (Slot, Screwdriver, Chisel, V-Holder):** Pre-rotated to print flat on their side with the support gusset resting on the build plate. This ensures continuous, uninterrupted extrusion across the shelf cantilever with **zero supports required**.
  * **Hook Holder & Gridfinity Shelves:** Pre-rotated to print flat on their backplates.
  * **Cleats:** Pre-rotated to print on their side faces, providing maximum layer strength across the $45^\circ$ cleat bevel.
* **Material:** **PETG**, **ABS**, or **ASA** is strongly recommended for workshop longevity, creep resistance under load, and impact toughness. **PLA** is suitable for lighter hand tool organizers.
* **Perimeters / Walls:** 4–5 walls (approx. 1.6–2.0 mm wall thickness).
* **Top & Bottom Layers:** 4–5 layers.
* **Infill:** 25%–40% (Gyroid, Grid, or Honeycomb).
* **Supports:** None needed when using the default exported orientations.

---

## Hardware Required

* **Screws:** M3 button head or socket head cap screws (M3 x 12 mm to M3 x 16 mm recommended).
* **Nuts:** Standard M3 hex nuts (DIN 934 / ISO 4032, 5.5 mm across flats, 2.4 mm thick) or standard M3 threaded heat-set inserts.

---

## Source Code & CAD Files

* **GitHub Repository:** [https://github.com/atiretoo/french_cleats](https://github.com/atiretoo/french_cleats)
* **STEP Files:** Full STEP assemblies and individual component models are included in `step_files.zip` under the Other Files section for seamless remixing and CAD customization.

---

## Development & AI Disclosure: The "Centaur" Approach

This project is developed using a collaborative human-AI workflow. The CadQuery Python code, geometric algorithms, refactoring, and documentation were written and refined with the assistance of advanced AI models.

I approach AI not as a tool for blind self-automation, but as a collaborative interaction. I aspire to be a [centaur](https://mitsloan.mit.edu/ideas-made-to-matter/3-ways-to-use-ai-are-you-a-cyborg-a-centaur-or-a-self-automator), maintaining structured and controlled interactions with AI, harnessing it as a tool for targeted efficiency. In this model, the AI acts as a high-powered pair-programming partner, helping me rapidly explore geometry, write parametric test suites, and audit dimensional consistency. Meanwhile, I hold the strategic architectural vision, conduct the physical slicing, 3D printing, and workshop validation, and apply and build domain knowledge throughout the process.
