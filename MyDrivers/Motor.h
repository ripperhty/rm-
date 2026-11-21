#ifndef __MOTOR_H
#define __MOTOR_H

typedef enum {
	MotorA=0,
	MotorB,
	MotorC,
	MotorD
} Motor_ID;

typedef enum {
    DIR_ClockWise = 0,         //cw -
    DIR_CounterClockWise = 1,   //ccw +
	DIR_Unknown = 2
} Rotate_Direction;

#define ArrPlusOne 16800

#include "main.h"
#include "tim.h"

void Motor_Init(Motor_ID Motor_id);
void Motor_Set_Speed(Motor_ID Motor_id, float Speed_Rate);

#endif