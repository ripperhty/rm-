# -*- coding: utf-8 -*-
"""生成中期报告插图：系统总体框图、控制数据流图。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
os.makedirs(ASSETS, exist_ok=True)

CJK = "C:/Windows/Fonts/msyh.ttc"
CJK_BD = "C:/Windows/Fonts/msyhbd.ttc"

INK = "#1f2328"
GREY = "#5b6572"
ARROW = "#4a5563"


def font(size, bold=False):
    path = CJK_BD if bold and os.path.exists(CJK_BD) else CJK
    return ImageFont.truetype(path, size)


def box(d, xy, fill, outline, radius=16, width=3):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(d, xy, s, f, fill=INK, anchor="mm", align="center", spacing=10):
    d.multiline_text(xy, s, font=f, fill=fill, anchor=anchor,
                     align=align, spacing=spacing)


def arrow(d, start, end, width=3, color=ARROW, head=14):
    import math
    d.line([start, end], fill=color, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    p1 = (end[0] - head * math.cos(ang - math.pi / 7),
          end[1] - head * math.sin(ang - math.pi / 7))
    p2 = (end[0] - head * math.cos(ang + math.pi / 7),
          end[1] - head * math.sin(ang + math.pi / 7))
    d.polygon([end, p1, p2], fill=color)


def poly_arrow(d, points, width=3, color=ARROW):
    """折线箭头，最后一个点为箭头端。"""
    d.line(points, fill=color, width=width, joint="curve")
    arrow(d, points[-2], points[-1], width=width, color=color)


# ---------------------------------------------------------------- 图 1 总体框图
def figure_system():
    W, H = 1600, 980
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    f_box = font(26, True)
    f_sub = font(21)
    f_mcu = font(34, True)
    f_line = font(23)

    # 中央主控
    mcu = (555, 120, 1075, 920)
    box(d, mcu, "#eaf1fd", "#3b6fc4", radius=22, width=4)
    text(d, (815, 190), "STM32F407VET6", f_mcu, "#1d3f75")
    text(d, (815, 240), "Cortex-M4F  168 MHz", f_sub, GREY)
    d.line([(605, 280), (1025, 280)], fill="#9db8e3", width=2)
    lines = [
        "TIM1 / TIM9 / TIM10 / TIM11",
        "四路双 PWM 调速 · 10 kHz",
        "",
        "TIM2 / TIM3 / TIM4 / TIM5",
        "四路正交编码器接口",
        "",
        "TIM8  三相 PWM · 10 kHz",
        "TIM6  5 kHz 中断",
        "TIM12 50 Hz · TIM13 100 Hz",
        "",
        "ADC1 · USART1/3 · GPIO/EXTI",
    ]
    y = 320
    for s in lines:
        if s:
            text(d, (815, y), s, f_line, INK)
        y += 50

    # 左侧：输入与人机交互
    left = [
        (95, 90, 435, 215, "#fff4e3", "#d08a2e", "上位机 / 遥控器", "速度指令 vx、ω"),
        (95, 285, 435, 400, "#fdeaea", "#c04545", "急停按钮", "PD3 · EXTI3 双边沿"),
        (95, 470, 435, 585, "#eef0f4", "#6b7686", "调试串口", "USART3 · 115200"),
        (95, 655, 435, 790, "#fff4e3", "#d08a2e", "12 V 电池", "1/11 分压 → PB0(ADC)"),
    ]
    for x0, y0, x1, y1, fill, oc, t1, t2 in left:
        box(d, (x0, y0, x1, y1), fill, oc)
        text(d, ((x0 + x1) / 2, y0 + 42), t1, f_box)
        text(d, ((x0 + x1) / 2, y1 - 38), t2, f_sub, GREY)
    for cy in (152, 342, 527, 722):
        arrow(d, (438, cy), (550, cy), width=3)

    # 右侧：执行机构与显示
    right = [
        (1165, 55, 1515, 205, "#e9f7ef", "#2e8b57", "4× 直流减速电机", "双 PWM + 正交编码器", "TIM1/9/10/11 + TIM2~5"),
        (1165, 235, 1515, 385, "#e9f7ef", "#2e8b57", "摩擦轮无刷电机", "三相 PWM · PA2 使能", "TIM8 · 5 kHz 更新"),
        (1165, 415, 1515, 565, "#e9f7ef", "#2e8b57", "云台舵机 ×2", "Pitch / Yaw · 50 Hz", "TIM12_CH1 / CH2"),
        (1165, 600, 1515, 720, "#eef0f4", "#6b7686", "OLED 128×64", "软件 I2C · PD11~PD14"),
        (1165, 750, 1515, 870, "#eef0f4", "#6b7686", "LED 状态指示", "PE8"),
    ]
    for item in right:
        x0, y0, x1, y1, fill, oc, t1, t2 = item[:8]
        box(d, (x0, y0, x1, y1), fill, oc)
        cx = (x0 + x1) / 2
        if len(item) == 9:
            text(d, (cx, y0 + 45), t1, f_box)
            text(d, (cx, y0 + 95), t2, f_sub, GREY)
            text(d, (cx, y0 + 135), item[8], font(19), GREY)
        else:
            text(d, (cx, y0 + 42), t1, f_box)
            text(d, (cx, y0 + 88), t2, f_sub, GREY)
    for cy in (130, 310, 490, 660, 810):
        arrow(d, (1080, cy), (1160, cy), width=3)

    out = os.path.join(ASSETS, "fig_system.png")
    img.save(out, dpi=(160, 160))
    print("saved", out)


# ------------------------------------------------------------ 图 2 控制数据流
def figure_control():
    W, H = 1600, 780
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    f_box = font(24, True)
    f_sub = font(19)
    f_lane = font(21, True)

    # 车道标题
    text(d, (40, 38), "底盘速度环：逆解 50 Hz / PID 100 Hz", f_lane, "#1d3f75", anchor="lm")
    text(d, (40, 400), "摩擦轮开环：TIM6 中断 5 kHz", f_lane, "#1d3f75", anchor="lm")

    lane1 = [
        (40, 100, 220, 230, "指令输入", "vx、ω"),
        (270, 100, 450, 230, "一阶低通", "τ = 50 ms"),
        (500, 100, 760, 230, "差速逆解", "归一化限幅"),
        (810, 100, 980, 230, "左右轮目标", "角速度"),
        (1030, 100, 1200, 230, "PID ×4", "100 Hz"),
        (1250, 100, 1410, 230, "双 PWM", "10 kHz"),
        (1460, 100, 1580, 230, "电机", ""),
    ]
    for x0, y0, x1, y1, t1, t2 in lane1:
        box(d, (x0, y0, x1, y1), "#eaf1fd", "#3b6fc4", radius=12, width=3)
        if t2:
            text(d, ((x0 + x1) / 2, y0 + 45), t1, f_box)
            text(d, ((x0 + x1) / 2, y1 - 40), t2, f_sub, GREY)
        else:
            text(d, ((x0 + x1) / 2, (y0 + y1) / 2), t1, f_box)
    for i in range(len(lane1) - 1):
        arrow(d, (lane1[i][2] + 4, 165), (lane1[i + 1][0] - 6, 165), width=3)

    # 反馈：电机 -> 编码器 -> PID
    poly_arrow(d, [(1580, 240), (1580, 320), (1115, 320), (1115, 240)], width=3)
    text(d, (1300, 348), "编码器测速反馈（每 10 ms 采样）", font(20), GREY)

    # 车道 2
    lane2 = [
        (40, 455, 250, 590, "TIM6 中断", "5 kHz"),
        (300, 455, 530, 590, "电角度积分", "θ += 70·Δt"),
        (580, 455, 830, 590, "Ud / Uq 变换", "三相正弦电压"),
        (880, 455, 1110, 590, "占空比映射", "TIM8 · 10 kHz"),
        (1160, 455, 1360, 590, "无刷电机", ""),
        (1410, 455, 1580, 590, "使能 / 急停", "PA2"),
    ]
    for x0, y0, x1, y1, t1, t2 in lane2:
        box(d, (x0, y0, x1, y1), "#e9f7ef", "#2e8b57", radius=12, width=3)
        if t2:
            text(d, ((x0 + x1) / 2, y0 + 48), t1, f_box)
            text(d, ((x0 + x1) / 2, y1 - 42), t2, f_sub, GREY)
        else:
            text(d, ((x0 + x1) / 2, (y0 + y1) / 2), t1, f_box)
    for i in range(len(lane2) - 1):
        arrow(d, (lane2[i][2] + 4, 522), (lane2[i + 1][0] - 6, 522), width=3)

    text(d, (40, 700), "云台：TIM12 50 Hz PWM → 舵机 Pitch / Yaw（速度指令映射为 1000~2000 μs 脉宽）",
         font(20), GREY, anchor="lm")

    out = os.path.join(ASSETS, "fig_control.png")
    img.save(out, dpi=(160, 160))
    print("saved", out)


if __name__ == "__main__":
    figure_system()
    figure_control()
