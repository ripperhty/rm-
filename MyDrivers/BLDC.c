
#include "stm32f4xx_hal.h"
#include "math.h"

#define VDC 12.0f    // 直流母线电压
#define POLE_PAIRS 7 // 电机极对数
#define PI 3.1415926f
#define TWO_PI 6.2831853f

#define PWM_ARR 8400.0f // 必须与 TIM8 的 ARR 一致

extern TIM_HandleTypeDef htim8;

static float e_angle = 0.0f;

// 限幅：限制在 min ~ max
static float constrain(float x, float min, float max)
{
    if (x > max)
        return max;
    if (x < min)
        return min;
    return x;
}

// 三相电压转 PWM
void BLDC_SetPhaseVoltage(float Ua, float Ub, float Uc)
{
    // 限制相电压，避免调制过度
    Ua = constrain(Ua, -VDC / 2.0f, VDC / 2.0f);
    Ub = constrain(Ub, -VDC / 2.0f, VDC / 2.0f);
    Uc = constrain(Uc, -VDC / 2.0f, VDC / 2.0f);

    // 电压映射到占空比
    uint16_t duty_a = (uint16_t)((0.5f + Ua / VDC) * PWM_ARR);
    uint16_t duty_b = (uint16_t)((0.5f + Ub / VDC) * PWM_ARR);
    uint16_t duty_c = (uint16_t)((0.5f + Uc / VDC) * PWM_ARR);

    // __HAL_TIM_SET_COMPARE(&htim8, TIM_CHANNEL_1, duty_a);
    // __HAL_TIM_SET_COMPARE(&htim8, TIM_CHANNEL_2, duty_b);
    // __HAL_TIM_SET_COMPARE(&htim8, TIM_CHANNEL_3, duty_c);
    TIM8->CCR1 = duty_a;
    TIM8->CCR2 = duty_b;
    TIM8->CCR3 = duty_c;
}

// 根据 Uq、Ud、电角度计算三相电压
void BLDC_SetRightangledVoltage(float Uq, float Ud, float angle)
{
    float Ua, Ub, Uc;

    Ua = cosf(angle) * Ud - sinf(angle) * Uq;

    Ub = cosf(angle - TWO_PI / 3.0f) * Ud - sinf(angle - TWO_PI / 3.0f) * Uq;

    Uc = cosf(angle + TWO_PI / 3.0f) * Ud - sinf(angle + TWO_PI / 3.0f) * Uq;

    BLDC_SetPhaseVoltage(Ua, Ub, Uc);
}

// 开环速度控制
// m_veloc：电角速度 rad/s
// intensity：q轴电压 V
// dt：本次调用与上次调用的时间间隔 s
void BLDC_SetVelocityOL(float m_veloc, float intensity, float dt)
{
    e_angle += m_veloc * dt;

    // 将电角度限制在 0 ~ 2π
    e_angle = fmodf(e_angle, TWO_PI);

    BLDC_SetRightangledVoltage(intensity, 0.0f, e_angle);
}

void BLDC_Send_En(bool flag)//这个给驱动板的en发信号用的，计算是一直计算，通过en来控制是否使能，未经验证
{
    if (flag)
    {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_2, GPIO_PIN_SET);
    }
    else{
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_2, GPIO_PIN_RESET);
    }
}
