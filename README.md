# Open Source French Cleat System
**Version 1.2.0**

A fully parametric, modular 3D printed French Cleat organization system.

This project was born out of necessity for my own workshop. I needed heavy-duty tool holders for heavy tools and jigs. I initially experimented with Hexagon Storage Wall (HSW) and OpenGrid, but ultimately returned to the strength of French cleats. However, I found that every French cleat tool holder on Printables used wildly different approaches for sizing tools, with inconsistent cleat thicknesses and heights. This repository is an attempt to standardize French cleat tool holders into a unified, highly tolerant, and predictable system.

## Rationale & Inspiration

While designing this system, I built upon the brilliant work already done by many, taking the best aspects of several existing systems and synthesizing them into a unified, highly tolerant standard. 

- **The Cleat Separation:** I was initially drawn to **Frenchfinity** (created by Bastelsaal) for the excellent concept of separating the cleat base from the tool holder itself. However, I found it difficult to slide the Frenchfinity holders and cleats together in practice (My printer may not be as dialed in as I think). I wanted to retain that two-part modularity but engineer a connection that was easier to assemble and lock.
- **The Locking Mechanism:** I was heavily inspired by Printables user **shoooo** (@shoooo_1013338), who utilized screws and ridges on a couple of models. Taking that concept, I standardized it and shifted to a **trapezoidal groove**, which provided a much tighter, self-aligning fit between the holder and the cleat.
- **The Grid Ecosystem:** To ensure this system doesn't exist in a vacuum, I designed the mounting dimensions to retain full compatibility with both **Gridfinity** (created by Zack Freedman) and **OpenGrid** (created by David D). Specifically, I adopted the OpenGrid spacing standard of **28 mm** across all the tool holders to ensure they interoperate flawlessly with existing Gridfinity and OpenGrid setups.

For a deeper dive into the iterations, FEA testing, and the history of the project's development, check out the [Design Rationale & History](docs/design_rationale_and_history.md) document.

## How to Install & Use

This project uses Python and [CadQuery](https://cadquery.readthedocs.io/) to generate 3D models (STL files) from code. You don't need to be a Python expert to generate your own tool holders, just follow these steps:

### 1. Install Prerequisites
You will need Python installed on your computer. 
*   **Install uv:** I highly recommend using `uv` (a very fast Python package manager). You can install it following [their official guide](https://docs.astral.sh/uv/getting-started/installation/).

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

## Attributions & Shoutouts

This project stands on the shoulders of giants. Huge thanks to the following creators and developers:

*   **Gridfinity** by Zack Freedman ([YouTube Introduction](https://www.youtube.com/watch?v=ra_9zU-mnl8))
*   **OpenGrid** by David D ([Printables Model #1214361](https://www.printables.com/model/1214361-opengrid-walldesk-mounting-framework-and-ecosystem))
*   **Frenchfinity** by Bastelsaal ([frenchfinity.xyz](https://frenchfinity.xyz/))
*   **Screw & Ridge Inspiration** by shoooo ([@shoooo_1013338 on Printables](https://www.printables.com/@shoooo_1013338))

## Development & AI Policy: The "Centaur" Approach

This project is developed using a collaborative human-AI workflow. The code, architecture, and documentation were written and refined with the assistance of advanced AI models. 

I approach AI not as a tool for blind self-automation, but as a collaborative interaction. I aspire to be a [centaur](https://mitsloan.mit.edu/ideas-made-to-matter/3-ways-to-use-ai-are-you-a-cyborg-a-centaur-or-a-self-automator), "... maintain[ing] structured and controlled interactions with AI, harnessing it as a tool for targeted efficiency". I acknowledge that when learning a new domain I might be a cyborg "... collaborat[ing] closely with the AI tool -- probing its suggestions, allowing it to lead the way, and taking its advice on some occasions while pushing back against it on others." Both are OK. In this model, the AI acts as a high-powered pair-programming partner. It helps me rapidly explore and develop my own understanding of complex topics. Meanwhile, I hold the strategic vision, conduct the physical testing/validation, and apply and build domain knowledge as I go.

For rules regarding AI-assisted contributions from the community, please see the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project utilizes a **Dual License** structure to comply with both software and open-source hardware best practices. These specific open-source licenses were chosen to support the transition to an anarchist economy—promoting mutual aid, free distribution of information, and breaking down artificial scarcity.

*   **Software (Python Code):** All source code in this repository is licensed under the [GNU General Public License v3.0 (GPLv3)](LICENSE). This ensures that any modifications to the code remain open-source and provides explicit patent protections.
*   **Hardware (3D Models):** The generated output files (STL and STEP files) are licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](LICENSE-MODELS.txt). This is the standard license for the 3D printing community.
