#ifndef __SERVO_H
#define __SERVO_H

#include "main.h"
#include "tim.h"
#include "drv_math.h"

extern volatile uint8_t estop_active;

typedef enum
{
	ServoPitch = 0,
	ServoYaw,
	ServoSpin, // 不一定
} Servo_ID;

class Servo
{
public:
	void set_speed(float __speed_rate);
	void set_rate_dead(float __rate_dead);
	void init(Servo_ID __id,
	float __rate_dead = 0.0f,   //速度死区
	float __rate_max  = 100.0f,
	float __ccr_stop  = 1500.0f,//停机
    float __ccr_fwd   = 1600.0f,//正向死区界
    float __ccr_rev   = 1400.0f,//反向死区界
    float __ccr_max   = 2000.0f,
    float __ccr_min   = 1000.0f);

private:
	Servo_ID id;
	float speed_rate;
	uint16_t ccr_value;
	int16_t current_angle;
	int16_t target_angle;
	uint16_t SpeedRate_To_CCR(float speed_rate);//不一定线性映射，要确定

	float rate_dead; /* speed_rate 自身死区，先不设置 */
	float rate_max;  /* 输入量程 */
    float ccr_stop;
    float ccr_fwd; /* 正向死区边界 */
    float ccr_rev; /* 反向死区边界 */
    float ccr_max;
    float ccr_min;
};

#endif
