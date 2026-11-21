/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Main program body
 ******************************************************************************
 * @attention
 *
 * Copyright (c) 2026 STMicroelectronics.
 * All rights reserved.
 *
 * This software is licensed under terms that can be found in the LICENSE file
 * in the root directory of this software component.
 * If no LICENSE file comes with this software, it is provided AS-IS.
 *
 ******************************************************************************
 */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "drv_uart.h"
#include "bsp_oled.h"
//#include "Motor.h"
#include "Encoder.h"
#include "alg_pid.h"
#include "bsp_adc.h"
#include <string.h>
#include <stdlib.h>
#include "diff_drive_ik.cpp"
#include "BLDC.h"
#include "Motor_cpp_style.h"
#include "Servo.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define UART1_RX_SIZE 64
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
uint8_t UART1_Rx_Buffer[UART1_RX_SIZE];

Class_PID PID_MotorA;
Class_PID PID_MotorB;
Class_PID PID_MotorC;
Class_PID PID_MotorD;

Motor Motor_A;
Motor Motor_B;
Motor Motor_C;
Motor Motor_D;

Servo Servo_Pitch;
Servo Servo_Yaw;

using namespace diff_drive;
IKParams p;
DiffDriveIK ik(p);
IKOutput out;
CommandSmoother smoother(0.05f, 0.02f);//50hz调用


float Kp = 3.0f;
float Ki = 12.0f;
float Kd = 0.0f;
float Kf = 0.0f;

volatile float vx_cmd = 0.0f, om_cmd = 0.0f;//原始目标，平滑后目标写在了中断中，
                                                                  //值由串口获得
volatile float vx_f=0.0f, om_f=0.0f;//平滑后目标
volatile float phiL_last = 0.0f;   /* 上次左轮 target 转速 rad/s*/
volatile float phiR_last = 0.0f;   /* 上次右轮 target 转速 */

volatile float SpeedRate_ServoPitch_cmd=0.0f;
volatile float SpeedRate_ServoYaw_cmd=0.0f;

float MotorA_current_speed;//现在转速
float MotorB_current_speed;
float MotorC_current_speed;
float MotorD_current_speed;

volatile uint8_t Calculate_Target=0;//二分频标记位

volatile bool BLDC_Enable_cmd=0;//BLDC_使能

volatile uint8_t estop_active = 0;    /* 1=急停中 */


volatile float temp_speed_rate=0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
void Serialplot_Call_Back(uint8_t *Buffer, uint16_t Length)
{

}
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
 * @brief  The application entry point.
 * @retval int
 */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */
  OLED_Init0();
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_TIM1_Init();
  MX_TIM2_Init();
  MX_TIM3_Init();
  MX_TIM4_Init();
  MX_TIM5_Init();
  MX_TIM9_Init();
  MX_TIM10_Init();
  MX_TIM11_Init();
  MX_USART3_UART_Init();
  MX_ADC1_Init();
  MX_TIM13_Init();
  MX_USART1_UART_Init();
  MX_TIM8_Init();
  MX_TIM6_Init();
  MX_TIM12_Init();
  /* USER CODE BEGIN 2 */
  Uart_Init(&huart1, UART1_Rx_Buffer, UART1_RX_SIZE, Serialplot_Call_Back);

  Motor_A.Init(MotorA);
  Motor_B.Init(MotorB);
  Motor_C.Init(MotorC);
  Motor_D.Init(MotorD);

  HAL_TIM_Base_Start_IT(&htim13);//PID中断100hz
  HAL_TIM_Base_Start_IT(&htim6);//摩擦轮计算中断5khz

  HAL_TIM_PWM_Start(&htim8, TIM_CHANNEL_1);//摩擦轮三相pwm定时器
  HAL_TIM_PWM_Start(&htim8, TIM_CHANNEL_2);
  HAL_TIM_PWM_Start(&htim8, TIM_CHANNEL_3);
                 
  PID_MotorA.Init(Kp, Ki, Kd, Kf, 100.0f,      100.0f, 0.01f, 0.0f);//要考虑前馈
  PID_MotorB.Init(Kp, Ki, Kd, Kf, 100.0f,      100.0f, 0.01f, 0.0f);
  PID_MotorC.Init(Kp, Ki, Kd, Kf, 100.0f,      100.0f, 0.01f, 0.0f);
  PID_MotorD.Init(Kp, Ki, Kd, Kf, 100.0f,      100.0f, 0.01f, 0.0f);

  Servo_Pitch.init(ServoPitch);
  Servo_Yaw.init(ServoYaw);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    float vol = (float)Get_Adc() / 4095.0f * 3.3f * 11.0f;//电池电压
    OLED_ShowFloat(0, 1, Kp, 1, 2);
    OLED_ShowFloat(0, 11, Ki, 1, 2);
    OLED_ShowFloat(0, 21, Kd, 1, 2);
    OLED_ShowFloat(0, 31, vol, 2, 2);
    OLED_ShowString(45, 31, "V");
    OLED_Refresh_Gram();
    HAL_Delay(1000);

    PID_MotorA.Set_K_P(Kp); PID_MotorA.Set_K_I(Ki); PID_MotorA.Set_K_D(Kd);
    PID_MotorB.Set_K_P(Kp); PID_MotorB.Set_K_I(Ki); PID_MotorB.Set_K_D(Kd);
    PID_MotorC.Set_K_P(Kp); PID_MotorC.Set_K_I(Ki); PID_MotorC.Set_K_D(Kd);
    PID_MotorD.Set_K_P(Kp); PID_MotorD.Set_K_I(Ki); PID_MotorD.Set_K_D(Kd);

  }
  /* USER CODE END 3 */
}

