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
hr = hp.add_run("第四届“拓竹杯”狼牙机器人争霸赛 · 中期进展报告")
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


# -*- coding: utf-8 -*-
"""《第四届“拓竹杯”狼牙机器人争霸赛 中期进展报告》正文部分。

与 _prefix.py（文档样式、页眉页脚、表格/插图等工具函数）拼接后运行。
"""

OUT = os.path.join(os.path.dirname(BASE),
                   "中期进展报告_第四届狼牙机器人争霸赛.docx")

# ------------------------------------------------------------------ 目录结构
HEADINGS = [
    (1, "1　团队信息与任务分工"),
    (2, "1.1　队伍概况"),
    (2, "1.2　成员与任务分工"),
    (2, "1.3　中期目标"),
    (1, "2　机器人总体方案"),
    (2, "2.1　比赛任务与规则约束"),
    (2, "2.2　整机组成与配合方式"),
    (2, "2.3　R1 射击机器人方案"),
    (2, "2.4　R2 取矿兑矿机器人方案"),
    (2, "2.5　电控与软件架构"),
    (2, "2.6　供电与线束方案"),
    (2, "2.7　规则符合性核对"),
    (1, "3　当前进展与阶段成果"),
    (2, "3.1　进展总览"),
    (2, "3.2　底盘与移动"),
    (2, "3.3　射击机构"),
    (2, "3.4　云台"),
    (2, "3.5　R2 取矿与兑换机构"),
    (2, "3.6　电控与程序"),
    (2, "3.7　选型与采购进展"),
    (2, "3.8　已完成的测试与验证"),
    (1, "4　当前问题与所需支持"),
    (2, "4.1　问题一：取矿机构方案与加工"),
    (2, "4.2　问题二：70 mm 台阶通过性"),
    (2, "4.3　问题三：发射一致性与云台扭矩"),
    (2, "4.4　所需支持汇总"),
    (1, "5　下一阶段计划"),
    (2, "5.1　任务分解与完成标准"),
    (2, "5.2　里程碑"),
    (1, "附录 A　比赛规则要点"),
    (1, "附录 B　材料清单与预算"),
    (1, "附录 C　关键参数汇总"),
    (1, "附录 D　讨论记录摘要"),
    (1, "附录 E　主要程序文件"),
]

page_map = {}
page_file = os.path.join(BASE, "toc_pages_mid.json")
if os.path.exists(page_file):
    for entry in json.load(open(page_file, encoding="utf-8")):
        page_map[entry["title"]] = entry.get("page")

# -------------------------------------------------------------------- 封面
for _ in range(2):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_after = Pt(6)
r = p.add_run("第四届“拓竹杯”狼牙机器人争霸赛")
set_run_font(r, ea=HEI, size=18, color=RGBColor(0x40, 0x40, 0x40))

for _ in range(2):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(4)
p.paragraph_format.line_spacing = 1.3
r = p.add_run("中 期 进 展 报 告")
set_run_font(r, ea=HEI, size=40)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_before = Pt(8)
r = p.add_run("R1 射击机器人　·　R2 取矿兑矿机器人")
set_run_font(r, ea=SONG, size=16, color=RGBColor(0x40, 0x40, 0x40))

for _ in range(5):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

info = [
    ("队伍名称", "________________"),
    ("参赛单位", "________________"),
    ("队　　长", "________________"),
    ("队伍成员", "________________"),
    ("报告日期", "2026 年 11 月 21 日"),
]
for label, value in info:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run("%s：%s" % (label, value))
    set_run_font(r, ea=SONG, size=14)

for _ in range(2):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)

page_break()

# -------------------------------------------------------------------- 目录
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
p.paragraph_format.space_after = Pt(12)
r = p.add_run("目　录")
set_run_font(r, ea=HEI, size=16)

