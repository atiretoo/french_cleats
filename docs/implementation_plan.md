# v2.0-dev: Active Initiatives & Physical Test Print Plan

## Executive Summary & Recent Commit Review

Reviewing recent progress on `v2.0-dev` (`cfdf40c` through `dc0ee26`), the v2.0 cycle centers on structural refactoring, interface standardization, robust printability, and redesigned tool holders:

1. **Digital Assets Architecture (`dc0ee26`)**:
   - Centralized vendor-neutral interface files under `assets/hsw/` and `assets/multiconnect/` with upstream attributions.
   - Removed local host path dependencies (`OneDrive`, `Desktop`) in favor of relative paths.
2. **Shallow Groove & Ridge Standard (`dc0ee26`, `core_library.py`)**:
   - Standardized the shallow trapezoidal profile (3.0 mm depth, 1.0 mm flat bottom, 7.0 mm surface opening at $45^\circ$, 0.5 mm bottom clearance).
   - Applied across cleats, backplates, and OpenGrid adapters.
3. **Perpendicular Magnetic Tool Holder (`12ab8cb`, `d6f345c`, `dc0ee26`)**:
   - Added perpendicular projection style (`--style perpendicular`) in `generate_magnetic_holder.py`.
   - Right-side shelf with full-height triangular brace, 2x magnet thickness wall, and centered vertical magnet column.
4. **Deep Shelf & Chamfered Chisel Holder (`16f139f`)**:
   - Increased shelf depth to 38 mm (+10 mm over v1.2.1 28 mm default) to accommodate larger handles.
   - Added $60^\circ$ (2 mm) chamfers on the top rim of tool holes for tool retention.
5. **[COMPLETED] 45-Degree Gridfinity Support Fins (`f8db89c`, `5b6f42f`, `6ced7d0`)**:
   - Implemented 45-degree build-plate printing for Gridfinity shelves with disposable support fins and micro-gap bridges.
   - **Status**: Physically printed and verified by user—works great!
6. **Honeycomb Storage Wall (HSW) Cleat Adapter (`79a9ec2`, `a40036a`, `dc0ee26`)**:
   - Added `src/hsw/generate_hsw_cleat_adapter.py` supporting both standard (40.88 mm vertical pitch) and rotated (23.6 mm pitch) HSW snap-fit plugs.
   - Implemented shortest-path side-entry M3 nut slots. (Moved to lower priority per user direction).
7. **Redesign Backlog (Carried over from v1.2.1 feedback)**:
   - **Corner Clamp Holder**: Needs thickened spine/gussets (original cracked under load).
   - **Bar / F-Clamp Holder**: Needs wider saddle or anti-rotation wings (clamps currently rotate).
   - **Saw / Thin Tool Cam Holder**: Cam-locking mechanism for thin blades and Japanese saws.

---

## Revised & Prioritized Physical Test Plan

```
┌─────────────────────────────────────────────────────────────────┐
│ Priority 1: Core Mechanical Standards & Validation             │
│ 1.1 [DONE] Shallow Groove & Ridge Fit Standard (0.20mm locked)  │
│ 1.2 [ON HOLD] Slant3D Edge Standards (Chamfers & Fillets)       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Informs edge detailing & fit
┌────────────────────────────────▼────────────────────────────────┐
│ Priority 2: Ergonomic & Functional Upgrades                     │
│ 2.1 Deep Shelf (38mm) & Chamfered Chisel Holder                 │
│ 2.2 [DONE] 45° Gridfinity Support Fin & Pocket Test             │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Informs structural sizing
┌────────────────────────────────▼────────────────────────────────┐
│ Priority 3: Structural Redesigns                                │
│ 3.1 Corner Clamp Holder (Reinforced 5mm+ Spine)                 │
│ 3.2 F-Clamp Holder (Anti-Rotation Saddle)                       │
│ 3.3 Eccentric Cam Locking Saw Holder                            │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Secondary ecosystem
┌────────────────────────────────▼────────────────────────────────┐
│ Priority 4: Ecosystem & Secondary Adaptors                      │
│ 4.1 Honeycomb Storage Wall (HSW) Cleat Adapter (Low Urgency)    │
└─────────────────────────────────────────────────────────────────┘
```

---

### Priority 1: Core Mechanical Standards & Validation

#### 1.1 [COMPLETED & VALIDATED] Self-Centering Ridge & Groove Tolerance Standards
* **Status**: **PASSED & VALIDATED**. Physical test prints confirmed that `C0.20_45` ($0.20\text{ mm}$ side clearance, $45.0^\circ$ parallel walls, $0.80\text{ mm}$ crest clearance) provides the best fit with minimal play and smooth seating in both orientations.
* **Locked-in Parameters for v2.0**:
  - `GROOVE_DEPTH = 3.0 mm`
  - `GROOVE_SURFACE_HALF_WIDTH = 3.5 mm` ($7.0\text{ mm}$ opening)
  - `GROOVE_BOTTOM_HALF_WIDTH = 0.5 mm` ($1.0\text{ mm}$ flat bottom at $45^\circ$)
  - `RIDGE_SIDE_CLEARANCE = 0.20 mm`
  - `RIDGE_DEPTH_CLEARANCE = 0.80 mm`
  - `RIDGE_HEIGHT = 2.20 mm`
  - `RIDGE_SURFACE_HALF_WIDTH = 3.30 mm` ($6.60\text{ mm}$ base width)
  - `RIDGE_PEAK_HALF_WIDTH = 1.10 mm` ($2.20\text{ mm}$ crest width at $45^\circ$)