/**
 * @brief System Clock Configuration
 * @retval None
 */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
   */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
   * in the RCC_OscInitTypeDef structure.
   */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 8;
  RCC_OscInitStruct.PLL.PLLN = 168;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
   */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

// void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
//{
//     if (huart->Instance == USART1)
//     {
//         ProcessData(rx_buf, Size);

//        HAL_UARTEx_ReceiveToIdle_DMA(&huart1, rx_buf, sizeof(rx_buf));
//        __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, DMA_IT_HT);
//    }
//}
static inline int cross_zero(float now, float last, float zero_band)
{
    if (fabsf(now) < zero_band && fabsf(last) < zero_band) {
        return 0;                      /* 都在零带内，不算过零 */
    }
    return ((now > 0.0f && last < 0.0f) ||
            (now < 0.0f && last > 0.0f)) ? 1 : 0;
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  if (htim->Instance == TIM6)
  {
    BLDC_SetVelocityOL(70.0f, 1.0f, 0.0002f);//q轴电压要确定
  }
  if (htim->Instance == TIM13)
  {
    if (estop_active)
    {
        Motor_A.Set_Speed(0);
        Motor_B.Set_Speed(0);
        Motor_C.Set_Speed(0);
        Motor_D.Set_Speed(0);
        return;   /* 不跑 IK、不跑 PID */
    }
    float vx_f=0.0f, om_f=0.0f;
    Calculate_Target++;
    if(Calculate_Target==2)//二分频，ik50hz pid100hz
    {
      Calculate_Target=0;
      
      using namespace diff_drive;
      smoother.smooth(vx_cmd, om_cmd, vx_f, om_f);//平滑//这个滤波有问题

      out = ik.solve(vx_cmd, om_cmd);//解算

      const float ZERO_BAND = 0.2f;   /* rad/s */
      if (cross_zero(out.phi_dot_L, phiL_last, ZERO_BAND)) {
        PID_MotorA.Set_Integral_Error(0.0f);
        PID_MotorB.Set_Integral_Error(0.0f);
      }
      if (cross_zero(out.phi_dot_R, phiR_last, ZERO_BAND)) {
          PID_MotorC.Set_Integral_Error(0.0f);
          PID_MotorD.Set_Integral_Error(0.0f);
      }

      phiL_last = out.phi_dot_L;
      phiR_last = out.phi_dot_R;

      PID_MotorA.Set_Target(out.phi_dot_L);
      PID_MotorB.Set_Target(out.phi_dot_L);
      PID_MotorC.Set_Target(out.phi_dot_R);
      PID_MotorD.Set_Target(out.phi_dot_R);
    }
      MotorA_current_speed = EncoderOutput_to_Fai(Encoder_MotorA);
      MotorB_current_speed = EncoderOutput_to_Fai(Encoder_MotorB);
      MotorC_current_speed = -EncoderOutput_to_Fai(Encoder_MotorC);
      MotorD_current_speed = -EncoderOutput_to_Fai(Encoder_MotorD);

    PID_MotorA.Set_Now(MotorA_current_speed);
    PID_MotorB.Set_Now(MotorB_current_speed);
    PID_MotorC.Set_Now(MotorC_current_speed);
    PID_MotorD.Set_Now(MotorD_current_speed);
    
    PID_MotorA.TIM_Adjust_PeriodElapsedCallback();
    PID_MotorB.TIM_Adjust_PeriodElapsedCallback();
    PID_MotorC.TIM_Adjust_PeriodElapsedCallback();
    PID_MotorD.TIM_Adjust_PeriodElapsedCallback();
    
    Motor_A.Set_Speed(PID_MotorA.Get_Out());
    Motor_B.Set_Speed(PID_MotorB.Get_Out());
    Motor_C.Set_Speed(PID_MotorC.Get_Out());
    Motor_D.Set_Speed(PID_MotorD.Get_Out());
    // UART1_Tx_Data[0] = 0xAB;
    // memcpy(&UART1_Tx_Data[1], &Target_SpeedRate, 4);
    // memcpy(&UART1_Tx_Data[5], &Now, 4);
    // UART_Send_Data(&huart1, UART1_Tx_Data, 9);

    Servo_Pitch.set_speed(SpeedRate_ServoPitch_cmd);
    Servo_Yaw.set_speed(SpeedRate_ServoYaw_cmd);

    BLDC_Send_En(BLDC_Enable_cmd);//摩擦轮状态更新

  }
}
float Parse_Cmd_Float(const uint8_t *buffer, uint16_t len)
{
  if (buffer == NULL || len < 2)
    return 0.0f;

  /* 找到�?一�?数字、小数点或负号的位置（跳过指令字母及�?能的分隔符） */
  uint16_t start = 0;
  while (start < len)
  {
    uint8_t c = buffer[start];
    if ((c >= '0' && c <= '9') || c == '.' || c == '-' || c == '+')
      break;
    start++;
  }

  if (start >= len)
    return 0.0f; /* 没有找到数字部分 */

  /* �?定数字结束位�?：遇到非数字、非小数点、非正负号、非科�?��?�数法字符时停�?? */
  uint16_t end = start;
  while (end < len)
  {
    uint8_t c = buffer[end];
    if ((c >= '0' && c <= '9') || c == '.' || c == '-' || c == '+' ||
        c == 'e' || c == 'E')
      end++;
    else
      break;
  }

  /* 拷贝到临时缓冲区并转�?为浮点数（atoi/atof 需要以 '\0' 结尾�? */
  char tmp[32];
  uint16_t num_len = end - start;
  if (num_len == 0 || num_len >= sizeof(tmp))
    return 0.0f;

  memcpy(tmp, &buffer[start], num_len);
  tmp[num_len] = '\0';

  return (float)atof(tmp);
}
/* 触发急停：可在 EXTI 回调、串口回调里调 */
void EStop_Trigger(void)
{
    estop_active  = 1;
}

