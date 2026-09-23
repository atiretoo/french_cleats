# Digital Assets (Reference CAD Models)

This directory stores upstream reference CAD files (STEP format) used by the parametric generator scripts in `src/`. 

All files stored here are small, standardized interface geometries required to ensure interoperability between the French Cleat system, Honeycomb Storage Wall (HSW), and OpenGrid / Multiconnect ecosystems.

---

## 1. Honeycomb Storage Wall (HSW)

Located in [`assets/hsw/`](hsw/):

| File | Description | Source / Upstream Project | Author | License |
|---|---|---|---|---|
| `insert-empty.step` | Standard HSW friction/snap-fit male plug template | [Honeycomb Storage Wall on Printables](https://www.printables.com/model/152592-honeycomb-storage-wall) | RostaP (@RostaP) | CC BY-NC 4.0 / Public Domain Reference |

**Usage in Code**:
- Used by [`src/hsw/generate_hsw_cleat_adapter.py`](../src/hsw/generate_hsw_cleat_adapter.py) to extract the authentic 8.0 mm tall snap-fit male plug geometry (retaining authentic lead-in chamfers and retention tabs).

---

## 2. Multiconnect / OpenGrid

Located in [`assets/multiconnect/`](multiconnect/):

| File | Description | Source / Upstream Project | Author | License |
|---|---|---|---|---|
| `round.step` | Multiconnect round male mounting button | [Multiconnect System on Printables](https://www.printables.com/model/285083-multiconnect-generic-connector-for-everything) | David D (@DavidD) | CC BY-NC-SA 4.0 |
| `top-back.step` | Top block with closed top slot for OpenGrid | [OpenGrid System on Printables](https://www.printables.com/model/1214361-opengrid-walldesk-mounting-framework-and-ecosystem) | David D (@DavidD) | CC BY-NC-SA 4.0 |
| `raw-slot-back.step` | Intermediate slot block for OpenGrid | [OpenGrid System on Printables](https://www.printables.com/model/1214361-opengrid-walldesk-mounting-framework-and-ecosystem) | David D (@DavidD) | CC BY-NC-SA 4.0 |
| `opening-raw-slot-back.step`| Open intermediate slot block | [OpenGrid System on Printables](https://www.printables.com/model/1214361-opengrid-walldesk-mounting-framework-and-ecosystem) | David D (@DavidD) | CC BY-NC-SA 4.0 |
| `embed-back-end.step` | Bottom end block with slot bottom stop | [OpenGrid System on Printables](https://www.printables.com/model/1214361-opengrid-walldesk-mounting-framework-and-ecosystem) | David D (@DavidD) | CC BY-NC-SA 4.0 |
| `slot-opening.step` | Cutter profile for slot insertion opening | [OpenGrid System on Printables](https://www.printables.com/model/1214361-opengrid-walldesk-mounting-framework-and-ecosystem) | David D (@DavidD) | CC BY-NC-SA 4.0 |

**Usage in Code**:
- Used by [`src/core_library.py`](../src/core_library.py) for `--mount multiconnect` backplates.
- Used by [`src/cleats/generate_cleats.py`](../src/cleats/generate_cleats.py) for Multiconnect-backed top cleats.
- Used by [`src/multiconnect/generate_opengrid_adapter.py`](../src/multiconnect/generate_opengrid_adapter.py) for OpenGrid wall-to-cleat adapters.

---

## Technical Policy & Best Practices

1. **No External Machine Path Dependencies**: Generator scripts determine asset locations relative to the repository root via `os.path.join(REPO_ROOT, "assets", ...)`. Scripts do not search host directories (like `Desktop` or `OneDrive`).
2. **Explicit CLI Overrides**: All generator scripts accept CLI arguments (e.g. `--step-path` or `--multiconnect-dir`) to allow developers to supply custom or experimental STEP files without modifying source code.
3. **Direct Git Tracking**: Compact reference STEP files are tracked directly in Git to keep cloning and generating completely frictionless without Git LFS requirements.
