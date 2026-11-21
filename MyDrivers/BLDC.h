#ifndef __BLDC_H__
#define __BLDC_H__

void BLDC_SetPhaseVoltage(float Ua, float Ub, float Uc);
void BLDC_SetRightangledVoltage(float Uq, float Ud, float e_angle);
void BLDC_SetVelocityOL(float m_veloc, float intensity, float dt);
void BLDC_Send_En(bool flag);

#endif