/* 解除急停：清状态，标记软起步 */
void EStop_Release(void)
{
    if (!estop_active) return;
    estop_active  = 0;

    /* 清 PID 内部积分/微分历史 */
    PID_MotorA.Reset();
    PID_MotorB.Reset();
    PID_MotorC.Reset();
    PID_MotorD.Reset();

    /* 清指令，避免恢复瞬间跳变 */
    vx_cmd = 0.0f;
    om_cmd = 0.0f;

    /* 重置平滑器，恢复后从当前指令重新平滑 */
    smoother.reset();
}
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == GPIO_PIN_3) 
    {
        if (HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_3) == GPIO_PIN_RESET) 
        {
			HAL_GPIO_WritePin(GPIOE,GPIO_PIN_8,GPIO_PIN_SET);
            EStop_Trigger();
        }
        else if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_3) == GPIO_PIN_SET)
        {
			HAL_GPIO_WritePin(GPIOE,GPIO_PIN_8,GPIO_PIN_RESET);
            EStop_Release();
        }
    }
}
/* USER CODE END 4 */

/**
 * @brief  This function is executed in case of error occurrence.
 * @retval None
 */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
 * @brief  Reports the name of the source file and the source line number
 *         where the assert_param error has occurred.
 * @param  file: pointer to the source file name
 * @param  line: assert_param error line source number
 * @retval None
 */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
