## Clock signal
set_property -dict { PACKAGE_PIN R2 IOSTANDARD LVCMOS33 } [get_ports { ddr_clock }]
create_clock -add -name sys_clk_pin -period 10.000 -waveform {0 5} [get_ports { ddr_clock }]

## RGB LEDs (only lower 3 RGB LEDs are available on Arty S7-50, 3 bits per LED)
## Assuming 6 outputs: {rgb_led_tri_o[5], ..., rgb_led_tri_o[0]}
## You may connect only the available ones as needed.

## RGB LED (Active Low)
set_property PACKAGE_PIN L17 [get_ports {rgb_led_tri_o[0]}]  ; 
set_property PACKAGE_PIN L18 [get_ports {rgb_led_tri_o[1]}]  ; 
set_property PACKAGE_PIN M14 [get_ports {rgb_led_tri_o[2]}]  ; 

set_property IOSTANDARD LVCMOS33 [get_ports {rgb_led_tri_o[*]}]

## Reset (Assuming connected to one of the push buttons, say, BTN0)
#set_property -dict { PACKAGE_PIN R18s IOSTANDARD LVCMOS33 } [get_ports { reset }]

## I2C
set_property -dict { PACKAGE_PIN J14 IOSTANDARD LVCMOS33 } [get_ports { i2c_scl_io }]
set_property -dict { PACKAGE_PIN J13 IOSTANDARD LVCMOS33 } [get_ports { i2c_sda_io }]

set_property PACKAGE_PIN P18 [get_ports {gpio_rtl_tri_o}]  ; 
set_property IOSTANDARD LVCMOS33 [get_ports {gpio_rtl_tri_o}]





