@echo off
echo Generating Cleats...
python src/cleats/generate_cleats.py --units 1 --mount groove
python src/cleats/generate_cleats.py --units 2 --mount groove
python src/cleats/generate_cleats.py --units 3 --mount groove
python src/cleats/generate_cleats.py --units 4 --mount groove

echo Generating OpenGrid Adapters...
python src/multiconnect/generate_opengrid_adapter.py --units 1
python src/multiconnect/generate_opengrid_adapter.py --units 2
python src/multiconnect/generate_opengrid_adapter.py --units 3
python src/multiconnect/generate_opengrid_adapter.py --units 4

echo Generating Screwdriver Holders...
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 10 --hole-spacing 25
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 14 --hole-spacing 30
python src/tool_holders/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-spacing 26 --hole-sizes 20,18,15.5,15,14,10 --recess-size 23 --recess-depth 1

echo Generating Clamp Holders...
python src/tool_holders/generate_clamp_holder.py --units 3 --num-slots 4 --mount groove

echo Generating Chisel Holders...
python src/tool_holders/generate_chisel_holder.py --units 4 --shelf-pos mid

echo Generating Slot Holders...
python src/tool_holders/generate_slot_holder.py --width-units 1 --depth-units 2 --slot-width 6.25 --back-clearance 10.0

echo Generating V Holders...
python src/tool_holders/generate_v_holder.py --width-units 2 --depth-units 4

echo Generating Power Tool Holders...
python src/tool_holders/generate_power_tool_holder.py --units 2 --mount groove

echo Generating Thin Tool Holders...
python src/tool_holders/generate_magnetic_holder.py --units 1 --mount groove
python src/tool_holders/generate_cam_holder.py --units 1 --mount groove

echo Generating Strength Testers...
python src/strength_testing/generate_strength_tester.py --mount groove

echo Generating Nut Pusher...
python src/utilities/generate_nut_pusher.py

echo Generating Corner Clamp Holders...
python src/tool_holders/generate_corner_clamp_holder.py

echo Generating Corner Clamp Tester...
python src/strength_testing/generate_corner_clamp_tester.py

echo Generating Shelves...
python src/gridfinity/generate_shelf.py --width-units 3 --depth-units 3
python src/gridfinity/generate_shelf.py --width-units 6 --depth-units 3
python src/gridfinity/generate_shelf.py --width-units 6 --depth-units 6

echo Generating Fin Test...
python src/strength_testing/generate_fin_test.py

echo Zipping STEP files for Release...
if exist exports\step_files.zip del exports\step_files.zip
powershell -Command "Compress-Archive -Path exports\step\* -DestinationPath exports\step_files.zip -Force"

echo Done!