for level, title in HEADINGS:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.left_indent = Cm(0.0 if level == 1 else 0.85)
    pf.space_before = Pt(2 if level == 1 else 0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    pf.tab_stops.add_tab_stop(Cm(14.9), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r1 = p.add_run(title)
    set_run_font(r1, ea=HEI if level == 1 else SONG, ascii_=TNR, size=12)
    r2 = p.add_run("\t")
    set_run_font(r2, ea=SONG, size=12)
    r3 = p.add_run(str(page_map.get(title, "—")))
    set_run_font(r3, ea=SONG, size=12)

# ============================================================ 1 团队与分工
h1 = heading("1　团队信息与任务分工", 1)
h1.paragraph_format.page_break_before = True

heading("1.1　队伍概况", 2)
para("本队参加第四届“拓竹杯”狼牙机器人争霸赛。按比赛规则，每支队伍每局最多派出两台机器人："
     "R1 为射击机器人，负责携带并发射弹丸、击毁对方高地靶与基地靶；R2 为取矿兑矿机器人，"
     "负责从己方矿石区取矿、运至中央高地区完成兑换，为己方换取额外弹丸。两支机器人共用一套"
     "底盘与电控平台，通过分工配合在 5 分钟一局的对抗中争取比分与兑换优势。")
para("截至本次中期考核，队伍的总体进度为：R1 的电控链路（底盘、云台、摩擦轮、急停、串口）"
     "已在台架上打通并完成初步验证；R1、R2 的机械结构处于设计与加工阶段；R2 的取矿与兑换"
     "机构方案正在收敛；采购清单与预算已基本确定，正在按清单采购。")

heading("1.2　成员与任务分工", 2)
para("队伍成员及分工如表 1 所示。", space_before=2)
caption("表 1　成员与任务分工", above=True)
table(
    ["姓名", "角色", "负责模块", "中期已完成的工作"],
    [
        ["（待填）", "队长", "总体方案、进度管理", "规则解读、任务分解、整机方案汇总"],
        ["（待填）", "机械", "R1 / R2 结构设计", "底盘与云台结构设计、取矿机构方案讨论"],
        ["（待填）", "电控", "嵌入式软件、供电线束", "底盘闭环、发射与云台驱动、急停与串口框架"],
        ["（待填）", "硬件与采购", "选型、采购、焊接", "材料清单与预算、双电池方案、分电与线束"],
        ["（待填）", "操作与调试", "操作手、联调", "台架测试、参数整定、比赛流程演练"],
    ],
    [2.2, 2.6, 4.6, 5.6],
)
para("说明：表中姓名待队伍确认后填写；分工按“模块负责人 + 交叉参与”的方式组织，"
     "每名成员在负责本模块的同时参与整机联调。")

heading("1.3　中期目标", 2)
para("结合比赛时间节点，队伍将中期目标拆分为三项：")
para("（1）R1 电控闭环打通：四轮底盘速度闭环、云台双轴控制、摩擦轮开环驱动、急停保护与"
     "上位机串口通信能够在台架上稳定运行；")
para("（2）R2 方案定型：完成取矿、存储、兑换机构的方案设计与关键尺寸核算，输出可加工的"
     "图纸或三维模型；")
para("（3）采购与整机准备：完成主控、驱动、电源、线束的采购与到货验收，为整机装配和第一次"
     "合练做好准备。")

# ============================================================ 2 总体方案
heading("2　机器人总体方案", 1)
heading("2.1　比赛任务与规则约束", 2)
para("比赛为红蓝双方对抗，采用 BO3 赛制，每局 5 分钟。单局内双方围绕三条主线展开：一是"
     "击毁对方高地靶（4 片开关，合计 30 分），二是高地靶被击毁后激活并击毁对方 4 个基地靶"
     "（3 个固定靶各 15 分、1 个移动靶 45 分，合计 90 分），三是 R2 通过取矿、运矿、兑换"
     "为己方换取额外弹丸。比赛结束时若未出现基地全毁，则依次比较总得分、有效兑换数量、"
     "兑换速度、在场机器人数量与总重量。")
para("比赛场地包含隧道区、起伏路段、70±1 mm 台阶、中央高地、兑换区以及双方矿石区，"
     "中央己方兑换区同时是对方机器人的禁区。机器人任意姿态下的外廓尺寸、弹丸规格、"
     "初始弹丸与兑换弹丸数量都有明确限制，这些约束直接决定了底盘、云台与发射机构的设计。")
para("需要说明的是，规则文本对尺寸的表述存在三处不一致：首页写作 500×500×550，2.4 节写作 "
     "550×500×500，附录一写作 500×550×500。队伍按最保守的 500×500×550 mm 包络进行设计，"
     "并计划在检录前向组委会书面确认，避免因尺寸判定影响参赛。", space_before=10)
caption("表 2　关键规则约束与设计对策", above=True)
table(
    ["约束项", "规则要求", "对设计的约束"],
    [
        ["外形尺寸", "任意姿态下不超过 500×500×550 mm", "云台、发射机构不得超界；轮距需压缩"],
        ["机器人配置", "R1 一台、R2 一台，BO3 每局 5 分钟", "两车共平台、备件通用，便于快速维修"],
        ["弹丸", "直径 17 mm、TPU、硬度 95A", "摩擦轮间隙与拨弹通道按 17 mm 设计"],
        ["弹丸数量", "初始 8 颗，最多兑换 3 次、每次 8 颗", "弹仓容量 ≥8，供弹机构需可快速补弹"],
        ["地形", "70±1 mm 台阶、隧道、起伏路", "底盘需具备越台阶能力，轮径与悬挂待验证"],
        ["安全", "可靠急停；禁用尖锐结构、高压气体", "硬件急停 + 软件急停双保险"],
        ["判罚", "弹丸命中本体不计分，恶意碰撞罚牌", "避免主动碰撞，控制策略以走位为主"],
    ],
    [2.6, 6.4, 6.0],
    font_size=10,
)
para("从得分结构看，高地靶只有 30 分，基地靶合计 90 分，但基地靶必须在我方高地靶被击毁后"
     "才激活。因此 R1 的首要任务是用尽可能少的弹丸击毁高地靶，为后续攻击基地靶争取时间；"
     "R2 则应尽早完成矿石兑换，保证 R1 的弹丸供给。两者在时间上的配合比单台机器人的性能"
     "更重要。")

heading("2.2　整机组成与配合方式", 2)
para("两台机器人采用“共平台、分模块”的设计思路：底盘、主控、供电与通信方案完全一致，"
     "R1 在底盘上叠加云台、发射与供弹模块，R2 叠加取矿、存储与兑换模块。这样既缩短了"
     "设计周期，也使备件、调试工具与操作习惯可以共用。R1 的电控组成如图 1 所示。")
figure(os.path.join(ASSETS, "fig_system.png"), 15.0)
caption("图 1　R1 电控系统总体框图")
para("R1 以 STM32F407VET6 主控板为核心：4 路双 PWM 驱动 MG310 底盘电机，4 路正交编码器"
     "构成速度反馈；TIM8 的三路 PWM 驱动摩擦轮无刷电机；TIM12 输出两路 50 Hz PWM 控制云台"
     "Yaw、Pitch 舵机；PD3 的急停按钮与 PE8 指示灯构成安全回路；OLED 用于现场显示参数与"
     "电池电压；USART1 与 Wi-Fi 模块相连，接入赛事服务器的 MQTT 数据流。")
para("两车的任务配合按比赛时间轴划分，如表 3 所示。", space_before=8)
caption("表 3　R1 与 R2 的任务分工与配合", above=True)
table(
    ["阶段", "时间", "R1 射击机器人", "R2 取矿兑矿机器人", "阶段目标"],
    [
        ["开局", "0～60 s", "快速占据射击位，击毁对方高地靶", "前往己方矿石区取矿", "拿下高地，打开基地靶"],
        ["中期", "60～180 s", "攻击对方基地靶，优先移动靶", "运送矿石至兑换区并完成兑换", "扩大比分、补充弹丸"],
        ["后期", "180～300 s", "持续压制，处理剩余基地靶", "继续兑换或协助防守", "锁定胜局或追分"],
    ],
    [1.8, 2.4, 4.6, 4.2, 4.0],
    font_size=10,
)
para("该分工的前提是底盘具有足够的机动性与越障能力：R1 需要在隧道与起伏路段之间快速转移，"
     "R2 需要稳定地把矿石送上中央高地。因此底盘方案在两台车上完全复用，后续的可靠性改进"
     "也只需做一次。")

heading("2.3　R1 射击机器人方案", 2)
para("R1 由底盘、二自由度云台、摩擦轮发射机构与供弹机构组成。底盘采用 4×MG310 直流减速"
     "电机（1:20，额定 7.4 V，允许 7～13 V），配 48 mm D 型槽轮胎，双 PWM 调速、四路正交"
     "编码器测速，差速转向。按 12 V 供电估算，正常行驶电流约 1.2～2.0 A，四轮堵转可达 8 A，"
     "因此底盘需要在软件上做限流保护。")
para("云台为 Yaw、Pitch 两轴，直接由舵机驱动。选型讨论中，MG996R（13 kg·cm）被认为扭矩"
     "偏小，难以带动带摩擦轮系统的云台；目前倾向于采用金属齿轮的 360° 大扭矩舵机（约 64 元/个，"
     "两只），具体扭矩需按云台与发射机构的总重量最终确定。总线舵机可以只用一个串口控制全部"
     "舵机并回传角度，但驱动板价格高、舵机本身也更贵，在目前 3 个舵机、定时器资源尚有余量的"
     "情况下暂不采用，仅作为后续扩展的备选。")
para("发射机构采用两只 C2208 无刷电机（12 V / 10 W，额定 0.8 A，0.03 N·m）对转夹持弹丸，"
     "摩擦轮本体沿用校内赛版本，两轮共用一个 PWM 信号，由双路无刷驱动板把一路 PWM 转换为"
     "三相驱动。弹丸为官方统一提供的 17 mm、95A TPU 小球，摩擦轮间隙与拨弹通道均按该尺寸"
     "设计。供弹机构由弹仓与拨弹轮组成，弹仓容量按不少于 8 发设计，拨弹由舵机驱动，"
     "具体结构待机械组出图。")

heading("2.4　R2 取矿兑矿机器人方案", 2)
para("R2 与 R1 共用底盘、主控与供电方案，差别在于上装：取矿机构、矿石存储与兑换机构。"
     "目前讨论的取矿方案为“升降 + 夹爪”组合：升降采用直流减速电机加蜗轮蜗杆，利用自锁"
     "特性在断电后保持高度；夹爪采用直流减速电机或 360° 舵机，夹持矿石后抬升、行驶至中央"
     "高地区，再放入兑换区。为适应矿石与兑换区的实际尺寸，机构设计为行程可调，并预留"
     "旋转与伸缩接口，便于后续根据场地图纸调整。")
para("该方案尚未定型：矿石尺寸、兑换区开口尺寸与高度需要组委会场地图纸确认；夹爪的"
     "夹持力、升降行程与整机重心也需要在样机上验证。队伍当前的判断是，R2 的难点不在控制"
     "而在机构可靠性——一旦卡矿或掉矿，本局将失去全部兑换机会，因此机构以简单、容错为"
     "首要原则。")

heading("2.5　电控与软件架构", 2)
para("电控采用“实时控制 + 通信协处理”的双芯片结构：STM32F407VET6 负责电机、编码器、"
     "舵机、摩擦轮与急停等硬实时任务；Wi-Fi 与 MQTT/Protobuf 通信由 ESP32 模块承担，两者"
     "通过 USART1（115200 bit/s，DMA 空闲中断收发）交换数据。这样既保证了控制周期的"
     "确定性，也避免了在 STM32 上实现 TCP/IP 协议栈带来的资源与实时性压力。")
para("软件按应用层、算法层、驱动层与硬件抽象层划分。应用层负责任务调度与状态管理；"
     "算法层包含 PID、差速逆运动学、指令平滑与数学工具；驱动层封装电机、编码器、舵机、"
     "无刷电机、OLED、ADC 与串口；最底层为 HAL 库与 CubeMX 生成的初始化代码。控制任务"
     "全部在定时器中断中完成，主循环只负责 1 Hz 的人机界面刷新。控制数据流如图 2 所示。")
figure(os.path.join(ASSETS, "fig_control.png"), 15.0)
caption("图 2　控制系统数据流")
para("时序上，TIM13 以 100 Hz 触发控制主中断，完成编码器采样、四路 PID、舵机与摩擦轮"
     "使能；中断内部二分频，得到 50 Hz 的逆运动学解算；TIM6 以 5 kHz 更新摩擦轮电角度。"
     "所有中断优先级均为 0，同优先级之间不互相抢占，5 kHz 中断的 CPU 占用需要在整机联调时"
     "用 DWT 或 IO 翻转法实测。")
para("赛事通信协议由组委会统一提供：服务器以 MQTT 发布 Protobuf v3 序列化的二进制流，"
     "Broker 地址为 192.168.1.2:3333，机器人通过场地 Wi-Fi 接入。机器人侧需要订阅 5 个"
     "主题，频率均为 1 Hz，内容如表 4 所示。", space_before=10)
caption("表 4　赛事通信指令", above=True)
table(
    ["主题", "方向", "主要内容", "用途"],
    [
        ["GameStatus", "服务器 → 机器人", "局号、阶段、剩余时间、双方得分", "驱动比赛状态机与倒计时"],
        ["TargetStatus", "服务器 → 机器人", "双方高地命中位图、基地击毁位图", "判断高地是否被击毁、基地是否激活"],
        ["ExchangeStatus", "服务器 → 机器人", "有效兑换数、已领取弹丸次数", "提示 R2 兑换进度与补弹时机"],
        ["RobotStatus", "服务器 → 机器人", "各车资格、罚时、红黄牌数", "异常时降速或停机"],
        ["GameResult", "服务器 → 机器人", "本局胜负、胜因、总比分", "记录与复盘"],
    ],
    [3.0, 3.4, 5.0, 3.6],
    font_size=10,
)
para("目前 STM32 侧只完成了串口收发框架与回调注册，Protobuf 解析与 MQTT 客户端尚未实现，"
     "计划由 ESP32 完成协议栈、STM32 只接收解析后的定长状态帧，以降低主控负担。")

heading("2.6　供电与线束方案", 2)
para("供电采用双电池方案（2026-10-31 讨论确定）：电池 A 单独为 C30D 主控板供电，电池 B 为"
     "外置舵机 BEC 与双路无刷驱动板供电，两包电池共地、正极不并联，各自串独立保险。"
     "这样做的原因是 C30D 的板载电机轨总持续电流只有 5 A、单路 1.3 A，舵机轨总持续 3 A，"
     "而摩擦轮启动峰值可达 9 A、两颗云台舵机堵转可达 5 A，混在一起会触发保护甚至掉电。")
figure(os.path.join(ASSETS, "fig_power.png"), 15.0)
caption("图 3　双电池供电拓扑")
para("按现有负载估算，R1 正常工况整机电流约 5.2～6.5 A，峰值约 24.6 A；其中电池 A 轨约"
     "2.6 A（峰值 8.6 A），电池 B 轨约 3.9 A（峰值 16 A）。电池 B 选用 3S 2200～3300 mAh、"
     "30C 以上的电池，保证瞬时 20 A 以上的放电能力。供电分配与限流措施如表 5 所示。",
     space_before=8)
caption("表 5　供电分配与限流措施", above=True)
table(
    ["负载", "供电来源", "正常电流", "峰值电流", "措施"],
    [
        ["4× MG310 底盘", "电池 A → C30D 电机通道", "1.2～2.0 A", "8 A", "软件限流，单路 ≤1.2 A"],
        ["云台舵机 ×2", "电池 B → BEC-1", "1.0～1.8 A", "5 A", "外置 BEC，单独走线"],
        ["拨弹舵机", "电池 B → BEC-2", "0.5 A", "2 A", "与云台分 BEC，避免互相拉低"],
        ["2× C2208 摩擦轮", "电池 B → 双路驱动板", "1.6 A", "9 A", "独立供电，禁止走板载电机轨"],
        ["板载逻辑 / IMU", "C30D 5 V", "0.3～0.5 A", "0.6 A", "IMU 加 0.1 µF 滤波"],
    ],
    [3.2, 4.6, 2.6, 2.4, 4.2],
    font_size=10,
)

heading("2.7　规则符合性核对", 2)
para("为避免检录阶段出现问题，队伍按规则逐项核对了设计，结果如表 6 所示。", space_before=2)
caption("表 6　规则符合性核对", above=True)
table(
    ["规则要求", "本队方案", "状态"],
    [
        ["任意姿态尺寸 ≤ 500×500×550 mm", "按 500×500×550 包络设计；云台、发射机构不超界", "待整机测量"],
        ["可靠断电 / 急停措施", "PD3 硬件急停 + 软件急停，10 ms 内切断电机与发射", "已实现"],
        ["仅使用官方弹丸", "使用组委会提供的 17 mm、95A TPU 弹丸", "符合"],
        ["禁止尖锐结构、高压气体", "结构件倒角，无高压气路", "符合"],
        ["无线不得干扰其他机器人", "2.4 GHz Wi-Fi 接入指定信道，发射功率受限", "待现场确认"],
        ["机器人数量与操作手", "R1 一台、1 名操作手；R2 一台、≤2 名操作手", "符合"],
        ["总重量判定", "结构轻量化，铝件 + 3D 打印件混合", "持续优化"],
    ],
    [5.6, 7.0, 2.4],
    font_size=10,
)
para("尺寸与重量是当前最需要关注的合规项：轮距暂定 500 mm，已处于尺寸上限，需要与机械组"
     "确认测量基准并留出余量；云台在 Pitch 极限角度下是否超出包络，也需要在整机装配后实测。")

# ============================================================ 3 进展
heading("3　当前进展与阶段成果", 1)
heading("3.1　进展总览", 2)
para("按“设计完成、制作完成、测试通过”三个状态统计，各模块的进展如表 7 所示。", space_before=2)
caption("表 7　各模块进展总览", above=True)
table(
    ["工作模块", "当前状态", "成果或验证情况", "负责人"],
    [
        ["底盘机械", "设计完成", "四轮差速底盘三维模型，轮距 500 mm、轮径 48 mm", "机械"],
        ["底盘电控", "测试通过（台架）", "四轮正反转、编码器测速、100 Hz 闭环、急停", "电控"],
        ["云台", "设计完成，选型中", "双轴结构、TIM12 双通道驱动、急停回中", "机械 / 电控"],
        ["射击机构", "制作完成，测试中", "2×C2208 开环驱动，5 kHz 电角度更新，三相波形正常", "电控"],
        ["供弹机构", "方案设计", "弹仓 + 拨弹轮方案，按 8 发容量设计", "机械"],
        ["R2 取矿 / 兑换", "方案设计", "升降 + 夹爪方案，行程可调，待出图", "机械"],
        ["电源与线束", "设计完成，采购中", "双电池方案、分电与保险、电流核算", "硬件"],
        ["通信", "接口完成，联调未开始", "USART1 DMA 空闲中断收发框架", "电控"],
    ],
    [3.2, 3.8, 6.4, 2.2],
    font_size=10,
)
para("需要说明的是，底盘电控的“测试通过”指台架测试：四个电机可以按指令正反转并稳定调速，"
     "编码器读数与转向一致，100 Hz 控制周期与急停响应正常；带载行驶、越障与整机联调尚未"
     "进行，因此不能等同于整机测试通过。射击机构目前为开环验证，转速会随负载变化，闭环"
     "尚未实现。")

heading("3.2　底盘与移动", 2)
para("底盘电控已完成四路电机的双 PWM 驱动与测速闭环。每个电机由两路 PWM 组成 H 桥："
     "一路给定占空比调速，另一路保持常高电平以打开对应桥臂，速度指令为 −100～100 的百分比，"
     "映射为比较值 CCR = ARR + 1 − round(|u|/100 × (ARR + 1))，PWM 频率 10 kHz。方向由符号"
     "决定，通过交换两路 PWM 的角色实现正反转。")
para("测速采用定时器编码器模式，TIM2～TIM5 分别对四路正交编码器计数，控制周期内读取"
     "计数器并清零，按 ω = clamp(N, −140, 140)/140 × 28.462 × π 折算为轮速（rad/s）。"
     "该折算系数为经验值，尚未用标准转速源标定，是下一阶段的标定项。")
para("速度环采用位置式 PID，四个轮子各一个实例，在 100 Hz 中断中执行，参数为 K_P = 3.0、"
     "K_I = 12.0、K_D = 0、K_F = 0，积分与输出均限幅 ±100，并带有变速积分、积分分离、"
     "死区与微分先行等可配置措施。逆运动学以 50 Hz 运行，按 v_L = v_x − ω·b/2、"
     "v_R = v_x + ω·b/2 解算左右轮目标角速度，并在超限时按比例缩放以保持转弯半径。")
para("需要指出两点：一是逆解使用的轮半径暂取 35 mm、轮距 500 mm，与机械组当前 48 mm 轮径的"
     "选型尚未统一，装配后必须重新标定；二是代码虽然计算了平滑后的指令，但逆解仍使用原始"
     "指令，平滑环节尚未接入，已列入整改项。")

heading("3.3　射击机构", 2)
para("摩擦轮采用 V/f 开环驱动：TIM6 以 5 kHz 更新电角度 θ += 70 × 0.0002 rad，经反 Park"
     "变换得到三相正弦电压，再按 (0.5 + U/V_dc) × 8400 映射为 TIM8 三路比较值，PWM 为"
     "中心对齐、10 kHz。当前 Uq 固定 1 V、Ud = 0，属于恒压开环运行。")
para("台架测试中，两只 C2208 可以正常起转，三相波形对称，改变 Uq 可以明显改变转速；但"
     "用手轻触摩擦轮即可观察到转速下降，说明开环方式无法维持恒定线速度，发射初速会随"
     "弹丸挤压与电池电压波动而变化。这是下一阶段要解决的重点问题之一。")
para("另外，当前代码由 TIM8 直接输出三相互补 PWM 驱动电机，而整机方案计划使用双路无刷"
     "驱动板（输入一路 PWM、内部完成换相）。两种接口不一致，装车前需要统一：要么保留"
     "三相直驱方案并调整驱动板，要么把控制信号改为单路 PWM 并去掉软件换相。")

heading("3.4　云台", 2)
para("云台两路舵机由 TIM12 的 CH1（Yaw）与 CH2（Pitch）控制，定时器 1 MHz 计数、ARR 9999，"
     "输出 50 Hz、1000～2000 μs 的脉宽。为避免零指令附近抖动，映射采用带死区的分段线性"
     "方式：|speed_rate| 小于死区时输出中位 1500 μs，正转在 1600～2000 μs 之间线性映射，"
     "反转在 1400～1000 μs 之间线性映射，并对输入做 ±100 限幅与 NaN 保护。急停时两路"
     "立即回到 1500 μs 中位。")
para("台架上已验证 1.5 ms 中位与 1～2 ms 行程，舵机响应正常；带负载（云台 + 摩擦轮）的"
     "扭矩与回差尚未测试，舵机型号也未最终确定。")

heading("3.5　R2 取矿与兑换机构", 2)
para("R2 的取矿与兑换机构目前处于方案设计阶段，尚未开始制作。已确定的方向是：与 R1 共用"
     "底盘与主控；取矿采用升降 + 夹爪，升降用蜗轮蜗杆减速电机自锁，夹爪用直流减速电机或"
     "360° 舵机；矿石存储在车体后部，兑换时通过翻转或推放机构放入兑换区。")
para("方案未定型的主要原因是对外接口不明确：矿石的实际尺寸、兑换区开口与高度需要组委会"
     "场地图纸；如果兑换区较高，升降行程与重心会显著变化。队伍已按可调行程设计，待图纸"
     "公布后再冻结尺寸。")

heading("3.6　电控与程序", 2)
para("控制程序以 main.cpp 为入口，按模块拆分到 MyDrivers 目录：PID、差速逆解、电机、"
     "编码器、舵机、无刷电机、OLED、ADC 与串口驱动相互独立，便于单独测试。用户自写代码"
     "约 1600 行（不含 CubeMX 生成代码与字库）。主要文件见附录 E。")
para("调试过程中遇到一个典型问题：TIM6 的 5 kHz 中断始终无法进入，而 TIM13 的 100 Hz 中断"
     "工作正常。排查发现，实际参与编译的是 main.cpp，而 MX_TIM6_Init() 只写在未被加入工程"
     "的 main.c 中，链接器把该初始化函数当作死代码删除；由于定时器句柄停留在复位态，"
     "HAL_TIM_Base_Start_IT() 在状态检查处直接返回 HAL_ERROR，计数器根本没有启动。"
     "在 main.cpp 中补上初始化调用后中断恢复正常。这个问题的排查过程（链接输入文件、map "
     "文件与 HAL 源码交叉比对）已整理为队伍的内部调试记录，对后续类似问题有参考价值。")

heading("3.7　选型与采购进展", 2)
para("选型方面，队伍在 2026-10-31 的讨论中确定了以下方案：电源采用双电池（C30D 一包、"
     "舵机与摩擦轮一包，共地）；主控选用 WHEELTEC C30D（STM32F407VET6，4 路电机 + 6 路"
     "舵机）；底盘电机由赛事方提供 MG310（共 8 个），摩擦轮电机选用 2×C2208，云台舵机暂按"
     "金属齿大扭矩 360° 舵机，底盘轮胎选 48 mm D 型槽；姿态检测使用 2×ICM20602（Yaw、Pitch"
     "各一），走 I2C3 并加 0.1 µF 滤波。无线方案尚未最终确定：材料清单中曾计划改用板载蓝牙"
     "（USART2），但赛事官方协议要求通过场地 Wi-Fi 以 MQTT 接入，因此仍需 ESP32 类模块"
     "承担 Wi-Fi 通信，这一点需要在下次讨论中确认。")
para("采购方面，已标价项目合计约 752.5 元，涵盖主控、下载器、IMU、摄像头、ESP32 模块、"
     "摩擦轮电机、双路驱动板、舵机、BEC、线材、轮胎等；电池 A/B、拨弹舵机、扎带等尚未定价。"
     "清单摘要见附录 B。")

heading("3.8　已完成的测试与验证", 2)
para("截至报告日，已在台架上完成的测试项、判据与结果如表 8 所示。", space_before=2)
caption("表 8　已完成的台架测试", above=True)
table(
    ["序号", "测试项", "方法 / 判据", "结果"],
    [
        ["1", "四轮正反转", "给定 ±50% 指令，观察转向与占空比", "通过"],
        ["2", "PWM 频率", "示波器测量电机驱动引脚", "10 kHz，通过"],
        ["3", "编码器计数", "手动转动轮子，观察计数器增减", "通过"],
        ["4", "控制周期", "中断内翻转 IO，示波器测量", "100 Hz，通过"],
        ["5", "速度闭环", "阶跃指令，观察跟随性与稳态误差", "初步通过，待整定"],
        ["6", "逆运动学", "给定 v_x、ω，检查四轮目标符号与比例", "通过"],
        ["7", "摩擦轮驱动", "5 kHz 中断计数与三相波形观测", "初步通过，开环"],
        ["8", "舵机输出", "1.5 ms 中位、1～2 ms 行程测量", "通过，行程待标定"],
        ["9", "急停保护", "按下/松开按钮，观察停机与恢复", "通过"],
        ["10", "串口收发", "USART1 DMA 回环收发", "通过，协议未接"],
    ],
    [1.2, 4.0, 7.4, 2.4],
    font_size=10,
)
para("上述测试均在台架上完成，缺少整车状态下的带载、越障与连续发射数据；相关照片与示波器"
     "截图正在整理，将在提交版中补充。")

# ============================================================ 4 问题
heading("4　当前问题与所需支持", 1)
para("按对进度的影响程度排序，当前最需要解决的三个问题如下。")

heading("4.1　问题一：取矿机构方案与加工", 2)
para("问题表现：R2 的取矿、存储与兑换机构尚未定型，矿石尺寸、兑换区开口与高度依赖组委会"
     "场地图纸，机械组无法冻结尺寸，加工排期被迫后移。若继续拖延，R2 将无法在赛前完成"
     "连续取矿与兑换测试。")
para("已尝试的方法：参考开源步兵的取矿与供弹结构；把机构拆成“升降 + 夹爪 + 存储”三个"
     "模块分别讨论；按可调行程设计，预留旋转与伸缩接口。")
para("下一步思路：先按经验尺寸做一台 3D 打印样机，验证夹持与升降的可靠性，再根据场地图纸"
     "冻结尺寸并转铝件加工。")
para("所需支持：希望组委会尽早提供矿石与兑换区的详细尺寸；需要机械加工与 3D 打印资源，"
     "以及一次场地实测机会。")

heading("4.2　问题二：70 mm 台阶通过性", 2)
para("问题表现：底盘目前选配 48 mm 轮胎，而中央高地前的台阶高 70±1 mm，轮径小于台阶高度，"
     "直接越障困难；若无法上台阶，R1 将无法攻击高地靶，R2 也无法完成兑换。")
para("已尝试的方法：提高越障时的占空比与助跑速度；核算四轮驱动下的越障几何；与机械组"
     "讨论增大轮径或增加辅助轮的可行性。")
para("下一步思路：优先尝试 60～70 mm 轮径并配合助跑；若仍不足，考虑加装摆臂或辅助轮，"
     "但需重新核算尺寸包络与重量。")
para("所需支持：需要一个 70 mm 台阶的测试样件或场地，以及加工摆臂/辅助轮的资源。")

heading("4.3　问题三：发射一致性与云台扭矩", 2)
para("问题表现：摩擦轮为恒压开环，转速随负载与电池电压变化，发射初速不稳定；云台原定的"
     "MG996R 扭矩偏小，带摩擦轮系统时可能出现抖动或掉角。")
para("已尝试的方法：把电角度更新提高到 5 kHz，改善低速平稳性；提高 Uq 增加扭矩；在结构上"
     "减重。")
para("下一步思路：为摩擦轮增加转速或电流反馈，形成速度闭环；云台改用金属齿大扭矩舵机，"
     "并按实际重量复算扭矩余量。")
para("所需支持：需要测速方案（霍尔或反电势采样）与电流采样器件、两只大扭矩舵机，以及"
     "一批测试弹丸用于一致性测试。")

heading("4.4　所需支持汇总", 2)
para("上述问题对应的支持需求汇总如表 9 所示。", space_before=2)
caption("表 9　所需支持汇总", above=True)
table(
    ["类别", "具体需求", "用途", "期望时间"],
    [
        ["场地与图纸", "矿石、兑换区、台阶的详细尺寸与场地实测", "冻结 R2 机构尺寸、验证越障", "11 月底"],
        ["加工", "铝件加工、3D 打印、摆臂/辅助轮制作", "R2 样机、底盘越障改进", "12 月上旬"],
        ["器材", "大扭矩舵机 ×2、测速/电流采样器件", "云台与发射闭环", "12 月上旬"],
        ["测试", "测试弹丸一批、连续发射场地", "发射一致性与供弹可靠性", "12 月中旬"],
        ["技术指导", "结构强度与重量分配的评审", "控制整机重量、避免结构失效", "12 月上旬"],
    ],
    [2.6, 6.4, 4.6, 2.4],
    font_size=10,
)

# ============================================================ 5 计划
heading("5　下一阶段计划", 1)
heading("5.1　任务分解与完成标准", 2)
para("从本次考核到比赛，剩余时间约 5 周。任务按“电控迁移—机构制作—联调—可靠性”四条线"
     "并行推进，具体安排如表 10 所示。", space_before=2)
caption("表 10　下一阶段任务与完成标准", above=True)
table(
    ["任务", "负责人", "完成时间", "完成标准"],
    [
        ["电控迁移到 C30D，核对引脚与外设映射", "电控", "11 月 28 日", "四轮闭环、云台、摩擦轮在 C30D 上复现"],
        ["R2 取矿机构出图并制作样机", "机械", "12 月 5 日", "完成连续 10 次取矿不卡矿"],
        ["云台舵机选型、装配与带载测试", "机械 / 电控", "12 月 8 日", "Pitch/Yaw 全行程无丢步、回差 ≤2°"],
        ["ESP32 接入 MQTT/Protobuf 并联调", "电控", "12 月 10 日", "5 个主题 1 Hz 稳定接收，状态机可用"],
        ["摩擦轮转速闭环与发射一致性测试", "电控", "12 月 12 日", "初速波动 ≤5%，连续 20 发不卡弹"],
        ["整机合练（R1 + R2）", "全队", "12 月 15 日", "完成 5 分钟全流程演练 3 次以上"],
        ["可靠性、备件与文档", "全队", "12 月 20 日", "关键件有备件，操作手册与检查表齐备"],
    ],
    [6.2, 2.4, 2.6, 4.8],
    font_size=10,
)

heading("5.2　里程碑", 2)
para("（1）11 月 28 日：电控迁移完成，R1 在 C30D 上复现全部台架功能；")
para("（2）12 月 10 日：通信与 R2 样机就位，具备第一次整机合练条件；")
para("（3）12 月 15 日：完成首次 5 分钟全流程合练，形成问题清单；")
para("（4）12 月 20 日：完成可靠性改进与备件准备，进入赛前封版；")
para("（5）赛前一周：只做参数微调与操作演练，不再改动结构。")

# ============================================================ 附录
heading("附录 A　比赛规则要点", 1)
para("为便于备赛查阅，将与本队设计直接相关的规则要点整理如表 A.1 所示。", space_before=2)
caption("表 A.1　比赛规则要点", above=True)
table(
    ["项目", "要求"],
    [
        ["赛制", "红蓝对抗，BO3，每局 5 分钟"],
        ["机器人", "每队 R1 射击机器人 1 台、R2 取矿兑矿机器人 1 台"],
        ["操作手", "R1 1 名，R2 不超过 2 名"],
        ["尺寸", "任意姿态不超过 500×500×550 mm（规则表述不一，按最保守值控制）"],
        ["弹丸", "直径 17 mm、TPU、硬度 95A，仅限官方弹丸"],
        ["弹丸数量", "初始 8 颗；最多兑换 3 次，每次 8 颗"],
        ["高地靶", "4 片开关（2 大 5 分、2 小 10 分），合计 30 分"],
        ["基地靶", "3 个固定靶各 15 分、1 个移动靶 45 分，合计 90 分"],
        ["台阶", "70±1 mm，可登上中央高地"],
        ["禁区", "中央己方兑换区为对方禁区，停留 10 s 黄牌、20 s 红牌"],
        ["安全", "必须具有可靠的断电或急停措施"],
    ],
    [3.4, 11.6],
    font_size=10,
)

heading("附录 B　材料清单与预算", 1)
para("材料清单与预算摘要如表 B.1 所示，已标价项目合计约 752.5 元，不含电池 A/B、拨弹舵机、"
     "扎带与舵机测试仪等待定价项目。", space_before=2)
caption("表 B.1　材料清单与预算摘要", above=True)
table(
    ["分类", "项目", "数量", "小计（元）"],
    [
        ["中控", "WHEELTEC C30D 主控板", "1", "357"],
        ["中控", "ST-Link 下载器", "1", "11.42"],
        ["中控", "ICM20602 IMU（Yaw / Pitch）", "2", "35.18"],
        ["中控", "USB 免驱摄像头", "1", "16.61"],
        ["中控", "ESP32-P4 / ESP32-C5", "各 1", "133.6"],
        ["驱动", "C2208 摩擦轮电机", "2", "74"],
        ["驱动", "双路无刷驱动板", "1", "33.65"],
        ["驱动", "MG996R 舵机（云台）", "2", "28.82"],
        ["驱动", "5V 5A BEC", "2", "44.88"],
        ["线材", "电机线、分电端子、杜邦线等", "若干", "8.14"],
        ["其他", "轮胎（48 mm D 型槽）", "4", "9.2"],
        ["电源", "电池 A / B", "2", "待定"],
        ["合计", "已标价项目", "—", "≈752.5"],
    ],
    [2.6, 8.2, 2.2, 2.6],
    font_size=10,
)
para("注：云台舵机拟由 MG996R 升级为金属齿 360° 大扭矩舵机（约 64 元/个，两只），表中仍按原采购清单列示，预算需相应调整；电池 A/B 与拨弹舵机尚未定价，未计入合计。", space_before=6)

heading("附录 C　关键参数汇总", 1)
caption("表 C.1　关键参数汇总", above=True)
table(
    ["参数", "取值", "参数", "取值"],
    [
        ["系统主频", "168 MHz", "电机 PWM 频率", "10 kHz"],
        ["控制周期", "10 ms（100 Hz）", "逆解周期", "20 ms（50 Hz）"],
        ["摩擦轮更新频率", "5 kHz", "摩擦轮电角速度", "70 rad/s"],
        ["摩擦轮母线电压", "12 V", "摩擦轮 Uq", "1 V（开环）"],
        ["舵机 PWM 频率", "50 Hz", "舵机脉宽范围", "1000～2000 μs"],
        ["轮半径（暂定）", "35 mm", "轮距（暂定）", "500 mm"],
        ["底盘电机", "MG310，1:20", "轮胎", "48 mm D 型槽"],
        ["电池 A", "3S 2550 mAh", "电池 B", "3S 2200～3300 mAh，≥20 A"],
        ["PID 参数", "K_P=3.0，K_I=12.0", "输出限幅", "±100"],
    ],
    [4.6, 3.2, 4.6, 2.6],
    font_size=10,
)

heading("附录 D　讨论记录摘要", 1)
para("（1）2026-10-31 选型讨论：确定双电池方案（C30D 一包、舵机与摩擦轮一包，共地）；"
     "主控、驱动、线材与电源方案基本确定；无线一度计划改用板载蓝牙（USART2），后因官方"
     "协议要求 Wi-Fi/MQTT 而保留 ESP32 方案，待确认。")
para("（2）云台讨论：MG996R 扭矩不足以带动带摩擦轮系统的云台，Yaw、Pitch 均倾向金属齿"
     "360° 大扭矩舵机（约 64 元/个）；总线舵机可回传角度、只需一个串口，但驱动板昂贵，"
     "在舵机数量少、定时器有余量时暂不采用。")
para("（3）供弹讨论：开源步兵采用大疆 2006 无刷电机拨弹；本队可先用大扭矩 360° 舵机按"
     "时间控制拨弹，若行程较长再改用电机，具体看机械设计。")
para("（4）接口与线束：电机线、分电端子、杜邦线长度与接口仍需在整机装配时统一。")

heading("附录 E　主要程序文件", 1)
caption("表 E.1　主要程序文件", above=True)
table(
    ["模块", "文件", "主要功能", "行数"],
    [
        ["应用入口", "Core/Src/main.cpp", "任务调度、中断回调、急停逻辑", "401"],
        ["PID 算法", "alg_pid.h / alg_pid.cpp", "通用 PID（前馈、变速积分等）", "398"],
        ["运动学", "diff_drive_ik.cpp", "差速逆解、归一化限幅、指令平滑", "90"],
        ["电机驱动", "Motor_cpp_style.h / .cpp", "双 PWM 调速与方向控制", "127"],
        ["编码器", "Encoder.h / Encoder.c", "脉冲读取与轮速折算", "36"],
        ["无刷电机", "BLDC.h / BLDC.c", "三相正弦开环驱动", "73"],
        ["舵机", "Servo.h / Servo.cpp", "速度—脉宽映射与限幅", "107"],
        ["显示", "bsp_oled.h / bsp_oled.c", "OLED 驱动与绘图接口", "375"],
        ["串口", "drv_uart.h / drv_uart.c", "DMA 空闲中断收发框架", "194"],
    ],
    [2.4, 6.4, 4.6, 1.6],
    font_size=10,
)

doc.core_properties.title = "第四届“拓竹杯”狼牙机器人争霸赛 中期进展报告"
doc.core_properties.subject = "R1 射击机器人 / R2 取矿兑矿机器人"
doc.core_properties.comments = "按中期考核通知的五部分结构整理"

doc.save(OUT)
print("saved:", OUT)
