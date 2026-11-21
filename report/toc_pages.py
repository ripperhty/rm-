# -*- coding: utf-8 -*-
"""从 LibreOffice 生成的 PDF 书签中提取各级标题所在页码。"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PDF = sys.argv[1]
OUT = sys.argv[2]

data = open(PDF, "rb").read()

# 所有间接对象（该 PDF 未使用对象流）
objs = {}
for m in re.finditer(rb"(\d+)\s+0\s+obj(.*?)endobj", data, re.S):
    objs[int(m.group(1))] = m.group(2)


def get_int(body, key):
    m = re.search(key + rb"\s+(\d+)\s+0\s+R", body)
    return int(m.group(1)) if m else None


def decode_title(body):
    m = re.search(rb"/Title\s*<([0-9A-Fa-f]+)>", body)
    if m:
        return bytes.fromhex(m.group(1).decode()).decode("utf-16-be", "replace").lstrip("\ufeff")
    m = re.search(rb"/Title\s*\((.*?)\)", body, re.S)
    if m:
        return m.group(1).decode("latin-1")
    return ""


def dest_page(body):
    m = re.search(rb"/Dest\s*\[\s*(\d+)\s+0\s+R", body)
    if m:
        return int(m.group(1))
    m = re.search(rb"/A\s*<<(.*?)>>", body, re.S)
    if m:
        m2 = re.search(rb"/D\s*\[\s*(\d+)\s+0\s+R", m.group(1))
        if m2:
            return int(m2.group(1))
    # 间接 /Dest N 0 R
    m = re.search(rb"/Dest\s+(\d+)\s+0\s+R", body)
    if m:
        return int(m.group(1))
    return None


# 页面树：根 -> Pages -> Kids 递归，得到页对象顺序
root = None
m = re.search(rb"/Outlines\s+(\d+)\s+0\s+R", data)
if m:
    root = int(m.group(1))
else:
    for oid, body in objs.items():
        if re.search(rb"/First\s+\d+\s+0\s+R", body) and b"/Title" not in body:
            root = oid
            break

page_order = []
pages_root = None
for oid, body in objs.items():
    if re.search(rb"/Type\s*/Pages\b", body) and b"/Parent" not in body:
        pages_root = oid
        break


def walk_pages(oid):
    body = objs[oid]
    if re.search(rb"/Type\s*/Page\b", body):
        page_order.append(oid)
        return
    kids = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
    if kids:
        for m in re.finditer(rb"(\d+)\s+0\s+R", kids.group(1)):
            walk_pages(int(m.group(1)))


if pages_root:
    walk_pages(pages_root)

page_index = {oid: i + 1 for i, oid in enumerate(page_order)}


def walk_outline(oid, depth, out):
    body = objs[oid]
    out.append((depth, decode_title(body), page_index.get(dest_page(body))))
    first = get_int(body, rb"/First")
    if first:
        walk_outline(first, depth + 1, out)
    nxt = get_int(body, rb"/Next")
    if nxt:
        walk_outline(nxt, depth, out)


entries = []
if root:
    first = get_int(objs[root], rb"/First")
    if first:
        walk_outline(first, 1, entries)

for d, t, p in entries:
    print("%*s%s  ->  %s" % (d * 2, "", t, p))

json.dump([{"depth": d, "title": t, "page": p} for d, t, p in entries],
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("pages:", len(page_order), "entries:", len(entries))
