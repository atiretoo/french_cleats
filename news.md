# NEWS

A chronological record of changes, fixes, and improvements to the Modular French Cleat (MFC) System, listed from newest to oldest.

---

## [1.2.2] - 2026-10-17

### Changed
* **Nut Slot & Screw Hole Tolerances:** Increased captive nut slot tolerances from +0.1 mm to +0.3 mm on both axes (**5.80 mm × 2.70 mm** for standard DIN 934 M3 hex nuts) and increased screw clearance hole diameters to **∅3.4 mm**. Physical workshop testing confirmed this completely eliminates tight binding and layer splitting during nut installation while retaining reliable friction fit so nuts do not fall out during mounting.
* **Slicer & Print Orientation Audits:** Standardized default export orientations across the ecosystem to ensure clean, support-free printing:
  * `screwdriver_holder`, `slot_holder`, and `hook` now default to lying flat on their side (`right_down`), ensuring continuous filament extrusion along the shelf gusset for maximum shear strength without slicer supports.
  * `opengrid_adapter` now defaults to `top_down` for optimal bed contact and adhesion.
* **Naming Conventions:** Renamed magnetic holder export files from `_M` to `_Mags` (e.g., `2Mags`, `3Mags`) to prevent confusion with metric screw dimensions (M3/M4).

### Fixed
* **Power Tool Holder Geometry:** Corrected an inverted coordinate bug on the `ZX` workplane slot cutter that previously caused the U-shaped tool cradle cutout to cut backwards into the shelf body.

### Removed
* **Fragile Prototypes:** Removed the 2.5 mm thin spine clamp holders and experimental cam clamp from batch export pending the heavy-duty v2.0 reinforced redesign.

---

## [1.2.1] - 2026-09-24

### Added
* **Printables Release Documentation:** Created comprehensive Printables model description documentation (`docs/printables_desc.md`) with sizing guides, printing guidelines, and hardware requirements.
* **Formal Attributions:** Explicitly documented inspirations and design lineage:
  * **Frenchfinity** (Bastelsaal) for the two-part cleat separation concept.
  * **shoooo** (@shoooo_1013338) for screw-and-ridge locking inspiration.
  * **OpenGrid** (David D) for the 28 mm pitch standard.
  * **Gridfinity** (Zack Freedman) for bin storage interoperability.

### Changed
* **Licensing Structure:** Re-established full GNU GPLv3 in `COPYING` for source code and parametric scripts alongside Creative Commons Attribution-ShareAlike 4.0 (`LICENSE`) for 3D model designs, adding boilerplate headers to all source files.
* **Gridfinity Shelf Print Orientation:** Updated default orientation to `back_down` for clean bed adhesion without requiring supports.
* **Batch Build Cleanup:** Cleaned up obsolete fin test references from batch generation scripts.

---

## [1.2.0] - 2026-09-20

### Added
* **Automated STEP Export:** Added automated STEP CAD file (`.step`) generation alongside all `.stl` exports across all scripts, bundled into `exports/step_files.zip` for easier CAD remixing.
* **Nut Pusher Auxiliary Tools:** Added 3D-printable ergonomic M3 and M4 hex nut pusher handles featuring a 120° V-notch tip to safely seat captive hex nuts into deep cleat channels without slipping or scratching.
* **Heavy-Duty Power Tool Holder:** Added dual-prong power tool holder (2U, 140 mm depth) with radius cradles designed for cordless drills, impact drivers, and angle grinders.
* **Magnetic Tool Holders:** Added flush-mount tool holders with parameterized magnet pocket diameters (10.2 mm and 19.2 mm) and counts (2x, 3x) for quick-draw retention of saws, rules, and blades.
* **Nut Slot Push-Through Holes:** Added 1.0–1.5 mm push-through holes behind all captive nut slots to allow easy removal of hex nuts using a paperclip or hex key.
* **Support Fin Breakaway Research:** Researched, designed, and tested sacrificial breakaway 45° support fins with micro-gap bridges (0.05–0.10 mm) for printing tall overhangs without traditional slicer supports (advanced fin features moved to v2-dev).

### Changed
* **Workplane Coordinate Refactor (ZX Standard):** Refactored all CadQuery workplanes across the entire codebase from `XZ` to cyclically-positive `ZX` to eliminate inverted normal vectors and ensure predictable extrusion directions.
* **Stress Relieving & Hardware Clearance:** Reduced tool holder shelf thicknesses to 5 mm to maximize screw clearance and added 4 mm inner fillet transitions at brace-to-backplate junctions for stress distribution.
* **Chisel Holder Parametrization:** Parameterized chisel holder to support arbitrary tool counts, custom tool spacing, and variable slot depths/widths.
* **Directory Structure Reorganization:** Reorganized `src/` directory into modular domain packages (`cleats/`, `tool_holders/`, `gridfinity/`, `multiconnect/`, `strength_testing/`, `utilities/`).

---

## [1.1.0] - 2026-09-15

### Added
* **Modular Two-Part French Cleat Standard:** Established the core modular French cleat system separating cleat mounts (top and bottom) from tool holders.
* **Trapezoidal Locking Grooves:** Standardized 45° self-aligning trapezoidal registration ridges and grooves to eliminate holder sag, rotation, and peel-away torque under load.
* **OpenGrid Compatibility:** Standardized backplate dimensions and hole spacing on the 28 mm OpenGrid pitch with 1U, 2U, 3U, and 4U top and bottom cleat mounts.
* **Gridfinity Shelves:** Parametric shelf generators with negative Gridfinity baseplate pockets (3x3U, 6x3U, 6x6U) to mount Gridfinity bins on French cleat walls.
* **Core Tool Holders:**
  * Screwdriver Holders (uniform hole sets: 10 mm dia at 25 mm spacing, 14 mm dia at 30 mm spacing; stepped/variable hole set for mechanic drivers).
  * Slot Holders (6.25 mm slot with 10 mm clearance for Japanese pull saws, steel rules, and squares).
  * V-Holders (angled V-jaws for pliers, wire strippers, and snips).
  * Cylindrical Hooks (10 mm dia, 5° upward slope for cords and hanging tools).
* **Automated Print Orientations:** Automated edge-oriented export for top and bottom cleats to ensure continuous filament strands along the 45° bevel for maximum shear strength.
* **Documentation & Governance:** Created project README with design rationale, installation guides using `uv`, AI collaboration disclosure ("Centaur" approach), and Code of Conduct.
