# -*- coding: utf-8 -*-
"""生成《四轮差速底盘与摩擦轮发射机构控制系统》中期报告 DOCX。"""
import json
import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
OUT = os.path.join(os.path.dirname(BASE), "中期报告_四轮差速底盘与摩擦轮控制系统.docx")

SONG = "宋体"
HEI = "黑体"
TNR = "Times New Roman"
CONSOLAS = "Consolas"

BODY_PT = 12          # 小四
TABLE_PT = 10.5       # 五号
TEXT_WIDTH = Cm(15.0)


# ----------------------------------------------------------------- 基础工具
def set_run_font(run, ea=SONG, ascii_=TNR, size=BODY_PT, bold=False,
                 color=None, italic=False):
    run.font.name = ascii_
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), ea)
    rfonts.set(qn("w:ascii"), ascii_)
    rfonts.set(qn("w:hAnsi"), ascii_)


def shade(element, fill):
    """为段落或单元格添加底色。"""
    pr = element.get_or_add_pPr() if hasattr(element, "get_or_add_pPr") else element
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def para(text="", indent=True, size=BODY_PT, align=None, space_before=0,
         space_after=0, line=1.5, bold=False, ea=SONG):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(BODY_PT * 2) if indent else Pt(0)
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        set_run_font(r, ea=ea, size=size, bold=bold)
    return p


def heading(text, level):
    p = doc.add_heading(level=level)
    p.paragraph_format.first_line_indent = Pt(0)
    r = p.add_run(text)
    if level == 1:
        set_run_font(r, ea=HEI, ascii_=HEI, size=16, bold=False)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(10)
    elif level == 2:
        set_run_font(r, ea=HEI, ascii_=HEI, size=14, bold=False)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
    else:
        set_run_font(r, ea=HEI, ascii_=HEI, size=12, bold=False)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.keep_with_next = True
    return p


def caption(text, above=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    if above:
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
    else:
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(9)
        p.paragraph_format.keep_with_next = False
    r = p.add_run(text)
    set_run_font(r, ea=SONG, size=10.5, bold=True)
    return p


def formula(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(3)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.5
    r = p.add_run(text)
    set_run_font(r, ea=SONG, ascii_="Cambria Math", size=11.5)
    return p


def code_block(code):
    p = doc.add_paragraph()
    shade(p._p, "F4F4F4")
    pf = p.paragraph_format
    pf.left_indent = Cm(0.8)
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(3)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    for i, line in enumerate(code.split("\n")):
        r = p.add_run(line)
        set_run_font(r, ea=SONG, ascii_=CONSOLAS, size=9.5)
        if i != len(code.split("\n")) - 1:
            r.add_break()
    return p


def figure(path, width_cm=15.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(path, width=Cm(width_cm))


def _rebuild_tbl_pr(table, widths, top=40, bottom=40, left=80, right=80):
    """按 OOXML 规定顺序重建 tblPr，避免重复或乱序元素导致文件被判定损坏。"""
    tbl = table._tbl
    old = tbl.tblPr
    style = old.find(qn("w:tblStyle")) if old is not None else None

    new = OxmlElement("w:tblPr")
    if style is not None:
        new.append(style)

    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "center")

    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), str(int(sum(Cm(w).twips for w in widths))))
    tbl_w.set(qn("w:type"), "dxa")
    new.append(tbl_w)
    new.append(jc)

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    new.append(layout)

    mar = OxmlElement("w:tblCellMar")
    for tag, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement("w:%s" % tag)
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    new.append(mar)

    look = OxmlElement("w:tblLook")
    for key, val in (("val", "04A0"), ("firstRow", "1"), ("lastRow", "0"),
                     ("firstColumn", "1"), ("lastColumn", "0"),
                     ("noHBand", "0"), ("noVBand", "1")):
        look.set(qn("w:%s" % key), val)
    new.append(look)

    tbl.replace(old, new)


def table(headers, rows, widths, align_center=True, font_size=TABLE_PT):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"

    # 固定列宽：写入 tblGrid，避免渲染器重新分配列宽
    for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(Cm(w).twips)))

    # 表头
    hdr = t.rows[0]
    tr_pr = hdr._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    tr_pr.append(th)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = Cm(widths[i])
        shade(cell._tc.get_or_add_tcPr(), "DCE6F1")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(h)
        set_run_font(r, ea=HEI, ascii_=HEI, size=font_size, bold=False)

    for row in rows:
        cells = t.add_row().cells
        tr = t.rows[-1]._tr
        tr_pr = tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        tr_pr.append(cant)
        for i, val in enumerate(row):
            cell = cells[i]
            cell.width = Cm(widths[i])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (align_center or i == 0) \
                else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(val))
            set_run_font(r, ea=SONG, size=font_size)
    # 表格整体宽度
    for row in t.rows:
        for i, cell in enumerate(row.cells):
            cell.width = Cm(widths[i])
    _rebuild_tbl_pr(t, widths)
    # 表后留出少量间距
    sp = doc.add_paragraph()
    sp.paragraph_format.first_line_indent = Pt(0)
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)
    sp.paragraph_format.line_spacing = Pt(1)
    return t


def add_field(paragraph, instr, hint=""):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    text_el = OxmlElement("w:t")
    text_el.text = hint
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    for el in (fld_begin, instr_el, fld_sep, text_el, fld_end):
        run._r.append(el)


def page_break():
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)


# ----------------------------------------------------------------- 文档与样式
doc = Document()

sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(3.0)
sec.right_margin = Cm(3.0)
sec.top_margin = Cm(2.54)
sec.bottom_margin = Cm(2.54)
sec.header_distance = Cm(1.5)
sec.footer_distance = Cm(1.75)
sec.different_first_page_header_footer = True

