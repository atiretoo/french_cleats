/*
 * Pegboard Spacer.scad
 *
 */


$fn=100;

spacer_hole_diameter  = 6.0;
spacer_wall_thickness = 4.0;
spacer_height         = 8.5;

difference() {
    cylinder(d=spacer_hole_diameter+spacer_wall_thickness*2, h=spacer_height, center=true);
    cylinder(d=spacer_hole_diameter, h=spacer_height+0.1, center=true);
}
