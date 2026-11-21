#ifndef __BSP_OLED_H
#define __BSP_OLED_H

#include "main.h"        // ?? HAL ???? GPIO ??(???????)
#include <stdint.h>

/* ================== ????(???????) ================== */
/* ?? OLED ?? GPIOD: RST=PD12, DC=PD11, SCL=PD14, SDA=PD13 */
#define OLED_RST_PORT   GPIOD
#define OLED_RST_PIN    GPIO_PIN_12

#define OLED_DC_PORT    GPIOD
#define OLED_DC_PIN     GPIO_PIN_11

#define OLED_SCL_PORT   GPIOD
#define OLED_SCL_PIN    GPIO_PIN_14

#define OLED_SDA_PORT   GPIOD
#define OLED_SDA_PIN    GPIO_PIN_13

/* ================== ?????(HAL) ================== */
#define OLED_RST_Clr()   HAL_GPIO_WritePin(OLED_RST_PORT, OLED_RST_PIN, GPIO_PIN_RESET)
#define OLED_RST_Set()   HAL_GPIO_WritePin(OLED_RST_PORT, OLED_RST_PIN, GPIO_PIN_SET)

#define OLED_RS_Clr()    HAL_GPIO_WritePin(OLED_DC_PORT,  OLED_DC_PIN,  GPIO_PIN_RESET)
#define OLED_RS_Set()    HAL_GPIO_WritePin(OLED_DC_PORT,  OLED_DC_PIN,  GPIO_PIN_SET)

#define OLED_SCLK_Clr()  HAL_GPIO_WritePin(OLED_SCL_PORT, OLED_SCL_PIN, GPIO_PIN_RESET)
#define OLED_SCLK_Set()  HAL_GPIO_WritePin(OLED_SCL_PORT, OLED_SCL_PIN, GPIO_PIN_SET)

#define OLED_SDIN_Clr()  HAL_GPIO_WritePin(OLED_SDA_PORT, OLED_SDA_PIN, GPIO_PIN_RESET)
#define OLED_SDIN_Set()  HAL_GPIO_WritePin(OLED_SDA_PORT, OLED_SDA_PIN, GPIO_PIN_SET)

#define OLED_CMD   0
#define OLED_DATA  1

#define OLED_Height  64
#define OLED_Width   128

#define CNSizeWidth  16
#define CNSizeHeight 16

/* ================== ???? ================== */
extern uint8_t OLED_GRAM[128][8];

/* ================== ???? ================== */
void OLED_WR_Byte(uint8_t dat, uint8_t cmd);
void OLED_Display_On(void);
void OLED_Display_Off(void);
void OLED_Refresh_Gram(void);
void OLED_Refresh_Line(void);
void OLED_Init0(void);
void OLED_Clear(void);
void OLED_DrawPoint(uint8_t x, uint8_t y, uint8_t t);
void OLED_DrawPoint_Shu(uint8_t x, uint8_t y, uint8_t t);
void OLED_ShowChar(uint8_t x, uint8_t y, uint8_t chr, uint8_t size, uint8_t mode);
void OLED_ShowNumber(uint8_t x, uint8_t y, uint32_t num, uint8_t len, uint8_t size);
void OLED_ShowString(uint8_t x, uint8_t y, const uint8_t *p);
void OLED_ShowString16(uint8_t x, uint8_t y, const uint8_t *p);
void OLED_ShowFloat(uint8_t show_x, uint8_t show_y, const float needtoshow, uint8_t zs_num, uint8_t xs_num);

void OLED_Set_Pos(unsigned char x, unsigned char y);
void OLED_DrawBMP(unsigned char x0, unsigned char y0, unsigned char x1, unsigned char y1, const unsigned char BMP[]);
void OLED_Show_POT(void);

extern const unsigned char gImage_usb[420];

#endif