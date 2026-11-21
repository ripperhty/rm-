#ifndef __MOTOR_CPP_H
#define __MOTOR_CPP_H

#include "main.h"
#include "tim.h"
#define ArrPlusOne 16800
typedef enum {
	MotorA=0,
	MotorB,
	MotorC,
	MotorD
} Motor_ID;

typedef enum {
    DIR_ClockWise = 0,         //cw -
    DIR_CounterClockWise = 1   //ccw +
} Rotate_Direction;

class Motor
{
public:
    void Init(Motor_ID __id);
    void Set_Speed(float Speed_Rate);

protected:
    Motor_ID id;
    float Speed_Rate;
    Rotate_Direction dir;
};


#endif
