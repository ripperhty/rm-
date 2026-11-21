#include "Encoder.h"

int16_t Encoder_Get_Out(Motor_Encoder_ID Motor_Encoder)
{
 int16_t Encoder_TIM;   
 switch(Motor_Encoder)
 {
	case Encoder_MotorA:  Encoder_TIM= TIM2 -> CNT;   TIM2 -> CNT=0;  break;
	case Encoder_MotorB:  Encoder_TIM= TIM3 -> CNT;   TIM3 -> CNT=0;  break;
	case Encoder_MotorC:  Encoder_TIM= TIM4 -> CNT;   TIM4 -> CNT=0;  break;	
	case Encoder_MotorD:  Encoder_TIM= TIM5 -> CNT;   TIM5 -> CNT=0;  break;	
	default: Encoder_TIM=0;
 }
	return Encoder_TIM;
}

float EncoderOutput_to_Fai(Motor_Encoder_ID Motor_Encoder)
{
	int16_t Output=Encoder_Get_Out(Motor_Encoder);

	if (Output >  Encoder_Max) Output =  Encoder_Max;
    if (Output < -Encoder_Max) Output = -Encoder_Max;
	float Fai = Output / Encoder_Max * 28.462f *PI;
    return Fai;

}
