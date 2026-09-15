# Open Source French Cleat System

A fully parametric, modular 3D-printable French Cleat organization system.

This project was born out of necessity for Drew Tyre's own workshop. He needed heavy-duty tool holders for heavy tools and jigs. He initially experimented with Hexagon Storage Wall (HSW) and OpenGrid, but ultimately returned to the strength of French cleats. However, he found that every French cleat tool holder on Printables used wildly different approaches for sizing tools, with inconsistent cleat thicknesses and heights. This repository is an attempt to standardize French cleat tool holders into a unified, highly tolerant, and predictable system.

The files are released under the **CC BY-SA 4.0 (Copyleft)** license. This specific open-source license was chosen to support the transition to an anarchist economy—promoting mutual aid, free distribution of information, and breaking down artificial scarcity. Anyone is free to download, print, modify, and even commercialize these files, provided they attribute the original creators and share any modifications under the exact same open license.

## How to Install & Use

This project uses Python and [CadQuery](https://cadquery.readthedocs.io/) to generate 3D models (STL files) from code. You don't need to be a Python expert to generate your own tool holders, just follow these steps:

### 1. Install Prerequisites
You will need Python installed on your computer. 
*   **Install uv:** We highly recommend using `uv` (a very fast Python package manager). You can install it following [their official guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Setup the Project
Clone the repository and install `cadquery`:
```bash
git clone https://github.com/atiretoo/french_cleats.git
cd french_cleats

# Create a virtual environment and install dependencies
uv venv
uv pip install cadquery
```

### 3. Generate the Models
You can run the generator scripts individually (e.g., `python src/generate_cleats.py`), or use the provided batch/shell scripts to generate the entire ecosystem at once into an `exports/` folder.

**On Windows:**
Activate the environment and run the batch file:
```cmd
.venv\Scripts\activate
generate_all.bat
```

**On Mac / Linux:**
Activate the environment and run the shell script:
```bash
source .venv/bin/activate
chmod +x generate_all.sh
./generate_all.sh
```

## Rationale & Inspiration

While designing this system, we wanted to build upon the brilliant work already done by the maker community, taking the best aspects of several existing systems and synthesizing them into a unified, highly tolerant standard.

- **The Cleat Separation:** We were initially drawn to **Frenchfinity** (created by Bastelsaal) for the excellent concept of separating the cleat base from the tool holder itself. However, we found it difficult to slide the Frenchfinity holders and cleats together in practice. We wanted to retain that two-part modularity but engineer a connection that was easier to assemble and lock.
- **The Locking Mechanism:** We were heavily inspired by Printables user **shoooo** (@shoooo_1013338), who utilized screws and ridges on a couple of models. Taking that concept, we standardized it and shifted to a **trapezoidal groove**, which provided a much tighter, self-aligning fit between the holder and the cleat.
- **The Grid Ecosystem:** To ensure this system doesn't exist in a vacuum, we designed the mounting dimensions to retain full compatibility with both **Gridfinity** (created by Zack Freedman) and **OpenGrid** (created by David D). Specifically, we adopted the OpenGrid spacing standard of **28 mm** across all the tool holders to ensure they interoperate flawlessly with existing Gridfinity and OpenGrid setups.

## Attributions & Shoutouts

This project stands on the shoulders of giants. Huge thanks to the following creators and developers:

*   **Gridfinity** by Zack Freedman ([YouTube Introduction](https://www.youtube.com/watch?v=ra_9zU-mnl8))
*   **OpenGrid** by David D ([Printables Model #1214361](https://www.printables.com/model/1214361-opengrid-walldesk-mounting-framework-and-ecosystem))
*   **Frenchfinity** by Bastelsaal ([frenchfinity.xyz](https://frenchfinity.xyz/))
*   **Screw & Ridge Inspiration** by shoooo ([@shoooo_1013338 on Printables](https://www.printables.com/@shoooo_1013338))

## Development & AI Policy: The "Centaur" Approach

This project is developed using a collaborative human-AI workflow. The CadQuery scripts, Python generators, and overall system architecture were written and refined with the assistance of **Google Gemini**. 

We approach AI not as a tool for blind automation, but as a [collaborative "Centaur"](https://mitsloan.mit.edu/ideas-made-to-matter/3-ways-to-use-ai-are-you-a-cyborg-a-centaur-or-a-self-automator). In this model, the AI acts as a high-powered pair-programming partner. It helps us rapidly explore and develop our own understanding of complex topics—whether that is navigating the quirks of 3D modeling coordinate systems, calculating trapezoidal tolerances, or optimizing Python code. Meanwhile, we maintain the strategic vision, conduct the physical testing, and apply and build domain knowledge in maker systems as we go.

For rules regarding AI-assisted contributions from the community, please see our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](LICENSE).
