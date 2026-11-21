#include "Motor.h"
#include "main.h"
Rotate_Direction dir=DIR_Unknown;
void Motor_Set_Speed(Motor_ID Motor_id, float Speed_Rate)
{
    if (Speed_Rate > 0.0f) {
        dir = DIR_CounterClockWise;
    } else {
        dir = DIR_ClockWise;
        Speed_Rate = -Speed_Rate;
    }
	if (Speed_Rate < 0.0f)   Speed_Rate = 0.0f;
    if (Speed_Rate > 100.0f) Speed_Rate = 100.0f;
	uint16_t CCR_TargetValue = 16799- (uint16_t)(Speed_Rate * 16799.0f / 100.0f + 0.5f);

	switch (Motor_id)
    {
        case MotorA:
            if(dir==DIR_ClockWise)
			{
                __HAL_TIM_SET_COMPARE(&htim10, TIM_CHANNEL_1, ArrPlusOne - 1);
                __HAL_TIM_SET_COMPARE(&htim11, TIM_CHANNEL_1, CCR_TargetValue);
                
			}
			else if(dir==DIR_CounterClockWise)
			{

                __HAL_TIM_SET_COMPARE(&htim11, TIM_CHANNEL_1, ArrPlusOne - 1);
                __HAL_TIM_SET_COMPARE(&htim10, TIM_CHANNEL_1, CCR_TargetValue);
			}
            break;
            
        case MotorB:
            if(dir==DIR_ClockWise)
			{
				TIM11->CCR1=CCR_TargetValue;
				TIM10->CCR1=ArrPlusOne-1;
			}
			else if(dir==DIR_CounterClockWise)
			{
				TIM10->CCR1=CCR_TargetValue;
				TIM11->CCR1=ArrPlusOne-1;
			}
            break;
            
        case MotorC:
            if(dir==DIR_ClockWise)
			{
				TIM11->CCR1=CCR_TargetValue;
				TIM10->CCR1=ArrPlusOne-1;
			}
			else if(dir==DIR_CounterClockWise)
			{
				TIM10->CCR1=CCR_TargetValue;
				TIM11->CCR1=ArrPlusOne-1;
			}
            break;
            
        case MotorD:
            if(dir==DIR_ClockWise)
			{
				TIM11->CCR1=CCR_TargetValue;
				TIM10->CCR1=ArrPlusOne-1;
			}
			else if(dir==DIR_CounterClockWise)
			{
				TIM10->CCR1=CCR_TargetValue;
				TIM11->CCR1=ArrPlusOne-1;
			}
            break;
            
        default:
            break;
    }
}

void Motor_Init(Motor_ID Motor_id)
{
    switch (Motor_id)
    {
    case MotorA:
        HAL_TIM_PWM_Start(&htim10, TIM_CHANNEL_1);
        HAL_TIM_PWM_Start(&htim11, TIM_CHANNEL_1);
        HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);
    break;

    case MotorB:
        HAL_TIM_PWM_Start(&htim9, TIM_CHANNEL_1);
        HAL_TIM_PWM_Start(&htim9, TIM_CHANNEL_2);
        HAL_TIM_Encoder_Start(&htim3, TIM_CHANNEL_ALL);
    break;

    case MotorC:
        HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
        HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);
        HAL_TIM_Encoder_Start(&htim4, TIM_CHANNEL_ALL);
    break;

    case MotorD:
        HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_3);
        HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_4);
        HAL_TIM_Encoder_Start(&htim5, TIM_CHANNEL_ALL);
    break;
    
    default:
        break;
    }
}