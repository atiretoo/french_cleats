#!/bin/bash
echo "Generating Cleats..."
python src/cleats/generate_cleats.py --units 1 --mount groove
python src/cleats/generate_cleats.py --units 2 --mount groove
python src/cleats/generate_cleats.py --units 3 --mount groove
python src/cleats/generate_cleats.py --units 4 --mount groove

echo "Generating OpenGrid Adapters..."
python src/multiconnect/generate_opengrid_adapter.py --units 1
python src/multiconnect/generate_opengrid_adapter.py --units 2
python src/multiconnect/generate_opengrid_adapter.py --units 3
python src/multiconnect/generate_opengrid_adapter.py --units 4

echo "Generating Screwdriver Holders..."
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 10 --hole-spacing 25
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 14 --hole-spacing 30
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-spacing 26 --hole-sizes 20,18,15.5,15,14,10 --recess-size 23 --recess-depth 1


echo "Generating Chisel Holders..."
python src/tool_holders/generate_chisel_holder.py --tools 4 --spacing 35.0 --shelf-pos mid

echo "Generating Slot Holders..."
python src/tool_holders/generate_slot_holder.py --width-units 1 --depth-units 2 --slot-width 6.25 --back-clearance 10.0

echo "Generating V Holders..."
python src/tool_holders/generate_v_holder.py --width-units 2 --depth-units 4

echo "Generating Power Tool Holders..."
python src/tool_holders/generate_power_tool_holder.py --units 2 --mount groove

echo "Generating Thin Tool Holders..."
python src/tool_holders/generate_magnetic_holder.py --units 1 --mount groove --mag-count 2 --mag-dia 10.2 --mag-depth 2.0
python src/tool_holders/generate_magnetic_holder.py --units 1 --mount groove --mag-count 3 --mag-dia 10.2 --mag-depth 2.0
python src/tool_holders/generate_magnetic_holder.py --units 1 --mount groove --mag-count 2 --mag-dia 19.2 --mag-depth 2.0

echo "Generating Hook Holders..."
python src/tool_holders/generate_hook.py --width-units 1 --length-units 4 --diameter 10.0 --slope 5.0

echo "Generating Auxiliary Tools..."
python src/utilities/generate_nut_pusher.py --screw M3 --handle-length 11.0
python src/utilities/generate_nut_pusher.py --screw M4 --handle-length 11.0

echo "Generating Strength Testers..."
python src/strength_testing/generate_strength_tester.py --mount groove



echo "Generating Shelves..."
python src/gridfinity/generate_shelf.py --width-units 3 --depth-units 3
python src/gridfinity/generate_shelf.py --width-units 6 --depth-units 3
python src/gridfinity/generate_shelf.py --width-units 6 --depth-units 6

echo "Zipping STEP files for Release..."
cd exports && zip -r step_files.zip step/ && cd ..

echo "Done!"
