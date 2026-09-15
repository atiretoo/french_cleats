@echo off
echo Generating Cleats...
python src/generate_cleats.py --units 1 --mount groove
python src/generate_cleats.py --units 2 --mount groove
python src/generate_cleats.py --units 3 --mount groove
python src/generate_cleats.py --units 4 --mount groove

echo Generating Screwdriver Holders...
python src/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 10 --hole-spacing 25
python src/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-size 14 --hole-spacing 30
python src/generate_screwdriver_holder.py --width-units 1 --depth-units 6 --hole-spacing 26 --hole-sizes 20,18,15.5,15,14,10 --recess-size 23 --recess-depth 1

echo Generating Clamp Holders...
python src/generate_clamp_holder.py --units 3 --num-slots 4 --mount groove

echo Generating Chisel Holders...
python src/generate_chisel_holder.py --units 4 --shelf-pos mid

echo Generating Slot Holders...
python src/generate_slot_holder.py --width-units 1 --depth-units 2 --slot-width 6.25 --back-clearance 10.0

echo Generating V Holders...
python src/generate_v_holder.py --width-units 2 --depth-units 4

echo Generating Strength Testers...
python src/generate_strength_tester.py --mount groove

echo Done!

echo Generating Nut Pusher...
python src/generate_nut_pusher.py

echo Generating Corner Clamp Holders...
python src/generate_corner_clamp_holder.py

echo Generating Corner Clamp Tester...
python src/generate_corner_clamp_tester.py

echo Generating Shelves...
python src/generate_shelf.py --width-units 3 --depth-units 3
python src/generate_shelf.py --width-units 6 --depth-units 3

python src/generate_shelf.py --width-units 6 --depth-units 6
