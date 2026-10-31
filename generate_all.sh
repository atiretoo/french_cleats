#!/bin/bash
echo "Generating Cleats..."
python src/cleats/generate_cleats.py --units 1
python src/cleats/generate_cleats.py --units 2
python src/cleats/generate_cleats.py --units 3
python src/cleats/generate_cleats.py --units 4

echo "Generating OpenGrid Adapters..."
python src/multiconnect/generate_opengrid_adapter.py --units 1
python src/multiconnect/generate_opengrid_adapter.py --units 2
python src/multiconnect/generate_opengrid_adapter.py --units 3
python src/multiconnect/generate_opengrid_adapter.py --units 4

echo "Generating Screwdriver Holders..."
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 10 --hole-spacing 25
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 14 --hole-spacing 30
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-spacing 26 --hole-sizes 20,18,15.5,15,14,10 --recess-size 23 --recess-depth 1

echo "Generating Clamp Holders..."
python src/tool_holders/generate_clamp_holder.py --units 4 --num-slots 4

echo "Generating Chisel Holders..."
python src/tool_holders/generate_chisel_holder.py --tools 4 --spacing 35.0 --shelf-pos mid

echo "Generating Slot Holders..."
python src/tool_holders/generate_slot_holder.py --width-units 1 --depth-units 2 --slot-width 6.25 --back-clearance 10.0
python src/tool_holders/generate_slot_holder.py --width-units 1 --depth-units 3 --slot-width 6.25 --back-clearance 9.0

echo "Generating V Holders..."
python src/tool_holders/generate_v_holder.py --width-units 2 --depth-units 4

echo "Generating Power Tool Holders..."
python src/tool_holders/generate_power_tool_holder.py --units 2

echo "Generating Sheet Metal Tool Holders..."
python src/tool_holders/generate_sheet_metal_holder.py --units 1 --metal-width 25.0

echo "Generating Multi-Tool Cam Holders..."
python src/tool_holders/generate_shooo_cam_holder.py --tools 1 --tilt-fin
python src/tool_holders/generate_shooo_cam_holder.py --tools 2 --tilt-fin
python src/tool_holders/generate_shooo_cam_holder.py --tools 3 --tilt-fin
python src/tool_holders/generate_shooo_cam_holder.py --tools 4 --tilt-fin
python src/tool_holders/generate_shooo_cam_holder.py --tools 5 --tilt-fin

echo "Generating Hook Holders..."
python src/tool_holders/generate_hook.py --width-units 1 --length-units 4 --diameter 10.0 --slope 5.0

echo "Generating Hose and Extension Cord Holders..."
python src/tool_holders/generate_hose_holder.py --units 7 --depth 150.0

echo "Generating HSW Cleat Adapters..."
python src/hsw/generate_hsw_cleat_adapter.py --hsw-orientation standard
python src/hsw/generate_hsw_cleat_adapter.py --hsw-orientation rotated

echo "Generating Pegboard Adapters..."
python src/pegboard/generate_pegboard_adapter.py --generate-all

echo "Generating IKEA Skadis Adapters..."
python src/pegboard/generate_skadis_adapter.py --generate-all

echo "Generating Shelf-Edge Cleat Adapters..."
python src/shelf/generate_shelf_edge_adapter.py --units 2 --rail-height 73.0 --screw M3
python src/shelf/generate_shelf_edge_adapter.py --units 7 --rail-height 73.0 --screw M3
python src/shelf/generate_shelf_edge_adapter.py --test-wedge --test-spacing

echo "Generating Auxiliary Tools..."
python src/utilities/generate_nut_pusher.py --screw M3
python src/utilities/generate_nut_pusher.py --screw M4
python src/utilities/generate_nut_pusher.py --screw M5

echo "Generating Strength Testers..."
python src/strength_testing/generate_strength_tester.py
python src/strength_testing/generate_ridge_groove_tester.py

echo "Generating Corner Clamp Holders..."
python src/tool_holders/generate_corner_clamp_holder.py

echo "Generating Mallet Holders..."
python src/tool_holders/generate_mallet_holder.py --units 3

echo "Generating Claw Hammer Holders..."
python src/tool_holders/generate_claw_hammer_holder.py --units 2

echo "Generating Corner Clamp Tester..."
python src/strength_testing/generate_corner_clamp_tester.py

echo "Generating Shelves..."
python src/gridfinity/generate_shelf.py --width-units 1 --depth-units 1
python src/gridfinity/generate_shelf.py --width-units 3 --depth-units 3
python src/gridfinity/generate_shelf.py --width-units 6 --depth-units 3
python src/gridfinity/generate_shelf.py --width-units 6 --depth-units 6

echo "Zipping STEP files for Release..."
cd exports && zip -r step_files.zip step/ && cd ..

echo "Done!"
