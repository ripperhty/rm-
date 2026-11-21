#include "bsp_adc.h"

// CubeMX 会自动在 adc.c 中生成 ADC_HandleTypeDef hadc1;
extern ADC_HandleTypeDef hadc1;

uint16_t Get_Adc(void)
{
    uint16_t adc_value = 0;

    // 1. 启动 ADC 转换
    HAL_ADC_Start(&hadc1);

    // 2. 等待转换完成，超时时间设为 10ms
    if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK)
    {
        // 3. 读取转换结果
        adc_value = (uint16_t)HAL_ADC_GetValue(&hadc1);
    }

    // 4. 停止转换（单次采样模式下建议停止，降低功耗）
    HAL_ADC_Stop(&hadc1);

    return adc_value;
}