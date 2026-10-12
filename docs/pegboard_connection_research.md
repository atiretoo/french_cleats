# Pegboard & IKEA SKÅDIS Connection Taxonomy and Attachment Research

## Executive Summary

For the Printables **Designer Challenge: Pegboard Wall Organizers** (curated by agepbiz, October 2026), 3D-printed attachments for wall storage split into two primary geometric grid families and **six distinct mechanical connection archetypes**.

When designing a Modular French Cleat (MFC) adapter (where the adapter mounts to the board and presents MFC raised ridges on the front for mounting tool holders), standard gravity hooks are problematic because pulling a heavy workshop tool upward often pulls the adapter off the wall. This document classifies all existing connection types across both board families to inform our adapter designs.

---

## 1. Physical Grid & Board Standards

| Specification | Standard 1/4" Pegboard | IKEA SKÅDIS |
| :--- | :--- | :--- |
| **Hole Geometry** | Round holes ($\approx 6.35\text{ mm}$ / $1/4"$) | Rounded slots ($5.0\text{ mm}$ wide $\times 15.0\text{ mm}$ tall) |
| **Grid Spacing** | $1.0\text{ inch}$ ($25.4\text{ mm}$) square pitch | $40.0\text{ mm}$ vertical $\times 40.0\text{ mm}$ horizontal (staggered $20\text{ mm}$) |
| **Board Thickness** | $1/8"$ ($3.2\text{ mm}$) metal/hardboard to $1/4"$ ($6.35\text{ mm}$) composite | Exactly $5.0\text{ mm}$ composite wood/MDF |
| **Primary Failure Mode** | Hooks lift out & wobble when lifting heavy tools | Hooks dislodge easily upon tool withdrawal |

---

## 2. Classification of Connection Topologies

### Family A: Standard Round-Hole Pegboard (1" Grid, 1/4" Holes)

#### 1. Classic Tilt-and-Drop (L-Hook + Standoff Pin)
* **Mechanism**: An L-shaped top pin enters the hole when tilted $30^\circ\text{--}45^\circ$, drops behind the board, and a simple lower cylinder pin (1" or 2" down) sits in a lower hole to eliminate rotational sway.
* **Pros**: Single-piece, print-in-place, zero hardware.
* **Cons**: Tends to dislodge when an operator lifts a heavy tool straight up.

#### 2. Locking Pin / Slide-Wedge (e.g., Sy's Peglock Style)
* **Mechanism**: The top hook seats into the hole, leaving clearance above its neck. A separate printed vertical locking pin or sliding clip is pushed down into the remaining gap from the front, physically blocking the hook from pivoting upward.
* **Pros**: Rock-solid; completely prevents accidental pull-out.
* **Cons**: 2-piece design; requires vertical clearance above the mount to insert the pin.

#### 3. Compliant Snap-Fit / Split-Barb Rivets
* **Mechanism**: Two flexible cantilever prongs with angled lead-in chamfers and retaining barbs. Pushed straight into the hole from the front; they compress on entry and expand once past the board thickness.
* **Pros**: Installs straight from the front with zero upward tilting (ideal for wider multi-column cleats).
* **Cons**: Prone to layer delamination or creep under continuous heavy load if printed in PLA (requires PETG).

#### 4. Through-Bolt / Expansion Anchor
* **Mechanism**: Uses a captive M4/M5 screw through the pegboard hole into a printed or metal toggle nut on the back.
* **Pros**: Extreme pull-out load capacity (can hold full power-tool racks).
* **Cons**: Requires access to the back of the board or blind-toggle complexity.

---

### Family B: IKEA SKÅDIS (40 mm Grid, 5x15 mm Slots)

#### 1. Drop-In L-Hooks (First-Party Style)
* **Mechanism**: Flat tabs ($4.5\text{ mm}$ thick) with downward-facing hooks that pass through the $15\text{ mm}$ slot and drop down behind the $5\text{ mm}$ board, with a flat foot resting in the slot below.
* **Pros**: 1-piece, simple print.
* **Cons**: Notorious for lifting out when removing tools.

#### 2. Front-Inserted Locking Wedge / Key (Community Favorite)
* **Mechanism**: The hook only fills the bottom $8\text{ mm}$ of the slot. After insertion, a small printable wedge or slide-key is pressed into the remaining top $7\text{ mm}$ of the slot from the front, locking the hook tightly against the board.
* **Pros**: Completely wobble-free, zero lifting out, removable without damage.
* **Cons**: Requires a separate small wedge part.

#### 3. Quarter-Turn Twist-Lock (T-Nut / Cam-Lock)
* **Mechanism**: A horizontal T-shaped lug ($4.5\text{ mm}\times 14\text{ mm}$) passes through the slot and rotates $90^\circ$ into a vertical orientation, clamping the back face of the board.
* **Pros**: Installs from the front, high clamping force, doesn't require tilting.
* **Cons**: Multi-part rotating assembly.

#### 4. Compliant Dual-Barb Flex-Clips
* **Mechanism**: Dual spring arms that span the top and bottom of the $15\text{ mm}$ slot. Pushed straight in, they compress and then spring open with barbs seated against the rear $5\text{ mm}$ face.
* **Pros**: 1-piece, push-fit, perfectly flush.
* **Cons**: Requires PETG for long-term spring elasticity.

#### 5. Rear-Clamping Bolt / Skådis T-Nut
* **Mechanism**: M3/M4 bolt through the adapter front into a printable T-nut that sits vertically behind the slot. As the screw tightens, the T-nut rotates $90^\circ$ and clamps the board.
* **Pros**: Industrial rigidity, ideal for heavy modular rails.
* **Cons**: Requires metal hardware (screws/nuts).

---

## 3. Engineering Recommendations for MFC Contest Adapters

Because a French Cleat adapter is designed to support **heavy workshop tools**, traditional gravity hooks that lift out easily will hurt user reviews and contest voting.

For the contest entry, the most competitive approach:

1. **For Standard Pegboard**: 
   * **Recommended**: A **2-hole vertical bracket with an integrated slide-lock wedge** (or a 2-part pin). It demonstrates high engineering rigor and solves the #1 pegboard complaint (hooks pulling out with the tool).
2. **For IKEA SKÅDIS**:
   * **Recommended**: A **Drop-In + Front Slide Wedge** or a **Compliant Dual-Barb Flex-Clip** sized for the exact $5.0\text{ mm}$ board thickness. 
3. **The Cleat Face**:
   * On the front face, provide the MFC **raised ridge** and central M3 screw hole. 
   * A single 1U wide ($28\text{ mm}$) or 2U wide ($56\text{ mm}$) adapter plate with the ridge allows users to mount *any* Modular French Cleat tool holder directly onto their pegboard or Skådis wall!
