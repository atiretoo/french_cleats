# Copyright (C) 2026 Andrew Tyre
#
# This file is part of french_cleats.
#
# french_cleats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# french_cleats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with french_cleats.  If not, see <https://www.gnu.org/licenses/>.
import os
import sys

# Add src to path to import generate_strength_tester

from generate_strength_tester import create_strength_tester
import cadquery as cq

def export_step_for_fea():
    print("Generating top thin strength tester...")
    # top position, thin (0.5 thickness factor)
    tester = create_strength_tester(position="top", thickness_factor=0.5)
    
    os.makedirs("strength_testing", exist_ok=True)
    filename = "strength_testing/tester_top_half_FEA.step"
    
    # Exporting as STEP is the most reliable way to pass CadQuery objects to FEA meshers like Gmsh
    cq.exporters.export(tester, filename)
    print(f"Exported STEP file for FEA to {filename}")

if __name__ == '__main__':
    export_step_for_fea()