normal = doc.styles["Normal"]
normal.font.name = TNR
normal.font.size = Pt(BODY_PT)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.first_line_indent = Pt(BODY_PT * 2)

for lvl in (1, 2, 3):
    st = doc.styles["Heading %d" % lvl]
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.font.name = HEI
    st.element.rPr.rFonts.set(qn("w:eastAsia"), HEI)

# 打开文档时更新域（目录）
settings = doc.settings.element

# 页眉页脚（非首页）
header = sec.header
hp = header.paragraphs[0]
hp.text = ""
pPr = hp._p.get_or_add_pPr()
bdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single")
bottom.set(qn("w:sz"), "4")
bottom.set(qn("w:space"), "1")
bottom.set(qn("w:color"), "BFBFBF")
bdr.append(bottom)
insert_at = 1 if pPr.find(qn("w:pStyle")) is not None else 0
pPr.insert(insert_at, bdr)
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
hr = hp.add_run("四轮差速底盘与摩擦轮发射机构控制系统 · 中期报告")
set_run_font(hr, ea=SONG, size=9, color=RGBColor(0x80, 0x80, 0x80))

footer = sec.footer
fp = footer.paragraphs[0]
fp.text = ""
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r1 = fp.add_run("— ")
set_run_font(r1, ea=SONG, size=9)
add_field(fp, " PAGE ", "1")
r2 = fp.add_run(" —")
set_run_font(r2, ea=SONG, size=9)

# -------------------------------------------------------------------- 封面
for _ in range(2):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_after = Pt(6)
r = p.add_run("移 动 机 器 人 控 制 系 统")
set_run_font(r, ea=HEI, size=16, color=RGBColor(0x40, 0x40, 0x40))

for _ in range(2):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(4)
p.paragraph_format.line_spacing = 1.3
r = p.add_run("四轮差速底盘与摩擦轮\n发射机构控制系统设计")
set_run_font(r, ea=HEI, size=28)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_before = Pt(6)
r = p.add_run("—— 中 期 报 告 ——")
set_run_font(r, ea=HEI, size=16, color=RGBColor(0x40, 0x40, 0x40))

for _ in range(4):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

info = [
    ("姓　　名", "________________"),
    ("学　　号", "________________"),
    ("专　　业", "________________"),
    ("指导教师", "________________"),
    ("学　　院", "________________"),
]
for label, value in info:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run("%s：%s" % (label, value))
    set_run_font(r, ea=SONG, size=14)

for _ in range(3):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
r = p.add_run("2026 年 11 月")
set_run_font(r, ea=SONG, size=14)

page_break()

# -------------------------------------------------------------------- 摘要
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(12)
r = p.add_run("摘　要")
set_run_font(r, ea=HEI, size=16)

para("本报告总结了移动机器人控制系统的阶段性研制工作。系统以 STM32F407VET6 为主控，"
     "围绕四轮差速底盘、摩擦轮发射机构与二自由度云台三部分展开：采用双 PWM 方式驱动四路"
     "直流减速电机，利用 TIM2~TIM5 的正交编码器接口测量轮速，在 100 Hz 定时中断中完成四路"
     "速度环 PID 运算；以 50 Hz 频率执行带归一化限幅的差速逆运动学解算，并对速度指令进行"
     "一阶低通平滑；摩擦轮无刷电机采用 V/f 开环三相正弦驱动，由 5 kHz 中断更新电角度；"
     "云台两路舵机由 50 Hz PWM 控制。系统同时实现了基于外部中断的急停保护、OLED 状态显示"
     "与电池电压采集。中期调试中定位并解决了 TIM6 中断无法进入的问题，其根本原因是主程序"
     "未调用 MX_TIM6_Init()，导致 HAL 定时器句柄停留在复位态、启动函数提前返回。目前各执行"
     "机构的软件链路已基本打通，下一阶段将重点完成通信协议、参数标定、闭环整定与整机联调。")
para("关键词：STM32F407；差速驱动；PID 控制；逆运动学；无刷电机；嵌入式系统", indent=False,
     space_before=6)

page_break()

# -------------------------------------------------------------------- 目录
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_after = Pt(12)
r = p.add_run("目　录")
set_run_font(r, ea=HEI, size=16)

toc_path = os.path.join(BASE, "toc_pages.json")
toc_entries = []
if os.path.exists(toc_path):
    toc_entries = json.load(open(toc_path, encoding="utf-8"))

