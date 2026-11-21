#ifndef __ENCODER_H
#define __ENCODER_H

#include "main.h" 

#define Encoder_Max 140.0f
#define PI    3.14159265f

typedef enum{
	Encoder_MotorA=0,
	Encoder_MotorB,
	Encoder_MotorC,
	Encoder_MotorD
}Motor_Encoder_ID;

int16_t Encoder_Get_Out(Motor_Encoder_ID Motor_Encoder);
float EncoderOutput_to_Fai(Motor_Encoder_ID Motor_Encoder);

#endif
