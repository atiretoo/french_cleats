import cadquery as cq
import argparse

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_library import create_baseplate, export_model, UNIT_WIDTH, BACKPLATE_THICKNESS

baseplate, *_ = create_baseplate()
baseplate, *_ = baseplate.translate((-100, 0, 0))
export_model(baseplate, "orientation_test.stl", category='strength_testing', print_orientation='none')
