# -*- coding: utf-8 -*-
"""供电拓扑图（双电池方案）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
CJK = "C:/Windows/Fonts/msyh.ttc"
CJK_BD = "C:/Windows/Fonts/msyhbd.ttc"
INK = "#1f2328"
GREY = "#5b6572"


def font(size, bold=False):
    return ImageFont.truetype(CJK_BD if bold else CJK, size)


def box(d, xy, fill, outline, title, subs, title_font, sub_font, radius=16):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=3)
    x0, y0, x1, y1 = xy
    cx = (x0 + x1) / 2
    d.multiline_text((cx, y0 + 40), title, font=title_font, fill=INK,
                     anchor="mm", align="center")
    y = y0 + 92
    for s in subs:
        d.multiline_text((cx, y), s, font=sub_font, fill=GREY,
                         anchor="mm", align="center")
        y += 38


def arrow(d, pts, label=None, label_pos=None, color="#4a5563", width=4):
    import math
    d.line(pts, fill=color, width=width, joint="curve")
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    head = 16
    p1 = (x2 - head * math.cos(ang - math.pi / 7), y2 - head * math.sin(ang - math.pi / 7))
    p2 = (x2 - head * math.cos(ang + math.pi / 7), y2 - head * math.sin(ang + math.pi / 7))
    d.polygon([(x2, y2), p1, p2], fill=color)
    if label:
        lx, ly = label_pos
        d.text((lx, ly), label, font=font(19), fill=GREY, anchor="mm")


img = Image.new("RGB", (1600, 900), "white")
d = ImageDraw.Draw(img)
ft = font(26, True)
fs = font(20)

box(d, (60, 70, 360, 230), "#fff4e3", "#d08a2e", "电池 A",
    ["E326S 3S 2550 mAh", "C30D 专用"], ft, fs)
box(d, (500, 60, 920, 250), "#eaf1fd", "#3b6fc4", "C30D 主控板",
    ["STM32F407VET6", "4 路电机 + 6 路舵机"], ft, fs)
box(d, (1080, 60, 1500, 250), "#e9f7ef", "#2e8b57", "4× MG310 底盘电机",
    ["双 PWM 调速 + 编码器", "走板载电机通道"], ft, fs)

box(d, (500, 320, 920, 480), "#eef0f4", "#6b7686", "2× 5V 5A BEC",
    ["外置舵机电源"], ft, fs)
box(d, (1080, 320, 1500, 480), "#e9f7ef", "#2e8b57", "云台舵机 ×2 + 拨弹舵机",
    ["5 V 供电，C30D 只出信号"], ft, fs)

box(d, (60, 560, 360, 720), "#fff4e3", "#d08a2e", "电池 B",
    ["3S 2200–3300 mAh", "≥20 A 瞬时"], ft, fs)
box(d, (500, 560, 920, 720), "#eef0f4", "#6b7686", "双路无刷驱动板",
    ["1 路 PWM → 三相"], ft, fs)
box(d, (1080, 560, 1500, 720), "#e9f7ef", "#2e8b57", "2× C2208 摩擦轮电机",
    ["12 V 独立供电"], ft, fs)

arrow(d, [(365, 150), (495, 150)], "12 V", (430, 128))
arrow(d, [(925, 150), (1075, 150)], "功率 + PWM", (1000, 128))
arrow(d, [(365, 640), (495, 640)], "12 V", (430, 618))
arrow(d, [(925, 640), (1075, 640)], "三相", (1000, 618))
arrow(d, [(210, 550), (210, 400), (495, 400)], "12 V", (300, 378))
arrow(d, [(925, 400), (1075, 400)], "5 V", (1000, 378))

d.text((800, 800),
       "电池 A、B 共地、正极不并联；每包独立保险。摩擦轮与舵机不占用 C30D 板载供电轨。",
       font=font(21), fill=GREY, anchor="mm")

out = os.path.join(ASSETS, "fig_power.png")
img.save(out, dpi=(160, 160))
print("saved", out)
