#include "xgpio.h"
#include "xiic.h"
#include "xuartlite.h"
#include "xparameters.h"
#include "sleep.h"
#include "stdio.h"
#include "string.h"

#define VL53L0X_I2C_ADDR   0x29

// Define LED masks for the RGB LED (axi_gpio_0)
#define RED_LED1_MASK      0x01
#define GREEN_LED_MASK     0x02 
#define YELLOW_LED_MASK     0x04

// Define LED mask for the error LED/Buzzer (axi_gpio_1)
#define ERROR_BUZZER_MASK  0x01

XIic IicInstance;
XGpio Gpio0_Instance; // For RGB LED
XGpio Gpio1_Instance; // For the Buzzer
XUartLite UartInstance;

#define SYSRANGE_START      0x00
#define RESULT_RANGE_VAL    0x1E


// Function declarations...
int uart_init();
void uart_send_string(const char* str);
void uart_send_distance(u16 distance);
int vl53l0x_start_ranging();
u16 vl53l0x_read_distance();
void blink_led(XGpio *GpioInst, u32 led_mask, int delay_ms);
void generate_software_buzzer_tone(XGpio *GpioInst, int duration_ms);


int uart_init() {
    int Status;
    Status = XUartLite_Initialize(&UartInstance, XPAR_AXI_UARTLITE_0_BASEADDR);
    if (Status != XST_SUCCESS) { return XST_FAILURE; }
    return XST_SUCCESS;
}

void uart_send_string(const char* str) {
    XUartLite_Send(&UartInstance, (u8*)str, strlen(str));
    while (XUartLite_IsSending(&UartInstance));
}

void uart_send_distance(u16 distance) {
    char buffer[32];
    if (distance == 0xFFFF) {
        sprintf(buffer, "distance: ERROR\r\n");
    } else {
        sprintf(buffer, "distance: %d mm\r\n", distance);
    }
    uart_send_string(buffer);
}

int vl53l0x_start_ranging() {
    u8 cmd[2] = {SYSRANGE_START, 0x01};
    int Status = XIic_Send(IicInstance.BaseAddress, VL53L0X_I2C_ADDR, cmd, 2, XIIC_STOP);
    return (Status == 2) ? XST_SUCCESS : XST_FAILURE;
}

u16 vl53l0x_read_distance() {
    u8 reg = RESULT_RANGE_VAL;
    u8 data[2];
    int Status = XIic_Send(IicInstance.BaseAddress, VL53L0X_I2C_ADDR, &reg, 1, XIIC_REPEATED_START);
    if (Status != 1) return 0xFFFF;
    Status = XIic_Recv(IicInstance.BaseAddress, VL53L0X_I2C_ADDR, data, 2, XIIC_STOP);
    if (Status != 2) return 0xFFFF;
    return (data[0] << 8) | data[1];
}

void blink_led(XGpio *GpioInst, u32 led_mask, int delay_ms) {
    XGpio_DiscreteWrite(GpioInst, 1, led_mask);
    usleep(delay_ms * 1000);
    XGpio_DiscreteClear(GpioInst, 1, led_mask);
    usleep(delay_ms * 1000);
}


int main() {
    int Status;
    u16 distance;
    XIic_Config *IicConfig;
    XGpio_Config *Gpio0_Config, *Gpio1_Config;

    // --- Initialization ---
    uart_init();
    IicConfig = XIic_LookupConfig(XPAR_AXI_IIC_0_BASEADDR);
    XIic_CfgInitialize(&IicInstance, IicConfig, IicConfig->BaseAddress);
    Gpio0_Config = XGpio_LookupConfig(XPAR_AXI_GPIO_0_BASEADDR);
    XGpio_CfgInitialize(&Gpio0_Instance, Gpio0_Config, Gpio0_Config->BaseAddress);
    XGpio_SetDataDirection(&Gpio0_Instance, 1, 0x0);
    Gpio1_Config = XGpio_LookupConfig(XPAR_AXI_GPIO_1_BASEADDR);
    XGpio_CfgInitialize(&Gpio1_Instance, Gpio1_Config, Gpio1_Config->BaseAddress);
    XGpio_SetDataDirection(&Gpio1_Instance, 1, 0x0);

    usleep(200000);
    uart_send_string("VL53L0X Distance Monitor Started\r\n");
  
   
    // --- Main Loop with Updated Logic ---
    while (1) {
        vl53l0x_start_ranging();
        usleep(50000);
        distance = vl53l0x_read_distance();
        uart_send_distance(distance);

        
        if (distance >20 && distance < 150) {
            // DANGER ZONE (< 15cm): Solid RED LED, Buzzer ON
            XGpio_DiscreteWrite(&Gpio0_Instance, 1, RED_LED1_MASK);
            generate_software_buzzer_tone(&Gpio1_Instance, 50);
            

        }  else if (distance >150 && distance <400) {
            // SAFE ZONE (> 40cm): Solid GREEN LED, Buzzer OFF
            XGpio_DiscreteWrite(&Gpio0_Instance, 1, YELLOW_LED_MASK);
             generate_software_buzzer_tone(&Gpio1_Instance, 100);
         
        }
        else if(distance >400)  {
            // WARNING ZONE (15cm to 40cm): Solid YELLOW LED, Buzzer OFF
            XGpio_DiscreteWrite(&Gpio0_Instance, 1, GREEN_LED_MASK);
               XGpio_DiscreteWrite(&Gpio1_Instance, 1, 0); // Buzzer OFF
        }
        else {
    // SAFE ZONE (> 40cm): This also catches the "out of bound" reading.
    XGpio_DiscreteWrite(&Gpio0_Instance, 1, GREEN_LED_MASK); // Green LED ON
    XGpio_DiscreteWrite(&Gpio1_Instance, 1, 0);             // Buzzer OFF
}
        usleep(10000);
    }
    return 0;
}
void generate_software_buzzer_tone(XGpio *GpioInst, int duration_ms) {
    // For a 500Hz tone, the period is 2ms (2000 us).
    // Each half-period (ON or OFF) is 1ms (1000 us).
    const int half_period_us = 1000;
    int cycles = duration_ms * 1000 / (half_period_us * 2);

    for (int i = 0; i < cycles; i++) {
        XGpio_DiscreteWrite(GpioInst, 1, 1); // Buzzer ON
        usleep(half_period_us);
        XGpio_DiscreteWrite(GpioInst, 1, 0); // Buzzer OFF
        usleep(half_period_us);
    }
}