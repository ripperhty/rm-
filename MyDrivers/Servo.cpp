#include "Servo.h"

void Servo::set_speed(float __speed_rate)
{
    if(estop_active)
    {
        TIM12->CCR2=ccr_stop;
        TIM12->CCR1=ccr_stop;
        return;
    }
    speed_rate=__speed_rate;
    ccr_value=SpeedRate_To_CCR(speed_rate);
    switch (id)
    {
    case ServoPitch:
        TIM12->CCR2=ccr_value;
        break;
    case ServoYaw:
        TIM12->CCR1=ccr_value;
        break;
    default:
        break;
    }
}

void Servo::set_rate_dead(float __rate_dead)
{
    rate_dead = __rate_dead;
}

void Servo::init(Servo_ID __id,
	float __rate_dead,   //速度死区
	float __rate_max,
	float __ccr_stop,//停机
    float __ccr_fwd,//正向死区界
    float __ccr_rev,//反向死区界
    float __ccr_max,
    float __ccr_min)
{
    id=__id;
    speed_rate=0.0f;
    ccr_value=(uint16_t)ccr_stop;

    rate_dead=__rate_dead;
    rate_max=__rate_max;
    ccr_stop=__ccr_stop;
    ccr_fwd=__ccr_fwd;
    ccr_rev=__ccr_rev;
    ccr_max=__ccr_max;
    ccr_min=__ccr_min;
    switch (id)
		{
		case ServoPitch: // b15
			HAL_TIM_PWM_Start(&htim12, TIM_CHANNEL_2);
			break;

		case ServoYaw: // b14
			HAL_TIM_PWM_Start(&htim12, TIM_CHANNEL_1);
			break;

			// case ServoSpin:

			// break;

		default:

			break;
		}
}

uint16_t Servo::SpeedRate_To_CCR(float speed_rate)
{
    float mag, ccr;

    if (speed_rate != speed_rate) return (uint16_t)ccr_stop;   /* NaN 保护 */

    /* 1. 输入限幅 */
    if (speed_rate >  rate_max) speed_rate =  rate_max;
    if (speed_rate < -rate_max) speed_rate = -rate_max;

    /* 2. speed_rate 自身死区：太小直接停 */
    mag = (speed_rate >= 0.0f) ? speed_rate : -speed_rate;
    if (mag <= rate_dead) return (uint16_t)ccr_stop;

    /* 3. 归一化到 0~1，再映射到死区边界之外 */
    mag = (mag - rate_dead) / (rate_max - rate_dead);

    if (speed_rate > 0.0f)
        ccr = ccr_fwd + mag * (ccr_max - ccr_fwd);   /* 1600 → 2000 */
    else
        ccr = ccr_rev - mag * (ccr_rev - ccr_min);   /* 1400 → 1000 */

    if (ccr < ccr_min) ccr = ccr_min;
    if (ccr > ccr_max) ccr = ccr_max;
    /* 4. 四舍五入 */
    return (uint16_t)(ccr + 0.5f);
}