for entry in toc_entries:
    depth = entry.get("depth", 1)
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.left_indent = Cm(0.0 if depth == 1 else 0.85)
    pf.space_before = Pt(3 if depth == 1 else 0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.12
    pf.tab_stops.add_tab_stop(Cm(14.9), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r1 = p.add_run(entry["title"])
    set_run_font(r1, ea=HEI if depth == 1 else SONG, ascii_=TNR,
                 size=12, bold=False)
    r2 = p.add_run("\t")
    set_run_font(r2, ea=SONG, size=12)
    page = entry.get("page")
    r3 = p.add_run(str(page) if page else "—")
    set_run_font(r3, ea=SONG, size=12)

# ==================================================================== 1 概述
h1 = heading("1　项目概述", 1)
h1.paragraph_format.page_break_before = True
heading("1.1　项目背景与目标", 2)
para("本项目面向移动机器人平台的实际需求，研制一台由四轮差速底盘、摩擦轮发射机构和"
     "二自由度云台组成的移动机器人。底盘负责平面内的快速机动与精确走位，摩擦轮通过高速"
     "旋转的轮盘将弹丸加速射出，云台用于调整发射的俯仰角与偏航角。三者需要在统一的实时"
     "控制框架下协同工作，对控制周期、响应速度与安全性提出了较高要求。")
para("中期阶段的目标是完成控制系统软硬件平台的搭建，打通“指令输入—运动学解算—闭环"
     "控制—执行机构”的完整链路，并逐一验证各执行机构的基本功能，为后续整机联调与性能"
     "优化奠定基础。")

heading("1.2　中期目标完成情况", 2)
para("围绕上述目标开展的工作及完成情况如表 1 所示。", space_before=2)
caption("表 1　中期目标完成情况", above=True)
table(
    ["序号", "工作内容", "计划目标", "完成情况"],
    [
        ["1", "硬件平台", "主控选型与外设资源分配", "已完成"],
        ["2", "底盘驱动", "四路电机双 PWM 调速与正反转", "已完成"],
        ["3", "轮速测量", "四路正交编码器与转速折算", "已完成，系数待标定"],
        ["4", "速度闭环", "100 Hz 四轮独立 PID 速度环", "已完成，参数整定中"],
        ["5", "运动学解算", "差速逆解、归一化限幅与平滑", "已完成，平滑待接入"],
        ["6", "摩擦轮驱动", "5 kHz 三相正弦开环驱动与使能", "已完成，闭环待实现"],
        ["7", "云台控制", "双舵机 50 Hz PWM 与脉宽映射", "已完成，行程待标定"],
        ["8", "安全与人机交互", "急停、OLED 显示与电压采集", "已完成"],
        ["9", "通信接口", "USART1 DMA 空闲中断收发框架", "框架完成，协议待定义"],
        ["10", "整机联调", "直线、转向、发射联调与测试", "进行中（下一阶段）"],
    ],
    [1.2, 3.0, 6.8, 4.0],
    font_size=10,
)

heading("1.3　主要工作内容", 2)
para("（1）基于 STM32CubeMX 完成 STM32F407VET6 的时钟、定时器、编码器、ADC、串口与 "
     "DMA 配置，生成 Keil MDK 工程；")
para("（2）自行编写电机、编码器、舵机、无刷电机、OLED、ADC 与串口等底层驱动，形成独立于 "
     "CubeMX 生成代码的驱动层；")
para("（3）实现带前馈、变速积分、积分分离与限幅措施的通用 PID 类，并搭建四轮速度闭环；")
para("（4）实现差速逆运动学解算、等比归一化限幅与一阶低通指令平滑；")
para("（5）实现摩擦轮三相正弦开环驱动、使能控制与急停保护逻辑；")
para("（6）完成 TIM6 中断无法进入问题的定位与修复，并总结出可复用的排查方法。")

# ================================================================ 2 总体方案
heading("2　系统总体方案", 1)
heading("2.1　硬件平台与时钟配置", 2)
para("控制系统以 STM32F407VET6 为核心。该芯片基于 Cortex-M4F 内核，集成单精度浮点单元，"
     "最高主频 168 MHz，具备 512 KB Flash 与 192 KB SRAM（含 64 KB CCM），片内定时器、"
     "编码器接口与 DMA 资源丰富，能够满足四路电机控制、三相互补 PWM 与多路串口并发的需求。")
para("系统时钟当前由内部 HSI（16 MHz）经 PLL 倍频得到：PLLM = 8、PLLN = 168、PLLP = 2，"
     "得到 SYSCLK = 168 MHz；AHB 不分频，APB1 四分频（42 MHz，定时器时钟 84 MHz），"
     "APB2 二分频（84 MHz，定时器时钟 168 MHz）。各外设的 PWM 频率与中断频率均由此推算，"
     "如表 3 所示。")

heading("2.2　外设资源分配", 2)
para("系统外设资源分配如表 2 所示。四路直流电机采用双 PWM 驱动，四路正交编码器分别接入"
     "四个定时器的编码器接口；摩擦轮使用 TIM8 的三路 PWM 驱动三相桥；云台舵机由 TIM12 "
     "输出 50 Hz PWM；急停按钮接入 EXTI3，电池电压接入 ADC1_IN8。")
caption("表 2　系统外设资源分配", above=True)
table(
    ["功能", "外设 / 定时器", "引脚", "说明"],
    [
        ["电机 A 驱动", "TIM10_CH1/TIM11_CH1", "PB8 / PB9", "双 PWM 正反转"],
        ["电机 B 驱动", "TIM9_CH1/CH2", "PE5 / PE6", "双 PWM 正反转"],
        ["电机 C 驱动", "TIM1_CH1/CH2", "PE9 / PE11", "双 PWM 正反转"],
        ["电机 D 驱动", "TIM1_CH3/CH4", "PE13 / PE14", "双 PWM 正反转"],
        ["编码器 A", "TIM2 编码器模式", "PA15 / PB3", "32 位计数器"],
        ["编码器 B", "TIM3 编码器模式", "PB4 / PB5", "16 位计数器"],
        ["编码器 C", "TIM4 编码器模式", "PB6 / PB7", "16 位计数器"],
        ["编码器 D", "TIM5 编码器模式", "PA0 / PA1", "32 位计数器"],
        ["摩擦轮驱动", "TIM8_CH1~CH3", "PC6 / PC7 / PC8", "三相 PWM，10 kHz"],
        ["摩擦轮使能", "GPIO 输出", "PA2", "高电平使能"],
        ["云台舵机", "TIM12_CH1/CH2", "PB14 / PB15", "50 Hz 舵机 PWM"],
        ["电池电压", "ADC1_IN8", "PB0", "1/11 电阻分压"],
        ["急停输入", "EXTI3", "PD3", "双边沿触发"],
        ["状态指示", "GPIO 输出", "PE8", "急停指示灯"],
        ["上位机通信", "USART1 + DMA", "PA9 / PA10", "115200 bit/s"],
        ["调试串口", "USART3", "PD8 / PD9", "115200 bit/s"],
        ["OLED 显示", "GPIO 软件 I2C", "PD11~PD14", "128×64 点阵"],
    ],
    [2.8, 4.6, 3.4, 4.2],
    font_size=10,
)

heading("2.3　软件架构", 2)
para("软件按应用层、算法层、驱动层与硬件抽象层划分，整体结构如图 1 所示。应用层由 "
     "main.cpp 负责任务调度、状态管理与中断回调；算法层提供 PID、差速逆运动学、指令平滑"
     "与数学工具；驱动层封装电机、编码器、舵机、无刷电机、OLED、ADC 与串口；最底层为 "
     "STM32 HAL 库与 CubeMX 生成的初始化代码。")
figure(os.path.join(ASSETS, "fig_system.png"), 15.0)
caption("图 1　系统总体框图")
para("这种分层方式的优点是：算法与具体硬件解耦，便于单独测试与替换；驱动层接口统一，"
     "新增执行机构时只需增加对应驱动类；CubeMX 生成代码集中在 Core 目录，用户代码集中在 "
     "MyDrivers 目录，重新生成外设配置时冲突较小。用户自写代码约 1600 行（不含字库与 "
     "CubeMX 生成代码），文件清单见附录 A。")
para("需要说明的是，工程中同时保留了 CubeMX 生成的 main.c 与手写的 main.cpp 两份入口"
     "文件，实际参与编译的是 main.cpp（Keil 工程仅包含 main.cpp），main.c 仅作参考。"
     "这一双入口结构在后续调试中引发了 TIM6 初始化遗漏的问题，详见 4.2 节。")

heading("2.4　任务划分与中断时序", 2)
para("控制任务全部在定时器中断中完成，主循环只负责人机界面的低速刷新，避免阻塞控制链路。"
     "TIM13 以 100 Hz 触发控制主中断，完成编码器采样、四路 PID 运算、舵机更新与摩擦轮"
     "使能控制；在 100 Hz 中断内部再做二分频，每两次进入一次逆运动学解算，使解算频率为 "
     "50 Hz。TIM6 以 5 kHz 更新摩擦轮电角度。各定时器分工如表 3 所示。")
caption("表 3　定时器分工与任务频率", above=True)
table(
    ["定时器", "频率", "主要用途", "中断优先级"],
    [
        ["TIM1 / TIM9 / TIM10 / TIM11", "10 kHz", "四路电机双 PWM 输出", "—"],
        ["TIM8", "10 kHz", "摩擦轮三相 PWM（中心对齐）", "—"],
        ["TIM6", "5 kHz", "摩擦轮电角度积分与三相电压更新", "0（最高）"],
        ["TIM13", "100 Hz", "编码器采样、PID、舵机、摩擦轮使能", "0（最高）"],
        ["TIM12", "50 Hz", "云台舵机 PWM 输出", "—"],
        ["TIM2 / TIM3 / TIM4 / TIM5", "—", "四路正交编码器计数", "—"],
    ],
    [4.6, 2.2, 6.6, 2.6],
)
para("系统的控制数据流如图 2 所示：底盘速度环由指令输入、一阶低通、逆解、PID 与 PWM "
     "依次构成，编码器测速形成闭环反馈；摩擦轮则在 5 kHz 中断中更新电角度，经反 Park "
     "变换与占空比映射后输出三相 PWM。")
figure(os.path.join(ASSETS, "fig_control.png"), 15.0)
caption("图 2　控制系统数据流")
para("所有中断优先级均配置为 0，同优先级的中断之间不互相抢占，因此 TIM6 与 TIM13 不会"
     "彼此打断；但由于 5 kHz 中断中执行了三角函数运算，其 CPU 占用率需要在后续测试中"
     "用 DWT 或 IO 翻转法测量，必要时可将部分计算移出中断。")

# ================================================================ 3 模块实现
heading("3　关键模块设计与实现", 1)
heading("3.1　电机驱动与轮速测量", 2)
para("每个直流减速电机由两路 PWM 组成 H 桥控制：一路给定占空比调速，另一路保持常高电平"
     "（比较值 ARR − 1）以打开对应桥臂。速度指令为 −100~100 的百分比，取绝对值后映射为"
     "比较值：")
formula("CCR = ARR + 1 − round( |u| / 100 × (ARR + 1) )，ARR = 16799")
para("方向由符号决定，通过交换两路 PWM 的角色实现正反转。四路电机分别占用 TIM10/TIM11"
     "（A）、TIM9（B）、TIM1_CH1/CH2（C）、TIM1_CH3/CH4（D），PWM 频率为 "
     "168 MHz / 16800 = 10 kHz。")
para("测速采用定时器编码器模式：TIM2~TIM5 分别对四路正交编码器计数。控制周期（10 ms）"
     "内读取一次计数器并清零，得到该周期内的脉冲增量 N，再折算为轮子角速度：")
formula("ω = clamp(N, −140, 140) / 140 × 28.462 × π　（rad/s）")
para("式中 140 为单周期脉冲饱和值，28.462 为减速比与编码器线数的综合折算系数，π 将转/秒"
     "换算为弧度/秒。按当前折算系数，量程上限约为 89 rad/s（对应轮速约 3.1 m/s）。该系数"
     "目前为经验值，尚未用标准转速源标定，是下一阶段的标定项之一。")
para("由于 C、D 两个电机在机械上左右对称安装，代码中对这两路速度取反，保证四轮在同一"
     "车体坐标系下的正方向一致。")

heading("3.2　速度环 PID 控制", 2)
para("速度环采用位置式 PID，四个轮子各有一个 Class_PID 实例，在 TIM13 的 100 Hz 中断中"
     "依次执行。为兼顾快速性与超调，算法在经典 PID 基础上增加了前馈、变速积分、积分分离、"
     "死区与微分先行等可配置措施，其离散形式为：")
formula("u(k) = K_P·e(k) + K_I·Σe(j)·T_s + K_D·[e(k) − e(k−1)] / T_s + K_F·ΔTarget")
para("其中变速积分在误差较大时按比例降低积分权重，误差超过阈值后停止积分；积分分离在"
     "误差超过设定阈值时直接清零积分；积分项限幅为 ±100、输出限幅为 ±100，与速度指令的"
     "百分比量纲一致；死区用于抑制稳态附近的抖动；微分先行以“当前值”代替“误差”做微分，"
     "避免目标阶跃引起的微分冲击。")
para("当前整定参数为 K_P = 3.0、K_I = 12.0、K_D = 0、K_F = 0，控制周期 T_s = 10 ms，"
     "主要参数如表 4 所示。此外，在逆解目标过零时（cross_zero 函数判断符号变化且不处于"
     "零带内）主动清零对应轮的积分项，抑制换向过程中的积分累积与换向冲击。")
caption("表 4　速度环 PID 主要参数", above=True)
table(
    ["参数", "取值", "参数", "取值"],
    [
        ["比例系数 K_P", "3.0", "控制周期 T_s", "10 ms"],
        ["积分系数 K_I", "12.0", "积分限幅", "±100"],
        ["微分系数 K_D", "0", "输出限幅", "±100"],
        ["前馈系数 K_F", "0", "死区", "0"],
    ],
    [4.5, 3.0, 4.5, 3.0],
)

heading("3.3　差速逆运动学与指令平滑", 2)
para("给定车体线速度 v_x 与角速度 ω，左右轮轮心的线速度为：")
formula("v_L = v_x − ω·b / 2，　v_R = v_x + ω·b / 2")
para("为避免某一侧轮速超限导致轨迹畸变，采用等比归一化限幅：当 max(|v_L|, |v_R|) 超过 "
     "v_max = ω_max·r 时，两轮速度同时乘以比例系数 k = v_max / max(|v_L|, |v_R|)，从而"
     "保持 v_L / v_R 比值（即转弯半径）不变。限幅后再除以轮半径得到左右轮目标角速度：")
formula("ω_L = v_L / r，　ω_R = v_R / r")
para("其中轮半径 r = 35 mm、轮距 b = 500 mm、单轮最大角速度暂取 300 rad/s，主要参数如"
     "表 5 所示。逆运动学同时提供正解接口，可由左右轮速反推车体线速度与角速度，用于"
     "闭环校验。")
caption("表 5　差速逆运动学与平滑参数", above=True)
table(
    ["参数", "符号", "取值", "说明"],
    [
        ["轮半径", "r", "0.035 m", "待实测确认"],
        ["轮距", "b", "0.5 m", "待实测确认"],
        ["单轮最大角速度", "ω_max", "300 rad/s", "待最终确定"],
        ["平滑时间常数", "τ", "50 ms", "一阶低通"],
        ["解算周期", "T_s", "20 ms", "50 Hz"],
    ],
    [4.0, 2.0, 3.2, 5.8],
)
para("指令平滑采用一阶低通滤波器：y(k) = y(k−1) + α·[x(k) − y(k−1)]，其中 "
     "α = T_s / (τ + T_s)。取 τ = 50 ms、T_s = 20 ms，则 α ≈ 0.286，用于抑制上位机指令"
     "突变带来的冲击。需要指出，当前代码虽然计算了平滑后的 vx_f、om_f，但逆解仍然使用"
     "原始指令 vx_cmd、om_cmd，平滑环节尚未真正接入控制链路，已列入整改项（见 6.1 节）。")

heading("3.4　摩擦轮无刷电机开环驱动", 2)
para("摩擦轮采用无刷直流电机，由 TIM8 的三路 PWM 驱动三相桥。控制上采用 V/f 开环方式："
     "按给定电角速度积分得到电角度，再由 Uq、Ud 经反 Park 变换得到三相正弦电压：")
formula("Ua = cosθ·Ud − sinθ·Uq")
formula("Ub = cos(θ − 2π/3)·Ud − sin(θ − 2π/3)·Uq")
formula("Uc = cos(θ + 2π/3)·Ud − sin(θ + 2π/3)·Uq")
para("三相电压经母线电压归一化后映射为比较值：")
formula("CCR = (0.5 + U / V_dc) × 8400")
para("其中 V_dc = 12 V，TIM8 工作于中心对齐模式、ARR = 8399，PWM 频率为 "
     "168 MHz / (2 × 8400) = 10 kHz。电角度在 TIM6 的 5 kHz 中断中更新：θ += 70 × 0.0002 "
     "rad，并对 2π 取模，对应电角速度 70 rad/s。")
para("当前 Uq 固定为 1 V、Ud = 0，属于恒压开环运行，转速会随负载变化；后续需要引入转速"
     "闭环、电流采样与限幅。使能信号由 PA2 输出，可随时切断驱动，并与急停逻辑联动。")

heading("3.5　云台舵机控制", 2)
para("云台两路舵机由 TIM12 的 CH1（PB14，Yaw）与 CH2（PB15，Pitch）控制。定时器预分频"
     "值为 83，计数时钟 1 MHz，ARR = 9999，输出 50 Hz、周期 20 ms 的 PWM，比较值直接对应 "
     "1000~2000 μs 的脉宽。")
para("为避免舵机在零指令附近抖动，映射采用带死区的分段线性方式：|speed_rate| 小于死区时"
     "输出中位 1500 μs；正转在 1600~2000 μs 之间线性映射，反转在 1400~1000 μs 之间线性"
     "映射，并对输入做 ±100 限幅与 NaN 保护。急停时两路立即回到 1500 μs 中位，防止云台"
     "在急停过程中继续摆动。")

heading("3.6　人机接口与通信", 2)
para("显示部分采用 128×64 点阵 OLED，通过 GPIO 软件模拟 I2C 时序（PD11 为数据/命令选择、"
     "PD12 为复位、PD13 为 SDA、PD14 为 SCL）。主循环每秒刷新一次，显示当前 Kp、Ki、Kd "
     "与电池电压，便于在整定参数时脱离上位机观察状态。")
para("电池电压由 PB0（ADC1_IN8）采集，外部 1/11 电阻分压，12 位分辨率、单次转换、轮询"
     "读取，换算关系为 V = ADC / 4095 × 3.3 × 11。按此关系，12 V 电池对应的采样值约为 "
     "1353，量程上限约 36 V。")
para("串口方面，USART1（PA9/PA10，115200 bit/s）配置为 DMA 空闲中断接收 + DMA 发送，"
     "移植自 SCUT-RobotLab 的 UART 管理框架，通过函数指针注册接收回调，便于后续接入"
     "上位机协议；USART3（PD8/PD9）作为调试口使用。")

heading("3.7　急停与安全逻辑", 2)
para("急停按钮接 PD3，配置为双边沿触发的外部中断。按下时拉高 PE8 指示灯并置位 "
     "estop_active；松开时清除标志。TIM13 控制中断检测到 estop_active 后立即将四轮速度"
     "置零并跳过逆解与 PID 运算，同时舵机回中、摩擦轮断使能，保证任何时刻都能可靠停机。")
para("解除急停时，程序清空 PID 的积分与历史状态、清零速度指令并复位平滑器，避免恢复"
     "瞬间的指令跳变与积分冲击。由于急停判断放在控制中断的最前端，其响应延迟不超过一个"
     "控制周期（10 ms）。")

# ================================================================ 4 关键问题
heading("4　关键问题与解决", 1)
heading("4.1　TIM6 中断无法进入的问题", 2)
para("现象：TIM13 的 100 Hz 控制中断工作正常，但 TIM6 的 5 kHz 回调始终不执行，摩擦轮"
     "不转，系统也没有进入 HardFault。")
para("排查：首先确认 TIM6 已在 CubeMX 中使能（PSC = 0、ARR = 16799、NVIC 中断使能），"
     "tim.c 中也生成了 MX_TIM6_Init() 与 TIM6_DAC_IRQHandler()。随后检查 Keil 工程的链接"
     "输入文件（.lnp）与依赖文件（.d），发现参与编译的 main 来自 main.cpp，而 "
     "MX_TIM6_Init() 的调用只出现在未被加入工程的 main.c 中。map 文件中出现了如下记录：")
code_block("Removing tim.o(i.MX_TIM6_Init), (76 bytes).")
para("说明该初始化函数从未被引用，被链接器当作死代码删除。")
para("原因：htim6 位于 .bss 段，未初始化时全部为 0，其 State 字段为 HAL_TIM_STATE_RESET。"
     "HAL_TIM_Base_Start_IT() 在使能更新中断之前会检查句柄状态，不满足则直接返回 "
     "HAL_ERROR：")
code_block("if (htim->State != HAL_TIM_STATE_READY)\n"
           "{\n"
           "  return HAL_ERROR;   /* 未置位 DIER.UIE，也未使能 CR1.CEN */\n"
           "}")
para("因此 TIM6 的计数器根本没有启动，更新中断源不存在，回调自然无法进入；又因为函数"
     "在访问寄存器之前就提前返回，也没有触发 HardFault，最终表现为“静默失效”。")
para("解决：在 main.cpp 的外设初始化序列中、HAL_TIM_Base_Start_IT(&htim6) 之前补上 "
     "MX_TIM6_Init() 调用。修复后重新编译，map 文件中不再出现该函数的删除记录，仿真"
     "可见 htim6.Instance 指向 0x40001000、State 变为 READY，TIM6 中断正常进入。")
para("经验总结：（1）CubeMX 只维护 main.c，手写的 main.cpp 不会被自动更新，凡是在 "
     "CubeMX 中新增外设，都必须同步修改实际参与编译的入口文件；（2）HAL 启动类函数的"
     "返回值不应忽略，工程中应检查其是否为 HAL_OK，以便及早发现句柄未初始化的问题。")

heading("4.2　双入口文件带来的维护风险", 2)
para("工程目录中同时存在 main.c 与 main.cpp，两者都定义了 main 函数与部分回调。Keil "
     "工程当前只将 main.cpp 加入编译，但 CubeMX 每次重新生成代码时只会更新 main.c，"
     "因此新增外设的初始化调用会“生成在不参与编译的文件里”，4.1 节的问题正是由此产生。"
     "建议将 main.c 移出工程（或改名备份），保留唯一入口；并在每次 CubeMX 重新生成后，"
     "按检查表核对 main.cpp 中的外设初始化调用是否同步。")

heading("4.3　其他调试问题", 2)
para("（1）C/C++ 混编：HAL 回调在 C 文件中定义，必须保证 C++ 侧的 HAL_TIM_PeriodElapsed"
     "Callback 等符号为 C 链接。main.h 已用 extern \"C\" 包裹，链接正常，回调能够正确"
     "覆盖 HAL 的弱定义。")
para("（2）宏重定义：PI 宏在 Encoder.h 与 drv_math.h 中重复定义，编译时产生警告，建议"
     "统一到一个公共头文件中。")
para("（3）文件格式：个别文件末尾缺少换行，属于格式类警告，不影响功能，可在后续整理"
     "代码时统一处理。")

# ================================================================ 5 测试
heading("5　阶段性测试与结果", 1)
heading("5.1　测试平台与方法", 2)
para("调试平台包括 12 V 稳压电源、ST-Link 调试器、示波器、USB 转串口模块与 Keil MDK "
     "在线调试环境。测试遵循“先单轮后整机、先开环后闭环、先空载后负载”的顺序：先单独"
     "验证每一路 PWM 与编码器，再联调四轮速度环，最后进行底盘运动与摩擦轮测试。")

heading("5.2　功能验证情况", 2)
para("各功能模块的验证项、判据与当前状态如表 6 所示。", space_before=2)
caption("表 6　功能验证情况", above=True)
table(
    ["序号", "测试项", "方法 / 判据", "状态"],
    [
        ["1", "四轮正反转", "给定 ±50% 指令，观察转向与占空比", "正常"],
        ["2", "PWM 频率", "示波器测量 PE9、PE13 等引脚", "10 kHz，正常"],
        ["3", "编码器计数", "手动转动轮子，观察计数器增减", "正常"],
        ["4", "控制周期", "中断内翻转 IO，示波器测量", "100 Hz，正常"],
        ["5", "速度闭环", "阶跃指令，观察跟随性与稳态误差", "初步通过，待整定"],
        ["6", "逆运动学", "给定 v_x/ω，检查四轮目标符号与比例", "正常"],
        ["7", "摩擦轮驱动", "5 kHz 中断计数与三相波形观测", "初步通过，待标定"],
        ["8", "舵机输出", "1.5 ms 中位、1~2 ms 行程测量", "正常，行程待标定"],
        ["9", "急停保护", "按下/松开按钮，观察停机与恢复", "正常"],
        ["10", "电池电压", "与万用表读数对比", "功能正常，误差待测"],
    ],
    [1.2, 3.8, 6.8, 3.2],
)

heading("5.3　结果说明", 2)
para("上述结论来自开发过程中的台架观察，尚未形成完整的定量测试记录。阶跃响应曲线、"
     "稳态误差、最高车速、连续工作时间等指标，将在下一阶段用示波器与上位机采集后补充，"
     "并整理为图表纳入最终报告。")
para("从当前调试情况看，四轮速度环能够跟随指令变化，但由于编码器折算系数尚未标定、"
     "PID 参数仅做了初步整定，低速段存在量化噪声、换向时存在短暂超调，需要在下一阶段"
     "结合实测数据继续优化。")

# ================================================================ 6 问题计划
heading("6　存在的问题与下一步计划", 1)
heading("6.1　当前存在的主要问题", 2)
para("结合中期调试情况，当前存在的主要问题、影响与拟采取的措施如表 7 所示。", space_before=2)
caption("表 7　当前存在的主要问题", above=True)
table(
    ["序号", "问题描述", "影响与优先级", "拟采取措施"],
    [
        ["1", "指令平滑结果未参与逆解，仍使用原始指令", "指令突变时冲击较大；高", "修改为使用平滑后的 vx_f、om_f"],
        ["2", "编码器折算系数为经验值，未标定", "轮速与里程不准；高", "用标准转速源或光电门标定"],
        ["3", "摩擦轮仅开环 V/f，Uq 固定", "转速随负载漂移；高", "增加转速反馈与电流限幅"],
        ["4", "上位机通信协议未定义，回调为空", "无法远程控制；高", "定义帧格式、CRC 与超时保护"],
        ["5", "缺少欠压、过流、超速保护", "存在硬件风险；中", "增加保护阈值与故障状态机"],
        ["6", "5 kHz 中断负载未测量", "可能影响实时性；中", "DWT 计时或 IO 翻转测量"],
        ["7", "主循环使用 HAL_Delay(1000) 阻塞", "响应不够及时；低", "改为时基调度或状态机"],
        ["8", "main.c 与 main.cpp 并存", "易遗漏初始化；中", "移出 main.c，保留单一入口"],
        ["9", "轮径、轮距等机械参数未实测", "解算存在系统误差；中", "实测并更新参数表"],
        ["10", "定量测试数据不足", "难以评估性能；中", "补充阶跃、稳态与续航测试"],
    ],
    [1.3, 5.5, 4.0, 4.2],
)

heading("6.2　下一阶段工作计划", 2)
para("下一阶段的工作按“通信—标定—闭环—联调—总结”的顺序推进，具体安排如表 8 所示。",
     space_before=2)
caption("表 8　下一阶段工作计划", above=True)
table(
    ["阶段", "时间", "主要工作", "预期成果"],
    [
        ["一", "第 1~2 周", "定义并实现上位机通信协议；完成 USART1 收发联调", "可远程下发速度、舵机与摩擦轮指令"],
        ["二", "第 3~4 周", "标定编码器系数、轮径与轮距；整定四轮速度环", "轮速测量准确，阶跃响应满足指标"],
        ["三", "第 5~6 周", "摩擦轮转速闭环、电流采样与限幅", "发射转速稳定，具备过流保护"],
        ["四", "第 7~8 周", "底盘直线、原地旋转、走位精度与云台随动联调", "整机运动性能达标"],
        ["五", "第 9 周", "整理测试数据与图表，撰写最终报告", "完成最终报告与演示"],
    ],
    [1.6, 2.6, 7.2, 3.6],
)

# ================================================================ 7 总结
heading("7　中期总结", 1)
para("中期阶段完成了移动机器人控制系统的总体方案设计与主要软件模块开发：搭建了以 "
     "STM32F407VET6 为核心、基于 CubeMX 与 HAL 库的工程框架；实现了四路直流电机的双 "
     "PWM 驱动与编码器测速、100 Hz 四轮速度闭环、50 Hz 差速逆运动学解算、摩擦轮三相"
     "正弦开环驱动、双舵机云台控制，以及急停保护、OLED 显示与电池电压采集等功能。用户"
     "自写代码约 1600 行，模块划分清晰，具备继续扩展的基础。")
para("调试过程中遇到并解决了 TIM6 中断无法进入的问题。该问题表面上是“中断不触发”，"
     "实质是入口文件不同步导致外设句柄未初始化、HAL 启动函数提前返回。通过链接输入文件"
     "与 map 文件的交叉比对定位根因，说明在嵌入式开发中，除了检查寄存器配置，还应关注"
     "“代码是否真正参与了编译与链接”。这一排查方法对后续类似问题具有参考价值。")
para("总体来看，中期目标基本达成，各执行机构的软件链路已经打通，但距离整机稳定运行仍有"
     "差距：通信协议、参数标定、摩擦轮闭环与安全保护是下一阶段的工作重点。后续将按照"
     "第 6.2 节的计划推进，补齐定量测试数据，完成整机联调与最终报告。")

# ================================================================ 附录
heading("附录 A　主要文件清单", 1)
para("工程中用户自写代码的文件清单如表 A.1 所示（不含 CubeMX 生成代码与字库文件，"
     "MyDrivers 目录下的文件省略了路径前缀）。", space_before=2)
caption("表 A.1　用户代码文件清单", above=True)
table(
    ["模块", "文件", "主要功能", "行数"],
    [
        ["应用入口", "Core/Src/main.cpp", "任务调度、中断回调、急停逻辑", "401"],
        ["PID 算法", "alg_pid.h / alg_pid.cpp", "通用 PID 类（前馈、变速积分等）", "398"],
        ["运动学", "diff_drive_ik.cpp", "差速逆解、归一化限幅、指令平滑", "90"],
        ["电机驱动", "Motor_cpp_style.h / .cpp", "双 PWM 调速与方向控制", "127"],
        ["编码器", "Encoder.h / Encoder.c", "脉冲读取与轮速折算", "36"],
        ["无刷电机", "BLDC.h / BLDC.c", "三相正弦开环驱动", "73"],
        ["舵机", "Servo.h / Servo.cpp", "速度—脉宽映射与限幅", "107"],
        ["显示", "bsp_oled.h / bsp_oled.c", "OLED 驱动与绘图接口", "375"],
        ["ADC", "bsp_adc.h / bsp_adc.c", "电池电压采集", "29"],
        ["串口", "drv_uart.h / drv_uart.c", "DMA 空闲中断收发框架", "194"],
        ["数学工具", "drv_math.h / drv_math.cpp", "限幅、绝对值、端序转换", "199"],
    ],
    [2.4, 6.2, 5.0, 1.4],
)

heading("附录 B　关键参数汇总", 1)
caption("表 B.1　关键参数汇总", above=True)
table(
    ["参数", "取值", "参数", "取值"],
    [
        ["系统主频", "168 MHz", "电机 PWM 频率", "10 kHz"],
        ["控制周期", "10 ms（100 Hz）", "逆解周期", "20 ms（50 Hz）"],
        ["摩擦轮更新频率", "5 kHz", "摩擦轮电角速度", "70 rad/s"],
        ["摩擦轮母线电压", "12 V", "摩擦轮 Uq", "1 V"],
        ["舵机 PWM 频率", "50 Hz", "舵机脉宽范围", "1000~2000 μs"],
        ["轮半径", "35 mm", "轮距", "500 mm"],
        ["编码器单周期饱和值", "±140", "轮速折算系数", "28.462"],
        ["电池分压比", "11 : 1", "ADC 分辨率", "12 bit"],
    ],
    [4.6, 3.0, 4.6, 2.8],
)

heading("参考文献", 1)
refs = [
    "[1] STMicroelectronics. RM0090 Reference Manual: STM32F405/415, STM32F407/417, "
    "STM32F427/437 and STM32F429/439 advanced Arm-based 32-bit MCUs[Z]. 2023.",
    "[2] STMicroelectronics. UM1725 Description of STM32F4 HAL and LL drivers[Z]. 2023.",
    "[3] Siegwart R, Nourbakhsh I R, Scaramuzza D. Introduction to Autonomous Mobile "
    "Robots[M]. 2nd ed. Cambridge: MIT Press, 2011.",
    "[4] 刘金琨. 先进 PID 控制 MATLAB 仿真[M]. 4 版. 北京: 电子工业出版社, 2016.",
]
for ref in refs:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.left_indent = Cm(0.74)
    pf.space_before = Pt(2)
    pf.line_spacing = 1.5
    r = p.add_run(ref)
    set_run_font(r, ea=SONG, size=10.5)

doc.core_properties.title = "四轮差速底盘与摩擦轮发射机构控制系统设计——中期报告"
doc.core_properties.subject = "移动机器人控制系统中期报告"
doc.core_properties.author = ""
doc.core_properties.comments = "由工程源码与调试记录整理"

doc.save(OUT)
print("saved:", OUT)
