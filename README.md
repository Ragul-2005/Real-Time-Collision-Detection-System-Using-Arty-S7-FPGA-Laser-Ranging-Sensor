# Real-Time-Collision-Detection-System-Using-Arty-S7-FPGA-Laser-Ranging-Sensor

## Project Overview

Real-Time Collision Detection System using Arty S7 FPGA and VL53L0X LiDAR sensor. Implements an AXI-based MicroBlaze soft processor for I2C communication to measure distance and trigger alerts. Designed for high-speed, accurate object detection in embedded and automotive safety applications.

---

## Hardware Required 

- **FPGA Board:** Arty S7-50
- **Sensor:** VL53L0X Time-of-Flight (LiDAR) Sensor
- **Other Components:**  RGB LEDs for distance indication

## Software & Tools

- **Vivado Design Suite** (for hardware design and bitstream generation)
- **Vitis IDE** (for software development on MicroBlaze)
- **Xilinx SDK Drivers** (for I2C communication with VL53L0X)
- **Language:** Verilog (for hardware) & C (for firmware)

---

## Workflow / Design Steps

### **1. Hardware Design (Vivado)**
- Create a new Vivado project for Arty S7 FPGA.
- Add a **MicroBlaze soft processor** with AXI Interconnect.
- Integrate **AXI IIC IP core** for VL53L0X sensor communication.
- Integrate **AXI UART IP core** for Website communication.
- Add **AXI GPIO IP** for RGB LED, Buzzer control.
- Connect to **BRAM controllers** and configure address mapping.
- Validate design, generate bitstream, and export to Vitis.

### **2. Software Development (Vitis)**
- Create a new Vitis application project using the exported hardware.
- Include VL53L0X driver and initialize the sensor via I2C.
- Read distance measurements in real time.
- Apply logic to control **RGB LEDs** based on distance thresholds.
- Build and load the application on FPGA.

### **3. Testing**
- Power on FPGA board and VL53L0X sensor.
- Observe RGB LED color changes based on object distance.
- Validate detection range and timing performance.

---