* **Objects Validated**:
  1. `backplate_coupon_1u_REF_45.stl` (Universal reference gauge).
  2. `cleat_coupon_C0.20_45.stl` (Snug self-centering fit without binding).

#### 1.2 [ON HOLD / UNCHECKED] Slant3D-Inspired Edge Geometry Standard: Chamfers & Fillets
* **Status**: **UNCHECKED / ON HOLD**. Comprehensive edge finishing (chamfering all build-plate contact edges and filleting all Z/shelf edges) could not be made to work consistently across tool holders due to OpenCASCADE CAD kernel limitations (`BRep_API: command not done`).
* **What Works & Is Retained**:
  1. **Backplate Back Chamfers**: 2.0 mm $45^\circ$ chamfers across ALL 4 back perimeter edges at the wall interface ($Z = 0$), eliminating elephant's foot and ensuring flush seating on imperfect walls.
  2. **Backplate Front Edges**: The 4 front edges of the backplate ($Z = -11$) remain strictly sharp to prevent grooved weak points where shelves join.
  3. **Backplate Corner Fillets**: Large 2.5 mm radius fillets along the 4 Z-axis edges (the outer vertical corners).
  4. **Structural Shelf Junction Fillets**: 5.0 mm load-bearing fillets applied to horizontal shelf-backplate junctions (`ShelfJuncSel`) on flush holders for cantilever strength.
  5. **Brace Corner Alignment**: Flush side-braces stopped 2.5 mm short (`bottom_y + 2.5`) to eliminate overhanging corners past the backplate's 2.5 mm rounded corners.
* **Why Unchecked / Deferred**:
  - Global `apply_bed_chamfer` is disabled because automatic orientation-based bed chamfers caused slicing artifacts and geometric conflicts.
  - Adding outer edge fillets to flush shelves/projections breaks the junction fillet topology in OpenCASCADE. Outer edges on flush holders are kept sharp to ensure clean side printing (`left_down`/`right_down`).
  - Complex filleting can be revisited in external CAD (e.g., Onshape/SolidWorks using Parasolid) if desired.
* **Retired**:
  - Deleted `src/tool_holders/generate_cam_holder.py` as it was a failed experiment (keeping `generate_shooo_cam_holder.py` for ongoing multi-tool cam development).

---

### Priority 2: Ergonomic & Functional Upgrades

#### 2.1 Deep Shelf & Chamfered Chisel Holder
* **Goal**: Validate that the 38 mm shelf depth (+10 mm) provides sufficient clearance for heavy wooden handles, and evaluate the $60^\circ$ (2 mm) chamfer for centering brass ferrules.
* **Objects to Print**:
  - `chisel_holder_4tools_5u_mid_groove_H73.0.stl` (or a 2-tool test slice).
* **Evaluation Criteria**:
  - [ ] Chisel handles seat securely into the $60^\circ$ chamfered hole rim without wobble.
  - [ ] Chisel blades hang clear of the backplate and wall.
  - [ ] 38 mm shelf depth balances tool center of gravity cleanly.

#### 2.2 [COMPLETED] 45° Gridfinity Shelf Support Fin & Pocket Test
* **Status**: **PASSED & VALIDATED**. User confirmed the 45-degree build-plate orientation with micro-gap support fin printed past the fins, broke away cleanly, and functions great.

---

### Priority 3: Structural Redesigns

#### 3.1 Corner Clamp Holder Redesign (Spine Reinforcement)
* **Goal**: Thicken the clamp spine from 2.5 mm to 5.0+ mm with filleted structural ribs to resolve the breakage seen in earlier testing.
* **Objects to Print**:
  - Corner clamp holder prototype with reinforced spine.
* **Evaluation Criteria**:
  - [ ] Clamp weight and clamping pressure do not cause delamination or bending along the spine.

#### 3.2 F-Clamp / Bar Clamp Holder Redesign (Anti-Rotation Saddle)
* **Goal**: Widen the saddle or add anti-rotation flanges so long bar clamps cannot pivot or twist out of alignment.
* **Objects to Print**:
  - Widened clamp holder prototype.
* **Evaluation Criteria**:
  - [ ] Bar clamp rests straight without twisting when adjacent tools are bumped.

#### 3.3 Saw / Thin Tool Eccentric Cam Holder
* **Goal**: Validate cam lobe geometry, pivot pin strength, and friction grip against smooth steel blades.
* **Objects to Print**:
  - Cam holder body and cam lever prototype.
* **Evaluation Criteria**:
  - [ ] Cam swings freely and grips blade under gravity/wedge action.
  - [ ] One-handed insertion and lifting release works smoothly.

---

### Priority 4: Ecosystem & Secondary Adaptors

#### 4.1 Honeycomb Storage Wall (HSW) Cleat Adapter Test (Low Urgency)
* **Goal**: Verify snap-fit engagement into an actual HSW wall panel, shortest-path side nut slot usability, and plug center-to-center pitch.
* **Objects to Print**:
  - `hsw_cleat_adapter_1u_standard_M3.stl` (40.88 mm vertical pitch) or `rotated` (23.6 mm pitch).
* **Timing**: Defer printing until primary MFC tool holders and standards are validated.

---

## Immediate Next Actions

1. **Verify Chisel Holder (P2.1)**:
   - Check test prints of deep shelf (38 mm) and $60^\circ$ chamfered ferrules.
2. **Structural Redesign of Clamp Holders (P3.1 & P3.2)**:
   - Reinforce corner clamp spine (5.0+ mm).
   - Widen F-clamp saddle to prevent pivoting.
3. **Eccentric Cam Holder Prototyping (P3.3)**:
   - Continue testing multi-tool cam mechanisms in `generate_shooo_cam_holder.py`.
