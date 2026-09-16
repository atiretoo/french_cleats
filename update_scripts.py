import os, re

# 1. Update holder_base.py
hb_path = "src/holder_base.py"
with open(hb_path, "r") as f:
    hb = f.read()

hb = hb.replace(
    'def export_stl(shape, filename, rotate_for_printing=True, category=""):',
    'def export_stl(shape, filename, rotate_for_printing=True, category="", export_step=True):'
)

# Replace the unconditional step export with a conditional one
hb = hb.replace(
    'cq.exporters.export(export_shape, out_path_step)',
    'if export_step:\n        cq.exporters.export(export_shape, out_path_step)'
)
# Fix the print statement
hb = hb.replace(
    'print(f"Exported {out_path_stl} and {out_path_step}")',
    'if export_step:\n        print(f"Exported {out_path_stl} and {out_path_step}")\n    else:\n        print(f"Exported {out_path_stl}")'
)
with open(hb_path, "w") as f:
    f.write(hb)

# 2. Update the scripts in src/strength_testing
files = [
    "generate_strength_tester.py",
    "generate_clamp_tester.py",
    "generate_corner_clamp_tester.py",
    "generate_fin_test.py"
]

for f in files:
    path = os.path.join("src", "strength_testing", f)
    with open(path, "r") as file:
        content = file.read()
    
    # Change category from 'utilities' to 'strength_testing' and add export_step=False
    # Previous: export_stl(..., category='utilities')
    # Change to: export_stl(..., category='strength_testing', export_step=False)
    content = re.sub(
        r"category='utilities'",
        "category='strength_testing', export_step=False",
        content
    )
    
    # If the file is generate_strength_tester, fix the filename string
    if f == "generate_strength_tester.py":
        content = content.replace('"strength_testing/tester_', '"tester_')
    
    with open(path, "w") as file:
        file.write(content)

print("Python scripts updated.")
